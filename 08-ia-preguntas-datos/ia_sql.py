"""Pregunta a tus datos con IA.

Convierte una pregunta en lenguaje normal en una consulta SQL con Gemini,
la ejecuta en modo SOLO LECTURA sobre ventas.db (los datos ficticios del
proyecto 6) y, si se le pide, explica el resultado en una frase.

Solo usa la biblioteca estándar de Python: no hay que instalar nada.
"""

import json
import os
import re
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

CARPETA = Path(__file__).parent
ARCHIVO_BD = CARPETA.parent / "06-sql-ventas" / "ventas.db"
ARCHIVO_CLAVE = CARPETA / ".env"  # aquí guardas tu clave; git no lo sube

MODELO = "gemini-3.5-flash-lite"
URL_GEMINI = ("https://generativelanguage.googleapis.com/v1beta/models/"
              f"{MODELO}:generateContent")
MAX_FILAS = 50  # para no llenar la pantalla con miles de filas

# Lo que significa cada columna. La IA lo necesita para escribir bien el SQL,
# igual que un camarero nuevo necesita la carta antes de tomar nota.
DESCRIPCION_COLUMNAS = """
- fecha: texto AAAA-MM-DD (todas las ventas son de 2025)
- pedido: código del pedido (un pedido puede tener varias líneas)
- producto: nombre de la prenda
- talla: talla de la prenda
- unidades: número de unidades de esa línea
- precio_unitario: precio de una unidad en la moneda del pedido (NO en euros)
- moneda: EUR, USD o GBP
- coste_unitario_eur: coste de una unidad, en euros
- devuelto: 1 si la línea se devolvió, 0 si no
- importe_eur: unidades × precio ya pasado a euros. Úsalo para hablar de euros.
"""


class ErrorIA(Exception):
    """Un error que se puede enseñar tal cual al usuario."""


# ---------------------------------------------------------------- base de datos

def conectar():
    """Abre ventas.db en modo solo lectura.

    Es como un carné de biblioteca que deja leer los libros pero no
    arrancarles páginas: aunque la IA escribiera un DELETE, SQLite lo rechazaría.
    """
    if not ARCHIVO_BD.exists():
        raise ErrorIA("Falta ventas.db. Ejecuta antes: "
                      "python3 ../06-sql-ventas/cargar_bd.py")
    conexion = sqlite3.connect(ARCHIVO_BD.resolve().as_uri() + "?mode=ro",
                               uri=True)
    conexion.execute("PRAGMA query_only = ON")  # segundo candado
    return conexion


def esquema():
    """Describe la tabla para la IA: columnas y valores posibles de las de texto."""
    with conectar() as conexion:
        columnas = [f"{fila[1]} ({fila[2]})" for fila in
                    conexion.execute("PRAGMA table_info(ventas)")]
        valores = {}
        for columna in ("producto", "talla", "moneda"):
            valores[columna] = [fila[0] for fila in conexion.execute(
                f"SELECT DISTINCT {columna} FROM ventas ORDER BY 1")]
    conexion.close()
    texto = "Tabla: ventas\nColumnas: " + ", ".join(columnas) + "\n"
    texto += "Significado:" + DESCRIPCION_COLUMNAS
    for columna, lista in valores.items():
        texto += f"Valores exactos de {columna}: {', '.join(lista)}\n"
    return texto


def es_consulta_segura(sql):
    """Primer filtro: solo una consulta y que sea de lectura (SELECT o WITH)."""
    limpia = sql.strip().rstrip(";").strip()
    if not limpia:
        return False, "La consulta está vacía."
    if ";" in limpia:
        return False, "Solo se permite una consulta cada vez."
    sin_comentarios = re.sub(r"(?s)^(\s*(--[^\n]*|/\*.*?\*/))*\s*", "", limpia)
    if not re.match(r"(?is)^(select|with)\b", sin_comentarios):
        return False, "Solo se permiten consultas de lectura (SELECT)."
    # Un «WITH … DELETE» empieza por WITH: buscamos palabras de escritura
    # fuera de los textos entre comillas.
    palabras = {t.upper() for t in _TOKEN.findall(limpia) if re.fullmatch(r"\w+", t)}
    if palabras & _ESCRITURA:
        return False, "Solo se permiten consultas de lectura (SELECT)."
    return True, ""


def ejecutar(sql):
    """Ejecuta la consulta y devuelve (columnas, filas, si_se_ha_cortado)."""
    segura, motivo = es_consulta_segura(sql)
    if not segura:
        raise ErrorIA(motivo)
    try:
        with conectar() as conexion:
            cursor = conexion.execute(sql.strip().rstrip(";"))
            columnas = [d[0] for d in cursor.description or []]
            filas = cursor.fetchmany(MAX_FILAS + 1)
        conexion.close()
    except sqlite3.Error as error:
        raise ErrorIA(f"SQLite no ha podido ejecutarla: {error}") from error
    cortado = len(filas) > MAX_FILAS
    # Los datos binarios (BLOB) no se pueden enviar como JSON: los pasamos a texto.
    filas = [[v.hex() if isinstance(v, bytes) else v for v in f]
             for f in filas[:MAX_FILAS]]
    return columnas, filas, cortado


