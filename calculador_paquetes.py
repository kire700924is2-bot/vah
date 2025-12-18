# -*- coding: utf-8 -*-
"""
CALCULADOR DE PAQUETES
Módulo especializado para cálculo de paquetes de materiales
"""

import json
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime


def calcular_total_presupuesto(presupuesto_data: Dict) -> Dict:
    """
    Calcular el total de un presupuesto incluyendo subtotal, IVA y total.

    Args:
        presupuesto_data: Diccionario con los datos del presupuesto

    Returns:
        Diccionario con subtotal, IVA y total
    """
    try:
        items = presupuesto_data.get('items', [])

        if not isinstance(items, list):
            raise ValueError("Los items deben ser una lista")

        subtotal = 0.0

        for item in items:
            if isinstance(item, dict):
                # Intentar obtener importe directamente
                importe = item.get('importe', 0)

                if not importe:
                    # Calcular importe si no está presente
                    precio = item.get('precio_unitario', item.get('precio', 0))
                    cantidad = item.get('cantidad', item.get('piezas', 1))

                    try:
                        precio = float(precio)
                        cantidad = float(cantidad)
                        importe = precio * cantidad
                    except (ValueError, TypeError):
                        importe = 0

                subtotal += float(importe)

        # Obtener IVA (por defecto 16%)
        iva_porcentaje = presupuesto_data.get('iva', 0.16)
        iva_monto = subtotal * iva_porcentaje
        total = subtotal + iva_monto

        return {
            'subtotal': round(subtotal, 2),
            'iva_porcentaje': iva_porcentaje,
            'iva_monto': round(iva_monto, 2),
            'total': round(total, 2),
            'items_calculados': len(items),
            'fecha_calculo': datetime.now().isoformat(),
            'estado': 'EXITOSO'
        }

    except Exception as e:
        return {
            'subtotal': 0,
            'iva_porcentaje': 0,
            'iva_monto': 0,
            'total': 0,
            'error': str(e),
            'estado': 'ERROR'
        }


def validar_estructura_presupuesto(presupuesto_data: Dict) -> Tuple[bool, str]:
    """
    Validar la estructura básica de un presupuesto.

    Args:
        presupuesto_data: Diccionario con datos del presupuesto

    Returns:
        Tupla con (es_valido, mensaje)
    """
    try:
        # Validar que sea un diccionario
        if not isinstance(presupuesto_data, dict):
            return False, "El presupuesto debe ser un diccionario"

        # Validar items
        items = presupuesto_data.get('items', [])
        if not isinstance(items, list):
            return False, "Los items deben ser una lista"

        # Validar cada item
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                return False, f"Item {i+1} no es un diccionario"

            # Validar campos mínimos
            if not item.get('descripcion'):
                return False, f"Item {i+1} no tiene descripción"

        # Validar IVA si está presente
        if 'iva' in presupuesto_data:
            try:
                iva = float(presupuesto_data['iva'])
                if not (0 <= iva <= 1):
                    return False, f"El IVA debe estar entre 0 y 1 (0%-100%), recibido: {iva}"
            except (ValueError, TypeError):
                return False, "El IVA debe ser un número"

        return True, "Estructura válida"

    except Exception as e:
        return False, f"Error en validación: {str(e)}"


