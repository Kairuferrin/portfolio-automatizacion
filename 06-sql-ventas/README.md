# Project 6 · Business questions with SQL

> ⚠️ **Fictional data.** These are the same made-up sales from [project 5](../05-python-ventas/).

## The problem
A CSV is fine for storing sales, but not for asking them quick questions. Which size gets returned most? What currency do customers pay in? Does the average ticket go up at Christmas? Answering each one by hand in Excel takes time.

## The solution
1. **`cargar_bd.py`** saves the sales in a **SQLite** database (`ventas.db`), a single file that needs no server. It adds the `importe_eur` (amount in euros) column by reusing the conversion functions from project 5, without copying the code.
2. **`consultas.sql`** contains 6 business questions written in **SQL**.

## How to use it
```bash
python3 ../05-python-ventas/generar_datos.py   # only if the CSV doesn't exist
python3 cargar_bd.py
sqlite3 ventas.db < consultas.sql
```

## Results (with the fictional data)
| Question | Answer |
|---|---|
| 1. Net revenue per month | Matches project 5. December is the best month: €19,196 |
| 2. Products with the most units sold | Jacket (475), Dress (461), T-shirt (455) |
| 3. Most returned sizes | M (9.0% of lines) and L (8.5%); XS is the least returned (5.8%) |
| 4. Payment currencies | EUR 80.3%, USD 10.3%, GBP 9.4% |
| 5. Average gross ticket per quarter (includes returned orders) | Between €100.63 (Q4) and €108.58 (Q3). The query labels quarters T1–T4 (`trimestre` = quarter) |
| 6. Most returned product (query written by me) | Trousers (8.8% of lines); the sweatshirt is the least returned (6.3%) |

In question 1 there may be differences of ±€0.02 compared with project 5, because here each sale is rounded to cents before adding up.

## What I learned
- **SQL** = asking a table questions: `SELECT` (which columns), `FROM` (which table), `WHERE` (filter rows), `GROUP BY` (group, like a pivot table), `ORDER BY` (sort) and `LIMIT` (keep only the first ones).
- **Summary functions:** `SUM`, `COUNT`, `ROUND` and `COUNT(DISTINCT ...)` to count orders without repeats.
- **`CASE WHEN`:** an "if… then…" inside the query, like Excel's IF function.
- **Subquery:** a query inside another one, to calculate percentages of the total.
- **Reusing code** by importing functions from another project instead of copying them.
