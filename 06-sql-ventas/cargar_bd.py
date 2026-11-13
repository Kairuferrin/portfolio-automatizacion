"""Carga las ventas ficticias del proyecto 5 en una base de datos SQLite.

Crea ventas.db con una tabla «ventas»: los datos originales más una
columna importe_eur (el importe ya pasado a euros con el tipo de cambio del
día, reutilizando las funciones del proyecto 5).

Uso:
    python3 cargar_bd.py
"""

import csv
import sqlite3
import sys
from pathlib import Path

CARPETA = Path(__file__).parent
CARPETA_P5 = CARPETA.parent / "05-python-ventas"
ARCHIVO_VENTAS = CARPETA_P5 / "ventas_ficticias.csv"
ARCHIVO_BD = CARPETA / "ventas.db"

# Reutilizamos las funciones de conversión del proyecto 5 en vez de copiarlas.
# sys.path es la lista de carpetas donde Python busca código para importar:
# añadimos la del proyecto 5 para poder importar su archivo resumen_ventas.py.
sys.path.insert(0, str(CARPETA_P5))
# (El comentario «noqa» solo le dice al revisor de estilo que este import
# va aquí abajo a propósito, después de añadir la carpeta.)
from resumen_ventas import a_euros, descargar_tipos_de_cambio  # noqa: E402

CREAR_TABLA = """
CREATE TABLE ventas (
    fecha               TEXT,     -- AAAA-MM-DD
    pedido              TEXT,
    producto            TEXT,
    talla               TEXT,
    unidades            INTEGER,
    precio_unitario     REAL,     -- en la moneda del pedido
    moneda              TEXT,     -- EUR, USD o GBP
    coste_unitario_eur  REAL,
    devuelto            INTEGER,  -- 1 = sí, 0 = no
    importe_eur         REAL      -- unidades × precio, pasado a euros
)
"""


def main():
    if not ARCHIVO_VENTAS.exists():
        sys.exit("Falta el CSV del proyecto 5. Ejecuta antes: "
                 f"python3 {CARPETA_P5 / 'generar_datos.py'}")

    tipos = descargar_tipos_de_cambio()
    fechas_ordenadas = sorted(tipos)

    filas = []
    with ARCHIVO_VENTAS.open(encoding="utf-8") as f:
        for v in csv.DictReader(f):
            unidades = int(v["unidades"])
            precio = float(v["precio_unitario"])
            importe_eur = a_euros(unidades * precio, v["moneda"], v["fecha"],
                                  tipos, fechas_ordenadas)
            filas.append((
                v["fecha"], v["pedido"], v["producto"], v["talla"], unidades,
                precio, v["moneda"], float(v["coste_unitario_eur"]),
                1 if v["devuelto"] == "sí" else 0, round(importe_eur, 2),
            ))

    # Empezamos de cero cada vez, para que el resultado sea siempre el mismo.
    ARCHIVO_BD.unlink(missing_ok=True)
    # El «with» guarda los cambios (commit) al terminar el bloque, pero en
    # sqlite3 no cierra la conexión: por eso hacemos close() justo después.
    with sqlite3.connect(ARCHIVO_BD) as conexion:
        conexion.execute(CREAR_TABLA)
        conexion.executemany(
            "INSERT INTO ventas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", filas)
    conexion.close()

    print(f"Creada {ARCHIVO_BD.name} con {len(filas)} ventas en la tabla «ventas».")


if __name__ == "__main__":
    main()
