"""
Repoint the Vapi assistant at the deployed Insforge function and move to the
stateless 2-tool design (search_products + place_order(items, delivery_address)).

Usage:
  VAPI_API_KEY=... INSFORGE_URL=https://<app>.functions.insforge.app/vapi-tools \
    uv run python update_vapi_for_insforge.py
"""

import json
import os
import sys
import urllib.request
import urllib.error

VAPI = "https://api.vapi.ai"
KEY = os.environ.get("VAPI_API_KEY")
URL = os.environ.get("INSFORGE_URL")
ASSISTANT_ID = os.environ.get("ASSISTANT_ID", "d52222e2-8657-4035-9a84-6068eee88de0")
SEARCH_TOOL_ID = os.environ.get("SEARCH_TOOL_ID", "31dc734f-1237-4ea0-8ffa-d1ece86ffc2a")
PLACE_TOOL_ID = os.environ.get("PLACE_TOOL_ID", "64abd06d-542c-4898-8081-1f87a8de3d4b")

if not (KEY and URL):
    sys.exit("Set VAPI_API_KEY and INSFORGE_URL.")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
PROMPT = open(os.path.join(os.path.dirname(__file__), "system-prompt.md")).read()


def http(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(VAPI + path, data=data, method=method,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:500])
        raise


# 1) Point search_products at the Insforge URL (same single endpoint for all tools).
http(f"/tool/{SEARCH_TOOL_ID}", "PATCH", {"server": {"url": URL}})
print("search_products -> Insforge URL")

# 2) Rewrite place_order to the stateless items+address schema, point at Insforge.
http(f"/tool/{PLACE_TOOL_ID}", "PATCH", {
    "function": {
        "name": "place_order",
        "description": "Place the delivery order for everything the caller asked for. Call once, at the end, after confirming items and getting a delivery address.",
        "parameters": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "Everything the caller wants to buy.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Product name or brand, e.g. 'Marlboro Red'."},
                            "quantity": {"type": "number", "description": "How many. Default 1."},
                        },
                        "required": ["name"],
                    },
                },
                "delivery_address": {"type": "string", "description": "Where to deliver."},
            },
            "required": ["items", "delivery_address"],
        },
    },
    "server": {"url": URL},
})
print("place_order -> stateless items+address schema, Insforge URL")

# 3) Assistant keeps only search_products + place_order; refresh prompt.
http(f"/assistant/{ASSISTANT_ID}", "PATCH", {
    "model": {
        "provider": "custom-llm",
        "url": "https://api.tokenfactory.nebius.com/v1",
        "model": os.environ.get("NEBIUS_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507"),
        "temperature": 0.4,
        "messages": [{"role": "system", "content": PROMPT}],
        "toolIds": [SEARCH_TOOL_ID, PLACE_TOOL_ID],
    }
})
print("Assistant now uses 2 tools (search_products, place_order) on Insforge, brain still Nebius.")
print("Done.")
