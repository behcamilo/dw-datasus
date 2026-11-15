"""Gera a origem simulada do SIH: RD (9 tabelas), SP (atos e profissionais) e RJ (AIH rejeitadas, os 9 assuntos do RD).

Uso:  python scripts/05_gerar_origem_sih.py                       # só RR
      python scripts/05_gerar_origem_sih.py --todas               # as 27 UFs
      python scripts/05_gerar_origem_sih.py --todas --grupos RJ   # só o RJ (o SP é gerado junto com o RD)

Processa uma competência por vez, para caber na memória (o SIH-SP de SP tem 83 milhões de atos).
DT_TRANSACAO: RD e RJ espalhados em blocos iguais pelos dias úteis do mês seguinte, na ordem de DT_SAIDA; o ato do SP herda a da AIH;
o profissional fica com a do primeiro ato em que aparece.
"""

import config
import origem

RD, SP, RJ = ("SIH", "RD"), ("SIH", "SP"), ("SIH", "RJ")


def calcular_dt_transacao_aih(con, periodo, bruto="bruto_rd", destino="rd"):
    """Tabela `destino` com as AIH (RD ou RJ) da competência e a DT_TRANSACAO de cada uma."""
    con.register("calendario", origem.calendario_de_distribuicao([periodo]))
    # A linha na posição p (de n, por DT_SAIDA) cai no dia útil (p * dias) // n: blocos iguais do primeiro ao último dia útil.
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE {destino} AS
        SELECT b.*, c.data AS DT_TRANSACAO
        FROM (SELECT *, row_number() OVER (ORDER BY DT_SAIDA, linha) - 1 AS posicao, count(*) OVER () AS total FROM {bruto}) b
        JOIN calendario c ON c.idx = (b.posicao * c.dias) // b.total""")


def montar_diagnostico(con, colunas, grupo=RD, base="rd"):
    """Uma linha por diagnóstico preenchido: principal (ordem 0), secundários (1 a 9) e CID de notificação."""
    chave = ", ".join(config.CHAVE_REPETIDA[grupo])
    blocos = [f"SELECT {chave}, 0 AS ordem, DIAG_PRINC AS cid, 'principal' AS tipo, DT_TRANSACAO FROM {base} WHERE {origem.sql_preenchido('DIAG_PRINC')}"]
    for i in range(1, 10):
        if f"DIAGSEC{i}" in colunas:  # o RJ não tem secundários
            tipo = f"TPDISEC{i}" if f"TPDISEC{i}" in colunas else "NULL"
            blocos.append(f"SELECT {chave}, {i}, DIAGSEC{i}, {tipo}, DT_TRANSACAO FROM {base} WHERE {origem.sql_preenchido(f'DIAGSEC{i}')}")
    blocos.append(f"SELECT {chave}, CAST(NULL AS INTEGER), CID_NOTIF, 'notificacao', DT_TRANSACAO FROM {base} WHERE {origem.sql_preenchido('CID_NOTIF')}")
    con.execute("CREATE OR REPLACE TEMP TABLE t AS " + " UNION ALL ".join(blocos))


def gerar_aih(con, mapa, saida, uf, sal, grupo=RD, base="rd"):
    """Grava os assuntos de um grupo de AIH (RD ou RJ)."""
    principal = f"{grupo[0]}/{grupo[1]}/{config.ASSUNTO_PRINCIPAL[grupo]}"
    for assunto in origem.assuntos_do_grupo(mapa, *grupo):
        colunas = origem.colunas_do_assunto(mapa, *grupo, assunto)
        chave, pai = list(config.CHAVE_UNICA[grupo]), "" if assunto == config.ASSUNTO_PRINCIPAL[grupo] else principal
        if assunto == "diagnostico":
            montar_diagnostico(con, colunas, grupo, base)
            tipo, chave = "filha", chave + ["ordem", "tipo"]
        elif assunto in config.TABELAS_ESPARSAS[grupo]:
            padrao = config.COLUNAS_VALOR_PADRAO.get(grupo, [])
            filtro = " OR ".join(origem.sql_preenchido(c) for c in colunas if c not in padrao)
            origem.montar_tabela(con, "t", base, *grupo, colunas, sal, filtro=filtro)
            tipo = "esparsa"
        else:
            origem.montar_tabela(con, "t", base, *grupo, colunas, sal)
            tipo = "plana"
        origem.gravar_tabela(con, "t", saida, *grupo, assunto, uf, tipo, chave, pai, acumular=True)


