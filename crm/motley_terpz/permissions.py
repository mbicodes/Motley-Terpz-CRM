"""
Motley Terpz — CRM Lead permission filter.
Hides Tolling pipeline leads from users without the "CRM Tolling Access" role.
"""
import frappe


def get_lead_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    conditions = []

    # 1. Org hierarchy condition (original CRM logic)
    from crm.permissions.org_hierarchy import get_lead_permission_query_conditions as _org
    org_cond = _org(user)
    if org_cond:
        conditions.append(f"({org_cond})")

    # 2. Tolling access control — hide Tolling leads from unauthorised users
    if user != "Administrator" and "CRM Tolling Access" not in frappe.get_roles(user):
        conditions.append(
            "(`tabCRM Lead`.`custom_pipeline` != 'Tolling' "
            "OR `tabCRM Lead`.`custom_pipeline` IS NULL "
            "OR `tabCRM Lead`.`custom_pipeline` = '')"
        )

    return " AND ".join(conditions) if conditions else ""
