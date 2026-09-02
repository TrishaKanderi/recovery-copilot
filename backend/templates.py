"""
Template-based multilingual outreach. Works fully offline (no LLM key needed)
so the pipeline is demoable end-to-end immediately. If GROQ_API_KEY is set,
pipeline.py will additionally ask Groq to personalize the tone on top of
these templates for the live demo/video.
"""

MESSAGES = {
    "instant_retry": {
        "en": "Hi {name}, your payment of INR {amount} didn't go through due to a temporary bank issue. We're retrying it automatically — no action needed.",
        "hi": "Namaste {name}, aapka INR {amount} ka payment ek temporary bank issue ki wajah se fail ho gaya. Hum ise automatically retry kar rahe hain — aapko kuch karne ki zaroorat nahi.",
        "te": "Namaskaram {name}, mee INR {amount} payment oka temporary bank issue వల్ల fail ayyindi. Memu automatic ga retry chestunnamu — meeru em cheyalsina pani ledu.",
    },
    "delayed_retry": {
        "en": "Hi {name}, your payment of INR {amount} couldn't go through (insufficient balance). We'll retry in 24 hours — feel free to top up your account before then.",
        "hi": "Namaste {name}, aapka INR {amount} ka payment balance kam hone ki wajah se nahi ho paaya. Hum 24 ghante mein dobara try karenge — chahen to pehle balance add kar sakte hain.",
        "te": "Namaskaram {name}, mee INR {amount} payment balance takkuva vundatam valla avvaledu. Memu 24 gantalalo malli try chestamu — appatiki mundu balance add cheskovachu.",
    },
    "mandate_reauth": {
        "en": "Hi {name}, your saved payment method needs a quick re-authorization to complete the INR {amount} payment. Tap here to re-authorize securely.",
        "hi": "Namaste {name}, INR {amount} ka payment complete karne ke liye aapke payment method ko dobara authorize karna hoga. Yahan tap karke secure tarike se authorize karein.",
        "te": "Namaskaram {name}, INR {amount} payment complete cheyadaniki mee saved payment method ni malli authorize cheyali. Ikkada tap chesi securely authorize cheyandi.",
    },
    "update_payment_method": {
        "en": "Hi {name}, your card on file has expired, so we couldn't process INR {amount}. Please update your payment method to avoid service interruption.",
        "hi": "Namaste {name}, aapka saved card expire ho gaya hai, isliye INR {amount} process nahi ho saka. Service band na ho isliye payment method update kar dein.",
        "te": "Namaskaram {name}, mee saved card expire ayyindi, andukey INR {amount} process avvaledu. Service aagipoyakunda undataniki payment method update cheyandi.",
    },
    "nudge_message": {
        "en": "Hi {name}, you left INR {amount} worth of items in your cart. Complete your purchase now before they're gone!",
        "hi": "Namaste {name}, aapne cart mein INR {amount} ke items chhod diye hain. Khatam hone se pehle apni purchase complete kar lein!",
        "te": "Namaskaram {name}, meeru cart lo INR {amount} value items vadili petaru. Ivi ayipoyakamunde mee purchase complete cheyandi!",
    },
    "payment_reminder": {
        "en": "Hi {name}, a reminder that invoice of INR {amount} is overdue. Please clear it at your earliest to avoid late fees.",
        "hi": "Namaste {name}, INR {amount} ka invoice overdue hai. Late fees se bachne ke liye jald se jald clear karein.",
        "te": "Namaskaram {name}, INR {amount} invoice overdue ayyindi. Late fees ravakunda undataniki dayachesi tondaraga clear cheyandi.",
    },
    "escalate_human": {
        "en": "Hi {name}, we've flagged your INR {amount} case for a specialist to follow up personally — you'll hear from our team shortly.",
        "hi": "Namaste {name}, aapka INR {amount} ka case ek specialist ko diya gaya hai jo personally follow up karega — hamari team jald contact karegi.",
        "te": "Namaskaram {name}, mee INR {amount} case oka specialist ki pampinchamu, vallu personal ga follow up chestaru — mee team tondaralo contact chestundi.",
    },
}


def render_message(action: str, language: str, name: str, amount: float) -> str:
    lang = language if language in ("en", "hi", "te") else "en"
    template = MESSAGES.get(action, MESSAGES["escalate_human"])[lang]
    return template.format(name=name, amount=f"{amount:,.0f}")
