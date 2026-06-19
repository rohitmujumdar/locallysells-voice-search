// LocallySells voice-tool handler — Insforge edge function (Deno).
// Semantic + keyword hybrid search. One function serves all Vapi tools.
//   - search_products(query, category?, limit?)  -> semantic (Nebius embeddings) + keyword
//   - place_order(items, delivery_address)
// NEBIUS_API_KEY is an Insforge secret (Deno.env). If embeddings fail, falls back to keyword.

const catalog = /*__CATALOG__*/ [] as unknown;
const vectors = /*__VECTORS__*/ [] as unknown; // number[][] aligned with catalog

type Product = {
  name: string; brand: string; category: string; price: number | null;
  format: string; flavor: string; description?: string; sku: string; barcode: string; conf: number;
};
const CATALOG = catalog as Product[];
const VECS = vectors as number[][];

const NB_KEY = Deno.env.get("NEBIUS_API_KEY");
const EMBED_URL = "https://api.tokenfactory.nebius.com/v1/embeddings";
const EMBED_MODEL = "Qwen/Qwen3-Embedding-8B";
const DIM = 512;

const CATEGORY_ALIASES: Record<string, string> = {
  cigarette: "cigarettes", cigarettes: "cigarettes", smokes: "cigarettes",
  cigar: "cigars", cigars: "cigars",
  vape: "vape", vapes: "vape", "e-cig": "vape", ecig: "vape", disposable: "vape",
  hookah: "hookah", shisha: "hookah",
  pouch: "nicotine", pouches: "nicotine", nicotine: "nicotine", zyn: "nicotine",
  cbd: "cbd",
  accessory: "accessories", accessories: "accessories", lighter: "accessories",
};

// ---- keyword search (sync; used as fallback + for order lookup) -------------
function keywordSearch(query = "", category = "", limit = 20): Product[] {
  const q = query.trim().toLowerCase();
  let cat = category.trim().toLowerCase();
  cat = CATEGORY_ALIASES[cat] ?? cat;

  if (/^\d{8,14}$/.test(q)) {
    const exact = CATALOG.filter((r) => (r.barcode || "").trim() === q);
    if (exact.length) return exact.slice(0, 5);
  }
  let res = CATALOG;
  if (cat) res = res.filter((r) => (r.category || "").toLowerCase() === cat);
  if (q) {
    const singular = (t: string) => (t.endsWith("s") && t.length > 3 ? t.slice(0, -1) : t);
    const tokens = q.split(/\s+/).filter(Boolean);
    res = res.filter((r) => {
      const hay = `${r.name} ${r.brand} ${r.flavor} ${r.category} ${r.sku} ${r.barcode}`.toLowerCase();
      return tokens.every((t) => hay.includes(t) || hay.includes(singular(t)));
    });
  }
  return [...res].sort((a, b) => (b.conf - a.conf) || a.name.localeCompare(b.name)).slice(0, Math.min(limit, 100));
}

// ---- semantic search (async; embeds query via Nebius, cosine over VECS) -----
function cosine(a: number[], b: number[]): number {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i]; }
  return dot / (Math.sqrt(na) * Math.sqrt(nb) + 1e-9);
}

