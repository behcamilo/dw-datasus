"""Lista os arquivos do recorte no FTP do DATASUS, sem baixar.

Gera: docs/inventario.csv e um resumo na tela (arquivos e MB por sistema, grupo e ano).
"""

import pandas as pd

import config
from ftp_datasus import descrever, listar_arquivos


def montar_inventario():
    linhas = []
    ultimo_ano = {}  # último ano publicado de cada sistema, antes de filtrar pelo recorte
    for sistema, grupos in config.SISTEMAS_E_GRUPOS.items():
        print(f"Listando {sistema} no FTP...")
        for arquivo in listar_arquivos(sistema, grupos):
            info = descrever(arquivo)
            if info["grupo"] not in grupos or not info["ano"]:
                continue  # outro grupo, ou nome de arquivo não reconhecido
            ultimo_ano[sistema] = max(ultimo_ano.get(sistema, 0), info["ano"])
            if info["ano"] in config.ANOS and info["uf"] in config.UFS:
                linhas.append(info)
    inventario = pd.DataFrame(linhas)
    inventario = inventario.sort_values(["sistema", "grupo", "ano", "mes", "uf"]).reset_index(drop=True)
    return inventario, ultimo_ano


def mostrar_resumo(inventario, ultimo_ano):
    inventario = inventario.assign(mb=inventario["tamanho_bytes"] / 1024**2)

    print(f"\n=== Resumo por sistema, grupo e ano ({len(config.UFS)} UFs) ===")
    por_ano = inventario.groupby(["sistema", "grupo", "ano"]).agg(
        arquivos=("arquivo", "count"), mb=("mb", "sum")
    )
    print(por_ano.round(1).to_string())

    print("\n=== Total por sistema e grupo (tamanho do .dbc, comprimido) ===")
    por_grupo = inventario.groupby(["sistema", "grupo"]).agg(
        arquivos=("arquivo", "count"), mb=("mb", "sum")
    )
    print(por_grupo.round(1).to_string())
    print(f"TOTAL: {len(inventario)} arquivos, {inventario['mb'].sum() / 1024:.1f} GB")

    print("\n=== Último ano publicado no FTP (em qualquer UF) ===")
    for sistema, ano in ultimo_ano.items():
        print(f"{sistema}: {ano}")


if __name__ == "__main__":
    inventario, ultimo_ano = montar_inventario()
    config.ARQUIVO_INVENTARIO.parent.mkdir(parents=True, exist_ok=True)
    inventario.to_csv(config.ARQUIVO_INVENTARIO, index=False)
    print(f"\n{len(inventario)} arquivos salvos em {config.ARQUIVO_INVENTARIO}")
    mostrar_resumo(inventario, ultimo_ano)
