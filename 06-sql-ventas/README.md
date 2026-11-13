# Proyecto 6 · Preguntas de negocio con SQL

> ⚠️ **Datos ficticios.** Son las mismas ventas inventadas del [proyecto 5](../05-python-ventas/).

## El problema
Un CSV sirve para guardar ventas, pero no para hacerles preguntas rápidas. ¿Qué talla se devuelve más? ¿En qué moneda nos pagan? ¿Sube el ticket medio en Navidad? Responder a cada una a mano en Excel lleva tiempo.

## La solución
1. **`cargar_bd.py`** guarda las ventas en una base de datos **SQLite** (`ventas.db`), un único archivo que no necesita servidor. Añade la columna `importe_eur` reutilizando las funciones de conversión del proyecto 5, sin copiar el código.
2. **`consultas.sql`** contiene 5 preguntas de negocio escritas en **SQL**.

## Cómo usarlo
```bash
python3 ../05-python-ventas/generar_datos.py   # solo si no existe el CSV
python3 cargar_bd.py
sqlite3 ventas.db < consultas.sql
```

## Resultados (con los datos ficticios)
| Pregunta | Respuesta |
|---|---|
| 1. Ingresos netos por mes | Coinciden con el proyecto 5. Diciembre es el mejor mes: 19.196 € |
| 2. Productos con más unidades vendidas | Chaqueta (475), Vestido (461), Camiseta (455) |
| 3. Tallas más devueltas | La M (9,0 % de líneas) y la L (8,5 %); la XS es la que menos (5,8 %) |
| 4. Monedas de pago | EUR 80,3 %, USD 10,3 %, GBP 9,4 % |
| 5. Ticket medio bruto por trimestre (incluye pedidos devueltos) | Entre 100,63 € (T4) y 108,58 € (T3) |

En la pregunta 1 puede haber diferencias de ±0,02 € con el proyecto 5, porque aquí cada venta se redondea a céntimos antes de sumar.

## Qué he aprendido
- **SQL** = hacer preguntas a una tabla: `SELECT` (qué columnas), `FROM` (de qué tabla), `WHERE` (filtrar filas), `GROUP BY` (agrupar, como una tabla dinámica), `ORDER BY` (ordenar) y `LIMIT` (quedarme con las primeras).
- **Funciones de resumen:** `SUM`, `COUNT`, `ROUND` y `COUNT(DISTINCT ...)` para contar pedidos sin repetir.
- **`CASE WHEN`:** un «si… entonces…» dentro de la consulta, como la función SI de Excel.
- **Subconsulta:** una consulta dentro de otra, para calcular porcentajes sobre el total.
- **Reutilizar código** importando funciones de otro proyecto en vez de copiarlas.
