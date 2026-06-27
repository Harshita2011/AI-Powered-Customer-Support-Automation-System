"""
Task 1: LangGraph Workflow
===========================
Assembles the complete Customer Support Automation System graph.

Workflow:
  START
    │
    ▼
  intent_classification_node    (Task 3 — classify intent + load memory)
    │
    ▼  [conditional edge: route_by_intent]
    ├─► sales_agent             (Task 5)
    ├─► technical_agent         (Task 5)
    ├─► billing_agent           (Task 5)  ─► [conditional: approval needed?]
    ├─► account_agent           (Task 5)        ├─► human_approval_node (Task 8)
    └─► memory_recall_agent     (Task 7)        │       │
                │                               │       ▼ [route_after_approval]
                │                               │   supervisor_agent / end_rejected
                ▼                               │
          supervisor_agent (Task 9) ◄───────────┘
                │
                ▼
              END
"""

from langgraph.graph import StateGraph, END

from src.state import CustomerSupportState
from src.intent import intent_classification_node
from src.router import route_by_intent, route_after_approval_check, route_after_approval
from src.agents import (
    sales_agent,
    technical_agent,
    billing_agent,
    account_agent,
    memory_recall_agent,
)
from src.human_loop import human_approval_node
from src.supervisor import supervisor_agent, end_rejected_node


def build_graph() -> StateGraph:
    """
    Build and compile the complete LangGraph state machine.

    Returns:
        A compiled LangGraph graph ready to invoke.
    """
    # ── 1. Initialise graph with our state schema ──────────────────────────────
    graph = StateGraph(CustomerSupportState)

    # ── 2. Register all nodes ──────────────────────────────────────────────────
    graph.add_node("intent_classifier",    intent_classification_node)  # Task 3
    graph.add_node("sales_agent",          sales_agent)                 # Task 5
    graph.add_node("technical_agent",      technical_agent)             # Task 5
    graph.add_node("billing_agent",        billing_agent)               # Task 5
    graph.add_node("account_agent",        account_agent)               # Task 5
    graph.add_node("memory_recall_agent",  memory_recall_agent)         # Task 7
    graph.add_node("human_approval_node",  human_approval_node)         # Task 8
    graph.add_node("supervisor_agent",     supervisor_agent)            # Task 9
    graph.add_node("end_rejected",         end_rejected_node)           # rejection path

    # ── 3. Entry point ─────────────────────────────────────────────────────────
    graph.set_entry_point("intent_classifier")

    # ── 4. Conditional routing after intent classification (Task 4) ────────────
    graph.add_conditional_edges(
        "intent_classifier",
        route_by_intent,
        {
            "sales_agent":          "sales_agent",
            "technical_agent":      "technical_agent",
            "billing_agent":        "billing_agent",
            "account_agent":        "account_agent",
            "memory_recall_agent":  "memory_recall_agent",
        },
    )

    # ── 5. Sales / Technical / Account / Memory → straight to supervisor ───────
    graph.add_edge("sales_agent",         "supervisor_agent")
    graph.add_edge("technical_agent",     "supervisor_agent")
    graph.add_edge("account_agent",       "supervisor_agent")
    graph.add_edge("memory_recall_agent", "supervisor_agent")

    # ── 6. Billing → conditional human approval check (Task 8) ────────────────
    graph.add_conditional_edges(
        "billing_agent",
        route_after_approval_check,
        {
            "human_approval_node": "human_approval_node",
            "supervisor_agent":    "supervisor_agent",
        },
    )

    # ── 7. After human approval → supervisor or end_rejected ──────────────────
    graph.add_conditional_edges(
        "human_approval_node",
        route_after_approval,
        {
            "supervisor_agent": "supervisor_agent",
            "end_rejected":     "end_rejected",
        },
    )

    # ── 8. Terminal edges ──────────────────────────────────────────────────────
    graph.add_edge("supervisor_agent", END)
    graph.add_edge("end_rejected",     END)

    # ── 9. Compile ─────────────────────────────────────────────────────────────
    compiled = graph.compile()
    print("[Graph] LangGraph workflow compiled successfully.")
    return compiled


# ── Convenience run function ───────────────────────────────────────────────────

def run_query(
    graph,
    customer_id: str,
    query: str,
    customer_name: str = "Customer",
) -> CustomerSupportState:
    """
    Run a single customer query through the compiled graph.

    Args:
        graph         : Compiled LangGraph graph.
        customer_id   : Unique customer identifier for memory lookup.
        query         : The customer's support query.
        customer_name : Customer's display name.

    Returns:
        The final state after the graph has finished executing.
    """
    initial_state: CustomerSupportState = {
        "customer_id":           customer_id,
        "customer_name":         customer_name,
        "query":                 query,
        "intent":                None,
        "department":            None,
        "retrieved_context":     None,
        "conversation_history":  [],
        "requires_approval":     False,
        "approval_status":       None,
        "draft_response":        None,
        "supervisor_notes":      None,
        "final_response":        None,
        "error":                 None,
    }

    final_state = graph.invoke(initial_state)
    return final_state
