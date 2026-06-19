"""
Motley Terpz — Pipeline Health Dashboard API
Aggregates CRM Lead metrics per pipeline for Matt's health dashboard.
"""

import frappe
from frappe.utils import flt, nowdate, add_days, getdate
from crm.motley_terpz.sales_intelligence import _is_manager, _lead_cond


PIPELINES = [
    {"key": "fresh_frozen",      "label": "Fresh Frozen",        "icon": "❄️"},
    {"key": "rosin_solventless", "label": "Rosin / Solventless", "icon": "🌿"},
    {"key": "retail_distro",     "label": "Retail / Distro",     "icon": "🏪"},
    {"key": "tolling",           "label": "Tolling",             "icon": "⚙️"},
]

PIPELINE_FILTER_MAP = {
    "fresh_frozen":      "Fresh Frozen",
    "rosin_solventless": "Rosin / Solventless",
    "retail_distro":     "Retail / Distro",
    "tolling":           "Tolling",
}


@frappe.whitelist()
def get_pipeline_health():
    """
    Returns per-pipeline health metrics + a company-wide summary.
    """
    today = getdate(nowdate())
    week_ago      = str(add_days(today, -7))
    month_ago_30  = str(add_days(today, -30))

    result = {
        "pipelines": [],
        "summary": {},
    }

    total_leads       = 0
    total_active      = 0
    total_ar          = 0.0
    total_ar_overdue  = 0.0
    total_no_contact  = 0
    total_new_week    = 0

    lc = _lead_cond()

    for p in PIPELINES:
        pipeline_value = PIPELINE_FILTER_MAP[p["key"]]

        # ── Stage counts ──────────────────────────────────────────────────────
        stage_rows = frappe.db.sql(f"""
            SELECT status, COUNT(*) AS cnt
            FROM `tabCRM Lead`
            WHERE custom_pipeline = %(pipeline)s
              {lc}
            GROUP BY status
        """, {"pipeline": pipeline_value}, as_dict=True)

        stage_counts = {r.status: r.cnt for r in stage_rows}
        lead_count   = sum(stage_counts.values())
        active_count = stage_counts.get("Active", 0)

        # ── New leads this week ───────────────────────────────────────────────
        new_week = frappe.db.sql(f"""
            SELECT COUNT(*) AS cnt
            FROM `tabCRM Lead`
            WHERE custom_pipeline = %(pipeline)s
              AND creation >= %(week_ago)s
              {lc}
        """, {"pipeline": pipeline_value, "week_ago": week_ago}, as_dict=True)[0].cnt or 0

        # ── No contact in 30+ days ────────────────────────────────────────────
        no_contact = frappe.db.sql(f"""
            SELECT COUNT(*) AS cnt
            FROM `tabCRM Lead`
            WHERE custom_pipeline = %(pipeline)s
              AND status NOT IN ('Lost', 'Inactive')
              AND (custom_last_contact_date IS NULL
                   OR custom_last_contact_date < %(month_ago)s)
              {lc}
        """, {"pipeline": pipeline_value, "month_ago": month_ago_30}, as_dict=True)[0].cnt or 0

        # ── AR data via linked CRM leads ──────────────────────────────────────
        ar_rows = frappe.db.sql(f"""
            SELECT
                COALESCE(SUM(l.custom_ar_balance), 0)     AS total_ar,
                COALESCE(SUM(
                    CASE WHEN l.custom_ar_aging_days > 30
                         THEN l.custom_ar_balance ELSE 0 END
                ), 0) AS overdue_ar
            FROM `tabCRM Lead` l
            WHERE l.custom_pipeline = %(pipeline)s
              AND l.custom_ar_balance > 0
              {lc}
        """, {"pipeline": pipeline_value}, as_dict=True)

        pipeline_ar         = flt(ar_rows[0].total_ar) if ar_rows else 0.0
        pipeline_ar_overdue = flt(ar_rows[0].overdue_ar) if ar_rows else 0.0

        # ── Top active leads (most recent contact) ────────────────────────────
        top_leads = frappe.db.sql(f"""
            SELECT
                l.name,
                l.lead_name,
                l.status,
                l.custom_relationship_tier  AS tier,
                l.custom_ar_balance         AS ar_balance,
                l.custom_ar_status          AS ar_status,
                l.custom_last_contact_date  AS last_contact_date,
                l.custom_next_followup_date AS next_followup_date
            FROM `tabCRM Lead` l
            WHERE l.custom_pipeline = %(pipeline)s
              AND l.status = 'Active'
              {lc}
            ORDER BY l.custom_ar_balance DESC
            LIMIT 8
        """, {"pipeline": pipeline_value}, as_dict=True)

        # ── Overdue follow-ups ────────────────────────────────────────────────
        overdue_followups = frappe.db.sql(f"""
            SELECT COUNT(*) AS cnt
            FROM `tabCRM Lead`
            WHERE custom_pipeline = %(pipeline)s
              AND custom_next_followup_date IS NOT NULL
              AND custom_next_followup_date < %(today)s
              AND status NOT IN ('Lost', 'Inactive')
              {lc}
        """, {"pipeline": pipeline_value, "today": str(today)}, as_dict=True)[0].cnt or 0

        result["pipelines"].append({
            "key":               p["key"],
            "label":             p["label"],
            "icon":              p["icon"],
            "lead_count":        lead_count,
            "active_count":      active_count,
            "stage_counts":      stage_counts,
            "new_this_week":     new_week,
            "no_contact_30d":    no_contact,
            "overdue_followups": overdue_followups,
            "total_ar":          pipeline_ar,
            "overdue_ar":        pipeline_ar_overdue,
            "top_leads":         top_leads,
        })

        total_leads      += lead_count
        total_active     += active_count
        total_ar         += pipeline_ar
        total_ar_overdue += pipeline_ar_overdue
        total_no_contact += no_contact
        total_new_week   += new_week

    result["summary"] = {
        "total_leads":       total_leads,
        "total_active":      total_active,
        "total_ar":          total_ar,
        "total_ar_overdue":  total_ar_overdue,
        "total_no_contact":  total_no_contact,
        "new_this_week":     total_new_week,
    }

    return result
