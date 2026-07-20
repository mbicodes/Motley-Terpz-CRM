import frappe


@frappe.whitelist()
def complete_task(task: str, note: str = ""):
	"""Mark a CRM Task as Done and, if a note was given, log it as a
	Comment against the task's linked record so it shows up in that
	record's activity timeline alongside calls/emails/notes."""
	task_doc = frappe.get_doc("CRM Task", task)
	task_doc.status = "Done"
	task_doc.save(ignore_permissions=True)

	note = (note or "").strip()
	if note and task_doc.reference_doctype and task_doc.reference_docname:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Comment",
				"reference_doctype": task_doc.reference_doctype,
				"reference_name": task_doc.reference_docname,
				"content": f"Task \"{task_doc.title}\" completed: {note}",
			}
		).insert(ignore_permissions=True)

	return {"ok": True}
