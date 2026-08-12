from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

from consulta_outros_resultados import consultar_data


HOST = "127.0.0.1"
PORTA = 8000


class ServidorConsulta(BaseHTTPRequestHandler):

    def enviar_json(self, dados, status=200):

        resposta = json.dumps(
            dados,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        # Permite que o index.html converse com este servidor.
        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Content-Length",
            str(len(resposta))
        )

        self.end_headers()

        self.wfile.write(resposta)


    def do_GET(self):

        caminho = urlparse(self.path)

        # ------------------------------------------------------
        # Rota de teste
        # ------------------------------------------------------

        if caminho.path == "/":

            self.enviar_json({
                "servidor": "FERA DA SORTE",
                "status": "online"
            })

            return


        # ------------------------------------------------------
        # Consulta de resultados
        # ------------------------------------------------------

        if caminho.path == "/consultar":

            parametros = parse_qs(caminho.query)

            data = parametros.get("data", [None])[0]

            if not data:

                self.enviar_json({
                    "sucesso": False,
                    "mensagem": "Data não informada."
                }, 400)

                return


            print()
            print("=" * 60)
            print("CONSULTA FERA DA SORTE")
            print("Data:", data)
            print("=" * 60)


            resultado = consultar_data(data)

            self.enviar_json(resultado)

            return


        # ------------------------------------------------------
        # Rota inexistente
        # ------------------------------------------------------

        self.enviar_json({
            "sucesso": False,
            "mensagem": "Rota não encontrada."
        }, 404)


# ==========================================================
# INICIAR SERVIDOR
# ==========================================================

if __name__ == "__main__":

    servidor = HTTPServer(
        (HOST, PORTA),
        ServidorConsulta
    )

    print()
    print("=" * 60)
    print("       FERA DA SORTE — SERVIDOR DE CONSULTA")
    print("=" * 60)
    print()
    print("Servidor iniciado.")
    print()
    print(f"Endereço:")
    print(f"http://{HOST}:{PORTA}")
    print()
    print("Para consultar uma data:")
    print(
        f"http://{HOST}:{PORTA}/consultar?data=12/08/2026"
    )
    print()
    print("Para encerrar: CTRL + C")
    print("=" * 60)
    print()

    try:

        servidor.serve_forever()

    except KeyboardInterrupt:

        print()
        print("Servidor encerrado.")

    finally:

        servidor.server_close()