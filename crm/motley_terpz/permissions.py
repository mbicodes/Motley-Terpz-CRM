"""
Motley Terpz — CRM Lead permission filter.

Rules (non-superuser users only):
  1. Org-hierarchy scoping (original CRM logic).
  2. Tolling pipeline hidden from users without the "CRM Tolling Access" role.
  3. Ownership scoping: each user sees only leads they own OR unassigned leads.
     A lead assigned to another user is invisible to everyone except that owner.

Full cross-rep visibility is limited to the Administrator account and holders of
the "Super Admin" role — see crm.motley_terpz.access.sees_all_data.
"""
import frappe

from crm.motley_terpz.access import sees_all_data, visible_owners


def get_lead_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    # Only the Administrator account and Super Admin role bypass all filters.
    # Sales/System/Accounts Manager roles alone do NOT bypass.
    if sees_all_data(user):
        return ""

    conditions = []

    # 1. Org hierarchy condition (original CRM logic), widened across the user's
    #    shared visibility group so group members see each other's leads.
    from crm.permissions.org_hierarchy import get_lead_permission_query_conditions as _org
    org_parts = [p for p in (_org(o) for o in visible_owners(user)) if p]
    if org_parts:
        conditions.append("(" + " OR ".join(f"({p})" for p in org_parts) + ")")

    # 2. Tolling access control — hide Tolling leads from unauthorised users
    if "CRM Tolling Access" not in frappe.get_roles(user):
        conditions.append(
            "(`tabCRM Lead`.`custom_pipeline` != 'Tolling' "
            "OR `tabCRM Lead`.`custom_pipeline` IS NULL "
            "OR `tabCRM Lead`.`custom_pipeline` = '')"
        )

    # 3. Ownership filter — show leads owned by anyone in the user's shared
    #    visibility group (usually just the user) + unassigned leads.
    owner_in = ", ".join(frappe.db.escape(o) for o in visible_owners(user))
    conditions.append(
        f"(`tabCRM Lead`.`lead_owner` IN ({owner_in}) "
        f"OR `tabCRM Lead`.`lead_owner` IS NULL "
        f"OR `tabCRM Lead`.`lead_owner` = '')"
    )

    return " AND ".join(conditions) if conditions else ""


# ── CRM Deal ownership scoping ──────────────────────────────────────────────
# Mirrors the lead rules: only the Administrator account and Super Admin role
# see every deal. Every other user (System/Sales Manager roles included) sees
# only deals they own (deal_owner) or that are assigned to them via Frappe's
# assignment system (_assign). A deal owned/assigned to someone else is invisible.

def get_deal_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    if sees_all_data(user):
        return ""

    owners = visible_owners(user)
    owner_in = ", ".join(frappe.db.escape(o) for o in owners)
    assign_likes = " OR ".join(
        f"`tabCRM Deal`.`_assign` LIKE {frappe.db.escape('%' + o + '%')}" for o in owners
    )
    return f"(`tabCRM Deal`.`deal_owner` IN ({owner_in}) OR {assign_likes})"


def has_deal_permission(doc, ptype, user):
    if not user:
        user = frappe.session.user

    if sees_all_data(user):
        return True

    # Allow creating new deals; ownership is enforced once saved.
    if ptype == "create":
        return True

    owners = visible_owners(user)
    if doc.get("deal_owner") in owners:
        return True

    assign = doc.get("_assign") or ""
    return any(o in assign for o in owners)
