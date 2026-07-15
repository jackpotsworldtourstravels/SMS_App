import pytest

from app.services.categorization import categorize_message


@pytest.mark.parametrize(
    "body,expected",
    [
        (
            "123456 is your OTP for txn of Rs.500.00 at AMAZON. Do not share this OTP with anyone. -HDFC Bank",
            "OTP",
        ),
        (
            "Your OTP for net banking login is 998877. Valid for 10 mins. -SBI",
            "OTP",
        ),
        (
            "Use 445566 as one-time password to complete your transaction. Your account will be debited if verified.",
            "OTP",
        ),
        (
            "Rs.500.00 debited from A/c XX1234 on 14-07-26 towards UPI-swiggy. Avl bal Rs.10,234.50 -ICICI Bank",
            "DEBIT",
        ),
        (
            "Rs 1200 has been debited from your account ending 4321 on 14-Jul-26. Avl Bal: Rs 5000",
            "DEBIT",
        ),
        (
            "You have paid to Zomato Rs.350.00 from your HDFC Bank A/c.",
            "DEBIT",
        ),
        (
            "Rs.15000.00 credited to A/c XX1234 on 14-07-26 by NEFT. Avl bal Rs.25,234.50 -Axis Bank",
            "CREDIT",
        ),
        (
            "INR 2,500.00 deposited in your account XXXX1234 on 14-Jul-2026.",
            "CREDIT",
        ),
        (
            "Rs.50 cashback credited to your wallet for your recent purchase.",
            "CREDIT",
        ),
        (
            "Reminder: Your electricity bill is due on 20th July.",
            "UNKNOWN",
        ),
        ("", "UNKNOWN"),
        (
            "Rs.1.00 Dr. from A/C XXXXXX0000 and Cr. to 9999999999@ybl. "
            "Ref:000000000000. AvlBal:Rs1000.00(2026:01:01 00:00:00). "
            "Not you? Call 18005700/5000-BOB",
            "DEBIT",
        ),
        (
            "Dear BOB UPI User: Your account is credited with INR 1.00 on "
            "2026-01-01 12:00:00 PM by UPI Ref No 000000000000; AvlBal: "
            "Rs1000.00 - BOB",
            "CREDIT",
        ),
    ],
)
def test_categorize_message(body, expected):
    assert categorize_message(body) == expected


def test_otp_boilerplate_does_not_get_classified_as_debit():
    # OTP messages routinely warn about debits/credits if the OTP is
    # shared — this must still classify as OTP, not DEBIT/CREDIT.
    body = (
        "Do not share your OTP 334455 with anyone. Sharing OTP can lead to your "
        "account being debited fraudulently. -Bank"
    )
    assert categorize_message(body) == "OTP"
