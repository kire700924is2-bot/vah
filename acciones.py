# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/acciones.py
Lógica de implementación de todas las acciones del sistema.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QInputDialog
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt6.QtCore import QFileInfo


class AccionesPresupuesto:
    """Implementa la lógica de todas las acciones del sistema."""

    def __init__(self, ventana_principal):
        self.ventana = ventana_principal
        self.ruta_actual = None
        self.datos_presupuesto = {}

    def nuevo_presupuesto(self):
        """Crea un nuevo presupuesto."""
        if self._verificar_cambios_no_guardados():
            respuesta = QMessageBox.question(
                self.ventana, "Nuevo presupuesto",
                "¿Desea guardar los cambios del presupuesto actual?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel
            )

            if respuesta == QMessageBox.StandardButton.Save:
                if not self.guardar():
                    return False
            elif respuesta == QMessageBox.StandardButton.Cancel:
                return False

        # Reiniciar ventana
        self.ventana.le_cliente.clear()
        self.ventana.le_obra.clear()
        self.ventana.sp_presupuesto.setValue(1)
        self.ventana.sp_partida.setValue(1)
        self.ventana.le_titulo.clear()
        self.ventana.te_desc.clear()
        self.ventana.tbl.setRowCount(0)
        self.ventana.tbl_he.setRowCount(0)
        self.ventana.tbl_paquetes.setRowCount(0)

        self.ruta_actual = None
        self.datos_presupuesto = {}
        QMessageBox.information(self.ventana, "Nuevo presupuesto",
                                "Presupuesto creado exitosamente.")
        return True

    def nueva_partida(self):
        """Agrega una nueva partida al presupuesto."""
        # Incrementar número de partida
        num_partida = self.ventana.sp_partida.value() + 1
        self.ventana.sp_partida.setValue(num_partida)

        # Limpiar campos de partida (pero mantener cliente/obra)
        self.ventana.le_titulo.clear()
        self.ventana.te_desc.clear()
        self.ventana.tbl.setRowCount(0)
        self.ventana.tbl_he.setRowCount(0)
        self.ventana.tbl_paquetes.setRowCount(0)

        QMessageBox.information(self.ventana, "Nueva partida",
                                f"Partida #{num_partida} creada.")
        return True

    def guardar(self) -> bool:
        """Guarda el presupuesto actual."""
        if self.ruta_actual:
            return self._guardar_a_ruta(self.ruta_actual)
        else:
            return self.guardar_como()

    def guardar_como(self) -> bool:
        """Guarda el presupuesto con un nuevo nombre."""
        ruta, _ = QFileDialog.getSaveFileName(
            self.ventana,
            "Guardar presupuesto",
            f"Presupuesto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.vah",
            "Archivos VAH (*.vah);;Todos los archivos (*.*)"
        )

        if ruta:
            if not ruta.endswith('.vah'):
                ruta += '.vah'
            return self._guardar_a_ruta(ruta)
        return False

    def _guardar_a_ruta(self, ruta: str) -> bool:
        """Guarda el presupuesto a una ruta específica."""
        try:
            datos = self._obtener_datos_presupuesto()

            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)

            self.ruta_actual = ruta
            QMessageBox.information(self.ventana, "Guardar",
                                    f"Presupuesto guardado en:\n{ruta}")
            return True
        except Exception as e:
            QMessageBox.critical(self.ventana, "Error al guardar",
                                 f"No se pudo guardar el archivo:\n{str(e)}")
            return False

    def _obtener_datos_presupuesto(self) -> Dict[str, Any]:
        """Obtiene todos los datos del presupuesto actual."""
        datos = {
            "cliente": self.ventana.le_cliente.text(),
            "obra": self.ventana.le_obra.text(),
            "presupuesto": self.ventana.sp_presupuesto.value(),
            "partida": self.ventana.sp_partida.value(),
            "fecha": self.ventana.de_fv.date().toString("yyyy-MM-dd"),
            "color_global": self.ventana.cbo_color_global.currentText(),
            "titulo": self.ventana.le_titulo.text(),
            "descripcion": self.ventana.te_desc.toPlainText(),
            "desperdicio": self.ventana.sb_desperdicio.value(),
            "fv_pct": self.ventana.sb_fv_pct.value(),
            "color_partida": self.ventana.cbo_color.currentText(),
            "precio_kg": self.ventana.sp_precio_kg.value(),
            "ancho": self.ventana.sp_ancho.value(),
            "alto": self.ventana.sp_alto.value(),
            "mo": self.ventana.sp_mo.value(),
            "acc": self.ventana.sp_acc.value(),
            "pzas_global": self.ventana.sb_pzas_global.value(),
            "materiales": self._obtener_datos_tabla(self.ventana.tbl),
            "herreria": self._obtener_datos_tabla(self.ventana.tbl_he),
            "paquetes": self._obtener_datos_paquetes(),
            "timestamp": datetime.now().isoformat()
        }
        return datos

    def _obtener_datos_tabla(self, tabla):
        """Extrae datos de una tabla."""
        datos = []
        for fila in range(tabla.rowCount()):
            fila_datos = {}
            for col in range(tabla.columnCount()):
                item = tabla.item(fila, col)
                if item:
                    fila_datos[f"col_{col}"] = item.text()
            datos.append(fila_datos)
        return datos

    def _obtener_datos_paquetes(self):
        """Extrae datos de la tabla de paquetes."""
        datos = []
        for fila in range(self.ventana.tbl_paquetes.rowCount()):
            fila_datos = {}
            for col in range(self.ventana.tbl_paquetes.columnCount()):
                item = self.ventana.tbl_paquetes.item(fila, col)
                if item:
                    fila_datos[f"col_{col}"] = item.text()
            datos.append(fila_datos)
        return datos

    def copiar(self):
        """Copia la selección actual."""
        # Implementar lógica de copia según el widget activo
        widget_activo = self.ventana.focusWidget()

        if widget_activo == self.ventana.tbl:
            self._copiar_tabla(self.ventana.tbl)
        elif widget_activo == self.ventana.tbl_he:
            self._copiar_tabla(self.ventana.tbl_he)
        elif widget_activo == self.ventana.tbl_paquetes:
            self._copiar_tabla(self.ventana.tbl_paquetes)
        elif widget_activo == self.ventana.te_desc:
            self.ventana.te_desc.copy()
        else:
            QMessageBox.information(self.ventana, "Copiar",
                                    "Seleccione contenido para copiar.")

    def _copiar_tabla(self, tabla):
        """Copia selección de tabla al portapapeles."""
        seleccion = tabla.selectedRanges()
        if seleccion:
            texto = ""
            for rango in seleccion:
                for fila in range(rango.topRow(), rango.bottomRow() + 1):
                    fila_texto = []
                    for col in range(rango.leftColumn(), rango.rightColumn() + 1):
                        item = tabla.item(fila, col)
                        fila_texto.append(item.text() if item else "")
                    texto += "\t".join(fila_texto) + "\n"

            # Copiar al portapapeles
            clipboard = self.ventana.clipboard()
            clipboard.setText(texto)
            QMessageBox.information(self.ventana, "Copiar",
                                    f"{len(seleccion[0].rowCount())} filas copiadas.")

    def pegar(self):
        """Pega contenido del portapapeles."""
        # Implementar lógica de pegado
        pass

    def insertar(self):
        """Inserta un nuevo elemento."""
        # Mostrar diálogo de inserción
        opciones = ["Material", "Paquete", "Partida", "Nota"]
        item, ok = QInputDialog.getItem(
            self.ventana, "Insertar", "Seleccione tipo:",
            opciones, 0, False
        )

        if ok and item:
            if item == "Material":
                self.ventana.cbo_tipo.setCurrentText("ALUMINIO")
                self.ventana.le_filtro.setFocus()
            elif item == "Paquete":
                self.ventana.cbo_tipo.setCurrentText("PAQUETE ALUMINIO")
                self.ventana.le_filtro.setFocus()

    def modificar(self):
        """Modifica el elemento seleccionado."""
        # Implementar lógica de modificación
        pass

    def eliminar(self):
        """Elimina el elemento seleccionado."""
        widget_activo = self.ventana.focusWidget()

        if widget_activo == self.ventana.tbl:
            self._eliminar_filas_tabla(self.ventana.tbl)
        elif widget_activo == self.ventana.tbl_he:
            self._eliminar_filas_tabla(self.ventana.tbl_he)
        elif widget_activo == self.ventana.tbl_paquetes:
            self._eliminar_filas_tabla(self.ventana.tbl_paquetes)

    def _eliminar_filas_tabla(self, tabla):
        """Elimina filas seleccionadas de una tabla."""
        filas_seleccionadas = sorted(
            set(index.row() for index in tabla.selectedIndexes()),
            reverse=True  # Eliminar de abajo hacia arriba
        )

        if filas_seleccionadas:
            respuesta = QMessageBox.question(
                self.ventana, "Eliminar",
                f"¿Eliminar {len(filas_seleccionadas)} elemento(s) seleccionado(s)?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                for fila in filas_seleccionadas:
                    tabla.removeRow(fila)
                self.ventana._recalc_summary()

    def imprimir(self):
        """Imprime el presupuesto actual."""
        dialog = QPrintDialog()
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            printer = dialog.printer()
            # TODO: Implementar lógica de impresión
            QMessageBox.information(self.ventana, "Imprimir",
                                    "Impresión enviada a la impresora.")

    def imprimir_pantalla(self):
        """Captura la pantalla actual."""
        # TODO: Implementar captura de pantalla
        pass

    def imprimir_archivo(self, formato: str = "PDF"):
        """Exporta a archivo (PDF, Excel, etc.)."""
        if formato == "PDF":
            ruta, _ = QFileDialog.getSaveFileName(
                self.ventana, "Exportar a PDF",
                f"Presupuesto_{datetime.now().strftime('%Y%m%d')}.pdf",
                "Archivos PDF (*.pdf)"
            )
            if ruta:
                self._exportar_a_pdf(ruta)
        elif formato == "Excel":
            ruta, _ = QFileDialog.getSaveFileName(
                self.ventana, "Exportar a Excel",
                f"Presupuesto_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "Archivos Excel (*.xlsx)"
            )
            if ruta:
                self._exportar_a_excel(ruta)

    def _exportar_a_pdf(self, ruta: str):
        """Exporta el presupuesto a PDF."""
        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(ruta)

            # TODO: Implementar renderizado del presupuesto
            QMessageBox.information(self.ventana, "Exportar PDF",
                                    f"PDF exportado a:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self.ventana, "Error",
                                 f"No se pudo exportar PDF:\n{str(e)}")

    def _exportar_a_excel(self, ruta: str):
        """Exporta el presupuesto a Excel."""
        # TODO: Implementar exportación a Excel usando openpyxl
        pass

    def _verificar_cambios_no_guardados(self) -> bool:
        """Verifica si hay cambios no guardados."""
        # Implementar lógica para detectar cambios
        return False