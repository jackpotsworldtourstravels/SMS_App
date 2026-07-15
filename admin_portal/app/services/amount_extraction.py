import re
from decimal import Decimal, InvalidOperation

# "Rs."/"Rs" and "INR" require a non-letter before (and, for the suffix
# form, after) them so they don't false-match inside another word (e.g.
# "Mrs. Sharma", "PRINR"). The ₹ symbol needs no such guard — it isn't
# part of any English word. [:\-\s]* between the currency token and the
# number tolerates the colons/dashes some banks use ("Rs:500",
# "INR-500") in addition to plain whitespace or no separator at all.
_CURRENCY_PREFIX = r"(?:(?<![A-Za-z])Rs\.?|(?<![A-Za-z])INR\.?|₹)"
_CURRENCY_SUFFIX = r"(?:Rs\.?|INR\.?|₹)(?![A-Za-z])"
_NUMBER = r"[\d,]+(?:\.\d{1,2})?"

_AMOUNT_PATTERN = re.compile(
    rf"(?:{_CURRENCY_PREFIX}[:\-\s]*(?P<amt_prefix>{_NUMBER}))"
    rf"|(?:(?P<amt_suffix>{_NUMBER})[:\-\s]*{_CURRENCY_SUFFIX})",
    re.IGNORECASE,
)


def extract_amount(body: str) -> Decimal | None:
    """Best-effort extraction of the transaction amount from a bank SMS
    body. Matches either currency-then-number ("Rs.500", "INR 2,350") or
    number-then-currency ("5000.00 INR") formats and takes whichever
    occurs first in the message — in real bank SMS formats the
    transaction amount consistently appears before any mention of the
    account balance, so the first match is the transaction amount, not
    the balance. Returns None if no amount is found (e.g. most OTP
    messages) — a heuristic, not a guarantee, the same way
    categorize_message() and extract_reference_id() are."""

    if not body:
        return None

    match = _AMOUNT_PATTERN.search(body)
    if not match:
        return None

    raw = (match.group("amt_prefix") or match.group("amt_suffix")).replace(",", "")

    try:
        return Decimal(raw)
    except InvalidOperation:
        return None
