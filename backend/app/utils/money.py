"""
Money utilities ensuring all financial calculations use integer minor units (paise).
Floating point values are strictly forbidden for monetary storage and arithmetic.
"""


def rupees_to_paise(rupees: float | int) -> int:
    """Convert INR rupees to integer paise."""
    return int(round(rupees * 100))


def paise_to_rupees(paise: int) -> float:
    """Convert integer paise to INR rupees (display purposes only)."""
    return round(paise / 100.0, 2)


def validate_paise_amount(amount_paise: int) -> int:
    """Ensure monetary amount in paise is a non-negative integer."""
    if not isinstance(amount_paise, int):
        raise ValueError("Monetary amount must be an integer representing paise.")
    if amount_paise < 0:
        raise ValueError("Monetary amount cannot be negative.")
    return amount_paise
