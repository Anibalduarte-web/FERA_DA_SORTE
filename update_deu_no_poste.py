from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
import csv
import os
import re
import sys
from datetime import datetime

# ==============================================================
# CONFIGURAÇÕES
# ==============================================================

URL_BASE = "https://www.ojogodobicho.com"
URL_MAIN = URL_BASE + "/resultado/"

PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_CSV = os.path.join(PASTA_PROJETO, "resultados.csv")
ARQUIVO_HTML = os.path.join(PASTA_PROJETO, "resultado.html")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

COLUNAS = [
    "Data",
    "Banca",
    "Horario",
    "Premio",
    "Milhar",
    "Centena",
    "Grupo",
    "Bicho"
]

# ==============================================================
# FUNÇÕES ORIGINAIS
# ==============================================================


def obter_data_argumento():
    """Lê a data informada no comando."""

    if len(sys.argv) >= 2:
        data_arg = " ".join(sys.argv[1:]).strip().strip('"').strip("'")

        formatos = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]

        for fmt in formatos:
            try:
                dt = datetime.strptime(data_arg, fmt)
                return dt.strftime("%d/%m/%Y")
            except ValueError:
                continue

        print()
        print("ERRO: Data inválida.")
        print("Use o formato DD/MM/AAAA.")
        print()
        input("Pressione ENTER para sair...")
        exit(1)

    return datetime.now(
        ZoneInfo("America/Sao_Paulo")
    ).strftime("%d/%m/%Y")


def buscar_link_data(data_str):
    """
    Monta diretamente a URL da data.
    Não depende mais da lista 'Últimos dias'.
    """

    dt = datetime.strptime(data_str, "%d/%m/%Y")

    return (
        f"{URL_BASE}/resultado/"
        f"{dt.year:04d}/"
        f"{dt.month:02d}/"
        f"{dt.day:02d}/"
    )


def extrair_banca_horario(wrap):
    """Extrai a banca e o horário do <caption> da tabela."""
    banca = ""
    horario = "--:--"
    caption = wrap.find("caption")
    if caption:
        titulo_txt = caption.get_text(" ", strip=True)
        match = re.search(
            r"([A-Za-z]{2,10})\s*\(\s*(\d{2}:\d{2})\s*\)", titulo_txt)
        if match:
            banca = match.group(1).upper()
            horario = match.group(2)
        else:
            match2 = re.search(r"^([A-Za-z]+)", titulo_txt)
            if match2:
                banca = match2.group(1).capitalize()
                horario = "--:--"
    return banca, horario


