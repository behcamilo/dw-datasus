"""Baixa as tabelas de domínio (config.DOMINIOS e uma SIGTAP por competência) para dados/raw/dominio/<fonte>/.

Cada arquivo ganha uma linha no manifesto (sistema = 'DOMINIO'). O que já foi baixado é pulado.
"""

import ftplib
import gzip
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import config
from manifesto import calcular_sha256, ler_manifesto, registrar_no_manifesto

PASTA_DOMINIO = config.PASTA_RAW / "dominio"


def itens_sigtap_por_competencia():
    """Uma SIGTAP por competência; quando há várias versões (sufixo _vAAMMDDhhmm), fica a mais recente."""
    servidor, pasta = config.SIGTAP_FTP
    ftp = ftplib.FTP(servidor, timeout=120, encoding="latin-1")
    ftp.login()
    nomes = ftp.nlst(pasta)
    ftp.quit()
    itens = []
    for competencia in config.SIGTAP_COMPETENCIAS:
        versoes = sorted(Path(n).name for n in nomes if Path(n).name.startswith(f"TabelaUnificada_{competencia}_v"))
        if not versoes:
            print(f"AVISO: SIGTAP {competencia} não encontrada no FTP")
            continue
        itens.append({"fonte": "sigtap", "periodo": f"{competencia[:4]}-{competencia[4:]}",
                      "descricao": f"SIGTAP competência {competencia}",
                      "url": f"ftp://{servidor}{pasta}/{versoes[-1]}"})
    return itens


def baixar_ftp(url, destino):
    """Baixa por FTP. Devolve a data de modificação informada pelo servidor (ou '')."""
    partes = urlparse(url)
    ftp = ftplib.FTP(partes.hostname, timeout=120, encoding="latin-1")
    ftp.login()
    try:
        resposta = ftp.sendcmd(f"MDTM {partes.path}")  # ex.: '213 20220528101500'
        modificado = datetime.strptime(resposta.split()[1][:14], "%Y%m%d%H%M%S").isoformat(sep=" ")
    except Exception:
        modificado = ""  # nem todo servidor FTP responde ao MDTM
    with open(destino, "wb") as f:
        ftp.retrbinary(f"RETR {partes.path}", f.write)
    ftp.quit()
    return modificado


def baixar_http(url, destino):
    with urllib.request.urlopen(url, timeout=120) as resposta, open(destino, "wb") as f:
        conteudo = resposta.read()
        # A API do IBGE devolve o JSON em gzip mesmo sem pedir: descomprime para guardar o arquivo legível.
        if conteudo[:2] == b"\x1f\x8b":
            conteudo = gzip.decompress(conteudo)
        f.write(conteudo)
        return resposta.headers.get("Last-Modified", "")


def baixar_item(item):
    nome = item.get("arquivo") or Path(urlparse(item["url"]).path).name
    pasta = PASTA_DOMINIO / item["fonte"]
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / nome
    parcial = destino.with_name(destino.name + ".part")  # só vira o nome final se terminar inteiro

    baixar = baixar_ftp if item["url"].startswith("ftp") else baixar_http
    modificado = baixar(item["url"], parcial)
    parcial.replace(destino)

    registrar_no_manifesto({
        "arquivo": nome, "sistema": "DOMINIO", "grupo": item["fonte"], "uf": "", "periodo": item["periodo"],
        "bytes": destino.stat().st_size, "sha256": calcular_sha256(destino),
        "dbc_bytes": "", "dbc_sha256": "",
        "modificado_ftp": modificado, "caminho_ftp": item["url"],
        "data_download": datetime.now().isoformat(sep=" ", timespec="seconds"),
    })
    return destino


if __name__ == "__main__":
    manifesto = ler_manifesto()
    feitos = set(zip(manifesto["grupo"][manifesto["sistema"] == "DOMINIO"],
                     manifesto["arquivo"][manifesto["sistema"] == "DOMINIO"]))
    falhas = []
    for item in config.DOMINIOS + itens_sigtap_por_competencia():
        nome = item.get("arquivo") or Path(urlparse(item["url"]).path).name
        if (item["fonte"], nome) in feitos and (PASTA_DOMINIO / item["fonte"] / nome).exists():
            print(f"já baixado: {item['fonte']}/{nome}")
            continue
        print(f"baixando {item['fonte']}/{nome} ...")
        try:
            destino = baixar_item(item)
            print(f"  ok, {destino.stat().st_size / 1024:.0f} KB")
        except Exception as erro:
            print(f"  FALHOU: {erro}")
            falhas.append(nome)
    print(f"\nConcluído. Falhas: {len(falhas)}" + (f" -> {falhas}" if falhas else ""))
