
# -*- coding: utf-8 -*-
from typing import Dict, Any, Tuple

def compute_paquete_herrajes_inline(*, svc, clave: str, piezas: int, extra: Dict[str, Any]) -> Tuple[float, float]:
    total = float(svc.paquete_herrajes_precio_total(clave) or 0)
    piezas = max(1, int(piezas or 1))
    return total, total * piezas
