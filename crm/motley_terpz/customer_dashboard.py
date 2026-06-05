"""
Motley Terpz — Customer Dashboard API
Fetches Sales Orders, Sales Invoices, and Delivery Notes for a given customer.
"""
import frappe
from frappe.utils import flt

PAGE_SIZE = 15

@frappe.whitelist()
def get_customer_docs(customer, doctype, page=1):
    if not frappe.has_permission(doctype, "read"):
        frappe.throw("Not permitted", frappe.PermissionError)

    page = int(page or 1)
    offset = (page - 1) * PAGE_SIZE

    FIELD_MAP = {
        "Sales Order": {
            "date_field": "transaction_date",
            "fields": ["name", "transaction_date", "status", "grand_total", "advance_paid", "delivery_date"],
            "columns": [
                {"key": "name",             "label": "Order #"},
                {"key": "transaction_date", "label": "Date"},
                {"key": "status",           "label": "Status"},
                {"key": "grand_total",      "label": "Total",        "currency": True},
                {"key": "advance_paid",     "label": "Advance Paid", "currency": True},
                {"key": "delivery_date",    "label": "Delivery Date"},
            ],
        },
        "Sales Invoice": {
            "date_field": "posting_date",
            "fields": ["name", "posting_date", "due_date", "status", "grand_total", "outstanding_amount"],
            "columns": [
                {"key": "name",               "label": "Invoice #"},
                {"key": "posting_date",       "label": "Date"},
                {"key": "due_date",           "label": "Due Date"},
                {"key": "status",             "label": "Status"},
                {"key": "grand_total",        "label": "Total",       "currency": True},
                {"key": "outstanding_amount", "label": "Outstanding", "currency": True},
            ],
        },
        "Delivery Note": {
            "date_field": "posting_date",
            "fields": ["name", "posting_date", "status", "grand_total"],
            "columns": [
                {"key": "name",         "label": "DN #"},
                {"key": "posting_date", "label": "Date"},
                {"key": "status",       "label": "Status"},
                {"key": "grand_total",  "label": "Total", "currency": True},
            ],
        },
    }

    if doctype not in FIELD_MAP:
        frappe.throw(f"Unsupported doctype: {doctype}")

    cfg = FIELD_MAP[doctype]
    date_field = cfg["date_field"]
    fields_sql = ", ".join(cfg["fields"])

    rows = frappe.db.sql(f"""
        SELECT {fields_sql}
        FROM `tab{doctype}`
        WHERE customer = %(customer)s AND docstatus IN (0, 1)
        ORDER BY {date_field} DESC, name DESC
        LIMIT %(limit)s OFFSET %(offset)s
    """, {"customer": customer, "limit": PAGE_SIZE, "offset": offset}, as_dict=True)

    total = frappe.db.sql(f"""
        SELECT COUNT(*) AS cnt FROM `tab{doctype}`
        WHERE customer = %(customer)s AND docstatus IN (0, 1)
    """, {"customer": customer}, as_dict=True)[0].cnt

    import math
    return {
        "rows":        [dict(r) for r in rows],
        "total":       total,
        "page":        page,
        "page_size":   PAGE_SIZE,
        "total_pages": max(1, math.ceil(total / PAGE_SIZE)),
        "columns":     cfg["columns"],
    }


@frappe.whitelist()
def get_customer_info(customer):
    if not frappe.has_permission("Customer", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)

    c = frappe.db.get_value("Customer", customer,
        ["customer_name", "customer_group", "payment_terms", "is_frozen"], as_dict=True)
    if not c:
        frappe.throw(f"Customer not found: {customer}")

    ar = frappe.db.get_value("CRM Lead", {"custom_erp_customer": customer},
        ["custom_ar_balance", "custom_ar_aging_days", "custom_ar_status",
         "custom_last_payment_date", "custom_mtd_revenue"], as_dict=True) or {}

    return {
        "customer":       customer,
        "customer_name":  c.customer_name,
        "customer_group": c.customer_group or "",
        "payment_terms":  c.payment_terms or "",
        "is_frozen":      bool(c.is_frozen),
        "ar_balance":     flt(ar.get("custom_ar_balance")),
        "ar_aging_days":  int(ar.get("custom_ar_aging_days") or 0),
        "ar_status":      ar.get("custom_ar_status") or "—",
        "last_payment":   str(ar.get("custom_last_payment_date") or "")[:10] or None,
        "mtd_revenue":    flt(ar.get("custom_mtd_revenue")),
    }
