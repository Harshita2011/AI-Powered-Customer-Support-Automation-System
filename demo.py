"""
Demo Script — Interactive Mode
================================
Runs the AI Customer Support Automation System with real user input.
Type your query, enter your name and customer ID, and get a response.
Type 'quit' or 'exit' to stop.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# Auto-approve high-risk requests for demo
#import src.human_loop as hl
#hl.AUTO_APPROVE = True
#hl.AUTO_APPROVE_DECISION = "approved"

from src.graph import build_graph, run_query

DIVIDER = "\n" + "=" * 65 + "\n"
THIN    = "-" * 65


def print_result(query: str, state: dict):
    """Pretty-print the result of a query."""
    print(DIVIDER)
    print(f"  Customer   : {state.get('customer_name')} ({state.get('customer_id')})")
    print(f"  Query      : {query}")
    print(f"  Intent     : {state.get('intent')}")
    print(f"  Department : {state.get('department')}")
    approval = state.get('approval_status')
    if approval:
        print(f"  Approval   : {approval.upper()}")
    print(f"  Supervisor : {state.get('supervisor_notes')}")
    print(THIN)
    print("  RESPONSE:")
    print(THIN)
    final = state.get("final_response", "No response generated.")
    for line in final.split("\n"):
        print("  " + line)
    print(DIVIDER)


def get_customer_info() -> tuple[str, str]:
    """Prompt once for customer name and ID at session start."""
    print(DIVIDER)
    print("  ABC TECHNOLOGIES — AI CUSTOMER SUPPORT SYSTEM")
    print("  Built with LangGraph")
    print(DIVIDER)
    print("  Please enter your details to begin.\n")

    name = input("  Your name       : ").strip()
    if not name:
        name = "Customer"

    cust_id = input("  Your customer ID: ").strip()
    if not cust_id:
        cust_id = f"CUST-{name[:4].upper()}"

    print(f"\n  Welcome, {name}! (ID: {cust_id})")
    print("  Type your support query below. Type 'quit' to exit.\n")
    return name, cust_id


def main():
    # Build graph once
    print("\n[System] Starting AI Customer Support System...")
    graph = build_graph()
    print("[System] System ready.\n")

    # Get customer info once per session
    customer_name, customer_id = get_customer_info()

    session_count = 0

    while True:
        print(THIN)
        query = input("  Your query : ").strip()

        if not query:
            print("  Please enter a query.")
            continue

        if query.lower() in ("quit", "exit", "q", "bye"):
            print(DIVIDER)
            print(f"  Thank you for contacting ABC Technologies, {customer_name}!")
            print(f"  Total queries handled this session: {session_count}")
            print(f"  Your conversation history is saved under ID: {customer_id}")
            print(DIVIDER)
            break

        # Run through LangGraph
        print(f"\n[System] Processing your query...\n")
        try:
            state = run_query(
                graph,
                customer_id=customer_id,
                query=query,
                customer_name=customer_name,
            )
            print_result(query, state)
            session_count += 1

        except Exception as e:
            print(f"\n[Error] Something went wrong: {e}")
            print("  Please try again or rephrase your query.\n")

        # Ask if they want to continue
        again = input("  Do you have another query? (yes/no) : ").strip().lower()
        if again in ("no", "n", "quit", "exit"):
            print(DIVIDER)
            print(f"  Thank you for contacting ABC Technologies, {customer_name}!")
            print(f"  Total queries handled this session: {session_count}")
            print(f"  Your conversation history is saved under ID: {customer_id}")
            print(DIVIDER)
            break


if __name__ == "__main__":
    main()
