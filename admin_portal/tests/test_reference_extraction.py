import pytest

from app.services.reference_extraction import extract_reference_id


@pytest.mark.parametrize(
    "body,expected",
    [
        (
            "Rs.1.00 Dr. from A/C XXXXXX0000 and Cr. to 9999999999@ybl. "
            "Ref:000000000000. AvlBal:Rs1000.00. Not you? Call 18005700-BOB",
            "000000000000",
        ),
        (
            "Dear BOB UPI User: Your account is credited with INR 1.00 by "
            "UPI Ref No 000000000000; AvlBal: Rs1000.00 - BOB",
            "000000000000",
        ),
        (
            "Dear UPI user A/C X0000 debited by 200.0 on date 13Dec24 trf to "
            "SOMEONE Refno471403237586. If not u? call 1800111109. -SBI",
            "Refno471403237586"[len("Refno"):],
        ),
        (
            "Rs.15000.00 credited to A/c XX1234 by NEFT UTR: HDFCN52023071012345. "
            "Avl bal Rs.25,234.50 -Axis Bank",
            "HDFCN52023071012345",
        ),
        (
            "Payment of Rs.500 successful. Transaction ID: TXN20260715ABCDE",
            "TXN20260715ABCDE",
        ),
        (
            "123456 is your OTP for txn of Rs.500.00 at AMAZON. Do not share this OTP with anyone. -HDFC Bank",
            None,
        ),
        ("", None),
    ],
)
def test_extract_reference_id(body, expected):
    assert extract_reference_id(body) == expected


def test_reference_number_label_does_not_swallow_number_as_the_code():
    # "Reference Number:" must not capture the word "Number" itself as the
    # code when the real digits come after the colon.
    body = "Your payment Reference Number: 445566778899 has been processed."
    assert extract_reference_id(body) == "445566778899"
