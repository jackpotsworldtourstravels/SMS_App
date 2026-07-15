import re

# Ordered by how commonly each label appears in Indian bank/UPI SMS. Each
# pattern captures the alphanumeric code following the label; separators
# (period/space/colon/dash) between the label and the code vary by bank, so
# all are made optional rather than assuming one fixed format.
_REFERENCE_PATTERNS: list[re.Pattern] = [
    # "Ref:966697814398", "Ref No 939110992912", "Refno:471403237586",
    # "Reference No. ...", "Reference Number: ..."
    re.compile(
        r"\bRef(?:erence)?\.?\s*(?:Number|No\.?)?\s*[:\-]?\s*([A-Za-z0-9]{6,22})\b",
        re.IGNORECASE,
    ),
    # "UTR: 123456789012", "UTR No. 123456789012"
    re.compile(
        r"\bUTR\.?\s*(?:No\.?)?\s*[:\-]?\s*([A-Za-z0-9]{6,22})\b",
        re.IGNORECASE,
    ),
    # "Txn ID: ABC123", "Transaction ID 123456", "Txn No: 123456"
    re.compile(
        r"\b(?:Txn|Transaction)\.?\s*(?:ID|No\.?|Number)?\s*[:\-]?\s*([A-Za-z0-9]{6,22})\b",
        re.IGNORECASE,
    ),
]


def extract_reference_id(body: str) -> str | None:
    """Best-effort extraction of a UTR/Ref No./Transaction ID from a bank
    SMS body. Returns None if the message doesn't contain a recognizable
    one (e.g. most OTP messages) — this is a heuristic, not a guarantee,
    the same way categorize_message() is."""

    if not body:
        return None

    for pattern in _REFERENCE_PATTERNS:
        match = pattern.search(body)
        if match:
            candidate = match.group(1)
            # Guard against accidentally capturing a plain word when the
            # label wasn't actually followed by a real reference code.
            if any(char.isdigit() for char in candidate):
                return candidate

    return None
