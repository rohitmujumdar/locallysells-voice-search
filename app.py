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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
