"""
Task 5: Specialized Department Agents
======================================
Four department agents + one memory recall agent.
Each agent uses RAG context and conversation history to draft a response.

Agents:
  - Sales Agent
  - Technical Support Agent
  - Billing Agent         (also flags high-risk requests)
  - Account Agent
  - Memory Recall Agent   (no RAG, uses SQLite history only)
"""

import re
from src.state import CustomerSupportState
from src.rag import get_vector_store, retrieve_context
from src.memory import format_history_for_prompt

# ── High-risk keywords that trigger human-in-the-loop ─────────────────────────
HIGH_RISK_KEYWORDS = [
    "refund", "cancel subscription", "cancellation",
    "close account", "account closure",
    "compensation", "escalate to management", "escalation",
    "money back", "reimbursement",
]


def _needs_approval(query: str) -> bool:
    """Return True if the query contains any high-risk keywords."""
    q = query.lower()
    return any(kw in q for kw in HIGH_RISK_KEYWORDS)


def _build_response(
    department: str,
    persona: str,
    query: str,
    context: str,
    customer_name: str = "Customer",
) -> str:
    """
    Construct a realistic department agent response.
    In production this would call an LLM with a detailed system prompt.
    Here we build a structured, context-aware reply directly.

    IMPORTANT: This response intentionally does NOT include conversation
    history. History is display-only (shown to the customer alongside
    this response) and must never be embedded into the text that gets
    persisted to memory — doing so causes each saved turn to contain the
    previous turn's history, which then gets pulled back out and
    re-embedded on the next turn, growing without bound.
    """
    greeting = f"Hello {customer_name},"

    response = f"""{greeting}

Thank you for contacting ABC Technologies {department}.

I understand your query: "{query}"

Based on our knowledge base, here is the information relevant to your request:

{context[:1200]}

Please do not hesitate to reach out if you need further assistance.

Best regards,
{persona}
ABC Technologies {department}"""

    return response.strip()


# ── Sales Agent ───────────────────────────────────────────────────────────────

def sales_agent(state: CustomerSupportState) -> CustomerSupportState:
    """Handle Sales queries: pricing, plans, product information."""
    print("[Sales Agent] Processing query...")
    vs = get_vector_store()
    context = retrieve_context(vs, state["query"])
    history_text = format_history_for_prompt(state.get("conversation_history", []))

    response = _build_response(
        department="Sales",
        persona="Alex | Sales Specialist",
        query=state["query"],
        context=context,
        customer_name=state.get("customer_name") or "Valued Customer",
    )

    return {
        **state,
        "department": "Sales",
        "retrieved_context": context,
        "draft_response": response,        # clean — safe to persist to memory
        "history_display": history_text,   # display-only, must NOT be saved
        "requires_approval": False,
    }


# ── Technical Support Agent ───────────────────────────────────────────────────

def technical_agent(state: CustomerSupportState) -> CustomerSupportState:
    """Handle Technical queries: errors, crashes, login, configuration."""
    print("[Technical Agent] Processing query...")
    vs = get_vector_store()
    context = retrieve_context(vs, state["query"])
    history_text = format_history_for_prompt(state.get("conversation_history", []))

    # Enrich context with troubleshooting steps if crash/error mentioned
    if any(kw in state["query"].lower() for kw in ["crash", "error", "upload", "not working"]):
        extra = retrieve_context(vs, "file upload troubleshooting application error", k=2)
        context = context + "\n\n--- Additional Troubleshooting ---\n" + extra

    response = _build_response(
        department="Technical Support",
        persona="Sam | Technical Support Engineer",
        query=state["query"],
        context=context,
        customer_name=state.get("customer_name") or "Valued Customer",
    )

    return {
        **state,
        "department": "Technical Support",
        "retrieved_context": context,
        "draft_response": response,
        "history_display": history_text,
        "requires_approval": False,
    }


# ── Billing Agent ─────────────────────────────────────────────────────────────

