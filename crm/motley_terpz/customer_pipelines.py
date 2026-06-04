"""
Motley Terpz — Pipeline Customer Lists
Returns ERPNext customers filtered by what pipeline they belong to,
along with live AR data from the nightly CRM sync (or computed live).

Pipelines:
  fresh_frozen      – customers with SI items in Fresh Frozen Main (or children)
  rosin_solventless – customers with SI items in Extracts Motley (or children)
  retail_distro     – customers whose customer_group = Retail/Distro (or children)
  tolling           – customers billed toll-processing-fee item code
"""

import frappe
from frappe.utils import flt


EXCLUDED_CUSTOMERS_SQL = """
    AND c.name NOT IN (SELECT name FROM `tabCompany`)
    AND COALESCE(c.is_internal_customer, 0) = 0
    AND (c.represents_company IS NULL OR c.represents_company = '')
"""

PIPELINE_ITEM_GROUPS = {
    "fresh_frozen":      "Fresh Frozen Main",
    "rosin_solventless": "Extracts Motley",
}

TOLLING_ITEM_CODE = "toll-processing-fee"


def _get_descendants(parent_item_group):
    """Recursive CTE to get all child item groups."""
    rows = frappe.db.sql_list("""
        WITH RECURSIVE ig_tree AS (
            SELECT name FROM `tabItem Group` WHERE name = %(parent)s
            UNION ALL
            SELECT ig.name FROM `tabItem Group` ig
            JOIN ig_tree ON ig.parent_item_group = ig_tree.name
        )
        SELECT name FROM ig_tree
    """, {"parent": parent_item_group})
    return rows or [parent_item_group]


def _get_customer_group_descendants(parent_group):
    """Recursive CTE to get all child customer groups."""
    rows = frappe.db.sql_list("""
        WITH RECURSIVE cg_tree AS (
            SELECT name FROM `tabCustomer Group` WHERE name = %(parent)s
            UNION ALL
            SELECT cg.name FROM `tabCustomer Group` cg
            JOIN cg_tree ON cg.parent_customer_group = cg_tree.name
        )
        SELECT name FROM cg_tree
    """, {"parent": parent_group})
    return rows or [parent_group]


def _ar_data_for_customers(customer_names):
    """
    Pull AR data for a list of customers.
    First tries CRM Lead linked fields (nightly sync), then computes live.
    Returns dict keyed by customer name.
    """
    if not customer_names:
        return {}

    # Get from CRM Lead (nightly sync data)
    leads = frappe.db.sql("""
        SELECT
            custom_erp_customer  AS customer,
            custom_ar_balance    AS ar_balance,
            custom_ar_aging_days AS ar_aging_days,
            custom_ar_status     AS ar_status,
            custom_cod_flag      AS cod_flag,
            custom_last_invoice_date   AS last_invoice_date,
            custom_last_invoice_amount AS last_invoice_amount,
            custom_last_payment_date   AS last_payment_date,
            custom_mtd_revenue         AS mtd_revenue,
            custom_trailing_8w_revenue AS trailing_8w_revenue,
            custom_payment_terms       AS payment_terms
        FROM `tabCRM Lead`
        WHERE custom_erp_customer IN %(names)s
          AND custom_erp_customer IS NOT NULL
          AND custom_erp_customer != ''
    """, {"names": tuple(customer_names)}, as_dict=True)

    ar_map = {r.customer: r for r in leads}

    # For any customer not in CRM Lead, compute live AR balance
    missing = [n for n in customer_names if n not in ar_map]
    if missing:
        live = frappe.db.sql("""
            SELECT
                si.customer,
                COALESCE(SUM(si.outstanding_amount), 0)             AS ar_balance,
                COALESCE(MAX(DATEDIFF(CURDATE(), si.due_date)), 0)   AS ar_aging_days
            FROM `tabSales Invoice` si
            WHERE si.customer IN %(names)s
              AND si.docstatus = 1 AND si.outstanding_amount > 0.01
            GROUP BY si.customer
        """, {"names": tuple(missing)}, as_dict=True)

        for r in live:
            bal  = flt(r.ar_balance)
            aging = int(r.ar_aging_days or 0)
            if aging > 90:
                status = "Blocked"
            elif aging > 30:
                status = "Overdue"
            elif bal > 0:
                status = "Watch"
            else:
                status = "Clean"
            ar_map[r.customer] = frappe._dict({
                "customer": r.customer,
                "ar_balance": bal,
                "ar_aging_days": aging,
                "ar_status": status,
                "cod_flag": 0,
                "last_invoice_date": None,
                "last_invoice_amount": 0,
                "last_payment_date": None,
                "mtd_revenue": 0,
                "trailing_8w_revenue": 0,
                "payment_terms": frappe.db.get_value("Customer", r.customer, "payment_terms") or "",
            })

    return ar_map


