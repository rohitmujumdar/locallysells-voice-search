# LocallySells Voice Search — Team Handoff

> Everything you need to understand, run, demo, and extend this project without the original chat context. Built for the Multimodal Midsummer Hackathon (June 19, 2026).

---

## 1. TL;DR — what this is and its current state

A **voice agent** for LocallySells (a tobacco/nicotine delivery marketplace). You call a phone number, talk naturally, and it:
- **Searches the catalog by meaning** (semantic search), not just brand keywords.
- **Takes an order** for delivery (order number + ETA + 21+ reminder).
- **Stays safe**: refuses callers under 21, never invents products or prices.

**Status: fully live and demo-ready.**
- ✅ Conversational semantic search working
- ✅ Voice ordering working (mock fulfillment: real order number + ETA, no real payment/dispatch yet)
- ✅ 6/6 core eval suite passing
- ✅ Live phone number, public repo, deck (pptx + pdf)

**Call it:** **+1 (458) 273-9589**
**Repo:** https://github.com/rohitmujumdar/locallysells-voice-search

---

## 2. The stack: three platforms

```
Caller ──speech──▶ Vapi ──thinks on──▶ Nebius brain (Qwen3-30B-A3B)
                    │                        │ decides: search or order
                    │                        ▼
                    │                 Insforge edge function (Deno)
                    │                   ├─ Nebius embeddings (semantic match)
                    │                   └─ 198-product catalog + vectors
                    ◀──── spoken answer with real prices ────
```

| Platform | Role |
|----------|------|
| **Vapi** | Voice spine: speech-to-text, the call loop, text-to-speech, custom tools |
| **Nebius** Token Factory | The brain (`Qwen3-30B-A3B-Instruct`) AND the embeddings (`Qwen3-Embedding-8B`, 512-dim) |
| **Insforge** | Serverless Deno edge function that runs our search + order tools, stores the catalog vectors, holds the Nebius key as a secret |

**Important nuance:** Nebius is the embedding *model*, not the vector store. The 198 product vectors are precomputed and bundled into the Insforge function; cosine-similarity matching runs in-memory there. No separate vector DB (would use pgvector if the catalog scaled to thousands).

---

## 3. Key IDs, URLs, and accounts

| Thing | Value |
|-------|-------|
| Vapi assistant | `LocallySells Voice Search` — `d52222e2-8657-4035-9a84-6068eee88de0` |
| Vapi tool: search_products | `31dc734f-1237-4ea0-8ffa-d1ece86ffc2a` |
| Vapi tool: place_order | `64abd06d-542c-4898-8081-1f87a8de3d4b` |
| Vapi phone number | **+1 (458) 273-9589** (id `dd6bc1c3-4beb-455d-948f-f5a5aff476e7`) |
| Nebius custom-llm credential (Vapi) | `e61f48b1-...` — linked at assistant-level `credentialIds` (NOT on the model) |
| Brain model | `Qwen/Qwen3-30B-A3B-Instruct-2507` |
| Embedding model | `Qwen/Qwen3-Embedding-8B` (512-dim) |
| Insforge project | `locally-sells-voice-search` (appkey `hedqzne5`, region us-west) |
| Insforge function URL | `https://hedqzne5.function2.insforge.app/vapi-tools` |
| Eval suite (core, 6/6) | `daf09ed5-b4e2-414b-be2c-0ee2ad9c0227` |
| Eval suite (conversational) | `9e793eda-5aef-479b-95ca-e2ae78800922` |

**Accounts** (Rohit owns all): Vapi, Nebius Token Factory, Insforge, GitHub `rohitmujumdar`.
**Secrets** (ask Rohit, NOT in the repo): `VAPI_API_KEY` (Vapi private key), `NEBIUS_API_KEY` (also stored as an Insforge secret named `NEBIUS_API_KEY`).

---

## 4. How a call works (the round trip)

