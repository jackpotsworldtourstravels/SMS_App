import re

from app.models.message import MessageCategory

# Order matters: OTP is checked first because OTP messages routinely contain
# debit/credit boilerplate ("...your account will be debited if you share
# this OTP") that would otherwise misclassify them as CREDIT/DEBIT.
_CATEGORY_RULES: list[tuple[str, re.Pattern]] = [
    (
        MessageCategory.OTP,
        re.compile(
            r"\bOTP\b|one[\s-]?time password|verification code|\bOTP is\b",
            re.IGNORECASE,
        ),
    ),
    (
        MessageCategory.DEBIT,
        re.compile(
            r"\bdebit(ed)?\b|\bwithdrawn\b|\bspent\b|has been debited|paid to|"
            r"debited from",
            re.IGNORECASE,
        ),
    ),
    (
        MessageCategory.CREDIT,
        re.compile(
            r"\bcredit(ed)?\b|\bdeposited\b|received in your account|\bcashback\b|"
            r"\brefund(ed)?\b|credited to",
            re.IGNORECASE,
        ),
    ),
]


def categorize_message(body: str) -> str:
    if not body:
        return MessageCategory.UNKNOWN

    for category, pattern in _CATEGORY_RULES:
        if pattern.search(body):
            return category

    return MessageCategory.UNKNOWN
