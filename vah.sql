USE aluminio

SELECT * FROM materiales_aluminio
SELECT * FROM paquete_aluminio_items
select * from paquetes_aluminio
select * from tipos_item

Use clientes

select * from cat_anodizado
select * from cat_tipo_partida
select * from cat_unidad
select * from clientes
select * from 
select * from 
select * from 
select * from 

DROP TABLE 

use herrajes

select * from materiales_herraje
select * from paquete_herraje_items
select * from paquetes_herrajes

use herreria

select * from materiales_herreria

use otros

select * from materiales_otros

use plasticos

select * from materiales_plasticos

use proveedores

select * from proveedores

use vah

select * from presupuestos

use vidrio

select * from materiales_vidrio





-- Información general de todas las tablas
SELECT 
    s.name AS Esquema,
    t.name AS Tabla,
    t.create_date AS Fecha_Creacion,
    t.modify_date AS Fecha_Modificacion,
    p.rows AS Filas,
    SUM(a.total_pages) * 8 / 1024 AS Tamanio_MB
FROM sys.tables t
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
INNER JOIN sys.indexes i ON t.object_id = i.object_id
INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE t.is_ms_shipped = 0
    AND i.object_id > 255
GROUP BY s.name, t.name, t.create_date, t.modify_date, p.rows
ORDER BY s.name, t.name;


-- Columnas detalladas de cada tabla
SELECT 
    s.name AS Esquema,
    t.name AS Tabla,
    c.name AS Columna,
    ty.name AS Tipo_Dato,
    c.max_length AS Longitud,
    c.precision AS Precision,
    c.scale AS Escala,
    CASE WHEN c.is_nullable = 1 THEN 'SI' ELSE 'NO' END AS Permite_Null,
    CASE WHEN c.is_identity = 1 THEN 'SI' ELSE 'NO' END AS Es_Identidad,
    ISNULL(dc.definition, '') AS Valor_Default,
    ISNULL(pk.is_primary_key, 'NO') AS Es_PK,
    ISNULL(fk.is_foreign_key, 'NO') AS Es_FK
FROM sys.tables t
INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
INNER JOIN sys.columns c ON t.object_id = c.object_id
INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
LEFT JOIN (
    SELECT ic.object_id, ic.column_id, 'SI' AS is_primary_key
    FROM sys.indexes i
    INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    WHERE i.is_primary_key = 1
) pk ON t.object_id = pk.object_id AND c.column_id = pk.column_id
LEFT JOIN (
    SELECT fc.parent_object_id, fc.parent_column_id, 'SI' AS is_foreign_key
    FROM sys.foreign_key_columns fc
) fk ON t.object_id = fk.parent_object_id AND c.column_id = fk.parent_column_id
WHERE t.is_ms_shipped = 0
ORDER BY s.name, t.name, c.column_id;












delete from ;

-- ALUMINIO: confirma que la columna del color tenga valor > 0
SELECT sa, nat, bmo, e100, e200, e400, bco, hue, gris, cho, ace, madl, madt, np
FROM aluminio.dbo.materiales_aluminio
WHERE UPPER(clave)=UPPER('7333');  -- ← cambia '7333' por tu clave AL

-- HERRERÍA: confirma que exista kg/m
SELECT kilogramos
FROM herreria.dbo.materiales_herreria
WHERE UPPER(Clave)=UPPER('P001');  -- ← cambia por una clave HE de tu paquete

-- HERRAJES: confirma P.U.
SELECT Precio
FROM herrajes.dbo.materiales_herraje
WHERE UPPER(Clave)=UPPER('PINSTG');  -- ← clave HR de tu paquete

-- VIDRIO/PLÁSTICOS/OTROS (según uses)
SELECT Precio FROM vidrio.dbo.materiales_vidrio WHERE UPPER(Clave)=UPPER('CC6');
SELECT Precio FROM plasticos.dbo.materiales_plasticos WHERE UPPER(Clave)=UPPER('P002');
SELECT Precio FROM otros.dbo.materiales_otros WHERE UPPER(Clave)=UPPER('P001');


