"""
Motley Terpz — Email Campaigns ("blast tool").

Deliberately built on Frappe's own Newsletter + Email Group engine rather
than a bespoke bulk-mailer: that gets us HTML/Rich-Text/Markdown
authoring, queuing (Email Queue, throttled by the scheduler), unsubscribe
handling, and send-status tracking for free, all already battle-tested
elsewhere in Frappe. This module is a thin CRM-shaped wrapper around it:

  1. build_audience()   — turn a set of CRM Lead / CRM Deal / Contact
                           records into an Email Group + members
  2. create_campaign()  — draft a Newsletter
  3. send_test()         — Newsletter.send_test_email()
  4. send_campaign()     — Newsletter.send_emails(), then logs a
                           Communication against each recipient's CRM
                           Lead/Deal so the send shows up in that
                           record's activity timeline
  5. list_campaigns() / get_campaign_status() — for the Campaigns page

Only CRM Sales User (and above) may send — same gate as the existing
one-off "Send Email" feature on Lead/Deal.
"""

import json

import frappe
from frappe.utils import now_datetime, validate_email_address

DEFAULT_SENDER_EMAIL = "Douglas@kiloandco.com"
DEFAULT_SENDER_NAME = "Motley Terpz"

EMAIL_FIELD_BY_DOCTYPE = {
    "CRM Lead": "email",
    "CRM Deal": "email",
    "Contact": "email_id",
}


def _check_sender_access():
    roles = set(frappe.get_roles())
    if not ({"Sales User", "Sales Manager", "System Manager"} & roles):
        frappe.throw("Not permitted to send campaigns", frappe.PermissionError)


def _title_for(doctype, row):
    if doctype == "CRM Lead":
        return row.get("lead_name") or row.get("name")
    if doctype == "CRM Deal":
        return row.get("organization") or row.get("name")
    if doctype == "Contact":
        return row.get("full_name") or row.get("name")
    return row.get("name")


@frappe.whitelist()
def search_recipients(doctype, txt=""):
    """Records of the given doctype with a usable email address, for the
    audience-builder's search box."""
    if doctype not in EMAIL_FIELD_BY_DOCTYPE:
        frappe.throw(f"Unsupported doctype: {doctype}")
    email_field = EMAIL_FIELD_BY_DOCTYPE[doctype]

    title_field = {"CRM Lead": "lead_name", "CRM Deal": "organization", "Contact": "full_name"}[doctype]
    or_filters = None
    if txt:
        or_filters = [[title_field, "like", f"%{txt}%"], [email_field, "like", f"%{txt}%"]]

    return _recipient_rows(doctype, {email_field: ["is", "set"]}, or_filters, limit_page_length=20)


@frappe.whitelist()
def get_recipients_by_names(doctype, names):
    """Records of the given doctype/names with a usable email address —
    lets a bulk selection from the Leads/Deals list view be pre-filled into
    the audience builder instead of re-searching each name one at a time."""
    if isinstance(names, str):
        names = json.loads(names)
    if doctype not in EMAIL_FIELD_BY_DOCTYPE:
        frappe.throw(f"Unsupported doctype: {doctype}")
    email_field = EMAIL_FIELD_BY_DOCTYPE[doctype]
    return _recipient_rows(
        doctype,
        {"name": ["in", names], email_field: ["is", "set"]},
        limit_page_length=0,
    )


def _recipient_rows(doctype, filters, or_filters=None, limit_page_length=20):
    _check_sender_access()
    email_field = EMAIL_FIELD_BY_DOCTYPE[doctype]
    title_field = {"CRM Lead": "lead_name", "CRM Deal": "organization", "Contact": "full_name"}[doctype]
    rows = frappe.get_all(
        doctype,
        filters=filters,
        or_filters=or_filters,
        fields=["name", email_field, title_field],
        limit_page_length=limit_page_length,
        order_by="modified desc",
    )
    return [
        {"name": r["name"], "email": r[email_field], "title": _title_for(doctype, r)}
        for r in rows
        if r.get(email_field)
    ]


@frappe.whitelist()
def get_audiences():
    """Existing Email Groups, for reuse across campaigns."""
    _check_sender_access()
    return frappe.get_all(
        "Email Group", fields=["name", "title", "total_subscribers"], order_by="modified desc"
    )


@frappe.whitelist()
def build_audience(title, recipients):
    """Create a new Email Group from a list of
    [{"name": <doc name>, "doctype": <CRM Lead|CRM Deal|Contact>, "email": ...}, ...]
    and remember which CRM record each address maps to (crm_doctype/crm_name
    on the Email Group Member) so a later send can log back to that record.
    """
    _check_sender_access()
    if isinstance(recipients, str):
        recipients = json.loads(recipients)
    if not recipients:
        frappe.throw("Pick at least one recipient")

    group = frappe.get_doc({"doctype": "Email Group", "title": title}).insert(ignore_permissions=True)

    seen = set()
    for r in recipients:
        email = (r.get("email") or "").strip()
        if not email or email in seen:
            continue
        seen.add(email)
        try:
            validate_email_address(email, throw=True)
        except Exception:
            continue
        member = frappe.get_doc({
            "doctype": "Email Group Member",
            "email_group": group.name,
            "email": email,
        })
        member.insert(ignore_permissions=True)
        if r.get("name") and r.get("doctype") in EMAIL_FIELD_BY_DOCTYPE:
            frappe.db.set_value(
                "Email Group Member", member.name,
                {"crm_reference_doctype": r["doctype"], "crm_reference_name": r["name"]},
                update_modified=False,
            )

    frappe.db.set_value("Email Group", group.name, "total_subscribers", len(seen))
    return {"name": group.name, "total_subscribers": len(seen)}


