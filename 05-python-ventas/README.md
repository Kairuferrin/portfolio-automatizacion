# Proyecto 5 · Resumen mensual de ventas con Python

> ⚠️ **Datos ficticios.** Las ventas de este proyecto las genera un script a propósito para practicar. No pertenecen a ninguna empresa real.

## El problema
El «director financiero de bolsillo» del [proyecto 1](../01-mapa-proceso/) necesita, cada mes, los números de la marca de ropa: ingresos, devoluciones, margen y comparación con el mes anterior. Calcularlos a mano en Excel es lento, y algunas ventas llegan en dólares o en libras.

## La solución
Dos scripts de Python que solo usan la biblioteca estándar (no hay que instalar nada):

1. **`generar_datos.py`** crea `ventas_ficticias.csv`: unas 1.400 líneas de venta de 2025 con fecha, pedido, producto, talla, unidades, precio, moneda, coste y si se devolvió. Usa una semilla fija, así que cada ejecución genera exactamente los mismos datos.
2. **`resumen_ventas.py`**:
   - pasa a euros las ventas en USD y GBP con el tipo de cambio de **ese mismo día**, usando la API del [proyecto 2](../02-api-json/) con una sola petición para todo el año;
   - calcula por mes los ingresos netos, las devoluciones (en € y en %), el coste, el margen (en € y en %) y la variación frente al mes anterior;
   - ordena los productos según lo que facturan;
   - guarda el resultado en `resumen_mensual.csv`, que usará el proyecto 6.

## Cómo usarlo
```bash
python3 generar_datos.py
python3 resumen_ventas.py
```

## Resultado (con los datos ficticios)
```
Mes        Ingresos    Devol.  %Dev     Margen  %Marg  vs ant.
2025-01     9084.93    555.16  9.7%    5713.93  62.9%        —
2025-02     5146.94     95.00  1.9%    3287.94  63.9%   -43.3%
...
2025-11    16642.02   1186.56  7.3%   10396.02  62.5%   +31.6%
2025-12    19196.02   1971.00 10.2%   12086.02  63.0%   +15.3%
```
La chaqueta es el producto que más factura y la camiseta el que menos.

## Decisiones tomadas
- **Devoluciones:** se restan de los ingresos, y su coste no se cuenta porque la prenda vuelve al almacén. Es una suposición: tampoco se cuentan gastos de envío ni pérdidas.
- **Tasa de devolución:** porcentaje de líneas de pedido devueltas, no de unidades ni de euros.
- **Fines de semana y festivos:** como no hay tipo de cambio oficial esos días, se usa el del último día hábil anterior.

## Qué he aprendido
- **Leer y escribir CSV** con `csv.DictReader` y `csv.DictWriter`: cada fila es una ficha con casillas.
- **Agrupar por mes** con `defaultdict`, como una tabla dinámica de Excel.
- **Llamar a una API desde Python** con `urllib`, y qué hacer si falla la conexión.
- **Funciones:** dividir el trabajo en recetas pequeñas con nombre (`a_euros`, `tipo_del_dia`).