async function embedQuery(q: string): Promise<number[] | null> {
  if (!NB_KEY || !q) return null;
  try {
    const r = await fetch(EMBED_URL, {
      method: "POST",
      headers: { "Authorization": `Bearer ${NB_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({ model: EMBED_MODEL, input: q, dimensions: DIM }),
    });
    if (!r.ok) return null;
    const d = await r.json();
    return d?.data?.[0]?.embedding ?? null;
  } catch {
    return null;
  }
}

async function search(query = "", category = "", limit = 20): Promise<Product[]> {
  const q = query.trim();
  let cat = category.trim().toLowerCase();
  cat = CATEGORY_ALIASES[cat] ?? cat;

  // barcode shortcut stays exact
  if (/^\d{8,14}$/.test(q)) return keywordSearch(q, category, limit);

  const qvec = VECS.length ? await embedQuery(q) : null;
  if (!qvec) return keywordSearch(query, category, limit); // reliable fallback

  // keyword token set for a hybrid boost (exact brand mentions should win)
  const singular = (t: string) => (t.endsWith("s") && t.length > 3 ? t.slice(0, -1) : t);
  const tokens = q.toLowerCase().split(/\s+/).filter(Boolean);

  const scored = CATALOG.map((p, i) => {
    if (cat && (p.category || "").toLowerCase() !== cat) return null;
    const sem = VECS[i] ? cosine(qvec, VECS[i]) : 0;
    const hay = `${p.name} ${p.brand} ${p.flavor} ${p.category}`.toLowerCase();
    const kwHits = tokens.filter((t) => hay.includes(t) || hay.includes(singular(t))).length;
    const kwBoost = tokens.length ? (kwHits / tokens.length) * 0.25 : 0;
    return { p, score: sem + kwBoost };
  }).filter(Boolean) as Array<{ p: Product; score: number }>;

  scored.sort((a, b) => b.score - a.score);
  // keep clearly-relevant matches; semantic scores below ~0.3 are usually noise
  const top = scored.filter((s) => s.score >= 0.30);
  const chosen = (top.length ? top : scored).slice(0, Math.min(limit, 100));
  return chosen.map((s) => s.p);
}

function bestMatch(name: string): Product | null {
  const r = keywordSearch(name, "", 5);
  return r.length ? r[0] : null;
}

// ---- formatting ------------------------------------------------------------
function fmt(p: Product): string {
  const price = p.price != null ? `$${p.price.toFixed(2)}` : "price n/a";
  const parts = [p.name, price];
  if (p.format) parts.push(p.format);
  if (p.flavor && p.flavor.toLowerCase() !== "regular") parts.push(p.flavor);
  return parts.join(" — ");
}

function searchSummary(query: string, category: string, products: Product[]): string {
  if (!products.length) {
    let scope = query ? ` matching "${query}"` : "";
    if (category) scope += ` in ${category}`;
    return `No products found${scope}. Suggest the caller try a different brand or category.`;
  }
  const top = products.slice(0, 3);
  const lines = [`Found ${products.length} match(es).`, "Top results:"];
  for (const p of top) lines.push("  - " + fmt(p));
  if (products.length > 3) {
    lines.push("Also available: " + products.slice(3, 8).map((p) => p.name).join(", ") + ".");
  }
  return lines.join("\n");
}

function orderNumber(): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  let s = "";
  for (let i = 0; i < 6; i++) s += chars[Math.floor(Math.random() * chars.length)];
  return "LS-" + s;
}

function placeOrder(args: Record<string, unknown>): string {
  const address = String(args.delivery_address ?? args.address ?? "").trim();
  let rawItems = args.items ?? [];
  if (typeof rawItems === "string") {
    try { rawItems = JSON.parse(rawItems); } catch { rawItems = []; }
  }
  if (!Array.isArray(rawItems) || rawItems.length === 0) {
    return "No items to order yet. Confirm what the caller wants first, then place the order.";
  }
  if (!address) {
    return "I need a delivery address before placing the order. Ask the caller where to deliver.";
  }
  const lines: string[] = [];
  let total = 0;
  for (const it of rawItems as Array<Record<string, unknown>>) {
    const name = String(it.name ?? it.product_name ?? "");
    const qty = Math.max(1, parseInt(String(it.quantity ?? 1)) || 1);
    const prod = bestMatch(name);
    if (!prod) { lines.push(`${qty} x ${name} (not found)`); continue; }
    total += (prod.price ?? 0) * qty;
    lines.push(`${qty} x ${prod.name}`);
  }
  return `Order ${orderNumber()} confirmed: ${lines.join(", ")}. Total $${total.toFixed(2)}, ` +
    `delivering to ${address}. Estimated delivery about 45 minutes. ` +
    `Remind the caller that a valid 21-plus ID is required at the door.`;
}

async function handleTool(name: string, args: Record<string, unknown>): Promise<string> {
  if (name === "search_products") {
    const products = await search(
      String(args.query ?? args.q ?? ""),
      String(args.category ?? ""),
      Number(args.limit) || 20,
    );
    return searchSummary(String(args.query ?? args.q ?? ""), String(args.category ?? ""), products);
  }
  if (name === "place_order") return placeOrder(args);
  return `Unknown tool: ${name}`;
}

export default async function handler(req: Request) {
  if (req.method === "GET") {
    return Response.json({ ok: true, catalog_size: CATALOG.length, vectors: VECS.length, embeddings: !!NB_KEY });
  }
  let body: Record<string, unknown> = {};
  try { body = await req.json(); } catch { /* ignore */ }

  const msg = (body.message ?? body) as Record<string, unknown>;
  const calls = (msg.toolCallList ?? msg.toolCalls ?? []) as Array<Record<string, unknown>>;

  const results = [];
  for (const tc of calls) {
    const fn = (tc.function ?? tc) as Record<string, unknown>;
    let args = fn.arguments ?? {};
    if (typeof args === "string") { try { args = JSON.parse(args); } catch { args = {}; } }
    results.push({
      toolCallId: tc.id ?? tc.toolCallId,
      result: await handleTool(String(fn.name ?? ""), args as Record<string, unknown>),
    });
  }
  return Response.json({ results });
}
