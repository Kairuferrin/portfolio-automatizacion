"""Genera ventas FICTICIAS de una pequeña marca de ropa online (año 2025).

Los datos son inventados a propósito, solo para practicar. No pertenecen a
ninguna empresa real.

Uso:
    python3 generar_datos.py
Crea el archivo ventas_ficticias.csv en esta misma carpeta.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

# Semilla fija: cada vez que se ejecuta salen exactamente los mismos datos.
random.seed(42)

# Catálogo ficticio: precio de venta y coste de fabricación, en euros.
PRODUCTOS = {
    "Camiseta": {"precio": 25, "coste": 8},
    "Sudadera": {"precio": 55, "coste": 20},
    "Pantalón": {"precio": 60, "coste": 22},
    "Vestido": {"precio": 70, "coste": 25},
    "Chaqueta": {"precio": 95, "coste": 38},
}
TALLAS = ["XS", "S", "M", "L", "XL"]

# Pedidos por día según el mes (más en Navidad, menos en febrero). Inventado.
PEDIDOS_POR_DIA = {1: 3, 2: 2, 3: 3, 4: 3, 5: 4, 6: 4,
                   7: 3, 8: 2, 9: 4, 10: 4, 11: 6, 12: 7}

# Moneda en la que paga el cliente: (moneda, probabilidad, factor de precio).
# El factor convierte el precio en euros al precio en esa moneda:
# una camiseta de 25 € cuesta 25 × 1,1 = 27,50 $ o 25 × 0,85 = 21,25 £.
MONEDAS = [("EUR", 0.80, 1.0), ("USD", 0.12, 1.1), ("GBP", 0.08, 0.85)]

PROBABILIDAD_DEVOLUCION = 0.08


def elegir_moneda():
    """Elige la moneda del pedido según las probabilidades de MONEDAS."""
    r = random.random()
    acumulado = 0.0
    for moneda, prob, factor in MONEDAS:
        acumulado += prob
        if r < acumulado:
            return moneda, factor
    return MONEDAS[0][0], MONEDAS[0][2]


def main():
    destino = Path(__file__).with_name("ventas_ficticias.csv")
    filas = []
    numero_pedido = 1000
    dia = date(2025, 1, 1)

    while dia.year == 2025:
        media = PEDIDOS_POR_DIA[dia.month]
        pedidos_hoy = max(0, round(random.gauss(media, 1)))
        for _ in range(pedidos_hoy):
            numero_pedido += 1
            moneda, factor = elegir_moneda()
            producto = random.choice(list(PRODUCTOS))
            datos = PRODUCTOS[producto]
            filas.append({
                "fecha": dia.isoformat(),
                "pedido": f"#{numero_pedido}",
                "producto": producto,
                "talla": random.choice(TALLAS),
                "unidades": random.choice([1, 1, 1, 2, 2, 3]),
                "precio_unitario": round(datos["precio"] * factor, 2),
                "moneda": moneda,
                "coste_unitario_eur": datos["coste"],
                "devuelto": "sí" if random.random() < PROBABILIDAD_DEVOLUCION else "no",
            })
        dia += timedelta(days=1)

    with destino.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"Creado {destino.name} con {len(filas)} líneas de venta (ficticias).")


if __name__ == "__main__":
    main()
