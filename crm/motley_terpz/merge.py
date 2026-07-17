"""
Motley Terpz — Merge duplicate CRM Leads / Contacts.

Two-step flow, mirroring Salesforce's "merge contacts":
  1. preview(doctype, survivor, duplicate) — field-by-field diff, plus a
     count of linked records (notes/tasks/calls/deals) that will follow
     the duplicate into the survivor.
  2. execute(doctype, survivor, duplicate, resolved_values) — writes the
     chosen field values onto the survivor, then uses Frappe's own
     rename-merge engine (frappe.rename_doc(..., merge=True)) to re-point
     every Link/Dynamic Link reference (notes, tasks, call logs, deal
     contacts, communications, ...) from the duplicate to the survivor,
     and deletes the duplicate.

Child table rows (e.g. line items) on the duplicate are NOT copied over —
only linked *records* (which reference this doc via reference_docname)
follow. This matches how core Frappe/ERPNext "Merge with existing"
behaves everywhere else in the system.
"""

import json

import frappe
from frappe.utils import cstr

MERGEABLE_DOCTYPES = {"CRM Lead", "Contact"}

SKIP_FIELDTYPES = {
    "Section Break", "Column Break", "Tab Break", "HTML", "Button",
    "Table", "Table MultiSelect", "Fold", "Heading",
}

SKIP_FIELDS = {
    "name", "owner", "creation", "modified", "modified_by", "idx",
    "docstatus", "naming_series",
}


def _check_access(doctype):
    if doctype not in MERGEABLE_DOCTYPES:
        frappe.throw(f"Merge is not supported for {doctype}")
    roles = set(frappe.get_roles())
    if not ({"System Manager", "Sales Manager"} & roles):
        frappe.throw("Not permitted to merge records", frappe.PermissionError)


def _doc_title(doc):
    if doc.doctype == "CRM Lead":
        return doc.lead_name or doc.name
    if doc.doctype == "Contact":
        return doc.get("full_name") or doc.name
    return doc.name


def _linked_record_counts(doctype, name):
    """Records that will follow this document into the survivor on merge."""
    counts = {
        "notes": frappe.db.count("FCRM Note", {"reference_doctype": doctype, "reference_docname": name}),
        "tasks": frappe.db.count("CRM Task", {"reference_doctype": doctype, "reference_docname": name}),
        "calls": frappe.db.count("CRM Call Log", {"reference_doctype": doctype, "reference_docname": name}),
    }
    if doctype == "CRM Lead":
        counts["deals"] = frappe.db.count("CRM Deal", {"lead": name})
    if doctype == "Contact":
        counts["deals"] = frappe.db.count("CRM Contacts", {"contact": name})
    return counts


@frappe.whitelist()
def preview(doctype, survivor, duplicate):
    _check_access(doctype)
    if survivor == duplicate:
        frappe.throw("Pick two different records to merge")

    meta = frappe.get_meta(doctype)
    survivor_doc = frappe.get_doc(doctype, survivor)
    duplicate_doc = frappe.get_doc(doctype, duplicate)

    fields = []
    for df in meta.fields:
        if df.fieldtype in SKIP_FIELDTYPES or df.fieldname in SKIP_FIELDS:
            continue
        if df.read_only:
            # Usually synced from a child table (e.g. Contact.email_id from
            # email_ids) — not safely settable directly, so not mergeable here.
            continue
        s_val = survivor_doc.get(df.fieldname)
        d_val = duplicate_doc.get(df.fieldname)
        if cstr(s_val) == cstr(d_val):
            continue
        fields.append({
            "fieldname": df.fieldname,
            "label": df.label or df.fieldname,
            "fieldtype": df.fieldtype,
            "survivor_value": s_val,
            "duplicate_value": d_val,
            "suggested": "duplicate" if (not s_val and d_val) else "survivor",
        })

    return {
        "survivor": {"name": survivor_doc.name, "title": _doc_title(survivor_doc)},
        "duplicate": {"name": duplicate_doc.name, "title": _doc_title(duplicate_doc)},
        "fields": fields,
        "linked_records": _linked_record_counts(doctype, duplicate),
    }


@frappe.whitelist()
def execute(doctype, survivor, duplicate, resolved_values=None):
    _check_access(doctype)
    if survivor == duplicate:
        frappe.throw("Pick two different records to merge")

    survivor_doc = frappe.get_doc(doctype, survivor)
    if not survivor_doc.has_permission("write"):
        frappe.throw("No write permission on the surviving record", frappe.PermissionError)
    if not frappe.get_doc(doctype, duplicate).has_permission("delete"):
        frappe.throw("No delete permission on the duplicate record", frappe.PermissionError)

    if isinstance(resolved_values, str):
        resolved_values = json.loads(resolved_values or "{}")

    if resolved_values:
        for fieldname, value in resolved_values.items():
            survivor_doc.set(fieldname, value)
        survivor_doc.save()

    frappe.rename_doc(doctype, duplicate, survivor, merge=True, force=True)
    frappe.db.commit()

    return {"name": survivor}