@frappe.whitelist()
def create_campaign(subject, content, content_type, email_group, newsletter=None):
    """Draft a Newsletter — not sent yet. Updates in place if `newsletter`
    points at an existing, not-yet-sent draft; otherwise creates a new one."""
    _check_sender_access()
    if content_type not in ("Rich Text", "Markdown", "HTML"):
        frappe.throw("Invalid content type")

    if newsletter and frappe.db.exists("Newsletter", newsletter):
        doc = frappe.get_doc("Newsletter", newsletter)
        if doc.email_sent:
            frappe.throw("This campaign has already been sent and can't be edited")
    else:
        doc = frappe.new_doc("Newsletter")
        doc.sender_email = DEFAULT_SENDER_EMAIL
        doc.sender_name = DEFAULT_SENDER_NAME
        doc.send_unsubscribe_link = 1

    doc.subject = subject
    doc.content_type = content_type
    doc.email_group = [{"email_group": email_group}]
    if content_type == "HTML":
        doc.message_html = content
    elif content_type == "Markdown":
        doc.message_md = content
    else:
        doc.message = content

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)
    return {"name": doc.name}


@frappe.whitelist()
def get_campaign(newsletter):
    """Full editable content for reopening a saved draft."""
    _check_sender_access()
    doc = frappe.get_doc("Newsletter", newsletter)
    groups = doc.get_email_groups()
    return {
        "name": doc.name,
        "subject": doc.subject,
        "content_type": doc.content_type,
        "content": doc.get_message(),
        "email_group": groups[0] if groups else None,
        "email_sent": doc.email_sent,
    }


@frappe.whitelist()
def send_test(newsletter, email):
    _check_sender_access()
    doc = frappe.get_doc("Newsletter", newsletter)
    doc.send_test_email(email)

    reference_doctype, reference_name = _find_crm_reference_by_email(email)
    if reference_doctype:
        _log_communication(
            subject=f"[Test] {doc.subject}",
            content=doc.get_message(),
            recipient_email=email,
            reference_doctype=reference_doctype,
            reference_name=reference_name,
        )
    return {"ok": True}


@frappe.whitelist()
def send_campaign(newsletter):
    _check_sender_access()
    doc = frappe.get_doc("Newsletter", newsletter)
    doc.send_emails()
    _log_crm_communications(doc)
    return {"ok": True}


def _find_crm_reference_by_email(email):
    """Best-effort lookup of a CRM Lead/Deal/Contact whose email matches, so
    a send can be logged against it even outside a built audience (e.g. a
    one-off test send). Returns (doctype, name) or (None, None)."""
    for doctype, email_field in EMAIL_FIELD_BY_DOCTYPE.items():
        name = frappe.db.get_value(doctype, {email_field: email})
        if name:
            return doctype, name
    return None, None


def _log_communication(subject, content, recipient_email, reference_doctype, reference_name):
    frappe.get_doc({
        "doctype": "Communication",
        "communication_type": "Communication",
        "communication_medium": "Email",
        "sent_or_received": "Sent",
        "subject": subject,
        "content": content,
        "sender": DEFAULT_SENDER_EMAIL,
        "recipients": recipient_email,
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "communication_date": now_datetime(),
    }).insert(ignore_permissions=True)


def _log_crm_communications(newsletter_doc):
    """So a sent campaign shows up in each recipient's CRM Lead/Deal
    activity timeline, the same way a one-off email already does."""
    group_names = newsletter_doc.get_email_groups()
    members = frappe.get_all(
        "Email Group Member",
        filters={"email_group": ["in", group_names], "crm_reference_doctype": ["is", "set"]},
        fields=["email", "crm_reference_doctype", "crm_reference_name"],
    )
    content = newsletter_doc.get_message()
    for m in members:
        if not frappe.db.exists(m.crm_reference_doctype, m.crm_reference_name):
            continue
        _log_communication(
            subject=newsletter_doc.subject,
            content=content,
            recipient_email=m.email,
            reference_doctype=m.crm_reference_doctype,
            reference_name=m.crm_reference_name,
        )


@frappe.whitelist()
def get_campaign_status(newsletter):
    _check_sender_access()
    doc = frappe.get_doc("Newsletter", newsletter)
    status = doc.get_sending_status()
    status["total_recipients"] = len(doc.newsletter_recipients)
    return status


@frappe.whitelist()
def list_campaigns():
    _check_sender_access()
    rows = frappe.get_all(
        "Newsletter",
        fields=["name", "subject", "email_sent", "email_sent_at", "total_recipients",
                "creation", "owner", "content_type"],
        order_by="creation desc",
        limit_page_length=100,
    )
    return rows
