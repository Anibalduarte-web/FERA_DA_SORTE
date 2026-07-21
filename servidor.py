from flask import Flask, send_from_directory
import subprocess
import sys
import os

app = Flask(__name__, static_folder=".")


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/atualizar")
def atualizar():

    print("\n==============================")
    print("Atualizando resultados...")
    print("==============================")

    try:

        subprocess.run(
            [sys.executable, "update_deu_no_poste.py"],
            cwd=os.getcwd(),
            check=True
        )

        print("Atualização concluída.\n")
        print("CSV atualizado em:")
        print(os.path.abspath("resultados.csv"))
        return "OK"

    except Exception as e:

        print(e)
        return str(e), 500


@app.route("/<path:arquivo>")
def arquivos(arquivo):
    return send_from_directory(".", arquivo)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
