"""
Register the Tier 2 ordering tools (add_to_cart, view_cart, place_order) with Vapi
and attach them to the existing LocallySells assistant, alongside search_products.

Usage:
  VAPI_API_KEY=... ASSISTANT_ID=... BASE_URL=https://<tunnel> uv run python add_ordering.py
"""

import json
import os
import sys
import urllib.request
import urllib.error

API = "https://api.vapi.ai"
KEY = os.environ.get("VAPI_API_KEY")
ASSISTANT_ID = os.environ.get("ASSISTANT_ID", "d52222e2-8657-4035-9a84-6068eee88de0")
BASE = os.environ.get("BASE_URL", "https://totals-accountability-behavior-hdtv.trycloudflare.com").rstrip("/")

if not KEY:
    sys.exit("Set VAPI_API_KEY.")

HEADERS = {
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}
SYSTEM_PROMPT = open(os.path.join(os.path.dirname(__file__), "system-prompt.md")).read()


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode())
        raise


TOOLS = [
    {
        "name": "add_to_cart",
        "description": "Add a product to the caller's cart when they say they want to buy it. Call with the product name and quantity.",
        "url": f"{BASE}/add_to_cart",
        "params": {
            "product_name": {"type": "string", "description": "Name or brand of the product to add, e.g. 'Marlboro Red'."},
            "quantity": {"type": "number", "description": "How many. Default 1."},
        },
        "required": ["product_name"],
    },
    {
        "name": "view_cart",
        "description": "Read back the current cart contents and total when the caller asks what's in their cart.",
        "url": f"{BASE}/view_cart",
        "params": {},
        "required": [],
    },
    {
        "name": "place_order",
        "description": "Place the order for everything in the cart. Requires a delivery address. Call this only after the caller has confirmed and given an address.",
        "url": f"{BASE}/place_order",
        "params": {
            "delivery_address": {"type": "string", "description": "Where to deliver the order."},
        },
        "required": ["delivery_address"],
    },
]

new_ids = []
for t in TOOLS:
    body = {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t["description"],
            "parameters": {"type": "object", "properties": t["params"], "required": t["required"]},
        },
        "server": {"url": t["url"]},
    }
    created = call("POST", "/tool", body)
    new_ids.append(created["id"])
    print(f"Created tool {t['name']}: {created['id']}")

# Attach to the assistant alongside the existing search tool, refresh the prompt.
assistant = call("GET", f"/assistant/{ASSISTANT_ID}")
existing = assistant.get("model", {}).get("toolIds", []) or []
all_ids = list(dict.fromkeys(existing + new_ids))  # dedupe, preserve order

patch = {
    "model": {
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.4,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
        "toolIds": all_ids,
    }
}
call("PATCH", f"/assistant/{ASSISTANT_ID}", patch)
print("Assistant now has tools:", all_ids)
