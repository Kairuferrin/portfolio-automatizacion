"""Servidor web local para «Pregunta a tus datos con IA».

Uso:
    python3 app.py
y abre http://localhost:8008 en el navegador.

Es un camarero muy simple: recibe pedidos de la página (index.html), se los
pasa a la cocina (ia_sql.py) y devuelve el plato en formato JSON.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import ia_sql

PUERTO = 8008
PAGINA = Path(__file__).parent / "index.html"


class Manejador(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._responder(200, PAGINA.read_bytes(), "text/html; charset=utf-8")
        else:
            self._responder(404, b"No encontrado", "text/plain; charset=utf-8")

    def do_POST(self):
        rutas = {"/api/sql": self._generar_sql,
                 "/api/ejecutar": self._ejecutar,
                 "/api/explicar": self._explicar,
                 "/api/formatear": self._formatear}
        funcion = rutas.get(self.path)
        if funcion is None:
            return self._json(404, {"error": "Ruta desconocida."})
        if not self._viene_de_esta_pagina():
            return self._json(403, {"error": "Solo se acepta desde esta página."})
        try:
            largo = int(self.headers.get("Content-Length", 0))
            datos = json.loads(self.rfile.read(largo) or b"{}")
            if not isinstance(datos, dict):
                raise ValueError("se esperaba un objeto JSON")
            self._json(200, funcion(datos))
        except ia_sql.ErrorIA as error:
            self._json(400, {"error": str(error)})
        except ValueError:  # incluye el JSON mal escrito
            self._json(400, {"error": "Petición mal formada."})
        except Exception as error:  # cualquier otro fallo: mensaje genérico
            print("Error inesperado:", repr(error))
            self._json(500, {"error": "Error inesperado en el servidor."})

    def _viene_de_esta_pagina(self):
        """Evita que otra web abierta en el navegador use este servidor.

        Es como un portero que solo abre a quien viene de la propia casa.
        """
        permitidos = {f"localhost:{PUERTO}", f"127.0.0.1:{PUERTO}"}
        if self.headers.get("Host", "") not in permitidos:
            return False
        origen = self.headers.get("Origin")
        return origen is None or origen.split("://", 1)[-1] in permitidos

    # --- lo que hace cada ruta -------------------------------------------

    @staticmethod
    def _generar_sql(datos):
        pregunta = str(datos.get("pregunta", "")).strip()
        if not pregunta:
            raise ia_sql.ErrorIA("Escribe una pregunta.")
        return ia_sql.pregunta_a_sql(pregunta)

    @staticmethod
    def _ejecutar(datos):
        columnas, filas, cortado = ia_sql.ejecutar(str(datos.get("sql", "")))
        return {"columnas": columnas, "filas": filas, "cortado": cortado}

    @staticmethod
    def _explicar(datos):
        columnas, filas, _ = ia_sql.ejecutar(str(datos.get("sql", "")))
        texto = ia_sql.explicar(str(datos.get("pregunta", "")),
                                str(datos.get("sql", "")), columnas, filas)
        return {"explicacion": texto}

    @staticmethod
    def _formatear(datos):
        return {"sql": ia_sql.formatear_sql(str(datos.get("sql", "")))}

    # --- utilidades -------------------------------------------------------

    def _json(self, codigo, objeto):
        cuerpo = json.dumps(objeto, ensure_ascii=False).encode("utf-8")
        self._responder(codigo, cuerpo, "application/json; charset=utf-8")

    def _responder(self, codigo, cuerpo, tipo):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, formato, *args):
        print("·", self.command, self.path)  # registro corto en el terminal


if __name__ == "__main__":
    # 127.0.0.1 = solo tu ordenador puede abrir la página, nadie más de la red.
    servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador)
    print(f"Abierto en http://localhost:{PUERTO}  (Ctrl+C para parar)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado.")
