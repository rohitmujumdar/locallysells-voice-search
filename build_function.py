"""
Assemble the deployable Insforge edge function by injecting the catalog and the
precomputed embedding vectors into _template.ts -> index.ts.

  uv run python build_function.py
"""
import json
import os

HERE = os.path.join(os.path.dirname(__file__), "insforge/functions/vapi-tools")
tpl = open(os.path.join(HERE, "_template.ts")).read()
catalog = open(os.path.join(HERE, "catalog.json")).read()
vectors = open(os.path.join(HERE, "catalog_vectors.json")).read()

src = (tpl
       .replace("/*__CATALOG__*/ []", catalog)
       .replace("/*__VECTORS__*/ []", vectors))

out = os.path.join(HERE, "index.ts")
open(out, "w").write(src)
print(f"built index.ts: {os.path.getsize(out)/1024:.0f} KB "
      f"({len(json.loads(catalog))} products, {len(json.loads(vectors))} vectors)")
