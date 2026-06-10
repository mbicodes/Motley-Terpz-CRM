"""
Motley Terpz — Sales Intelligence APIs
Features: Command Center (01), Cash Projection (02), Customer Health Scores (03),
          Sales Projection by Product Line (04), AR Aging Heatmap (09)
"""
import frappe
from frappe.utils import flt, getdate, nowdate, cint
from datetime import timedelta


# ── Product line → item_group mapping (adjust to match your ERPNext item groups) ──
PRODUCT_LINES = {
    "Fresh Frozen":       ["Fresh Frozen"],
    "Solventless / IWH":  ["Extracts", "Solventless", "IWH", "IWH/Solventless"],
    "Rosin":              ["Rosin", "Live Rosin", "Pressed Hash"],
    "Distribution":       ["Distribution", "Retail", "Retail / Distro"],
}


def _default_company():
    default = frappe.defaults.get_global_default("company")
    if default:
        return default
    # Fall back to first company alphabetically
    companies = frappe.get_all("Company", pluck="name", order_by="name")
    return companies[0] if companies else ""


@frappe.whitelist()
def get_companies():
    return frappe.get_all("Company", fields=["name", "abbr"], order_by="name")


def _sum_invoices(company, from_date, to_date):
    result = frappe.db.sql("""
        SELECT COALESCE(SUM(grand_total), 0) AS total
        FROM `tabSales Invoice`
        WHERE docstatus=1 AND company=%(company)s
          AND posting_date BETWEEN %(from_date)s AND %(to_date)s
    """, {"company": company, "from_date": from_date, "to_date": to_date}, as_dict=True)
    return flt(result[0].total) if result else 0.0


def _pct_change(old_val, new_val):
    if not old_val:
        return 100.0 if new_val else 0.0
    return round((new_val - old_val) / old_val * 100, 1)


def _ar_aging_summary(company, today):
    rows = frappe.db.sql("""
        SELECT due_date, outstanding_amount
        FROM `tabSales Invoice`
        WHERE docstatus=1 AND company=%(company)s AND outstanding_amount > 0
    """, {"company": company}, as_dict=True)

    buckets = {"current": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "90_plus": 0.0}
    for r in rows:
        amt = flt(r.outstanding_amount)
        if not r.due_date:
            buckets["current"] += amt
            continue
        days_over = (today - getdate(r.due_date)).days
        if days_over <= 0:
            buckets["current"] += amt
        elif days_over <= 30:
            buckets["1_30"] += amt
        elif days_over <= 60:
            buckets["31_60"] += amt
        elif days_over <= 90:
            buckets["61_90"] += amt
        else:
            buckets["90_plus"] += amt
    return buckets