# ---------------------------------------------------------------- formato

# Palabras que empiezan una línea nueva. Las de dos palabras van primero.
CLAUSULAS = ["GROUP BY", "ORDER BY", "UNION ALL", "LEFT JOIN", "INNER JOIN",
             "WITH", "SELECT", "FROM", "WHERE", "HAVING", "LIMIT", "UNION",
             "JOIN"]
# Trozos del SQL, cada uno se trata como una pieza que no se corta:
# comentarios, textos y nombres entre comillas, números (también .5 o 1e3),
# nombres («tabla.columna»), paréntesis y comas, y operadores (=, *, <>…).
_TOKEN = re.compile(
    r"--[^\n]*|/\*.*?\*/"                          # comentarios
    r"|[xX]'[0-9A-Fa-f]*'"                          # x'41' (datos binarios)
    r"|'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\""          # 'texto' y "nombre"
    r"|`[^`]*`|\[[^\]]*\]"                          # `nombre` y [nombre]
    r"|(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"        # números
    r"|\w+(?:\.\w+)*|[(),;]"
    r"|[^\s\w(),;'\"`\[]+", re.S)
_ESCRITURA = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE",
              "ATTACH", "DETACH", "PRAGMA", "VACUUM", "REINDEX"}
# Tras estas palabras, el paréntesis va separado: «IN (», «AS (».
_NO_FUNCION = {"IN", "AS", "AND", "OR", "NOT", "ON", "EXISTS", "WHEN",
               "THEN", "ELSE", "SELECT", "FROM", "WHERE", "BY"}


def _pegar(actual, texto):
    """Añade un trozo a la línea, con espacio delante o sin él."""
    final = re.search(r"(\w+)$", actual)
    anterior = final.group(1).upper() if final else ""
    es_funcion = (texto.startswith("(") and anterior
                  and anterior not in _NO_FUNCION)  # SUM(, ROUND(…
    pegado = (not actual.strip() or actual.endswith("(")
              or texto in (",", ")") or actual.endswith(" ") or es_funcion)
    return actual + (texto if pegado else " " + texto)


def formatear_sql(sql):
    """Ordena el SQL en varias líneas para que se lea fácil.

    No cambia lo que hace la consulta, solo dónde van los saltos de línea:
    cada cláusula en su línea, una columna del SELECT por línea y una línea
    en blanco entre los bloques del WITH. Las subconsultas cortas se quedan
    en una sola línea. Si algo no cuadra, devuelve el SQL tal cual.
    """
    tokens = _TOKEN.findall(sql.strip().rstrip(";"))
    if not tokens:
        return sql
    resultado = _formatear(tokens)
    # Comprobación final: el SQL ordenado debe tener exactamente los mismos
    # trozos que el original. Si no, mejor no tocarlo.
    if _TOKEN.findall(resultado) != tokens:
        return sql
    return resultado


def _formatear(tokens):
    lineas, actual = [], ""
    pila = []           # «q» = paréntesis de subconsulta, «f» = de función
    ultima = {0: ""}    # última cláusula vista en cada nivel
    i = 0

    def nivel():
        return pila.count("q")

    def nueva_linea(sangria, en_blanco=False):
        nonlocal actual
        if actual.strip():
            lineas.append(actual.rstrip())
        if en_blanco:
            lineas.append("")
        actual = " " * sangria

    def añadir(texto):
        nonlocal actual
        actual = _pegar(actual, texto)

    while i < len(tokens):
        tok = tokens[i]
        if tok.startswith("--"):
            # Un comentario de línea se come todo lo que va detrás en esa
            # línea, así que después siempre saltamos de línea.
            sangria = len(actual) - len(actual.lstrip())
            añadir(tok)
            nueva_linea(sangria)  # la línea siguiente mantiene la alineación
            i += 1
            continue
        dos = (tok + " " + tokens[i + 1]).upper() if i + 1 < len(tokens) else ""
        en_funcion = bool(pila) and pila[-1] == "f"
        clausula = dos if dos in CLAUSULAS else tok.upper()
        if clausula in CLAUSULAS and not en_funcion:
            nueva_linea(nivel() * 2)
            añadir(clausula)
            ultima[nivel()] = clausula
            i += 2 if clausula == dos else 1
            continue
        if tok == "(":
            siguiente = tokens[i + 1].upper() if i + 1 < len(tokens) else ""
            if siguiente in ("SELECT", "WITH"):
                # ¿Subconsulta corta? Entonces la dejamos en una línea.
                profundidad, j = 0, i
                while j < len(tokens):
                    profundidad += {"(": 1, ")": -1}.get(tokens[j], 0)
                    if profundidad == 0:
                        break
                    j += 1
                trozo = ""
                for pieza in tokens[i:j + 1]:
                    trozo = _pegar(trozo, pieza)
                sin_comentarios = not any(t.startswith("--") for t in tokens[i:j + 1])
                if len(trozo) <= 60 and sin_comentarios:
                    añadir(trozo)
                    i = j + 1
                    continue
                añadir("(")
                pila.append("q")
                ultima[nivel()] = ""
            else:
                añadir("(")
                pila.append("f")
        elif tok == ")":
            tipo = pila.pop() if pila else "f"
            if tipo == "q":
                nueva_linea(nivel() * 2)
            añadir(")")
        elif tok == "," and not en_funcion:
            añadir(",")
            if ultima.get(nivel()) == "SELECT":
                nueva_linea(nivel() * 2 + 7)  # alineado bajo la 1.ª columna
            elif ultima.get(nivel()) == "WITH":
                nueva_linea(nivel() * 2, en_blanco=True)
        else:
            añadir(tok)
        i += 1
    nueva_linea(0)
    return "\n".join(lineas)


