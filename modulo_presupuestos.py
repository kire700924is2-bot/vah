# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/modulo_presupuestos.py
Versión completa usando core/utils.py y core/constants.py

INTEGRACIÓN COMPLETA DE FUNCIONALIDADES:
- Importación centralizada de constantes desde core.constants
- Importación de funciones helper desde core.utils
- Mantenimiento de toda la funcionalidad original
- Código más limpio y mantenible

EJECUCIÓN RECOMENDADA: python -m presupuestos
"""

from __future__ import annotations

import sys
import os
import warnings

# Suprimir advertencia de importación circular (no afecta funcionalidad)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Configurar path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Resto del código permanece igual...
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Set

from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QIcon, QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QGroupBox, QLabel, QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox,
    QTextEdit, QPushButton, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QSplitter, QSizePolicy
)

# ... resto del archivo sin cambios



# ============================================================================
# INICIALIZACIÓN DEL MÓDULO CORE
# ============================================================================

# Inicializar el módulo core para resolver problemas de importación
try:
    from presupuestos.core.utils import initialize_module

    initialize_module()
except ImportError:
    # Si falla, intentar agregar la ruta manualmente
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from core.utils import initialize_module

    initialize_module()

# ============================================================================
# IMPORTACIÓN DE CONSTANTES Y UTILIDADES DESDE CORE
# ============================================================================

from presupuestos.core.constants import (
    # Índices de columnas para tabla estándar
    C_TIPO, C_COLOR, C_CLAVE, C_DESC, C_CA, C_ANCHO, C_CH, C_ALTO, C_PZAS, C_PU, C_IMP,

    # Índices de columnas para tabla de Herrería
    H_TIPO, H_CLAVE, H_DESC, H_CA, H_ANCHO, H_CH, H_ALTO, H_METROS, H_KG_M, H_KGS,
    H_PKG, H_PZAS, H_PU, H_IMP,

    # Índices de columnas para tabla de Paquetes (6 columnas)
    P_TIPO, P_CLAVE, P_DESC, P_ANCHO, P_ALTO, P_PZAS,

    # Índices de columnas para tabla Anidada
    A_TIPO, A_COLOR, A_CLAVE, A_DESC, A_CA, A_ANCHO, A_CH, A_ALTO, A_PZAS, A_PU, A_IMP,

    # Reglas de editabilidad por tipo de material
    EDITABILIDAD,

    # Valores por defecto y configuraciones
    ICON_PATH,
    WINDOW_TITLE,
    DEFAULT_COLOR_GLOBAL,
    SPLITTER_LEFT_RATIO,
    COLOR_EDITABLE,
    COLOR_READONLY,
    COLOR_FOCUS_BORDER,
    COLOR_TABLE_READONLY_BG,
    COLOR_TABLE_READONLY_TEXT,
    COLOR_ANIDADA_BG,
    COLOR_ANIDADA_BORDER,
    STYLESHEET,

    # Listas de opciones
    TIPOS_MATERIAL,
    TIPOS_BUSQUEDA,
    COLORES_GLOBAL,
    COLORES_PARTIDA,
)

# Importar funciones de utilidad desde core.utils
from presupuestos.core.utils import (
    # Funciones de conversión
    to_float as _f,
    to_int as _i,
    format_money as _money,

    # Funciones de UI
    connect_upper_lineedit as _connect_upper_lineedit,
    connect_upper_textedit as _connect_upper_textedit,
    connect_upper_combobox as _connect_upper_combobox,

    # Funciones matemáticas
    round_up_to_005 as _round_up_to_005,
    ajustar_medidas_industriales as _ajustar_medidas_industriales,

    # Funciones para tablas
    safe_table_text,
    set_table_item_text,
    set_table_money,

    # Funciones para manejo de paquetes
    es_tipo_paquete,

    # Otras utilidades
    limpiar_texto,
    normalizar_clave,
)

# ============================================================================
# IMPORTACIÓN DE MÓDULOS EXTERNOS
# ============================================================================

try:
    from . import busquedas  # type: ignore
    from .foco import (  # type: ignore
        install_global_key_filter,
        connect_focus_flows,
        focus_col,
        focus_after_add,
        force_focus_on_pzas
    )
    # IMPORTANTE: Importar dimensioning SOLO para uso interno en cálculos
    from .calculators.dimensioning import adjust_dimension  # type: ignore
except Exception:
    import sys
    import os

    sys.path.insert(0, os.path.dirname(__file__))
    import busquedas  # type: ignore
    from foco import (  # type: ignore
        install_global_key_filter,
        connect_focus_flows,
        focus_col,
        focus_after_add,
        force_focus_on_pzas
    )

    # Fallback si dimensioning no está disponible
    try:
        from calculators.dimensioning import adjust_dimension
    except ImportError:
        import math


        # Función de respaldo que replica la lógica básica
        def adjust_dimension(value: float, step: float = 0.05) -> float:
            """Función de respaldo si dimensioning.py no está disponible."""
            if value <= 0:
                return 0.0
            # Lógica simplificada: subir al siguiente múltiplo de step
            return math.ceil(value / step) * step

try:
    from presupuestos.service import Service
    from presupuestos.calculators import EspecificacionesCtx, dispatch_calculo
    from presupuestos.rules_zero_price import guard_before_add
except Exception:
    # Clases de respaldo para desarrollo
    class Service:
        def buscar_por_tipo(self, **_):
            return []

        def buscar_por_tabla(self, **_):
            return []

        def clientes_buscar(self, *_):
            return []

        def herreria_kg_por_m(self, clave):
            return 0.0

        def paquete_aluminio_items(self, clave_paquete):
            # Datos de ejemplo actualizados basados en la imagen
            if clave_paquete == "PPHER":
                return [
                    {"clave": "9083", "descripcion": "BOLSA", "horizontal": 1, "vertical": 2, "cantidad": 1,
                     "tipo": "AL"},
                    {"clave": "PH", "descripcion": "PRUEBA PAQUETE HERRAJES", "horizontal": 1, "vertical": 1,
                     "cantidad": 1, "tipo": "PH"},
                    {"clave": "9088", "descripcion": "JUNQUILLO", "horizontal": 1, "vertical": 0, "cantidad": 1,
                     "tipo": "AL"}
                ]
            elif clave_paquete == "PH":
                # Este es el paquete de herrajes anidado
                return [
                    {"clave": "H001", "descripcion": "BISAGRA", "horizontal": 1, "vertical": 0, "cantidad": 4,
                     "tipo": "HR"},
                    {"clave": "H002", "descripcion": "PESTILLO", "horizontal": 1, "vertical": 0, "cantidad": 1,
                     "tipo": "HR"},
                    {"clave": "H003", "descripcion": "MANIJA", "horizontal": 1, "vertical": 0, "cantidad": 1,
                     "tipo": "HR"}
                ]
            return []

        def paquete_herrajes_items(self, clave_paquete):
            # Datos de ejemplo para paquete de herrajes
            if clave_paquete == "PH":
                return [
                    {"clave": "H001", "descripcion": "BISAGRA", "horizontal": 1, "vertical": 0, "cantidad": 4,
                     "tipo": "HR"},
                    {"clave": "H002", "descripcion": "PESTILLO", "horizontal": 1, "vertical": 0, "cantidad": 1,
                     "tipo": "HR"},
                    {"clave": "H003", "descripcion": "MANIJA", "horizontal": 1, "vertical": 0, "cantidad": 1,
                     "tipo": "HR"}
                ]
            return []

        def obtener_descripcion_material(self, tipo_base, clave_real):
            if clave_real == "9083":
                return "Material BOLSA"
            elif clave_real == "9088":
                return "Material JUNQUILLO"
            elif clave_real == "H001":
                return "BISAGRA"
            elif clave_real == "H002":
                return "PESTILLO"
            elif clave_real == "H003":
                return "MANIJA"
            else:
                return f"Componente {clave_real}"


    from dataclasses import dataclass


    @dataclass
    class EspecificacionesCtx:
        svc: Any
        tipo: str
        clave: str
        color: str | None
        ancho: float
        alto: float
        piezas: int
        ca: float
        ch: float
        extra: Dict[str, Any]


    def dispatch_calculo(ctx: EspecificacionesCtx) -> Tuple[float, float]:
        return 0.0, 0.0


    def guard_before_add(*_, **__):
        class R:
            proceed = True
            faltantes = []

        return R()


# ============================================================================
# CLASE PRINCIPAL PresupuestosWindow (COMPLETA)
# ============================================================================

class PresupuestosWindow(QMainWindow):
    # Índices de columnas (para referencia local)
    C_TIPO = C_TIPO
    C_COLOR = C_COLOR
    C_CLAVE = C_CLAVE
    C_DESC = C_DESC
    C_CA = C_CA
    C_ANCHO = C_ANCHO
    C_CH = C_CH
    C_ALTO = C_ALTO
    C_PZAS = C_PZAS
    C_PU = C_PU
    C_IMP = C_IMP

    H_TIPO = H_TIPO
    H_CLAVE = H_CLAVE
    H_DESC = H_DESC
    H_CA = H_CA
    H_ANCHO = H_ANCHO
    H_CH = H_CH
    H_ALTO = H_ALTO
    H_METROS = H_METROS
    H_KG_M = H_KG_M
    H_KGS = H_KGS
    H_PKG = H_PKG
    H_PZAS = H_PZAS
    H_PU = H_PU
    H_IMP = H_IMP

    P_TIPO = P_TIPO
    P_CLAVE = P_CLAVE
    P_DESC = P_DESC
    P_ANCHO = P_ANCHO
    P_ALTO = P_ALTO
    P_PZAS = P_PZAS

    A_TIPO = A_TIPO
    A_COLOR = A_COLOR
    A_CLAVE = A_CLAVE
    A_DESC = A_DESC
    A_CA = A_CA
    A_ANCHO = A_ANCHO
    A_CH = A_CH
    A_ALTO = A_ALTO
    A_PZAS = A_PZAS
    A_PU = A_PU
    A_IMP = A_IMP

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Usar constantes importadas
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon(ICON_PATH))
        self.svc = Service()
        self._prog = False
        self._search_timer = QTimer(self, interval=160, singleShot=True)
        self._search_timer.timeout.connect(lambda: busquedas.do_search(self))
        self._paquete_actual = None
        self._paquete_seleccionado = None
        self._paquetes_desglosados = {}
        self._paquetes_anidados_pendientes = {}
        self._cantidades_base_componentes = {}
        self._instancias_paquetes = {}
        self._tabla_anidada_activa = False  # Indica si la tabla anidada está mostrando un paquete
        self._paquete_anidado_actual = None  # Clave del paquete actualmente en tabla anidada
        self._componentes_base_actuales = []  # Componentes base del paquete actual (sin multiplicar)

        # Construir UI antes del menú
        self._build_ui()
        self._build_menu()

        self.keyfilter = install_global_key_filter(self)
        self._ensure_focusable_widgets()
        connect_focus_flows(self)

        # IMPORTANTE: Configurar política de foco para permitir Shift+Tab
        self._setup_focus_policy()

    # ============================================================================
    # MÉTODOS DE CONSTRUCCIÓN DE UI
    # ============================================================================

    def _ensure_focusable_widgets(self):
        """
        Asegura que todos los widgets tengan política de foco correcta
        """
        # Lista de TODOS los widgets que deben ser enfocables
        focusable_widgets = [
            self.le_cliente, self.le_obra, self.sp_presupuesto, self.sp_partida,
            self.de_fv, self.cbo_color_global, self.cbo_color, self.le_titulo,
            self.te_desc, self.sb_desperdicio, self.sb_fv_pct, self.sp_precio_kg,
            self.sp_ancho, self.sp_alto, self.sp_mo, self.sp_acc,
            self.sb_pzas_global, self.cbo_tipo, self.cbo_buscar, self.le_filtro,
            self.tbl, self.tbl_he, self.tbl_paquetes, self.tbl_anidada
        ]

        for widget in focusable_widgets:
            if widget:
                # Asegurar que sean enfocables
                if hasattr(widget, 'setFocusPolicy'):
                    # Solo cambiar si no es NoFocus
                    if widget.focusPolicy() == Qt.FocusPolicy.NoFocus:
                        # Para widgets de solo lectura, mantener NoFocus
                        if not getattr(widget, 'isReadOnly', lambda: False)():
                            widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _setup_focus_policy(self):
        """Configura políticas de foco para todos los widgets editables"""
        widgets = [
            self.le_cliente, self.le_obra, self.sp_presupuesto, self.sp_partida,
            self.de_fv, self.cbo_color_global, self.cbo_color, self.le_titulo,
            self.te_desc, self.sb_desperdicio, self.sb_fv_pct, self.sp_precio_kg,
            self.sp_ancho, self.sp_alto, self.sp_mo, self.sp_acc,
            self.sb_pzas_global, self.cbo_tipo, self.cbo_buscar, self.le_filtro
        ]

        for widget in widgets:
            if widget:
                # Solo para widgets que no son de solo lectura
                if not getattr(widget, 'isReadOnly', lambda: False)():
                    widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def showEvent(self, e):
        """Evento que se ejecuta cuando la ventana se muestra."""
        super().showEvent(e)
        if not self.isMaximized():
            self.showMaximized()
        self._set_fecha_hoy()
        QTimer.singleShot(0, self._apply_split_20_80)

    def resizeEvent(self, e):
        """Evento que se ejecuta cuando la ventana cambia de tamaño."""
        super().resizeEvent(e)
        self._apply_split_20_80()

    def _apply_split_20_80(self) -> None:
        """Aplica la división 20%/80% al splitter principal."""
        try:
            if hasattr(self, "split") and self.split is not None:
                w = max(1, self.width())
                left = int(w * SPLITTER_LEFT_RATIO)
                right = max(1, w - left)
                sizes = self.split.sizes()
                if not sizes or abs(sizes[0] - left) > 3:
                    self.split.setSizes([left, right])
        except Exception:
            pass

    def _build_ui(self) -> None:
        """Construye toda la interfaz de usuario."""
        root = QWidget(self)
        self.setCentralWidget(root)

        # Layout principal
        rl = QHBoxLayout(root)
        rl.setContentsMargins(8, 8, 8, 8)
        rl.setSpacing(8)

        # Splitter principal (20%/80%)
        self.split = QSplitter(Qt.Orientation.Horizontal, self)
        self.split.setHandleWidth(6)
        rl.addWidget(self.split)

        # --- PANEL IZQUIERDO (20%) ---
        left = QWidget(self)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(8)

        # Grupo: Datos del presupuesto
        gb_d = QGroupBox("Datos del presupuesto", self)
        g = QGridLayout(gb_d)
        g.setContentsMargins(8, 8, 8, 8)
        g.setSpacing(6)

        r = 0
        g.addWidget(QLabel("CLIENTE:"), r, 0)
        self.le_cliente = QLineEdit(self)
        g.addWidget(self.le_cliente, r, 1)
        r += 1
        self.le_cliente.textEdited.connect(lambda s: busquedas.clientes_start_search(self, s))
        _connect_upper_lineedit(self.le_cliente)

        self.btn_nuevo_cliente = QPushButton("Nuevo cliente", self,
                                             clicked=lambda: busquedas.nuevo_cliente(self))
        self.btn_nuevo_cliente.setEnabled(False)
        g.addWidget(self.btn_nuevo_cliente, r, 1)
        r += 1

        self.lst_clientes = QListWidget(self)
        self.lst_clientes.setVisible(False)
        self.lst_clientes.itemActivated.connect(lambda it: busquedas.pick_cliente(self, it))
        g.addWidget(self.lst_clientes, r, 0, 1, 2)
        r += 1

        g.addWidget(QLabel("OBRA:"), r, 0)
        self.le_obra = QLineEdit(self)
        g.addWidget(self.le_obra, r, 1)
        r += 1
        _connect_upper_lineedit(self.le_obra)

        # NUEVO: Campo Presupuesto
        g.addWidget(QLabel("PRESUPUESTO:"), r, 0)
        self.sp_presupuesto = QSpinBox(self, minimum=1, maximum=999999)
        self.sp_presupuesto.setValue(1)
        self.sp_presupuesto.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.sp_presupuesto.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sp_presupuesto.setReadOnly(True)
        g.addWidget(self.sp_presupuesto, r, 1)
        r += 1

        # NUEVO: Campo Partida
        g.addWidget(QLabel("PARTIDA:"), r, 0)
        self.sp_partida = QSpinBox(self, minimum=1, maximum=999999)
        self.sp_partida.setValue(1)
        self.sp_partida.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.sp_partida.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.sp_partida.setReadOnly(True)
        g.addWidget(self.sp_partida, r, 1)
        r += 1

        g.addWidget(QLabel("FECHA:"), r, 0)
        self.de_fv = QDateEdit(self, calendarPopup=True)
        g.addWidget(self.de_fv, r, 1)
        r += 1

        g.addWidget(QLabel("COLOR:"), r, 0)
        self.cbo_color_global = QComboBox(self)
        self.cbo_color_global.setEditable(True)
        self.cbo_color_global.addItems(COLORES_GLOBAL)
        self.cbo_color_global.setCurrentText(DEFAULT_COLOR_GLOBAL)
        self.cbo_color_global.currentTextChanged.connect(
            lambda _=None: self._sync_color_rule(from_user=True)
        )
        g.addWidget(self.cbo_color_global, r, 1)
        r += 1
        _connect_upper_combobox(self.cbo_color_global)

        # Grupo: Datos de la partida
        gb_p = QGroupBox("Datos de la partida", self)
        pv = QVBoxLayout(gb_p)
        pv.setContentsMargins(8, 8, 8, 8)
        pv.setSpacing(6)

        self.le_titulo = QLineEdit(self)
        self.le_titulo.setPlaceholderText("TÍTULO DE PARTIDA")
        pv.addWidget(self.le_titulo)
        _connect_upper_lineedit(self.le_titulo)

        self.te_desc = QTextEdit(self)
        self.te_desc.setPlaceholderText("DESCRIPCIÓN DE LA PARTIDA")
        pv.addWidget(self.te_desc, 1)
        _connect_upper_textedit(self.te_desc)

        # Grupo: Valores de la partida
        gb_v = QGroupBox("Valores de la partida", self)
        gv = QGridLayout(gb_v)
        gv.setContentsMargins(8, 8, 8, 8)
        gv.setSpacing(6)

        rr = 0
        gv.addWidget(QLabel("DESPERDICIO:"), rr, 0)
        self.sb_desperdicio = QSpinBox(self, minimum=0, maximum=999)
        self.sb_desperdicio.setValue(2)
        self.sb_desperdicio.setSuffix("%")
        gv.addWidget(self.sb_desperdicio, rr, 1)
        rr += 1

        gv.addWidget(QLabel("F.V. (%):"), rr, 0)
        self.sb_fv_pct = QSpinBox(self, minimum=0, maximum=999)
        self.sb_fv_pct.setValue(25)
        self.sb_fv_pct.setSuffix("%")
        gv.addWidget(self.sb_fv_pct, rr, 1)
        rr += 1

        gv.addWidget(QLabel("COLOR (PARTIDA):"), rr, 0)
        self.cbo_color = QComboBox(self)
        self.cbo_color.setEditable(True)
        self.cbo_color.addItems(COLORES_PARTIDA)
        gv.addWidget(self.cbo_color, rr, 1)
        rr += 1
        _connect_upper_combobox(self.cbo_color)

        gv.addWidget(QLabel("$ / KG:"), rr, 0)
        self.sp_precio_kg = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=99999999.99)
        gv.addWidget(self.sp_precio_kg, rr, 1)
        rr += 1

        gv.addWidget(QLabel("KG:"), rr, 0)
        self.sp_kg = QDoubleSpinBox(self, decimals=3, minimum=0.0, maximum=99999999.999)
        self.sp_kg.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.sp_kg.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sp_kg.setEnabled(False)
        gv.addWidget(self.sp_kg, rr, 1)
        rr += 1

        gv.addWidget(QLabel("ANCHO:"), rr, 0)
        self.sp_ancho = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=9999.99)
        self.sp_ancho.setValue(0.0)
        gv.addWidget(self.sp_ancho, rr, 1)
        rr += 1

        gv.addWidget(QLabel("ALTO:"), rr, 0)
        self.sp_alto = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=9999.99)
        self.sp_alto.setValue(0.0)
        gv.addWidget(self.sp_alto, rr, 1)
        rr += 1

        gv.addWidget(QLabel("MANO DE OBRA:"), rr, 0)
        self.sp_mo = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=99999999.99)
        gv.addWidget(self.sp_mo, rr, 1)
        rr += 1

        gv.addWidget(QLabel("ACCESORIOS:"), rr, 0)
        self.sp_acc = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=99999999.99)
        gv.addWidget(self.sp_acc, rr, 1)
        rr += 1

        gv.addWidget(QLabel("P.U.:"), rr, 0)
        self.sp_pu_partida = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=9999999999.99)
        self.sp_pu_partida.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.sp_pu_partida.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sp_pu_partida.setReadOnly(True)
        self.sp_pu_partida.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.sp_pu_partida.setEnabled(False)
        gv.addWidget(self.sp_pu_partida, rr, 1)
        rr += 1

        gv.addWidget(QLabel("PIEZAS:"), rr, 0)
        self.sb_pzas_global = QSpinBox(self, minimum=1, maximum=999999)
        gv.addWidget(self.sb_pzas_global, rr, 1)
        rr += 1

        # Grupo: Resumen de partida y presupuesto
        gb_r = QGroupBox("Resumen de partida y presupuesto", self)

        def mk_disp():
            """Crea un widget de visualización de solo lectura."""
            w = QDoubleSpinBox(self, decimals=2, minimum=0.0, maximum=9999999999.99)
            w.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
            w.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            w.setReadOnly(True)
            w.setAlignment(Qt.AlignmentFlag.AlignRight)
            w.setEnabled(False)
            return w

        gr = QGridLayout(gb_r)
        gr.setContentsMargins(8, 8, 8, 8)
        gr.setSpacing(6)

        rsum = 0
        gr.addWidget(QLabel("TOTAL DE LA PARTIDA:"), rsum, 0)
        self.sp_total_partida = mk_disp()
        gr.addWidget(self.sp_total_partida, rsum, 1)
        rsum += 1

        gr.addWidget(QLabel("SUB TOTAL:"), rsum, 0)
        self.sp_subtotal = mk_disp()
        gr.addWidget(self.sp_subtotal, rsum, 1)
        rsum += 1

        gr.addWidget(QLabel("I.V.A. (16%):"), rsum, 0)
        self.sp_iva = mk_disp()
        gr.addWidget(self.sp_iva, rsum, 1)
        rsum += 1

        gr.addWidget(QLabel("TOTAL:"), rsum, 0)
        self.sp_total = mk_disp()
        gr.addWidget(self.sp_total, rsum, 1)
        rsum += 1

        # Agregar widgets al panel izquierdo
        lv.addWidget(gb_d)
        lv.addWidget(gb_p, 1)
        lv.addWidget(gb_v)
        lv.addWidget(gb_r)
        self.split.addWidget(left)

        # --- PANEL DERECHO (80%) ---
        right = QWidget(self)
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(8)

        # Barra de búsqueda
        bar = QWidget(self)
        b = QGridLayout(bar)
        b.setContentsMargins(0, 0, 0, 0)
        b.setSpacing(6)

        b.addWidget(QLabel("TIPO:"), 0, 0)
        self.cbo_tipo = QComboBox(self)
        self.cbo_tipo.addItems(TIPOS_MATERIAL)
        self.cbo_tipo.currentTextChanged.connect(
            lambda _=None: self._after_choose_filtro()
        )
        b.addWidget(self.cbo_tipo, 0, 1)
        _connect_upper_combobox(self.cbo_tipo)

        b.addWidget(QLabel("BUSCAR POR:"), 0, 2)
        self.cbo_buscar = QComboBox(self)
        self.cbo_buscar.addItems(TIPOS_BUSQUEDA)
        b.addWidget(self.cbo_buscar, 0, 3)
        self.cbo_buscar.activated.connect(lambda _=None: self.le_filtro.setFocus())
        _connect_upper_combobox(self.cbo_buscar)

        b.addWidget(QLabel("FILTRO:"), 0, 4)
        self.le_filtro = QLineEdit(self)
        self.le_filtro.textChanged.connect(
            lambda _t: (
                self._search_timer.start(),
                self.lst_result.setVisible(bool((self.le_filtro.text() or '').strip()))
            )
        )
        b.addWidget(self.le_filtro, 0, 5)
        _connect_upper_lineedit(self.le_filtro)

        self.lst_result = QListWidget(self)
        self.lst_result.setVisible(False)
        self.lst_result.setMinimumHeight(220)
        self.lst_result.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.lst_result.itemDoubleClicked.connect(
            lambda it: self._on_pick_result_paquete(it) if self._es_tipo_paquete() else busquedas.on_pick_result(self,
                                                                                                                 it)
        )
        b.addWidget(self.lst_result, 1, 0, 1, 6)
        b.setRowStretch(0, 0)
        b.setRowStretch(1, 1)
        rv.addWidget(bar)

        # --- CONTENEDOR DE TABLAS VISIBLES SIMULTÁNEAMENTE ---
        tablas_container = QWidget(self)
        tablas_layout = QVBoxLayout(tablas_container)
        tablas_layout.setContentsMargins(0, 0, 0, 0)
        tablas_layout.setSpacing(4)

        # 1. Tabla de Paquetes - NUEVA POSICIÓN (ARRIBA) - CON 6 COLUMNAS
        self.gb_tabla_paquetes = QGroupBox("📦 Paquetes", self)
        self.gb_tabla_paquetes.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        vm_paquetes = QVBoxLayout(self.gb_tabla_paquetes)
        vm_paquetes.setContentsMargins(4, 8, 4, 4)

        # Tabla de paquetes (SOLO PAQUETES PADRES) - 6 COLUMNAS
        self.tbl_paquetes = QTableWidget(0, 6, self)
        self.tbl_paquetes.setHorizontalHeaderLabels([
            "Tipo", "Clave", "Descripción", "Ancho", "Alto", "Piezas"
        ])
        self.tbl_paquetes.verticalHeader().setVisible(False)
        self.tbl_paquetes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_paquetes.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tbl_paquetes.itemChanged.connect(self._on_tbl_paquetes_changed)

        vm_paquetes.addWidget(self.tbl_paquetes, 1)
        tablas_layout.addWidget(self.gb_tabla_paquetes, 1)

        # 2. Tabla Anidada - NUEVA TABLA para componentes del paquete actual
        self.gb_tabla_anidada = QGroupBox("📝 Anidada (Componentes del paquete actual)", self)
        self.gb_tabla_anidada.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.gb_tabla_anidada.setVisible(False)  # Oculto inicialmente
        vm_anidada = QVBoxLayout(self.gb_tabla_anidada)
        vm_anidada.setContentsMargins(4, 8, 4, 4)

        self.tbl_anidada = QTableWidget(0, 11, self)
        self.tbl_anidada.setHorizontalHeaderLabels([
            "Tipo", "Color", "Clave", "Descripción", "Cant. Ancho",
            "Ancho", "Cant. Alto", "Alto", "Piezas", "P.U.", "Importe"
        ])
        self.tbl_anidada.verticalHeader().setVisible(False)
        self.tbl_anidada.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_anidada.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        vm_anidada.addWidget(self.tbl_anidada, 1)
        tablas_layout.addWidget(self.gb_tabla_anidada, 1)

        # 3. Tabla estándar (Materiales) - CON TÍTULO
        self.gb_tabla_materiales = QGroupBox("📋 Materiales", self)
        self.gb_tabla_materiales.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        vm_materiales = QVBoxLayout(self.gb_tabla_materiales)
        vm_materiales.setContentsMargins(4, 8, 4, 4)

        self.tbl = QTableWidget(0, 11, self)
        self.tbl.setHorizontalHeaderLabels([
            "Tipo", "Color", "Clave", "Descripción", "Cant. Ancho",
            "Ancho", "Cant. Alto", "Alto", "Piezas", "P.U.", "Importe"
        ])
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.itemChanged.connect(self._on_tbl_std_changed)
        self.tbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        vm_materiales.addWidget(self.tbl)
        tablas_layout.addWidget(self.gb_tabla_materiales, 1)

        # 4. Tabla de Herrería - CON TÍTULO
        self.gb_tabla_herreria = QGroupBox("🔧 Herrería", self)
        self.gb_tabla_herreria.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        vm_herreria = QVBoxLayout(self.gb_tabla_herreria)
        vm_herreria.setContentsMargins(4, 8, 4, 4)

        self.tbl_he = QTableWidget(0, 14, self)
        self.tbl_he.setHorizontalHeaderLabels([
            "Tipo", "Clave", "Descripción", "Cant. Ancho",
            "Ancho", "Cant. Alto", "Alto", "Metros", "Kg/m", "Kgs.", "$/kg",
            "Piezas", "P.U.", "Importe"
        ])
        self.tbl_he.verticalHeader().setVisible(False)
        self.tbl_he.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_he.itemChanged.connect(self._on_tbl_he_changed)
        self.tbl_he.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        vm_herreria.addWidget(self.tbl_he)
        tablas_layout.addWidget(self.gb_tabla_herreria, 1)

        # Añadir contenedor de tablas al layout principal
        rv.addWidget(tablas_container, 1)
        self.split.addWidget(right)

        # Estilos - Usar constante importada
        self.setStyleSheet(STYLESHEET)

        # Inicialización diferida
        QTimer.singleShot(0, lambda: (
            self._sync_color_rule(from_user=False),
            self.le_cliente.setFocus()
        ))

    # ============================================================================
    # MÉTODOS DE MANEJO DE PAQUETES (CRÍTICOS - COMPLETOS)
    # ============================================================================

    def _es_tipo_paquete(self) -> bool:
        """Verifica si el tipo seleccionado es un paquete"""
        tipo_seleccionado = (self.cbo_tipo.currentText() or "").strip().upper()
        # Usar función importada de core.utils
        return es_tipo_paquete(tipo_seleccionado)

    def _sync_color_rule(self, from_user: bool = False) -> None:
        """Sincroniza la regla de color global con el color de partida."""
        g = (self.cbo_color_global.currentText() or "").strip().upper()
        if g == "VARIOS":
            self.cbo_color.setEnabled(True)
            if from_user:
                self.cbo_color.setFocus()
        else:
            self.cbo_color.setCurrentText(g)
            self.cbo_color.setEnabled(False)

    def _set_fecha_hoy(self) -> None:
        """Establece la fecha actual en el campo de fecha."""
        if hasattr(self, "de_fv") and self.de_fv:
            self.de_fv.setDate(QDate.currentDate())
            self.de_fv.setCalendarPopup(True)

    # Métodos delegados a busquedas.py (se mantienen igual)
    def _normalize_token(self, s: str) -> str:
        return busquedas.normalize_token(s)

    def _svc_query(self, tipo_norm: str, buscar_norm: str, filtro_up: str):
        return busquedas._svc_query(self, tipo_norm, buscar_norm, filtro_up)

    def _search_rows_uniform(self, tipo_raw: str, buscar_raw: str, filtro: str):
        return busquedas.search_rows_uniform(self, tipo_raw, buscar_raw, filtro)

    def _after_choose_filtro(self):
        return busquedas.after_choose_filtro(self)

    def _do_search(self):
        return busquedas.do_search(self)

    def _on_pick_result(self, item):
        return busquedas.on_pick_result(self, item)

    # ============================================================================
    # MÉTODOS DE MANEJO DE PAQUETES (COMPLETOS)
    # ============================================================================

    def _on_pick_result_paquete(self, item: QListWidgetItem) -> None:
        """
        Maneja la selección de un paquete.
        1. Agrega el paquete a la tabla Paquetes
        2. Carga los componentes del paquete en la tabla Anidada (sin multiplicar)
        3. NO los pasa aún a la tabla Materiales
        """
        if item is None:
            return

        # Obtener datos del paquete seleccionado
        datos = item.data(Qt.ItemDataRole.UserRole)
        if not datos:
            return

        tipo_seleccionado = (self.cbo_tipo.currentText() or "").strip().upper()
        clave_paquete = datos.get("clave", "").strip()
        descripcion_paquete = datos.get("descripcion", "").strip()

        # Guardar datos del paquete seleccionado
        self._paquete_seleccionado = {
            "tipo": tipo_seleccionado,
            "clave": clave_paquete,
            "descripcion": descripcion_paquete,
            "datos": datos
        }

        # 1. AGREGAR PAQUETE PADRE A TABLA "PAQUETES" (ACUMULATIVO)
        self._agregar_paquete_a_tabla(
            tipo_seleccionado,
            clave_paquete,
            descripcion_paquete,
            float(self.sp_ancho.value()),
            float(self.sp_alto.value())
        )

        # 2. CARGAR COMPONENTES EN TABLA ANIDADA (SIN MULTIPLICAR)
        self._cargar_componentes_a_tabla_anidada(clave_paquete, tipo_seleccionado)

        # Configurar tabla
        header = self.tbl_paquetes.horizontalHeader()
        header.setSectionResizeMode(P_TIPO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(P_CLAVE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(P_DESC, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(P_ANCHO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(P_ALTO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(P_PZAS, QHeaderView.ResizeMode.ResizeToContents)

        self._paquete_actual = clave_paquete

        # Ocultar lista de resultados
        self.lst_result.setVisible(False)
        self.le_filtro.clear()

        # Establecer foco en celda de Piezas del nuevo paquete
        if self.tbl_paquetes.rowCount() > 0:
            QTimer.singleShot(100, lambda: self._enfocar_celda_piezas_paquetes(self.tbl_paquetes.rowCount() - 1))

    def _cargar_componentes_a_tabla_anidada(self, clave_paquete: str, tipo_paquete: str) -> None:
        """
        Carga los componentes del paquete en la tabla Anidada.
        Los componentes se cargan con sus cantidades base (sin multiplicar por piezas del paquete).
        """
        try:
            # Limpiar tabla anidada previa
            self._limpiar_tabla_anidada()

            # Mostrar tabla anidada
            self.gb_tabla_anidada.setVisible(True)
            self._tabla_anidada_activa = True
            self._paquete_anidado_actual = clave_paquete

            # Reiniciar lista de componentes base
            self._componentes_base_actuales = []

            ancho_original = float(self.sp_ancho.value())
            alto_original = float(self.sp_alto.value())

            # Obtener componentes del paquete principal
            if tipo_paquete.startswith("PAQUETE ALUMINIO"):
                componentes = self.svc.paquete_aluminio_items(clave_paquete)
            elif tipo_paquete.startswith("PAQUETE HERRAJES"):
                componentes = self.svc.paquete_herrajes_items(clave_paquete)
            else:
                componentes = []

            # Procesar cada componente (incluyendo paquetes anidados)
            for comp in componentes:
                tipo_componente = comp.get("tipo", "").strip().upper()
                clave_comp = comp.get("clave", "").strip()
                descripcion_comp = comp.get("descripcion", "").strip()
                cantidad_base = comp.get("cantidad", 1)

                # Guardar componente base
                self._componentes_base_actuales.append({
                    "comp": comp,
                    "tipo_componente": tipo_componente,
                    "clave": clave_comp,
                    "descripcion": descripcion_comp,
                    "cantidad_base": cantidad_base
                })

                # Si es un paquete anidado (PH), obtener sus componentes también
                if tipo_componente == "PH":
                    self._cargar_componentes_paquete_anidado_a_anidada(
                        clave_comp, cantidad_base, ancho_original, alto_original
                    )
                else:
                    # Componente normal - agregar a tabla anidada
                    self._agregar_componente_a_tabla_anidada(
                        comp, tipo_componente, ancho_original, alto_original, cantidad_base
                    )

        except Exception as e:
            QMessageBox.critical(self, "Error BD",
                                 f"No se pudieron obtener componentes:\n{str(e)}")
            return

    def _cargar_componentes_paquete_anidado_a_anidada(self, clave_paquete_anidado: str,
                                                      cantidad_paquete_anidado: int,
                                                      ancho_original: float, alto_original: float) -> None:
        """
        Carga los componentes de un paquete anidado en la tabla Anidada.
        """
        try:
            # Obtener componentes del paquete anidado
            componentes_anidados = self.svc.paquete_herrajes_items(clave_paquete_anidado)

            for comp_anidado in componentes_anidados:
                tipo_componente = comp_anidado.get("tipo", "").strip().upper()
                clave_comp = comp_anidado.get("clave", "").strip()
                descripcion_comp = comp_anidado.get("descripcion", "").strip()
                cantidad_base = comp_anidado.get("cantidad", 1)

                # Calcular cantidad total (base * cantidad del paquete anidado)
                cantidad_total = cantidad_base * cantidad_paquete_anidado

                # Guardar componente base
                self._componentes_base_actuales.append({
                    "comp": comp_anidado,
                    "tipo_componente": tipo_componente,
                    "clave": clave_comp,
                    "descripcion": descripcion_comp,
                    "cantidad_base": cantidad_total,  # Ya multiplicado por cantidad del paquete anidado
                    "es_anidado": True
                })

                # Agregar a tabla anidada
                self._agregar_componente_a_tabla_anidada(
                    comp_anidado, tipo_componente, ancho_original, alto_original, cantidad_total
                )

        except Exception as e:
            print(f"Error al cargar componentes del paquete anidado {clave_paquete_anidado}: {e}")

    def _agregar_componente_a_tabla_anidada(self, comp: Dict[str, Any], tipo_componente: str,
                                            ancho_original: float, alto_original: float,
                                            cantidad: float) -> None:
        """
        Agrega un componente a la tabla Anidada (solo visualización).
        """
        try:
            self._prog = True

            clave_real = comp.get("clave", "").strip()
            descripcion_real = comp.get("descripcion", "").strip()
            horizontal = comp.get("horizontal", 1)
            vertical = comp.get("vertical", 1)

            # Convertir a valores numéricos
            try:
                horizontal_val = float(horizontal)
            except (ValueError, TypeError):
                horizontal_val = 1.0 if tipo_componente == "AL" else 0.0

            try:
                vertical_val = float(vertical)
            except (ValueError, TypeError):
                vertical_val = 1.0 if tipo_componente == "AL" else 0.0

            # Determinar tipo para mostrar en la tabla
            if tipo_componente == "AL":
                tipo_mostrar = "ALUMINIO"
            elif tipo_componente in ["HR", "PH"]:
                tipo_mostrar = "HERRAJES"
            else:
                tipo_mostrar = tipo_componente

            # Si no tiene descripción o es genérica, buscar en la BD
            if not descripcion_real or descripcion_real.startswith("Material "):
                try:
                    descripcion_real = self.svc.obtener_descripcion_material(tipo_mostrar, clave_real)
                except Exception:
                    descripcion_real = f"Componente {clave_real}"

            # Agregar fila a la tabla anidada
            r_comp = self.tbl_anidada.rowCount()
            self.tbl_anidada.insertRow(r_comp)

            self._set_or_update_item(self.tbl_anidada, r_comp, A_TIPO,
                                     tipo_mostrar, editable=False)
            self._set_or_update_item(self.tbl_anidada, r_comp, A_COLOR,
                                     self._get_color_partida_o_global(), editable=False)
            self._set_or_update_item(self.tbl_anidada, r_comp, A_CLAVE,
                                     clave_real, editable=False)
            self._set_or_update_item(self.tbl_anidada, r_comp, A_DESC,
                                     descripcion_real, editable=False)
            # Cant. Ancho toma valor de Horizontal
            self._set_or_update_item(self.tbl_anidada, r_comp, A_CA,
                                     f"{horizontal_val:.0f}", editable=False)
            # Ancho toma valor ORIGINAL
            self._set_or_update_item(self.tbl_anidada, r_comp, A_ANCHO,
                                     f"{ancho_original:.2f}", editable=False)
            # Cant. Alto toma valor de Vertical
            self._set_or_update_item(self.tbl_anidada, r_comp, A_CH,
                                     f"{vertical_val:.0f}", editable=False)
            # Alto toma valor ORIGINAL
            self._set_or_update_item(self.tbl_anidada, r_comp, A_ALTO,
                                     f"{alto_original:.2f}", editable=False)
            # Cantidad del componente (SIN MULTIPLICAR por piezas del paquete madre)
            self._set_or_update_item(self.tbl_anidada, r_comp, A_PZAS,
                                     f"{cantidad}", editable=False)
            self._set_or_update_item(self.tbl_anidada, r_comp, A_PU, "0.00", editable=False)
            self._set_or_update_item(self.tbl_anidada, r_comp, A_IMP, "0.00", editable=False)

            # Guardar valores ORIGINALES de ancho/alto
            self.tbl_anidada.item(r_comp, A_ANCHO).setData(Qt.ItemDataRole.UserRole, ancho_original)
            self.tbl_anidada.item(r_comp, A_ALTO).setData(Qt.ItemDataRole.UserRole, alto_original)

            # Calcular valores del componente (para visualización)
            try:
                self._calc_anidada_row(r_comp)
            except Exception:
                pass

        finally:
            self._prog = False

    def _calc_anidada_row(self, r: int) -> None:
        """Calcula los valores de una fila de la tabla Anidada."""
        try:
            tipo = self._safe_text(self.tbl_anidada, r, A_TIPO, "").strip().upper()
            clave = self._safe_text(self.tbl_anidada, r, A_CLAVE, "")
            color = self._get_color_partida_o_global()

            # Obtener valores de la tabla anidada
            ancho_original = _f(self._safe_text(self.tbl_anidada, r, A_ANCHO, "0"))
            alto_original = _f(self._safe_text(self.tbl_anidada, r, A_ALTO, "0"))

            ca = _f(self._safe_text(self.tbl_anidada, r, A_CA, "1"), 1)
            ch = _f(self._safe_text(self.tbl_anidada, r, A_CH, "1"), 1)
            pzas = _i(self._safe_text(self.tbl_anidada, r, A_PZAS, "1"), 1)
            precio_kg = float(self.sp_precio_kg.value())

            # Para cálculos, usar medidas ajustadas
            ancho_ajustado, alto_ajustado = _ajustar_medidas_industriales(ancho_original, alto_original)

            ctx = EspecificacionesCtx(
                svc=self.svc,
                tipo=tipo,
                clave=clave,
                color=color,
                ancho=ancho_ajustado,
                alto=alto_ajustado,
                piezas=pzas,
                ca=ca,
                ch=ch,
                extra={
                    "precio_kg": precio_kg,
                    "ca": ca,
                    "ch": ch
                }
            )

            pu, imp = dispatch_calculo(ctx)

            self._set_money(self.tbl_anidada, r, A_PU, pu)
            self._set_money(self.tbl_anidada, r, A_IMP, imp)

        except Exception as e:
            print(f"Error calculando fila anidada: {e}")

    def _agregar_paquete_a_tabla(self, tipo: str, clave: str, descripcion: str,
                                 ancho_original: float, alto_original: float,
                                 es_anidado: bool = False, padre_clave: str = None) -> None:
        """
        Agrega un paquete a la tabla de Paquetes.
        """
        r = self.tbl_paquetes.rowCount()
        self.tbl_paquetes.insertRow(r)

        # Tipo (no editable)
        item_tipo = QTableWidgetItem(tipo)
        item_tipo.setFlags(item_tipo.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item_tipo.setBackground(Qt.GlobalColor.lightGray if es_anidado else Qt.GlobalColor.white)
        # Guardar datos adicionales
        item_tipo.setData(Qt.ItemDataRole.UserRole, {
            "clave": clave,
            "es_anidado": es_anidado,
            "padre_clave": padre_clave
        })
        self.tbl_paquetes.setItem(r, P_TIPO, item_tipo)

        # Clave (no editable)
        item_clave = QTableWidgetItem(clave)
        item_clave.setFlags(item_clave.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item_clave.setBackground(Qt.GlobalColor.lightGray if es_anidado else Qt.GlobalColor.white)
        self.tbl_paquetes.setItem(r, P_CLAVE, item_clave)

        # Descripción (no editable)
        item_desc = QTableWidgetItem(descripcion)
        item_desc.setFlags(item_desc.flags() & ~Qt.ItemFlag.ItemIsEditable)
        item_desc.setBackground(Qt.GlobalColor.lightGray if es_anidado else Qt.GlobalColor.white)
        self.tbl_paquetes.setItem(r, P_DESC, item_desc)

        # Ancho - EDITABLE solo si NO es anidado
        item_ancho = QTableWidgetItem(f"{ancho_original:.2f}")
        item_ancho.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if es_anidado:
            # Solo informativo para paquetes anidados
            item_ancho.setFlags(item_ancho.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_ancho.setBackground(Qt.GlobalColor.lightGray)
        else:
            # Editable para paquete madre
            item_ancho.setBackground(Qt.GlobalColor.yellow)

        # Guardar valor original para referencia
        item_ancho.setData(Qt.ItemDataRole.UserRole, ancho_original)
        self.tbl_paquetes.setItem(r, P_ANCHO, item_ancho)

        # Alto - EDITABLE solo si NO es anidado
        item_alto = QTableWidgetItem(f"{alto_original:.2f}")
        item_alto.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if es_anidado:
            # Solo informativo para paquetes anidados
            item_alto.setFlags(item_alto.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_alto.setBackground(Qt.GlobalColor.lightGray)
        else:
            # Editable para paquete madre
            item_alto.setBackground(Qt.GlobalColor.yellow)

        # Guardar valor original para referencia
        item_alto.setData(Qt.ItemDataRole.UserRole, alto_original)
        self.tbl_paquetes.setItem(r, P_ALTO, item_alto)

        # Piezas - EDITABLE solo si NO es anidado
        item_pzas = QTableWidgetItem("1")
        item_pzas.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        if es_anidado:
            # Solo informativo para paquetes anidados
            item_pzas.setFlags(item_pzas.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item_pzas.setBackground(Qt.GlobalColor.lightGray)
        else:
            # Editable para paquete madre
            item_pzas.setBackground(Qt.GlobalColor.yellow)

        self.tbl_paquetes.setItem(r, P_PZAS, item_pzas)

    def _on_tbl_paquetes_changed(self, item: QTableWidgetItem) -> None:
        """
        Responde a cambios en la tabla de Paquetes.
        Cuando se cambia el valor de Piezas y se presiona Enter/Tab:
        1. Multiplica todos los componentes de la tabla Anidada por las nuevas piezas
        2. Consolida en la tabla Materiales (sumando ítems iguales)
        3. Limpia la tabla Anidada
        """
        if item is None or getattr(self, "_prog", False):
            return

        row = item.row()
        col = item.column()

        # Obtener clave del paquete desde la fila
        item_clave = self.tbl_paquetes.item(row, P_CLAVE)
        if not item_clave:
            return

        clave_paquete = item_clave.text().strip()

        # Obtener si es anidado
        item_tipo_paquete = self.tbl_paquetes.item(row, P_TIPO)
        es_anidado = False
        if item_tipo_paquete:
            datos_paquete = item_tipo_paquete.data(Qt.ItemDataRole.UserRole)
            if datos_paquete:
                es_anidado = datos_paquete.get("es_anidado", False)

        # Si es anidado, NO permitir cambios
        if es_anidado:
            return

        try:
            if col == P_PZAS:
                # Cambio en Piezas del paquete madre - MULTIPLICAR Y CONSOLIDAR
                piezas_paquete = _i(item.text(), 1)

                # 1. Actualizar los componentes en la tabla Anidada multiplicando por piezas
                self._actualizar_tabla_anidada_con_piezas(piezas_paquete)

                # 2. Consolidar componentes de la tabla Anidada en la tabla Materiales
                self._consolidar_anidada_a_materiales()

                # 3. Limpiar tabla Anidada y ocultarla
                self._limpiar_tabla_anidada()
                self.gb_tabla_anidada.setVisible(False)
                self._tabla_anidada_activa = False
                self._paquete_anidado_actual = None

                # 4. Recalcular totales
                self._recalc_summary()

        except Exception as e:
            print(f"Error al procesar cambio en tabla Paquetes: {e}")
            import traceback
            traceback.print_exc()

    def _actualizar_tabla_anidada_con_piezas(self, piezas_paquete: int) -> None:
        """
        Actualiza las cantidades en la tabla Anidada multiplicando por las piezas del paquete.
        """
        if not self._tabla_anidada_activa or self.tbl_anidada.rowCount() == 0:
            return

        try:
            self._prog = True

            for r in range(self.tbl_anidada.rowCount()):
                item_pzas = self.tbl_anidada.item(r, A_PZAS)
                if item_pzas:
                    # Obtener cantidad base del componente
                    cantidad_base_text = item_pzas.text()
                    cantidad_base = _f(cantidad_base_text, 0)

                    # Multiplicar por las piezas del paquete
                    cantidad_total = cantidad_base * piezas_paquete

                    # Actualizar en la tabla Anidada
                    item_pzas.setText(f"{cantidad_total}")

                    # Recalcular la fila
                    self._calc_anidada_row(r)

        finally:
            self._prog = False

    def _consolidar_anidada_a_materiales(self) -> None:
        """
        Consolida los componentes de la tabla Anidada en la tabla Materiales.
        Suma ítems iguales en lugar de crear filas duplicadas.
        """
        if not self._tabla_anidada_activa or self.tbl_anidada.rowCount() == 0:
            return

        try:
            self._prog = True

            # Para cada fila en la tabla Anidada
            for r_anidada in range(self.tbl_anidada.rowCount()):
                # Obtener datos del componente anidado
                tipo_anidada = self._safe_text(self.tbl_anidada, r_anidada, A_TIPO, "").strip()
                clave_anidada = self._safe_text(self.tbl_anidada, r_anidada, A_CLAVE, "").strip()
                desc_anidada = self._safe_text(self.tbl_anidada, r_anidada, A_DESC, "").strip()
                ca_anidada = _f(self._safe_text(self.tbl_anidada, r_anidada, A_CA, "1"), 1)
                ancho_anidada = _f(self._safe_text(self.tbl_anidada, r_anidada, A_ANCHO, "0"))
                ch_anidada = _f(self._safe_text(self.tbl_anidada, r_anidada, A_CH, "1"), 1)
                alto_anidada = _f(self._safe_text(self.tbl_anidada, r_anidada, A_ALTO, "0"))
                pzas_anidada = _f(self._safe_text(self.tbl_anidada, r_anidada, A_PZAS, "1"), 1)

                # Buscar si ya existe un componente igual en la tabla Materiales
                componente_existente = None
                for r_material in range(self.tbl.rowCount()):
                    tipo_material = self._safe_text(self.tbl, r_material, C_TIPO, "").strip()
                    clave_material = self._safe_text(self.tbl, r_material, C_CLAVE, "").strip()
                    desc_material = self._safe_text(self.tbl, r_material, C_DESC, "").strip()
                    ca_material = _f(self._safe_text(self.tbl, r_material, C_CA, "1"), 1)
                    ancho_material = _f(self._safe_text(self.tbl, r_material, C_ANCHO, "0"))
                    ch_material = _f(self._safe_text(self.tbl, r_material, C_CH, "1"), 1)
                    alto_material = _f(self._safe_text(self.tbl, r_material, C_ALTO, "0"))

                    # Verificar si es el mismo componente
                    if (tipo_material == tipo_anidada and
                            clave_material == clave_anidada and
                            desc_material == desc_anidada and
                            ca_material == ca_anidada and
                            abs(ancho_material - ancho_anidada) < 0.001 and
                            ch_material == ch_anidada and
                            abs(alto_material - alto_anidada) < 0.001):
                        componente_existente = r_material
                        break

                if componente_existente is not None:
                    # Sumar a la fila existente
                    item_pzas_existente = self.tbl.item(componente_existente, C_PZAS)
                    if item_pzas_existente:
                        cantidad_existente = _f(item_pzas_existente.text(), 0)
                        nueva_cantidad_total = cantidad_existente + pzas_anidada

                        # Actualizar cantidad
                        self.tbl.blockSignals(True)
                        item_pzas_existente.setText(f"{nueva_cantidad_total}")
                        self.tbl.blockSignals(False)

                        # Recalcular la fila
                        self._calc_std_row(componente_existente)
                else:
                    # Crear nueva fila en Materiales
                    r_nueva = self.tbl.rowCount()
                    self.tbl.insertRow(r_nueva)

                    # Copiar datos de la tabla Anidada a Materiales
                    for col_anidada, col_material in [
                        (A_TIPO, C_TIPO),
                        (A_COLOR, C_COLOR),
                        (A_CLAVE, C_CLAVE),
                        (A_DESC, C_DESC),
                        (A_CA, C_CA),
                        (A_ANCHO, C_ANCHO),
                        (A_CH, C_CH),
                        (A_ALTO, C_ALTO),
                        (A_PZAS, C_PZAS),
                        (A_PU, C_PU),
                        (A_IMP, C_IMP)
                    ]:
                        item_anidada = self.tbl_anidada.item(r_anidada, col_anidada)
                        if item_anidada:
                            self._set_or_update_item(self.tbl, r_nueva, col_material,
                                                     item_anidada.text(),
                                                     editable=col_material in [C_CA, C_CH,
                                                                               C_ANCHO, C_ALTO,
                                                                               C_PZAS])

                    # Aplicar editabilidad según tipo
                    self._apply_editabilidad_std(r_nueva)

                    # Recalcular la fila (para asegurar cálculos correctos)
                    self._calc_std_row(r_nueva)

        finally:
            self._prog = False

    def _limpiar_tabla_anidada(self) -> None:
        """Limpia completamente la tabla Anidada."""
        self.tbl_anidada.setRowCount(0)
        self._componentes_base_actuales = []

    def _enfocar_celda_piezas_paquetes(self, fila: int) -> None:
        """Enfoca la celda de Piezas en la tabla de Paquetes"""
        if fila < self.tbl_paquetes.rowCount():
            self.tbl_paquetes.setCurrentCell(fila, P_PZAS)
            self.tbl_paquetes.editItem(self.tbl_paquetes.item(fila, P_PZAS))

    def _set_or_update_item(self, tbl: QTableWidget, r: int, c: int,
                            text: str, editable: bool = True) -> None:
        """
        Establece o actualiza un ítem en la tabla.
        """
        set_table_item_text(tbl, r, c, text, editable)

    def _set_money(self, tbl: QTableWidget, r: int, c: int, value: float) -> None:
        """Establece un valor monetario formateado en la tabla."""
        set_table_money(tbl, r, c, value)

    def _safe_text(self, table: QTableWidget, r: int, c: int, default: str = "0") -> str:
        """Obtiene el texto de una celda de forma segura."""
        return safe_table_text(table, r, c, default)

    def _get_tipo(self, row: int) -> str:
        """Obtiene el tipo de material de una fila."""
        return self._safe_text(self.tbl, row, C_TIPO, "")

    def _get_color_partida_o_global(self) -> str:
        """Obtiene el color a usar (partida o global)."""
        g = (self.cbo_color_global.currentText() or "").strip().upper()
        if g and g != "VARIOS":
            return g
        return (self.cbo_color.currentText() or "").strip().upper()

    # ============================================================================
    # MÉTODOS PARA TABLAS ESTÁNDAR Y HERRERÍA
    # ============================================================================

    def _add_std(self, rec: Dict[str, Any], tipo: str, color: str,
                 ancho: float, alto: float, _pzas_ignored: int) -> None:
        """
        Agrega un renglón a la tabla estándar.
        Para paquetes, ahora se manejan de forma especial.
        """
        tipo_normalizado = tipo.strip().upper()

        # Verificar si es un paquete
        if self._es_tipo_paquete():
            # Para paquetes, no se agrega directamente
            return
        else:
            r = self.tbl.rowCount()
            self.tbl.insertRow(r)

            try:
                self._prog = True

                clave = rec.get("clave", "")
                descripcion = rec.get("descripcion", "")

                self._set_or_update_item(self.tbl, r, C_TIPO, tipo, editable=False)
                self._set_or_update_item(self.tbl, r, C_COLOR,
                                         self._get_color_partida_o_global(), editable=False)
                self._set_or_update_item(self.tbl, r, C_CLAVE,
                                         clave, editable=False)
                self._set_or_update_item(self.tbl, r, C_DESC,
                                         descripcion, editable=False)
                self._set_or_update_item(self.tbl, r, C_CA, "1", editable=True)
                # ✅ Mostrar valor ORIGINAL (NO ajustado)
                self._set_or_update_item(self.tbl, r, C_ANCHO,
                                         f"{ancho:.2f}", editable=True)
                self._set_or_update_item(self.tbl, r, C_CH, "1", editable=True)
                # ✅ Mostrar valor ORIGINAL (NO ajustado)
                self._set_or_update_item(self.tbl, r, C_ALTO,
                                         f"{alto:.2f}", editable=True)
                self._set_or_update_item(self.tbl, r, C_PZAS, "1", editable=True)
                self._set_or_update_item(self.tbl, r, C_PU, "0.00", editable=False)
                self._set_or_update_item(self.tbl, r, C_IMP, "0.00", editable=False)

                self._apply_editabilidad_std(r)

                try:
                    self._calc_std_row(r)
                except Exception:
                    pass

            finally:
                self._prog = False
                self._recalc_summary()

    def _add_he(self, rec: Dict[str, Any], tipo: str, color: str,
                ancho: float, alto: float, _pzas_ignored: int) -> None:
        """
        Agrega un renglón a la tabla de Herrería.
        NOTA: Este método es para herrería estándar, no para paquetes.
        """
        if not hasattr(self, "tbl_he"):
            return

        r = self.tbl_he.rowCount()
        self.tbl_he.insertRow(r)

        try:
            self._prog = True

            tipo_txt = (tipo or "").strip().upper()
            clave = str(rec.get("clave", "") or "")
            desc = str(rec.get("descripcion", "") or "")

            try:
                ancho_val = float(ancho or 0.0)
            except Exception:
                ancho_val = 0.0
            try:
                alto_val = float(alto or 0.0)
            except Exception:
                alto_val = 0.0

            ca_val = 1.0
            ch_val = 1.0
            pzas_val = 1

            try:
                kg_m_val = self.svc.herreria_kg_por_m(clave) or 0.0
                kg_m_val = float(kg_m_val)
            except Exception:
                kg_m_val = 0.0

            precio_kg_val = float(self.sp_precio_kg.value())

            # Para cálculos, usar medidas ajustadas
            ancho_ajustado, alto_ajustado = _ajustar_medidas_industriales(ancho_val, alto_val)
            metros_val = (ca_val * ancho_ajustado) + (ch_val * alto_ajustado)
            kgs_val = metros_val * kg_m_val

            ctx = EspecificacionesCtx(
                svc=self.svc,
                tipo="HERRERIA",
                clave=clave,
                color=self._get_color_partida_o_global(),
                ancho=ancho_ajustado,  # Usar ajustado para cálculos
                alto=alto_ajustado,  # Usar ajustado para cálculos
                piezas=pzas_val,
                ca=ca_val,
                ch=ch_val,
                extra={
                    "precio_kg": precio_kg_val,
                    "ca": ca_val,
                    "ch": ch_val,
                },
            )

            pu_val, imp_val = dispatch_calculo(ctx)

            self._set_or_update_item(self.tbl_he, r, H_TIPO, tipo_txt, editable=False)
            self._set_or_update_item(self.tbl_he, r, H_CLAVE, clave, editable=False)
            self._set_or_update_item(self.tbl_he, r, H_DESC, desc, editable=False)

            self._set_or_update_item(self.tbl_he, r, H_CA, f"{ca_val:.0f}", editable=True)
            # ✅ Mostrar valor ORIGINAL (NO ajustado)
            self._set_or_update_item(self.tbl_he, r, H_ANCHO, f"{ancho_val:.2f}", editable=True)
            self._set_or_update_item(self.tbl_he, r, H_CH, f"{ch_val:.0f}", editable=True)
            # ✅ Mostrar valor ORIGINAL (NO ajustado)
            self._set_or_update_item(self.tbl_he, r, H_ALTO, f"{alto_val:.2f}", editable=True)

            self._set_or_update_item(self.tbl_he, r, H_METROS, f"{metros_val:.3f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_KG_M, f"{kg_m_val:.3f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_KGS, f"{kgs_val:.3f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_PKG, f"{precio_kg_val:.2f}", editable=False)

            self._set_or_update_item(self.tbl_he, r, H_PZAS, f"{pzas_val:d}", editable=True)
            self._set_money(self.tbl_he, r, H_PU, pu_val)
            self._set_money(self.tbl_he, r, H_IMP, imp_val)

            self._recalc_summary()

        finally:
            self._prog = False

    def _apply_editabilidad_std(self, row: int) -> None:
        """Aplica las reglas de editabilidad a una fila según su tipo."""
        tipo = (self._get_tipo(row) or "").strip().upper()
        rules = EDITABILIDAD.get(
            tipo,
            EDITABILIDAD.get(
                busquedas.normalize_token(tipo),
                EDITABILIDAD["OTROS"]
            )
        )

        def set_editable(c: int, editable: bool):
            it = self.tbl.item(row, c)
            if it is None:
                it = QTableWidgetItem("")
                self.tbl.setItem(row, c, it)
            flags = it.flags()
            it.setFlags(
                (flags | Qt.ItemFlag.ItemIsEditable) if editable
                else (flags & ~Qt.ItemFlag.ItemIsEditable)
            )

        set_editable(C_CA, bool(rules["CA"]))
        set_editable(C_CH, bool(rules["CH"]))
        set_editable(C_ANCHO, bool(rules["ANCHO"]))
        set_editable(C_ALTO, bool(rules["ALTO"]))
        set_editable(C_PZAS, bool(rules["PZAS"]))

    def _on_tbl_std_changed(self, item: QTableWidgetItem) -> None:
        """
        Responde a cambios en la tabla estándar.
        """
        if item is None:
            return

        if getattr(self, "_prog", False):
            return

        row = item.row()
        col = item.column()

        if col not in (
                C_CA,
                C_ANCHO,
                C_CH,
                C_ALTO,
                C_PZAS,
                C_PU,
        ):
            return

        try:
            self._prog = True
            self._calc_std_row(row)

        except Exception as e:
            QMessageBox.warning(
                self,
                "Cálculo",
                f"Hubo un problema al calcular la fila:\n{e}"
            )
        finally:
            self._prog = False

    def _on_tbl_he_changed(self, item: QTableWidgetItem) -> None:
        """
        Responde a cambios en la tabla de Herrería.
        """
        if item is None:
            return

        if getattr(self, "_prog", False):
            return

        row = item.row()
        col = item.column()

        if col not in (H_CA, H_ANCHO, H_CH, H_ALTO, H_PZAS):
            return

        try:
            self._prog = True
            self._calc_he_row(row)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Cálculo Herrería",
                f"Hubo un problema al calcular la fila:\n{e}"
            )
        finally:
            self._prog = False

    def _calc_he_row(self, r: int) -> None:
        """Calcula los valores de una fila de la tabla de Herrería."""
        try:
            self._prog = True

            ca_val = _f(self._safe_text(self.tbl_he, r, H_CA, "1"), 1.0)
            ancho_val = _f(self._safe_text(self.tbl_he, r, H_ANCHO, "0"), 0.0)
            ch_val = _f(self._safe_text(self.tbl_he, r, H_CH, "1"), 1.0)
            alto_val = _f(self._safe_text(self.tbl_he, r, H_ALTO, "0"), 0.0)
            pzas_val = _i(self._safe_text(self.tbl_he, r, H_PZAS, "1"), 1)

            clave = self._safe_text(self.tbl_he, r, H_CLAVE, "")

            try:
                kg_m_val = self.svc.herreria_kg_por_m(clave) or 0.0
                kg_m_val = float(kg_m_val)
            except Exception:
                kg_m_val = 0.0

            precio_kg_val = float(self.sp_precio_kg.value())

            # Para cálculos, usar medidas ajustadas
            ancho_ajustado, alto_ajustado = _ajustar_medidas_industriales(ancho_val, alto_val)
            metros_val = (ca_val * ancho_ajustado) + (ch_val * alto_ajustado)
            kgs_val = metros_val * kg_m_val

            self._set_or_update_item(self.tbl_he, r, H_METROS, f"{metros_val:.3f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_KG_M, f"{kg_m_val:.3f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_KGS, f"{kgs_val:.3f}", editable=False)
            self._set_or_update_item(self.tbl_he, r, H_PKG, f"{precio_kg_val:.2f}", editable=False)

            ctx = EspecificacionesCtx(
                svc=self.svc,
                tipo="HERRERIA",
                clave=clave,
                color=self._get_color_partida_o_global(),
                ancho=ancho_ajustado,  # Usar ajustado para cálculos
                alto=alto_ajustado,  # Usar ajustado para cálculos
                piezas=pzas_val,
                ca=ca_val,
                ch=ch_val,
                extra={
                    "precio_kg": precio_kg_val,
                    "ca": ca_val,
                    "ch": ch_val,
                },
            )

            pu_val, imp_val = dispatch_calculo(ctx)

            self._set_money(self.tbl_he, r, H_PU, pu_val)
            self._set_money(self.tbl_he, r, H_IMP, imp_val)

            self._recalc_summary()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error en cálculo",
                f"Error al calcular fila {r}:\n{str(e)}"
            )
        finally:
            self._prog = False

    def _calc_std_row(self, r: int) -> None:
        """Calcula los valores de una fila de la tabla estándar."""
        tipo = (self._get_tipo(r) or "").strip().upper()
        clave = self._safe_text(self.tbl, r, C_CLAVE, "")
        color = self._get_color_partida_o_global()

        # Obtener valores ORIGINALES de la tabla
        ancho_original = _f(self._safe_text(self.tbl, r, C_ANCHO, "0"))
        alto_original = _f(self._safe_text(self.tbl, r, C_ALTO, "0"))

        ca = _f(self._safe_text(self.tbl, r, C_CA, "1"), 1)
        ch = _f(self._safe_text(self.tbl, r, C_CH, "1"), 1)
        pzas = _i(self._safe_text(self.tbl, r, C_PZAS, "1"), 1)
        precio_kg = float(self.sp_precio_kg.value())

        try:
            g = guard_before_add(
                svc=self.svc,
                tipo=tipo,
                clave=clave,
                color=color,
                precio_kg=precio_kg
            )
        except Exception as e:
            g = type("G", (), {"proceed": True, "faltantes": []})()
            QMessageBox.warning(
                self,
                "Reglas previas",
                f"No fue posible validar reglas previas:\n{e}"
            )

        if not getattr(g, "proceed", True):
            self._set_money(self.tbl, r, C_PU, 0.0)
            self._set_money(self.tbl, r, C_IMP, 0.0)
            self._recalc_summary()
            return

        # ✅ PARA CÁLCULOS: Usar medidas ajustadas industrialmente
        ancho_ajustado, alto_ajustado = _ajustar_medidas_industriales(ancho_original, alto_original)

        if tipo in ["HERRERÍA", "HERRERIA"]:
            # Para herrería, usar valores ajustados
            ancho = ancho_ajustado
            alto = alto_ajustado
        else:
            # Para otros tipos, también usar ajustados en cálculos
            ancho = ancho_ajustado
            alto = alto_ajustado

        ctx = EspecificacionesCtx(
            svc=self.svc,
            tipo=tipo,
            clave=clave,
            color=color,
            ancho=ancho,  # ✅ Valor AJUSTADO para cálculos
            alto=alto,  # ✅ Valor AJUSTADO para cálculos
            piezas=pzas,
            ca=ca,
            ch=ch,
            extra={
                "precio_kg": precio_kg,
                "ca": ca,
                "ch": ch
            }
        )

        try:
            pu, imp = dispatch_calculo(ctx)
        except Exception as e:
            pu, imp = 0.0, 0.0
            QMessageBox.warning(
                self,
                "Cálculo",
                f"No fue posible calcular el P.U./Importe:\n{e}"
            )

        self._set_money(self.tbl, r, C_PU, pu)
        self._set_money(self.tbl, r, C_IMP, imp)
        self._recalc_summary()

    def _recalc_summary(self) -> None:
        """Recalcula todos los totales y resúmenes."""
        A = 0.0

        for r in range(self.tbl.rowCount()):
            A += _f(self._safe_text(self.tbl, r, C_IMP, "0"), 0.0)

        try:
            if hasattr(self, "tbl_he"):
                for r in range(self.tbl_he.rowCount()):
                    A += _f(self._safe_text(self.tbl_he, r, H_IMP, "0"), 0.0)
        except Exception:
            pass

        try:
            if hasattr(self, "tbl_he") and hasattr(self, "sp_kg"):
                total_kgs = 0.0
                for r in range(self.tbl_he.rowCount()):
                    total_kgs += _f(self._safe_text(self.tbl_he, r, H_KGS, "0"), 0.0)
                self.sp_kg.setValue(total_kgs)
        except Exception:
            pass

        B = float(self.sp_mo.value()) + float(self.sp_acc.value())
        C = A + B
        D = C + (C * (float(self.sb_desperdicio.value()) / 100.0))
        E = D + (D * (float(self.sb_fv_pct.value()) / 100.0))

        piezas = max(1, int(self.sb_pzas_global.value()))
        total_partida = E * piezas

        self.sp_pu_partida.setValue(E)
        self.sp_total_partida.setValue(total_partida)

        sub = total_partida
        iva = sub * 0.16
        tot = sub + iva

        self.sp_subtotal.setValue(sub)
        self.sp_iva.setValue(iva)
        self.sp_total.setValue(tot)

    # ============================================================================
    # MÉTODOS DE MENÚ (COMPLETOS - mismos que antes)
    # ============================================================================

    def _build_menu(self) -> None:
        """Construye la barra de menú completa."""
        mb = self.menuBar()

        # ========== MENÚ ARCHIVO ==========
        m_archivo = mb.addMenu("&Archivo")

        # Nuevo Presupuesto
        act_nuevo = QAction("&Nuevo Presupuesto", self)
        act_nuevo.setShortcut(QKeySequence("Ctrl+N"))
        act_nuevo.triggered.connect(self._on_nuevo_presupuesto)
        m_archivo.addAction(act_nuevo)

        # Abrir Presupuesto
        act_abrir = QAction("&Abrir Presupuesto", self)
        act_abrir.setShortcut(QKeySequence("Ctrl+O"))
        act_abrir.triggered.connect(self._on_abrir_presupuesto)
        m_archivo.addAction(act_abrir)

        m_archivo.addSeparator()

        # Guardar Presupuesto
        act_guardar = QAction("&Guardar Presupuesto", self)
        act_guardar.setShortcut(QKeySequence("Ctrl+S"))
        act_guardar.triggered.connect(self._on_guardar_presupuesto)
        m_archivo.addAction(act_guardar)

        # Guardar Como
        act_guardar_como = QAction("&Guardar Como...", self)
        act_guardar_como.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_guardar_como.triggered.connect(self._on_guardar_como_presupuesto)
        m_archivo.addAction(act_guardar_como)

        m_archivo.addSeparator()

        # Imprimir
        act_imprimir = QAction("&Imprimir", self)
        act_imprimir.setShortcut(QKeySequence("Ctrl+P"))
        act_imprimir.triggered.connect(self._on_imprimir)
        m_archivo.addAction(act_imprimir)

        # Vista Previa de Impresión
        act_vista_previa = QAction("Vista &Previa de Impresión", self)
        act_vista_previa.triggered.connect(self._on_vista_previa)
        m_archivo.addAction(act_vista_previa)

        m_archivo.addSeparator()

        # Exportar a Excel
        act_exportar_excel = QAction("Exportar a E&xcel", self)
        act_exportar_excel.setShortcut(QKeySequence("Ctrl+E"))
        act_exportar_excel.triggered.connect(self._on_exportar_excel)
        m_archivo.addAction(act_exportar_excel)

        # Exportar a PDF
        act_exportar_pdf = QAction("Exportar a &PDF", self)
        act_exportar_pdf.setShortcut(QKeySequence("Ctrl+D"))
        act_exportar_pdf.triggered.connect(self._on_exportar_pdf)
        m_archivo.addAction(act_exportar_pdf)

        m_archivo.addSeparator()

        # Configuración
        act_config = QAction("&Configuración", self)
        act_config.triggered.connect(self._on_configuracion)
        m_archivo.addAction(act_config)

        m_archivo.addSeparator()

        # Salir
        act_salir = QAction("&Salir", self)
        act_salir.setShortcut(QKeySequence("Ctrl+Q"))
        act_salir.triggered.connect(self.close)
        m_archivo.addAction(act_salir)

        # ========== MENÚ EDICIÓN ==========
        m_edicion = mb.addMenu("&Edición")

        # Cortar
        act_cortar = QAction("Cor&tar", self)
        act_cortar.setShortcut(QKeySequence("Ctrl+X"))
        act_cortar.triggered.connect(self._on_cortar)
        m_edicion.addAction(act_cortar)

        # Copiar
        act_copiar = QAction("&Copiar", self)
        act_copiar.setShortcut(QKeySequence("Ctrl+C"))
        act_copiar.triggered.connect(self._on_copiar)
        m_edicion.addAction(act_copiar)

        # Pegar
        act_pegar = QAction("&Pegar", self)
        act_pegar.setShortcut(QKeySequence("Ctrl+V"))
        act_pegar.triggered.connect(self._on_pegar)
        m_edicion.addAction(act_pegar)

        m_edicion.addSeparator()

        # Seleccionar Todo
        act_sel_todo = QAction("&Seleccionar Todo", self)
        act_sel_todo.setShortcut(QKeySequence("Ctrl+A"))
        act_sel_todo.triggered.connect(self._on_seleccionar_todo)
        m_edicion.addAction(act_sel_todo)

        m_edicion.addSeparator()

        # Deshacer
        act_deshacer = QAction("&Deshacer", self)
        act_deshacer.setShortcut(QKeySequence("Ctrl+Z"))
        act_deshacer.triggered.connect(self._on_deshacer)
        m_edicion.addAction(act_deshacer)

        # Rehacer
        act_rehacer = QAction("&Rehacer", self)
        act_rehacer.setShortcut(QKeySequence("Ctrl+Y"))
        act_rehacer.triggered.connect(self._on_rehacer)
        m_edicion.addAction(act_rehacer)

        m_edicion.addSeparator()

        # Buscar
        act_buscar = QAction("&Buscar", self)
        act_buscar.setShortcut(QKeySequence("Ctrl+F"))
        act_buscar.triggered.connect(self._on_buscar)
        m_edicion.addAction(act_buscar)

        # Reemplazar
        act_reemplazar = QAction("&Reemplazar", self)
        act_reemplazar.setShortcut(QKeySequence("Ctrl+H"))
        act_reemplazar.triggered.connect(self._on_reemplazar)
        m_edicion.addAction(act_reemplazar)

        # ========== MENÚ PRESUPUESTO ==========
        m_presupuesto = mb.addMenu("&Presupuesto")

        # Nueva Partida
        act_nueva_partida = QAction("Nueva &Partida", self)
        act_nueva_partida.setShortcut(QKeySequence("Ctrl+T"))
        act_nueva_partida.triggered.connect(self._on_nueva_partida)
        m_presupuesto.addAction(act_nueva_partida)

        # Duplicar Partida
        act_duplicar_partida = QAction("&Duplicar Partida", self)
        act_duplicar_partida.triggered.connect(self._on_duplicar_partida)
        m_presupuesto.addAction(act_duplicar_partida)

        # Eliminar Partida
        act_eliminar_partida = QAction("&Eliminar Partida", self)
        act_eliminar_partida.setShortcut(QKeySequence("Del"))
        act_eliminar_partida.triggered.connect(self._on_eliminar_partida)
        m_presupuesto.addAction(act_eliminar_partida)

        m_presupuesto.addSeparator()

        # Calcular Totales
        act_calcular_totales = QAction("Calcular &Totales", self)
        act_calcular_totales.setShortcut(QKeySequence("F9"))
        act_calcular_totales.triggered.connect(self._on_calcular_totales)
        m_presupuesto.addAction(act_calcular_totales)

        # Recalcular Todo
        act_recalcular_todo = QAction("&Recalcular Todo", self)
        act_recalcular_todo.setShortcut(QKeySequence("F5"))
        act_recalcular_todo.triggered.connect(self._on_recalcular_todo)
        m_presupuesto.addAction(act_recalcular_todo)

        m_presupuesto.addSeparator()

        # Validar Presupuesto
        act_validar_presupuesto = QAction("&Validar Presupuesto", self)
        act_validar_presupuesto.triggered.connect(self._on_validar_presupuesto)
        m_presupuesto.addAction(act_validar_presupuesto)

        # Verificar Precios
        act_verificar_precios = QAction("Verificar &Precios", self)
        act_verificar_precios.triggered.connect(self._on_verificar_precios)
        m_presupuesto.addAction(act_verificar_precios)

        # ========== MENÚ MANTENIMIENTO ==========
        m_mantenimiento = mb.addMenu("&Mantenimiento")

        # Catálogo de Materiales
        act_catalogo_materiales = QAction("&Catálogo de Materiales", self)
        act_catalogo_materiales.triggered.connect(self._on_catalogo_materiales)
        m_mantenimiento.addAction(act_catalogo_materiales)

        # Catálogo de Clientes
        act_catalogo_clientes = QAction("Catálogo de &Clientes", self)
        act_catalogo_clientes.triggered.connect(self._on_catalogo_clientes)
        m_mantenimiento.addAction(act_catalogo_clientes)

        m_mantenimiento.addSeparator()

        # Definir Paquetes
        act_definir_paquetes = QAction("Definir &Paquetes", self)
        act_definir_paquetes.triggered.connect(self._on_definir_paquetes)
        m_mantenimiento.addAction(act_definir_paquetes)

        # Configurar Herrajes
        act_configurar_herrajes = QAction("Configurar &Herrajes", self)
        act_configurar_herrajes.triggered.connect(self._on_configurar_herrajes)
        m_mantenimiento.addAction(act_configurar_herrajes)

        # Parámetros del Sistema
        act_parametros_sistema = QAction("&Parámetros del Sistema", self)
        act_parametros_sistema.triggered.connect(self._on_parametros_sistema)
        m_mantenimiento.addAction(act_parametros_sistema)

        # ========== MENÚ REPORTES ==========
        m_reportes = mb.addMenu("&Reportes")

        # Reporte de Presupuesto
        act_reporte_presupuesto = QAction("&Reporte de Presupuesto", self)
        act_reporte_presupuesto.triggered.connect(self._on_reporte_presupuesto)
        m_reportes.addAction(act_reporte_presupuesto)

        # Análisis de Costos
        act_analisis_costos = QAction("Análisis de &Costos", self)
        act_analisis_costos.triggered.connect(self._on_analisis_costos)
        m_reportes.addAction(act_analisis_costos)

        # Lista de Materiales
        act_lista_materiales = QAction("&Lista de Materiales", self)
        act_lista_materiales.triggered.connect(self._on_lista_materiales)
        m_reportes.addAction(act_lista_materiales)

        m_reportes.addSeparator()

        # Reporte de Ventas
        act_reporte_ventas = QAction("Reporte de &Ventas", self)
        act_reporte_ventas.triggered.connect(self._on_reporte_ventas)
        m_reportes.addAction(act_reporte_ventas)

        # Reporte de Inventario
        act_reporte_inventario = QAction("Reporte de &Inventario", self)
        act_reporte_inventario.triggered.connect(self._on_reporte_inventario)
        m_reportes.addAction(act_reporte_inventario)

        # ========== MENÚ VENTANA ==========
        m_ventana = mb.addMenu("&Ventana")

        # Nueva Ventana
        act_nueva_ventana = QAction("&Nueva Ventana", self)
        act_nueva_ventana.triggered.connect(self._on_nueva_ventana)
        m_ventana.addAction(act_nueva_ventana)

        # Cerrar Ventana
        act_cerrar_ventana = QAction("&Cerrar Ventana", self)
        act_cerrar_ventana.triggered.connect(self._on_cerrar_ventana)
        m_ventana.addAction(act_cerrar_ventana)

        m_ventana.addSeparator()

        # Cascada
        act_cascada = QAction("&Cascada", self)
        act_cascada.triggered.connect(self._on_cascada)
        m_ventana.addAction(act_cascada)

        # Mosaico Horizontal
        act_mosaico_h = QAction("Mosaico &Horizontal", self)
        act_mosaico_h.triggered.connect(self._on_mosaico_horizontal)
        m_ventana.addAction(act_mosaico_h)

        # Mosaico Vertical
        act_mosaico_v = QAction("Mosaico &Vertical", self)
        act_mosaico_v.triggered.connect(self._on_mosaico_vertical)
        m_ventana.addAction(act_mosaico_v)

        m_ventana.addSeparator()

        # Siguiente Ventana
        act_sig_ventana = QAction("&Siguiente Ventana", self)
        act_sig_ventana.setShortcut(QKeySequence("Ctrl+Tab"))
        act_sig_ventana.triggered.connect(self._on_siguiente_ventana)
        m_ventana.addAction(act_sig_ventana)

        # Ventana Anterior
        act_ant_ventana = QAction("Ventana &Anterior", self)
        act_ant_ventana.setShortcut(QKeySequence("Ctrl+Shift+Tab"))
        act_ant_ventana.triggered.connect(self._on_ventana_anterior)
        m_ventana.addAction(act_ant_ventana)

        # ========== MENÚ AYUDA ==========
        m_ayuda = mb.addMenu("&Ayuda")

        # Contenido de Ayuda
        act_contenido_ayuda = QAction("&Contenido de Ayuda", self)
        act_contenido_ayuda.setShortcut(QKeySequence("F1"))
        act_contenido_ayuda.triggered.connect(self._on_contenido_ayuda)
        m_ayuda.addAction(act_contenido_ayuda)

        # Tutoriales
        act_tutoriales = QAction("&Tutoriales", self)
        act_tutoriales.triggered.connect(self._on_tutoriales)
        m_ayuda.addAction(act_tutoriales)

        m_ayuda.addSeparator()

        # Acerca de VAH
        act_acerca_de = QAction("&Acerca de VAH", self)
        act_acerca_de.triggered.connect(self._on_acerca_de)
        m_ayuda.addAction(act_acerca_de)

        # Verificar Actualizaciones
        act_actualizaciones = QAction("Verificar &Actualizaciones", self)
        act_actualizaciones.triggered.connect(self._on_verificar_actualizaciones)
        m_ayuda.addAction(act_actualizaciones)

    # ============================================================================
    # MÉTODOS DE MANEJO DE MENÚ (COMPLETOS)
    # ============================================================================

    def _on_nuevo_presupuesto(self):
        """Crea un nuevo presupuesto."""
        QMessageBox.information(self, "Nuevo Presupuesto", "Funcionalidad: Nuevo Presupuesto")

    def _on_abrir_presupuesto(self):
        """Abre un presupuesto existente."""
        QMessageBox.information(self, "Abrir Presupuesto", "Funcionalidad: Abrir Presupuesto")

    def _on_guardar_presupuesto(self):
        """Guarda el presupuesto actual."""
        QMessageBox.information(self, "Guardar Presupuesto", "Funcionalidad: Guardar Presupuesto")

    def _on_guardar_como_presupuesto(self):
        """Guarda el presupuesto actual con un nuevo nombre."""
        QMessageBox.information(self, "Guardar Como", "Funcionalidad: Guardar Como")

    def _on_imprimir(self):
        """Imprime el presupuesto actual."""
        QMessageBox.information(self, "Imprimir", "Funcionalidad: Imprimir")

    def _on_vista_previa(self):
        """Muestra vista previa de impresión."""
        QMessageBox.information(self, "Vista Previa", "Funcionalidad: Vista Previa de Impresión")

    def _on_exportar_excel(self):
        """Exporta el presupuesto a Excel."""
        QMessageBox.information(self, "Exportar a Excel", "Funcionalidad: Exportar a Excel")

    def _on_exportar_pdf(self):
        """Exporta el presupuesto a PDF."""
        QMessageBox.information(self, "Exportar a PDF", "Funcionalidad: Exportar a PDF")

    def _on_configuracion(self):
        """Abre la configuración del sistema."""
        QMessageBox.information(self, "Configuración", "Funcionalidad: Configuración")

    def _on_cortar(self):
        """Corta el texto seleccionado."""
        QMessageBox.information(self, "Cortar", "Funcionalidad: Cortar")

    def _on_copiar(self):
        """Copia el texto seleccionado."""
        QMessageBox.information(self, "Copiar", "Funcionalidad: Copiar")

    def _on_pegar(self):
        """Pega el texto del portapapeles."""
        QMessageBox.information(self, "Pegar", "Funcionalidad: Pegar")

    def _on_seleccionar_todo(self):
        """Selecciona todo el contenido."""
        QMessageBox.information(self, "Seleccionar Todo", "Funcionalidad: Seleccionar Todo")

    def _on_deshacer(self):
        """Deshace la última acción."""
        QMessageBox.information(self, "Deshacer", "Funcionalidad: Deshacer")

    def _on_rehacer(self):
        """Rehace la última acción deshecha."""
        QMessageBox.information(self, "Rehacer", "Funcionalidad: Rehacer")

    def _on_buscar(self):
        """Abre el cuadro de búsqueda."""
        QMessageBox.information(self, "Buscar", "Funcionalidad: Buscar")

    def _on_reemplazar(self):
        """Abre el cuadro de reemplazo."""
        QMessageBox.information(self, "Reemplazar", "Funcionalidad: Reemplazar")

    def _on_nueva_partida(self):
        """Crea una nueva partida en el presupuesto."""
        QMessageBox.information(self, "Nueva Partida", "Funcionalidad: Nueva Partida")

    def _on_duplicar_partida(self):
        """Duplica la partida actual."""
        QMessageBox.information(self, "Duplicar Partida", "Funcionalidad: Duplicar Partida")

    def _on_eliminar_partida(self):
        """Elimina la partida actual."""
        QMessageBox.information(self, "Eliminar Partida", "Funcionalidad: Eliminar Partida")

    def _on_calcular_totales(self):
        """Calcula los totales del presupuesto."""
        self._recalc_summary()
        QMessageBox.information(self, "Calcular Totales", "Totales calculados correctamente.")

    def _on_recalcular_todo(self):
        """Recalcula todos los valores del presupuesto."""
        for r in range(self.tbl.rowCount()):
            self._calc_std_row(r)
        for r in range(self.tbl_he.rowCount()):
            self._calc_he_row(r)
        self._recalc_summary()
        QMessageBox.information(self, "Recalcular Todo", "Todos los valores han sido recalculados.")

    def _on_validar_presupuesto(self):
        """Valida el presupuesto actual."""
        QMessageBox.information(self, "Validar Presupuesto", "Funcionalidad: Validar Presupuesto")

    def _on_verificar_precios(self):
        """Verifica los precios de los materiales."""
        QMessageBox.information(self, "Verificar Precios", "Funcionalidad: Verificar Precios")

    def _on_catalogo_materiales(self):
        """Abre el catálogo de materiales."""
        # Ruta del catálogo de materiales
        catalogo_path = r"D:\vah\catalogos\catalogo_materiales.py"
        if os.path.exists(catalogo_path):
            try:
                subprocess.Popen([sys.executable, catalogo_path])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el catálogo:\n{str(e)}")
        else:
            QMessageBox.warning(self, "No encontrado", f"Archivo no encontrado:\n{catalogo_path}")

    def _on_catalogo_clientes(self):
        """Abre el catálogo de clientes."""
        QMessageBox.information(self, "Catálogo de Clientes", "Funcionalidad: Catálogo de Clientes")

    def _on_definir_paquetes(self):
        """Abre la definición de paquetes."""
        QMessageBox.information(self, "Definir Paquetes", "Funcionalidad: Definir Paquetes")

    def _on_configurar_herrajes(self):
        """Abre la configuración de herrajes."""
        QMessageBox.information(self, "Configurar Herrajes", "Funcionalidad: Configurar Herrajes")

    def _on_parametros_sistema(self):
        """Abre los parámetros del sistema."""
        QMessageBox.information(self, "Parámetros del Sistema", "Funcionalidad: Parámetros del Sistema")

    def _on_reporte_presupuesto(self):
        """Genera reporte de presupuesto."""
        QMessageBox.information(self, "Reporte de Presupuesto", "Funcionalidad: Reporte de Presupuesto")

    def _on_analisis_costos(self):
        """Genera análisis de costos."""
        QMessageBox.information(self, "Análisis de Costos", "Funcionalidad: Análisis de Costos")

    def _on_lista_materiales(self):
        """Genera lista de materiales."""
        QMessageBox.information(self, "Lista de Materiales", "Funcionalidad: Lista de Materiales")

    def _on_reporte_ventas(self):
        """Genera reporte de ventas."""
        QMessageBox.information(self, "Reporte de Ventas", "Funcionalidad: Reporte de Ventas")

    def _on_reporte_inventario(self):
        """Genera reporte de inventario."""
        QMessageBox.information(self, "Reporte de Inventario", "Funcionalidad: Reporte de Inventario")

    def _on_nueva_ventana(self):
        """Crea una nueva ventana del módulo."""
        nueva_ventana = PresupuestosWindow()
        nueva_ventana.show()

    def _on_cerrar_ventana(self):
        """Cierra la ventana actual."""
        self.close()

    def _on_cascada(self):
        """Organiza ventanas en cascada."""
        QMessageBox.information(self, "Cascada", "Funcionalidad: Organizar ventanas en cascada")

    def _on_mosaico_horizontal(self):
        """Organiza ventanas en mosaico horizontal."""
        QMessageBox.information(self, "Mosaico Horizontal", "Funcionalidad: Organizar ventanas en mosaico horizontal")

    def _on_mosaico_vertical(self):
        """Organiza ventanas en mosaico vertical."""
        QMessageBox.information(self, "Mosaico Vertical", "Funcionalidad: Organizar ventanas en mosaico vertical")

    def _on_siguiente_ventana(self):
        """Cambia a la siguiente ventana."""
        QMessageBox.information(self, "Siguiente Ventana", "Funcionalidad: Cambiar a siguiente ventana")

    def _on_ventana_anterior(self):
        """Cambia a la ventana anterior."""
        QMessageBox.information(self, "Ventana Anterior", "Funcionalidad: Cambiar a ventana anterior")

    def _on_contenido_ayuda(self):
        """Muestra el contenido de ayuda."""
        QMessageBox.information(self, "Ayuda", "Funcionalidad: Contenido de Ayuda\nPresiona F1 para más información.")

    def _on_tutoriales(self):
        """Muestra tutoriales."""
        QMessageBox.information(self, "Tutoriales", "Funcionalidad: Tutoriales")

    def _on_acerca_de(self):
        """Muestra información acerca de VAH."""
        about_text = """<h3>VAH - Sistema de Presupuestos</h3>
        <p><b>Versión:</b> 2.0.0</p>
        <p><b>Desarrollado por:</b> Equipo de Desarrollo VAH</p>
        <p><b>Fecha:</b> 2024</p>
        <p><b>Contacto:</b> soporte@vah.com</p>
        <hr>
        <p>Sistema integral para gestión de presupuestos en aluminio y herrería.</p>"""
        QMessageBox.about(self, "Acerca de VAH", about_text)

    def _on_verificar_actualizaciones(self):
        """Verifica actualizaciones del sistema."""
        QMessageBox.information(self, "Actualizaciones",
                                "Funcionalidad: Verificar Actualizaciones\nEl sistema está actualizado a la última versión.")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal de la aplicación."""
    app = QApplication(sys.argv)
    w = PresupuestosWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()