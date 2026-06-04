"""
Motley Terpz & TSBC Ranch — CRM Setup
Runs on after_migrate to ensure all custom fields, lead statuses,
and pipeline Kanban views are present on every install/update.
Safe to call multiple times — all operations are idempotent.
"""
import json
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def run_setup():
    if not frappe.db.exists("DocType", "CRM Lead"):
        return
    create_motley_custom_fields()
    create_lead_statuses()
    create_pipeline_views()
    frappe.db.commit()


# ── Custom Fields ──────────────────────────────────────────────────────────────

def create_motley_custom_fields():
    fields = {
        "CRM Lead": [
            # ── Tab ──────────────────────────────────────────────────────────
            {"fieldname": "custom_motley_tab",          "fieldtype": "Tab Break",     "label": "Motley Terpz",          "insert_after": "net_total"},

            # ── Section A: Identity & Ownership ──────────────────────────────
            {"fieldname": "custom_account_info_section", "fieldtype": "Section Break", "label": "Identity & Ownership",  "insert_after": "custom_motley_tab"},
            {"fieldname": "custom_relationship_tier",   "fieldtype": "Select",        "label": "Relationship Tier",
             "options": "AAA\nAA\nA\nFriends & Family\nWIP\nLead",
             "reqd": 1, "in_list_view": 1, "in_standard_filter": 1, "insert_after": "custom_account_info_section"},
            {"fieldname": "custom_pipeline",            "fieldtype": "Select",        "label": "Pipeline",
             "options": "\nFresh Frozen\nRosin / Solventless\nRetail / Distro\nTolling",
             "in_list_view": 1, "in_standard_filter": 1, "insert_after": "custom_relationship_tier"},
            {"fieldname": "custom_account_owner",       "fieldtype": "Link",          "label": "Account Owner",
             "options": "User", "in_standard_filter": 1, "insert_after": "custom_pipeline"},
            {"fieldname": "custom_company",             "fieldtype": "Select",        "label": "Company",
             "options": "\nTSBC Ranch\nMotley Terpz\nBoth",
             "in_standard_filter": 1, "insert_after": "custom_account_owner"},
            {"fieldname": "custom_revenue_size",        "fieldtype": "Select",        "label": "Revenue Size",
             "options": "\n$25M+\n$5M+\n$1M+\n$500K+\n$100K+\n<$50K\nUnknown",
             "insert_after": "custom_company"},

            # ── Section B: Activity & Behavior ───────────────────────────────
            {"fieldname": "custom_section_activity",    "fieldtype": "Section Break", "label": "Activity & Behavior",   "insert_after": "custom_revenue_size"},
            {"fieldname": "custom_buyer_activity",      "fieldtype": "Select",        "label": "Buyer Activity",
             "options": "\nConsistent\nInconsistent\nDeposit\nNever Purchased\nCollab\nHave not contacted",
             "insert_after": "custom_section_activity"},
            {"fieldname": "custom_last_contact_date",   "fieldtype": "Date",          "label": "Last Contact Date",     "insert_after": "custom_buyer_activity"},
            {"fieldname": "custom_next_followup_date",  "fieldtype": "Date",          "label": "Next Follow-up Date",   "insert_after": "custom_last_contact_date"},
            {"fieldname": "custom_notes",               "fieldtype": "Long Text",     "label": "Notes",                 "insert_after": "custom_next_followup_date"},

            # ── Section C: Flags & Special Handling ──────────────────────────
            {"fieldname": "custom_section_flags",       "fieldtype": "Section Break", "label": "Flags & Special Handling", "insert_after": "custom_notes"},
            {"fieldname": "custom_single_source",       "fieldtype": "Check",         "label": "Single Source",         "insert_after": "custom_section_flags"},
            {"fieldname": "custom_cod_only",            "fieldtype": "Check",         "label": "COD Only",              "insert_after": "custom_single_source"},
            {"fieldname": "custom_no_ocal",             "fieldtype": "Check",         "label": "No-OCAL",               "insert_after": "custom_cod_only"},
            {"fieldname": "custom_col_break_flags",     "fieldtype": "Column Break",  "label": "",                      "insert_after": "custom_no_ocal"},
            {"fieldname": "custom_col_break_flags2",    "fieldtype": "Column Break",  "label": "",                      "insert_after": "custom_col_break_flags"},
            {"fieldname": "custom_account_flags",       "fieldtype": "Small Text",    "label": "Account Flags",
             "description": "Comma-separated: No-OCAL, COD Only, Custom QC Process, Single Source, Do Not Contact",
             "insert_after": "custom_col_break_flags2"},
            {"fieldname": "custom_clickup_link",        "fieldtype": "Data",          "label": "ClickUp Link",          "insert_after": "custom_account_flags"},
            {"fieldname": "custom_slack_channel",       "fieldtype": "Data",          "label": "Slack Channel",         "insert_after": "custom_clickup_link"},

            # ── Section D: Monthly Demand (lbs) ──────────────────────────────
            {"fieldname": "custom_demand_section",      "fieldtype": "Section Break", "label": "Monthly Demand (lbs)",  "collapsible": 1, "insert_after": "custom_slack_channel"},
            {"fieldname": "custom_demand_fresh_frozen", "fieldtype": "Float",         "label": "Fresh Frozen",          "insert_after": "custom_demand_section"},
            {"fieldname": "custom_demand_rosin",        "fieldtype": "Float",         "label": "Rosin",                 "insert_after": "custom_demand_fresh_frozen"},
            {"fieldname": "custom_demand_vrr",          "fieldtype": "Float",         "label": "VRR",                   "insert_after": "custom_demand_rosin"},
            {"fieldname": "custom_demand_food_grade",   "fieldtype": "Float",         "label": "Food Grade",            "insert_after": "custom_demand_vrr"},
            {"fieldname": "custom_demand_bubble",       "fieldtype": "Float",         "label": "Bubble Hash",           "insert_after": "custom_demand_food_grade"},
            {"fieldname": "custom_demand_col_break",    "fieldtype": "Column Break",  "label": "",                      "insert_after": "custom_demand_bubble"},
            {"fieldname": "custom_demand_cpg",          "fieldtype": "Float",         "label": "CPG",                   "insert_after": "custom_demand_col_break"},
            {"fieldname": "custom_demand_bho",          "fieldtype": "Float",         "label": "BHO / Live Resin",      "insert_after": "custom_demand_cpg"},
            {"fieldname": "custom_demand_thca",         "fieldtype": "Float",         "label": "THCA",                  "insert_after": "custom_demand_bho"},
            {"fieldname": "custom_demand_trim",         "fieldtype": "Float",         "label": "Trim / Biomass",        "insert_after": "custom_demand_thca"},
            {"fieldname": "custom_demand_flower",       "fieldtype": "Float",         "label": "Flower / Pre-rolls",    "insert_after": "custom_demand_trim"},
            {"fieldname": "custom_demand_other",        "fieldtype": "Long Text",     "label": "Other Demand Notes",    "insert_after": "custom_demand_flower"},

            # ── Section E: ERPNext — Live Data (read-only) ────────────────────
            {"fieldname": "custom_erpnext_section",     "fieldtype": "Section Break", "label": "ERPNext — Live Data",   "collapsible": 1, "insert_after": "custom_demand_other"},
            {"fieldname": "custom_erp_customer",        "fieldtype": "Link",          "label": "ERPNext Customer",
             "options": "Customer", "insert_after": "custom_erpnext_section"},
            {"fieldname": "custom_ar_balance",          "fieldtype": "Currency",      "label": "AR Balance",            "read_only": 1, "insert_after": "custom_erp_customer"},
            {"fieldname": "custom_ar_aging_days",       "fieldtype": "Int",           "label": "AR Aging (days)",       "read_only": 1, "insert_after": "custom_ar_balance"},
            {"fieldname": "custom_ar_status",           "fieldtype": "Select",        "label": "AR Status",
             "options": "\nClean\nWatch\nOverdue\nBlocked",
             "read_only": 1, "in_list_view": 1, "in_standard_filter": 1, "insert_after": "custom_ar_aging_days"},
            {"fieldname": "custom_cod_flag",            "fieldtype": "Check",         "label": "COD Flag",
             "read_only": 1, "description": "Auto-set from Payment Terms nightly", "insert_after": "custom_ar_status"},
            {"fieldname": "custom_erp_col_break",       "fieldtype": "Column Break",  "label": "",                      "insert_after": "custom_cod_flag"},
            {"fieldname": "custom_last_invoice_date",   "fieldtype": "Date",          "label": "Last Invoice Date",     "read_only": 1, "insert_after": "custom_erp_col_break"},
            {"fieldname": "custom_last_invoice_amount", "fieldtype": "Currency",      "label": "Last Invoice Amount",   "read_only": 1, "insert_after": "custom_last_invoice_date"},
            {"fieldname": "custom_last_payment_date",   "fieldtype": "Date",          "label": "Last Payment Date",     "read_only": 1, "insert_after": "custom_last_invoice_amount"},
            {"fieldname": "custom_mtd_revenue",         "fieldtype": "Currency",      "label": "MTD Revenue",           "read_only": 1, "insert_after": "custom_last_payment_date"},
            {"fieldname": "custom_trailing_8w_revenue", "fieldtype": "Currency",      "label": "8-Week Trailing Revenue","read_only": 1, "insert_after": "custom_mtd_revenue"},
            {"fieldname": "custom_payment_terms",       "fieldtype": "Data",          "label": "Payment Terms",         "read_only": 1, "insert_after": "custom_trailing_8w_revenue"},
            {"fieldname": "custom_last_sync",           "fieldtype": "Datetime",      "label": "Last Synced",           "read_only": 1, "insert_after": "custom_payment_terms"},
        ]
    }
    create_custom_fields(fields, ignore_validate=True)


