import os
import sys
import subprocess
import time
import webbrowser

PASTA = os.path.dirname(os.path.abspath(__file__))

SERVIDOR_A = os.path.join(PASTA, "servidor_trilha_A_auto.py")
SERVIDOR_B = os.path.join(PASTA, "servidor_trilha_B.py")

print("==========================================")
print(" FERA DA SORTE - TESTE DOS SERVIDORES")
print("==========================================")
print()

for nome, servidor in (
    ("TRILHA A", SERVIDOR_A),
    ("TRILHA B", SERVIDOR_B),
):
    print(f"{nome}:")
    print(f"Arquivo: {servidor}")

    if not os.path.exists(servidor):
        print("ERRO: arquivo não encontrado.")
        print()
        continue

    try:
        processo = subprocess.Popen(
            [sys.executable, servidor],
            cwd=PASTA
        )
        print(f"Processo iniciado. PID: {processo.pid}")
    except Exception as erro:
        print(f"ERRO ao iniciar: {erro}")

    print()

print("Teste concluído.")
print()
print("Aguardando os servidores iniciarem...")
time.sleep(2)

URL_FERA = "http://127.0.0.1:5000/"
print(f"Abrindo Fera da Sorte em: {URL_FERA}")
webbrowser.open(URL_FERA)

print()
input("Pressione ENTER para fechar...")
