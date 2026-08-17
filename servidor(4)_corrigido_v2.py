from flask import Flask, send_from_directory, jsonify
import subprocess
import sys
import os
import re
import threading
import webbrowser
import html
import requests
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder=".")


@app.after_request
def adicionar_cors(resposta):
    resposta.headers["Access-Control-Allow-Origin"] = "*"
    resposta.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resposta

URL_POSTE_ONTEM = "https://www.ojogodobicho.com/resultadosanteriores.htm"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Cache-Control": "no-cache"
}


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/resultados.csv")
def resultados_csv():
    caminho = os.path.join(os.getcwd(), "resultados.csv")
    if not os.path.exists(caminho):
        return "Arquivo resultados.csv não encontrado.", 404

    resposta = send_from_directory(
        os.getcwd(),
        "resultados.csv",
        mimetype="text/csv"
    )
    resposta.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resposta.headers["Pragma"] = "no-cache"
    return resposta


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


def texto_limpo(celula):
    return html.escape(celula.get_text(" ", strip=True))


def cabecalho_normalizado(celulas):
    return [
        re.sub(r"\s+", " ", c.get_text(" ", strip=True)).strip().upper()
        for c in celulas
    ]


def normalizar_texto(texto):
    return re.sub(r"\s+", " ", texto).strip()


def cabecalho_normalizado(celulas):
    return [
        normalizar_texto(c.get_text(" ", strip=True)).upper()
        for c in celulas
    ]


def pontuacao_tabela(tabela, tipo):
    texto = normalizar_texto(tabela.get_text(" ", strip=True)).upper()
    linhas = tabela.find_all("tr")

    if not linhas:
        return -1

    pontuacao = 0

    if tipo == "ontem":
        for marcador in ("PPT", "PTM", "PTV", "FED", "COR"):
            if marcador in texto:
                pontuacao += 2
        if "DEU NO POSTE" in texto:
            pontuacao += 5
    else:
        for marcador in ("1º", "2º", "3º", "4º", "5º"):
            if marcador in texto:
                pontuacao += 1
        if re.search(r"\d{2}/\d{2}", texto):
            pontuacao += 4
        if "RESULTADOS DE" in texto:
            pontuacao += 5

    if len(linhas) >= 2:
        pontuacao += 1

    return pontuacao


def encontrar_tabela(tabelas, tipo, ignorar=None):
    melhor_tabela = None
    melhor_pontuacao = 0

    for tabela in tabelas:
        if ignorar is not None and tabela is ignorar:
            continue

        pontos = pontuacao_tabela(tabela, tipo)

        if pontos > melhor_pontuacao:
            melhor_pontuacao = pontos
            melhor_tabela = tabela

    if melhor_tabela is None:
        return None, None

    linhas = melhor_tabela.find_all("tr")

    for linha in linhas[:5]:
        celulas = linha.find_all(["th", "td"])
        if celulas:
            return melhor_tabela, celulas

    return melhor_tabela, []


def encontrar_titulo_anterior(tabela, limite=80):
    elementos = tabela.find_all_previous(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "strong"],
        limit=limite
    )

    for elemento in elementos:
        texto = normalizar_texto(elemento.get_text(" ", strip=True))

        if re.search(
            r"(?:segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)"
            r".*\d{1,2}\s+de\s+[A-Za-zÀ-ÿ]+\s+de\s+\d{4}",
            texto,
            re.IGNORECASE
        ):
            return html.escape(texto)

    return ""


