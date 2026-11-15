"""Baixa os arquivos do recorte do FTP do DATASUS, converte para Parquet e registra no manifesto.

Uso:  python scripts/02_baixar.py --recorte               # pede confirmação antes
      python scripts/02_baixar.py --recorte --parte 3/8    # 3ª de 8 fatias (para rodar 8 processos em paralelo)
      python scripts/02_baixar.py --recorte --confirmado   # sem perguntar
      python scripts/02_baixar.py --amostra                # 1 mês de cada grupo em SP, PR e RR

Cada arquivo: .dbc em dados/raw/_dbc/, Parquet em dados/raw/<sistema>/<grupo>/ e uma linha em dados/manifesto.csv (com sha256).
Pode ser interrompido e rodado de novo: o que já está no manifesto é pulado.
"""

import argparse
import asyncio
import zlib
from datetime import datetime

from pysus.api.extensions import ExtensionFactory
from pysus.api.ftp.client import FTP

import config
from ftp_datasus import descrever, listar_arquivos
from manifesto import calcular_sha256, ler_manifesto, registrar_no_manifesto

PASTA_DBC = config.PASTA_RAW / "_dbc"
TENTATIVAS = 3


# Escolha dos arquivos

def quer_baixar(info, modo):
    """Diz se o arquivo faz parte do modo escolhido: 'amostra' ou 'recorte'."""
    if modo == "amostra":
        a = config.AMOSTRA
        return (info["uf"] in a["ufs"] and info["ano"] == a["ano"] and info["mes"] in (None, a["mes"]))
    return info["uf"] in config.UFS and info["ano"] in config.ANOS


def arquivos_do_recorte(modo):
    """Lista o FTP e devolve [(objeto_pysus, info)] dos arquivos que queremos baixar."""
    escolhidos = []
    for sistema, grupos in config.SISTEMAS_E_GRUPOS.items():
        for arquivo in listar_arquivos(sistema, grupos):
            info = descrever(arquivo)
            if info["grupo"] in grupos and quer_baixar(info, modo):
                escolhidos.append((arquivo, info))
    return escolhidos


def caminho_parquet(info):
    nome = info["arquivo"].rsplit(".", 1)[0] + ".parquet"
    return config.PASTA_RAW / info["sistema"] / info["grupo"] / nome


def ja_baixado(info, manifesto):
    """Pula se o manifesto tem o arquivo, o Parquet existe e o FTP não foi revisado."""
    linhas = manifesto[(manifesto["sistema"] == info["sistema"])
                       & (manifesto["grupo"] == info["grupo"])
                       & (manifesto["arquivo"] == info["arquivo"])]
    if linhas.empty or not caminho_parquet(info).exists():
        return False
    ultima = linhas.iloc[-1]  # o manifesto só cresce: a última linha é a versão em uso
    if ultima["modificado_ftp"] != info["modificado_ftp"]:
        print(f"  AVISO: {info['arquivo']} foi revisado no FTP desde o último download; baixando de novo.")
        return False
    return True


# Download de um arquivo

async def baixar_dbc(cliente, arquivo, info):
    """Baixa o .dbc para um nome '.part' e só o renomeia depois de conferir o tamanho."""
    dbc = PASTA_DBC / info["sistema"] / info["grupo"] / info["arquivo"]
    dbc.parent.mkdir(parents=True, exist_ok=True)

    # Se o .dbc completo já existe (ex.: parou antes de converter), não baixa de novo.
    if dbc.exists() and dbc.stat().st_size == info["tamanho_bytes"]:
        return dbc

    parcial = dbc.with_name(dbc.name + ".part")
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            await cliente.download(arquivo, parcial)
            if parcial.stat().st_size != info["tamanho_bytes"]:
                raise IOError("tamanho baixado diferente do tamanho no FTP")
            parcial.replace(dbc)
            return dbc
        except Exception as erro:
            print(f"  tentativa {tentativa}/{TENTATIVAS} falhou: {erro}")
            # Reconecta: a sessão FTP pode ter caído.
            await cliente.close()
            await cliente.connect()
    raise RuntimeError(f"não foi possível baixar {info['arquivo']}")