# ---------------------------------------------------------------- Gemini

def leer_clave():
    """Busca la clave en una variable de entorno o, si no, en el archivo .env."""
    clave = os.environ.get("GEMINI_API_KEY", "").strip()
    if not clave and ARCHIVO_CLAVE.exists():
        for linea in ARCHIVO_CLAVE.read_text(encoding="utf-8").splitlines():
            nombre, _, valor = linea.partition("=")
            if nombre.strip() == "GEMINI_API_KEY":
                clave = valor.strip().strip('"').strip("'")
    if not clave or clave == "pon_aqui_tu_clave":
        raise ErrorIA("Falta la clave de Gemini: ponla en el archivo .env "
                      "(mira .env.example).")
    return clave


def llamar_gemini(prompt, salida_json=False):
    """Envía el texto a Gemini y devuelve su respuesta como texto."""
    configuracion = {"temperature": 0}  # 0 = respuestas lo más estables posible
    if salida_json:
        configuracion["responseMimeType"] = "application/json"
    cuerpo = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                         "generationConfig": configuracion}).encode("utf-8")
    peticion = urllib.request.Request(
        URL_GEMINI, data=cuerpo, method="POST",
        headers={"Content-Type": "application/json",
                 "x-goog-api-key": leer_clave()})
    try:
        with urllib.request.urlopen(peticion, timeout=60) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise ErrorIA("Gemini dice 429: has agotado la cuota gratuita "
                          "por ahora. Espera un rato.") from error
        detalle = error.read().decode("utf-8", "replace")[:300]
        raise ErrorIA(f"Gemini ha devuelto el error {error.code}: {detalle}") from error
    except OSError as error:
        raise ErrorIA(f"No se ha podido conectar con Gemini: {error}") from error
    try:
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as error:
        raise ErrorIA("Gemini no ha devuelto texto (quizá ha bloqueado la "
                      "pregunta).") from error


def pregunta_a_sql(pregunta):
    """Pide a Gemini el SQL que responde a la pregunta.

    Devuelve un diccionario con «sql» y «explicacion_sql» (qué hace la consulta).
    Si la pregunta no se puede responder con estos datos, «sql» viene vacío.
    """
    prompt = f"""Eres un experto en SQL de SQLite. Escribe UNA consulta que
responda a la pregunta usando solo esta tabla:

{esquema()}
Reglas:
- Solo SELECT (o WITH ... SELECT). Nunca modifiques datos.
- Usa los valores exactos de texto que aparecen arriba.
- Para importes en euros usa importe_eur y redondea con ROUND(..., 2).
- Para porcentajes multiplica por 100.0 y redondea a 1 decimal.
- Pon nombres de columna claros en español con AS.
- Si la pregunta no se puede responder con estos datos, deja "sql" vacío y
  explica por qué en "explicacion_sql".

Responde SOLO con JSON con esta forma:
{{"sql": "...", "explicacion_sql": "una frase sencilla sobre qué calcula la consulta"}}

Pregunta: {pregunta}"""
    texto = llamar_gemini(prompt, salida_json=True)
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as error:
        raise ErrorIA("Gemini no ha respondido con el formato esperado.") from error
    return {"sql": formatear_sql(str(datos.get("sql") or "").strip()),
            "explicacion_sql": str(datos.get("explicacion_sql", "")).strip()}


def explicar(pregunta, sql, columnas, filas):
    """Pide a Gemini una explicación corta del resultado, sin inventar cifras."""
    tabla = json.dumps({"columnas": columnas, "filas": filas[:20]},
                       ensure_ascii=False)
    prompt = f"""Pregunta del usuario: {pregunta}
Consulta SQL ejecutada: {sql}
Resultado (columnas y filas): {tabla}

Explica el resultado en español, en 1 o 2 frases sencillas, para alguien que
no sabe SQL. Usa solo las cifras del resultado; no inventes ninguna."""
    return llamar_gemini(prompt).strip()