def extrair_resultados_dia(url_dia, data_str):
    """Acessa a página do dia e extrai todas as tabelas."""

    resp = requests.get(url_dia, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    print("=" * 50)
    print("Quantidade de tabelas HTML      :", len(soup.find_all("table")))
    print("Quantidade de div.table-wrap    :",
          len(soup.find_all("div", class_="table-wrap")))
    print("=" * 50)

    resultados = []

    soup = BeautifulSoup(resp.text, "html.parser")

    table_wraps = soup.find_all("div", class_="table-wrap")

    if not table_wraps:
        raise Exception(
            "Nenhuma tabela de resultado foi encontrada na página do dia."
        )

    print("\n=== TABELAS ENCONTRADAS ===")

    for wrap in table_wraps:
        cap = wrap.find("caption")

        if cap:
            print(cap.get_text(" ", strip=True))
        else:
            print("Tabela sem CAPTION")

    for wrap in table_wraps:
        banca, horario = extrair_banca_horario(wrap)
        tabela = wrap.find("table")

        if not tabela:
            continue

        for tr in tabela.find_all("tr"):
            cels = [
                td.get_text(strip=True)
                for td in tr.find_all(["td", "th"])
            ]

            if len(cels) < 5:
                continue

            primeira_coluna = cels[0].lower().replace("ê", "e")

            if primeira_coluna in ("premio", "prêmio"):
                continue

            resultados.append({
                "Data": data_str,
                "Banca": banca,
                "Horario": horario,
                "Premio": cels[0],
                "Milhar": cels[1],
                "Centena": cels[2],
                "Grupo": cels[3],
                "Bicho": cels[4]
            })

    return resultados


def carregar_chaves_existentes():
    """Lê o CSV existente e retorna chaves para evitar duplicidade."""
    chaves = set()
    if not os.path.exists(ARQUIVO_CSV):
        return chaves
    with open(ARQUIVO_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            chave = (
                row.get("Data", ""),
                row.get("Banca", ""),
                row.get("Horario", ""),
                row.get("Premio", ""),
                row.get("Milhar", "")
            )
            chaves.add(chave)
    return chaves


def salvar_resultados(resultados):
    """Salva resultados novos no CSV usando ponto e vírgula."""
    try:
        chaves = carregar_chaves_existentes()
        arquivo_existe = os.path.exists(ARQUIVO_CSV)
        novos = 0
        with open(ARQUIVO_CSV, "a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUNAS, delimiter=";")
            if not arquivo_existe:
                writer.writeheader()
            for r in resultados:
                chave = (r["Data"], r["Banca"], r["Horario"],
                         r["Premio"], r["Milhar"])
                if chave not in chaves:
                    writer.writerow(r)
                    chaves.add(chave)
                    novos += 1
        return novos
    except PermissionError:
        print()
        print("ERRO: O arquivo resultados.csv está aberto.")
        print()
        input("Pressione ENTER para sair...")
        exit(1)

# ==============================================================
# NOVA FUNÇÃO — GERADOR DE HTML BONITO MODO APP
# ==============================================================


EMOJI_BICHO = {
    "Avestruz": "🦩",
    "Águia": "🦅",
    "Burro": "🐴",
    "Borboleta": "🦋",
    "Cachorro": "🐶",
    "Cabra": "🐐",
    "Carneiro": "🐏",
    "Camelo": "🐫",
    "Cobra": "🐍",
    "Coelho": "🐇",
    "Cavalo": "🐎",
    "Elefante": "🐘",
    "Galo": "🐓",
    "Gato": "🐱",
    "Jacaré": "🐊",
    "Leão": "🦁",
    "Macaco": "🐒",
    "Porco": "🐖",
    "Pavão": "🦚",
    "Peru": "🦃",
    "Touro": "🐂",
    "Tigre": "🐅",
    "Urso": "🐻",
    "Veado": "🦌",
    "Vaca": "🐄"
}


def gerar_html_bonito(resultados, data_str):
    """Gera resultado.html com layout visual moderno e emojis."""

    COR_BANCA = {
        "PPT": {"fundo": "#dbeafe", "borda": "#3b82f6", "texto": "#1e3a8a"},
        "PTM": {"fundo": "#dcfce7", "borda": "#22c55e", "texto": "#14532d"},
        "PT":  {"fundo": "#fef9c3", "borda": "#eab308", "texto": "#713f12"},
        "PTV": {"fundo": "#fce7f3", "borda": "#ec4899", "texto": "#831843"},
    }

    linhas_html = ""

    # IMPORTANTE: AQUI A IDENTAÇÃO ESTÁ CORRIGIDA!
    for r in resultados:
        banca = r["Banca"].upper()

        cor = COR_BANCA.get(
            banca,
            {"fundo": "#f3f4f6", "borda": "#9ca3af", "texto": "#111827"}
        )

        emoji = EMOJI_BICHO.get(r["Bicho"], "❓")

        linhas_html += f"""
        <div class="card" style="background:{cor['fundo']};border-left:6px solid {cor['borda']};">
            <div class="cel" style="color:{cor['texto']};font-weight:bold;">{r['Banca']}</div>
            <div class="cel">{r['Horario']}</div>
            <div class="cel">{r['Premio']}</div>
            <div class="cel">{r['Milhar']}</div>
            <div class="cel">{r['Centena']}</div>
            <div class="cel">{r['Grupo']}</div>
            <div class="cel bicho-emoji">{emoji} {r['Bicho']}</div>
        </div>"""

    # Geração do bloco HTML inteiro (Sem sujeiras ou aspas soltas)
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FERA_DA_SORTE — {data_str}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}

        body {{
            font-family: Arial, sans-serif;
            background: #f0f4f8;
            padding: 30px 20px;
        }}

        .topo {{
            text-align: center;
            margin-bottom: 25px;
        }}

        .topo h1 {{
            font-size: 1.8rem;
            color: #1e293b;
            letter-spacing: 1px;
        }}

        .topo p {{
            font-size: 0.95rem;
            color: #64748b;
            margin-top: 5px;
        }}

        .container {{
            max-width: 820px;
            margin: 0 auto;
        }}

        /* Cabeçalho */
        .cabecalho {{
            display: grid;
            grid-template-columns: 80px 80px 70px 90px 90px 70px 1fr;
            background: #1e293b;
            color: #ffffff;
            border-radius: 12px;
            padding: 10px 16px;
            margin-bottom: 10px;
            text-align: center;
            font-size: 0.82rem;
            font-weight: bold;
            letter-spacing: 0.5px;
        }}

        /* Cards de resultado - Efeito suave */
        .card {{
            display: grid;
            grid-template-columns: 80px 80px 70px 90px 90px 70px 1fr;
            border-radius: 12px;
            padding: 10px 16px;
            margin-bottom: 8px;
            text-align: center;
            font-size: 0.88rem;
            align-items: center;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
            transition: transform 0.15s;
            animation: fadeIn 0.4s ease-out forwards;
        }}

        .card:hover {{ transform: scale(1.02); }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        .cel {{ padding: 4px 2px; color: #1e293b; }}

        .bicho-emoji {{
            font-size: 1.15rem; /* Aumentado para mais destaque */
            font-weight: bold;
        }}

        /* Legenda de cores */
        .legenda {{
            display: flex;
            gap: 16px;
            justify-content: center;
            flex-wrap: wrap;
            margin: 20px auto 24px;
        }}

        .legenda-item {{
            display: flex;
            align-items: center;
            gap: 7px;
            font-size: 0.82rem;
            color: #475569;
        }}

        .legenda-cor {{
            width: 14px;
            height: 14px;
            border-radius: 4px;
        }}

        /* Rodapé */
        .rodape {{
            text-align: center;
            margin-top: 30px;
            font-size: 0.78rem;
            color: #94a3b8;
        }}
    </style>
</head>
<body>

    <div class="topo">
        <h1>🎲 Deu no Poste</h1>
        <p>Resultados do dia <strong>{data_str}</strong></p>
    </div>

    <div class="legenda">
        <div class="legenda-item">
            <div class="legenda-cor" style="background:#3b82f6;"></div> PPT
        </div>
        <div class="legenda-item">
            <div class="legenda-cor" style="background:#22c55e;"></div> PTM
        </div>
        <div class="legenda-item">
            <div class="legenda-cor" style="background:#eab308;"></div> PT
        </div>
        <div class="legenda-item">
            <div class="legenda-cor" style="background:#ec4899;"></div> PTV
        </div>
    </div>

    <div class="container">

        <div class="cabecalho">
            <div>Banca</div>
            <div>Horário</div>
            <div>Prêmio</div>
            <div>Milhar</div>
            <div>Centena</div>
            <div>Grupo</div>
            <div>Bicho</div>
        </div>

        {linhas_html}

    </div>

    <div class="rodape">
        Gerado automaticamente em {datetime.now().strftime("%d/%m/%Y %H:%M")}
        — update_deu_no_poste.py
    </div>

</body>
</html>"""

    with open(ARQUIVO_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"    Arquivo Visual gerado: {ARQUIVO_HTML}")


# ==============================================================
# PRINCIPAL
# ==============================================================

def main(data_str=None):
    """Executa a coleta. Se nenhuma data for informada, usa a data atual."""
    if data_str is None:
        data_str = obter_data_argumento()

    print("=" * 55)
    print("  FERA_DA_SORTE — Coleta de Resultados")
    print(f"  Data: {data_str}")
    print("=" * 55)

    print("\n[1] Buscando link da data no site...")
    url_dia = buscar_link_data(data_str)
    print(f"    OK -> {url_dia}")

    print("\n[2] Extraindo resultados das tabelas...")
    resultados = extrair_resultados_dia(url_dia, data_str)
    print(f"    Registros encontrados: {len(resultados)}")

    if not resultados:
        print("    Nenhum resultado encontrado.")
        return

    print("\n[3] Salvando no CSV...")
    novos = salvar_resultados(resultados)
    print(f"    Registros novos : {novos}")
    print(f"    Arquivo         : {ARQUIVO_CSV}")
    if novos == 0:
        print("    Nenhum resultado novo foi encontrado.")

    else:
        print(f"    Foram adicionados {novos} registros ao CSV.")

    print("\n[4] Gerando HTML bonito...")
    gerar_html_bonito(resultados, data_str)
    print("    OK!")

    print("\n[5] Prévia:")
    print(
        f"{'Data':<12} {'Banca':<8} {'Hora':<7} "
        f"{'Premio':<7} {'Milhar':<7} {'Centena':<9} "
        f"{'Grupo':<7} {'Bicho'}"
    )
    print("-" * 80)
    for r in resultados:
        print(
            f"{r['Data']:<12} {r['Banca']:<8} {r['Horario']:<7} "
            f"{r['Premio']:<7} {r['Milhar']:<7} {r['Centena']:<9} "
            f"{r['Grupo']:<7} {r['Bicho']}"
        )

    print("\n" + "=" * 55)
    print("  Concluído com sucesso!")
    print("=" * 55)


if __name__ == "__main__":
    main()
