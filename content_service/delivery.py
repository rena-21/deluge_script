"""
Email delivery of generated content to clients.
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path


def _smtp_connection():
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    server = smtplib.SMTP(host, port)
    server.starttls()
    server.login(user, password)
    return server, user


def _save_content_file(order_id: str, content: str) -> Path:
    output_dir = Path(__file__).parent / "generated"
    output_dir.mkdir(exist_ok=True)
    filepath = output_dir / f"order_{order_id}.txt"
    filepath.write_text(content, encoding="utf-8")
    return filepath


def send_content_to_client(order: dict, content: str):
    """Send the generated content as an email attachment to the client."""
    filepath = _save_content_file(order["id"], content)
    server, sender = _smtp_connection()

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = order["client_email"]
    msg["Subject"] = f"[Order #{order['id']}] Your content is ready!"

    body = f"""Hello {order['client_name']},

Your content order is ready! Here are the details:

  Order ID   : #{order['id']}
  Topic      : {order['topic']}
  Type       : {order['content_type']}
  Language   : {order['language']}
  Words      : ~{order['word_count']}

The content is attached to this email as a text file.

Thank you for your order!

---
ContentAI Service
"""
    msg.attach(MIMEText(body, "plain"))

    with open(filepath, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename=order_{order['id']}.txt")
    msg.attach(part)

    try:
        server.sendmail(sender, order["client_email"], msg.as_string())
    finally:
        server.quit()

    return filepath


def send_order_confirmation(order: dict):
    """Send a confirmation email when an order is placed."""
    server, sender = _smtp_connection()

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = order["client_email"]
    msg["Subject"] = f"[Order #{order['id']}] Confirmed — We're working on it!"

    body = f"""Hello {order['client_name']},

Thank you for your order! Here's a summary:

  Order ID   : #{order['id']}
  Topic      : {order['topic']}
  Type       : {order['content_type']}
  Language   : {order['language']}
  Words      : ~{order['word_count']}
  Price      : {order['price']}€

Your content will be delivered to this email within the hour.

---
ContentAI Service
"""
    msg.attach(MIMEText(body, "plain"))
    try:
        server.sendmail(sender, order["client_email"], msg.as_string())
    finally:
        server.quit()
