# ABC Technologies — AI-Powered Customer Support Automation System
### Built with LangGraph

---

## Overview
This project implements an AI-powered Customer Support Automation System for ABC Technologies. It uses **LangGraph** for workflow orchestration, **FAISS** for RAG-based knowledge retrieval, and **SQLite** for persistent conversation memory.

---

## Architecture

```
START
  │
  ▼
Intent Classifier ──► Sales Agent ──────────────────────────► Supervisor ──► END
                  ──► Technical Agent ──────────────────────► Supervisor ──► END
                  ──► Billing Agent ──► [High Risk?]
                  │                         ├── YES ──► Human Approval ──► Supervisor ──► END
                  │                         └── NO  ──► Supervisor ──► END
                  ──► Account Agent ───────────────────────► Supervisor ──► END
                  ──► Memory Recall Agent ─────────────────► Supervisor ──► END
```

---

## Features (Tasks Completed)

| Task | Description | File |
|------|-------------|------|
| 1 | LangGraph Workflow | `src/graph.py` |
| 2 | State Structure | `src/state.py` |
| 3 | Intent Classification | `src/intent.py` |
| 4 | Conditional Routing | `src/router.py` |
| 5 | Department Agents (x4) | `src/agents.py` |
| 6 | RAG Pipeline (FAISS) | `src/rag.py` |
| 7 | SQLite Memory | `src/memory.py` |
| 8 | Human-in-the-Loop | `src/human_loop.py` |
| 9 | Supervisor Agent | `src/supervisor.py` |
| 10 | Demo with 5 Queries | `demo.py` |

---

## Project Structure

```
customer_support_system/
├── src/
│   ├── __init__.py
│   ├── state.py          # Task 2 — Shared state TypedDict
│   ├── intent.py         # Task 3 — Intent classification node
│   ├── router.py         # Task 4 — Conditional routing functions
│   ├── agents.py         # Task 5 — Sales, Technical, Billing, Account, Memory agents
│   ├── rag.py            # Task 6 — FAISS RAG pipeline
│   ├── memory.py         # Task 7 — SQLite conversation memory
│   ├── human_loop.py     # Task 8 — Human-in-the-loop approval node
│   ├── supervisor.py     # Task 9 — Supervisor quality review agent
│   └── graph.py          # Task 1 — Full LangGraph graph assembly
├── docs/
│   ├── company_policy.txt
│   ├── pricing_guide.txt
│   ├── technical_manual.txt
│   └── faq.txt
├── diagrams/
│   └── workflow.png      # LangGraph architecture diagram
├── demo.py               # Task 10 — Run all 5 sample queries
├── memory.db             # SQLite database
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone / Extract the project
```bash
unzip customer_support_system.zip
cd customer_support_system
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the demo
```bash
python demo.py
```

---

## Demo Queries

| # | Query | Expected Path |
|---|-------|---------------|
| 1 | What are the pricing plans available? | Sales Agent |
| 2 | I forgot my account password. | Account Agent |
| 3 | My application crashes when I upload a file. | Technical Support Agent |
| 4 | I need a refund for my annual subscription. | Billing Agent → **Human Approval** |
| 5 | What was my previous support issue? | Memory Recall Agent |

---

## Human-in-the-Loop

For refund, cancellation, account closure, compensation, or escalation requests, the system automatically pauses and requires supervisor approval.

---

## SQLite Memory Schema

```sql
CREATE TABLE conversations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT    NOT NULL,
    timestamp   TEXT    NOT NULL,
    role        TEXT    NOT NULL,   -- 'customer' | 'agent'
    message     TEXT    NOT NULL,
    intent      TEXT,
    department  TEXT
);
```

The database is stored at `memory.db` in the project root.

---

## Knowledge Base Documents

| Document | Content |
|----------|---------|
| `company_policy.txt` | Refund, cancellation, closure, compensation, SLA policies |
| `pricing_guide.txt`  | Subscription plans, pricing, discounts, billing |
| `technical_manual.txt` | Installation, troubleshooting, error codes |
| `faq.txt`            | General, billing, account, technical FAQs |

---

## Support Departments

| Department | Handles |
|------------|---------|
| Sales | Pricing, plans, product information, trials |
| Technical Support | Errors, crashes, installation, configuration |
| Billing | Invoices, payments, refunds, cancellations |
| Account Management | Password reset, profile updates, activation |

---

## License
Assignment project for educational purposes — ABC Technologies (fictional).
