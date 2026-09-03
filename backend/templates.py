# -*- coding: utf-8 -*-
"""
Template-based multilingual outreach. Works fully offline (no LLM key needed)
so the pipeline is demoable end-to-end immediately. If GROQ_API_KEY is set,
pipeline.py can additionally ask Groq to personalize the tone on top of
these templates.
"""

MESSAGES = {
    "instant_retry": {
        "en": "Hi {name}, your payment of INR {amount} didn't go through due to a temporary bank issue. We're retrying it automatically — no action needed.",
        "hi": "नमस्ते {name}, आपका INR {amount} का भुगतान एक अस्थायी बैंक समस्या के कारण नहीं हो पाया। हम इसे स्वचालित रूप से दोबारा कोशिश कर रहे हैं — आपको कुछ करने की आवश्यकता नहीं है।",
        "te": "నమస్కారం {name}, మీ INR {amount} చెల్లింపు తాత్కాలిక బ్యాంక్ సమస్య వల్ల జరగలేదు. మేము దీన్ని ఆటోమేటిక్‌గా మళ్లీ ప్రయత్నిస్తున్నాము — మీరు ఏమీ చేయాల్సిన అవసరం లేదు.",
    },
    "delayed_retry": {
        "en": "Hi {name}, your payment of INR {amount} couldn't go through (insufficient balance). We'll retry in 24 hours — feel free to top up your account before then.",
        "hi": "नमस्ते {name}, बैलेंस कम होने के कारण आपका INR {amount} का भुगतान नहीं हो सका। हम 24 घंटे में दोबारा कोशिश करेंगे — चाहें तो पहले अपना बैलेंस जोड़ सकते हैं।",
        "te": "నమస్కారం {name}, బ్యాలెన్స్ సరిపోకపోవడం వల్ల మీ INR {amount} చెల్లింపు జరగలేదు. మేము 24 గంటల్లో మళ్లీ ప్రయత్నిస్తాము — అంతకుముందు మీ బ్యాలెన్స్ జోడించుకోవచ్చు.",
    },
    "mandate_reauth": {
        "en": "Hi {name}, your saved payment method needs a quick re-authorization to complete the INR {amount} payment. Tap here to re-authorize securely.",
        "hi": "नमस्ते {name}, INR {amount} का भुगतान पूरा करने के लिए आपके सेव किए गए भुगतान तरीके को दोबारा अधिकृत करना होगा। सुरक्षित रूप से अधिकृत करने के लिए यहाँ टैप करें।",
        "te": "నమస్కారం {name}, INR {amount} చెల్లింపును పూర్తి చేయడానికి మీ సేవ్ చేసిన చెల్లింపు విధానాన్ని మళ్లీ ఆథరైజ్ చేయాలి. సురక్షితంగా ఆథరైజ్ చేయడానికి ఇక్కడ నొక్కండి.",
    },
    "update_payment_method": {
        "en": "Hi {name}, your card on file has expired, so we couldn't process INR {amount}. Please update your payment method to avoid service interruption.",
        "hi": "नमस्ते {name}, आपका सेव किया गया कार्ड एक्सपायर हो गया है, इसलिए INR {amount} प्रोसेस नहीं हो सका। सेवा बाधित न हो इसके लिए कृपया अपना भुगतान तरीका अपडेट करें।",
        "te": "నమస్కారం {name}, మీ సేవ్ చేసిన కార్డ్ గడువు ముగిసింది, అందుకే INR {amount} ప్రాసెస్ కాలేదు. సేవకు అంతరాయం కలగకుండా ఉండటానికి దయచేసి మీ చెల్లింపు విధానాన్ని అప్‌డేట్ చేయండి.",
    },
    "nudge_message": {
        "en": "Hi {name}, you left INR {amount} worth of items in your cart. Complete your purchase now before they're gone!",
        "hi": "नमस्ते {name}, आपने कार्ट में INR {amount} के सामान छोड़ दिए हैं। खत्म होने से पहले अपनी खरीदारी पूरी कर लें!",
        "te": "నమస్కారం {name}, మీరు కార్ట్‌లో INR {amount} విలువైన వస్తువులను వదిలేశారు. అవి అయిపోకముందే మీ కొనుగోలును పూర్తి చేయండి!",
    },
    "payment_reminder": {
        "en": "Hi {name}, a reminder that invoice of INR {amount} is overdue. Please clear it at your earliest to avoid late fees.",
        "hi": "नमस्ते {name}, याद दिलाना चाहते हैं कि INR {amount} का इनवॉइस बकाया है। लेट फीस से बचने के लिए कृपया जल्द से जल्द भुगतान करें।",
        "te": "నమస్కారం {name}, INR {amount} ఇన్‌వాయిస్ గడువు దాటిందని గుర్తు చేస్తున్నాము. లేట్ ఫీజులు రాకుండా ఉండటానికి దయచేసి వీలైనంత త్వరగా చెల్లించండి.",
    },
    "escalate_human": {
        "en": "Hi {name}, we've flagged your INR {amount} case for a specialist to follow up personally — you'll hear from our team shortly.",
        "hi": "नमस्ते {name}, आपके INR {amount} के मामले को व्यक्तिगत रूप से फॉलो अप करने के लिए एक विशेषज्ञ को भेजा गया है — हमारी टीम जल्द ही आपसे संपर्क करेगी।",
        "te": "నమస్కారం {name}, మీ INR {amount} కేసును వ్యక్తిగతంగా ఫాలో అప్ చేయడానికి ఒక నిపుణుడికి పంపించాము — మా టీమ్ త్వరలో మిమ్మల్ని సంప్రదిస్తుంది.",
    },
}


def render_message(action: str, language: str, name: str, amount: float) -> str:
    lang = language if language in ("en", "hi", "te") else "en"
    template = MESSAGES.get(action, MESSAGES["escalate_human"])[lang]
    return template.format(name=name, amount=f"{amount:,.0f}")
