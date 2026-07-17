"""Motley Terpz — notification cleanup.

The stock panel can only mark notifications as read; read items still pile
up in the list. This gives users a true "Clear all" for their own
notifications.
"""

import frappe


@frappe.whitelist()
def clear_all():
    """Delete ALL of the current user's CRM notifications."""
    user = frappe.session.user
    names = frappe.get_all("CRM Notification", filters={"to_user": user}, pluck="name")
    for name in names:
        frappe.delete_doc("CRM Notification", name, ignore_permissions=True)
    return len(names)
