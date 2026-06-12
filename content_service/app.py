"""
FastAPI web server — order form + order processing endpoint.
"""
from fastapi import FastAPI, Form, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from datetime import datetime

from database import Order, get_price, init_db, save_order, update_order_status, get_order
from generator import generate_content
from delivery import send_content_to_client, send_order_confirmation

app = FastAPI(title="ContentAI Service")
init_db()


ORDER_FORM_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ContentAI — Order Content</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', sans-serif; background: #f0f4f8; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }}
    .card {{ background: white; border-radius: 16px; padding: 40px; max-width: 520px; width: 100%; box-shadow: 0 4px 24px rgba(0,0,0,.1); }}
    h1 {{ font-size: 1.8rem; color: #1a1a2e; margin-bottom: 6px; }}
    .subtitle {{ color: #666; margin-bottom: 28px; font-size: .95rem; }}
    label {{ display: block; font-weight: 600; color: #333; margin-bottom: 6px; font-size: .9rem; }}
    input, select, textarea {{ width: 100%; padding: 11px 14px; border: 1.5px solid #dde3ec; border-radius: 8px; font-size: .95rem; margin-bottom: 18px; transition: border .2s; }}
    input:focus, select:focus, textarea:focus {{ outline: none; border-color: #6c63ff; }}
    textarea {{ resize: vertical; min-height: 80px; }}
    .price-box {{ background: #f7f5ff; border: 1.5px solid #6c63ff; border-radius: 8px; padding: 14px 18px; margin-bottom: 20px; color: #4b44cc; font-weight: 700; font-size: 1.05rem; }}
    button {{ width: 100%; padding: 14px; background: #6c63ff; color: white; border: none; border-radius: 10px; font-size: 1rem; font-weight: 700; cursor: pointer; transition: background .2s; }}
    button:hover {{ background: #574fd6; }}
    .halal {{ display: inline-block; background: #e8f5e9; color: #2e7d32; border-radius: 20px; padding: 3px 12px; font-size: .8rem; font-weight: 600; margin-bottom: 24px; }}
  </style>
  <script>
    const prices = {{
      "article-500": 12, "article-1000": 18, "article-2000": 30,
      "post-150": 5, "post-300": 8,
      "email-300": 7, "email-500": 10,
      "product_desc-200": 6, "product_desc-400": 9
    }};
    function updatePrice() {{
      const type = document.getElementById('content_type').value;
      const words = document.getElementById('word_count').value;
      const key = type + '-' + words;
      const price = prices[key] || (words * 0.015).toFixed(2);
      document.getElementById('price-display').textContent = price + ' €';
    }}
  </script>
</head>
<body>
  <div class="card">
    <h1>✍️ ContentAI</h1>
    <p class="subtitle">Professional AI-generated content, delivered to your inbox.</p>
    <span class="halal">✅ Halal Business</span>

    <form action="/order" method="post">
      <label>Your name</label>
      <input type="text" name="client_name" placeholder="Mohammed Dupont" required>

      <label>Your email</label>
      <input type="email" name="client_email" placeholder="you@example.com" required>

      <label>Content topic</label>
      <textarea name="topic" placeholder="Ex: Benefits of intermittent fasting for Muslims during Ramadan" required></textarea>

      <label>Content type</label>
      <select name="content_type" id="content_type" onchange="updatePrice()">
        <option value="article">Blog Article</option>
        <option value="post">Social Media Post</option>
        <option value="email">Marketing Email</option>
        <option value="product_desc">Product Description</option>
      </select>

      <label>Language</label>
      <select name="language">
        <option value="fr">Français</option>
        <option value="en">English</option>
        <option value="ar">العربية</option>
      </select>

      <label>Word count</label>
      <select name="word_count" id="word_count" onchange="updatePrice()">
        <option value="500">~500 words</option>
        <option value="1000">~1000 words</option>
        <option value="2000">~2000 words</option>
        <option value="150">~150 words (post)</option>
        <option value="300">~300 words</option>
        <option value="200">~200 words (product)</option>
        <option value="400">~400 words (product)</option>
      </select>

      <div class="price-box">Price: <span id="price-display">12 €</span></div>
      <button type="submit">Place Order & Pay →</button>
    </form>
  </div>
</body>
</html>
"""

SUCCESS_HTML = """
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Order Confirmed</title>
<style>body{{font-family:'Segoe UI',sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#f0f4f8}}
.card{{background:white;border-radius:16px;padding:40px;max-width:440px;text-align:center;box-shadow:0 4px 24px rgba(0,0,0,.1)}}
h2{{color:#2e7d32;font-size:1.6rem;margin-bottom:10px}} p{{color:#555;line-height:1.6}}</style></head>
<body><div class="card">
<h2>✅ Order #{order_id} Confirmed!</h2>
<p>Hi <strong>{name}</strong>!<br><br>Your <strong>{content_type}</strong> about <em>"{topic}"</em> is being generated now.<br><br>
You'll receive it at <strong>{email}</strong> within the hour.<br><br>
<span style="font-size:.85rem;color:#888">Price: {price}€ — Thank you for trusting ContentAI!</span></p>
</div></body></html>
"""


def process_order_background(order: Order):
    """Generate content and deliver it — runs in background after response is sent."""
    try:
        update_order_status(order.id, "generating")
        content = generate_content(order.topic, order.content_type, order.language, order.word_count)
        send_content_to_client(order.__dict__, content)
        update_order_status(
            order.id, "done",
            delivered_at=datetime.now().isoformat(),
            preview=content[:200]
        )
    except Exception as e:
        update_order_status(order.id, "failed")
        raise e


@app.get("/", response_class=HTMLResponse)
def order_form():
    return ORDER_FORM_HTML


@app.post("/order", response_class=HTMLResponse)
def place_order(
    background_tasks: BackgroundTasks,
    client_name: str = Form(...),
    client_email: str = Form(...),
    topic: str = Form(...),
    content_type: str = Form(...),
    language: str = Form(...),
    word_count: int = Form(...),
):
    price = get_price(content_type, word_count)
    order = Order(
        client_name=client_name,
        client_email=client_email,
        topic=topic,
        content_type=content_type,
        language=language,
        word_count=word_count,
        price=price,
    )
    save_order(order)
    send_order_confirmation(order.__dict__)
    background_tasks.add_task(process_order_background, order)

    return SUCCESS_HTML.format(
        order_id=order.id,
        name=client_name,
        content_type=content_type,
        topic=topic,
        email=client_email,
        price=price,
    )


@app.get("/order/{order_id}")
def check_order(order_id: str):
    order = get_order(order_id.upper())
    if not order:
        return JSONResponse({"error": "Order not found"}, status_code=404)
    order.pop("content_preview", None)
    return order