async def converter_para_parquet(dbc, info):
    """Converte .dbc -> Parquet (PySUS). Escreve num '.tmp' para nunca deixar Parquet pela metade."""
    destino = caminho_parquet(info)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name(destino.name + ".tmp")
    temporario.unlink(missing_ok=True)  # o PySUS reaproveitaria um arquivo sobrando de uma execução interrompida

    arquivo_dbc = await ExtensionFactory.instantiate(dbc)
    await arquivo_dbc.to_parquet(output_path=temporario)
    temporario.replace(destino)
    return destino


def montar_periodo(info):
    if info["mes"]:
        return f"{int(info['ano'])}-{int(info['mes']):02d}"
    return str(int(info["ano"]))  # SIM e SINASC são anuais


async def baixar_tudo(escolhidos):
    cliente = FTP()
    await cliente.connect()
    falhas = []
    try:
        for i, (arquivo, info) in enumerate(escolhidos, start=1):
            print(f"[{i}/{len(escolhidos)}] {info['arquivo']}")
            try:
                dbc = await baixar_dbc(cliente, arquivo, info)
                parquet = await converter_para_parquet(dbc, info)
                registrar_no_manifesto({
                    "arquivo": info["arquivo"], "sistema": info["sistema"], "grupo": info["grupo"],
                    "uf": info["uf"], "periodo": montar_periodo(info),
                    "bytes": parquet.stat().st_size, "sha256": calcular_sha256(parquet),
                    "dbc_bytes": dbc.stat().st_size, "dbc_sha256": calcular_sha256(dbc),
                    "modificado_ftp": info["modificado_ftp"], "caminho_ftp": info["caminho_ftp"],
                    "data_download": datetime.now().isoformat(sep=" ", timespec="seconds"),
                })
            except Exception as erro:
                print(f"  FALHOU: {erro}")
                falhas.append(info["arquivo"])
    finally:
        await cliente.close()
    return falhas


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--amostra", action="store_true", help="1 mês de cada grupo em SP, PR e RR")
    parser.add_argument("--recorte", action="store_true", help="baixa todo o recorte do config.py")
    parser.add_argument("--confirmado", action="store_true", help="não pergunta antes de baixar (a confirmação já foi feita por quem chamou)")
    parser.add_argument("--parte", help="K/N: este processo cuida só da K-ésima de N fatias da lista. "
                                        "Rode N processos juntos para usar vários núcleos")
    args = parser.parse_args()
    if not (args.recorte or args.amostra):
        parser.error("escolha --amostra ou --recorte")  # sem argumento nada é baixado, para não repetir download por engano
    modo = "recorte" if args.recorte else "amostra"

    escolhidos = arquivos_do_recorte(modo)
    if args.parte:
        # A fatia vem de um hash do nome do arquivo, e não da posição na lista: cada processo lista o FTP por conta própria.
        k, n = map(int, args.parte.split("/"))
        escolhidos = [e for e in escolhidos
                      if zlib.crc32(f"{e[1]['sistema']}/{e[1]['grupo']}/{e[1]['arquivo']}".encode()) % n == k - 1]
    manifesto = ler_manifesto()
    pendentes = [(a, i) for a, i in escolhidos if not ja_baixado(i, manifesto)]

    mb = sum(i["tamanho_bytes"] for _, i in pendentes) / 1024**2
    print(f"{len(escolhidos)} arquivos no recorte, {len(escolhidos) - len(pendentes)} já baixados, "
          f"{len(pendentes)} a baixar (~{mb:.0f} MB comprimidos; o Parquet ocupa mais, e o .dbc também é mantido).")

    if args.recorte and pendentes and not args.confirmado:
        try:
            resposta = input("Confirma o download? [s/N] ")
        except EOFError:
            resposta = ""
        if resposta.strip().lower() != "s":
            raise SystemExit("Cancelado.")

    falhas = asyncio.run(baixar_tudo(pendentes))
    print(f"\nConcluído. Falhas: {len(falhas)}" + (f" -> {falhas}" if falhas else ""))
