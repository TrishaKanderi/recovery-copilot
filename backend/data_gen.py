"""
Generates a synthetic batch of at-risk-revenue records that mimic what you'd
see from Razorpay test-mode: failed payments, abandoned checkouts, failed
subscription mandates, and overdue B2B invoices.

This is intentionally rule-driven and reproducible (seeded) so the pitch can
show honest, repeatable metrics on a held-out batch, not a cherry-picked demo.
"""
import random
from datetime import datetime, timedelta

random.seed(42)

FIRST_NAMES = [
    "Arjun", "Priya", "Rohit", "Sneha", "Karthik", "Divya", "Vikram", "Anjali",
    "Suresh", "Meera", "Rahul", "Pooja", "Naveen", "Lakshmi", "Aditya", "Kavya",
    "Manoj", "Swathi", "Ganesh", "Nisha",
]

LANGUAGES = ["en", "hi", "te"]

DECLINE_CODES = {
    "payment_failed": [
        "insufficient_funds",
        "bank_timeout",
        "otp_failed",
        "card_expired",
        "issuer_declined",
    ],
    "checkout_abandoned": ["no_payment_attempted"],
    "subscription_failed": ["insufficient_funds", "mandate_expired", "bank_timeout"],
    "invoice_overdue": ["no_response"],
}

AMOUNT_RANGES = {
    "payment_failed": (299, 15000),
    "checkout_abandoned": (499, 25000),
    "subscription_failed": (199, 2999),
    "invoice_overdue": (5000, 250000),
}


def generate_batch(n=80):
    records = []
    for i in range(n):
        rtype = random.choices(
            ["payment_failed", "checkout_abandoned", "subscription_failed", "invoice_overdue"],
            weights=[0.40, 0.30, 0.20, 0.10],
        )[0]
        low, high = AMOUNT_RANGES[rtype]
        amount = round(random.uniform(low, high), 2)
        decline_code = random.choice(DECLINE_CODES[rtype])
        created_at = datetime.utcnow() - timedelta(hours=random.randint(1, 96))
        records.append(
            {
                "id": f"REC-{1000 + i}",
                "type": rtype,
                "amount": amount,
                "currency": "INR",
                "decline_code": decline_code,
                "customer_name": random.choice(FIRST_NAMES),
                "customer_language": random.choices(LANGUAGES, weights=[0.5, 0.3, 0.2])[0],
                "created_at": created_at.isoformat(),
            }
        )
    return records


if __name__ == "__main__":
    import json

    print(json.dumps(generate_batch(10), indent=2))
