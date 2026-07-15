import pytest

from app.services.reference_extraction import extract_reference_id


@pytest.mark.parametrize(
    "body,expected",
    [
        # From the user's own examples.
        (
            "Rs.500 debited from A/c XX1234 on 12-Jul-2026. UPI Ref No "
            "966697814398. Balance Rs.2,500.",
            "966697814398",
        ),
        (
            "INR 1,250 credited. Ref No: 845612397451.",
            "845612397451",
        ),
        (
            "Rs.1.00 Dr. from A/C XXXXXX0000 and Cr. to 9999999999@ybl. "
            "Ref:123456789012. AvlBal:Rs1000.00. Not you? Call 18005700-BOB",
            "123456789012",
        ),
        (
            "Dear BOB UPI User: Your account is credited with INR 1.00 by "
            "UPI Ref No 874512369845; AvlBal: Rs1000.00 - BOB",
            "874512369845",
        ),
        (
            "Dear UPI user A/C X0000 debited by 200.0 on date 13Dec24 trf to "
            "SOMEONE Refno471403237586. If not u? call 1800111109. -SBI",
            "471403237586",
        ),
        (
            "Rs.15000.00 credited to A/c XX1234 by NEFT. UTR: 123456789012. "
            "Avl bal Rs.25,234.50 -Axis Bank",
            "123456789012",
        ),
        (
            "Payment of Rs.500 successful. Transaction ID: 998877665544",
            "998877665544",
        ),
        (
            "Rs.100 credited via UPI. RRN 112233445566 -Bank",
            "112233445566",
        ),
        (
            "123456 is your OTP for txn of Rs.500.00 at AMAZON. Do not share this OTP with anyone. -HDFC Bank",
            None,
        ),
        ("", None),
        # 11 or 13 digits must not be mistaken for a 12-digit reference.
        ("Ref No 12345678901", None),
        ("Ref No 1234567890123", None),
    ],
)
def test_extract_reference_id(body, expected):
    assert extract_reference_id(body) == expected


def test_reference_number_label_does_not_swallow_number_as_the_code():
    # "Reference Number:" must not capture the word "Number" itself as the
    # code when the real digits come after the colon.
    body = "Your payment Reference Number: 445566778899 has been processed."
    assert extract_reference_id(body) == "445566778899"


def test_prefers_keyword_anchored_number_over_unrelated_twelve_digit_number():
    # The message has two 12-digit numbers: an unrelated one (e.g. part of
    # a masked long account/card number) and the actual labelled Ref No.
    # The labelled one must win.
    body = (
        "Card ending 123456789012 used for a purchase. "
        "UPI Ref No 998877665544 confirms the transaction."
    )
    assert extract_reference_id(body) == "998877665544"


def test_falls_back_to_any_standalone_twelve_digit_number_without_a_keyword():
    # No recognizable keyword label at all — fall back to the first
    # standalone 12-digit number found.
    body = "Your account activity: 665544332211 processed successfully today."
    assert extract_reference_id(body) == "665544332211"


def test_does_not_match_twelve_digit_substring_of_a_longer_number():
    # A 16-digit number must not have its first 12 digits mistaken for a
    # standalone reference.
    body = "Card number 1234567890123456 was used."
    assert extract_reference_id(body) is None
