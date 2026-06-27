-- ABC Technologies Customer Support System
-- SQLite Memory Schema
-- Task 7 — memory.db

-- ============================================================
-- TABLE: conversations
-- Stores every customer <-> agent interaction turn.
-- Keyed by customer_id so history can be retrieved per customer.
-- ============================================================

CREATE TABLE IF NOT EXISTS conversations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,  -- auto row ID
    customer_id TEXT    NOT NULL,                   -- unique customer identifier
    timestamp   TEXT    NOT NULL,                   -- ISO-8601 datetime string
    role        TEXT    NOT NULL                    -- 'customer' | 'agent'
                CHECK(role IN ('customer', 'agent')),
    message     TEXT    NOT NULL,                   -- raw message content
    intent      TEXT,                               -- classified intent (nullable)
    department  TEXT                                -- routed department (nullable)
);

-- Index for fast per-customer history lookup
CREATE INDEX IF NOT EXISTS idx_customer_id ON conversations(customer_id);
CREATE INDEX IF NOT EXISTS idx_timestamp   ON conversations(timestamp);

-- ============================================================
-- EXAMPLE DATA (for reference only)
-- ============================================================

-- INSERT INTO conversations VALUES
--   (1, 'CUST-004', '2026-06-25T10:00:00', 'customer',
--    'I need a refund for my annual subscription.', 'Billing', 'Billing'),
--   (2, 'CUST-004', '2026-06-25T10:00:00', 'agent',
--    'Hello David, your refund request has been escalated...', 'Billing', 'Billing');

-- ============================================================
-- QUERY EXAMPLES
-- ============================================================

-- Get all history for a customer (chronological):
-- SELECT role, message, timestamp, intent, department
--   FROM conversations
--  WHERE customer_id = 'CUST-004'
--  ORDER BY id ASC;

-- Get last N interactions:
-- SELECT role, message, timestamp, intent, department
--   FROM conversations
--  WHERE customer_id = ?
--  ORDER BY id DESC
--  LIMIT 10;
