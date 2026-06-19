"""
LocallySells voice-search tool handler for Vapi.

Vapi calls this endpoint when the agent invokes the `search_products` custom tool.
It searches the real LocallySells master catalog (catalog.csv, 198 products) and
returns a concise result the agent speaks back.

Search logic mirrors the production endpoint
(apps/retailer/src/app/api/master-catalog/search/route.ts):
  - barcode exact-match shortcut
  - case-insensitive substring match on name/brand/sku/barcode
  - optional category filter
  - order by confidence_score desc, then name
  - limit

Run locally:
  uv run uvicorn app:app --host 0.0.0.0 --port 8000
"""

import csv
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

CATALOG_PATH = Path(__file__).parent / "catalog.csv"

# ---- load catalog once at startup ------------------------------------------

def _load_catalog():
    rows = []
    with open(CATALOG_PATH, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                r["_price"] = float(r["price"]) if r.get("price") else None
            except ValueError:
                r["_price"] = None
            try:
                r["_conf"] = int(r["confidence_score"]) if r.get("confidence_score") else 0
            except ValueError:
                r["_conf"] = 0
            rows.append(r)
    return rows

CATALOG = _load_catalog()

# Map spoken/loose category words to the catalog's category values.
CATEGORY_ALIASES = {
    "cigarette": "cigarettes", "cigarettes": "cigarettes", "smokes": "cigarettes",
    "cigar": "cigars", "cigars": "cigars",
    "vape": "vape", "vapes": "vape", "e-cig": "vape", "ecig": "vape",
    "e-cigarette": "vape", "disposable": "vape",
    "hookah": "hookah", "shisha": "hookah",
    "pouch": "nicotine", "pouches": "nicotine", "nicotine": "nicotine",
    "zyn": "nicotine",
    "cbd": "cbd",
    "accessory": "accessories", "accessories": "accessories",
    "lighter": "accessories", "lighters": "accessories",
}


def search(query: str = "", category: str = "", limit: int = 20):
    q = (query or "").strip().lower()
    cat = (category or "").strip().lower()
    cat = CATEGORY_ALIASES.get(cat, cat)

    # barcode exact-match shortcut
    if q.isdigit() and 8 <= len(q) <= 14:
        exact = [r for r in CATALOG if r.get("barcode", "").strip() == q]
        if exact:
            return exact[:5]

    results = CATALOG
    if cat:
        results = [r for r in results if r.get("category", "").strip().lower() == cat]
    if q:
        results = [
            r for r in results
            if q in r.get("name", "").lower()
            or q in r.get("brand", "").lower()
            or q in r.get("sku", "").lower()
            or q in r.get("barcode", "").lower()
            or q in r.get("flavor", "").lower()
        ]

    results = sorted(results, key=lambda r: (-r["_conf"], r.get("name", "")))
    return results[: min(limit, 100)]


def _fmt_product(r):
    price = f"${r['_price']:.2f}" if r["_price"] is not None else "price n/a"
    parts = [r.get("name", "Unknown"), price]
    if r.get("format"):
        parts.append(r["format"])
    if r.get("flavor") and r["flavor"].lower() != "regular":
        parts.append(r["flavor"])
    return " — ".join(parts)


def build_result_string(query, category, products):
    """A compact, speakable summary the agent can read from. Top 3 highlighted."""
    if not products:
        scope = f' matching "{query}"' if query else ""
        scope += f" in {category}" if category else ""
        return f"No products found{scope}. Suggest the caller try a different brand or category."

    top = products[:3]
    lines = [f"Found {len(products)} match(es)."]
    lines.append("Top results:")
    for r in top:
        lines.append("  - " + _fmt_product(r))
    if len(products) > 3:
        extra = ", ".join(p.get("name", "") for p in products[3:8])
        lines.append(f"Also available: {extra}.")
    return "\n".join(lines)


# ---- Vapi payload parsing ---------------------------------------------------

def _extract_tool_calls(body: dict):
    """Return list of (tool_call_id, args_dict). Handles Vapi message shapes."""
    msg = body.get("message", body)
    calls = []

    # Current Vapi shape: message.toolCallList[] or message.toolCalls[]
    for tc in (msg.get("toolCallList") or msg.get("toolCalls") or []):
        tc_id = tc.get("id") or tc.get("toolCallId")
        fn = tc.get("function") or tc
        args = fn.get("arguments", {})
        if isinstance(args, str):
            import json
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        calls.append((tc_id, args or {}))

    # Legacy single functionCall shape
    if not calls and msg.get("functionCall"):
        fc = msg["functionCall"]
        args = fc.get("parameters", {})
        calls.append((body.get("id") or "call_0", args or {}))

    return calls


# ---- Tier 2: ordering (mock cart + order) ----------------------------------
# In-memory carts keyed by the Vapi call id, so concurrent demo calls don't mix.
# This is a hackathon mock: no DB write, no payment. It proves the voice flow.

import random
import string

CARTS = {}  # { call_id: [ {name, price, qty}, ... ] }


def _call_id(body: dict) -> str:
    msg = body.get("message", body)
    call = msg.get("call") or {}
    return call.get("id") or "default"


def _cart_total(cart):
    return sum((i["price"] or 0) * i["qty"] for i in cart)


def _best_match(name: str):
    res = search(name, "", 5)
    return res[0] if res else None


def _order_number():
    return "LS-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


app = FastAPI(title="LocallySells Voice Search")


@app.get("/")
def health():
    return {"ok": True, "catalog_size": len(CATALOG)}


@app.get("/search")
def search_get(q: str = "", category: str = "", limit: int = 20):
    """Plain REST for quick manual testing."""
    products = search(q, category, limit)
    return {"products": products, "summary": build_result_string(q, category, products)}


@app.post("/search_products")
async def search_products(request: Request):
    """Vapi custom-tool webhook."""
    body = await request.json()
    calls = _extract_tool_calls(body)

    if not calls:
        # Allow direct {query, category} POST for testing
        args = body if isinstance(body, dict) else {}
        products = search(args.get("query", ""), args.get("category", ""), args.get("limit", 20))
        return {"summary": build_result_string(args.get("query", ""), args.get("category", ""), products),
                "products": products[:8]}

    results = []
    for tc_id, args in calls:
        query = args.get("query") or args.get("q") or ""
        category = args.get("category") or ""
        limit = int(args.get("limit") or 20)
        products = search(query, category, limit)
        results.append({
            "toolCallId": tc_id,
            "result": build_result_string(query, category, products),
        })

    return JSONResponse({"results": results})


@app.post("/add_to_cart")
async def add_to_cart(request: Request):
    """Vapi tool: add a product (by name) to the caller's cart."""
    body = await request.json()
    cart_id = _call_id(body)
    calls = _extract_tool_calls(body) or [("call_0", body if isinstance(body, dict) else {})]

    results = []
    for tc_id, args in calls:
        name = args.get("product_name") or args.get("name") or args.get("query") or ""
        try:
            qty = max(1, int(args.get("quantity") or 1))
        except (TypeError, ValueError):
            qty = 1

        prod = _best_match(name)
        if not prod:
            res = f'I could not find "{name}" in the catalog. Ask the caller to try another product or brand.'
        else:
            cart = CARTS.setdefault(cart_id, [])
            cart.append({"name": prod["name"], "price": prod["_price"], "qty": qty})
            total = _cart_total(cart)
            count = sum(i["qty"] for i in cart)
            res = (
                f'Added {qty} x {prod["name"]} at ${prod["_price"]:.2f} each. '
                f'Cart now has {count} item(s), total ${total:.2f}.'
            )
        results.append({"toolCallId": tc_id, "result": res})

    return JSONResponse({"results": results})


@app.post("/view_cart")
async def view_cart(request: Request):
    """Vapi tool: read back the current cart."""
    body = await request.json()
    cart_id = _call_id(body)
    calls = _extract_tool_calls(body) or [("call_0", {})]

    cart = CARTS.get(cart_id, [])
    if not cart:
        summary = "The cart is empty."
    else:
        lines = [f'{i["qty"]} x {i["name"]} (${i["price"]:.2f} each)' for i in cart]
        summary = "Cart: " + "; ".join(lines) + f". Total ${_cart_total(cart):.2f}."

    return JSONResponse({"results": [{"toolCallId": tc, "result": summary} for tc, _ in calls]})


@app.post("/place_order")
async def place_order(request: Request):
    """Vapi tool: confirm + place the order for whatever is in the cart."""
    body = await request.json()
    cart_id = _call_id(body)
    calls = _extract_tool_calls(body) or [("call_0", body if isinstance(body, dict) else {})]

    results = []
    for tc_id, args in calls:
        address = args.get("delivery_address") or args.get("address") or ""
        cart = CARTS.get(cart_id, [])

        if not cart:
            res = "The cart is empty, so there's nothing to order. Help the caller add a product first."
        elif not address:
            res = "I need a delivery address before placing the order. Ask the caller where to deliver."
        else:
            order_no = _order_number()
            total = _cart_total(cart)
            items = ", ".join(f'{i["qty"]} x {i["name"]}' for i in cart)
            CARTS[cart_id] = []  # clear after ordering
            res = (
                f"Order {order_no} confirmed: {items}. Total ${total:.2f}, "
                f"delivering to {address}. Estimated delivery about 45 minutes. "
                f"Remind the caller that a valid 21-plus ID is required at the door."
            )
        results.append({"toolCallId": tc_id, "result": res})

    return JSONResponse({"results": results})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
