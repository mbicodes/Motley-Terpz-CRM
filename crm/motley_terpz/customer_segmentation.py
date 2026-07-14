"""
Motley Terpz — Customer Segmentation (read-only)

Groups active ERPNext Customers into sections by the sales person handling
them: Nikki / Douglas / Dominic / Unidentified.

A customer belongs to a rep's section when:
  - the rep's user is in the customer's assignment list (_assign), or
  - the rep's Sales Person record appears in the customer's Sales Team.
Customers matching none of the reps land in "Unidentified".
"""
import json

import frappe

# Reps shown as sections, in display order. Each must be a User; the Sales
# Person link is resolved through Sales Person.custom_email at runtime.
SECTION_REPS = [
    {"key": "nikki",   "label": "Nikki",   "user": "nikki@motleyterpz.com"},
    {"key": "douglas", "label": "Douglas", "user": "douglas@motleyterpz.com"},
    {"key": "dominic", "label": "Dominic", "user": "dominic@motleyterpz.com"},
]


@frappe.whitelist()
def get_customer_segmentation():
    # Sales Person records owned by each rep (via custom_email)
    sp_rows = frappe.db.sql(
        """
        SELECT name, custom_email
        FROM `tabSales Person`
        WHERE enabled = 1 AND IFNULL(custom_email, '') != ''
        """,
        as_dict=True,
    )
    sp_names_by_user = {}
    for r in sp_rows:
        sp_names_by_user.setdefault(r.custom_email, set()).add(r.name)

    # Customer → sales persons from the customer's Sales Team child table
    st_rows = frappe.db.sql(
        """
        SELECT parent, sales_person
        FROM `tabSales Team`
        WHERE parenttype = 'Customer'
        """,
        as_dict=True,
    )
    st_by_customer = {}
    for r in st_rows:
        st_by_customer.setdefault(r.parent, set()).add(r.sales_person)

    customers = frappe.get_all(
        "Customer",
        filters={"disabled": 0},
        fields=[
            "name", "customer_name", "customer_group", "territory",
            "custom_license_type", "_assign",
        ],
        order_by="customer_name asc",
    )

    sections = [
        {
            "key": rep["key"],
            "label": rep["label"],
            "user": rep["user"],
            "full_name": frappe.db.get_value("User", rep["user"], "full_name") or rep["label"],
            "customers": [],
        }
        for rep in SECTION_REPS
    ]
    unidentified = {
        "key": "unidentified",
        "label": "Unidentified",
        "user": None,
        "full_name": "No sales person assigned",
        "customers": [],
    }

    for c in customers:
        try:
            assigned = set(json.loads(c._assign) if c._assign else [])
        except Exception:
            assigned = set()
        team = st_by_customer.get(c.name, set())

        row = {
            "name": c.name,
            "customer_name": c.customer_name,
            "customer_group": c.customer_group,
            "territory": c.territory,
            "license_type": c.custom_license_type,
        }

        matched = False
        for rep, section in zip(SECTION_REPS, sections):
            if rep["user"] in assigned or (team & sp_names_by_user.get(rep["user"], set())):
                section["customers"].append(row)
                matched = True
        if not matched:
            unidentified["customers"].append(row)

    sections.append(unidentified)
    for s in sections:
        s["count"] = len(s["customers"])

    return {"sections": sections, "total": len(customers)}
