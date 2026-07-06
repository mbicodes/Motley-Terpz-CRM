"""
Motley Terpz — central access-control helpers.

Single source of truth for "who sees everything" and "who is fulfillment-only".
Every permission filter and dashboard endpoint should import from here so the
rules stay consistent across the CRM Lead/Deal query conditions and the Sales
Intelligence dashboards.

Visibility model (per client direction, June 2026):
  • Administrator  — sees all data (technical superuser).
  • "Super Admin"  — a custom role (assigned to Matt) that also sees all data.
  • Everyone else  — restricted to their own leads/deals/customers, REGARDLESS
                     of role (Sales Manager included). Only the two above cross
                     into another rep's pipeline.

Operations / Fulfillment ("Stock Manager") must never see AR balances, revenue,
or pricing on the CRM dashboards — see is_operations_only().
"""
import frappe

# Role that grants full cross-rep visibility (in addition to Administrator).
SUPER_ADMIN_ROLE = "Super Admin"

# Roles treated as "Operations / Fulfillment" for AR/pricing redaction.
OPERATIONS_ROLES = {"Stock Manager"}

# Roles that legitimately need AR/pricing visibility. An Operations user who
# also holds one of these is NOT redacted.
AR_PRIVILEGED_ROLES = {
    "Sales Manager", "Finance Manager", "Accounts Manager", "System Manager",
}

# Finance / AR roles — see company-wide AR & financials on the CRM dashboards
# (read-only). This is the AR axis only; it does NOT grant cross-rep visibility
# into other reps' leads/deals/pipeline (that stays Administrator + Super Admin).
FINANCE_ROLES = {"Finance Manager", "Accounts Manager"}


def sees_all_data(user=None):
    """True only for the Administrator account or holders of the Super Admin
    role. These are the only identities allowed to see every rep's data
    (leads, deals, pipeline — everything)."""
    if not user:
        user = frappe.session.user
    if user == "Administrator":
        return True
    return SUPER_ADMIN_ROLE in frappe.get_roles(user)


def sees_all_financials(user=None):
    """True for identities allowed to see company-wide AR / revenue / cash on
    the CRM dashboards: the Administrator, Super Admin, and Finance / Accounts
    Managers. Leads/deals visibility is governed separately by sees_all_data."""
    if not user:
        user = frappe.session.user
    if sees_all_data(user):
        return True
    return bool(set(frappe.get_roles(user)) & FINANCE_ROLES)


def is_operations_only(user=None):
    """True for a fulfillment user (Stock Manager) who holds no role that would
    legitimately expose AR/pricing, and who is not a super user. Used to strip
    financial figures from dashboard responses."""
    if not user:
        user = frappe.session.user
    if sees_all_data(user):
        return False
    roles = set(frappe.get_roles(user))
    if roles & AR_PRIVILEGED_ROLES:
        return False
    return bool(roles & OPERATIONS_ROLES)
