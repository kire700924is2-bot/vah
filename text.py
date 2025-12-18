"""Text/number helpers for Presupuestos (consolidated)."""

def _f(x, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return float(default)
