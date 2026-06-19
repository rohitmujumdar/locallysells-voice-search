# LocallySells Voice Search

Voice search, voice ordering, and conversational product discovery for **LocallySells**, a local tobacco and nicotine delivery marketplace. Call in, talk naturally, and the agent finds real products by meaning and takes your order.

Built for the Multimodal Midsummer Hackathon on **Vapi + Nebius + Insforge**.

> **Try it live:** call **+1 (458) 273-9589** and ask something like *"what's a good smooth light cigarette?"* or *"I want something fruity to vape, what do you have?"*

---

## What it does

- **Conversational voice search.** Ask the way a real person talks. "Those little white minty pouches" finds ZYN. "An easy starter vape" finds the SMOK Novo kit. "A smooth light cigarette" finds Marlboro Lights. It matches by *meaning*, not just brand keywords.
- **Voice ordering.** "Two packs of Marlboro Red, deliver to 123 Main Street" places the order, reads back an order number and ETA, and reminds you a 21+ ID is checked at the door.
- **Stays honest and safe.** Refuses underage callers (21+), never invents products or prices, and declines medical advice.

## The stack (three platforms, working together)

```
  Caller ──speech──▶  Vapi  ──thinks on──▶  Nebius brain (Qwen3-30B-A3B)
                       │                          │ decides to search / order
                       │                          ▼
                       │                   Insforge edge function (Deno)
                       │                     ├─ Nebius embeddings (semantic match)
                       │                     └─ 198-product catalog + vectors
                       ◀────── spoken answer with real prices ──────
```

| Platform | Role |
|----------|------|
| **Vapi** | Voice spine: speech-to-text, the live call loop, text-to-speech, and custom tools |
| **Nebius** Token Factory | The brain (`Qwen3-30B-A3B-Instruct`) *and* the embeddings (`Qwen3-Embedding-8B`) that power semantic search |
| **Insforge** | Hosts the tool handler as a serverless Deno edge function, stores the catalog vectors, and keeps the Nebius key as a secret |

## How a call works

1. Vapi hears the caller and passes the conversation to the Nebius brain.
2. The brain decides to call one of two custom tools, hosted on Insforge.
3. `search_products` embeds the caller's query with Nebius and ranks the catalog by cosine similarity (with a keyword boost so exact brands still win). `place_order` confirms the order.
4. The brain reads the result back to the caller in natural speech.

LocallySells itself stays a black box. The agent only ever touches catalog search and a mock order, so the demo never depends on the production app being up.

## Semantic search

`search_products` does more than keyword matching:

| You say | It finds |
|---------|----------|
| "something minty and refreshing" | Elf Bar Cool Mint |
| "an easy starter vape for a beginner" | SMOK Novo Starter Kit |
| "a smooth light cigarette" | Marlboro Lights, Marlboro Gold |
| "Marlboro Reds" (exact) | Marlboro Red King Size, $8.99 |

Catalog products are embedded once with Nebius (512-dim, precomputed). At query time the function embeds the caller's phrase and ranks by cosine similarity. A keyword-hybrid boost keeps exact brand mentions on top, and if embeddings ever fail the function falls back to keyword search.

## Quality: tested with evals, not vibes

Two Vapi test suites run a simulated caller against the agent and grade the transcripts:

- **Core suite (6/6):** search happy path, category breadth, no-hallucination on unknown brands, 21+ refusal, full order flow, order-without-address guardrail.
- **Conversational suite:** rambling personas with vague descriptions, misremembered brands, multi-turn narrowing, and compound requests.

The evals earned their keep. They caught a silent-agent bug before any live demo (the brain was timing out), which led to switching from a 70B model to the faster `Qwen3-30B-A3B`, plus fixes to plural search and order handling.

## Repo layout

| Path | What |
|------|------|
| `insforge/functions/vapi-tools/_template.ts` | The edge function logic (semantic + keyword hybrid search, ordering) |
| `insforge/functions/vapi-tools/catalog.json` | 198-product catalog snapshot |
| `insforge/functions/vapi-tools/catalog_vectors.json` | Precomputed Nebius embeddings |
| `build_function.py` | Assembles the deployable `index.ts` from the template + data |
| `embed_catalog.py` | Precomputes catalog embeddings via Nebius |
| `create_vapi.py`, `update_vapi_for_insforge.py`, `swap_to_nebius.py` | Set up the Vapi assistant, tools, and Nebius brain |
| `create_evals.py`, `create_conversational_evals.py`, `run_evals.py` | Build and run the Vapi test suites |
| `system-prompt.md` | The agent persona (21+ rule, summarize top 3, always say prices) |
| `system-overview.html` | Illustrated walkthrough of the whole system |

## Run it yourself

```bash
uv sync

# 1. precompute catalog embeddings (once)
NEBIUS_API_KEY=...  uv run python embed_catalog.py

# 2. build + deploy the edge function to Insforge
uv run python build_function.py
npx @insforge/cli functions deploy vapi-tools --file insforge/functions/vapi-tools/index.ts

# 3. point the Nebius key at the function as an Insforge secret
npx @insforge/cli secrets add NEBIUS_API_KEY "..."

# 4. create the Vapi assistant + tools, then set the Nebius brain
VAPI_API_KEY=... uv run python create_vapi.py
VAPI_API_KEY=... INSFORGE_URL=https://<app>.function2.insforge.app/vapi-tools \
  uv run python update_vapi_for_insforge.py
```

## Notes

- 21+ age-restricted. The agent refuses underage callers; ID is checked at delivery in the real product.
- No secrets in the repo. Keys are passed via environment variables and an Insforge secret.
- The catalog is a snapshot of the real LocallySells master catalog, used so the demo has zero dependency on the production app.
