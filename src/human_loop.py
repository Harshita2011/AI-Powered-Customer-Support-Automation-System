"""
Task 8: Human-in-the-Loop Approval
=====================================
For high-risk requests (refunds, cancellations, closures, compensation,
escalation), the workflow pauses and waits for a human supervisor to
approve or reject before the final response is sent to the customer.

In a real deployment this would integrate with a ticketing system or
Slack bot. Here we simulate it with an interactive console prompt and
provide an auto-approve mode for demo purposes.
"""

import time
from src.state import CustomerSupportState

# Set to True to skip the interactive prompt during automated demos
AUTO_APPROVE = False
AUTO_APPROVE_DECISION = "approved"   # 'approved' | 'rejected'


def human_approval_node(state: CustomerSupportState) -> CustomerSupportState:
    """
    LangGraph node: pause for human supervisor review of high-risk requests.

    Displays the draft response and customer query to the supervisor, then
    waits for an 'approve' or 'reject' decision.

    Updates state fields:
      - approval_status : 'approved' | 'rejected'
      - draft_response  : updated with rejection note if rejected
    """
    print("\n" + "=" * 65)
    print("🔴  HUMAN-IN-THE-LOOP APPROVAL REQUIRED")
    print("=" * 65)
    print(f"Customer ID  : {state.get('customer_id', 'N/A')}")
    print(f"Customer Name: {state.get('customer_name', 'N/A')}")
    print(f"Intent       : {state.get('intent', 'N/A')}")
    print(f"Department   : {state.get('department', 'N/A')}")
    print(f"\nCustomer Query:\n  {state.get('query', '')}")
    print("\nDraft Response (for supervisor review):")
    print("-" * 65)
    print(state.get("draft_response", "No draft available."))
    print("-" * 65)

    if AUTO_APPROVE:
        decision = AUTO_APPROVE_DECISION
        print(f"\n[Auto-Mode] Supervisor decision: {decision.upper()}")
        time.sleep(0.5)
    else:
        # Interactive prompt for real use
        while True:
            decision = input(
                "\nSupervisor Decision — type 'approve' or 'reject': "
            ).strip().lower()
            if decision in ("approve", "approved"):
                decision = "approved"
                break
            elif decision in ("reject", "rejected"):
                decision = "rejected"
                break
            else:
                print("  Please enter 'approve' or 'reject'.")

    print(f"\n[Human Approval] Decision recorded: {decision.upper()}")
    print("=" * 65 + "\n")

    if decision == "approved":
        return {
            **state,
            "approval_status": "approved",
        }
    else:
        rejection_response = (
            f"Hello {state.get('customer_name') or 'Valued Customer'},\n\n"
            "Thank you for contacting ABC Technologies Support.\n\n"
            "After careful review, we are unable to process your request at this time. "
            "A support specialist will follow up with you within 24 business hours "
            "to discuss your options.\n\n"
            "We apologize for any inconvenience and appreciate your patience.\n\n"
            "Best regards,\nABC Technologies Support Team"
        )
        return {
            **state,
            "approval_status": "rejected",
            "draft_response": rejection_response,
        }
