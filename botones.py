# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/botones.py
Gestión centralizada de botones, menús y atajos de teclado.
"""

from typing import Dict, List, Callable, Any, Optional
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QKeySequence, QAction
from PyQt6.QtWidgets import (
    QToolBar, QMenu, QPushButton, QToolButton, QWidget,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QStyle
)


class GestorBotones:
    """Clase centralizada para gestionar botones, menús y atajos."""

    def __init__(self, ventana_principal):
        """
        Inicializa el gestor de botones.

        Args:
            ventana_principal: Referencia a la ventana principal
        """
        self.ventana = ventana_principal
        self.acciones = {}  # Diccionario de acciones: nombre -> QAction
        self.botones = {}  # Diccionario de botones: nombre -> QToolButton
        self.menus = {}  # Diccionario de menús: nombre -> QMenu

    def crear_acciones(self) -> Dict[str, QAction]:
        """Crea y configura todas las acciones disponibles."""
        acciones = {}

        # ACCIONES DE ARCHIVO
        acciones['nuevo_presupuesto'] = self._crear_accion(
            "📄 Nuevo Presupuesto",
            "Crea un nuevo presupuesto",
            QKeySequence.StandardKey.New,
            "Ctrl+N",
            lambda: self._ejecutar_accion('nuevo_presupuesto'),
            "nuevo"
        )

        acciones['nueva_partida'] = self._crear_accion(
            "➕ Nueva Partida",
            "Agrega una nueva partida al presupuesto actual",
            QKeySequence.StandardKey.AddTab,
            "Ctrl+Shift+N",
            lambda: self._ejecutar_accion('nueva_partida'),
            "nuevo"
        )

        acciones['guardar'] = self._crear_accion(
            "💾 Guardar",
            "Guarda el presupuesto actual",
            QKeySequence.StandardKey.Save,
            "Ctrl+G",
            lambda: self._ejecutar_accion('guardar'),
            "guardar"
        )

        acciones['guardar_como'] = self._crear_accion(
            "💾 Guardar como...",
            "Guarda el presupuesto con un nombre diferente",
            QKeySequence.StandardKey.SaveAs,
            "Ctrl+Shift+G",
            lambda: self._ejecutar_accion('guardar_como'),
            "guardar_como"
        )

        acciones['imprimir'] = self._crear_accion(
            "🖨️ Imprimir",
            "Imprime el presupuesto actual",
            QKeySequence.StandardKey.Print,
            "Ctrl+P",
            lambda: self._ejecutar_accion('imprimir'),
            "imprimir"
        )

        # ACCIONES DE EDICIÓN
        acciones['copiar'] = self._crear_accion(
            "📋 Copiar",
            "Copia la selección actual",
            QKeySequence.StandardKey.Copy,
            "Ctrl+C",
            lambda: self._ejecutar_accion('copiar'),
            "copiar"
        )

        acciones['pegar'] = self._crear_accion(
            "📎 Pegar",
            "Pega el contenido del portapapeles",
            QKeySequence.StandardKey.Paste,
            "Ctrl+V",
            lambda: self._ejecutar_accion('pegar'),
            "pegar"
        )

        acciones['insertar'] = self._crear_accion(
            "➕ Insertar",
            "Inserta un nuevo elemento",
            None,
            "Ctrl+I",
            lambda: self._ejecutar_accion('insertar'),
            "insertar"
        )

        acciones['modificar'] = self._crear_accion(
            "✏️ Modificar",
            "Modifica el elemento seleccionado",
            None,
            "Ctrl+M",
            lambda: self._ejecutar_accion('modificar'),
            "modificar"
        )

        acciones['eliminar'] = self._crear_accion(
            "🗑️ Eliminar",
            "Elimina el elemento seleccionado",
            QKeySequence.StandardKey.Delete,
            "Del",
            lambda: self._ejecutar_accion('eliminar'),
            "eliminar"
        )

        # ACCIONES DE HERRAMIENTAS
        acciones['calculadora'] = self._crear_accion(
            "🧮 Calculadora",
            "Abre la calculadora de presupuestos",
            None,
            "Ctrl+K",
            lambda: self._ejecutar_accion('calculadora'),
            "calculadora"
        )

        acciones['configuracion'] = self._crear_accion(
            "⚙️ Configuración",
            "Abre la configuración del sistema",
            None,
            "Ctrl+Shift+C",
            lambda: self._ejecutar_accion('configuracion'),
            "configuracion"
        )

        self.acciones = acciones
        return acciones

    def _crear_accion(self, texto: str, tooltip: str,
                      shortcut_std=None, shortcut_text: str = "",
                      slot=None, icon_name: str = None) -> QAction:
        """Crea una acción con icono, texto y atajo."""
        accion = QAction(texto, self.ventana)
        accion.setToolTip(f"{tooltip} ({shortcut_text})" if shortcut_text else tooltip)

        # Establecer atajo de teclado
        if shortcut_std:
            accion.setShortcut(shortcut_std)
        elif shortcut_text:
            accion.setShortcut(shortcut_text)

        # Conectar señal
        if slot:
            accion.triggered.connect(slot)

        # Asignar icono (puedes usar iconos del sistema o personalizados)
        if icon_name:
            # Aquí puedes cargar iconos personalizados desde archivos
            # Por ahora uso iconos del sistema Qt
            try:
                # Mapeo de iconos personalizados
                icon_map = {
                    "nuevo": QStyle.StandardPixmap.SP_FileIcon,
                    "guardar": QStyle.StandardPixmap.SP_DialogSaveButton,
                    "copiar": QStyle.StandardPixmap.SP_FileDialogContentsView,
                    "pegar": QStyle.StandardPixmap.SP_DialogApplyButton,
                    "imprimir": QStyle.StandardPixmap.SP_FileDialogDetailedView,
                }
                if icon_name in icon_map:
                    icon = self.ventana.style().standardIcon(icon_map[icon_name])
                    accion.setIcon(icon)
            except:
                pass

        return accion

    def crear_barra_herramientas(self) -> QToolBar:
        """Crea y configura la barra de herramientas principal."""
        toolbar = QToolBar("Barra de herramientas principal", self.ventana)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setMovable(True)
        toolbar.setFloatable(False)

        # Agrupar botones por funcionalidad
        self._agregar_grupo_archivo(toolbar)
        toolbar.addSeparator()
        self._agregar_grupo_edicion(toolbar)
        toolbar.addSeparator()
        self._agregar_grupo_herramientas(toolbar)

        return toolbar

    def _agregar_grupo_archivo(self, toolbar: QToolBar):
        """Agrega botones del grupo Archivo."""
        grupos = [
            ('nuevo_presupuesto', '📄 Nuevo'),
            ('nueva_partida', '➕ Partida'),
            ('guardar', '💾 Guardar'),
            ('guardar_como', '💾 Guardar como'),
            ('imprimir', '🖨️ Imprimir')
        ]

        for accion_nombre, texto_boton in grupos:
            if accion_nombre in self.acciones:
                # Crear botón personalizado
                btn = QToolButton()
                btn.setDefaultAction(self.acciones[accion_nombre])
                btn.setText(texto_boton)
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
                btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                toolbar.addWidget(btn)
                self.botones[accion_nombre] = btn

    def _agregar_grupo_edicion(self, toolbar: QToolBar):
        """Agrega botones del grupo Edición."""
        grupos = [
            ('copiar', '📋 Copiar'),
            ('pegar', '📎 Pegar'),
            ('insertar', '➕ Insertar'),
            ('modificar', '✏️ Modificar'),
            ('eliminar', '🗑️ Eliminar')
        ]

        for accion_nombre, texto_boton in grupos:
            if accion_nombre in self.acciones:
                btn = QToolButton()
                btn.setDefaultAction(self.acciones[accion_nombre])
                btn.setText(texto_boton)
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
                btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                toolbar.addWidget(btn)
                self.botones[accion_nombre] = btn

    def _agregar_grupo_herramientas(self, toolbar: QToolBar):
        """Agrega botones del grupo Herramientas."""
        grupos = [
            ('calculadora', '🧮 Calculadora'),
            ('configuracion', '⚙️ Configurar')
        ]

        for accion_nombre, texto_boton in grupos:
            if accion_nombre in self.acciones:
                btn = QToolButton()
                btn.setDefaultAction(self.acciones[accion_nombre])
                btn.setText(texto_boton)
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
                btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
                toolbar.addWidget(btn)
                self.botones[accion_nombre] = btn

    def crear_menu_principal(self) -> Dict[str, QMenu]:
        """Crea y configura el menú principal."""
        menus = {}

        # MENÚ ARCHIVO
        menu_archivo = QMenu("&Archivo", self.ventana)
        menu_archivo.addAction(self.acciones['nuevo_presupuesto'])
        menu_archivo.addAction(self.acciones['nueva_partida'])
        menu_archivo.addSeparator()
        menu_archivo.addAction(self.acciones['guardar'])
        menu_archivo.addAction(self.acciones['guardar_como'])
        menu_archivo.addSeparator()
        menu_archivo.addAction(self.acciones['imprimir'])
        menu_archivo.addSeparator()
        menu_archivo.addAction("Salir", self.ventana.close)
        menus['archivo'] = menu_archivo

        # MENÚ EDITAR
        menu_editar = QMenu("&Editar", self.ventana)
        menu_editar.addAction(self.acciones['copiar'])
        menu_editar.addAction(self.acciones['pegar'])
        menu_editar.addSeparator()
        menu_editar.addAction(self.acciones['insertar'])
        menu_editar.addAction(self.acciones['modificar'])
        menu_editar.addAction(self.acciones['eliminar'])
        menus['editar'] = menu_editar

        # MENÚ PARTIDA
        menu_partida = QMenu("&Partida", self.ventana)
        menu_partida.addAction("Nueva partida", lambda: self._ejecutar_accion('nueva_partida'))
        menu_partida.addAction("Duplicar partida", lambda: self._ejecutar_accion('duplicar_partida'))
        menu_partida.addAction("Eliminar partida", lambda: self._ejecutar_accion('eliminar_partida'))
        menus['partida'] = menu_partida

        # MENÚ PRESUPUESTO
        menu_presupuesto = QMenu("&Presupuesto", self.ventana)
        menu_presupuesto.addAction("Nuevo presupuesto", lambda: self._ejecutar_accion('nuevo_presupuesto'))
        menu_presupuesto.addAction("Copiar presupuesto", lambda: self._ejecutar_accion('copiar_presupuesto'))
        menu_presupuesto.addAction("Exportar a Excel", lambda: self._ejecutar_accion('exportar_excel'))
        menu_presupuesto.addAction("Exportar a PDF", lambda: self._ejecutar_accion('exportar_pdf'))
        menus['presupuesto'] = menu_presupuesto

        # MENÚ HERRAMIENTAS
        menu_herramientas = QMenu("&Herramientas", self.ventana)
        menu_herramientas.addAction(self.acciones['calculadora'])
        menu_herramientas.addAction(self.acciones['configuracion'])
        menu_herramientas.addSeparator()
        menu_herramientas.addAction("Conversor de unidades", lambda: self._ejecutar_accion('conversor'))
        menu_herramientas.addAction("Estadísticas", lambda: self._ejecutar_accion('estadisticas'))
        menus['herramientas'] = menu_herramientas

        # MENÚ AYUDA
        menu_ayuda = QMenu("A&yuda", self.ventana)
        menu_ayuda.addAction("📘 Ayuda", lambda: self._ejecutar_accion('ayuda'))
        menu_ayuda.addAction("ℹ️ Acerca de", lambda: self._ejecutar_accion('acerca_de'))
        menus['ayuda'] = menu_ayuda

        self.menus = menus
        return menus

    def _ejecutar_accion(self, nombre_accion: str):
        """Ejecuta una acción específica."""
        # Aquí delegarías a un archivo acciones.py
        print(f"Ejecutando acción: {nombre_accion}")
        # TODO: Conectar con acciones.py

    def configurar_estilos(self):
        """Configura estilos CSS para botones y menús."""
        estilo = """
        /* ESTILOS GENERALES PARA BOTONES */
        QToolButton {
            padding: 6px 10px;
            margin: 2px;
            border: 1px solid #c0c0c0;
            border-radius: 4px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f6f6f6, stop:1 #e6e6e6);
            color: #333333;
            font-weight: bold;
            min-width: 80px;
            min-height: 60px;
        }

        QToolButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #e6f0ff, stop:1 #c6e0ff);
            border: 1px solid #4a90e2;
        }

        QToolButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #c6e0ff, stop:1 #a6d0ff);
            border: 1px solid #2a70c2;
        }

        QToolButton:disabled {
            background: #f0f0f0;
            color: #a0a0a0;
            border: 1px solid #d0d0d0;
        }

        /* BARRA DE HERRAMIENTAS */
        QToolBar {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #f8f8f8, stop:1 #e8e8e8);
            border-bottom: 1px solid #c0c0c0;
            spacing: 4px;
            padding: 4px;
        }

        QToolBar::separator {
            width: 1px;
            background: #c0c0c0;
            margin: 4px 8px;
        }

        /* MENÚS */
        QMenu {
            background-color: #ffffff;
            border: 1px solid #c0c0c0;
            border-radius: 4px;
            padding: 4px;
        }

        QMenu::item {
            padding: 6px 24px 6px 24px;
            margin: 2px;
            border-radius: 3px;
        }

        QMenu::item:selected {
            background-color: #e6f0ff;
            color: #2a70c2;
        }

        QMenu::separator {
            height: 1px;
            background: #e0e0e0;
            margin: 4px 8px;
        }

        /* ESTILOS PARA GRUPOS DE BOTONES */
        .grupo-archivo {
            border-right: 1px solid #d0d0d0;
            padding-right: 8px;
        }

        .grupo-edicion {
            border-right: 1px solid #d0d0d0;
            padding-right: 8px;
        }

        /* BOTONES CON ÍCONOS GRANDES */
        QToolButton[icon-size="large"] {
            min-width: 100px;
            min-height: 80px;
            font-size: 10px;
        }

        /* BADGE PARA NOTIFICACIONES */
        .badge {
            background-color: #ff4444;
            color: white;
            border-radius: 10px;
            padding: 1px 5px;
            font-size: 10px;
            font-weight: bold;
            position: absolute;
            top: 2px;
            right: 2px;
        }
        """

        self.ventana.setStyleSheet(self.ventana.styleSheet() + estilo)

    def actualizar_estados(self, contexto: str = "normal"):
        """Actualiza el estado de botones según el contexto."""
        estados = {
            "normal": {
                "guardar": True,
                "guardar_como": True,
                "copiar": True,
                "pegar": True,
                "insertar": True,
                "modificar": False,  # Solo si hay selección
                "eliminar": False,  # Solo si hay selección
            },
            "edicion": {
                "guardar": True,
                "guardar_como": True,
                "copiar": False,
                "pegar": True,
                "insertar": True,
                "modificar": True,
                "eliminar": True,
            },
            "vacio": {
                "guardar": False,
                "guardar_como": False,
                "copiar": False,
                "pegar": False,
                "insertar": True,
                "modificar": False,
                "eliminar": False,
            }
        }

        if contexto in estados:
            for accion_nombre, habilitado in estados[contexto].items():
                if accion_nombre in self.acciones:
                    self.acciones[accion_nombre].setEnabled(habilitado)
                if accion_nombre in self.botones:
                    self.botones[accion_nombre].setEnabled(habilitado)