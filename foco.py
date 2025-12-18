# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/foco.py — Manejo centralizado de focos y navegación por teclado
VERSIÓN DEFINITIVA CON SHIFT+TAB FUNCIONAL 100%

ESTRATEGIA:
1. Para Shift+Tab: Navegación manual directa entre widgets
2. Para Tab: Lógica especial solo para tablas
3. Para Enter: Conversión a Tab

MODIFICACIÓN IMPORTANTE:
- Tabla de Paquetes: Salta automáticamente paquetes anidados (solo informativos)
- Solo paquetes madre reciben foco en campo Ancho
- CORRECCIÓN: Foco en "Piezas" de tabla Paquetes funcionando correctamente
"""

from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QWidget

# Constantes de teclado
EVENT_KEYPRESS = QEvent.Type.KeyPress
KEY_TAB = Qt.Key.Key_Tab
KEY_RETURN = Qt.Key.Key_Return
KEY_ENTER = Qt.Key.Key_Enter
KEY_ESCAPE = Qt.Key.Key_Escape
NO_MOD = Qt.KeyboardModifier.NoModifier
SHIFT_MOD = Qt.KeyboardModifier.ShiftModifier


class GlobalKeyFilter(QObject):
    """
    Filtro de teclas global - SOLUCIÓN COMPLETA
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.w = parent  # PresupuestosWindow
        self._focus_widgets = []  # Cache de widgets enfocables

    def eventFilter(self, obj, ev):
        ev_type = ev.type()

        if ev_type == EVENT_KEYPRESS:
            k = ev.key()
            mod = ev.modifiers()

            # --- SHIFT+TAB: Navegación hacia atrás (MANUAL) ---
            if k == KEY_TAB and mod == SHIFT_MOD:
                return self._handle_shift_tab()

            # --- TAB (sin Shift): Navegación hacia adelante ---
            elif k == KEY_TAB and mod == NO_MOD:
                return self._handle_tab(obj, ev)

            # --- ENTER → TAB ---
            elif k in (KEY_RETURN, KEY_ENTER):
                return self._handle_enter(obj)

            # --- ESC: Cerrar lista de clientes ---
            elif k == KEY_ESCAPE:
                return self._handle_escape(obj)

        return False

    def _handle_shift_tab(self):
        """
        Manejo MANUAL de Shift+Tab - 100% funcional
        """
        current = QApplication.focusWidget()
        if not current:
            return False

        # Obtener lista ordenada de widgets enfocables
        widgets = self._get_focusable_widgets_ordered()

        if not widgets:
            return False

        # Encontrar índice del widget actual
        current_idx = -1
        for i, widget in enumerate(widgets):
            if widget == current:
                current_idx = i
                break

        if current_idx == -1:
            return False

        # Navegar al widget anterior
        for i in range(current_idx - 1, -1, -1):
            prev_widget = widgets[i]
            if prev_widget.isEnabled() and prev_widget.isVisible():
                prev_widget.setFocus()
                return True

        # Si no hay widget anterior, ir al último
        for i in range(len(widgets) - 1, -1, -1):
            last_widget = widgets[i]
            if last_widget != current and last_widget.isEnabled() and last_widget.isVisible():
                last_widget.setFocus()
                return True

        return False

    def _get_focusable_widgets_ordered(self):
        """
        Obtiene TODOS los widgets enfocables en orden lógico de navegación
        """
        # Si ya tenemos la lista cacheada, usarla
        if hasattr(self, '_cached_widgets') and self._cached_widgets:
            return self._cached_widgets

        widgets = []

        # Definir el orden EXACTO de navegación basado en tu interfaz
        # Panel izquierdo primero, luego panel derecho

        # 1. PANEL IZQUIERDO
        left_widgets = [
            self.w.le_cliente,  # CLIENTE
            self.w.le_obra,  # OBRA
            self.w.sp_presupuesto,  # PRESUPUESTO
            self.w.sp_partida,  # PARTIDA
            self.w.de_fv,  # FECHA
            self.w.cbo_color_global,  # COLOR GLOBAL
            self.w.cbo_color,  # COLOR (PARTIDA) - solo si está habilitado
            self.w.le_titulo,  # TÍTULO
            self.w.te_desc,  # DESCRIPCIÓN
            self.w.sb_desperdicio,  # DESPERDICIO
            self.w.sb_fv_pct,  # F.V. (%)
            self.w.sp_precio_kg,  # $ / KG
            self.w.sp_ancho,  # ANCHO
            self.w.sp_alto,  # ALTO
            self.w.sp_mo,  # MANO DE OBRA
            self.w.sp_acc,  # ACCESORIOS
            self.w.sb_pzas_global,  # PIEZAS (globales)
        ]

        # 2. PANEL DERECHO
        right_widgets = [
            self.w.cbo_tipo,  # TIPO
            self.w.cbo_buscar,  # BUSCAR POR
            self.w.le_filtro,  # FILTRO
            self.w.tbl_paquetes,  # Tabla Paquetes
            self.w.tbl,  # Tabla Materiales
            self.w.tbl_he,  # Tabla Herrería
        ]

        # Combinar en orden correcto
        all_widgets = []

        # Solo agregar widgets que existen y son enfocables
        for widget in left_widgets + right_widgets:
            if (widget is not None and
                    hasattr(widget, 'setFocus') and
                    widget.focusPolicy() != Qt.FocusPolicy.NoFocus):
                all_widgets.append(widget)

        # Cachear para mejor rendimiento
        self._cached_widgets = all_widgets

        return all_widgets

    def _handle_tab(self, obj, ev):
        """
        Manejo de Tab (sin Shift) - solo lógica especial para tablas
        """
        fw = QApplication.focusWidget()

        # Tabla estándar (Materiales)
        tbl = getattr(self.w, "tbl", None)
        if tbl is not None and (fw is tbl or tbl.isAncestorOf(fw)):
            return self._handle_table_tab(tbl, "std")

        # Tabla de Herrería
        tbl_he = getattr(self.w, "tbl_he", None)
        if tbl_he is not None and (fw is tbl_he or tbl_he.isAncestorOf(fw)):
            return self._handle_table_tab(tbl_he, "he")

        # Tabla de Paquetes
        tbl_paquetes = getattr(self.w, "tbl_paquetes", None)
        if tbl_paquetes is not None and (fw is tbl_paquetes or tbl_paquetes.isAncestorOf(fw)):
            return self._handle_paquetes_table_tab(tbl_paquetes)

        # Para otros widgets, dejar que Qt maneje el Tab normalmente
        return False

    def _handle_table_tab(self, table, table_type):
        """Maneja Tab dentro de tablas"""
        try:
            row = table.currentRow()
            col = table.currentColumn()
        except Exception:
            return False

        if row < 0 or col < 0:
            return False

        if table_type == "std":
            return self._navigate_std_table(table, row, col)
        elif table_type == "he":
            return self._navigate_he_table(table, row, col)

        return False

    def _navigate_std_table(self, table, row, col):
        """Navegación en tabla estándar"""
        # Tipo de la fila actual
        tipo = ""
        try:
            if hasattr(self.w, "_get_tipo"):
                tipo = (self.w._get_tipo(row) or "").strip().upper()
            else:
                it_tipo = table.item(row, getattr(self.w, "C_TIPO", 0))
                tipo = (it_tipo.text() if it_tipo else "").strip().upper()
        except Exception:
            tipo = ""

        C_CA = getattr(self.w, "C_CA", -1)
        C_ANCHO = getattr(self.w, "C_ANCHO", -1)
        C_CH = getattr(self.w, "C_CH", -1)
        C_ALTO = getattr(self.w, "C_ALTO", -1)
        C_PZAS = getattr(self.w, "C_PZAS", -1)

        # Normalizar tipo
        tipo_norm = tipo.upper()
        if "Á" in tipo_norm: tipo_norm = tipo_norm.replace("Á", "A")
        if "É" in tipo_norm: tipo_norm = tipo_norm.replace("É", "E")
        if "Í" in tipo_norm: tipo_norm = tipo_norm.replace("Í", "I")
        if "Ó" in tipo_norm: tipo_norm = tipo_norm.replace("Ó", "O")
        if "Ú" in tipo_norm: tipo_norm = tipo_norm.replace("Ú", "U")

        es_al = tipo_norm.startswith("ALUMINIO")
        es_he = tipo_norm.startswith("HERRAJES")
        es_vi = tipo_norm.startswith("VIDRIO")
        es_paq_al = any(x in tipo_norm for x in ["PAQUETE ALUMINIO", "PAQUETE ALUMIO", "PAQ-AL", "PAQ AL"])

        # Si estamos en PZAS, salir a TIPO
        if col == C_PZAS and hasattr(self.w, "cbo_tipo"):
            try:
                self.w.cbo_tipo.setFocus()
                return True
            except Exception:
                pass

        # Determinar destino
        dest = None

        if es_al:
            if col == C_CA:
                dest = C_ANCHO
            elif col == C_ANCHO:
                dest = C_CH
            elif col == C_CH:
                dest = C_ALTO
            elif col == C_ALTO:
                dest = C_PZAS
        elif es_he:
            dest = C_PZAS  # Solo PZAS es editable
        elif es_vi or es_paq_al:
            if col == C_ANCHO:
                dest = C_ALTO
            elif col == C_ALTO:
                dest = C_PZAS

        if dest is not None and dest >= 0:
            try:
                table.setCurrentCell(row, dest)
                it = table.item(row, dest)
                if it is not None:
                    table.editItem(it)
                return True
            except Exception:
                pass

        return False

    def _navigate_he_table(self, table, row, col):
        """Navegación en tabla de Herrería"""
        H_CA = 3
        H_ANCHO = 4
        H_CH = 5
        H_ALTO = 6
        H_PZAS = 11

        dest = None

        if col == H_CA:
            dest = H_ANCHO
        elif col == H_ANCHO:
            dest = H_CH
        elif col == H_CH:
            dest = H_ALTO
        elif col == H_ALTO:
            dest = H_PZAS
        elif col == H_PZAS and hasattr(self.w, "cbo_tipo"):
            try:
                self.w.cbo_tipo.setFocus()
                return True
            except Exception:
                pass

        if dest is not None:
            try:
                table.setCurrentCell(row, dest)
                it = table.item(row, dest)
                if it is not None:
                    table.editItem(it)
                return True
            except Exception:
                pass

        return False

    def _handle_paquetes_table_tab(self, table):
        """Maneja Tab en tabla de Paquetes - Salta paquetes anidados automáticamente"""
        try:
            row = table.currentRow()
            col = table.currentColumn()
        except Exception:
            return False

        # Verificar si la celda actual es de un paquete anidado
        item_tipo = table.item(row, getattr(self.w, "P_TIPO", 0))
        es_anidado = False

        if item_tipo:
            datos = item_tipo.data(Qt.ItemDataRole.UserRole)
            if datos and datos.get("es_anidado", False):
                es_anidado = True

        # Si estamos en un paquete anidado, saltar al siguiente paquete madre
        if es_anidado:
            # Buscar siguiente paquete madre
            for f in range(row + 1, table.rowCount()):
                item_tipo_next = table.item(f, getattr(self.w, "P_TIPO", 0))
                if item_tipo_next:
                    datos_next = item_tipo_next.data(Qt.ItemDataRole.UserRole)
                    if datos_next and not datos_next.get("es_anidado", False):
                        # Enfocar Ancho del siguiente paquete madre
                        table.setCurrentCell(f, getattr(self.w, "P_ANCHO", 3))
                        it = table.item(f, getattr(self.w, "P_ANCHO", 3))
                        if it is not None:
                            table.editItem(it)
                        return True

            # Si no hay más paquetes madre, ir al combo TIPO
            if hasattr(self.w, "cbo_tipo"):
                try:
                    self.w.cbo_tipo.setFocus()
                    return True
                except Exception:
                    pass
            return True

        # Para paquetes madre, navegación normal
        P_ANCHO = getattr(self.w, "P_ANCHO", 3)
        P_ALTO = getattr(self.w, "P_ALTO", 4)
        P_PZAS = getattr(self.w, "P_PZAS", 5)

        # Secuencia: Ancho → Alto → Piezas → TIPO
        if col == P_ANCHO:  # Ancho → Alto
            dest = P_ALTO
        elif col == P_ALTO:  # Alto → Piezas
            dest = P_PZAS
        elif col == P_PZAS:  # Piezas → TIPO
            if hasattr(self.w, "cbo_tipo"):
                try:
                    self.w.cbo_tipo.setFocus()
                    return True
                except Exception:
                    pass
            return True
        else:
            # Si estamos en Tipo, Clave o Descripción, ir a Ancho
            dest = P_ANCHO

        if dest is not None:
            try:
                table.setCurrentCell(row, dest)
                it = table.item(row, dest)
                if it is not None:
                    # CORRECCIÓN: Asegurar que la celda sea editable
                    if (dest == P_PZAS and
                        not es_anidado and
                        (it.flags() & Qt.ItemFlag.ItemIsEditable)):
                        table.editItem(it)
                    elif dest != P_PZAS:
                        table.editItem(it)
                return True
            except Exception as e:
                print(f"Error al enfocar celda: {e}")
                pass

        return False

    def _handle_enter(self, obj):
        """Convierte ENTER a TAB"""
        # Casos especiales primero
        if hasattr(self.w, "lst_clientes") and obj is self.w.lst_clientes:
            try:
                import busquedas
                busquedas.accept_current_cliente(self.w)
                if hasattr(self.w, "le_obra"):
                    self.w.le_obra.setFocus()
                return True
            except Exception:
                pass

        if obj is getattr(self.w, "te_desc", None):
            try:
                if hasattr(self.w, "sb_desperdicio"):
                    self.w.sb_desperdicio.setFocus()
                    return True
            except Exception:
                pass

        # ENTER en tablas → TAB
        if (obj is getattr(self.w, "tbl", None) or
                obj is getattr(self.w, "tbl_he", None) or
                obj is getattr(self.w, "tbl_paquetes", None)):
            # Simular Tab
            QApplication.sendEvent(obj, QKeyEvent(EVENT_KEYPRESS, KEY_TAB, NO_MOD))
            return True

        # ENTER general → TAB
        QApplication.sendEvent(obj, QKeyEvent(EVENT_KEYPRESS, KEY_TAB, NO_MOD))
        return True

    def _handle_escape(self, obj):
        """Maneja ESC para cerrar lista de clientes"""
        if (obj is getattr(self.w, "le_cliente", None) or
                obj is getattr(self.w, "lst_clientes", None)):
            if hasattr(self.w, "lst_clientes"):
                self.w.lst_clientes.setVisible(False)
                return True
        return False