1. Vapi answers, hears the caller, sends the conversation to the Nebius brain (configured as Vapi's "custom LLM").
2. The brain decides to call `search_products` or `place_order`. Vapi POSTs that tool call to the Insforge function URL.
3. The function handles it:
   - `search_products`: embeds the caller's query with Nebius, ranks the 198 catalog vectors by cosine similarity (keyword-hybrid boost so exact brands still win, keyword fallback if embeddings fail).
   - `place_order`: takes a full `items` list + `delivery_address`, returns an order number + ETA + 21+ reminder.
4. The function returns JSON; Vapi reads the result back to the caller in speech.

LocallySells itself is a black box. The agent only ever touches catalog search + a mock order, so the demo never depends on the production app.

---

## 5. Repo layout

| Path | What |
|------|------|
| `insforge/functions/vapi-tools/_template.ts` | The edge function logic (semantic + keyword search, ordering). **Edit this**, not index.ts |
| `insforge/functions/vapi-tools/catalog.json` | 198-product catalog snapshot |
| `insforge/functions/vapi-tools/catalog_vectors.json` | Precomputed Nebius embeddings |
| `insforge/functions/vapi-tools/index.ts` | **Generated** (gitignored) by build_function.py — do not edit by hand |
| `build_function.py` | Assembles deployable index.ts from template + catalog + vectors |
| `embed_catalog.py` | Precomputes catalog embeddings via Nebius (run when catalog changes) |
| `create_vapi.py` | Creates the Vapi assistant + tools |
| `update_vapi_for_insforge.py` | Points tools at Insforge + sets the Nebius brain (run after deploy) |
| `swap_to_nebius.py` | Swaps the brain model; `--revert` returns to gpt-4o |
| `create_evals.py`, `create_conversational_evals.py`, `run_evals.py` | Build + run Vapi test suites |
| `system-prompt.md` | Agent persona (21+ rule, summarize top 3, always say prices) |
| `system-overview.html` | Illustrated system walkthrough (good for demo + screenshots) |
| `PITCH.md`, `DEMO_SCRIPT.md` | Pitch source (NotebookLM) + demo recording script |
| `catalog.csv` | Source catalog (real LocallySells master-catalog snapshot, 198 products) |

---

## 6. How to run / change things

Prereqs: `uv` (Python), `node` + `npx`, the Insforge CLI (`npx @insforge/cli`, login as Rohit).

**Change the search/order logic:**
```bash
# edit insforge/functions/vapi-tools/_template.ts
uv run python build_function.py        # regenerate index.ts
npx @insforge/cli functions deploy vapi-tools --file insforge/functions/vapi-tools/index.ts
```

**Change the catalog:** edit catalog.csv → rebuild catalog.json → `NEBIUS_API_KEY=... uv run python embed_catalog.py` → build_function.py → deploy.

**Change the agent prompt:** edit system-prompt.md → `VAPI_API_KEY=... INSFORGE_URL=https://hedqzne5.function2.insforge.app/vapi-tools uv run python update_vapi_for_insforge.py`

**Swap the brain model:** edit PREFER list in swap_to_nebius.py or set `NEBIUS_MODEL`, then run update_vapi_for_insforge.py.

**Run the evals:**
```bash
VAPI_API_KEY=... TEST_SUITE_ID=daf09ed5-b4e2-414b-be2c-0ee2ad9c0227 uv run python run_evals.py
```

---

## 7. Gotchas / hard-won lessons

- **Vapi API blocks the default `Python-urllib` User-Agent** (Cloudflare 1010). All scripts send a browser User-Agent. Keep that.
- **Vapi custom-llm auth:** the Nebius credential must be linked at the assistant's top-level `credentialIds`, NOT on the model object (model has no credentialId field). Miss this and the agent goes silent.
- **Voice latency:** the 70B Llama timed out mid-call (`pipeline-error-custom-llm-llm-failed`). Use the fast `Qwen3-30B-A3B` (~1.1s). Do not switch back to a big model.
- **Vapi PAYG needs a card on file** for chat test suites; voice tests need a phone number.
- **Insforge functions** must `export default async function(req)`, NOT `Deno.serve()`. Single-file deploy, so data is inlined.
- **LLM passed `items` as a JSON string** for place_order; the function parses both string and array. Keep that tolerance.
- **STT mishears brands** ("Marlboro Reds" → "Malboro secrets"). The agent recovers gracefully; we chose not to add transcriber keyword hints.

---

## 8. What's done vs. what's next

**Done:** semantic search, voice ordering (mock), safety rules, 6/6 evals, live number, deck, public repo.

**Next steps if continuing:**
- Wire **real fulfillment**: payment + order write + delivery dispatch (currently mocked).
- Bigger catalog (live API has 1,100 products; we use a 198 snapshot for demo reliability).
- Store-side **AI Product Generator** (a separate LocallySells feature, photo to listings — not part of this voice build).
- Move vectors to a real vector store (pgvector) if the catalog grows.

---

## 9. Billing cleanup (do this after the hackathon)

- **Vapi:** the phone number **+1 (458) 273-9589** bills monthly (~$2-3). Release it in Phone Numbers if not needed. Card is on file (PAYG); remove if you want zero exposure.
- **Nebius:** card on file for verification; $100 promo credits don't expire, but it's PAYG after.
- **Insforge:** likely free tier; double-check Billing.

---

## 10. Demo cheat sheet

Open `system-overview.html` (or https://raw.githack.com/rohitmujumdar/locallysells-voice-search/main/system-overview.html) to present the architecture.

Live call phrases that show it off:
- "I'm looking for a smooth, light cigarette." → finds Marlboro Lights (semantic)
- "Those little white minty pouches?" → finds ZYN
- "Which is the most popular?" → conversational follow-up
- "Two packs of Marlboro Red, deliver to 123 Main Street." → places order
- "Actually, I'm 19." → refuses (21+)

After the call, hammer: it understood meaning not keywords, prices were real, it held a conversation, the whole stack ran in ~1 second, and it's eval-tested 6/6.
