"""
Motley Terpz — "My Day" action dashboard.

Sales-dashboard feedback: "we need a place where sales can see all tasks,
all recent moves ... clickable to the actual task tab in the account page."

Single aggregation endpoint: my open tasks (overdue first), this week's
logged/scheduled meetings, and my most recent activity across every
Lead/Deal I've touched. Managers (sees_all_data) get a rep switcher;
everyone else always sees their own.
"""

import frappe
from frappe.utils import add_days, get_url_to_form, getdate, nowdate

from crm.motley_terpz.access import sees_all_data

OPEN_TASK_STATUSES = ("Backlog", "Todo", "In Progress")
RECENT_LIMIT = 20


def _doc_title(doctype, name, cache):
    key = (doctype, name)
    if key in cache:
        return cache[key]
    title = name
    if doctype == "CRM Lead":
        title = frappe.db.get_value("CRM Lead", name, "lead_name") or name
    elif doctype == "CRM Deal":
        title = frappe.db.get_value("CRM Deal", name, "organization") or name
    cache[key] = title
    return title


def _record_route(doctype, name, tab=None):
    if doctype == "CRM Lead":
        path = f"/crm/leads/{name}"
    elif doctype == "CRM Deal":
        path = f"/crm/deals/{name}"
    elif doctype == "Contact":
        path = f"/contacts/{name}"
    else:
        return None
    return f"{path}#{tab}" if tab else path


@frappe.whitelist()
def get_reps():
    """Users eligible for the rep switcher (managers only).

    Rep universe derived the same way as the Rep Leaderboard (batch_d.py):
    anyone who actually owns a deal or a lead — not role membership, which
    on this site is shared broadly with non-sales staff.
    """
    if not sees_all_data():
        return []
    reps = set(frappe.db.sql_list(
        "SELECT DISTINCT deal_owner FROM `tabCRM Deal` WHERE deal_owner IS NOT NULL AND deal_owner != ''"
    ))
    reps |= set(frappe.db.sql_list(
        "SELECT DISTINCT lead_owner FROM `tabCRM Lead` WHERE lead_owner IS NOT NULL AND lead_owner != ''"
    ))
    if not reps:
        return []
    return frappe.get_all(
        "User",
        filters={"enabled": 1, "name": ["in", list(reps)]},
        fields=["name", "full_name"],
        order_by="full_name asc",
    )


@frappe.whitelist()
def get_my_day(user=None):
    requested = user
    user = user or frappe.session.user
    if requested and requested != frappe.session.user and not sees_all_data():
        frappe.throw("Not permitted to view another rep's day", frappe.PermissionError)

    title_cache = {}
    today = getdate(nowdate())

    # ── Tasks ────────────────────────────────────────────────────────────
    tasks = frappe.get_all(
        "CRM Task",
        filters={"assigned_to": user, "status": ["in", OPEN_TASK_STATUSES]},
        fields=["name", "title", "status", "priority", "due_date",
                "reference_doctype", "reference_docname", "modified"],
        order_by="due_date asc",
    )
    for t in tasks:
        t["is_overdue"] = bool(t.due_date and getdate(t.due_date) < today)
        t["reference_title"] = (
            _doc_title(t.reference_doctype, t.reference_docname, title_cache)
            if t.reference_doctype and t.reference_docname else None
        )
        t["route"] = _record_route(t.reference_doctype, t.reference_docname, "tasks")

    overdue_count = sum(1 for t in tasks if t["is_overdue"])
    due_today_count = sum(
        1 for t in tasks if t.due_date and getdate(t.due_date) == today
    )

    # ── This week's meetings (events the rep logged/scheduled) ────────────
    week_end = add_days(today, 7)
    meetings = frappe.get_all(
        "Event",
        filters={
            "owner": user,
            "starts_on": ["between", [today, week_end]],
        },
        fields=["name", "subject", "starts_on", "ends_on", "status",
                "reference_doctype", "reference_docname"],
        order_by="starts_on asc",
    )
    for m in meetings:
        m["reference_title"] = (
            _doc_title(m.reference_doctype, m.reference_docname, title_cache)
            if m.reference_doctype and m.reference_docname else None
        )
        m["route"] = _record_route(m.reference_doctype, m.reference_docname)

    # ── Recent moves: notes, tasks, calls I've logged, most recent first ──
    recent = []
    for note in frappe.get_all(
        "FCRM Note", filters={"owner": user},
        fields=["name", "title", "reference_doctype", "reference_docname", "creation"],
        order_by="creation desc", limit_page_length=RECENT_LIMIT,
    ):
        recent.append({
            "type": "note", "timestamp": note.creation,
            "label": note.title or "Note",
            "reference_doctype": note.reference_doctype,
            "reference_docname": note.reference_docname,
        })
    for task in frappe.get_all(
        "CRM Task", filters={"owner": user},
        fields=["name", "title", "status", "reference_doctype", "reference_docname", "creation"],
        order_by="creation desc", limit_page_length=RECENT_LIMIT,
    ):
        recent.append({
            "type": "task", "timestamp": task.creation,
            "label": task.title, "status": task.status,
            "reference_doctype": task.reference_doctype,
            "reference_docname": task.reference_docname,
        })
    for call in frappe.get_all(
        "CRM Call Log", filters={"owner": user},
        fields=["name", "type", "status", "reference_doctype", "reference_docname", "creation"],
        order_by="creation desc", limit_page_length=RECENT_LIMIT,
    ):
        recent.append({
            "type": "call", "timestamp": call.creation,
            "label": f"{call.type or 'Call'} — {call.status or ''}".strip(" —"),
            "reference_doctype": call.reference_doctype,
            "reference_docname": call.reference_docname,
        })

    for r in recent:
        r["reference_title"] = (
            _doc_title(r["reference_doctype"], r["reference_docname"], title_cache)
            if r.get("reference_doctype") and r.get("reference_docname") else None
        )
        r["route"] = _record_route(r.get("reference_doctype"), r.get("reference_docname"))

    recent.sort(key=lambda r: r["timestamp"], reverse=True)
    recent = recent[:RECENT_LIMIT]

    return {
        "user": user,
        "tasks": tasks,
        "overdue_count": overdue_count,
        "due_today_count": due_today_count,
        "meetings": meetings,
        "meetings_count": len(meetings),
        "recent": recent,
    }
