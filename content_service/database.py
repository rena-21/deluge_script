"""
Order and revenue database — SQLite backend.
"""
import sqlite3
import uuid
from datetime import datetime, date
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

DB_PATH = Path(__file__).parent / "orders.db"


@dataclass
class Order:
    client_name: str
    client_email: str
    topic: str
    content_type: str      # "article" | "post" | "email" | "product_desc"
    language: str          # "fr" | "en" | "ar"
    word_count: int
    price: float
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    status: str = "pending"          # pending | generating | done | failed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    delivered_at: Optional[str] = None
    content_preview: Optional[str] = None


PRICES = {
    ("article", 500):   12.0,
    ("article", 1000):  18.0,
    ("article", 2000):  30.0,
    ("post", 150):       5.0,
    ("post", 300):       8.0,
    ("email", 300):      7.0,
    ("email", 500):     10.0,
    ("product_desc", 200): 6.0,
    ("product_desc", 400): 9.0,
}


def get_price(content_type: str, word_count: int) -> float:
    """Return the closest matching price for a content type + word count."""
    matches = {k: v for k, v in PRICES.items() if k[0] == content_type}
    if not matches:
        return round(word_count * 0.015, 2)
    closest_key = min(matches.keys(), key=lambda k: abs(k[1] - word_count))
    return matches[closest_key]


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                client_name TEXT NOT NULL,
                client_email TEXT NOT NULL,
                topic TEXT NOT NULL,
                content_type TEXT NOT NULL,
                language TEXT NOT NULL,
                word_count INTEGER NOT NULL,
                price REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                delivered_at TEXT,
                content_preview TEXT
            )
        """)
        conn.commit()


def save_order(order: Order):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO orders VALUES (
                :id, :client_name, :client_email, :topic,
                :content_type, :language, :word_count, :price,
                :status, :created_at, :delivered_at, :content_preview
            )
        """, order.__dict__)
        conn.commit()


def update_order_status(order_id: str, status: str, delivered_at: str = None, preview: str = None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            UPDATE orders SET status=?, delivered_at=?, content_preview=?
            WHERE id=?
        """, (status, delivered_at, preview, order_id))
        conn.commit()


def get_order(order_id: str) -> Optional[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        return dict(row) if row else None


def get_daily_revenue(target_date: date = None) -> dict:
    target_date = target_date or date.today()
    prefix = target_date.isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT * FROM orders
            WHERE created_at LIKE ? AND status='done'
        """, (f"{prefix}%",)).fetchall()
        orders = [dict(r) for r in rows]
    total = sum(o["price"] for o in orders)
    return {"date": prefix, "orders": len(orders), "revenue": round(total, 2), "details": orders}


def get_pending_orders() -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM orders WHERE status='pending' ORDER BY created_at"
        ).fetchall()
        return [dict(r) for r in rows]
