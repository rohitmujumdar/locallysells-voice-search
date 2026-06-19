# LocallySells Voice Search: Pitch

> Source doc for generating slides or an audio overview (e.g. NotebookLM). Each section maps roughly to one slide.

## 1. The problem

LocallySells is a local tobacco and nicotine delivery marketplace, an Uber Eats for licensed smoke shops. Browsing a 1,100-product catalog by tapping through categories is slow and clumsy, especially for customers who do not know exact brand names. People do not think in SKUs. They think "something smooth and light" or "those minty pouches."

## 2. The idea

A voice agent you can just talk to. Call in, describe what you want the way you would to a clerk, and it finds real products by meaning, tells you prices, and takes your order for delivery.

## 3. What we built

A production-style voice agent with three capabilities:
- **Conversational voice search** that understands intent, not just keywords.
- **Voice ordering** with delivery, order numbers, and a 21+ ID reminder.
- **Built-in safety:** refuses underage callers, never invents products or prices.

## 4. How it works: three platforms, deeply integrated

- **Vapi** runs the live call: speech to text, the conversation loop, text to speech, and custom tools.
- **Nebius** is the brain (Qwen3-30B-A3B) that interprets intent, and the embeddings (Qwen3-Embedding-8B) that power semantic search.
- **Insforge** hosts our search and ordering logic as a serverless edge function, stores the catalog vectors, and holds the Nebius key as a secret.

The caller hears one smooth conversation. Behind it, the brain calls our tools, which retrieve from a real catalog and answer with real prices.

## 5. The standout feature: semantic search

Most voice search is just keyword matching with extra steps. Ours embeds the caller's phrase with Nebius and ranks the catalog by meaning:
- "a smooth light cigarette" finds Marlboro Lights
- "an easy starter vape for a beginner" finds the SMOK Novo kit
- "those little white minty pouches" finds ZYN

Exact brand names still win through a keyword-hybrid boost, and it falls back to keyword search if embeddings ever fail.

## 5b. Voice ordering (working today)

The second voice capability: ordering. "Two packs of Marlboro Red, deliver to 123 Main Street" is confirmed, an order number and ETA are read back, and the caller is reminded a 21+ ID is checked at delivery. It works end to end in the demo and passes our order-flow evals (one clean order, real confirmation, address required). Fulfillment is mocked for the hackathon: the order number and ETA are real to the caller, but no payment or delivery dispatch is wired yet. That is the obvious next step, not a research problem.

## 5c. Secondary feature: the AI Product Generator (store side)

Voice is the customer-facing story. On the store-owner side, LocallySells also has an AI Product Generator that attacks the biggest friction in onboarding a shop: listing inventory.

A shop owner photographs their shelf, even 10 to 15 products at once, and the system turns that one photo into complete, ready-to-sell listings:
- **Detect every product** in the frame with Claude vision, not just one.
- **Write a full listing per product:** title, HTML description, four SEO alt-texts, category, researched price, weight, tax codes, variants, and meta fields, returned as structured JSON.
- **Review and edit:** every field is editable, the owner picks which products and variants to keep, nothing saves until approved.
- **Generate a clean product photo** per item with an OpenAI image model, stored in Supabase.

The clever part is cost control. Many shops sell the same branded items (Marlboro, ZYN, Elf Bar), so before paying to generate an image, the system checks a shared 1,100-product master catalog: an exact barcode match reuses the existing photo, a conservative fuzzy match (brand plus distinguishing tokens like size and strength) reuses only when safe, and a true miss generates a fresh image and saves it back so the next store reuses it. Savings compound, and the admin portal tracks reuse rate and dollars saved.

What would take an hour of manual data entry per handful of products takes about a minute: take a photo, glance over it, tap save.

## 6. We tested it, not just vibed it

We built two Vapi test suites where a simulated caller talks to the agent and an AI grader scores the transcripts: a core suite (search, ordering, 21+ refusal, no hallucination) at 6 of 6, and a conversational suite of rambling real-world personas. The evals caught a real silent-agent bug before any live demo, the brain was timing out on a 70B model, which we fixed by switching to the faster Qwen3-30B-A3B. Quality came from measurement, not luck.

## 7. Why it matters

Voice search only means something if it understands how people actually talk. By grounding a conversational brain in real catalog data through semantic retrieval, the agent turns vague human intent into the right product at the right price, hands-free, in under a minute.

## 8. Try it

Call +1 (458) 273-9589. Ask for "something smooth and light" or "an easy vape to start with." Repo and an illustrated system overview are public on GitHub.

## 9. Visuals to include in the deck

Screenshots make this land. Grab these (all are behind your logins, so capture them quickly):

**From Vapi (proof it works and was tested):**
- A call log with the transcript and "Success Evaluation: true" (the inbound call that ordered Marlboro Red).
- The Test Suites results showing 6 of 6 passing.
- The assistant config showing the custom LLM pointed at Nebius.

**From LocallySells (the product the agent serves):**
- The storefront / catalog on app.locallysells.com (shows the marketplace).
- The AI Product Generator wizard: the four steps (upload photo, detected products, editable review cards, saved listings with generated photos). This is the strongest store-side visual.
- If available, the admin counter showing image reuse rate and dollars saved.

**From this repo:**
- system-overview.html (open it, screenshot the call-flow diagram and the semantic-search examples).

Suggested order in the deck: lead with the voice call (live or recorded), then the system-overview diagram, then the eval results, then the Product Generator as the "and there's more" beat.
