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

## 6. We tested it, not just vibed it

We built two Vapi test suites where a simulated caller talks to the agent and an AI grader scores the transcripts: a core suite (search, ordering, 21+ refusal, no hallucination) at 6 of 6, and a conversational suite of rambling real-world personas. The evals caught a real silent-agent bug before any live demo, the brain was timing out on a 70B model, which we fixed by switching to the faster Qwen3-30B-A3B. Quality came from measurement, not luck.

## 7. Why it matters

Voice search only means something if it understands how people actually talk. By grounding a conversational brain in real catalog data through semantic retrieval, the agent turns vague human intent into the right product at the right price, hands-free, in under a minute.

## 8. Try it

Call +1 (458) 273-9589. Ask for "something smooth and light" or "an easy vape to start with." Repo and an illustrated system overview are public on GitHub.
