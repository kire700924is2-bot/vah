# -*- coding: utf-8 -*-
"""
busquedas.py — Búsqueda de Cliente y Filtro (materiales)
Mantiene toda la lógica de búsqueda para dejar limpio modulo_presupuestos.py.

Cambios relevantes (solo en este archivo):
- Mapeo exacto TIPO → tabla según indicación del usuario.
- Normalización robusta (acentos) y de "BUSCAR POR" (CLAVE/DESCRIPCIÓN).
- Limpieza/reenfoque al cambiar TIPO (FILTRO recibe foco).
- Mensajería clara en errores y "sin resultados".
- CORRECCIÓN: HERRAJES ahora lleva foco a columna PIEZAS (no Cant. Ancho)
"""

from typing import Any, Dict, List, Optional
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QListWidgetItem, QMessageBox


# ----------------- Normalización -----------------
def normalize_token(s: str) -> str:
    import unicodedata
    s = (s or "").upper()
    # quita acentos
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )

def _normalize_buscar_por(s: str) -> str:
    t = normalize_token(s)
    if t.startswith("CL"):       # CL, CLAVE
        return "CLAVE"
    if t.startswith("DE"):       # DE, DES, DESCRIPCION
        return "DESCRIPCION"
    return "CLAVE"

# ----------------- Mapa TIPO → tabla -----------------
_TABLE_MAP = {
    "ALUMINIO":          "dbo.materiales_aluminio",
    "PAQUETE ALUMINIO":  "dbo.paquetes_aluminio",
    "HERRAJES":          "dbo.materiales_herraje",
    "PAQUETE HERRAJES":  "dbo.paquetes_herrajes",
    "HERRERIA":          "dbo.materiales_herreria",   # sin acento
    "HERRERÍA":          "dbo.materiales_herreria",   # con acento
    "OTROS":             "dbo.materiales_otros",
    "PLASTICOS":         "dbo.materiales_plasticos",  # sin acento
    "PLÁSTICOS":         "dbo.materiales_plasticos",  # con acento
    "VIDRIO":            "dbo.materiales_vidrio",
}

def _table_for_tipo(tipo_raw: str) -> Optional[str]:
    t = (tipo_raw or "").strip()
    if not t:
        return None
    # busca directo y con token normalizado
    return _TABLE_MAP.get(t) or _TABLE_MAP.get(normalize_token(t))

# ----------------- Servicio de consulta -----------------
def _svc_query(window, tipo_raw: str, buscar_raw: str, filtro_raw: str) -> List[Dict[str, Any]]:
    """Consulta uniforme contra Service, con fallback seguro."""
    tabla = _table_for_tipo(tipo_raw)
    buscar = _normalize_buscar_por(buscar_raw)
    filtro = (filtro_raw or "").strip().upper()

    if not tabla:
        return []

    # Intento 1: método por tabla (preferido)
    try:
        rows = window.svc.buscar_por_tabla(tabla=tabla, buscar_por=buscar, filtro=filtro)
        if rows:
            return rows
    except Exception:
        # seguimos a fallback
        pass

    # Intento 2: método específico si existiera
    try:
        mname = f"buscar_{normalize_token(tipo_raw).lower()}"
        if hasattr(window.svc, mname):
            return getattr(window.svc, mname)(buscar_por=buscar, filtro=filtro) or []
    except Exception:
        pass

    # Intento 3: API genérica
    try:
        return window.svc.buscar_por_tipo(tipo=tipo_raw, buscar_por=buscar, filtro=filtro, tabla=tabla) or []
    except Exception:
        try:
            return window.svc.buscar_por_tipo(tipo=tipo_raw, buscar_por=buscar, filtro=filtro) or []
        except Exception:
            return []

# API usada por modulo_presupuestos.py
def search_rows_uniform(window, tipo_raw: str, buscar_raw: str, filtro: str) -> List[Dict[str, Any]]:
    return _svc_query(window, tipo_raw, buscar_raw, filtro)

# ----------------- Interacción (barra de búsqueda) -----------------
def after_choose_filtro(window):
    """Se llama al cambiar TIPO: limpia resultados y mueve foco a FILTRO."""
    try:
        window.lst_result.clear()
        window.lst_result.setVisible(False)
        window.le_filtro.clear()
        window.le_filtro.setFocus()
    except Exception:
        pass

