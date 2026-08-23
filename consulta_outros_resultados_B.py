import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
import sys

# ==============================================================
# CONFIGURAÇÕES
# ==============================================================

URL_BASE = "https://www.ojogodobicho.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ==============================================================
# 1. CONVERTER DATA
# ==============================================================

def validar_data(data_str):

    try:
        dt = datetime.strptime(data_str, "%d/%m/%Y")
        return dt

    except ValueError:
        return None


# ==============================================================
# 2. MONTAR URL DA DATA
# ==============================================================

def buscar_link_data(data_str):

    dt = validar_data(data_str)

    if dt is None:
        raise ValueError("Data inválida.")

    return (
        f"{URL_BASE}/resultado/"
        f"{dt.year:04d}/"
        f"{dt.month:02d}/"
        f"{dt.day:02d}/"
    )


# ==============================================================
# 3. IDENTIFICAR BANCA E HORÁRIO
# ==============================================================

def extrair_banca_horario(wrap):

    banca = ""
    horario = "--:--"

    caption = wrap.find("caption")

    if caption:

        titulo_txt = caption.get_text(" ", strip=True)

        match = re.search(
            r"([A-Za-z]{2,10})\s*\(\s*(\d{2}:\d{2})\s*\)",
            titulo_txt
        )

        if match:

            banca = match.group(1).upper()
            horario = match.group(2)

        else:

            match2 = re.search(
                r"^([A-Za-z]+)",
                titulo_txt
            )

            if match2:
                banca = match2.group(1).upper()

    return banca, horario


# ==============================================================
# 4. EXTRAIR RESULTADOS
# ==============================================================

def extrair_resultados_dia(url_dia, data_str):

    resposta = requests.get(
        url_dia,
        headers=HEADERS,
        timeout=30
    )

    resposta.raise_for_status()

    soup = BeautifulSoup(
        resposta.text,
        "html.parser"
    )

    resultados = []

    tabelas = soup.select("div.table-wrap")

    for tabela in tabelas:

        banca, horario = extrair_banca_horario(tabela)

        linhas = tabela.select("tbody tr")

        for linha in linhas:

            colunas = linha.find_all("td")

            if len(colunas) < 4:
                continue

            valores = [
                c.get_text(" ", strip=True)
                for c in colunas
            ]

            premio = valores[0]
            milhar = valores[1]
            centena = valores[2]
            grupo = valores[3]
            bicho = valores[4] if len(valores) > 4 else ""

            resultados.append({
                "Data": data_str,
                "Banca": banca,
                "Horario": horario,
                "Premio": premio,
                "Milhar": milhar,
                "Centena": centena,
                "Grupo": grupo,
                "Bicho": bicho
            })

    return resultados


# ==============================================================
# 5. CONSULTA COMPLETA
# ==============================================================

def consultar_data(data_str):

    try:

        url = buscar_link_data(data_str)

        resultados = extrair_resultados_dia(
            url,
            data_str
        )

        return {
            "sucesso": True,
            "data": data_str,
            "url": url,
            "quantidade": len(resultados),
            "resultados": resultados
        }

    except requests.HTTPError as erro:

        return {
            "sucesso": False,
            "data": data_str,
            "mensagem": "Resultado inexistente ou página não encontrada."
        }

    except Exception as erro:

        return {
            "sucesso": False,
            "data": data_str,
            "mensagem": str(erro)
        }


# ==============================================================
# 6. EXECUÇÃO PELO TERMINAL
# ==============================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "Uso: python consulta_outros_resultados.py DD/MM/AAAA"
        )

        sys.exit(1)

    data = sys.argv[1]

    resposta = consultar_data(data)

    print(
        json.dumps(
            resposta,
            ensure_ascii=False,
            indent=2
        )
    )