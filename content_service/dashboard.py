"""
CLI revenue dashboard — run with: python dashboard.py
"""
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "orders.db"

TARGET_DAILY = 100.0


def _query(sql: str, params=()):
    if not DB_PATH.exists():
        return []
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def print_dashboard():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    # -- Daily stats --
    daily = _query(
        "SELECT COUNT(*) as n, COALESCE(SUM(price),0) as rev FROM orders WHERE created_at LIKE ? AND status='done'",
        (f"{today.isoformat()}%",)
    )[0]

    # -- Weekly stats --
    weekly = _query(
        "SELECT COUNT(*) as n, COALESCE(SUM(price),0) as rev FROM orders WHERE created_at >= ? AND status='done'",
        (week_start.isoformat(),)
    )[0]

    # -- Pending --
    pending = _query("SELECT COUNT(*) as n FROM orders WHERE status='pending'")[0]["n"]
    generating = _query("SELECT COUNT(*) as n FROM orders WHERE status='generating'")[0]["n"]

    # -- Last 5 orders --
    recent = _query("SELECT * FROM orders ORDER BY created_at DESC LIMIT 5")

    bar_filled = int((daily["rev"] / TARGET_DAILY) * 30)
    bar = "█" * bar_filled + "░" * (30 - bar_filled)
    pct = min(100, round(daily["rev"] / TARGET_DAILY * 100))

    print("\n" + "=" * 52)
    print("   💰  ContentAI  —  Revenue Dashboard")
    print("=" * 52)
    print(f"  📅  Today ({today.isoformat()})")
    print(f"      Orders done  : {daily['n']}")
    print(f"      Revenue      : {daily['rev']:.2f}€  /  goal: {TARGET_DAILY:.0f}€")
    print(f"      [{bar}] {pct}%")
    print()
    print(f"  📆  This week (since {week_start.isoformat()})")
    print(f"      Orders done  : {weekly['n']}")
    print(f"      Revenue      : {weekly['rev']:.2f}€")
    print()
    print(f"  ⏳  Queue  →  {pending} pending,  {generating} generating")
    print()
    print("  🕐  Last 5 orders:")
    print(f"  {'ID':>8}  {'Type':>12}  {'Lang':>4}  {'Price':>6}  {'Status':>10}  Client")
    print("  " + "-" * 60)
    for o in recent:
        print(f"  #{o['id']:>7}  {o['content_type']:>12}  {o['language']:>4}  {o['price']:>5.2f}€  {o['status']:>10}  {o['client_name'][:18]}")
    print("=" * 52 + "\n")

    needed = max(0, TARGET_DAILY - daily["rev"])
    if needed == 0:
        print("  🎉  Daily goal REACHED! Alhamdulillah!\n")
    else:
        avg_price = daily["rev"] / daily["n"] if daily["n"] else 12.0
        orders_needed = round(needed / avg_price) if avg_price else "-"
        print(f"  📊  Still need {needed:.2f}€ today  ≈  {orders_needed} more orders\n")


if __name__ == "__main__":
    print_dashboard()
