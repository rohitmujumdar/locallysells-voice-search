"""
Create the LocallySells Vapi assistant + search_products tool via the Vapi API.

Usage:
  VAPI_API_KEY=sk_... TOOL_URL=https://.../search_products uv run python create_vapi.py

Prints the created assistant id. Then open the Vapi dashboard, find this assistant,
and click "Talk to Assistant" (web call) to demo, or attach a phone number.
"""

import json
import os
import sys
import urllib.request
import urllib.error

API = "https://api.vapi.ai"
KEY = os.environ.get("VAPI_API_KEY")
TOOL_URL = os.environ.get(
    "TOOL_URL",
    "https://totals-accountability-behavior-hdtv.trycloudflare.com/search_products",
)

if not KEY:
    sys.exit("Set VAPI_API_KEY in the environment first.")

SYSTEM_PROMPT = open(os.path.join(os.path.dirname(__file__), "system-prompt.md")).read()


def post(path, body):
    req = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode())
        raise


# 1) Create the search_products custom tool
tool_body = {
    "type": "function",
    "function": {
        "name": "search_products",
        "description": (
            "Search the LocallySells tobacco and nicotine product catalog by keyword, "
            "brand, or category. Call this whenever the caller asks whether a product is "
            "available, what a price is, or what items exist in a category."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Brand, product name, or keyword the caller mentioned.",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter.",
                    "enum": ["cigarettes", "cigars", "vape", "hookah", "nicotine", "cbd", "accessories"],
                },
                "limit": {"type": "number", "description": "Max results. Default 20."},
            },
            "required": ["query"],
        },
    },
    "server": {"url": TOOL_URL},
}

tool = post("/tool", tool_body)
tool_id = tool["id"]
print("Created tool:", tool_id)

# 2) Create the assistant referencing the tool
assistant_body = {
    "name": "LocallySells Voice Search",
    "firstMessage": "Thanks for calling LocallySells — what can I help you find today?",
    "model": {
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.4,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
        "toolIds": [tool_id],
    },
    "voice": {"provider": "vapi", "voiceId": "Elliot"},
    "transcriber": {"provider": "deepgram", "model": "nova-2", "language": "en"},
}

assistant = post("/assistant", assistant_body)
print("Created assistant:", assistant["id"])
print("\nOpen https://dashboard.vapi.ai → Assistants → 'LocallySells Voice Search' → Talk to Assistant.")
