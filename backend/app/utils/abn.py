"""Australian Business Number (ABN) validation utility."""

_WEIGHTS = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]


def validate_abn(abn: str) -> bool:
    """Validate an Australian Business Number using the official algorithm.

    Steps:
    1. Subtract 1 from the first digit.
    2. Multiply each digit by its weighting factor.
    3. Sum the results.
    4. Divide by 89 — valid if remainder is 0.
    """
    digits = abn.replace(" ", "")
    if not digits.isdigit() or len(digits) != 11:
        return False

    d = [int(c) for c in digits]
    d[0] -= 1
    total = sum(w * v for w, v in zip(_WEIGHTS, d))
    return total % 89 == 0
