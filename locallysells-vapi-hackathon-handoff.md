# LOCALLYSELLS × VAPI — HACKATHON HANDOFF

> **Purpose of this doc:** Continue building a voice agent for LocallySells in a fresh chat session without losing context. Paste this whole thing into the new session as your first message.

---

## THE HACKATHON GOAL

Building **voice search + voice ordering + voice sales** for LocallySells, a tobacco-delivery marketplace. **Primary focus = voice SEARCH.** Using free credits from **Vapi** (voice agent platform — the spine), **Insforge**, and **Nebius**.

**Time box:** Multimodal hackathon. Plan was made ~11:30am with a ~4:00pm soft deadline, leaving time for testing + Vapi Evals + demo prep. Adjust to your actual remaining time.

**Demo target:** A Vapi voice agent where a user speaks a query like *"Do you have Marlboro Reds?"* or *"What vapes do you carry?"* → the agent calls a custom tool → the tool hits a search endpoint over LocallySells catalog data → the agent speaks back what's available with prices.

---

## HOW VAPI WORKS (the key technical model)

- Vapi runs a **listen → think → speak** loop. You plug in STT, an LLM, and TTS; Vapi orchestrates the live call.
- The integration mechanism for our use case is **Custom Tools**: you define a tool the agent can call; when the agent calls it, **Vapi sends an HTTP request to your server URL** with the tool call + arguments; your server executes and returns JSON; the agent speaks the result.
- Tools are created in the Vapi dashboard's **Tools** section (visual) or via API. Each tool has a `name`, `description` (the AI uses this to decide when to call it), and a `parameters` JSON schema.
- Default built-in tools also exist: `transferCall`, `endCall`, `sms`, `dtmf`, `apiRequest`.
- For "bring your own LLM," Vapi supports a **Custom LLM provider** via a URL — this is the natural place to use **Nebius** (host the thinking model).
- Latency target ~800ms end-to-end.
- The account in use showed **PAYG with 10 credits** — watch credit burn; test efficiently.

### The huge head start
LocallySells **already has a search endpoint**: `GET /api/master-catalog/search?q=keyword&category=...&limit=20` against a 1,109-product master catalog (Supabase-backed). Voice search's backend basically already exists — the Vapi tool just needs to call it (or call a standalone copy of it).

---

## THE BUILD PLAN (three tiers — build T1 fully before touching T2)

**TIER 1 — Voice Search (PRIMARY, the demo centerpiece — guarantee this)**
Vapi agent + a `search_products` custom tool → hits the master-catalog search → speaks results with prices. A complete, impressive demo on its own.

**TIER 2 — Voice Ordering (wow extension, only if T1 is solid)**
Add `add_to_cart` / `place_order` tool. "Add two and deliver to 123 Main St" → confirm → create order. More failure surface (cart state, address, order write).

**TIER 3 — Voice Sales (only if way ahead)**
Proactive upsell ("we have a deal on…"). This is mostly a **prompt change**, not new infra — fake it via agent instructions, don't build it.

### Suggested timeline (compress to remaining time)
1. **Setup + spike (~45 min):** get a Vapi agent talking at all (default assistant, no tools). Then a tool stub → confirm the tool-call round-trip fires.
2. **Tier 1 (~75 min):** wire `search_products` → search API. Write the agent system prompt. Get "do you have X?" working end to end.
3. **Tier 2 if solid (~45 min):** ordering tool OR deepen search.
4. **Evals + hardening (~45 min):** use Vapi **Evals** (create test conversations, validate behavior). Fix top 2 failure modes.
5. **Demo prep (~45 min):** script demo, pick 3–4 phrases that reliably work, rehearse twice, record a backup video in case live voice flakes.
6. **Buffer (~15 min):** things break.

---

## TWO OPEN DECISIONS (resolve these first in the new session)

1. **Where do Vapi tools call?**
   - Option A: the **real** LocallySells API (`master-catalog/search` on the live app).
   - Option B (recommended): a **standalone lightweight endpoint** (stand it up on **Insforge** or **Nebius**) querying the same/mock catalog data — safer than depending on prod live on stage; can hardcode/mock if needed.
   - **Recommendation:** standalone tool endpoint.

2. **Scope of search for the demo:**
   - Just catalog search ("do you have X?"), OR
   - Tied to a real store + location ("what's available near me right now")?
   - **Recommendation:** plain catalog search for the demo — avoids store/location complexity.

### Where each platform fits
- **Vapi** = voice agent + tools (the spine).
- **Nebius** = AI cloud / inference; good candidate to host the **LLM** Vapi thinks with (Custom LLM URL). Legit way to "use Nebius."
- **Insforge** = agent-backend/BaaS; candidate to host the **tool-handler endpoints** so you don't expose prod.

