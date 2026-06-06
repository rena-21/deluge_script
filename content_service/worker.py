"""
Background worker — processes pending orders continuously.
Run alongside the web server: python worker.py

Useful when running without FastAPI background tasks
(e.g. serverless deploy or simple VPS setup).
"""
import time
import logging
from datetime import datetime
from database import get_pending_orders, update_order_status
from generator import generate_content
from delivery import send_content_to_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

POLL_INTERVAL = 15  # seconds between checks


def process_one(order: dict):
    oid = order["id"]
    log.info(f"[#{oid}] Processing — {order['content_type']} / {order['language']} / {order['topic'][:40]}")
    update_order_status(oid, "generating")
    try:
        content = generate_content(
            order["topic"], order["content_type"], order["language"], order["word_count"]
        )
        send_content_to_client(order, content)
        update_order_status(oid, "done", delivered_at=datetime.now().isoformat(), preview=content[:200])
        log.info(f"[#{oid}] Done ✓  delivered to {order['client_email']}")
    except Exception as e:
        update_order_status(oid, "failed")
        log.error(f"[#{oid}] FAILED: {e}")


def run():
    log.info("Worker started — polling every %ds", POLL_INTERVAL)
    while True:
        pending = get_pending_orders()
        if pending:
            log.info(f"Found {len(pending)} pending order(s)")
            for order in pending:
                process_one(order)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