def billing_agent(state: CustomerSupportState) -> CustomerSupportState:
    """
    Handle Billing queries: invoices, payments, refunds.
    Flags high-risk requests (refunds, cancellations, etc.) for human approval.
    """
    print("[Billing Agent] Processing query...")
    vs = get_vector_store()
    context = retrieve_context(vs, state["query"])
    history_text = format_history_for_prompt(state.get("conversation_history", []))

    requires_approval = _needs_approval(state["query"])

    if requires_approval:
        print("[Billing Agent] ⚠️  HIGH-RISK request detected — flagging for human approval.")
        response = (
            f"Hello {state.get('customer_name') or 'Valued Customer'},\n\n"
            "Thank you for contacting ABC Technologies Billing Support.\n\n"
            f"I have received your request regarding: \"{state['query']}\"\n\n"
            "This request requires review and approval from our billing supervisor "
            "before it can be processed. Your case has been escalated and you will "
            "receive a response within 24 business hours.\n\n"
            "Reference information from our policy:\n\n"
            f"{context[:800]}\n\n"
            "Best regards,\nJordan | Billing Support Specialist\nABC Technologies Billing"
        )
    else:
        response = _build_response(
            department="Billing",
            persona="Jordan | Billing Support Specialist",
            query=state["query"],
            context=context,
            customer_name=state.get("customer_name") or "Valued Customer",
        )

    return {
        **state,
        "department": "Billing",
        "retrieved_context": context,
        "draft_response": response,
        "history_display": history_text,
        "requires_approval": requires_approval,
        "approval_status": "pending" if requires_approval else None,
    }


# ── Account Agent ─────────────────────────────────────────────────────────────

def account_agent(state: CustomerSupportState) -> CustomerSupportState:
    """Handle Account queries: password reset, profile updates, activation."""
    print("[Account Agent] Processing query...")
    vs = get_vector_store()
    context = retrieve_context(vs, state["query"])
    history_text = format_history_for_prompt(state.get("conversation_history", []))

    response = _build_response(
        department="Account Management",
        persona="Riley | Account Support Specialist",
        query=state["query"],
        context=context,
        customer_name=state.get("customer_name") or "Valued Customer",
    )

    return {
        **state,
        "department": "Account Management",
        "retrieved_context": context,
        "draft_response": response,
        "history_display": history_text,
        "requires_approval": False,
    }


# ── Memory Recall Agent ───────────────────────────────────────────────────────

def memory_recall_agent(state: CustomerSupportState) -> CustomerSupportState:
    """
    Handle Memory queries: customer asks about previous interactions.
    Retrieves history from SQLite and formulates a response — no RAG needed.

    NOTE: Unlike the other agents, this response's whole purpose IS to show
    history, so history_text is embedded here intentionally. To avoid this
    turn's response (which contains a full history dump) being re-saved and
    snowballing into FUTURE turns, the caller should save a short, generic
    summary string to memory for this turn instead of the full draft_response.
    See "history_display" / "memory_safe_response" below.
    """
    print("[Memory Recall Agent] Retrieving conversation history...")
    history = state.get("conversation_history", [])
    customer_name = state.get("customer_name") or "Valued Customer"

    if not history:
        response = (
            f"Hello {customer_name},\n\n"
            "I checked our records but could not find any previous interactions "
            "associated with your account. This may be your first contact with us, "
            "or your history may have been stored under a different customer ID.\n\n"
            "Please feel free to describe your current issue and I'll be happy to help!\n\n"
            "Best regards,\nABC Technologies Support Team"
        )
        memory_safe_response = response
        history_text = ""
    else:
        history_text = format_history_for_prompt(history)
        last_issues = [h for h in history if h["role"] == "customer"]
        last_issue_summary = last_issues[-1]["message"] if last_issues else "Not found"

        response = (
            f"Hello {customer_name},\n\n"
            "I've retrieved your previous support history from our records.\n\n"
            f"Your most recent support query was:\n\"{last_issue_summary}\"\n\n"
            f"Full conversation history:\n\n{history_text}\n\n"
            "Is there anything else I can help you with today?\n\n"
            "Best regards,\nABC Technologies Support Team"
        )

        # Short, clean version for persistence — avoids saving a giant
        # history dump that would get re-displayed and re-dumped on every
        # subsequent turn.
        memory_safe_response = (
            f"Hello {customer_name},\n\n"
            "I retrieved your previous support history and shared a summary "
            f"of your most recent query (\"{last_issue_summary}\") with you.\n\n"
            "Best regards,\nABC Technologies Support Team"
        )

    return {
        **state,
        "department": "Memory Recall",
        "draft_response": response,              # full version shown to customer
        "memory_safe_response": memory_safe_response,  # use THIS when saving to DB
        "history_display": history_text,
        "requires_approval": False,
        "retrieved_context": "N/A - Memory recall query",
    }