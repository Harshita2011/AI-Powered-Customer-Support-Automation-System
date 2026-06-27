"""
Task 7: SQLite Memory
=====================
Stores and retrieves customer conversation history using SQLite.
Supports per-customer history so the agent can answer questions
like "What was my previous issue?"
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional

# ── Database path ──────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory.db")


def init_db():
    """Create the conversations table if it does not already exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT    NOT NULL,
            timestamp   TEXT    NOT NULL,
            role        TEXT    NOT NULL,   -- 'customer' or 'agent'
            message     TEXT    NOT NULL,
            intent      TEXT,
            department  TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"[Memory] SQLite database ready at: {DB_PATH}")


def save_interaction(
    customer_id: str,
    customer_message: str,
    agent_response: str,
    intent: Optional[str] = None,
    department: Optional[str] = None,
):
    """
    Persist one full customer ↔ agent exchange to SQLite.

    Args:
        customer_id      : Unique customer identifier.
        customer_message : The raw customer query.
        agent_response   : The final response sent to the customer.
        intent           : Classified intent (e.g. 'Billing').
        department       : Routed department (e.g. 'Billing Support').
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ts = datetime.now().isoformat()

    cursor.execute(
        """INSERT INTO conversations
           (customer_id, timestamp, role, message, intent, department)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (customer_id, ts, "customer", customer_message, intent, department),
    )
    cursor.execute(
        """INSERT INTO conversations
           (customer_id, timestamp, role, message, intent, department)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (customer_id, ts, "agent", agent_response, intent, department),
    )
    conn.commit()
    conn.close()
    print(f"[Memory] Saved interaction for customer '{customer_id}'.")


def get_history(customer_id: str, limit: int = 10) -> List[dict]:
    """
    Retrieve the most recent conversation turns for a customer.

    Args:
        customer_id : The customer to look up.
        limit       : Maximum number of rows to return.

    Returns:
        List of dicts with keys: role, message, timestamp, intent, department.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT role, message, timestamp, intent, department
           FROM conversations
           WHERE customer_id = ?
           ORDER BY id DESC
           LIMIT ?""",
        (customer_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()

    history = [
        {
            "role": row[0],
            "message": row[1],
            "timestamp": row[2],
            "intent": row[3],
            "department": row[4],
        }
        for row in reversed(rows)   # chronological order
    ]
    print(f"[Memory] Retrieved {len(history)} history entries for '{customer_id}'.")
    return history


def format_history_for_prompt(history: List[dict]) -> str:
    """
    Convert raw history rows into a readable string suitable for an LLM prompt.

    Args:
        history : List returned by get_history().

    Returns:
        Human-readable conversation transcript.
    """
    if not history:
        return "No previous conversation history found for this customer."

    lines = ["=== Previous Conversation History ==="]
    for entry in history:
        role_label = "Customer" if entry["role"] == "customer" else "Agent"
        dept = f" [{entry['department']}]" if entry.get("department") else ""
        lines.append(
            f"[{entry['timestamp'][:19]}]{dept}\n{role_label}: {entry['message']}"
        )
    lines.append("=== End of History ===")
    return "\n\n".join(lines)


# Initialise database on import
init_db()
