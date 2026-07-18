"""
Motley Terpz — Commercial snapshot for the CRM Deal view.

Surfaces the ERPNext-side facts a rep needs without leaving the CRM:
  - the account's current AR balance + aging (informational only — no
    gating/blocking; judgment stays with the rep/management)
  - license status (number / type / expiry) from the CRM Organization,
    with a computed Expired / Expiring Soon / Valid badge
  - the most recent Delivery Note's manifest / logistics status
  - live on-hand stock (and any Pre-Order Only flag) for the Item linked
    on the deal (doc.custom_item)

A Deal's `organization` field is the CRM Organization's name, which is
also used verbatim as the ERPNext Customer name when the deal converts
(see erpnext_crm_settings.create_customer_in_erpnext) — so matching by
that same name is consistent with how this fork already links the two.
"""

import frappe
from frappe.utils import add_days, flt, getdate, nowdate


def _resolve_customer(organization):
    """Best-effort match of a CRM Organization name to an ERPNext Customer,
    mirroring the exact-name convention used when a deal converts."""
    if not organization:
        return None
    name = frappe.db.get_value("Customer", organization, "name")
    if name:
        return name
    return frappe.db.get_value("Customer", {"customer_name": organization}, "name")


def _is_internal(customer):
    if not customer:
        return False
    row = frappe.db.get_value(
        "Customer", customer, ["is_internal_customer", "represents_company"], as_dict=True
    )
    if not row:
        return False
    return bool(row.is_internal_customer) or bool(row.represents_company)


def _ar_summary(customer):
    if not customer or _is_internal(customer):
        return None

    rows = frappe.db.sql(
        """
        SELECT outstanding_amount, due_date
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND customer = %(customer)s AND outstanding_amount > 0.01
        """,
        {"customer": customer},
        as_dict=True,
    )
    today = getdate(nowdate())
    buckets = {"current": 0.0, "0_30": 0.0, "30_60": 0.0, "60_90": 0.0, "90_plus": 0.0}
    total = 0.0
    for r in rows:
        amt = flt(r.outstanding_amount)
        total += amt
        due = getdate(r.due_date) if r.due_date else today
        days_over = (today - due).days
        if days_over <= 0:
            buckets["current"] += amt
        elif days_over <= 30:
            buckets["0_30"] += amt
        elif days_over <= 60:
            buckets["30_60"] += amt
        elif days_over <= 90:
            buckets["60_90"] += amt
        else:
            buckets["90_plus"] += amt

    return {
        "customer": customer,
        "outstanding_total": round(total, 2),
        "buckets": {k: round(v, 2) for k, v in buckets.items()},
        "overdue_total": round(total - buckets["current"], 2),
        "invoice_count": len(rows),
    }


def _license_status(organization):
    if not organization:
        return None
    org = frappe.db.get_value(
        "CRM Organization", organization,
        ["custom_license_number", "custom_license_type", "custom_license_expiry"],
        as_dict=True,
    )
    if not org:
        return None

    expiry = org.custom_license_expiry
    status = "not_set"
    days_to_expiry = None
    if expiry:
        days_to_expiry = (getdate(expiry) - getdate(nowdate())).days
        if days_to_expiry < 0:
            status = "expired"
        elif days_to_expiry <= 30:
            status = "expiring_soon"
        else:
            status = "valid"

    return {
        "license_number": org.custom_license_number or "",
        "license_type": org.custom_license_type or "",
        "expiry": str(expiry) if expiry else None,
        "days_to_expiry": days_to_expiry,
        "status": status,
    }


def _manifest_status(customer):
    """Logistic status lives on Sales Order (custom_logistic_status); the
    actual manifest file lives on Delivery Note (custom_manifest) — pull
    the most recent of each independently since one can exist without
    the other (e.g. a Sales Order not yet shipped has no Delivery Note)."""
    if not customer or _is_internal(customer):
        return None

    so = frappe.db.get_value(
        "Sales Order",
        {"customer": customer, "docstatus": ["!=", 2]},
        ["name", "transaction_date", "status", "custom_logistic_status"],
        as_dict=True,
        order_by="transaction_date desc, creation desc",
    )
    dn = frappe.db.get_value(
        "Delivery Note",
        {"customer": customer, "docstatus": ["!=", 2]},
        ["name", "posting_date", "status", "custom_manifest"],
        as_dict=True,
        order_by="posting_date desc, creation desc",
    )
    if not so and not dn:
        return None

    return {
        "sales_order": so.name if so else None,
        "logistic_status": (so.custom_logistic_status or "") if so else "",
        "delivery_note": dn.name if dn else None,
        "delivery_date": str(dn.posting_date) if dn and dn.posting_date else None,
        "manifest_url": dn.custom_manifest if dn else None,
    }


def _stock_snapshot(item_code):
    if not item_code:
        return None
    item = frappe.db.get_value(
        "Item", item_code, ["item_name", "stock_uom", "custom_pre_order_only", "disabled"], as_dict=True
    )
    if not item:
        return None
    qty = frappe.db.sql(
        "SELECT COALESCE(SUM(actual_qty), 0) FROM `tabBin` WHERE item_code = %(item_code)s",
        {"item_code": item_code},
    )[0][0]
    return {
        "item_code": item_code,
        "item_name": item.item_name,
        "stock_uom": item.stock_uom,
        "actual_qty": flt(qty),
        "pre_order_only": bool(item.custom_pre_order_only),
        "disabled": bool(item.disabled),
    }


@frappe.whitelist()
def get_deal_commercial_snapshot(deal_name):
    if not frappe.has_permission("CRM Deal", "read", doc=deal_name):
        frappe.throw("Not permitted", frappe.PermissionError)

    deal = frappe.db.get_value(
        "CRM Deal", deal_name, ["organization", "custom_item"], as_dict=True
    )
    if not deal:
        frappe.throw(f"Deal {deal_name} not found")

    customer = _resolve_customer(deal.organization)

    return {
        "organization": deal.organization,
        "customer": customer,
        "ar": _ar_summary(customer),
        "license": _license_status(deal.organization),
        "manifest": _manifest_status(customer),
        "stock": _stock_snapshot(deal.custom_item),
    }
