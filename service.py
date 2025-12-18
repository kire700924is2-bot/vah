# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/service.py  (Revisión con mapeo de BD corregido)
--------------------------------------------------------------------
- Router por TIPO → (DB, tabla) alineado a tu entorno
- Métodos completos para paquetes de aluminio y herrajes
- Componentes con claves reales de materiales desde BD
- Búsqueda robusta con manejo de errores
"""

from __future__ import annotations
import os, contextlib
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import pyodbc
except Exception:
    pyodbc = None  # type: ignore

# =========================
# Conexión
# =========================

ENV_SERVER = os.environ.get("VAH_SQLSERVER", "").strip()
CANDIDATE_SERVERS = [
    ENV_SERVER or "",
    r"DESKTOP-AE60PIU\SQLEXPRESS",
    r"(local)\SQLEXPRESS",
    r".\SQLEXPRESS",
    r"localhost\SQLEXPRESS",
    r"127.0.0.1,1433",
]

# =========================
# Mapa de BD y tablas
# =========================

DBS = {
    "ALUMINIO": "aluminio",
    "HERRAJES": "herrajes",
    "HERRERIA": "herreria",
    "OTROS": "otros",
    "CLIENTES": "clientes",
    "VIDRIO": "vidrio",
    "PLASTICOS": "plasticos",
}


def T(dbkey: str, table: str) -> str:
    return f"[{DBS[dbkey]}].dbo.{table}"


TABLES = {
    # Materiales por tipo
    "ALUMINIO": T("ALUMINIO", "materiales_aluminio"),
    "HERRAJES": T("HERRAJES", "materiales_herraje"),
    "HERRERIA": T("HERRERIA", "materiales_herreria"),
    "VIDRIO": T("VIDRIO", "materiales_vidrio"),
    "PLASTICOS": T("PLASTICOS", "materiales_plasticos"),
    "OTROS": T("OTROS", "materiales_otros"),

    # Paquetes (cabeceras e items) en sus BD correctas
    "PAQ_AL_HEAD": T("ALUMINIO", "paquetes_aluminio"),
    "PAQ_AL_ITEMS": T("ALUMINIO", "paquete_aluminio_items"),
    "PAQ_HR_HEAD": T("HERRAJES", "paquetes_herrajes"),
    "PAQ_HR_ITEMS": T("HERRAJES", "paquete_herraje_items"),

    # Clientes
    "CLIENTES": T("CLIENTES", "clientes"),
}

COLS = {
    "AL": {"clave": "clave", "descripcion": "descripcion", "largo": "largo"},
    "AL_COLOR_MAP": {
        "NATURAL": "nat", "BLANCO": "bco", "E-100": "e100", "E-200": "e200", "E-400": "e400",
        "BRONCE": "bmo", "HUESO": "hue", "GRIS": "gris", "CHOCOLATE": "cho", "N.P.": "np",
        "ACERO": "ace", "MADERA LISA": "madl", "MADERA TEXTURIZADA": "madt"
    },
    "VI": {"clave": "clave", "descripcion": "descripcion", "precio_m2": "precio"},
    "HE": {"clave": "clave", "descripcion": "descripcion", "kg_m": "kilogramos"},
    "PL": {"clave": "clave", "descripcion": "descripcion", "precio": "precio"},
    "OT": {"clave": "clave", "descripcion": "descripcion", "precio": "precio"},
    "HR": {"clave": "clave", "descripcion": "descripcion", "precio": "precio"},

    "PAQ_AL": {"paquete": "clave_paquete", "tipo": "tipo", "clave": "clave",
               "horizontal": "horizontal", "vertical": "vertical", "cantidad": "cantidad"},
    "PAQ_HR": {"paquete": "clave_paquete", "clave": "clv_herraje", "cantidad": "cantidad"},
}

COLS_CLIENTES = {
    "id": "id",
    "titulo": "titulo",
    "nombre": "nombre",
    "a_paterno": "a_paterno",
}

GENERIC_PRICE = {
    "HR": ("HERRAJES", "precio"),
    "PL": ("PLASTICOS", "precio"),
    "OT": ("OTROS", "precio"),
    "VI": ("VIDRIO", "precio"),
}


# =========================
# Servicio
# =========================

class Service:
    def __init__(self) -> None:
        self._cnx: Optional["pyodbc.Connection"] = None  # type: ignore

    # ---------- Conexión ----------
    def connect(self):
        if self._cnx:
            return self._cnx
        if pyodbc is None:
            raise RuntimeError("pyodbc no disponible. Instala ODBC Driver 17/18 for SQL Server.")

        errors: List[str] = []
        for driver in ("{ODBC Driver 18 for SQL Server}", "{ODBC Driver 17 for SQL Server}"):
            for server in [s for s in CANDIDATE_SERVERS if s]:
                try:
                    cnx_str = (
                        f"DRIVER={driver};"
                        f"SERVER={server};"
                        "Encrypt=no;"
                        "TrustServerCertificate=yes;"
                        "Trusted_Connection=yes;"
                        "Connection Timeout=4;"
                    )
                    self._cnx = pyodbc.connect(cnx_str)
                    return self._cnx
                except Exception as e:
                    errors.append(f"{driver}@{server}: {e}")

        raise RuntimeError("No se pudo conectar a SQL Server. Intentos: " + " | ".join(errors))

    @contextlib.contextmanager
    def cursor(self):
        cnx = self.connect()
        cur = cnx.cursor()
        try:
            yield cur
        finally:
            cur.close()

    def _fetchone(self, sql: str, params: Iterable[Any]) -> Optional[tuple]:
        with self.cursor() as cur:
            cur.execute(sql, list(params))
            return cur.fetchone()

    def _fetchall(self, sql: str, params: Iterable[Any]) -> List[tuple]:
        with self.cursor() as cur:
            cur.execute(sql, list(params))
            return list(cur.fetchall())

    # =========================
    #   Búsqueda (Filtro)
    # =========================

    def _like_parts(self, buscar_por: str, filtro: str) -> Tuple[str, List[Any], str]:
        """
        Devuelve (where, params, order) con CI_AI:
        - CLAVE -> prefijo LIKE 'X%'
        - DESC  -> contiene LIKE '%X%'
        """
        bp = (buscar_por or "CLAVE").strip().upper()
        is_clave = bp.startswith("CLAVE")
        if is_clave:
            return " {col} COLLATE Latin1_General_CI_AI LIKE ? ", [f"{filtro}%"], " {col} "
        else:
            return " {col} COLLATE Latin1_General_CI_AI LIKE ? ", [f"%{filtro}%"], " {col} "

    def buscar_por_tabla(
            self, *, tabla: str, buscar_por: str, filtro: str,
            database: Optional[str] = None, top: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda directa por tabla (la usa el módulo).
        Acepta 'tabla' con o sin schema y puede inferir la BD por coincidencia.
        """
        if not tabla:
            return []
        filtro = (filtro or "").strip()
        if not filtro:
            return []

        # Resolver database si no viene (buscamos por 'cola' de la tabla en TABLES)
        if database is None:
            tail = tabla.split(".")[-1].lower()
            for _k, full in TABLES.items():
                if full.lower().endswith(f".{tail}"):
                    database = full.split("].")[0].lstrip("[").strip()
                    break

        if database:
            schema_tail = tabla.split(".")[-1]
            tabla_full = f"[{database}].dbo.{schema_tail}"
        else:
            tabla_full = tabla  # asumimos que ya viene como [db].dbo.<tabla> o dbo.<tabla>

        col_clave, col_desc = "clave", "descripcion"
        where_tpl, params, order_tpl = self._like_parts(buscar_por, filtro)
        col = col_clave if (buscar_por or "").upper().startswith("CLAVE") else col_desc

        sql = (
                f"SELECT TOP ({int(top)}) {col_clave}, {col_desc} "
                f"FROM {tabla_full} "
                f"WHERE " + where_tpl.format(col=col) +
                " ORDER BY " + order_tpl.format(col=("clave" if col == col_clave else "descripcion"))
        )

        rows = self._fetchall(sql, params)
        return [{"clave": str(r[0]).strip(), "descripcion": str(r[1]).strip()} for r in rows] if rows else []

    def buscar_por_tipo(self, *, tipo: str, buscar_por: str, filtro: str) -> List[Dict[str, Any]]:
        """
        Usa el router TIPO→TABLA correcto (BD real de tu servidor).
        """
        tipo_up = (tipo or "").strip().upper()
        if tipo_up == "ALUMINIO":
            table = TABLES["ALUMINIO"]
        elif tipo_up == "PAQUETE ALUMINIO":
            table = TABLES["PAQ_AL_HEAD"]
        elif tipo_up in {"HERRERIA", "HERRERÍA"}:
            table = TABLES["HERRERIA"]
        elif tipo_up == "VIDRIO":
            table = TABLES["VIDRIO"]
        elif tipo_up in {"PLASTICOS", "PLÁSTICOS"}:
            table = TABLES["PLASTICOS"]
        elif tipo_up == "HERRAJES":
            table = TABLES["HERRAJES"]
        elif tipo_up == "PAQUETE HERRAJES":
            table = TABLES["PAQ_HR_HEAD"]
        elif tipo_up == "OTROS":
            table = TABLES["OTROS"]
        else:
            return []

        # Extraemos la BD para forzarla en la consulta
        database = table.split("].")[0].lstrip("[").strip()
        tabla_tail = table.split(".")[-1]
        return self.buscar_por_tabla(tabla=tabla_tail, buscar_por=buscar_por, filtro=filtro, database=database, top=100)

    # =========================
    #   Clientes
    # =========================

    def clientes_buscar(self, filtro: str) -> List[Dict[str, Any]]:
        """
        Busca clientes en la base de datos [clientes].dbo.clientes.
        """
        text = (filtro or "").strip()
        if not text:
            return []

        like = f"%{text}%"
        sql = (
            "SELECT TOP (80) id, titulo, nombre, a_paterno "
            "FROM [clientes].dbo.clientes "
            "WHERE titulo   COLLATE Latin1_General_CI_AI LIKE ? "
            "   OR nombre   COLLATE Latin1_General_CI_AI LIKE ? "
            "   OR a_paterno COLLATE Latin1_General_CI_AI LIKE ? "
            "ORDER BY nombre ASC, a_paterno ASC, titulo ASC"
        )

        rows = self._fetchall(sql, [like, like, like])
        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append({
                "id": r[0],
                "titulo": r[1],
                "nombre": r[2],
                "a_paterno": r[3],
                "display": f"{r[1]} {r[2]} {r[3]}".strip()
            })
        return out

    # =========================
    #   Precios / Materiales
    # =========================

    # --- ALUMINIO ---
    def aluminio_largo(self, clave: str) -> Optional[float]:
        t = TABLES["ALUMINIO"];
        c = COLS["AL"]
        sql = f"SELECT {c['largo']} FROM {t} WHERE {c['clave']} = ?"
        row = self._fetchone(sql, [clave])
        return float(row[0]) if row and row[0] is not None else None

    def aluminio_precio(self, clave: str, color: Optional[str]) -> Optional[float]:
        t = TABLES["ALUMINIO"];
        c = COLS["AL"];
        cmap = COLS["AL_COLOR_MAP"]
        if not color:
            cols = ", ".join(cmap.values())
            sql = f"SELECT {cols} FROM {t} WHERE {c['clave']} = ?"
            row = self._fetchone(sql, [clave])
            if not row:
                return None
            for val in row:
                try:
                    if val is not None and float(val) > 0:
                        return float(val)
                except Exception:
                    pass
            return None
        col = cmap.get((color or "").strip().upper())
        if not col:
            return None
        sql = f"SELECT {col} FROM {t} WHERE {c['clave']} = ?"
        row = self._fetchone(sql, [clave])
        return float(row[0]) if row and row[0] is not None else None

    # --- VIDRIO ---
    def vidrio_precio(self, clave: str) -> Optional[float]:
        t = TABLES["VIDRIO"];
        c = COLS["VI"]
        sql = f"SELECT {c['precio_m2']} FROM {t} WHERE {c['clave']} = ?"
        row = self._fetchone(sql, [clave])
        return float(row[0]) if row and row[0] is not None else None

    # --- HERRERÍA ---
    def herreria_kg_por_m(self, clave: str) -> Optional[float]:
        t = TABLES["HERRERIA"];
        c = COLS["HE"]
        sql = f"SELECT {c['kg_m']} FROM {t} WHERE {c['clave']} = ?"
        row = self._fetchone(sql, [clave])
        return float(row[0]) if row and row[0] is not None else None

    # --- PLÁSTICOS / OTROS / HERRAJES ---
    def plasticos_precio(self, clave: str) -> Optional[float]:
        t = TABLES["PLASTICOS"];
        c = COLS["PL"]
        sql = f"SELECT {c['precio']} FROM {t} WHERE {c['clave']} = ?"
        row = self._fetchone(sql, [clave])
        return float(row[0]) if row and row[0] is not None else None

    def otros_precio(self, clave: str) -> Optional[float]:
        t = TABLES["OTROS"];
        c = COLS["OT"]
        sql = f"SELECT {c['precio']} FROM {t} WHERE {c['clave']} = ?"
        row = self._fetchone(sql, [clave])
        return float(row[0]) if row and row[0] is not None else None

    def herrajes_precio(self, clave: str) -> Optional[float]:
        t = TABLES["HERRAJES"];
        c = COLS["HR"]
        sql = f"SELECT {c['precio']} FROM {t} WHERE {c['clave']} = ?"
        row = self._fetchone(sql, [clave])
        return float(row[0]) if row and row[0] is not None else None

    def _resolve_cols_paquete_al_items(self) -> Dict[str, str]:
        """
        Detecta los nombres REALES de columnas en aluminio.dbo.paquete_aluminio_items
        """
        table_full = TABLES["PAQ_AL_ITEMS"]
        db = table_full.split("].")[0].lstrip("[").strip()
        table_name = table_full.split(".")[-1]

        sql_cols = f"""
        SELECT COLUMN_NAME
        FROM [{db}].INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=?;
        """
        cols = set(x[0].lower() for x in self._fetchall(sql_cols, [table_name]))

        def pick(*cands: str) -> Optional[str]:
            for c in cands:
                if c and c.lower() in cols:
                    return c
            return None

        m: Dict[str, Optional[str]] = {}
        m["paquete"] = pick("clave_paquete", "clv_paquete", "paquete")
        m["tipo"] = pick("tipo", "tp", "tipo_item")
        m["clave"] = pick("clave", "clv_item", "clv_material", "clv_aluminio", "clv", "clave_item")
        m["horizontal"] = pick("horizontal", "cant_ancho", "h", "hor", "horiz")
        m["vertical"] = pick("vertical", "cant_alto", "v", "ver", "vert")
        m["cantidad"] = pick("cantidad", "cant", "qty", "piezas")

        required = ("paquete", "clave", "cantidad")
        if any(m[k] is None for k in required):
            faltantes = [k for k in required if m[k] is None]
            raise RuntimeError(
                "paquete_aluminio_items: columnas requeridas no encontradas: "
                + ", ".join(faltantes) + f".\nColumnas reales: " + str(sorted(cols))
            )

        return {k: v or "" for k, v in m.items()}

    def _resolve_cols_paquete_hr_items(self) -> Dict[str, str]:
        """
        Detecta los nombres REALES de columnas en herrajes.dbo.paquete_herraje_items
        """
        table_full = TABLES["PAQ_HR_ITEMS"]
        db = table_full.split("].")[0].lstrip("[").strip()
        table_name = table_full.split(".")[-1]

        sql_cols = f"""
        SELECT COLUMN_NAME
        FROM [{db}].INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=?;
        """
        cols = set(x[0].lower() for x in self._fetchall(sql_cols, [table_name]))

        def pick(*cands: str) -> Optional[str]:
            for c in cands:
                if c and c.lower() in cols:
                    return c
            return None

        m: Dict[str, Optional[str]] = {}
        m["paquete"] = pick("clave_paquete", "clv_paquete", "paquete")
        m["clave"] = pick("clave", "clv_herraje", "clv_item", "clv_material", "clv", "clave_item")
        m["cantidad"] = pick("cantidad", "cant", "qty", "piezas")
        m["tipo"] = pick("tipo", "tp", "tipo_item")

        required = ("paquete", "clave", "cantidad")
        if any(m[k] is None for k in required):
            faltantes = [k for k in required if m[k] is None]
            raise RuntimeError(
                "paquete_herraje_items: columnas requeridas no encontradas: "
                + ", ".join(faltantes) + f".\nColumnas reales: " + str(sorted(cols))
            )

        return {k: v or "" for k, v in m.items()}

    # --- PAQUETES (items) --- NUEVOS MÉTODOS MEJORADOS ---

    def paquete_aluminio_items(self, clave_paquete: str) -> List[Dict[str, Any]]:
        """
        Lee items del paquete de aluminio y obtiene descripciones reales desde materiales_aluminio.
        Devuelve: [{"clave": "9083", "descripcion": "PERFIL PRINCIPAL 1\"", "cantidad": 4.0, ...}]
        """
        try:
            # 1. Obtener columnas reales
            cols = self._resolve_cols_paquete_al_items()
            t = TABLES["PAQ_AL_ITEMS"]

            # 2. Construir SELECT
            sel_parts = []
            if cols.get("tipo"):
                sel_parts.append(cols["tipo"])
            else:
                sel_parts.append("NULL AS tipo")
            sel_parts.append(cols["clave"])
            sel_parts.append(cols["horizontal"] if cols.get("horizontal") else "NULL AS horizontal")
            sel_parts.append(cols["vertical"] if cols.get("vertical") else "NULL AS vertical")
            sel_parts.append(cols["cantidad"])
            sel = ", ".join(sel_parts)

            # 3. Consultar items del paquete
            sql = f"SELECT {sel} FROM {t} WHERE {cols['paquete']} = ?"
            rows = self._fetchall(sql, [clave_paquete])

            if not rows:
                return []

            out: List[Dict[str, Any]] = []

            # 4. Para cada componente, obtener descripción real desde materiales_aluminio
            for r in rows:
                idx = 0
                tipo = r[idx];
                idx += 1
                clave = str(r[idx]).strip();
                idx += 1
                horizontal = r[idx];
                idx += 1
                vertical = r[idx];
                idx += 1
                cantidad = r[idx]

                # 5. Buscar descripción real en materiales_aluminio
                descripcion_real = self._buscar_descripcion_material_aluminio(clave)

                # 6. Determinar tipo (si no viene en el paquete, asumir "ALUMINIO")
                tipo_real = str(tipo).strip() if tipo else "ALUMINIO"

                out.append({
                    "tipo": tipo_real,
                    "clave": clave,
                    "descripcion": descripcion_real,
                    "horizontal": None if horizontal is None else float(horizontal),
                    "vertical": None if vertical is None else float(vertical),
                    "cantidad": 0.0 if cantidad is None else float(cantidad),
                })

            return out

        except Exception as e:
            print(f"Error en paquete_aluminio_items: {e}")
            return []

    def paquete_herrajes_items(self, clave_paquete: str) -> List[Dict[str, Any]]:
        """
        Lee items del paquete de herrajes y obtiene descripciones reales desde materiales_herraje.
        Devuelve: [{"clave": "9088", "descripcion": "TORNILLERIA COMPLETA", "cantidad": 1.0, ...}]
        """
        try:
            # 1. Obtener columnas reales
            cols = self._resolve_cols_paquete_hr_items()
            t = TABLES["PAQ_HR_ITEMS"]

            # 2. Construir SELECT
            sel_parts = []
            if cols.get("tipo"):
                sel_parts.append(cols["tipo"])
            else:
                sel_parts.append("'HERRAJES' AS tipo")
            sel_parts.append(cols["clave"])
            sel_parts.append(cols["cantidad"])
            sel = ", ".join(sel_parts)

            # 3. Consultar items del paquete
            sql = f"SELECT {sel} FROM {t} WHERE {cols['paquete']} = ?"
            rows = self._fetchall(sql, [clave_paquete])

            if not rows:
                return []

            out: List[Dict[str, Any]] = []

            # 4. Para cada componente, obtener descripción real desde materiales_herraje
            for r in rows:
                idx = 0
                tipo = r[idx];
                idx += 1
                clave = str(r[idx]).strip();
                idx += 1
                cantidad = r[idx]

                # 5. Buscar descripción real en materiales_herraje
                descripcion_real = self._buscar_descripcion_material_herraje(clave)

                # 6. Determinar tipo (si no viene en el paquete, asumir "HERRAJES")
                tipo_real = str(tipo).strip() if tipo else "HERRAJES"

                out.append({
                    "tipo": tipo_real,
                    "clave": clave,
                    "descripcion": descripcion_real,
                    "horizontal": 0.0,  # No aplica para herrajes
                    "vertical": 0.0,  # No aplica para herrajes
                    "cantidad": 0.0 if cantidad is None else float(cantidad),
                })

            return out

        except Exception as e:
            print(f"Error en paquete_herrajes_items: {e}")
            return []

    def _buscar_descripcion_material_aluminio(self, clave: str) -> str:
        """
        Busca la descripción de un material de aluminio por su clave.
        """
        try:
            t = TABLES["ALUMINIO"]
            sql = f"SELECT descripcion FROM {t} WHERE clave = ?"
            row = self._fetchone(sql, [clave])
            return str(row[0]).strip() if row and row[0] else f"Material {clave}"
        except Exception:
            return f"Material {clave}"

    def _buscar_descripcion_material_herraje(self, clave: str) -> str:
        """
        Busca la descripción de un material de herraje por su clave.
        """
        try:
            t = TABLES["HERRAJES"]
            sql = f"SELECT descripcion FROM {t} WHERE clave = ?"
            row = self._fetchone(sql, [clave])
            return str(row[0]).strip() if row and row[0] else f"Material {clave}"
        except Exception:
            return f"Material {clave}"

    def _buscar_descripcion_material_generico(self, tipo: str, clave: str) -> str:
        """
        Busca descripción de material por tipo genérico.
        """
        try:
            tipo_up = tipo.strip().upper()
            if tipo_up == "ALUMINIO":
                return self._buscar_descripcion_material_aluminio(clave)
            elif tipo_up == "HERRAJES":
                return self._buscar_descripcion_material_herraje(clave)
            elif tipo_up == "VIDRIO":
                t = TABLES["VIDRIO"]
            elif tipo_up in ["HERRERIA", "HERRERÍA"]:
                t = TABLES["HERRERIA"]
            elif tipo_up in ["PLASTICOS", "PLÁSTICOS"]:
                t = TABLES["PLASTICOS"]
            elif tipo_up == "OTROS":
                t = TABLES["OTROS"]
            else:
                return f"Material {clave}"

            sql = f"SELECT descripcion FROM {t} WHERE clave = ?"
            row = self._fetchone(sql, [clave])
            return str(row[0]).strip() if row and row[0] else f"Material {clave}"

        except Exception:
            return f"Material {clave}"

    def paquete_herrajes_precio_total(self, clave_paquete: str) -> Optional[float]:
        """
        Calcula el precio total de un paquete de herrajes.
        """
        t_items = TABLES["PAQ_HR_ITEMS"];
        ci = COLS["PAQ_HR"]
        t_hr = TABLES["HERRAJES"];
        ch = COLS["HR"]
        sql = (f"SELECT SUM(CAST(h.{ch['precio']} AS float) * CAST(i.{ci['cantidad']} AS float)) "
               f"FROM {t_items} i "
               f"JOIN {t_hr} h ON h.{ch['clave']} = i.{ci['clave']} "
               f"WHERE i.{ci['paquete']} = ?")
        row = self._fetchone(sql, [clave_paquete])
        return float(row[0]) if row and row[0] is not None else 0.0

    def try_precio_generico(self, tipo: str, clave: str) -> Optional[float]:
        """
        Intenta obtener precio genérico por tipo de material.
        """
        t = (tipo or "").strip().upper()
        gp = GENERIC_PRICE.get(t)
        if not gp:
            return None
        table_key, colname = gp
        table = TABLES[table_key]
        keycol = COLS[t]["clave"]
        sql = f"SELECT {colname} FROM {table} WHERE {keycol} = ?"
        row = self._fetchone(sql, [clave])
        return float(row[0]) if row and row[0] is not None else None

    def obtener_descripcion_material(self, tipo: str, clave: str) -> str:
        """
        Método público para obtener descripción de material por tipo y clave.
        """
        return self._buscar_descripcion_material_generico(tipo, clave)