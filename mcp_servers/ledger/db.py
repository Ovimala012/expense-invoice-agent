"""SQLite ledger with synthetic data. Week 1 uses SQLite; we can swap to PostgreSQL later."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ledger.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    approved INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS budgets (
    department TEXT PRIMARY KEY,
    monthly_limit REAL NOT NULL,
    spent REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS invoices (
    invoice_number TEXT NOT NULL,
    vendor_id TEXT NOT NULL,
    department TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    PRIMARY KEY (vendor_id, invoice_number)
);
"""

SEED_VENDORS = [("V001", "Acme Office Supply", 1), ("V002", "CloudHost LLC", 1), ("V003", "Unknown Consulting", 0)]
SEED_BUDGETS = [("Engineering", 50000.0, 31250.0), ("Marketing", 20000.0, 18900.0)]
SEED_INVOICES = [("INV-1001", "V001", "Engineering", 1250.0, "paid")]


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(reset: bool = False) -> None:
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
    with connect() as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT OR IGNORE INTO vendors VALUES (?, ?, ?)", SEED_VENDORS)
        conn.executemany("INSERT OR IGNORE INTO budgets VALUES (?, ?, ?)", SEED_BUDGETS)
        conn.executemany("INSERT OR IGNORE INTO invoices VALUES (?, ?, ?, ?, ?)", SEED_INVOICES)
