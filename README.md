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
  (English, Hindi, or Telugu) via templates. Runs fully offline; see
  "Extending with live LLM personalization" below for an optional upgrade.
- **TRACK** — records the outcome. In this prototype, response probabilities
  are simulated per action type (see "What's simulated" below).
- **STOP / LOOP** — the guardrail node. Caps automated attempts at 3 per
  case, then hands off to a human, so a customer is never contacted
  indefinitely by the agent.

Every node writes a structured entry to the case's `audit_trail`, viewable
per-case in the dashboard.

The pipeline is implemented as a plain, dependency-light state graph so the
whole thing runs with zero external services. The node/state shape maps
1:1 onto a `langgraph.StateGraph` — each function already takes and returns
the shared `case` state dict, so swapping in a real LangGraph is a
mechanical change.

## What's simulated

- The synthetic batch (`backend/data_gen.py`) stands in for real Razorpay
  test-mode webhook data.
- Customer responses in `TRACK` are sampled from a probability per action
  type, not real webhook callbacks. In production, `track()` would read a
  real payment-status or delivery-receipt event instead.
- Outreach is template-based by default (no API key required to run).

## Metrics the dashboard shows

- Total at-risk revenue vs. total recovered (₹), on a fresh 80-record
  batch every run
- Recovery rate %
- Recovery rate broken down **by root cause**
- Cases escalated to a human
- Full per-case audit trail and the exact multilingual messages sent

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

## Extending with live LLM personalization (optional)

`backend/templates.py` uses fixed templates so the pipeline runs offline
by default. To layer in live LLM personalization:

1. `pip install groq`
2. Set `GROQ_API_KEY` in your environment.
3. In `backend/pipeline.py`'s `outreach()` function, pass the templated
   `msg` through a Groq call that lightly personalizes tone/wording while
   keeping the amount, action, and language fixed. This keeps the
   *decision* rule-based and explainable while the *wording* gets LLM
   polish.

## Plugging in real Razorpay test-mode data

Replace `backend/data_gen.py`'s `generate_batch()` with a call to
Razorpay's test-mode Payments/Subscriptions APIs, filtering for
`failed` / `pending` states. The rest of the pipeline needs no changes —
`run_case()` only expects `id`, `type`, `amount`, `decline_code`,
`customer_name`, `customer_language`.

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

---
Built by Trisha Kanderi for the Razorpay AI Buildathon (Track 03).
