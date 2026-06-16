"""
Motley Terpz — CRM Lead permission filter.

Rules (non-admin users only):
  1. Org-hierarchy scoping (original CRM logic).
  2. Tolling pipeline hidden from users without the "CRM Tolling Access" role.
  3. Ownership scoping: each user sees only leads they own OR unassigned leads.
     A lead assigned to another user is invisible to everyone except that owner.
"""
import frappe


def get_lead_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    # Only the technical Administrator account bypasses all filters.
    # System Manager role alone does NOT bypass — regular staff often hold it.
    if user == "Administrator":
        return ""

    conditions = []

    # 1. Org hierarchy condition (original CRM logic)
    from crm.permissions.org_hierarchy import get_lead_permission_query_conditions as _org
    org_cond = _org(user)
    if org_cond:
        conditions.append(f"({org_cond})")

    # 2. Tolling access control — hide Tolling leads from unauthorised users
    if "CRM Tolling Access" not in frappe.get_roles(user):
        conditions.append(
            "(`tabCRM Lead`.`custom_pipeline` != 'Tolling' "
            "OR `tabCRM Lead`.`custom_pipeline` IS NULL "
            "OR `tabCRM Lead`.`custom_pipeline` = '')"
        )

    # 3. Ownership filter — show only this user's leads + unassigned leads
    escaped = frappe.db.escape(user)
    conditions.append(
        f"(`tabCRM Lead`.`lead_owner` = {escaped} "
        f"OR `tabCRM Lead`.`lead_owner` IS NULL "
        f"OR `tabCRM Lead`.`lead_owner` = '')"
    )

    return " AND ".join(conditions) if conditions else ""
