# Recovery Copilot

**Track 03 — AI Revenue Recovery**, Razorpay AI Buildathon.

An agent that closes the loop on at-risk revenue: it detects a failing
payment, abandoned checkout, failed subscription mandate, or overdue
invoice, diagnoses *why* it failed, picks a bounded recovery action, reaches
out to the customer **in their language (English / Hindi / Telugu)**, tracks
the response, and stops — with a full audit trail at every step.

## Why this, not just a retry bot

Most recovery tools do one thing (retry, or remind, or chase). Revenue loss
rarely happens in one clean step — a payment degrades for a different reason
each time, and the right fix depends on *why* it failed. This agent chains
detection → root-cause diagnosis → strategy → multilingual outreach →
tracking → a hard stop, so every case gets an explainable, gated response
instead of a one-size-fits-all nudge.

## Architecture

```
DETECT ──▶ ROOT_CAUSE ──▶ STRATEGY ──▶ OUTREACH ──▶ TRACK ──▶ STOP / LOOP
```

- **DETECT** — flags at-risk revenue records from a synthetic batch
  (payment failures, abandoned checkouts, failed mandates, overdue
  invoices).
- **ROOT_CAUSE** — classifies *why* it failed (insufficient funds, bank
  timeout, OTP/auth failure, expired card, no response) instead of treating
  every failure identically.
- **STRATEGY** — a rule-based, explainable mapping from root cause →
  recovery action, with a guardrail: any case above ₹50,000 is always
  escalated to a human, never fully automated.
- **OUTREACH** — generates the recovery message in the customer's language
  (English, Hindi, or Telugu) via templates (works fully offline) — see
  "Plugging in Groq" below to layer in live LLM personalization for the
  demo video.
- **TRACK** — records the outcome (in this prototype, simulated response
  probabilities per action type — see "What's simulated" below).
- **STOP / LOOP** — the guardrail node. Caps automated attempts at 3 per
  case, then hands off to a human. This is what makes "one failure handled
  gracefully" concrete: a customer is never contacted indefinitely by the
  agent.

Every node writes a structured entry to the case's `audit_trail`, viewable
per-case in the dashboard.

This is implemented as a plain, dependency-light state graph so the whole
thing runs with zero external services — but the node/state shape maps 1:1
onto a `langgraph.StateGraph` if you want to swap it in (each function
already takes and returns the shared `case` state dict).

## What's simulated (be upfront about this in your pitch)

- The synthetic batch (`backend/data_gen.py`) stands in for real Razorpay
  test-mode webhook data — swap in real test-mode API calls there.
- Customer responses in `TRACK` are sampled from a probability per action
  type, not real webhook callbacks — in production, `track()` would read a
  real payment-status or delivery-receipt event instead.
- Outreach is template-based by default (no API key required to run).

Being explicit about what's simulated vs. real is a strength, not a
weakness — the rubric asks for "honest metrics," not a black box.

## Metrics the dashboard shows

- Total at-risk revenue vs. total recovered (₹), on a fresh 80-record
  held-out batch every run
- Recovery rate %
- Recovery rate broken down **by root cause** (shows the diagnosis step is
  doing real work, not just noise)
- Cases escalated to a human (the guardrail firing, not a failure)
- Full per-case audit trail + the exact multilingual messages sent

## Running it

```bash
cd recovery-copilot
python3 -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Open **http://127.0.0.1:8000** and click **"Run batch (80 records)"**.
Click any row in the case ledger to see its full audit trail and the exact
messages sent.

## Plugging in Groq for the demo video (optional, makes it more impressive)

Right now `backend/templates.py` uses fixed templates so the whole thing
runs offline. To layer in live LLM personalization for your pitch video:

1. `pip install groq`
2. Set `GROQ_API_KEY` in your environment.
3. In `backend/pipeline.py`'s `outreach()` function, after building `msg`
   from the template, pass it through a Groq call asking the model to
   lightly personalize tone/wording while keeping the amount, action, and
   language fixed — that keeps the *decision* rule-based and explainable
   (required by the "explainable, bounded" bar) while the *wording* gets
   LLM polish.

## Plugging in real Razorpay test-mode data

Replace `backend/data_gen.py`'s `generate_batch()` with a call to
Razorpay's test-mode Payments/Subscriptions APIs, filtering for
`failed` / `pending` states. The rest of the pipeline needs no changes —
`run_case()` only expects `id`, `type`, `amount`, `decline_code`,
`customer_name`, `customer_language`.

## For the pitch (5-minute video)

1. **Problem** (30s): revenue loss is rarely one clean failure — show 2–3
   different root causes side by side.
2. **Live demo** (2 min): click "Run batch," show the summary numbers, open
   2 cases — one that recovered, one that hit the attempt cap and
   escalated (your "failure handled gracefully" example).
3. **Architecture** (1 min): walk the DETECT→...→STOP diagram, emphasize
   the guardrails (max attempts, high-value escalation).
4. **Honesty** (1 min): explicitly state what's simulated vs. real, and
   what you'd swap in for production (real webhooks, real Groq calls,
   real Razorpay test-mode data).
5. **Why it matters** (30s): tie back to the track's framing — this closes
   the loop from detection to diagnosis to recovery, not just one piece
   of it.

## Project structure

```
recovery-copilot/
  backend/
    data_gen.py     synthetic at-risk revenue batch
    templates.py     multilingual (en/hi/te) message templates
    pipeline.py      the DETECT→...→STOP state graph
    main.py          FastAPI app + dashboard hosting
  frontend/
    index.html       dashboard (single file, no build step)
  requirements.txt
```
