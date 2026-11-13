-- 5 preguntas de negocio a la base de datos de ventas (datos ficticios).
-- Uso: sqlite3 ventas.db < consultas.sql

.headers on
.mode column

-- 1. ¿Cuánto ingresamos cada mes, ya descontadas las devoluciones?
SELECT substr(fecha, 1, 7)                                 AS mes,
       ROUND(SUM(CASE WHEN devuelto = 0 THEN importe_eur ELSE 0 END), 2) AS ingresos_netos_eur
FROM ventas
GROUP BY mes
ORDER BY mes;

-- 2. ¿Qué 3 productos venden más unidades (sin contar devoluciones)?
SELECT producto,
       SUM(unidades) AS unidades_vendidas
FROM ventas
WHERE devuelto = 0
GROUP BY producto
ORDER BY unidades_vendidas DESC
LIMIT 3;

-- 3. ¿Qué tallas se devuelven más? (% de líneas de pedido devueltas)
SELECT talla,
       COUNT(*)                                  AS lineas,
       SUM(devuelto)                             AS devueltas,
       ROUND(100.0 * SUM(devuelto) / COUNT(*), 1) AS tasa_devolucion_pct
FROM ventas
GROUP BY talla
ORDER BY tasa_devolucion_pct DESC;

-- 4. ¿En qué monedas nos pagan? (% de la facturación bruta en euros)
SELECT moneda,
       ROUND(SUM(importe_eur), 2)                                          AS facturacion_eur,
       ROUND(100.0 * SUM(importe_eur) / (SELECT SUM(importe_eur) FROM ventas), 1) AS porcentaje
FROM ventas
GROUP BY moneda
ORDER BY facturacion_eur DESC;

-- 5. ¿Cuál es el ticket medio (importe medio por pedido) de cada trimestre?
--    Es el ticket BRUTO: incluye los pedidos que luego se devolvieron,
--    porque mide cuánto gasta el cliente al comprar.
SELECT CASE
         WHEN substr(fecha, 6, 2) BETWEEN '01' AND '03' THEN 'T1'
         WHEN substr(fecha, 6, 2) BETWEEN '04' AND '06' THEN 'T2'
         WHEN substr(fecha, 6, 2) BETWEEN '07' AND '09' THEN 'T3'
         ELSE 'T4'
       END                         AS trimestre,
       COUNT(DISTINCT pedido)      AS pedidos,
       ROUND(SUM(importe_eur) / COUNT(DISTINCT pedido), 2) AS ticket_medio_eur
FROM ventas
GROUP BY trimestre
ORDER BY trimestre;
