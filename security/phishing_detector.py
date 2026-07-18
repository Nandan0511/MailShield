# 🔐 security/phishing_detector.py

import re

# ---------------------------------------------------
# SUSPICIOUS PHISHING PHRASES
# ---------------------------------------------------
PHISHING_KEYWORDS = [

    "verify your account",

    "login immediately",

    "password expired",

    "click below",

    "bank account",

    "confirm identity",

    "security alert",

    "account suspended",

    "reset your password",

    "unauthorized login",

    "payment failed",

    "claim reward",

    "update billing",

    "verify payment",

    "confirm payment",

    "your account has been limited",

    "unusual activity detected",

    "identity verification",

    "validate your account"
]

# ---------------------------------------------------
# URGENCY WORDS
# ---------------------------------------------------
URGENCY_WORDS = [

    "urgent",

    "immediately",

    "act now",

    "within 24 hours",

    "final warning",

    "final notice",

    "last chance",

    "important action required",

    "respond immediately",

    "time sensitive"
]

# ---------------------------------------------------
# URL SHORTENERS
# ---------------------------------------------------
SHORTENERS = [

    "bit.ly",

    "tinyurl.com",

    "goo.gl",

    "t.co",

    "ow.ly",

    "rebrand.ly",

    "cutt.ly"
]

# ---------------------------------------------------
# SUSPICIOUS TLDs
# ---------------------------------------------------
SUSPICIOUS_TLDS = [

    ".xyz",

    ".top",

    ".click",

    ".work",

    ".loan",

    ".gq",

    ".cf",

    ".tk",

    ".ml"
]

# ---------------------------------------------------
# FREE EMAIL DOMAINS
# ---------------------------------------------------
FREE_EMAIL_PROVIDERS = [

    "@gmail.com",

    "@yahoo.com",

    "@hotmail.com",

    "@outlook.com",

    "@aol.com",

    "@proton.me"
]

# ---------------------------------------------------
# DETECT PHISHING
# ---------------------------------------------------
def detect_phishing(content):

    if not content:

        return {

            "risk": "LOW",

            "score": 0,

            "reasons": []
        }

    # -----------------------------------------------
    # LIMIT CONTENT SIZE
    # -----------------------------------------------
    content = content[:10000]

    content_lower = content.lower()

    reasons = []

    score = 0

    # -----------------------------------------------
    # PHISHING PHRASES
    # -----------------------------------------------
    for keyword in PHISHING_KEYWORDS:

        if keyword in content_lower:

            score += 12

            reasons.append(
                f"Suspicious phrase: {keyword}"
            )

    # -----------------------------------------------
    # URGENCY DETECTION
    # -----------------------------------------------
    for word in URGENCY_WORDS:

        if word in content_lower:

            score += 8

            reasons.append(
                f"Urgency language: {word}"
            )

    # -----------------------------------------------
    # URL DETECTION
    # -----------------------------------------------
    urls = re.findall(

        r"https?://[^\s]+",

        content
    )

    if len(urls) >= 3:

        score += 15

        reasons.append(
            f"{len(urls)} links detected"
        )

    if len(urls) >= 10:

        score += 20

        reasons.append(
            "Excessive number of links"
        )

    # -----------------------------------------------
    # URL SHORTENERS
    # -----------------------------------------------
    for shortener in SHORTENERS:

        if shortener in content_lower:

            score += 25

            reasons.append(
                f"Shortened URL: {shortener}"
            )

    # -----------------------------------------------
    # IP ADDRESS URL
    # -----------------------------------------------
    ip_url_pattern = (

        r"https?://"

        r"\d+\.\d+\.\d+\.\d+"
    )

    if re.search(
        ip_url_pattern,
        content
    ):

        score += 35

        reasons.append(
            "IP-based URL detected"
        )

    # -----------------------------------------------
    # SUSPICIOUS TLD
    # -----------------------------------------------
    for tld in SUSPICIOUS_TLDS:

        if tld in content_lower:

            score += 15

            reasons.append(
                f"Suspicious domain: {tld}"
            )

    # -----------------------------------------------
    # FREE EMAIL ADDRESSES
    # -----------------------------------------------
    email_pattern = (

        r"[A-Za-z0-9._%+-]+"

        r"@[A-Za-z0-9.-]+"

        r"\.[A-Za-z]{2,}"
    )

    found_emails = re.findall(
        email_pattern,
        content
    )

    for email in found_emails:

        email = email.lower()

        for provider in FREE_EMAIL_PROVIDERS:

            if provider in email:

                score += 5

                reasons.append(
                    f"Free email address: {email}"
                )

                break

    # -----------------------------------------------
    # REPEATED EXCLAMATION MARKS
    # -----------------------------------------------
    if content.count("!") >= 5:

        score += 10

        reasons.append(
            "Aggressive punctuation"
        )

    # -----------------------------------------------
    # RISK LEVEL
    # -----------------------------------------------
    if score >= 70:

        risk = "HIGH"

    elif score >= 35:

        risk = "MEDIUM"

    else:

        risk = "LOW"

    # -----------------------------------------------
    # REMOVE DUPLICATES
    # -----------------------------------------------
    reasons = list(dict.fromkeys(reasons))

    return {

        "risk": risk,

        "score": score,

        "reasons": reasons
    }