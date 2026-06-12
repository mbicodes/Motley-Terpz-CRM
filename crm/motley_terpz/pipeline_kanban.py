"""
Motley Terpz — Pipeline Kanban Board API
Serves the four deal pipeline kanban boards:
  fresh_frozen | rosin | distro | tolling
"""

import frappe
from frappe.utils import flt, nowdate


# ── Stage definitions per pipeline ──────────────────────────────────────────

PIPELINE_CONFIG = {
    "fresh_frozen": {
        "label": "Fresh Frozen",
        "pipeline_type": "Fresh Frozen",
        "stages": [
            {"name": "Inquiry",        "color": "blue"},
            {"name": "Sampling",       "color": "purple"},
            {"name": "Pricing",        "color": "yellow"},
            {"name": "Negotiating",    "color": "orange"},
            {"name": "Active Account", "color": "green"},
            {"name": "Closed Lost",    "color": "red"},
        ],
    },
    "rosin": {
        "label": "Solventless / Rosin",
        "pipeline_type": "Solventless / Rosin",
        "stages": [
            {"name": "Inquiry",        "color": "blue"},
            {"name": "Sampling",       "color": "purple"},
            {"name": "Pricing",        "color": "yellow"},
            {"name": "Negotiating",    "color": "orange"},
            {"name": "Active Account", "color": "green"},
            {"name": "Closed Lost",    "color": "red"},
        ],
    },
    "distro": {
        "label": "Distribution",
        "pipeline_type": "Distribution",
        "stages": [
            {"name": "Inquiry",          "color": "blue"},
            {"name": "License Verified", "color": "purple"},
            {"name": "Territory Agreed", "color": "yellow"},
            {"name": "Trial Order",      "color": "orange"},
            {"name": "Active Account",   "color": "green"},
            {"name": "Closed Lost",      "color": "red"},
        ],
    },
    "tolling": {
        "label": "Tolling",
        "pipeline_type": "Tolling",
        "stages": [
            {"name": "Inquiry",        "color": "blue"},
            {"name": "Material Reviewed", "color": "purple"},
            {"name": "Rate Agreed",    "color": "yellow"},
            {"name": "Contract Sent",  "color": "orange"},
            {"name": "Active Tolling", "color": "green"},
            {"name": "Completed",      "color": "gray"},
            {"name": "Closed Lost",    "color": "red"},
        ],
    },
}

# Fields fetched from CRM Deal for kanban cards
BASE_FIELDS = [
    "name", "organization", "deal_owner", "deal_value", "expected_closure_date",
    "custom_pipeline_type", "custom_pipeline_stage",
    "modified", "creation",
]
TOLLING_FIELDS = [
    "custom_input_material_type", "custom_lbs_per_run",
    "custom_rate_per_lb", "custom_byo_flag", "custom_work_order",
    "custom_run_frequency",
]
FF_ROSIN_FIELDS = ["custom_strain_name", "custom_available_lbs", "custom_target_output_g"]
DISTRO_FIELDS   = ["custom_license_number", "custom_license_verified"]


def _deal_fields(pipeline_key):
    extra = {
        "fresh_frozen": FF_ROSIN_FIELDS,
        "rosin":        FF_ROSIN_FIELDS,
        "distro":       DISTRO_FIELDS,
        "tolling":      TOLLING_FIELDS,
    }.get(pipeline_key, [])
    return BASE_FIELDS + extra


@frappe.whitelist()
def get_pipeline_config(pipeline):
    if pipeline not in PIPELINE_CONFIG:
        frappe.throw(f"Unknown pipeline: {pipeline}")
    cfg = PIPELINE_CONFIG[pipeline]
    return {
        "label": cfg["label"],
        "stages": cfg["stages"],
        "pipeline_type": cfg["pipeline_type"],
    }


