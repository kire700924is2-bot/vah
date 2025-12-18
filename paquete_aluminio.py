
# -*- coding: utf-8 -*-
from typing import Dict, Any, Tuple
from .aluminio import compute_aluminio
from .herreria import compute_herreria
from .vidrio import compute_vidrio
from .plasticos import compute_plasticos
from .otros import compute_otros
from .herrajes import compute_herrajes

def compute_paquete_aluminio_inline(
    *, svc, clave: str, color: str|None, ancho: float, alto: float, piezas: int, extra: Dict[str, Any]
) -> Tuple[float, float]:
    items = svc.paquete_aluminio_items(clave)
    if not items:
        return 0.0, 0.0
    total_pu = 0.0
    for it in items:
        sub = (it.get("tipo") or "").upper()
        subc = it.get("clave") or ""
        cantidad = int(it.get("cantidad") or 1)

        if sub == "AL":
            ca = float(it.get("horizontal") or 0)
            ch = float(it.get("vertical") or 0)
            pu, _ = compute_aluminio(
                svc=svc, clave=subc, color=color, ancho=ancho, alto=alto,
                piezas=1, ca=ca * cantidad, ch=ch * cantidad, extra=extra
            )
            total_pu += pu

        elif sub in {"HE","HERRERIA","HERRERÍA"}:
            pu, _ = compute_herreria(
                svc=svc, clave=subc, piezas=cantidad, ancho=ancho, alto=alto,
                extra={"precio_kg": extra.get("precio_kg", 0), "ca": extra.get("ca", 0), "ch": extra.get("ch", 0)}
            )
            total_pu += pu

        elif sub == "HR":
            pu, _ = compute_herrajes(svc=svc, clave=subc, piezas=cantidad, extra=extra)
            total_pu += pu

        elif sub == "PL":
            pu, _ = compute_plasticos(svc=svc, clave=subc, piezas=cantidad, extra=extra)
            total_pu += pu

        elif sub == "OT":
            pu, _ = compute_otros(svc=svc, clave=subc, piezas=cantidad, extra=extra)
            total_pu += pu

        elif sub == "VI":
            pu, _ = compute_vidrio(svc=svc, clave=subc, ancho=ancho, alto=alto, piezas=cantidad, extra=extra)
            total_pu += pu

    return total_pu, total_pu * max(1, int(piezas or 1))
