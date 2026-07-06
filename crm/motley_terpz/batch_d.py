"""
Motley Terpz — Batch D dashboards
  • get_rep_leaderboard   — all-reps performance, Super Admin only (F9)
  • get_upcoming_deliveries — SOs with a delivery date not yet fully shipped (F13)
  • get_purchase_insights  — customers slowing down / shifting mix (F14)
Goal-vs-actual (F10) reuses the existing Sales Target dashboard (Target Detail),
which is already dynamic — surfaced in the CRM sidebar.
"""
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate
from datetime import timedelta

from crm.motley_terpz.access import sees_all_data, sees_all_financials, is_operations_only

WON, LOST = "Won", "Lost"


def _month_bounds():
    today = getdate(nowdate())
    return today.replace(day=1), today


# ── F9 — All-reps leaderboard (Super Admin only) ─────────────────────────────

@frappe.whitelist()
def get_rep_leaderboard(from_date=None, to_date=None):
    if not sees_all_data():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    if not from_date or not to_date:
        f, t = _month_bounds()
        from_date, to_date = str(f), str(t)

    # Rep universe: anyone who owns a deal or is a lead's account owner.
    reps = set(frappe.db.sql_list("SELECT DISTINCT deal_owner FROM `tabCRM Deal` WHERE deal_owner IS NOT NULL AND deal_owner!=''"))
    reps |= set(frappe.db.sql_list(
        "SELECT DISTINCT custom_account_owner FROM `tabCRM Lead` WHERE custom_account_owner IS NOT NULL AND custom_account_owner!=''"))

    rows = []
    for rep in reps:
        esc = frappe.db.escape(rep)
        won = cint(frappe.db.count("CRM Deal", {"deal_owner": rep, "status": WON}))
        lost = cint(frappe.db.count("CRM Deal", {"deal_owner": rep, "status": LOST}))
        pipeline = frappe.db.sql(
            "SELECT COALESCE(SUM(deal_value),0) v, COUNT(*) c FROM `tabCRM Deal` "
            "WHERE deal_owner=%s AND status NOT IN (%s,%s)", (rep, WON, LOST), as_dict=True)[0]
        won_value = flt(frappe.db.sql(
            "SELECT COALESCE(SUM(deal_value),0) FROM `tabCRM Deal` WHERE deal_owner=%s AND status=%s",
            (rep, WON))[0][0])

        # Customers this rep owns (account_manager on customer OR lead account owner)
        cust_sub = (
            f"SELECT name FROM `tabCustomer` WHERE account_manager={esc} "
            f"UNION SELECT custom_erp_customer FROM `tabCRM Lead` "
            f"WHERE custom_account_owner={esc} AND custom_erp_customer IS NOT NULL AND custom_erp_customer!=''")
        revenue = flt(frappe.db.sql(
            f"SELECT COALESCE(SUM(grand_total),0) FROM `tabSales Invoice` "
            f"WHERE docstatus=1 AND customer IN ({cust_sub}) AND posting_date BETWEEN %s AND %s",
            (from_date, to_date))[0][0])
        ar = flt(frappe.db.sql(
            f"SELECT COALESCE(SUM(outstanding_amount),0) FROM `tabSales Invoice` "
            f"WHERE docstatus=1 AND outstanding_amount>0.01 AND customer IN ({cust_sub})")[0][0])

        total_closed = won + lost
        rows.append({
            "rep": rep,
            "rep_name": frappe.utils.get_fullname(rep),
            "deals_won": won, "deals_lost": lost,
            "win_rate": round(won / total_closed * 100, 1) if total_closed else 0.0,
            "open_deals": cint(pipeline.c), "pipeline_value": flt(pipeline.v),
            "won_value": won_value,
            "avg_deal_size": round(won_value / won, 2) if won else 0.0,
            "revenue": revenue, "ar_owned": ar,
        })

    rows.sort(key=lambda r: r["revenue"], reverse=True)
    totals = {
        "revenue": round(sum(r["revenue"] for r in rows), 2),
        "pipeline_value": round(sum(r["pipeline_value"] for r in rows), 2),
        "ar_owned": round(sum(r["ar_owned"] for r in rows), 2),
        "deals_won": sum(r["deals_won"] for r in rows),
    }
    return {"rows": rows, "totals": totals, "from_date": from_date, "to_date": to_date}


# ── F13 — Upcoming deliveries ────────────────────────────────────────────────

@frappe.whitelist()
def get_upcoming_deliveries():
    """Sales Orders with a delivery date that aren't fully delivered yet.
    Past-due (delivery date already passed) are flagged. Reps see only their
    assigned customers' deliveries; Operations/Finance/Admin/Super Admin see all
    (fulfillment needs full visibility across every rep's orders)."""
    today = getdate(nowdate())

    cond = ""
    if not sees_all_financials() and not is_operations_only():
        user = frappe.session.user
        esc = frappe.db.escape(user)
        like = frappe.db.escape(f"%{user}%")
        cond = f" AND (c.`_assign` LIKE {like} OR c.account_manager = {esc})"

    rows = frappe.db.sql(f"""
        SELECT so.name, so.customer_name, so.company, so.delivery_date,
               so.per_delivered, so.grand_total, so.status,
               DATEDIFF(CURDATE(), so.delivery_date) AS days_from_due
        FROM `tabSales Order` so
        JOIN `tabCustomer` c ON c.name = so.customer
        WHERE so.docstatus = 1
          AND so.delivery_date IS NOT NULL
          AND COALESCE(so.per_delivered,0) < 100
          AND so.status NOT IN ('Closed','Completed','Cancelled')
          AND COALESCE(c.is_internal_customer,0) = 0
          {cond}
        ORDER BY so.delivery_date ASC
    """, as_dict=True)

    hide_money = is_operations_only()
    out = []
    for r in rows:
        overdue = getdate(str(r.delivery_date)) < today
        out.append({
            "name": r.name, "customer": r.customer_name, "company": r.company,
            "delivery_date": str(r.delivery_date),
            "per_delivered": flt(r.per_delivered),
            "status": r.status,
            "days_overdue": int(r.days_from_due) if r.days_from_due and r.days_from_due > 0 else 0,
            "overdue": overdue,
            "grand_total": None if hide_money else flt(r.grand_total),
        })
    return {
        "rows": out,
        "overdue_count": sum(1 for r in out if r["overdue"]),
        "total_count": len(out),
    }


