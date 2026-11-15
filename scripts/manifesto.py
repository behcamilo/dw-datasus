"""Funções do manifesto de downloads (dados/manifesto.csv), usadas pelos scripts 02 e 03."""

import csv
import hashlib
import os
import time
from contextlib import contextmanager

import pandas as pd

import config

COLUNAS_MANIFESTO = [
    "arquivo", "sistema", "grupo", "uf", "periodo",
    "bytes", "sha256",                      # do arquivo que fica em dados/raw/ (Parquet, ou o próprio arquivo de domínio)
    "dbc_bytes", "dbc_sha256",              # do .dbc original baixado do FTP (vazio nas tabelas de domínio)
    "modificado_ftp", "caminho_ftp", "data_download",
]


def calcular_sha256(caminho):
    hash_ = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            hash_.update(bloco)
    return hash_.hexdigest()


def ler_manifesto():
    if not config.ARQUIVO_MANIFESTO.exists():
        return pd.DataFrame(columns=COLUNAS_MANIFESTO)
    return pd.read_csv(config.ARQUIVO_MANIFESTO, dtype=str)


@contextmanager
def trava_do_manifesto(espera_maxima=600):
    """Deixa só um processo gravar por vez (o download pode rodar em paralelo). A trava é um arquivo criado de forma exclusiva;
    se ficar presa mais de `espera_maxima` segundos (processo interrompido), é apagada."""
    trava = config.ARQUIVO_MANIFESTO.with_suffix(".lock")
    inicio = time.time()
    while True:
        try:
            os.close(os.open(trava, os.O_CREAT | os.O_EXCL))
            break
        except (FileExistsError, PermissionError):  # no Windows, a trava sendo apagada dá PermissionError
            if time.time() - inicio > espera_maxima:
                trava.unlink(missing_ok=True)  # trava abandonada
            time.sleep(0.1)
    try:
        yield
    finally:
        trava.unlink(missing_ok=True)


def registrar_no_manifesto(linha):
    """Acrescenta uma linha (o manifesto só cresce)."""
    config.ARQUIVO_MANIFESTO.parent.mkdir(parents=True, exist_ok=True)
    with trava_do_manifesto():
        novo = not config.ARQUIVO_MANIFESTO.exists()
        with open(config.ARQUIVO_MANIFESTO, "a", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=COLUNAS_MANIFESTO)
            if novo:
                escritor.writeheader()
            escritor.writerow(linha)
