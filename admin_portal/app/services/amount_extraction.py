import re
from decimal import Decimal, InvalidOperation

# "Rs."/"Rs" and "INR" require a non-letter before them so they don't
# false-match inside another word (e.g. "Mrs. Sharma", "PRINR"). The ₹
# symbol needs no such guard — it isn't part of any English word.
_AMOUNT_PATTERN = re.compile(
    r"(?:(?<![A-Za-z])Rs\.?|(?<![A-Za-z])INR|₹)\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)


def extract_amount(body: str) -> Decimal | None:
    """Best-effort extraction of the transaction amount from a bank SMS
    body. Takes the first Rs./INR/₹-prefixed number found — in real bank
    SMS formats the transaction amount consistently appears before any
    mention of the account balance, so the first match is the transaction
    amount, not the balance. Returns None if no amount is found (e.g. most
    OTP messages) — a heuristic, not a guarantee, the same way
    categorize_message() and extract_reference_id() are."""

    if not body:
        return None

    match = _AMOUNT_PATTERN.search(body)
    if not match:
        return None

    raw = match.group(1).replace(",", "")

    try:
        return Decimal(raw)
    except InvalidOperation:
        return None
