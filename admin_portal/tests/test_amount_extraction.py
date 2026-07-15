from decimal import Decimal

import pytest

from app.services.amount_extraction import extract_amount


@pytest.mark.parametrize(
    "body,expected",
    [
        ("Rs.500 debited from A/c XX1234...", Decimal("500")),
        ("INR 2,350 credited to your account...", Decimal("2350")),
        ("Rs. 10,000 transferred successfully.", Decimal("10000")),
        ("₹750 received via UPI.", Decimal("750")),
        ("Rs 500.50 debited from A/c XX1234", Decimal("500.50")),
        ("RS.1,234.56 credited", Decimal("1234.56")),
        (
            "Rs.500.00 debited from A/c XX1234 on 14-07-26. Avl bal Rs.10,234.50",
            Decimal("500.00"),
        ),
        ("123456 is your OTP. Do not share it.", None),
        ("", None),
        # "Mrs" must not be mistaken for "Rs".
        ("Mrs. Sharma called about the delivery.", None),
        # Number-before-currency format some banks use.
        ("Acct debited by 5000.00 INR on 15-07-26", Decimal("5000.00")),
        # Colon/dot separators instead of plain whitespace.
        ("Rs:500 debited", Decimal("500")),
        ("INR.500 credited", Decimal("500")),
        # Indian lakh-style grouping.
        ("INR 1,25,000 credited to your account...", Decimal("125000")),
    ],
)
def test_extract_amount(body, expected):
    assert extract_amount(body) == expected
