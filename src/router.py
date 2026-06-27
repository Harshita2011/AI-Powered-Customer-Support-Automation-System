"""
Task 4: Conditional Routing
============================
Reads state["intent"] and returns the name of the next node to execute.
LangGraph uses this function as the condition for a conditional edge.
"""

from src.state import CustomerSupportState


def route_by_intent(state: CustomerSupportState) -> str:
    """
    Routing function for LangGraph conditional edges.

    Maps intent → node name:
      Sales     → sales_agent
      Technical → technical_agent
      Billing   → billing_agent
      Account   → account_agent
      Memory    → memory_recall_agent
      (default) → sales_agent
    """
    intent = state.get("intent", "Sales")

    routing_map = {
        "Sales":     "sales_agent",
        "Technical": "technical_agent",
        "Billing":   "billing_agent",
        "Account":   "account_agent",
        "Memory":    "memory_recall_agent",
    }

    destination = routing_map.get(intent, "sales_agent")
    print(f"[Router] Intent='{intent}' → routing to '{destination}'")
    return destination


def route_after_approval_check(state: CustomerSupportState) -> str:
    """
    After the billing agent runs, decide whether human approval is needed.

    Returns:
      'human_approval_node' if requires_approval is True
      'supervisor_agent'    otherwise
    """
    if state.get("requires_approval", False):
        print("[Router] High-risk request detected → human approval required.")
        return "human_approval_node"
    print("[Router] No approval needed → forwarding to supervisor.")
    return "supervisor_agent"


def route_after_approval(state: CustomerSupportState) -> str:
    """
    After human approval decision, decide whether to proceed or end.

    Returns:
      'supervisor_agent' if approved
      'end'              if rejected
    """
    status = state.get("approval_status", "pending")
    if status == "approved":
        print("[Router] Request approved by supervisor → continuing to response.")
        return "supervisor_agent"
    elif status == "rejected":
        print("[Router] Request rejected by supervisor → ending workflow.")
        return "end_rejected"
    # Still pending (shouldn't happen in normal flow)
    return "human_approval_node"
