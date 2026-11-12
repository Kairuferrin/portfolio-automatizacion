# Proyecto 2 · Pedir datos a una API y leer el JSON

## El problema
La marca de ropa del [proyecto 1](../01-mapa-proceso/) vende también fuera de la zona euro. Para el informe mensual necesita pasar a euros las ventas cobradas en dólares (USD) o en libras (GBP). Hacerlo a mano significa buscar el tipo de cambio cada vez.

## La solución
Pedir el tipo de cambio a una **API** pública y gratuita, [Frankfurter](https://frankfurter.dev). Publica los tipos de referencia del Banco Central Europeo y no necesita registro ni clave.

- **API:** la ventanilla por la que un programa pide datos a otro.
- **Endpoint:** la dirección concreta de esa ventanilla (una URL).
- **JSON:** el formato en el que vuelve la respuesta. Son pares `"nombre": valor`, como una ficha con casillas.

## Cómo usarlo

### 1. Tipo de cambio de hoy
```bash
curl "https://api.frankfurter.dev/v1/latest?base=EUR&symbols=USD,GBP"
```
Respuesta real (12-11-2026):
```json
{"amount":1.0,"base":"EUR","date":"2026-11-12","rates":{"GBP":0.83595,"USD":1.1081}}
```
Cómo leerla: 1 € = 1,1081 $ y 1 € = 0,83595 £.

### 2. Tipos de cambio de un mes entero (para el informe mensual)
```bash
curl "https://api.frankfurter.dev/v1/2026-10-01..2026-10-31?base=EUR&symbols=USD"
```
Devuelve un tipo por cada día hábil. Por ejemplo, el 1 de octubre de 2026 era `"USD":1.1298`.

## Qué he aprendido
- La URL lleva **parámetros** después del `?`: `base=EUR` (la moneda de partida) y `symbols=USD,GBP` (las monedas que quiero).
- El JSON tiene **casillas dentro de casillas**: `rates` contiene `USD` y `GBP`.
- En el proyecto 1, el paso «recoger datos de Shopify» funcionará igual: una URL, unos parámetros y una respuesta en JSON. La diferencia es que Shopify pide una clave, porque sus datos son privados.
