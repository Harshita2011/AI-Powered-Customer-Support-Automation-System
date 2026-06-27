"""
Task 9: Supervisor Agent
=========================
The Supervisor reviews the draft response produced by department agents,
validates quality and tone, and either approves it or improves it before
it is sent to the customer.

Checks performed:
  - Response addresses the customer's actual query
  - Tone is professional and empathetic
  - Contact / next-step information is included
  - Response length is appropriate (not too short, not padded)
  - No placeholder text left in response
"""

from src.state import CustomerSupportState
from src.memory import save_interaction


# ── Quality checks ─────────────────────────────────────────────────────────────

def _quality_check(query: str, draft: str) -> list[str]:
    """
    Run a series of quality checks on the draft response.
    Returns a list of issue strings (empty = all good).
    """
    issues = []

    if len(draft.strip()) < 100:
        issues.append("Response is too short — needs more detail.")

    if "[PLACEHOLDER]" in draft or "TODO" in draft:
        issues.append("Draft contains placeholder text — must be removed.")

    if not any(
        phrase in draft.lower()
        for phrase in ["best regards", "thank you", "please", "contact"]
    ):
        issues.append("Response lacks professional closing or contact information.")

    # Check that at least some query keywords appear in the response
    query_words = set(query.lower().split())
    draft_lower = draft.lower()
    coverage = sum(1 for w in query_words if len(w) > 4 and w in draft_lower)
    if coverage < 1:
        issues.append("Response does not appear to address the customer's query keywords.")

    return issues


def _improve_response(draft: str, issues: list[str], department: str) -> str:
    """
    Apply simple corrections to the draft based on detected issues.
    In production, this would call an LLM for rewriting.
    """
    improved = draft

    if "too short" in " ".join(issues):
        improved += (
            "\n\nIf you require further assistance, please don't hesitate to "
            "contact our support team at support@abctech.com or via live chat "
            "at app.abctech.com. Our team is available Monday–Friday 9am–8pm EST."
        )

    if "placeholder" in " ".join(issues):
        improved = improved.replace("[PLACEHOLDER]", "").replace("TODO", "")

    if "professional closing" in " ".join(issues):
        improved += (
            "\n\nBest regards,\n"
            f"ABC Technologies {department} Team"
        )

    return improved.strip()


# ── Supervisor Node ────────────────────────────────────────────────────────────

def supervisor_agent(state: CustomerSupportState) -> CustomerSupportState:
    """
    LangGraph node: review, validate, and optionally improve the draft response.

    Updates state fields:
      - supervisor_notes : summary of quality check findings
      - final_response   : polished response ready for the customer
    """
    print("\n[Supervisor] Reviewing draft response...")

    draft = state.get("draft_response", "")
    query = state.get("query", "")
    department = state.get("department", "Support")
    customer_id = state.get("customer_id", "unknown")
    intent = state.get("intent", "")

    # 1. Run quality checks
    issues = _quality_check(query, draft)

    if issues:
        print(f"[Supervisor] Found {len(issues)} issue(s): {issues}")
        final_response = _improve_response(draft, issues, department)
        notes = f"Improved response. Issues resolved: {'; '.join(issues)}"
    else:
        print("[Supervisor] Draft passes all quality checks ✓")
        final_response = draft
        notes = "Draft approved without modifications."

    print(f"[Supervisor] Notes: {notes}")

    # 2. Persist to SQLite memory
    save_interaction(
        customer_id=customer_id,
        customer_message=query,
        agent_response=final_response,
        intent=intent,
        department=department,
    )
    print(f"[Supervisor] Interaction saved to memory for customer '{customer_id}'.")

    return {
        **state,
        "supervisor_notes": notes,
        "final_response": final_response,
    }


def end_rejected_node(state: CustomerSupportState) -> CustomerSupportState:
    """
    Terminal node for rejected requests.
    Sets the final response to the rejection message drafted by human_loop.
    """
    print("[End] Request was rejected by supervisor. Sending rejection response.")
    customer_id = state.get("customer_id", "unknown")
    query = state.get("query", "")
    intent = state.get("intent", "")
    department = state.get("department", "")
    rejection = state.get("draft_response", "Your request could not be processed.")

    save_interaction(
        customer_id=customer_id,
        customer_message=query,
        agent_response=rejection,
        intent=intent,
        department=department,
    )

    return {
        **state,
        "final_response": rejection,
        "supervisor_notes": "Request rejected by human supervisor.",
    }
