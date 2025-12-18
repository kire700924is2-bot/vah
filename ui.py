"""UI/UX helpers for Presupuestos (consolidated)."""

def adjust_dimension(value: float, step: float = 0.05) -> float:
    return round(value / step) * step