def gerar_sp(con, mapa, saida, uf, periodo, sal):
    if origem.carregar_bruto(con, *SP, uf, "bruto_sp", periodo) == 0:
        return
    # o ato herda a DT_TRANSACAO da AIH do RD (mesma chave)
    con.execute("""
        CREATE OR REPLACE TEMP TABLE sp AS
        SELECT s.*, r.DT_TRANSACAO FROM bruto_sp s
        LEFT JOIN rd r ON s.SP_NAIH = r.N_AIH AND s.SEQUENCIA = r.SEQUENCIA AND s.SP_AA = r.ANO_CMPT AND s.SP_MM = r.MES_CMPT""")
    sem_aih = con.execute("SELECT count(*) FROM sp WHERE DT_TRANSACAO IS NULL").fetchone()[0]
    if sem_aih:
        raise SystemExit(f"{sem_aih} atos do SIH-SP ({uf}, {periodo}) sem AIH correspondente no SIH-RD: não deveria acontecer.")

    # uma linha por ato, com a chave do profissional (documento com hash + CBO)
    colunas_ato = origem.colunas_do_assunto(mapa, *SP, "ato_profissional") + ["SP_PF_DOC", "SP_PF_CBO"]
    origem.montar_tabela(con, "t", "sp", *SP, colunas_ato, sal, com_id=True)
    # primeiro ato de cada profissional (vale a menor data entre as competências)
    con.execute("""INSERT INTO profissionais_acumulados
                   SELECT SP_PF_DOC, SP_PF_CBO, min(DT_TRANSACAO) FROM t WHERE SP_PF_DOC IS NOT NULL GROUP BY 1, 2""")
    origem.gravar_tabela(con, "t", saida, *SP, "ato_profissional", uf, "ato", ["id_origem"], "SIH/RD/internacao", acumular=True)


def gravar_profissional(con, saida, uf):
    """Uma linha por profissional (documento com hash + CBO), com a DT_TRANSACAO do primeiro ato."""
    con.execute("""CREATE OR REPLACE TEMP TABLE t AS
                   SELECT SP_PF_DOC, SP_PF_CBO, min(DT_TRANSACAO) AS DT_TRANSACAO FROM profissionais_acumulados GROUP BY 1, 2""")
    origem.gravar_tabela(con, "t", saida, *SP, "profissional", uf, "profissional", ["SP_PF_DOC", "SP_PF_CBO"])


def gerar_rj(con, mapa, saida, uf, sal):
    """AIH rejeitadas: mesmas regras do RD (não têm ato profissional)."""
    for assunto in origem.assuntos_do_grupo(mapa, *RJ):
        origem.limpar_tabela(saida, *RJ, assunto, uf)
    for periodo in origem.periodos_da_uf(*RJ, uf):
        if origem.carregar_bruto(con, *RJ, uf, "bruto_rj", periodo) == 0:
            continue
        calcular_dt_transacao_aih(con, periodo, "bruto_rj", "rj")
        gerar_aih(con, mapa, saida, uf, sal, RJ, "rj")


def gerar_rd_e_sp(con, mapa, saida, uf, sal):
    periodos = origem.periodos_da_uf(*RD, uf)
    print(f"SIH {uf}: {len(periodos)} competências")
    for assunto in origem.assuntos_do_grupo(mapa, *RD):
        origem.limpar_tabela(saida, *RD, assunto, uf)
    origem.limpar_tabela(saida, *SP, "ato_profissional", uf)
    con.execute("CREATE OR REPLACE TEMP TABLE profissionais_acumulados (SP_PF_DOC VARCHAR, SP_PF_CBO VARCHAR, DT_TRANSACAO DATE)")
    for periodo in periodos:
        if origem.carregar_bruto(con, *RD, uf, "bruto_rd", periodo) == 0:
            continue
        calcular_dt_transacao_aih(con, periodo)
        gerar_aih(con, mapa, saida, uf, sal)
        gerar_sp(con, mapa, saida, uf, periodo, sal)
    gravar_profissional(con, saida, uf)


def main():
    # o SP é gerado junto com o RD, porque o ato herda a data da AIH
    ufs, saida, grupos = origem.ler_argumentos("Gera a origem simulada do SIH (RD, SP e RJ).", grupos=["RD", "RJ"])
    sal, mapa, con = origem.carregar_sal(), origem.ler_mapa(), origem.abrir_duckdb("sih_" + "_".join(ufs)[:30])
    for uf in ufs:
        if "RD" in grupos:
            gerar_rd_e_sp(con, mapa, saida, uf, sal)
        if "RJ" in grupos:
            gerar_rj(con, mapa, saida, uf, sal)
        origem.resumir_catalogo(uf)
    origem.salvar_catalogo(saida)


if __name__ == "__main__":
    main()