def do_search(window):
    """Búsqueda incremental en FILTRO."""
    filtro = (window.le_filtro.text() or "").strip()
    if not filtro:
        window.lst_result.clear()
        window.lst_result.setVisible(False)
        return

    try:
        tipo_raw   = (window.cbo_tipo.currentText() or "").strip()
        buscar_raw = (window.cbo_buscar.currentText() or "").strip()
        rows = search_rows_uniform(window, tipo_raw, buscar_raw, filtro)
    except Exception as e:
        window.lst_result.clear()
        it = QListWidgetItem(f"— ERROR: {e} —")
        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        window.lst_result.addItem(it)
        window.lst_result.setVisible(True)
        return

    window.lst_result.clear()
    if not rows:
        it = QListWidgetItem("— SIN RESULTADOS —")
        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        window.lst_result.addItem(it)
        window.lst_result.setVisible(True)
        return

    for r in rows:
        clave = str(r.get("clave", "")).strip()
        desc  = str(r.get("descripcion", "")).strip()
        it = QListWidgetItem(f"{clave} — {desc}")
        it.setData(Qt.ItemDataRole.UserRole, r)
        window.lst_result.addItem(it)

    window.lst_result.setVisible(True)
    window.lst_result.setCurrentRow(0)

def on_pick_result(window, item):
    """Usuario selecciona un material/paquete de la lista."""
    from PyQt6.QtCore import QTimer

    try:
        rec   = item.data(Qt.ItemDataRole.UserRole) or {}
        tipo  = (window.cbo_tipo.currentText() or "").strip()
        color = (window.cbo_color.currentText() or "").strip()

        try:
            ancho = float(window.sp_ancho.value())
        except Exception:
            ancho = 0.0

        try:
            alto = float(window.sp_alto.value())
        except Exception:
            alto = 0.0

        # Normalizar el tipo para decidir a qué tabla va
        t_up = (tipo or "").upper()
        tnorm = (t_up.replace("Á","A")
                    .replace("É","E")
                    .replace("Í","I")
                    .replace("Ó","O")
                    .replace("Ú","U"))

        # 1) Agregar el renglón a la tabla adecuada
        if tnorm.startswith("HERRERIA"):
            # HERRERÍA → va a la tabla exclusiva inferior (tbl_he)
            window._add_he(rec, tipo, color, ancho, alto, 1)
            target_tbl = window.tbl_he
            # Fila recién agregada
            row = target_tbl.rowCount() - 1
            # Enfocamos en Cant. Ancho de Herrería
            focus_col = window.H_CA
        else:
            # Resto de tipos → tabla estándar superior
            window._add_std(rec, tipo, color, ancho, alto, 1)
            target_tbl = window.tbl
            # Fila recién agregada (siempre la última en tabla estándar)
            row = target_tbl.rowCount() - 1

            # Decidir columna según el tipo (CORREGIDO: HERRAJES va a PIEZAS)
            if tnorm.startswith("ALUMINIO"):
                # Solo materiales básicos de aluminio (no paquetes)
                if "PAQUETE" not in t_up:
                    focus_col = window.C_CA          # Cant. Ancho
                else:
                    focus_col = window.C_ANCHO       # Ancho (paquetes)
            elif tnorm.startswith("VIDRIO"):
                focus_col = window.C_ANCHO           # Ancho
            elif tnorm.startswith("HERRAJES"):
                # CORRECCIÓN: HERRAJES ahora va a PIEZAS (no Cant. Ancho)
                focus_col = window.C_PZAS            # Piezas
            else:
                # OTROS, PLÁSTICOS, HERRERÍA (no pasa aquí, ya fue filtrado arriba)
                focus_col = window.C_PZAS            # Piezas

        # 2) Limpiar / ocultar la lista de resultados
        window.lst_result.clear()
        window.lst_result.setVisible(False)

        # 3) Enfocar DESPUÉS de que Qt termine el doble-click
        def _focus_new_row():
            try:
                target_tbl.setFocus()
                target_tbl.setCurrentCell(row, focus_col)
                it = target_tbl.item(row, focus_col)
                if it is not None:
                    target_tbl.editItem(it)
            except Exception:
                # Si algo falla, no rompemos la app, solo no movemos el foco
                pass

        QTimer.singleShot(0, _focus_new_row)

    except Exception as e:
        QMessageBox.critical(window, "Error en selección", str(e))



