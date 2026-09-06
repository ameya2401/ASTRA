def calculate_total(prices: list[float]) -> float:
    """Calculates subtotal of prices."""
    total = 0.0
    for price in prices:
        total += price
    return total
