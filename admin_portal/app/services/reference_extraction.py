import re

# Indian bank/UPI transaction reference numbers (UTR / RRN) are almost
# always exactly 12 digits — this is the real-world NPCI UPI RRN format,
# confirmed against live bank SMS during testing. Extraction is therefore
# anchored on a standalone 12-digit run rather than a loosely-bounded
# alphanumeric token.
#
# (?<!\d) / (?!\d) guard against matching a 12-digit substring inside a
# longer run of digits (e.g. a 16-digit card number, or a phone number
# with country code) — plain \b word boundaries don't help here since
# digit-to-digit has no boundary at all.
_TWELVE_DIGITS = r"(?<!\d)(\d{12})(?!\d)"

# Keyword-anchored: prefer a 12-digit number that's actually labelled as
# the transaction reference, in case a message contains other 12-digit
# numbers that aren't (e.g. part of an account or phone number).
_KEYWORD_REFERENCE_PATTERN = re.compile(
    r"\b(?:"
    r"UTR|RRN|"
    r"UPI\s*Ref(?:erence)?\.?\s*(?:No\.?)?|"
    r"Ref(?:erence)?\.?\s*(?:ID|No\.?|Number)?|"
    r"Transaction\s*ID|"
    r"Txn\.?\s*Ref(?:erence)?\.?"
    r")\s*[:\-]?\s*" + _TWELVE_DIGITS,
    re.IGNORECASE,
)

# Fallback: no labelled reference found — take the first standalone
# 12-digit number in the message, if any.
_STANDALONE_TWELVE_DIGIT_PATTERN = re.compile(_TWELVE_DIGITS)


def extract_reference_id(body: str) -> str | None:
    """Best-effort extraction of a 12-digit UTR/RRN/Ref No. from a bank SMS
    body. Returns None if no 12-digit reference number is present (e.g.
    most OTP messages) — this is a heuristic, not a guarantee, the same way
    categorize_message() is."""

    if not body:
        return None

    keyword_match = _KEYWORD_REFERENCE_PATTERN.search(body)
    if keyword_match:
        return keyword_match.group(1)

    fallback_match = _STANDALONE_TWELVE_DIGIT_PATTERN.search(body)
    if fallback_match:
        return fallback_match.group(1)

    return None
