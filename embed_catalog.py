"""
Precompute semantic embeddings for the catalog using Nebius (Qwen3-Embedding-8B),
truncated to 512 dims. Writes catalog_vectors.json: a list aligned with the catalog,
each entry [rounded floats]. Run once whenever the catalog changes.

Usage:
  NEBIUS_API_KEY=... uv run python embed_catalog.py
"""

import json
import os
import sys
import urllib.request

NB = os.environ.get("NEBIUS_API_KEY")
if not NB:
    sys.exit("Set NEBIUS_API_KEY.")
URL = "https://api.tokenfactory.nebius.com/v1/embeddings"
MODEL = "Qwen/Qwen3-Embedding-8B"
DIM = 512

HERE = os.path.dirname(__file__)
CATALOG = json.load(open(os.path.join(HERE, "insforge/functions/vapi-tools/catalog.json")))


def embed(texts):
    body = json.dumps({"model": MODEL, "input": texts, "dimensions": DIM}).encode()
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "Authorization": f"Bearer {NB}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read())
    return [item["embedding"] for item in sorted(d["data"], key=lambda x: x["index"])]


def product_text(p):
    # Rich text so vague intents ("smooth and light", "minty") match by meaning.
    parts = [p["name"], p.get("brand", ""), p.get("category", ""),
             p.get("flavor", ""), p.get("format", ""), p.get("description", "")]
    return ". ".join(x for x in parts if x)


vecs = []
B = 40
for i in range(0, len(CATALOG), B):
    chunk = CATALOG[i:i + B]
    embs = embed([product_text(p) for p in chunk])
    for e in embs:
        vecs.append([round(x, 4) for x in e])
    print(f"  embedded {min(i + B, len(CATALOG))}/{len(CATALOG)}")

out = os.path.join(HERE, "insforge/functions/vapi-tools/catalog_vectors.json")
json.dump(vecs, open(out, "w"))
size = os.path.getsize(out)
print(f"wrote {len(vecs)} vectors (dim {DIM}) -> {out}  ({size/1024:.0f} KB)")
