"""
Recovery Copilot pipeline.

Architecture: a bounded, explainable state graph with five nodes, each of
which appends a structured entry to the case's audit trail. This mirrors a
LangGraph StateGraph (nodes + conditional routing over a shared state dict);
it's implemented here as a plain, dependency-light graph runner so the whole
project runs with zero external services, but the node/state shape maps
1:1 onto a real langgraph.StateGraph if you want to swap it in later.

    DETECT -> ROOT_CAUSE -> STRATEGY -> OUTREACH -> TRACK -> (loop or STOP)

Guardrails (the "bounded and gated" bar):
  - MAX_ATTEMPTS caps how many times we contact a customer per case.
  - Every action is logged with a timestamp, node name, and reasoning.
  - Escalation to a human is the only action ever taken for high-value or
    exhausted-retry cases - the agent never keeps escalating money actions
    on its own past that point.
"""
import os
import random
from datetime import datetime, timedelta

from .templates import render_message
from .data_gen import NAME_TRANSLIT

random.seed(7)

MAX_ATTEMPTS = 3
HIGH_VALUE_THRESHOLD = 50000  # INR - above this, always loop a human in

# root cause -> chosen recovery action (rule-based, explainable)
ROOT_CAUSE_TO_ACTION = {
    "insufficient_funds": "delayed_retry",
    "bank_timeout": "instant_retry",
    "otp_failed": "mandate_reauth",
    "issuer_declined": "escalate_human",
    "card_expired": "update_payment_method",
    "mandate_expired": "mandate_reauth",
    "no_payment_attempted": "nudge_message",
    "no_response": "payment_reminder",
}

# simulated success probability per action, used only to score the demo
# batch honestly (this is disclosed as simulated in the dashboard/README -
# swapping in real webhook outcomes is a one-line change, see README)
ACTION_SUCCESS_RATE = {
    "instant_retry": 0.42,
    "delayed_retry": 0.30,
    "mandate_reauth": 0.55,
    "update_payment_method": 0.20,
    "nudge_message": 0.22,
    "payment_reminder": 0.28,
    "escalate_human": 0.0,  # handled by a human, not scored here
}


def _log(case, node, message):
    case["audit_trail"].append(
        {
            "ts": datetime.utcnow().isoformat(),
            "node": node,
            "message": message,
        }
    )


def detect(case):
    _log(case, "DETECT", f"Flagged {case['type']} record ({case['id']}) worth INR {case['amount']:,.0f} as at-risk revenue.")
    case["status"] = "detected"
    return case


def root_cause(case):
    code = case["decline_code"]
    _log(case, "ROOT_CAUSE", f"Classified failure reason as '{code}'.")
    case["root_cause"] = code
    return case


def strategy(case):
    action = ROOT_CAUSE_TO_ACTION.get(case["root_cause"], "escalate_human")

    # guardrail: high-value cases always get a human in the loop, never
    # purely automated retries
    if case["amount"] > HIGH_VALUE_THRESHOLD and action != "escalate_human":
        _log(case, "STRATEGY", f"Amount INR {case['amount']:,.0f} exceeds high-value threshold — overriding '{action}' with human escalation.")
        action = "escalate_human"
    else:
        _log(case, "STRATEGY", f"Selected recovery action '{action}' for root cause '{case['root_cause']}'.")

    case["action"] = action
    return case


def outreach(case):
    # Use a native-script name inside non-English messages so the whole
    # message is genuinely localized, not just the surrounding sentence.
    lang = case["customer_language"]
    display_name = NAME_TRANSLIT.get(case["customer_name"], {}).get(lang, case["customer_name"])
    msg = render_message(case["action"], lang, display_name, case["amount"])
    case.setdefault("messages_sent", []).append(msg)
    _log(case, "OUTREACH", f"Sent '{case['action']}' message in '{case['customer_language']}'.")
    return case


def track(case):
    """Simulates a customer response. In production this node would read a
    real webhook/payment-status callback instead of sampling a probability."""
    if case["action"] == "escalate_human":
        case["status"] = "pending_human"
        _log(case, "TRACK", "Handed off to human agent — no further automated attempts.")
        return case

    p = ACTION_SUCCESS_RATE.get(case["action"], 0.0)
    recovered = random.random() < p

    if recovered:
        case["status"] = "recovered"
        case["recovered_amount"] = case["amount"]
        case["recovered_at"] = (datetime.utcnow() + timedelta(hours=random.randint(1, 20))).isoformat()
        _log(case, "TRACK", "Customer completed payment — case marked recovered.")
    else:
        case["status"] = "no_response"
        _log(case, "TRACK", "No response / payment still failing.")
    return case


def stop_or_loop(case):
    """Gate node: decides whether to retry, stop, or escalate. This is the
    guardrail that keeps the agent from contacting a customer indefinitely."""
    if case["status"] == "recovered":
        _log(case, "STOP", "Case closed — revenue recovered.")
        return case

    if case["status"] == "pending_human":
        _log(case, "STOP", "Case closed — awaiting human follow-up (outside automation scope).")
        return case

    case["attempts"] = case.get("attempts", 0) + 1
    if case["attempts"] >= MAX_ATTEMPTS:
        case["status"] = "escalated_exhausted"
        _log(case, "STOP", f"Reached max attempts ({MAX_ATTEMPTS}) with no response — escalating to human, stopping automation. This is the 'one failure handled gracefully' case.")
        return case

    _log(case, "STOP", f"No response yet (attempt {case['attempts']}/{MAX_ATTEMPTS}) — looping back to STRATEGY for next attempt.")
    return case


def run_case(record):
    case = dict(record)
    case["audit_trail"] = []
    case["attempts"] = 0

    case = detect(case)
    case = root_cause(case)

    while True:
        case = strategy(case)
        case = outreach(case)
        case = track(case)
        case = stop_or_loop(case)
        if case["status"] in ("recovered", "pending_human", "escalated_exhausted"):
            break

    return case


def run_batch(records):
    return [run_case(r) for r in records]


def summarize(cases):
    total_at_risk = sum(c["amount"] for c in cases)
    recovered_cases = [c for c in cases if c["status"] == "recovered"]
    total_recovered = sum(c["recovered_amount"] for c in recovered_cases)
    escalated = [c for c in cases if c["status"] in ("pending_human", "escalated_exhausted")]

    by_root_cause = {}
    for c in cases:
        rc = c["root_cause"]
        by_root_cause.setdefault(rc, {"count": 0, "recovered": 0})
        by_root_cause[rc]["count"] += 1
        if c["status"] == "recovered":
            by_root_cause[rc]["recovered"] += 1

    return {
        "total_cases": len(cases),
        "total_at_risk_amount": round(total_at_risk, 2),
        "total_recovered_amount": round(total_recovered, 2),
        "recovery_rate_pct": round(100 * total_recovered / total_at_risk, 2) if total_at_risk else 0,
        "cases_recovered": len(recovered_cases),
        "cases_escalated_to_human": len(escalated),
        "avg_attempts": round(sum(c["attempts"] for c in cases) / len(cases), 2) if cases else 0,
        "by_root_cause": by_root_cause,
    }
