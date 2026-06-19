# LocallySells Voice Search

A [Vapi](https://vapi.ai) voice agent for **LocallySells**, a tobacco/nicotine local-delivery marketplace. Call in and ask *"Do you have Marlboro Reds?"* or *"What vapes do you carry?"* and the agent searches the real product catalog and speaks back what's available, with prices.

Built for a multimodal hackathon (Vapi + Insforge + Nebius).

## How it works

```
Caller  ──speech──▶  Vapi (STT → gpt-4o → TTS)  ──tool call──▶  our FastAPI handler
                          ▲                                            │
                          └──────── top 3 matches + prices ◀───── catalog.csv (198 products)
```

Vapi runs the live call. When the agent needs product data it calls one custom tool,
`search_products`, which hits this FastAPI endpoint. The endpoint searches a snapshot of
the LocallySells master catalog and returns the top matches in Vapi's tool-result format.
The agent then speaks the answer.

See [`system-overview.html`](system-overview.html) for an illustrated walkthrough.

## The one tool: `search_products`

| in | out |
|----|-----|
| `query` (brand/keyword), optional `category`, optional `limit` | top matches with name, price, format, flavor |

Search mirrors the production `GET /api/master-catalog/search` endpoint: case-insensitive
substring match on name/brand/sku/barcode/flavor, optional category filter, barcode
exact-match shortcut, ordered by `confidence_score`.

## Run locally

```bash
uv sync
uv run uvicorn app:app --host 0.0.0.0 --port 8000

# expose a public HTTPS URL for Vapi to call
cloudflared tunnel --url http://127.0.0.1:8000
```

Then create the Vapi tool + assistant:

```bash
VAPI_API_KEY=your_private_key TOOL_URL=https://<your-tunnel>/search_products \
  uv run python create_vapi.py
```

## Files

| file | what |
|------|------|
| `app.py` | FastAPI tool handler (search + Vapi payload parsing) |
| `catalog.csv` | 198-product catalog snapshot, 7 categories |
| `create_vapi.py` | creates the Vapi tool + assistant via API |
| `system-prompt.md` | agent persona (21+ rule, summarize top 3, always say prices) |
| `vapi-tool-schema.json` | the `search_products` tool definition |
| `system-overview.html` | illustrated system walkthrough |

## Notes

- 21+ age-restricted; the agent refuses underage callers. ID is checked at delivery in the real product.
- No secrets in the repo. The Vapi API key is passed via environment variable only.
