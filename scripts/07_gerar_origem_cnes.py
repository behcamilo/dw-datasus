"""Gera a origem simulada do CNES (13 grupos, uma foto por mês).

Uso:  python scripts/07_gerar_origem_cnes.py [--todas | --ufs SP MG]
Processa uma competência por vez. DT_TRANSACAO = 5º dia útil do mês seguinte à competência.
Filhas do CNES-ST (instalações, serviços de apoio, comissões, convênios): uma linha por item preenchido.
"""

import pandas as pd

import config
import origem

GRUPOS = config.SISTEMAS_E_GRUPOS["CNES"]
FILHAS_ST = config.TABELAS_FILHAS_POR_ITEM[("CNES", "ST")]


def calcular_dt_transacao(con):
    """Tabela `base` com as linhas do grupo e a DT_TRANSACAO."""
    periodos = [r[0] for r in con.execute("SELECT DISTINCT periodo FROM bruto").fetchall()]
    datas = pd.DataFrame({"periodo": periodos, "data": [origem.quinto_dia_util_do_mes_seguinte(p) for p in periodos]})
    con.register("datas_cnes", datas)
    con.execute("CREATE OR REPLACE TEMP TABLE base AS SELECT b.*, d.data AS DT_TRANSACAO FROM bruto b JOIN datas_cnes d ON d.periodo = b.periodo")


def montar_filha_por_item(con, colunas):
    """Transforma as colunas do assunto em linhas (item, valor), só com os itens preenchidos."""
    lista = ", ".join(colunas)
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE t AS
        SELECT CNES, COMPETEN, item, valor, DT_TRANSACAO
        FROM (UNPIVOT (SELECT CNES, COMPETEN, DT_TRANSACAO, {lista} FROM base) ON {lista} INTO NAME item VALUE valor)
        WHERE {origem.sql_preenchido('valor')}""")


def gerar_grupo(con, mapa, saida, grupo, uf, sal):
    """Gera as tabelas do grupo, uma competência por vez."""
    sistema = "CNES"
    periodos = origem.periodos_da_uf(sistema, grupo, uf)
    if not periodos:
        print(f"  CNES-{grupo}: sem arquivos para {uf}")
        return
    chave = list(config.CHAVE_UNICA[(sistema, grupo)])
    principal = f"{sistema}/{grupo}/{config.ASSUNTO_PRINCIPAL[(sistema, grupo)]}"
    com_id = (sistema, grupo) in config.GRUPOS_COM_ID_ORIGEM
    assuntos = origem.assuntos_do_grupo(mapa, sistema, grupo)
    for assunto in assuntos:
        origem.limpar_tabela(saida, sistema, grupo, assunto, uf)
    for periodo in periodos:
        if origem.carregar_bruto(con, sistema, grupo, uf, "bruto", periodo) == 0:
            continue
        calcular_dt_transacao(con)
        for assunto in assuntos:
            colunas = origem.colunas_do_assunto(mapa, sistema, grupo, assunto)
            pai = "" if assunto == config.ASSUNTO_PRINCIPAL[(sistema, grupo)] else principal
            if grupo == "ST" and assunto in FILHAS_ST:
                montar_filha_por_item(con, colunas)
                origem.gravar_tabela(con, "t", saida, sistema, grupo, assunto, uf, "filha", ["CNES", "COMPETEN", "item"], pai, acumular=True)
            else:
                origem.montar_tabela(con, "t", "base", sistema, grupo, colunas, sal, com_id=com_id)
                origem.gravar_tabela(con, "t", saida, sistema, grupo, assunto, uf, "plana", chave, pai, acumular=True)
    origem.resumir_catalogo(uf, grupo)


def main():
    ufs, saida = origem.ler_argumentos("Gera a origem simulada do CNES.")
    sal, mapa, con = origem.carregar_sal(), origem.ler_mapa(), origem.abrir_duckdb("cnes_" + "_".join(ufs)[:30])
    for uf in ufs:
        print(f"CNES {uf}")
        for grupo in GRUPOS:
            gerar_grupo(con, mapa, saida, grupo, uf, sal)
    origem.salvar_catalogo(saida)


if __name__ == "__main__":
    main()