# ── F14 — Purchase pattern insights ──────────────────────────────────────────

@frappe.whitelist()
def get_purchase_insights():
    """Flag customers ordering less often than their own history, or whose spend
    has dropped sharply. Scoped: Super Admin/Finance see all; reps see own."""
    today = getdate(nowdate())
    d90 = today - timedelta(days=90)
    d180 = today - timedelta(days=180)

    cond = ""
    if not sees_all_financials():
        user = frappe.session.user
        esc = frappe.db.escape(user)
        like = frappe.db.escape(f"%{user}%")
        cond = f" AND (c.`_assign` LIKE {like} OR c.account_manager = {esc})"

    rows = frappe.db.sql(f"""
        SELECT si.customer, c.customer_name,
               SUM(CASE WHEN si.posting_date >= %(d90)s THEN si.grand_total ELSE 0 END)  AS rev_recent,
               SUM(CASE WHEN si.posting_date >= %(d180)s AND si.posting_date < %(d90)s
                        THEN si.grand_total ELSE 0 END)                                   AS rev_prior,
               COUNT(CASE WHEN si.posting_date >= %(d90)s THEN 1 END)                     AS orders_recent,
               COUNT(CASE WHEN si.posting_date >= %(d180)s AND si.posting_date < %(d90)s
                          THEN 1 END)                                                     AS orders_prior,
               MAX(si.posting_date)                                                       AS last_order
        FROM `tabSales Invoice` si
        JOIN `tabCustomer` c ON c.name = si.customer
        WHERE si.docstatus = 1
          AND COALESCE(c.is_internal_customer,0) = 0
          AND si.posting_date >= %(d180)s
          {cond}
        GROUP BY si.customer
        HAVING orders_prior > 0
    """, {"d90": str(d90), "d180": str(d180)}, as_dict=True)

    flagged = []
    for r in rows:
        reasons = []
        if r.orders_recent == 0:
            reasons.append("No orders in 90 days (was ordering before)")
        elif r.orders_recent < r.orders_prior:
            reasons.append(f"Ordering less often ({r.orders_prior}→{r.orders_recent} in 90d)")
        if flt(r.rev_prior) > 0:
            drop = (flt(r.rev_prior) - flt(r.rev_recent)) / flt(r.rev_prior) * 100
            if drop >= 40:
                reasons.append(f"Spend down {round(drop)}% vs prior 90d")
        if reasons:
            days_since = (today - getdate(str(r.last_order))).days if r.last_order else None
            flagged.append({
                "customer": r.customer, "customer_name": r.customer_name,
                "rev_recent": flt(r.rev_recent), "rev_prior": flt(r.rev_prior),
                "orders_recent": cint(r.orders_recent), "orders_prior": cint(r.orders_prior),
                "days_since_last_order": days_since,
                "reasons": reasons,
            })
    flagged.sort(key=lambda x: x["rev_prior"], reverse=True)
    return {"rows": flagged, "count": len(flagged)}


# ── F22 — Reorder-due reminders (ordering cadence) ───────────────────────────

@frappe.whitelist()
def get_reorder_due():
    """Customers statistically 'due' to reorder: gap since last order exceeds
    their own historical average ordering interval. Scoped like insights."""
    today = getdate(nowdate())
    cond = ""
    if not sees_all_financials():
        user = frappe.session.user
        esc = frappe.db.escape(user)
        like = frappe.db.escape(f"%{user}%")
        cond = f" AND (c.`_assign` LIKE {like} OR c.account_manager = {esc})"

    rows = frappe.db.sql(f"""
        SELECT si.customer, c.customer_name,
               COUNT(*) AS orders,
               MIN(si.posting_date) AS first_order,
               MAX(si.posting_date) AS last_order
        FROM `tabSales Invoice` si
        JOIN `tabCustomer` c ON c.name = si.customer
        WHERE si.docstatus = 1
          AND COALESCE(c.is_internal_customer,0) = 0
          {cond}
        GROUP BY si.customer
        HAVING orders >= 3
    """, as_dict=True)

    due = []
    for r in rows:
        span = (getdate(str(r.last_order)) - getdate(str(r.first_order))).days
        if span <= 0:
            continue
        avg_gap = span / (r.orders - 1)
        days_since = (today - getdate(str(r.last_order))).days
        if avg_gap > 0 and days_since > avg_gap:
            due.append({
                "customer": r.customer, "customer_name": r.customer_name,
                "avg_gap_days": round(avg_gap),
                "days_since_last_order": days_since,
                "overdue_by": round(days_since - avg_gap),
                "orders": cint(r.orders),
                "last_order": str(r.last_order),
            })
    due.sort(key=lambda x: x["overdue_by"], reverse=True)
    return {"rows": due, "count": len(due)}
