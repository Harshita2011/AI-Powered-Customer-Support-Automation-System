"""
Task 3: Intent Classification Node
===================================
Uses an LLM to classify the customer query into one of five intents:
  - Sales        : pricing, plans, product info
  - Technical    : errors, crashes, login, installation
  - Billing      : invoices, refunds, payments
  - Account      : password reset, profile, activation
  - Memory       : asking about previous interactions
"""

import re
from src.state import CustomerSupportState
from src.memory import get_history, format_history_for_prompt


# ── Simple LLM-free rule-based classifier (no API key needed for demo) ────────
# In production replace with an actual LLM call.

INTENT_RULES = {
    "Memory": [
        "previous", "last time", "before", "history", "earlier",
        "what did i", "what was my", "past issue", "previous issue",
        "last issue", "recall", "remember",
    ],
    "Sales": [
        "pricing", "price", "plan", "plans", "subscription", "cost",
        "how much", "packages", "tier", "upgrade", "trial", "discount",
        "features", "what does", "buy", "purchase",
    ],
    "Technical": [
        "crash", "error", "bug", "not working", "broken", "fail",
        "install", "login", "can't log", "cannot log", "upload",
        "slow", "freeze", "500", "403", "404", "issue with app",
        "application", "software", "configuration", "setup",
    ],
    "Billing": [
        "refund", "invoice", "payment", "charge", "bill", "receipt",
        "overcharged", "money", "cancel subscription", "renewal",
        "annual subscription", "credit card", "transaction",
    ],
    "Account": [
        "password", "reset", "forgot", "profile", "username",
        "email change", "account locked", "activate", "deactivate",
        "close account", "delete account", "2fa", "two factor",
        "authentication",
    ],
}


def classify_intent(query: str) -> str:
    """
    Rule-based intent classifier.
    Scores each intent by counting keyword matches and returns the winner.
    Defaults to 'Sales' if no keywords match.
    """
    query_lower = query.lower()
    scores = {intent: 0 for intent in INTENT_RULES}

    for intent, keywords in INTENT_RULES.items():
        for kw in keywords:
            if kw in query_lower:
                scores[intent] += 1

    # Memory check gets priority if any memory keyword matched
    if scores["Memory"] > 0:
        return "Memory"

    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return "Sales"   # safe default
    return best


# ── LangGraph Node ────────────────────────────────────────────────────────────

def intent_classification_node(state: CustomerSupportState) -> CustomerSupportState:
    """
    LangGraph node: classify query intent and load conversation history from SQLite.

    Updates state fields:
      - intent               : classified intent string
      - conversation_history : loaded from SQLite memory
    """
    query = state["query"]
    customer_id = state.get("customer_id", "unknown")

    print(f"\n[Intent] Classifying query: '{query}'")

    # 1. Load conversation history from SQLite
    history = get_history(customer_id)
    formatted_history = format_history_for_prompt(history)

    # 2. Classify intent
    intent = classify_intent(query)
    print(f"[Intent] Classified as: {intent}")

    return {
        **state,
        "intent": intent,
        "conversation_history": history,
    }