def encontrar_titulo_intervalo(tabela):
    elementos = tabela.find_all_previous(
        ["h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "strong"],
        limit=80
    )

    for elemento in elementos:
        texto = normalizar_texto(elemento.get_text(" ", strip=True))
        encontrado = re.search(
            r"Resultados\s+de\s+\d{2}/\d{2}\s+a\s+\d{2}/\d{2}",
            texto,
            re.IGNORECASE
        )

        if encontrado:
            return html.escape(encontrado.group(0))

    return "Resultados anteriores"


def extrair_tabela(tabela, cabecalho_celulas):
    todas_linhas = tabela.find_all("tr")

    if not todas_linhas:
        return [], []

    indice_cabecalho = 0

    for indice, linha in enumerate(todas_linhas):
        celulas = linha.find_all(["th", "td"])

        if celulas and [
            normalizar_texto(c.get_text(" ", strip=True)).upper()
            for c in celulas
        ] == cabecalho_normalizado(cabecalho_celulas):
            indice_cabecalho = indice
            break

    cabecalho = [
        html.escape(normalizar_texto(c.get_text(" ", strip=True)))
        for c in cabecalho_celulas
    ]

    linhas = []

    for linha in todas_linhas[indice_cabecalho + 1:]:
        celulas = linha.find_all(["td", "th"])

        if not celulas:
            continue

        valores = [texto_limpo(c) for c in celulas]

        if len(valores) != len(cabecalho):
            continue

        linhas.append(valores)

    return cabecalho, linhas


def coletar_outros_resultados():
    try:
        resposta = requests.get(
            URL_POSTE_ONTEM,
            headers=HEADERS,
            timeout=30
        )
    except requests.RequestException as erro:
        raise RuntimeError(
            "Não foi possível acessar a página Poste de Ontem: " + str(erro)
        )

    if resposta.status_code != 200:
        raise RuntimeError(
            f"O site respondeu HTTP {resposta.status_code} ao consultar Poste de Ontem."
        )

    soup = BeautifulSoup(resposta.text, "html.parser")
    tabelas = soup.find_all("table")

    if not tabelas:
        raise RuntimeError(
            "Nenhuma tabela foi encontrada na página Poste de Ontem.")

    tabela_ontem, cab_ontem = encontrar_tabela(tabelas, "ontem")
    tabela_historico, cab_historico = encontrar_tabela(
        tabelas, "historico", ignorar=tabela_ontem
    )

    if tabela_ontem is None:
        raise RuntimeError(
            "A tabela 'Deu no Poste de Ontem' não foi encontrada.")

    if tabela_historico is None:
        raise RuntimeError(
            "A tabela de resultados anteriores não foi encontrada.")

    cab1, linhas1 = extrair_tabela(tabela_ontem, cab_ontem)
    cab2, linhas2 = extrair_tabela(tabela_historico, cab_historico)

    if not cab1 or not linhas1:
        raise RuntimeError(
            "A tabela 'Deu no Poste de Ontem' foi encontrada, mas não possui dados.")

    if not cab2 or not linhas2:
        raise RuntimeError(
            "A tabela de resultados anteriores foi encontrada, mas não possui dados.")

    data_ontem = encontrar_titulo_anterior(tabela_ontem)
    titulo_historico = encontrar_titulo_intervalo(tabela_historico)

    return {
        "sucesso": True,
        "tabelas": [
            {
                "titulo": "Deu no Poste de Ontem",
                "subtitulo": data_ontem,
                "cabecalho": cab1,
                "linhas": linhas1
            },
            {
                "titulo": titulo_historico,
                "subtitulo": "",
                "cabecalho": cab2,
                "linhas": linhas2
            }
        ]
    }


@app.route("/outros-resultados")
def outros_resultados():
    try:
        dados = coletar_outros_resultados()
        return jsonify(dados)
    except Exception as e:
        print("Erro na Trilha 2:", e)
        return jsonify({
            "sucesso": False,
            "mensagem": str(e)
        }), 500


@app.route("/<path:arquivo>")
def arquivos(arquivo):
    return send_from_directory(".", arquivo)


if __name__ == "__main__":
    def abrir_fera_da_sorte():
        webbrowser.open("http://127.0.0.1:5000/")

    threading.Timer(1.0, abrir_fera_da_sorte).start()

    print("\n==============================")
    print("FERA DA SORTE")
    print("Servidor Flask iniciado.")
    print("Interface: http://127.0.0.1:5000/")
    print("==============================\n")

    app.run(host="127.0.0.1", port=5000)