@frappe.whitelist()
def get_pipeline_deals(pipeline):
    """
    Returns deals grouped by stage for a given pipeline key.
    {
        "stages": [...],
        "columns": { stage_name: [deal, ...], ... }
    }
    """
    if pipeline not in PIPELINE_CONFIG:
        frappe.throw(f"Unknown pipeline: {pipeline}")

    cfg = PIPELINE_CONFIG[pipeline]
    pipeline_type = cfg["pipeline_type"]
    fields = _deal_fields(pipeline)

    deals = frappe.get_all(
        "CRM Deal",
        filters={"custom_pipeline_type": pipeline_type},
        fields=fields,
        order_by="modified desc",
        limit=500,
    )

    # Fetch organization logos in bulk
    org_names = list({d.organization for d in deals if d.organization})
    org_logo_map = {}
    if org_names:
        rows = frappe.get_all(
            "CRM Organization",
            filters={"name": ["in", org_names]},
            fields=["name", "organization_logo"],
        )
        org_logo_map = {r.name: r.organization_logo for r in rows}

    # Fetch owner names in bulk
    owner_ids = list({d.deal_owner for d in deals if d.deal_owner})
    owner_map = {}
    if owner_ids:
        rows = frappe.get_all(
            "User",
            filters={"name": ["in", owner_ids]},
            fields=["name", "full_name", "user_image"],
        )
        owner_map = {r.name: r for r in rows}

    # Group by stage; unknown stages → first stage
    stage_names = [s["name"] for s in cfg["stages"]]
    columns = {s: [] for s in stage_names}
    uncategorized = []

    for deal in deals:
        stage = deal.get("custom_pipeline_stage") or ""
        deal["organization_logo"] = org_logo_map.get(deal.organization, "")
        owner = owner_map.get(deal.deal_owner, frappe._dict())
        deal["deal_owner_name"]  = owner.get("full_name", deal.deal_owner or "")
        deal["deal_owner_image"] = owner.get("user_image", "")
        if stage in columns:
            columns[stage].append(deal)
        else:
            uncategorized.append(deal)

    # Drop uncategorized into first stage
    if uncategorized and stage_names:
        columns[stage_names[0]].extend(uncategorized)

    return {
        "stages": cfg["stages"],
        "columns": columns,
    }


@frappe.whitelist()
def update_deal_stage(deal_name, new_stage, pipeline):
    """Called when a card is dragged to a new column."""
    if pipeline not in PIPELINE_CONFIG:
        frappe.throw(f"Unknown pipeline: {pipeline}")

    valid_stages = {s["name"] for s in PIPELINE_CONFIG[pipeline]["stages"]}
    if new_stage not in valid_stages:
        frappe.throw(f"Invalid stage '{new_stage}' for pipeline '{pipeline}'")

    frappe.db.set_value("CRM Deal", deal_name, "custom_pipeline_stage", new_stage)
    return {"success": True}


@frappe.whitelist()
def create_pipeline_deal(pipeline, stage, organization=None, deal_value=None,
                         deal_owner=None, expected_closure_date=None, **kwargs):
    """Quick-create a deal from the Kanban new-card button."""
    if pipeline not in PIPELINE_CONFIG:
        frappe.throw(f"Unknown pipeline: {pipeline}")

    cfg = PIPELINE_CONFIG[pipeline]
    pipeline_type = cfg["pipeline_type"]

    doc = frappe.new_doc("CRM Deal")
    doc.custom_pipeline_type  = pipeline_type
    doc.custom_pipeline_stage = stage
    doc.organization          = organization or ""
    doc.deal_value            = flt(deal_value)
    doc.deal_owner            = deal_owner or frappe.session.user
    doc.expected_closure_date = expected_closure_date or None

    # Pipeline-specific fields
    allowed_extra = {
        "fresh_frozen": ["custom_strain_name", "custom_available_lbs", "custom_target_output_g"],
        "rosin":        ["custom_strain_name", "custom_target_output_g"],
        "distro":       ["custom_license_number", "custom_license_verified"],
        "tolling":      [
            "custom_input_material_type", "custom_lbs_per_run",
            "custom_rate_per_lb", "custom_byo_flag", "custom_work_order",
            "custom_run_frequency",
        ],
    }.get(pipeline, [])

    for field in allowed_extra:
        if field in kwargs:
            setattr(doc, field, kwargs[field])

    doc.insert(ignore_permissions=False)
    return {"name": doc.name, "success": True}
