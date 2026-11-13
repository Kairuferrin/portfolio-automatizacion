"""Resumen mensual de ventas para el «director financiero de bolsillo».

Lee ventas_ficticias.csv, pasa a euros las ventas en dólares y libras con la
API de tipos de cambio del proyecto 2 y calcula, mes a mes:
ingresos, devoluciones, coste, margen y la variación frente al mes anterior.

Uso:
    python3 resumen_ventas.py
Muestra el resumen en pantalla y lo guarda en resumen_mensual.csv.
"""

import bisect
import csv
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

CARPETA = Path(__file__).parent
ARCHIVO_VENTAS = CARPETA / "ventas_ficticias.csv"
ARCHIVO_RESUMEN = CARPETA / "resumen_mensual.csv"
URL_TIPOS = ("https://api.frankfurter.dev/v1/2025-01-01..2025-12-31"
             "?base=EUR&symbols=USD,GBP")


def descargar_tipos_de_cambio():
    """Pide a la API los tipos de cambio diarios de 2025 (1 EUR = X moneda)."""
    try:
        with urllib.request.urlopen(URL_TIPOS, timeout=20) as respuesta:
            datos = json.load(respuesta)
        # datos["rates"] es una ficha: {"2025-01-02": {"USD": 1.03, "GBP": 0.83}, ...}
        # Con un año entero devuelve un tipo por día hábil (unos 255).
        return datos["rates"]
    except OSError as error:  # sin internet o la API no responde
        sys.exit(f"No se pudo conectar con la API de tipos de cambio: {error}")
    except (ValueError, KeyError) as error:  # la API respondió algo inesperado
        sys.exit(f"La API de tipos de cambio devolvió una respuesta inesperada: {error}")


def tipo_del_dia(tipos, fechas_ordenadas, fecha, moneda):
    """Devuelve el tipo de cambio de ese día o, si no hay (fin de semana o
    festivo), el del último día hábil anterior."""
    posicion = bisect.bisect_right(fechas_ordenadas, fecha) - 1
    if posicion < 0:  # antes del primer día con datos: usamos el primero
        posicion = 0
    return tipos[fechas_ordenadas[posicion]][moneda]


def a_euros(importe, moneda, fecha, tipos, fechas_ordenadas):
    """Convierte un importe a euros. Se divide porque el tipo dice cuántas
    unidades de la otra moneda vale 1 euro (lo vimos en el proyecto 2)."""
    if moneda == "EUR":
        return importe
    return importe / tipo_del_dia(tipos, fechas_ordenadas, fecha, moneda)


def main():
    if not ARCHIVO_VENTAS.exists():
        sys.exit("Falta ventas_ficticias.csv. Ejecuta antes: python3 generar_datos.py")

    tipos = descargar_tipos_de_cambio()
    fechas_ordenadas = sorted(tipos)

    meses = defaultdict(lambda: defaultdict(float))
    por_producto = defaultdict(float)

    with ARCHIVO_VENTAS.open(encoding="utf-8") as f:
        for venta in csv.DictReader(f):
            mes = venta["fecha"][:7]  # "2025-03-14" -> "2025-03"
            unidades = int(venta["unidades"])
            importe = unidades * float(venta["precio_unitario"])
            importe_eur = a_euros(importe, venta["moneda"], venta["fecha"],
                                  tipos, fechas_ordenadas)
            m = meses[mes]
            m["lineas"] += 1
            m["ingresos_brutos"] += importe_eur
            if venta["devuelto"] == "sí":
                m["lineas_devueltas"] += 1
                m["devoluciones"] += importe_eur
            else:
                # Solo cuenta el coste de lo que el cliente se queda.
                # Suposición: una devolución no cuesta nada (ni envío ni
                # pérdida), porque la prenda vuelve al almacén.
                m["coste"] += unidades * float(venta["coste_unitario_eur"])
                por_producto[venta["producto"]] += importe_eur

    filas = []
    anterior = None
    for mes in sorted(meses):
        m = meses[mes]
        netos = m["ingresos_brutos"] - m["devoluciones"]
        margen = netos - m["coste"]
        variacion = (netos - anterior) / anterior * 100 if anterior else None
        filas.append({
            "mes": mes,
            "ingresos_netos_eur": round(netos, 2),
            "devoluciones_eur": round(m["devoluciones"], 2),
            # Tasa de devolución: % de líneas de pedido devueltas (no de unidades ni de euros).
            "tasa_devolucion_pct": round(m["lineas_devueltas"] / m["lineas"] * 100, 1),
            "coste_eur": round(m["coste"], 2),
            "margen_eur": round(margen, 2),
            "margen_pct": round(margen / netos * 100, 1),
            "variacion_vs_mes_anterior_pct": round(variacion, 1) if variacion is not None else "",
        })
        anterior = netos

    with ARCHIVO_RESUMEN.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)

    print("RESUMEN MENSUAL 2025 (datos ficticios, importes en euros)\n")
    print(f"{'Mes':<8} {'Ingresos':>10} {'Devol.':>9} {'%Dev':>5} "
          f"{'Margen':>10} {'%Marg':>6} {'vs ant.':>8}")
    for fila in filas:
        var = fila["variacion_vs_mes_anterior_pct"]
        var_txt = f"{var:+.1f}%" if var != "" else "—"
        print(f"{fila['mes']:<8} {fila['ingresos_netos_eur']:>10.2f} "
              f"{fila['devoluciones_eur']:>9.2f} {fila['tasa_devolucion_pct']:>4.1f}% "
              f"{fila['margen_eur']:>10.2f} {fila['margen_pct']:>5.1f}% {var_txt:>8}")

    print("\nProductos que más facturan (ingresos netos del año):")
    for producto, total in sorted(por_producto.items(), key=lambda x: -x[1]):
        print(f"  {producto:<10} {total:>10.2f} €")

    print(f"\nGuardado en {ARCHIVO_RESUMEN.name}")


if __name__ == "__main__":
    main()