# ── API endpoints ─────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_pipeline_customers(pipeline, page_length=100):
    """
    Returns customer list with AR data for the given pipeline.
    pipeline: fresh_frozen | rosin_solventless | retail_distro | tolling
    """
    if not frappe.has_permission("Customer", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)

    page_length = int(page_length)
    pipeline = (pipeline or "").strip()

    # ── Step 1: get matching customer names ──────────────────────────────────
    customer_names = []

    if pipeline in ("fresh_frozen", "rosin_solventless"):
        parent_ig = PIPELINE_ITEM_GROUPS[pipeline]
        igs = _get_descendants(parent_ig)
        rows = frappe.db.sql("""
            SELECT DISTINCT si.customer
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON si.name = sii.parent
            JOIN `tabItem` i           ON i.name = sii.item_code
            JOIN `tabCustomer` c       ON c.name = si.customer
            WHERE si.docstatus = 1
              AND i.item_group IN %(igs)s
              {exc}
            LIMIT %(pl)s
        """.format(exc=EXCLUDED_CUSTOMERS_SQL),
            {"igs": tuple(igs), "pl": page_length}, as_dict=True)
        customer_names = [r.customer for r in rows]

    elif pipeline == "retail_distro":
        groups = _get_customer_group_descendants("Retail/Distro")
        rows = frappe.db.sql("""
            SELECT DISTINCT c.name AS customer
            FROM `tabCustomer` c
            WHERE c.customer_group IN %(groups)s
              {exc}
            LIMIT %(pl)s
        """.format(exc=EXCLUDED_CUSTOMERS_SQL.replace("c.name NOT IN", "c.name NOT IN")),
            {"groups": tuple(groups), "pl": page_length}, as_dict=True)
        customer_names = [r.customer for r in rows]

    elif pipeline == "tolling":
        rows = frappe.db.sql("""
            SELECT DISTINCT si.customer
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON si.name = sii.parent
            JOIN `tabCustomer` c       ON c.name = si.customer
            WHERE si.docstatus = 1
              AND sii.item_code = %(toll)s
              {exc}
            LIMIT %(pl)s
        """.format(exc=EXCLUDED_CUSTOMERS_SQL),
            {"toll": TOLLING_ITEM_CODE, "pl": page_length}, as_dict=True)
        customer_names = [r.customer for r in rows]

    else:
        frappe.throw(f"Unknown pipeline: {pipeline}")

    if not customer_names:
        return []

    # ── Step 2: get customer display names ──────────────────────────────────
    name_map = {
        r.name: r.customer_name
        for r in frappe.db.sql(
            "SELECT name, customer_name FROM `tabCustomer` WHERE name IN %(names)s",
            {"names": tuple(customer_names)}, as_dict=True
        )
    }

    # ── Step 3: get AR data ─────────────────────────────────────────────────
    ar_map = _ar_data_for_customers(customer_names)

    # ── Step 4: assemble result ─────────────────────────────────────────────
    result = []
    for cname in customer_names:
        ar = ar_map.get(cname, frappe._dict({}))
        result.append({
            "customer":            cname,
            "customer_name":       name_map.get(cname, cname),
            "ar_status":           ar.get("ar_status") or "—",
            "ar_balance":          flt(ar.get("ar_balance")),
            "ar_aging_days":       int(ar.get("ar_aging_days") or 0),
            "last_invoice_date":   str(ar.get("last_invoice_date") or "")[:10] or None,
            "last_invoice_amount": flt(ar.get("last_invoice_amount")),
            "last_payment_date":   str(ar.get("last_payment_date") or "")[:10] or None,
            "mtd_revenue":         flt(ar.get("mtd_revenue")),
            "trailing_8w_revenue": flt(ar.get("trailing_8w_revenue")),
            "payment_terms":       ar.get("payment_terms") or "",
            "cod_flag":            int(ar.get("cod_flag") or 0),
        })

    # Sort by AR balance descending (most urgent first)
    result.sort(key=lambda x: -x["ar_balance"])
    return result