# ----------------- CLIENTES -----------------
def format_cliente_for_list(rec: Dict[str, Any]) -> str:
    def take(*keys):
        for k in keys:
            v = rec.get(k)
            if v is not None:
                s = str(v).strip()
                if s:
                    return s
        return ""
    titulo = take("titulo","TITULO")
    nombre = take("nombre","NOMBRE")
    ap     = take("a_paterno","A_PATERNO","APELLIDO_PATERNO","APELLIDO1")
    am     = take("a_materno","A_MATERNO","APELLIDO_MATERNO","APELLIDO2")
    full = " ".join(x for x in [titulo, nombre, ap, am] if x)
    return full.upper() if full else (nombre or ap or am or "(SIN NOMBRE)").upper()

def clientes_start_search(window, text: str):
    """
    Búsqueda incremental de clientes:
    - Se dispara conforme se escribe en le_cliente (textEdited).
    - Siempre muestra la lista:
        * resultados ordenados ASC
        * "— SIN RESULTADOS —" si no hay coincidencias
        * "ERROR: ..." si la consulta falla (para poder ver qué pasa)
    """
    text = (text or "").strip()
    window.btn_nuevo_cliente.setEnabled(False)

    # Si está vacío, limpiamos y ocultamos
    if not text:
        window.lst_clientes.hide()
        window.lst_clientes.clear()
        return

    # Intentamos consultar a la BD
    try:
        rows = window.svc.clientes_buscar(text)
        error_msg = None
    except Exception as e:
        rows = []
        # guardamos mensaje de error para mostrarlo en la lista
        error_msg = str(e)

    window.lst_clientes.clear()

    if error_msg is not None:
        # Mostramos el error directamente en la lista para que se vea la ventana
        it = QListWidgetItem(f"ERROR: {error_msg}")
        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        window.lst_clientes.addItem(it)
        window.lst_clientes.setVisible(True)
        window.btn_nuevo_cliente.setEnabled(True)
        return

    # Sin error: rellenamos con resultados o "SIN RESULTADOS"
    if not rows:
        it = QListWidgetItem("— SIN RESULTADOS —")
        it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        window.lst_clientes.addItem(it)
        window.lst_clientes.setVisible(True)
        window.btn_nuevo_cliente.setEnabled(True)
        return

    # Hay filas → las agregamos
    for r in rows:
        it = QListWidgetItem(format_cliente_for_list(r))
        it.setData(Qt.ItemDataRole.UserRole, r)
        window.lst_clientes.addItem(it)

    # Orden ascendente por el texto que se muestra
    if window.lst_clientes.count() > 1:
        window.lst_clientes.sortItems(Qt.SortOrder.AscendingOrder)

    window.lst_clientes.setVisible(True)
    window.lst_clientes.setCurrentRow(0)

def accept_current_cliente(window):
    it = window.lst_clientes.currentItem()
    if it:
        pick_cliente(window, it)
    else:
        window.btn_nuevo_cliente.setEnabled(True)
        nuevo_cliente(window)

def pick_cliente(window, it: QListWidgetItem):
    rec = it.data(Qt.ItemDataRole.UserRole) or {}
    window.le_cliente.setText(format_cliente_for_list(rec))
    window.btn_nuevo_cliente.setEnabled(False)
    window.lst_clientes.clear()
    window.lst_clientes.setVisible(False)
    window.le_obra.setFocus()

def nuevo_cliente(window):
    txt = (window.le_cliente.text() or "").strip().upper()
    if not txt:
        QMessageBox.information(window, "Nuevo cliente", "Capture el nombre en CLIENTE.")
        window.le_cliente.setFocus()
        return
    window.le_cliente.setText(txt)
    window.btn_nuevo_cliente.setEnabled(False)
    window.le_obra.setFocus()