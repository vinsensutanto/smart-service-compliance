from flask import Blueprint, render_template

sop_page_bp = Blueprint("sop_page", __name__)

@sop_page_bp.route("/checklist/<session_id>")
def checklist_page(session_id):
    """
    Renders the checklist HTML page.
    The JS on this page will fetch the actual checklist JSON
    from /api/checklist/<session_id>.
    """
    return render_template("checklist.html", session_id=session_id)