# ── CRM Lead Statuses ─────────────────────────────────────────────────────────

def create_lead_statuses():
    if not frappe.db.exists("DocType", "CRM Lead Status"):
        return
    statuses = [
        {"lead_status": "Lead",      "type": "Open",    "position": 1, "color": "gray"},
        {"lead_status": "Contacted", "type": "Ongoing", "position": 2, "color": "orange"},
        {"lead_status": "Sample/QC", "type": "Ongoing", "position": 3, "color": "blue"},
        {"lead_status": "Active",    "type": "Ongoing", "position": 4, "color": "green"},
        {"lead_status": "Inactive",  "type": "On Hold", "position": 5, "color": "amber"},
        {"lead_status": "Lost",      "type": "Lost",    "position": 6, "color": "red"},
    ]
    for s in statuses:
        if not frappe.db.exists("CRM Lead Status", s["lead_status"]):
            frappe.get_doc({"doctype": "CRM Lead Status", **s}).insert(ignore_permissions=True)


# ── Pipeline Kanban Views ─────────────────────────────────────────────────────

KANBAN_COLUMNS = json.dumps([
    {"name": "Lead"}, {"name": "Contacted"}, {"name": "Sample/QC"},
    {"name": "Active"}, {"name": "Inactive"}, {"name": "Lost"},
])

