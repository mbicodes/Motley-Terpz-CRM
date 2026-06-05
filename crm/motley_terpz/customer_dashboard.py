"""
Motley Terpz — Customer Demographics Dashboard API
Returns all KPIs, trend data, AR aging, category breakdown and recent activity
for a given ERPNext Customer.
"""
import frappe
from frappe.utils import flt, getdate, nowdate, get_first_day, get_last_day, add_months
from datetime import timedelta
import datetime


@frappe.whitelist()
def get_customer_dashboard(customer):
    if not frappe.has_permission("Customer", "read", customer):
        frappe.throw("Not permitted", frappe.PermissionError)

    today = getdate(nowdate())
    year  = today.year

    # ── Customer & CRM info ───────────────────────────────────────────────────
    cust = frappe.db.get_value("Customer", customer, [
        "name", "customer_name", "customer_group", "territory",
        "payment_terms", "is_frozen", "creation"
    ], as_dict=True) or {}

    crm = frappe.db.get_value("CRM Lead", {"custom_erp_customer": customer}, [
        "name", "custom_relationship_tier", "custom_pipeline",
        "custom_account_owner", "custom_buyer_activity", "custom_ar_status",
        "custom_ar_balance", "custom_ar_aging_days", "custom_cod_flag",
        "custom_last_sync", "custom_notes", "custom_single_source",
        "custom_next_followup_date"
    ], as_dict=True) or {}

    # ── Lifetime KPIs ─────────────────────────────────────────────────────────
    lifetime = frappe.db.sql("""
        SELECT
            COALESCE(SUM(grand_total), 0)             AS lifetime_revenue,
            COALESCE(COUNT(name), 0)                  AS invoice_count,
            COALESCE(SUM(outstanding_amount), 0)      AS outstanding_ar,
            COALESCE(AVG(grand_total), 0)             AS avg_order_value,
            MAX(posting_date)                         AS last_invoice_date
        FROM `tabSales Invoice`
        WHERE customer = %(c)s AND docstatus = 1
    """, {"c": customer}, as_dict=True)
    lf = lifetime[0] if lifetime else {}

    # YTD revenue
    ytd = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0) AS rev
        FROM `tabSales Invoice`
        WHERE customer = %(c)s AND docstatus = 1
          AND YEAR(posting_date) = %(yr)s
    """, {"c": customer, "yr": year}, as_dict=True)

    # Last year revenue
    last_yr = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0) AS rev
        FROM `tabSales Invoice`
        WHERE customer = %(c)s AND docstatus = 1
          AND YEAR(posting_date) = %(yr)s
    """, {"c": customer, "yr": year - 1}, as_dict=True)

    # Last payment
    last_pay = frappe.db.sql("""
        SELECT MAX(posting_date) AS dt, COALESCE(SUM(paid_amount), 0) AS total_paid
        FROM `tabPayment Entry`
        WHERE party = %(c)s AND party_type = 'Customer' AND docstatus = 1
          AND payment_type = 'Receive'
    """, {"c": customer}, as_dict=True)
    lp = last_pay[0] if last_pay else {}

    # Total paid ever
    total_paid = flt(lf.get("lifetime_revenue", 0)) - flt(lf.get("outstanding_ar", 0))
    payment_rate = (total_paid / flt(lf.get("lifetime_revenue", 1)) * 100) if flt(lf.get("lifetime_revenue")) else 0

    last_order_dt = lf.get("last_invoice_date")
    days_since = (today - getdate(str(last_order_dt))).days if last_order_dt else None

    # ── AR Aging buckets ──────────────────────────────────────────────────────
    aging_rows = frappe.db.sql("""
        SELECT
            DATEDIFF(CURDATE(), due_date) AS days_overdue,
            outstanding_amount
        FROM `tabSales Invoice`
        WHERE customer = %(c)s AND docstatus = 1 AND outstanding_amount > 0.01
    """, {"c": customer}, as_dict=True)

    aging = {"current": 0.0, "30": 0.0, "60": 0.0, "90": 0.0}
    for r in aging_rows:
        d = int(r.days_overdue or 0)
        a = flt(r.outstanding_amount)
        if d <= 0:
            aging["current"] += a
        elif d <= 30:
            aging["current"] += a
        elif d <= 60:
            aging["30"] += a
        elif d <= 90:
            aging["60"] += a
        else:
            aging["90"] += a

    # ── Monthly revenue trend — 13 months ────────────────────────────────────
    months_data = frappe.db.sql("""
        SELECT
            YEAR(posting_date)  AS yr,
            MONTH(posting_date) AS mo,
            COALESCE(SUM(grand_total), 0) AS revenue,
            COUNT(name) AS orders
        FROM `tabSales Invoice`
        WHERE customer = %(c)s AND docstatus = 1
          AND posting_date >= %(start)s
        GROUP BY YEAR(posting_date), MONTH(posting_date)
        ORDER BY yr, mo
    """, {"c": customer, "start": str(today.replace(year=year-1, month=1, day=1))}, as_dict=True)

    MONTH_ABBR = ["", "Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]

    # Build full 12-month arrays for current & previous year
    current_year_trend  = []
    previous_year_trend = []
    month_map = {(r.yr, r.mo): r for r in months_data}

    for m in range(1, 13):
        label = MONTH_ABBR[m]
        cy = month_map.get((year,   m), {})
        py = month_map.get((year-1, m), {})
        current_year_trend.append({
            "month": label, "revenue": flt(cy.get("revenue", 0)), "orders": int(cy.get("orders", 0))
        })
        previous_year_trend.append({
            "month": label, "revenue": flt(py.get("revenue", 0)), "orders": int(py.get("orders", 0))
        })

    # ── Category (item group) breakdown ──────────────────────────────────────
    categories = frappe.db.sql("""
        SELECT
            COALESCE(i.item_group, 'Other') AS item_group,
            SUM(sii.base_net_amount) AS revenue,
            SUM(sii.qty) AS qty,
            COUNT(DISTINCT si.name) AS invoices
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        LEFT JOIN `tabItem` i      ON i.name  = sii.item_code
        WHERE si.customer = %(c)s AND si.docstatus = 1
        GROUP BY COALESCE(i.item_group, 'Other')
        ORDER BY revenue DESC
        LIMIT 10
    """, {"c": customer}, as_dict=True)

    # ── Recent invoices (last 15) ─────────────────────────────────────────────
    recent = frappe.db.sql("""
        SELECT name, posting_date, grand_total, outstanding_amount,
               status, due_date, payment_terms_template
        FROM `tabSales Invoice`
        WHERE customer = %(c)s AND docstatus = 1
        ORDER BY posting_date DESC LIMIT 15
    """, {"c": customer}, as_dict=True)

    # ── Top items by revenue ──────────────────────────────────────────────────
    top_items = frappe.db.sql("""
        SELECT
            sii.item_name, sii.item_group,
            SUM(sii.base_net_amount) AS revenue,
            SUM(sii.qty) AS qty,
            COUNT(DISTINCT si.name) AS times_ordered
        FROM `tabSales Invoice Item` sii
        JOIN `tabSales Invoice` si ON si.name = sii.parent
        WHERE si.customer = %(c)s AND si.docstatus = 1
        GROUP BY sii.item_name, sii.item_group
        ORDER BY revenue DESC LIMIT 8
    """, {"c": customer}, as_dict=True)

    # ── Quarterly revenue (last 8 quarters) ──────────────────────────────────
    quarters = frappe.db.sql("""
        SELECT
            YEAR(posting_date)                        AS yr,
            QUARTER(posting_date)                     AS qtr,
            COALESCE(SUM(grand_total), 0)             AS revenue
        FROM `tabSales Invoice`
        WHERE customer = %(c)s AND docstatus = 1
          AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
        GROUP BY YEAR(posting_date), QUARTER(posting_date)
        ORDER BY yr, qtr
    """, {"c": customer}, as_dict=True)

    return {
        "customer":    cust,
        "crm":         crm,
        "kpis": {
            "lifetime_revenue": flt(lf.get("lifetime_revenue")),
            "invoice_count":    int(lf.get("invoice_count", 0)),
            "outstanding_ar":   flt(lf.get("outstanding_ar")),
            "avg_order_value":  flt(lf.get("avg_order_value")),
            "last_invoice_date":str(last_order_dt or ""),
            "days_since_last_order": days_since,
            "ytd_revenue":      flt(ytd[0].rev if ytd else 0),
            "last_year_revenue":flt(last_yr[0].rev if last_yr else 0),
            "last_payment_date":str(lp.get("dt") or ""),
            "total_paid":       flt(total_paid),
            "payment_rate_pct": round(payment_rate, 1),
        },
        "ar_aging":            aging,
        "current_year_trend":  current_year_trend,
        "previous_year_trend": previous_year_trend,
        "category_breakdown":  [dict(r) for r in categories],
        "recent_invoices":     [dict(r) for r in recent],
        "top_items":           [dict(r) for r in top_items],
        "quarterly":           [dict(r) for r in quarters],
        "current_year":        year,
    }


# ── Paginated Sales Orders ────────────────────────────────────────────────────

@frappe.whitelist()
def get_sales_orders(customer, page=1):
    if not frappe.has_permission("Sales Order", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)
    import math
    page   = int(page or 1)
    limit  = 15
    offset = (page - 1) * limit

    rows = frappe.db.sql("""
        SELECT name, transaction_date, delivery_date, status,
               grand_total, advance_paid, per_delivered, per_billed
        FROM `tabSales Order`
        WHERE customer = %(c)s AND docstatus IN (0, 1)
        ORDER BY transaction_date DESC, name DESC
        LIMIT %(l)s OFFSET %(o)s
    """, {"c": customer, "l": limit, "o": offset}, as_dict=True)

    total = frappe.db.sql(
        "SELECT COUNT(*) AS n FROM `tabSales Order` WHERE customer=%s AND docstatus IN (0,1)",
        customer, as_dict=True)[0].n

    return {
        "rows":        [dict(r) for r in rows],
        "page":        page,
        "total":       total,
        "total_pages": max(1, math.ceil(total / limit)),
    }


# ── Paginated Delivery Notes ──────────────────────────────────────────────────

@frappe.whitelist()
def get_delivery_notes(customer, page=1):
    if not frappe.has_permission("Delivery Note", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)
    import math
    page   = int(page or 1)
    limit  = 15
    offset = (page - 1) * limit

    rows = frappe.db.sql("""
        SELECT name, posting_date, status, grand_total, lr_no, lr_date
        FROM `tabDelivery Note`
        WHERE customer = %(c)s AND docstatus IN (0, 1)
        ORDER BY posting_date DESC, name DESC
        LIMIT %(l)s OFFSET %(o)s
    """, {"c": customer, "l": limit, "o": offset}, as_dict=True)

    total = frappe.db.sql(
        "SELECT COUNT(*) AS n FROM `tabDelivery Note` WHERE customer=%s AND docstatus IN (0,1)",
        customer, as_dict=True)[0].n

    return {
        "rows":        [dict(r) for r in rows],
        "page":        page,
        "total":       total,
        "total_pages": max(1, math.ceil(total / limit)),
    }


@frappe.whitelist()
def get_customer_invoices(customer, page=1):
    if not frappe.has_permission("Sales Invoice", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)
    import math
    page = int(page or 1); limit = 15; offset = (page - 1) * limit
    rows = frappe.db.sql("""
        SELECT name, posting_date, due_date, status,
               grand_total, outstanding_amount, payment_terms_template
        FROM `tabSales Invoice`
        WHERE customer = %(c)s AND docstatus IN (0,1)
        ORDER BY posting_date DESC, name DESC
        LIMIT %(l)s OFFSET %(o)s
    """, {"c": customer, "l": limit, "o": offset}, as_dict=True)
    total = frappe.db.sql(
        "SELECT COUNT(*) AS n FROM `tabSales Invoice` WHERE customer=%s AND docstatus IN (0,1)",
        customer, as_dict=True)[0].n
    return {"rows": [dict(r) for r in rows], "page": page,
            "total": total, "total_pages": max(1, math.ceil(total / limit))}
