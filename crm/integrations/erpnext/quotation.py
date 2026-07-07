import frappe

from crm.integrations.erpnext.utils import should_sync

SUBMITTED_DEAL_STATUS = "Proposal/Quotation"
LOST_DEAL_STATUS = "Lost"

# Deal statuses that a quotation event must never move the deal out of
CLOSED_DEAL_STATUSES = ("Won", "Lost")


def on_submit(doc, method=None):
	"""Move the linked CRM Deal to Proposal/Quotation when a quotation is submitted."""
	_update_linked_deal_status(doc, SUBMITTED_DEAL_STATUS)


def on_change(doc, method=None):
	"""Move the linked CRM Deal to Lost when a submitted quotation is marked Lost.

	ERPNext marks a quotation Lost via db_set (declare_enquiry_lost), which only
	fires on_change — not on_update_after_submit — so we hook on_change.
	"""
	if doc.docstatus == 1 and doc.status == "Lost":
		_update_linked_deal_status(doc, LOST_DEAL_STATUS)


def _get_linked_deal(doc):
	deal = doc.get("crm_deal")
	if not deal and doc.get("quotation_to") == "CRM Deal":
		deal = doc.get("party_name")
	if deal and frappe.db.exists("CRM Deal", deal):
		return deal
	return None


def _update_linked_deal_status(doc, status):
	if not should_sync():
		return

	deal_name = _get_linked_deal(doc)
	if not deal_name or not frappe.db.exists("CRM Deal Status", status):
		return

	try:
		deal = frappe.get_doc("CRM Deal", deal_name)
		if deal.status == status or deal.status in CLOSED_DEAL_STATUSES:
			return
		deal.status = status
		if status == LOST_DEAL_STATUS:
			_set_lost_reason(deal, doc)
		deal.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"Error updating CRM Deal {deal_name} status from Quotation {doc.name}",
		)


def _set_lost_reason(deal, quotation):
	"""CRM Deal validation requires a lost reason (and notes when reason is Other)."""
	if not deal.lost_reason:
		reason = next(
			(
				row.lost_reason
				for row in quotation.get("lost_reasons") or []
				if row.lost_reason and frappe.db.exists("CRM Lost Reason", row.lost_reason)
			),
			None,
		)
		deal.lost_reason = reason or "Other"
	if deal.lost_reason == "Other" and not deal.lost_notes:
		deal.lost_notes = quotation.get("order_lost_reason") or (
			f"Quotation {quotation.name} was marked as Lost in ERPNext"
		)
