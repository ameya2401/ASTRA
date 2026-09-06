def calculate_total(prices: list[float], discount_rate: float = 0.0) -> float:
    """Calculates subtotal with discount rate validation."""
    if discount_rate < 0.0 or discount_rate > 1.0:
        raise ValueError("discount_rate must be between 0.0 and 1.0")

    total = 0.0
    for price in prices:
        if price > 0:
            total += price
    return total * (1.0 - discount_rate)
