"""
Swap the LocallySells Vapi assistant's brain from OpenAI gpt-4o to a Nebius
Token Factory model (OpenAI-compatible), paid by the Nebius credits.

  Smoke-test Nebius + pick a model + wire Vapi:
    NEBIUS_API_KEY=... VAPI_API_KEY=... uv run python swap_to_nebius.py

  Revert to gpt-4o (no Nebius needed):
    VAPI_API_KEY=... uv run python swap_to_nebius.py --revert

The swap is reversible at any time, so trying Nebius is zero-risk.
"""

import json
import os
import sys
import urllib.request
import urllib.error

VAPI = "https://api.vapi.ai"
NEBIUS_BASE = "https://api.tokenfactory.nebius.com/v1"
ASSISTANT_ID = os.environ.get("ASSISTANT_ID", "d52222e2-8657-4035-9a84-6068eee88de0")
VAPI_KEY = os.environ.get("VAPI_API_KEY")
NEBIUS_KEY = os.environ.get("NEBIUS_API_KEY")
REVERT = "--revert" in sys.argv

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
PROMPT = open(os.path.join(os.path.dirname(__file__), "system-prompt.md")).read()

if not VAPI_KEY:
    sys.exit("Set VAPI_API_KEY.")


def http(url, key, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": UA},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:600])
        raise


def vapi_set_model(model_obj):
    http(f"{VAPI}/assistant/{ASSISTANT_ID}", VAPI_KEY, "PATCH", {"model": model_obj})


# fetch current toolIds so we preserve them on either path
current = http(f"{VAPI}/assistant/{ASSISTANT_ID}", VAPI_KEY)
tool_ids = current.get("model", {}).get("toolIds", []) or []

if REVERT:
    vapi_set_model({
        "provider": "openai", "model": "gpt-4o", "temperature": 0.4,
        "messages": [{"role": "system", "content": PROMPT}], "toolIds": tool_ids,
    })
    print("Reverted assistant brain to OpenAI gpt-4o.")
    sys.exit(0)

if not NEBIUS_KEY:
    sys.exit("Set NEBIUS_API_KEY (or pass --revert).")

# 1) Discover available models on Nebius and pick a strong, fast tool-caller.
models = http(f"{NEBIUS_BASE}/models", NEBIUS_KEY).get("data", [])
ids = [m["id"] for m in models]
print(f"Nebius exposes {len(ids)} models.")

PREFER = [
    # Fast, low-latency tool-callers first — voice needs quick time-to-first-token.
    # The 70B Llama was timing out mid-call (pipeline-error-custom-llm-llm-failed).
    "Qwen/Qwen3-30B-A3B-Instruct-2507",
    "openai/gpt-oss-120b-fast",
    "Qwen/Qwen3-32B",
    "meta-llama/Llama-3.3-70B-Instruct",
]
model_id = next((m for m in PREFER if m in ids), None)
if not model_id:
    # fallback: any 70B/72B instruct model
    model_id = next((m for m in ids if "70B" in m or "72B" in m), ids[0] if ids else None)
if not model_id:
    sys.exit("No usable Nebius model found.")
print("Chosen model:", model_id)

# 2) Smoke-test tool calling directly against Nebius (independent of Vapi).
smoke = http(f"{NEBIUS_BASE}/chat/completions", NEBIUS_KEY, "POST", {
    "model": model_id,
    "messages": [
        {"role": "system", "content": "You help find tobacco products. Use the tool when asked about availability."},
        {"role": "user", "content": "Do you have Marlboro Reds?"},
    ],
    "tools": [{
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the product catalog.",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        },
    }],
    "tool_choice": "auto",
    "max_tokens": 200,
})
choice = smoke["choices"][0]["message"]
called = choice.get("tool_calls")
print("Tool-calling smoke test:", "PASS — model called the tool" if called else "WARN — model did NOT call the tool")
if called:
    print("  ->", called[0]["function"]["name"], called[0]["function"].get("arguments"))

# 3) Register a Vapi custom-llm credential holding the Nebius key.
try:
    cred = http(f"{VAPI}/credential", VAPI_KEY, "POST", {"provider": "custom-llm", "apiKey": NEBIUS_KEY})
    print("Created Vapi custom-llm credential:", cred.get("id"))
except urllib.error.HTTPError:
    print("Credential create failed (may already exist) — continuing.")

# 4) Point the assistant at Nebius, keep the same prompt + tools.
vapi_set_model({
    "provider": "custom-llm",
    "url": NEBIUS_BASE,
    "model": model_id,
    "temperature": 0.4,
    "messages": [{"role": "system", "content": PROMPT}],
    "toolIds": tool_ids,
})
print(f"\nDone. Assistant brain is now Nebius '{model_id}'.")
print("Tools preserved:", tool_ids)
print("Revert anytime with:  VAPI_API_KEY=... uv run python swap_to_nebius.py --revert")