PIPELINES = [
    {"label": "Fresh Frozen",       "icon": "❄️", "filter": "Fresh Frozen"},
    {"label": "Rosin / Solventless","icon": "🌿", "filter": "Rosin / Solventless"},
    {"label": "Retail / Distro",    "icon": "🏪", "filter": "Retail / Distro"},
    {"label": "Tolling",            "icon": "⚙️", "filter": "Tolling"},
]

# Customers AR view — list of leads linked to ERPNext customers
CUSTOMERS_COLUMNS = json.dumps([
    {"label": "Account",       "key": "lead_name",                  "type": "Data",     "width": "160px"},
    {"label": "ERP Customer",  "key": "custom_erp_customer",        "type": "Link",     "width": "140px"},
    {"label": "AR Status",     "key": "custom_ar_status",           "type": "Select",   "width": "100px"},
    {"label": "AR Balance",    "key": "custom_ar_balance",          "type": "Currency", "width": "120px"},
    {"label": "Aging (days)",  "key": "custom_ar_aging_days",       "type": "Int",      "width": "100px"},
    {"label": "Last Invoice",  "key": "custom_last_invoice_date",   "type": "Date",     "width": "110px"},
    {"label": "Invoice Amt",   "key": "custom_last_invoice_amount", "type": "Currency", "width": "110px"},
    {"label": "Last Payment",  "key": "custom_last_payment_date",   "type": "Date",     "width": "110px"},
    {"label": "MTD Revenue",   "key": "custom_mtd_revenue",         "type": "Currency", "width": "110px"},
    {"label": "8-Wk Revenue",  "key": "custom_trailing_8w_revenue", "type": "Currency", "width": "110px"},
    {"label": "Payment Terms", "key": "custom_payment_terms",       "type": "Data",     "width": "110px"},
    {"label": "COD",           "key": "custom_cod_flag",            "type": "Check",    "width": "60px"},
])

CUSTOMERS_ROWS = json.dumps([
    "name", "lead_name", "first_name", "custom_erp_customer", "custom_ar_status",
    "custom_ar_balance", "custom_ar_aging_days", "custom_last_invoice_date",
    "custom_last_invoice_amount", "custom_last_payment_date", "custom_mtd_revenue",
    "custom_trailing_8w_revenue", "custom_payment_terms", "custom_cod_flag",
    "custom_account_owner", "_assign", "modified",
])


def create_pipeline_views():
    if not frappe.db.exists("DocType", "CRM View Settings"):
        return

    for p in PIPELINES:
        existing = frappe.db.get_value(
            "CRM View Settings",
            {"label": p["label"], "dt": "CRM Lead", "type": "kanban"},
            "name",
        )
        if existing:
            frappe.db.set_value("CRM View Settings", existing, {
                "user": "", "kanban_columns": KANBAN_COLUMNS,
                "public": 1, "pinned": 0,
            })
        else:
            doc = frappe.new_doc("CRM View Settings")
            doc.label         = p["label"]
            doc.dt            = "CRM Lead"
            doc.type          = "kanban"
            doc.icon          = p["icon"]
            doc.column_field  = "status"
            doc.user          = ""
            doc.filters       = json.dumps({"custom_pipeline": ["=", p["filter"]]})
            doc.kanban_columns = KANBAN_COLUMNS
            doc.kanban_fields  = json.dumps([])
            doc.public         = 1
            doc.pinned         = 0
            doc.insert(ignore_permissions=True)

    # Customers AR view
    if not frappe.db.get_value("CRM View Settings", {"label": "Customers", "dt": "CRM Lead"}, "name"):
        doc = frappe.new_doc("CRM View Settings")
        doc.label             = "Customers"
        doc.dt                = "CRM Lead"
        doc.type              = "list"
        doc.route_name        = "Leads"
        doc.user              = ""
        doc.public            = 1
        doc.pinned            = 0
        doc.filters           = json.dumps({"custom_erp_customer": ["!=", ""]})
        doc.order_by          = "custom_ar_balance desc"
        doc.load_default_columns = 0
        doc.columns           = CUSTOMERS_COLUMNS
        doc.rows              = CUSTOMERS_ROWS
        doc.insert(ignore_permissions=True)
