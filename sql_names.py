# D:\vah\presupuestos\sql_names.py
# Utilidad única para formar nombres de tablas dentro de la BD activa (vah)
DB_DEFAULT = "vah"   # Solo informativo; NO se usa en el nombre
SCHEMA     = "dbo"

TABLES = {
    "AL":      "materiales_aluminio",
    "PAQ-AL":  "paquetes_aluminio",
    "HR":      "materiales_herraje",
    "PAQ-HR":  "paquetes_herrajes",
    "HE":      "materiales_herreria",
    "OT":      "materiales_otros",
    "PL":      "materiales_plasticos",
    "VI":      "materiales_vidrio",
}

# devuelve un nombre seguro de 2 partes: [dbo].[tabla]
def qname(table_key_or_name: str) -> str:
    name = TABLES.get(table_key_or_name.upper(), table_key_or_name)
    return f"[{SCHEMA}].[{name}]"