### Concrete first artifacts to ask for in the new session
- The exact `search_products` Vapi tool JSON schema (name/description/parameters).
- The agent **system prompt** (LocallySells persona, 21+ disclaimer, how to phrase spoken results — keep it short, prices included, don't read 20 results aloud, summarize top 3).
- The **tool-handler endpoint shape** (receives Vapi tool call → queries catalog → returns the Vapi JSON `{ results: [...] }` format with `toolCallId`).

---

## LOCALLYSELLS CONTEXT (the product the agent serves)

- **What it is:** "Uber Eats for licensed smoke shops." Consumers order tobacco/nicotine products for fast local delivery in SoCal (LA, Orange, Riverside, San Bernardino, Ventura counties). All products **21+ age-restricted**; ID checked at delivery.
- **Three-sided:** customers (buy), stores (sell/fulfill), admin (operate). Separate web app each.
- **Naming quirk:** originally "LocalGrid." In the DB, `suppliers` = stores, `retailers`/customer = consumers. `@localgrid/*` package names are intentional.
- **Stack:** Next.js 14 Turborepo monorepo, Supabase (DB/auth/realtime/storage), Vercel (auto-deploy on git push), Resend (email), Shipday (delivery), Claude (product photo analysis), OpenAI image model (product photos), Nominatim (geocoding).
- **Repo:** `LocalGrid123/locallysells`, local `~/Desktop/localgrid`. Supabase project `zsuoaqekxwauaffblcze.supabase.co`.
- **Relevant endpoints:**
  - `GET /api/master-catalog/search?q=keyword&category=...&limit=20` — keyword search
  - `GET /api/master-catalog/lookup?barcode=...` — barcode lookup
- **Product categories:** Cigarettes, Cigars, Vape/e-cigs, Hookah/Shisha, Nicotine Pouches, CBD, Accessories.

### Coding patterns (if the agent ends up calling real LocallySells code)
- Supplier lookup uses **`profile_id`**, never `user_id`. Never use `rpc('get_supplier_id')`.
- Use `createServiceClient()` (not anon client) for cross-user/admin queries — RLS returns empty arrays otherwise.
- Client `fetch()` needs `credentials: 'include'` (iOS Safari drops the cookie otherwise).
- After adding DB columns: `NOTIFY pgrst, 'reload schema';`.

---

## ⚠️ KNOWN ISSUE — admin portal is down (NOT blocking the hackathon)

- `admin.locallysells.com` currently serves a **completely blank white page** (not a 404, not a build error → JS crashes on load before rendering).
- **Most likely cause:** the most recent admin change was a "Sign Out" button feature where `AdminShell.tsx` (the component wrapping every admin page) was **deleted and recreated via a `cp` workaround** during a sandbox restriction. A dropped import or malformed line there would produce exactly this blank-page crash.
- **To diagnose:** open the blank page → F12 → Console tab → read the first red error (SyntaxError / "is not defined" / "Cannot find module" → points at the AdminShell recreate).
- **Fastest fix (hackathon-appropriate):** Vercel → project **`locallysells-adminn`** (double-n, NOT the dead duplicate `locallysells-admin-j2to`) → Deployments → find the last green/Ready deployment from BEFORE the sign-out commit → `⋯` → **Promote to Production / Redeploy**. One-click rollback restores admin.
- **Reminder:** this does NOT block the Vapi demo (voice search hits a catalog/tool endpoint, not the admin portal). Don't let it eat hackathon time — roll back and move on.

---

## CARRYOVER NON-HACKATHON ITEMS (ignore during hackathon; for later)

- Verify the OpenAI image + Claude model strings in the codebase are current/valid.
- Rotate any API keys that were ever pasted in plaintext (Resend, Shipday, cron secret) — keep real values only in Vercel.
- Test the AI product generator photo→listing→save flow end-to-end on a real iPad.
- **Legal/compliance is the real launch blocker:** tobacco delivery needs a PACT Act / California tobacco compliance attorney (registration, excise tax, real age verification beyond a checkbox, adult-signature delivery). An attorney consultation brief was already drafted.
- Payments are currently COD; Helcim pending activation.

---

## FIRST MESSAGE FOR THE NEW SESSION (suggested)

> "Continuing a hackathon build: a Vapi voice-search agent for LocallySells (a tobacco-delivery marketplace). I have free credits on Vapi, Insforge, Nebius. Primary goal is voice search; ordering is a stretch. I want to [resolve decision 1 + 2], then get a `search_products` Vapi custom tool + agent system prompt + tool-handler endpoint working, then do Vapi Evals and demo prep. Here's my full context: [paste this doc]. Let's start with [the spike / the tool schema / whatever you're on]."
