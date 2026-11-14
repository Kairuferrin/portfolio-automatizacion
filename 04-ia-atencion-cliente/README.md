# Proyecto 4 · Atención al cliente con IA

## El problema
La marca de ropa del [proyecto 1](../01-mapa-proceso/) recibe muchos emails repetidos, sobre todo «¿dónde está mi pedido?» y dudas sobre devoluciones. Contestarlos uno a uno a mano quita horas cada semana.

## La solución
Un flujo de **n8n** con IA (**Google Gemini**):

```mermaid
flowchart LR
    A[Email con la etiqueta Clientes] --> B[IA: clasificar y redactar]
    G[Gemini] -.-> B
    P[Formato de respuesta] -.-> B
    B --> C[Borrador en Gmail]
```

1. **Disparador:** n8n solo lee los emails con la etiqueta `Clientes` y deja en paz el resto del correo.
2. **IA:** Gemini clasifica el email (`donde_esta_mi_pedido`, `devolucion` u `otra`) y redacta una respuesta breve en el idioma del cliente.
3. **Formato de respuesta:** obliga a la IA a contestar siempre con las mismas dos casillas (`categoria` y `respuesta`), para que n8n sepa dónde está cada dato.
4. **Borrador:** la respuesta se guarda como **borrador** en la misma conversación de Gmail. **No se envía sola:** una persona la revisa y pulsa enviar.

**Reglas que sigue la IA:** no inventar fechas, importes ni reembolsos; pedir el número de pedido si falta; mandar las devoluciones al formulario del [proyecto 3](../03-n8n-devoluciones/).

**Ejemplo probado:** el email «Hola, hice el pedido #1023 hace 10 días y aún no me ha llegado» se clasificó como `donde_esta_mi_pedido` y generó un borrador de respuesta.

## Cómo usarlo
1. Ten n8n en marcha y las credenciales de Gmail del [proyecto 3](../03-n8n-devoluciones/).
2. Crea una clave de API de Gemini en [Google AI Studio](https://aistudio.google.com/apikey) y, en n8n, la credencial «Google Gemini(PaLM) Api».
3. En Gmail, crea la etiqueta `Clientes`.
4. Importa [`flujo-atencion-cliente.json`](flujo-atencion-cliente.json). Elige las credenciales en los nodos de Gmail y Gemini, y la etiqueta `Clientes` en el disparador.
5. Ponle la etiqueta `Clientes` a un email de prueba y pulsa **Execute workflow**.

⚠️ **Privacidad:** en el plan gratuito de Gemini, Google usa los datos enviados para mejorar sus productos. Para emails reales de clientes hay que usar un plan de pago.

## Por qué lo hice así
- **El problema:** responder a mano se lleva muchísimo tiempo, y las respuestas suelen ser las mismas. Además, de una empresa seria se espera uniformidad y formalidad en las respuestas, y eso puede fallar si cada una la escribe una persona.
- **Alternativas:** usé la versión estándar y gratuita de Gemini. Hay modelos de IA de pago más potentes que no son muy caros, pero estas respuestas no necesitan tanta potencia: para una pyme basta con un modelo sencillo (eso sí, de pago, por la privacidad; ver abajo).
- **Por qué Gemini:** trabajé todo el proceso dentro del ecosistema de Google, por comodidad y por compatibilidad entre las herramientas.
- **Por qué un borrador y no un envío automático:** para que una persona supervise la respuesta. La IA a veces se equivoca, así que el trabajo humano se centra en el pensamiento crítico: si la respuesta está bien, se envía; si está mal, se modifica.
- **Qué cambiaría en una empresa real:**
  - Lo pondría en la nube en vez de en mi ordenador.
  - Usaría una opción de pago, más privada: la versión gratuita recoge los datos, y aquí serían emails reales de clientes.
  - Delimitaría más qué puede contestar la IA. Cuando no pueda, el borrador lo diría según el caso: si la pregunta tiene que ver con la empresa, que alguien del equipo se pondrá en contacto; si no tiene que ver, aclararlo y decir que no puede darle respuesta.

## Qué he aprendido
- **Sub-nodos:** el modelo de IA y el formato de respuesta se enchufan por debajo del nodo principal.
- **Salida estructurada:** con un ejemplo JSON, la IA siempre responde con las mismas casillas.
- **Humano en el circuito:** la IA prepara el borrador y una persona decide si se envía.
- **Cuotas de la versión gratuita:** Gemini 3.8 Flash permite 20 peticiones al día y los reintentos automáticos también cuentan. Al superarla aparece el error 429.
- **Modelos retirados:** el error 404 indicaba que `gemini-2.5-flash-lite` ya no está disponible para usuarios nuevos y recomendaba `gemini-3.5-flash-lite`. Leer el error entero da la solución.
