"""Motley Terpz: stop CRM User-link fields from enforcing User Permissions.

Background
----------
CRM record visibility here is scoped by permission_query_conditions +
has_permission (crm.motley_terpz.*), not by User Permissions. A single stray
`User -> self` User Permission on a rep (applied to all doctypes) therefore
breaks shared visibility: Frappe's link-field user-permission check
(frappe.permissions.check_user_permission_on_link_fields) runs on the parent
doc AND every child row, and blocks any record whose User-link field points to
another user -- e.g. a CRM Status Change Log row owned by a teammate, raising
"You are not allowed to access this ... record because it is linked to User
'x@...' in row 1, field ...".

The canonical Frappe fix is `ignore_user_permissions` on those link fields.
These fields are ownership/actor metadata, so ignoring user permissions on them
is safe and does not weaken the query-condition scoping that actually governs
who sees which leads/deals.
"""

import frappe

FIELDS = {
    "CRM Lead": ["lead_owner"],
    "CRM Deal": ["deal_owner"],
    "CRM Status Change Log": ["log_owner"],
    "CRM Task": ["assigned_to"],
    "CRM Call Log": ["caller", "receiver"],
    "CRM Notification": ["from_user", "to_user"],
    "CRM Territory": ["territory_manager"],
}


def execute():
    for doctype, fieldnames in FIELDS.items():
        if not frappe.db.exists("DocType", doctype):
            continue
        for fieldname in fieldnames:
            existing = frappe.db.get_value(
                "Property Setter",
                {"doc_type": doctype, "field_name": fieldname, "property": "ignore_user_permissions"},
            )
            if existing:
                frappe.db.set_value("Property Setter", existing, "value", "1")
                continue
            frappe.make_property_setter(
                {
                    "doctype": doctype,
                    "fieldname": fieldname,
                    "property": "ignore_user_permissions",
                    "value": 1,
                    "property_type": "Check",
                },
                is_system_generated=False,
            )
    frappe.clear_cache()
