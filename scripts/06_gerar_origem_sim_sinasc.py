"""Gera a origem simulada do SIM (óbitos, 9 tabelas) e do SINASC (nascimentos, 5 tabelas).

Uso:  python scripts/06_gerar_origem_sim_sinasc.py [--todas]
Chave: UF + ANO + CONTADOR. DT_TRANSACAO = data do evento + 30 dias.
"""

import config
import origem

DIAS_DE_DEFASAGEM = 30  # suposição: o registro chega ao sistema 30 dias depois do evento
EVENTO = {("SIM", "DO"): "DTOBITO", ("SINASC", "DN"): "DTNASC"}  # coluna com a data do evento, no formato DDMMAAAA


def gerar_grupo(con, mapa, saida, sistema, grupo, uf, sal):
    if origem.carregar_bruto(con, sistema, grupo, uf, "bruto") == 0:
        print(f"  {sistema}-{grupo}: sem linhas para {uf}")
        return
    evento = EVENTO[(sistema, grupo)]
    # o arquivo é anual: o ano do arquivo entra na chave
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE base AS
        SELECT *, periodo AS ANO, CAST(try_strptime({evento}, '%d%m%Y') AS DATE) + {DIAS_DE_DEFASAGEM} AS DT_TRANSACAO
        FROM bruto""")
    sem_data = con.execute("SELECT count(*) FROM base WHERE DT_TRANSACAO IS NULL").fetchone()[0]
    if sem_data:
        raise SystemExit(f"{sem_data} linhas de {sistema}-{grupo} ({uf}) com {evento} inválida: não deveria acontecer (ver exploração).")

    chave = list(config.CHAVE_UNICA[(sistema, grupo)])
    principal = f"{sistema}/{grupo}/{config.ASSUNTO_PRINCIPAL[(sistema, grupo)]}"
    for assunto in origem.assuntos_do_grupo(mapa, sistema, grupo):
        colunas = origem.colunas_do_assunto(mapa, sistema, grupo, assunto)
        esparsa = assunto in config.TABELAS_ESPARSAS.get((sistema, grupo), [])
        filtro = " OR ".join(origem.sql_preenchido(c) for c in colunas) if esparsa else None
        origem.montar_tabela(con, "t", "base", sistema, grupo, colunas, sal, filtro=filtro)
        pai = "" if assunto == config.ASSUNTO_PRINCIPAL[(sistema, grupo)] else principal
        origem.gravar_tabela(con, "t", saida, sistema, grupo, assunto, uf, "esparsa" if esparsa else "plana", chave, pai)


def main():
    ufs, saida = origem.ler_argumentos("Gera a origem simulada do SIM e do SINASC.")
    sal, mapa, con = origem.carregar_sal(), origem.ler_mapa(), origem.abrir_duckdb("sim_sinasc")
    for uf in ufs:
        print(f"SIM e SINASC {uf}")
        for sistema, grupo in EVENTO:
            gerar_grupo(con, mapa, saida, sistema, grupo, uf, sal)
    origem.salvar_catalogo(saida)


if __name__ == "__main__":
    main()