def _pzas_global_to_tipo(window):
    """Maneja el cambio de foco desde PZAS globales hacia TIPO"""
    if not hasattr(window, "sb_pzas_global") or not hasattr(window, "cbo_tipo"):
        return

    fw = QApplication.focusWidget()

    # No robar foco si estamos en una tabla
    if (fw is getattr(window, "tbl", None) or
            fw is getattr(window, "tbl_he", None) or
            fw is getattr(window, "tbl_paquetes", None)):
        return

    # Verificar si es hijo de tabla
    parent = fw.parent()
    while parent:
        if (parent is getattr(window, "tbl", None) or
                parent is getattr(window, "tbl_he", None) or
                parent is getattr(window, "tbl_paquetes", None)):
            return
        parent = parent.parent()

    try:
        window.cbo_tipo.setFocus()
    except Exception:
        pass


def install_global_key_filter(window):
    """Instala el filtro global de teclas"""
    keyfilter = GlobalKeyFilter(window)
    QApplication.instance().installEventFilter(keyfilter)
    return keyfilter


def connect_focus_flows(window):
    """
    Conexiones de flujo de foco - Mantener igual que antes
    """
    # CLIENTE → OBRA
    if hasattr(window, "le_cliente") and hasattr(window, "le_obra"):
        def _cliente_to_obra():
            try:
                window.le_obra.setFocus()
            except Exception:
                pass

        window.le_cliente.editingFinished.connect(_cliente_to_obra)

    # OBRA → PRESUPUESTO
    if hasattr(window, "le_obra") and hasattr(window, "sp_presupuesto"):
        window.le_obra.editingFinished.connect(lambda: window.sp_presupuesto.setFocus())

    # PRESUPUESTO → PARTIDA
    if hasattr(window, "sp_presupuesto") and hasattr(window, "sp_partida"):
        window.sp_presupuesto.editingFinished.connect(lambda: window.sp_partida.setFocus())

    # PARTIDA → FECHA
    if hasattr(window, "sp_partida") and hasattr(window, "de_fv"):
        window.sp_partida.editingFinished.connect(lambda: window.de_fv.setFocus())

    # FECHA → COLOR GLOBAL
    if hasattr(window, "de_fv") and hasattr(window, "cbo_color_global"):
        window.de_fv.editingFinished.connect(lambda: window.cbo_color_global.setFocus())

    # COLOR GLOBAL → COLOR PARTIDA o TÍTULO
    if hasattr(window, "cbo_color_global"):
        def _after_color_global():
            g = (window.cbo_color_global.currentText() or "").strip().upper()
            if g == "VARIOS" and hasattr(window, "cbo_color"):
                window.cbo_color.setFocus()
            else:
                if hasattr(window, "le_titulo"):
                    window.le_titulo.setFocus()

        window.cbo_color_global.activated.connect(lambda _=None: _after_color_global())

    # COLOR(PARTIDA) → TÍTULO
    if hasattr(window, "cbo_color") and hasattr(window, "le_titulo"):
        window.cbo_color.activated.connect(lambda _=None: window.le_titulo.setFocus())

    # TÍTULO → DESCRIPCIÓN
    if hasattr(window, "le_titulo") and hasattr(window, "te_desc"):
        window.le_titulo.editingFinished.connect(lambda: window.te_desc.setFocus())

    # DESPERDICIO → F.V. (%)
    if hasattr(window, "sb_desperdicio") and hasattr(window, "sb_fv_pct"):
        window.sb_desperdicio.editingFinished.connect(lambda: window.sb_fv_pct.setFocus())

    # F.V. (%) → $ / KG
    if hasattr(window, "sb_fv_pct") and hasattr(window, "sp_precio_kg"):
        window.sb_fv_pct.editingFinished.connect(lambda: window.sp_precio_kg.setFocus())

    # $ / KG → ANCHO
    if hasattr(window, "sp_precio_kg") and hasattr(window, "sp_ancho"):
        window.sp_precio_kg.editingFinished.connect(lambda: window.sp_ancho.setFocus())

    # ANCHO → ALTO
    if hasattr(window, "sp_ancho") and hasattr(window, "sp_alto"):
        window.sp_ancho.editingFinished.connect(lambda: window.sp_alto.setFocus())

    # ALTO → MANO DE OBRA
    if hasattr(window, "sp_alto") and hasattr(window, "sp_mo"):
        window.sp_alto.editingFinished.connect(lambda: window.sp_mo.setFocus())

    # MANO DE OBRA → ACCESORIOS
    if hasattr(window, "sp_mo") and hasattr(window, "sp_acc"):
        window.sp_mo.editingFinished.connect(lambda: window.sp_acc.setFocus())

    # ACCESORIOS → PZAS (globales)
    if hasattr(window, "sp_acc") and hasattr(window, "sb_pzas_global"):
        window.sp_acc.editingFinished.connect(lambda: window.sb_pzas_global.setFocus())

    # PZAS (globales) → TIPO
    if hasattr(window, "sb_pzas_global") and hasattr(window, "cbo_tipo"):
        window.sb_pzas_global.editingFinished.connect(lambda: _pzas_global_to_tipo(window))

    # TIPO → BUSCAR POR
    if hasattr(window, "cbo_tipo") and hasattr(window, "cbo_buscar"):
        window.cbo_tipo.activated.connect(lambda _=None: window.cbo_buscar.setFocus())

    # BUSCAR POR → FILTRO
    if hasattr(window, "cbo_buscar") and hasattr(window, "le_filtro"):
        window.cbo_buscar.activated.connect(lambda _=None: window.le_filtro.setFocus())