def generar_detalle_paquete(paquete_data: Dict) -> Dict:
    """
    Generar detalle de un paquete de materiales.

    Args:
        paquete_data: Datos del paquete

    Returns:
        Diccionario con detalle del paquete
    """
    try:
        tipo = paquete_data.get('tipo', 'DESCONOCIDO').upper()
        clave = paquete_data.get('clave', 'GENERICO')
        ancho = float(paquete_data.get('ancho', 0))
        alto = float(paquete_data.get('alto', 0))
        color = paquete_data.get('color', 'ESTANDAR')
        piezas = int(paquete_data.get('piezas', 1))
        extra = paquete_data.get('extra', {})

        # Calcular área
        area_m2 = (ancho * alto) / 1000000 if ancho > 0 and alto > 0 else 0

        # Precios base por tipo de paquete
        precios_base = {
            'PAQ-AL': {
                'BASICO': 1200.00,
                'ESTANDAR': 1850.50,
                'PREMIUM': 2500.75,
                'VENTANA_CORREDIZA': 1800.00,
                'VENTANA_OSCILOBATIENTE': 2200.00,
                'PUERTA_CORREDIZA': 2800.00
            },
            'PAQ-HR': {
                'BASICO': 350.25,
                'COMPLETO': 550.50,
                'PREMIUM': 750.75
            }
        }

        # Obtener precio base
        precio_base = 800.00  # Precio por defecto

        if tipo in precios_base:
            if clave.upper() in precios_base[tipo]:
                precio_base = precios_base[tipo][clave.upper()]
            elif 'BASICO' in precios_base[tipo]:
                precio_base = precios_base[tipo]['BASICO']

        # Ajustes
        ajustes = []

        # Ajuste por área
        if area_m2 > 0:
            factor_area = 1 + min(area_m2 * 0.08, 0.5)  # Máximo 50% extra
            precio_base *= factor_area
            ajustes.append(f"Área: {area_m2:.2f} m² (x{factor_area:.2f})")

        # Ajuste por color
        if color and color.upper() not in ['BLANCO', 'NEGRO', 'ESTANDAR', 'STANDARD']:
            precio_base *= 1.05  # 5% extra para colores especiales
            ajustes.append(f"Color especial: {color} (x1.05)")

        # Ajuste por cantidad
        if piezas > 10:
            descuento = 0.90 if piezas > 20 else 0.95
            precio_base *= descuento
            ajustes.append(f"Cantidad: {piezas} unidades (x{descuento:.2f})")

        # Componentes del paquete
        componentes = []

        if tipo == 'PAQ-AL':
            componentes = [
                'Perfiles de aluminio',
                'Herrajes básicos',
                'Vidrio estándar',
                'Selladores',
                'Instalación básica'
            ]

            if 'perfiles' in extra:
                componentes.extend(extra['perfiles'])

            if 'accesorios' in extra:
                componentes.append('Accesorios premium')

        elif tipo == 'PAQ-HR':
            componentes = [
                'Juego completo de herrajes',
                'Tornillería',
                'Soportes',
                'Guías'
            ]

        # Calcular total
        total = precio_base * max(1, piezas)

        return {
            'detalle': f"Paquete {tipo} - {clave}",
            'tipo': tipo,
            'clave': clave,
            'descripcion': paquete_data.get('descripcion', f'Paquete {tipo}'),
            'dimensiones': f"{ancho:.0f}x{alto:.0f} mm",
            'area_m2': round(area_m2, 3),
            'color': color,
            'piezas': piezas,
            'precio_base': round(precio_base, 2),
            'total': round(total, 2),
            'componentes': componentes,
            'ajustes_aplicados': ajustes,
            'parametros_extra': extra,
            'fecha_generacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'version': '1.0'
        }

    except Exception as e:
        return {
            'error': str(e),
            'detalle': 'Error generando detalle de paquete',
            'total': 0,
            'fecha_error': datetime.now().isoformat()
        }


# Funciones adicionales para el sistema
def calcular_descuento(cantidad: int, precio_base: float) -> float:
    """
    Calcular descuento basado en cantidad.

    Args:
        cantidad: Cantidad de unidades
        precio_base: Precio base por unidad

    Returns:
        Precio con descuento aplicado
    """
    if cantidad >= 50:
        return precio_base * 0.85  # 15% descuento
    elif cantidad >= 20:
        return precio_base * 0.90  # 10% descuento
    elif cantidad >= 10:
        return precio_base * 0.95  # 5% descuento
    else:
        return precio_base


def validar_dimensiones(ancho: float, alto: float) -> Tuple[bool, str]:
    """
    Validar dimensiones para un paquete.

    Args:
        ancho: Ancho en mm
        alto: Alto en mm

    Returns:
        Tupla con (es_valido, mensaje)
    """
    if ancho <= 0 or alto <= 0:
        return False, "Las dimensiones deben ser mayores a 0"

    if ancho > 5000 or alto > 5000:
        return False, "Las dimensiones no pueden exceder 5000mm"

    area_m2 = (ancho * alto) / 1000000
    if area_m2 > 25:
        return False, f"El área no puede exceder 25 m² (actual: {area_m2:.2f} m²)"

    return True, "Dimensiones válidas"


# Exportar funciones principales
__all__ = [
    'calcular_total_presupuesto',
    'validar_estructura_presupuesto',
    'generar_detalle_paquete',
    'calcular_descuento',
    'validar_dimensiones'
]


# Ejemplo de uso
if __name__ == "__main__":
    # Prueba básica del módulo
    print("🔧 Probando calculador_paquetes.py")

    # Datos de prueba
    presupuesto_prueba = {
        'items': [
            {'descripcion': 'Item 1', 'precio_unitario': 100, 'cantidad': 2},
            {'descripcion': 'Item 2', 'precio_unitario': 50, 'cantidad': 3}
        ],
        'iva': 0.16
    }

    # Probar funciones
    resultado = calcular_total_presupuesto(presupuesto_prueba)
    print(f"\n📊 Resultado cálculo total: {resultado}")

    valido, mensaje = validar_estructura_presupuesto(presupuesto_prueba)
    print(f"\n✅ Validación estructura: {valido} - {mensaje}")

    paquete_prueba = {
        'tipo': 'PAQ-AL',
        'clave': 'VENTANA_CORREDIZA',
        'ancho': 1200,
        'alto': 1500,
        'color': 'BLANCO',
        'piezas': 2
    }

    detalle = generar_detalle_paquete(paquete_prueba)
    print(f"\n📦 Detalle paquete: {detalle.get('detalle')}")
    print(f"   Total: ${detalle.get('total', 0):,.2f}")

    print("\n✅ Módulo funcionando correctamente")