"""Lista os arquivos do FTP oficial do DATASUS (scripts 01 e 02) com as classes de dataset do PySUS.

Não usa `source="origin"`: no PySUS 2.11.7 ele consulta um espelho, e não o FTP oficial.
"""

import asyncio

from pysus.api.ftp import databases
from pysus.api.ftp.client import FTP

CLASSE_DO_SISTEMA = {
    "SIH": databases.SIH,
    "CNES": databases.CNES,
    "SIM": databases.SIM,
    "SINASC": databases.SINASC,
    "SIA": databases.SIA,  # fora do recorte
}


async def _listar(sistema, grupos):
    cliente = FTP()
    await cliente.connect()
    try:
        arquivos = []
        for item in await CLASSE_DO_SISTEMA[sistema](client=cliente).content:
            if hasattr(item, "_fetch_files"):
                # o CNES tem uma subpasta por grupo: abre só as do recorte
                if item.name in grupos:
                    arquivos.extend(await item._fetch_files())
            else:
                arquivos.append(item)
        return arquivos
    finally:
        await cliente.close()


def listar_arquivos(sistema, grupos):
    """Devolve os objetos de arquivo (do PySUS) que existem no FTP para o sistema."""
    return asyncio.run(_listar(sistema, grupos))


def descrever(arquivo):
    """Resume um arquivo do PySUS num dicionário simples."""
    return {
        "sistema": arquivo.dataset.name,
        "grupo": arquivo.group.name if arquivo.group else None,
        "uf": arquivo.state,
        "ano": arquivo.year,
        "mes": arquivo.month,
        "arquivo": arquivo.name,
        "tamanho_bytes": arquivo.size,
        # muda quando o DATASUS republica o arquivo
        "modificado_ftp": arquivo.modify.isoformat(sep=" "),
        "caminho_ftp": str(arquivo.path).replace("\\", "/"),
    }