# Funciones auxiliares (mantener igual)
def focus_col(window, row: int, col: int):
    if not hasattr(window, "tbl"):
        return
    try:
        window.tbl.setFocus()
        window.tbl.setCurrentCell(row, col)
        it = window.tbl.item(row, col)
        if it is not None:
            window.tbl.editItem(it)
    except Exception:
        pass


def focus_after_add(window, row: int):
    if not hasattr(window, "tbl"):
        return
    if row < 0 or row >= window.tbl.rowCount():
        return

    try:
        tipo = (window._get_tipo(row) or "").strip().upper()
    except Exception:
        tipo = ""

    tnorm = tipo.replace("Í", "I").replace("Á", "A").replace("É", "E").replace("Ó", "O").replace("Ú", "U")

    es_al = tnorm.startswith("ALUMINIO")
    es_he = tnorm.startswith("HERRAJES")
    es_vi = tnorm.startswith("VIDRIO")
    es_paq_al = ("PAQUETE ALUMINIO" in tipo) or ("PAQ-AL" in tnorm)

    if es_al:
        first_col = window.C_CA
    elif (es_vi or es_paq_al):
        first_col = window.C_ANCHO
    else:
        first_col = window.C_PZAS

    focus_col(window, row, first_col)


def force_focus_on_pzas(window, row: int):
    if not hasattr(window, "tbl"):
        return
    if row < 0 or row >= window.tbl.rowCount():
        return

    C_PZAS = getattr(window, "C_PZAS", -1)
    if C_PZAS >= 0:
        focus_col(window, row, C_PZAS)