# ─────────────────────────────────────────────────────────────────────────────
# 01 — Sales Command Center
# ─────────────────────────────────────────────────────────────────────────────
@frappe.whitelist()
def get_command_center(company=None):
    company = company or _default_company()
    today = getdate(nowdate())
    week_start = today - timedelta(days=today.weekday())
    last_week_start = week_start - timedelta(days=7)
    last_week_end = week_start - timedelta(days=1)
    thirty_ago = today - timedelta(days=30)

    rev_this = _sum_invoices(company, week_start, today)
    rev_last = _sum_invoices(company, last_week_start, last_week_end)

    top_customers = frappe.db.sql("""
        SELECT customer, customer_name,
               SUM(grand_total) AS revenue,
               COUNT(*) AS inv_count
        FROM `tabSales Invoice`
        WHERE docstatus=1 AND company=%(c)s
          AND posting_date >= %(d)s
        GROUP BY customer
        ORDER BY revenue DESC
        LIMIT 5
    """, {"c": company, "d": thirty_ago}, as_dict=True)

    ar_aging = _ar_aging_summary(company, today)
    ar_total = sum(ar_aging.values())

    so_data = frappe.db.sql("""
        SELECT COUNT(*) AS cnt, COALESCE(SUM(grand_total), 0) AS val
        FROM `tabSales Order`
        WHERE docstatus=1 AND company=%(c)s
          AND status IN ('To Deliver and Bill','To Bill','To Deliver')
    """, {"c": company}, as_dict=True)

    recent_invoices = frappe.db.sql("""
        SELECT name, customer_name, grand_total, outstanding_amount, posting_date, status
        FROM `tabSales Invoice`
        WHERE docstatus=1 AND company=%(c)s
        ORDER BY posting_date DESC, creation DESC
        LIMIT 10
    """, {"c": company}, as_dict=True)

    recent_leads = frappe.db.sql("""
        SELECT name, lead_name, status, creation, source
        FROM `tabCRM Lead`
        ORDER BY creation DESC
        LIMIT 5
    """, {}, as_dict=True)

    return {
        "revenue_this_week":  flt(rev_this),
        "revenue_last_week":  flt(rev_last),
        "revenue_trend":      "up" if rev_this >= rev_last else "down",
        "revenue_change_pct": _pct_change(rev_last, rev_this),
        "top_customers":      top_customers,
        "ar_aging":           ar_aging,
        "ar_total":           ar_total,
        "open_so_count":      cint(so_data[0].cnt) if so_data else 0,
        "open_so_value":      flt(so_data[0].val) if so_data else 0.0,
        "recent_invoices":    recent_invoices,
        "recent_leads":       recent_leads,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 02 — Weekly Cash Projection (all companies)
# ─────────────────────────────────────────────────────────────────────────────
@frappe.whitelist()
def get_cash_projection(company=None):
    today = getdate(nowdate())

    # Build WHERE clause — all companies if none specified
    if company:
        inv_where = "docstatus=1 AND company=%(c)s AND outstanding_amount > 0"
        so_where  = "docstatus=1 AND company=%(c)s AND status IN ('To Deliver and Bill','To Bill','To Deliver')"
        params = {"c": company}
    else:
        inv_where = "docstatus=1 AND outstanding_amount > 0"
        so_where  = "docstatus=1 AND status IN ('To Deliver and Bill','To Bill','To Deliver')"
        params = {}

    # Open invoices
    invoices = frappe.db.sql(f"""
        SELECT name, company, customer_name, grand_total, outstanding_amount,
               due_date, status
        FROM `tabSales Invoice`
        WHERE {inv_where}
        ORDER BY due_date ASC
    """, params, as_dict=True)

    # Open SOs (projected billing)
    sales_orders = frappe.db.sql(f"""
        SELECT name, company, customer_name, grand_total,
               COALESCE(delivery_date, transaction_date) AS due_date,
               status
        FROM `tabSales Order`
        WHERE {so_where}
        ORDER BY delivery_date ASC
    """, params, as_dict=True)

    def bucket(due_date_val):
        if not due_date_val:
            return "week1"
        d = getdate(due_date_val)
        diff = (d - today).days
        if diff < 0:
            return "overdue"
        elif diff <= 6:
            return "week1"
        elif diff <= 13:
            return "week2"
        elif diff <= 20:
            return "week3"
        else:
            return "week4plus"

    result = {"overdue": [], "week1": [], "week2": [], "week3": [], "week4plus": []}

    for inv in invoices:
        b = bucket(inv.due_date)
        result[b].append({
            "type": "invoice",
            "name": inv.name,
            "company": inv.company,
            "customer": inv.customer_name,
            "amount": flt(inv.outstanding_amount),
            "total": flt(inv.grand_total),
            "due_date": str(inv.due_date) if inv.due_date else "",
            "status": inv.status,
        })

    for so in sales_orders:
        b = bucket(so.due_date)
        result[b].append({
            "type": "sales_order",
            "name": so.name,
            "company": so.company,
            "customer": so.customer_name,
            "amount": flt(so.grand_total),
            "total": flt(so.grand_total),
            "due_date": str(so.due_date) if so.due_date else "",
            "status": so.status,
        })

    totals = {k: sum(r["amount"] for r in v) for k, v in result.items()}
    return {"rows": result, "totals": totals}


# ─────────────────────────────────────────────────────────────────────────────
# 03 — Customer Health Scores
# ─────────────────────────────────────────────────────────────────────────────
def _calculate_health_score(customer, company, today):
    """Score 0–100 across four dimensions."""
    score = 0

    # 1. Payment speed (40 pts)
    pay_data = frappe.db.sql("""
        SELECT
            AVG(DATEDIFF(pe.posting_date, si.posting_date)) AS avg_days,
            COUNT(*)                                          AS count
        FROM `tabPayment Entry Reference` per
        JOIN `tabPayment Entry` pe ON pe.name = per.parent
        JOIN `tabSales Invoice`   si ON si.name = per.reference_name
        WHERE pe.docstatus=1 AND pe.company=%(c)s
          AND pe.party=%(cust)s AND pe.party_type='Customer'
          AND pe.posting_date >= %(cutoff)s
    """, {"c": company, "cust": customer, "cutoff": today - timedelta(days=365)}, as_dict=True)

    if pay_data and pay_data[0].count:
        avg_days = flt(pay_data[0].avg_days)
        payment_terms_days = flt(
            frappe.db.get_value("Customer", customer, "payment_terms") or 0
        )
        if not payment_terms_days:
            payment_terms_days = 30  # default assumption
        ratio = avg_days / payment_terms_days if payment_terms_days else 1
        if ratio <= 1.0:
            score += 40
        elif ratio <= 1.5:
            score += 25
        elif ratio <= 2.0:
            score += 10
        # else 0
    else:
        score += 20  # neutral — no payment history yet

    # 2. Order frequency (20 pts)
    order_count = frappe.db.count("Sales Order", {
        "customer": customer, "company": company,
        "docstatus": 1,
        "transaction_date": [">=", str(today - timedelta(days=90))],
    })
    if order_count >= 5:
        score += 20
    elif order_count >= 3:
        score += 15
    elif order_count >= 1:
        score += 10

    # 3. AR balance (20 pts)
    outstanding = flt(frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0) AS total
        FROM `tabSales Invoice`
        WHERE docstatus=1 AND company=%(c)s AND customer=%(cust)s
    """, {"c": company, "cust": customer}, as_dict=True)[0].total)

    avg_invoice = flt(frappe.db.sql("""
        SELECT COALESCE(AVG(grand_total), 0) AS avg
        FROM `tabSales Invoice`
        WHERE docstatus=1 AND company=%(c)s AND customer=%(cust)s
          AND posting_date >= %(cutoff)s
    """, {"c": company, "cust": customer, "cutoff": today - timedelta(days=180)}, as_dict=True)[0].avg)

    if outstanding <= 0:
        score += 20
    elif not avg_invoice or outstanding <= avg_invoice:
        score += 15
    elif outstanding <= avg_invoice * 2:
        score += 8

    # 4. Recency (20 pts)
    last_order = frappe.db.get_value("Sales Order",
        {"customer": customer, "company": company, "docstatus": 1},
        "transaction_date", order_by="transaction_date desc")

    if last_order:
        days_since = (today - getdate(last_order)).days
        if days_since <= 14:
            score += 20
        elif days_since <= 30:
            score += 15
        elif days_since <= 60:
            score += 8
        elif days_since <= 90:
            score += 4

    return min(score, 100)


@frappe.whitelist()
def get_customer_health_scores(company=None):
    company = company or _default_company()
    today = getdate(nowdate())

    customers = frappe.db.sql("""
        SELECT DISTINCT si.customer, c.customer_name
        FROM `tabSales Invoice` si
        JOIN `tabCustomer` c ON c.name = si.customer
        WHERE si.docstatus=1 AND si.company=%(c)s
          AND si.posting_date >= %(cutoff)s
        ORDER BY c.customer_name
    """, {"c": company, "cutoff": today - timedelta(days=365)}, as_dict=True)

    result = []
    for cust in customers:
        score = _calculate_health_score(cust.customer, company, today)
        tier = "green" if score >= 70 else ("amber" if score >= 40 else "red")
        result.append({
            "customer": cust.customer,
            "customer_name": cust.customer_name,
            "score": score,
            "tier": tier,
        })

    result.sort(key=lambda x: x["score"])
    return result


@frappe.whitelist()
def get_single_health_score(customer, company=None):
    company = company or _default_company()
    today = getdate(nowdate())
    score = _calculate_health_score(customer, company, today)
    tier = "green" if score >= 70 else ("amber" if score >= 40 else "red")

    # Build breakdown for hover tooltip
    breakdown = _health_score_breakdown(customer, company, today)
    return {"score": score, "tier": tier, "breakdown": breakdown}


def _health_score_breakdown(customer, company, today):
    """Human-readable breakdown of score components."""
    lines = []

    pay_data = frappe.db.sql("""
        SELECT AVG(DATEDIFF(pe.posting_date, si.posting_date)) AS avg_days, COUNT(*) AS count
        FROM `tabPayment Entry Reference` per
        JOIN `tabPayment Entry` pe ON pe.name = per.parent
        JOIN `tabSales Invoice`   si ON si.name = per.reference_name
        WHERE pe.docstatus=1 AND pe.company=%(c)s AND pe.party=%(cust)s
          AND pe.party_type='Customer'
    """, {"c": company, "cust": customer}, as_dict=True)

    if pay_data and pay_data[0].count:
        lines.append(f"Avg days to pay: {round(flt(pay_data[0].avg_days))} days ({pay_data[0].count} invoices)")
    else:
        lines.append("No payment history")

    order_count = frappe.db.count("Sales Order",
        {"customer": customer, "company": company, "docstatus": 1,
         "transaction_date": [">=", str(today - timedelta(days=90))]})
    lines.append(f"Orders in last 90 days: {order_count}")

    last_order = frappe.db.get_value("Sales Order",
        {"customer": customer, "company": company, "docstatus": 1},
        "transaction_date", order_by="transaction_date desc")
    if last_order:
        days_since = (today - getdate(last_order)).days
        lines.append(f"Last order: {days_since} days ago")
    else:
        lines.append("No orders on record")

    return lines


# ─────────────────────────────────────────────────────────────────────────────
# 04 — Sales Projection by Product Line
# ─────────────────────────────────────────────────────────────────────────────
@frappe.whitelist()
def get_sales_projection(company=None):
    company = company or _default_company()
    today = getdate(nowdate())

    # 8 weeks back for actuals (show last 4 + project next 4)
    weeks = []
    for i in range(-3, 5):
        w_start = today - timedelta(days=today.weekday()) + timedelta(weeks=i)
        w_end = w_start + timedelta(days=6)
        label = "This week" if i == 0 else (
            f"Week +{i}" if i > 0 else f"Week {i}"
        )
        weeks.append({"label": label, "start": w_start, "end": w_end, "future": i > 0})

    result = []
    for week in weeks:
        row = {"label": week["label"], "future": week["future"], "lines": {}}

        for line_name, groups in PRODUCT_LINES.items():
            if not week["future"]:
                # Actuals from invoices
                placeholders = ",".join(["%s"] * len(groups))
                val = frappe.db.sql(f"""
                    SELECT COALESCE(SUM(sii.amount), 0) AS total
                    FROM `tabSales Invoice Item` sii
                    JOIN `tabSales Invoice` si ON si.name = sii.parent
                    WHERE si.docstatus=1 AND si.company=%s
                      AND si.posting_date BETWEEN %s AND %s
                      AND sii.item_group IN ({placeholders})
                """, tuple([company, str(week["start"]), str(week["end"])] + groups))
                row["lines"][line_name] = flt(val[0][0]) if val else 0.0
            else:
                # Projected from open SOs
                placeholders = ",".join(["%s"] * len(groups))
                val = frappe.db.sql(f"""
                    SELECT COALESCE(SUM(soi.amount), 0) AS total
                    FROM `tabSales Order Item` soi
                    JOIN `tabSales Order` so ON so.name = soi.parent
                    WHERE so.docstatus=1 AND so.company=%s
                      AND so.status IN ('To Deliver and Bill','To Bill','To Deliver')
                      AND COALESCE(so.delivery_date, so.transaction_date) BETWEEN %s AND %s
                      AND soi.item_group IN ({placeholders})
                """, tuple([company, str(week["start"]), str(week["end"])] + groups))
                row["lines"][line_name] = flt(val[0][0]) if val else 0.0

        row["total"] = sum(row["lines"].values())
        result.append(row)

    # Max value for chart scaling
    max_val = max((r["total"] for r in result), default=1) or 1
    return {"weeks": result, "product_lines": list(PRODUCT_LINES.keys()), "max_value": max_val}


# ─────────────────────────────────────────────────────────────────────────────
# 09 — AR Aging Heatmap  (uses ERPNext Accounts Receivable Summary engine)
# ─────────────────────────────────────────────────────────────────────────────
@frappe.whitelist()
def get_ar_aging_heatmap(company=None):
    from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import (
        execute,
    )

    company = company or _default_company()
    today_date = getdate(nowdate())

    filters = frappe._dict({
        "company": company,
        "report_date": today_date,
        "ageing_based_on": "Due Date",
        "calculate_ageing_with": "Report Date",
        "range": "30, 60, 90, 120",
        "show_future_payments": 0,
        "show_gl_balance": 0,
        "show_sales_person": 0,
        "party_type": "Customer",
    })

    _columns, data = execute(filters)

    BUCKET_KEYS = ["range1", "range2", "range3", "range4", "range5"]
    grid = []
    col_totals = {k: 0.0 for k in BUCKET_KEYS}
    col_totals["total"] = 0.0
    max_per_bucket = {k: 0.0 for k in BUCKET_KEYS}

    for row in (data or []):
        # Skip summary/total rows the report may append
        if row.get("is_total_row") or not row.get("party"):
            continue
        # Only customers
        if row.get("party_type") and row.get("party_type") != "Customer":
            continue

        outstanding = flt(row.get("outstanding", 0))
        if outstanding <= 0:
            continue

        buckets = {k: flt(row.get(k, 0)) for k in BUCKET_KEYS}
        grid.append({
            "customer":      row.get("party", ""),
            "customer_name": row.get("party_name") or row.get("party", ""),
            **buckets,
            "total": outstanding,
        })

        for k, v in buckets.items():
            col_totals[k] += v
            if v > max_per_bucket[k]:
                max_per_bucket[k] = v
        col_totals["total"] += outstanding

    grid.sort(key=lambda x: -x["total"])

    return {
        "grid": grid,
        "col_totals": col_totals,
        "max_per_bucket": max_per_bucket,
    }
