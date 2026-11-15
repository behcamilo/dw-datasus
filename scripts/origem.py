"""Funções usadas na geração da origem simulada (scripts 05 a 09).

A origem fica em dados/origem/<sistema>/<grupo>/<assunto>/uf=XX/mes=AAAA-MM/dados.parquet: uma tabela por assunto, com DT_TRANSACAO.
"""

import argparse
import os
import shutil
import time
from datetime import date, timedelta
from pathlib import Path

import duckdb
import pandas as pd

import config
from manifesto import ler_manifesto

CATALOGO = []  # tabelas geradas nesta execução; vão para dados/origem/_catalogo.csv


# Linha de comando

def ler_argumentos(descricao, grupos=None):
    """Devolve (UFs, pasta de saída) ou, com `grupos`, (UFs, pasta, grupos escolhidos)."""
    parser = argparse.ArgumentParser(description=descricao)
    if grupos:
        parser.add_argument("--grupos", nargs="+", choices=grupos, default=grupos, help="grupos a gerar (padrão: todos)")
    parser.add_argument("--ufs", nargs="+", default=config.UFS_PADRAO_DA_ORIGEM, help="UFs a gerar (padrão: RR)")
    parser.add_argument("--todas", action="store_true", help="gera as 27 UFs")
    parser.add_argument("--saida", default=str(config.PASTA_ORIGEM), help="pasta de saída (o script 09 usa outra para testar o determinismo)")
    args = parser.parse_args()
    ufs = config.UFS if args.todas else args.ufs
    return (ufs, Path(args.saida), args.grupos) if grupos else (ufs, Path(args.saida))


def carregar_sal():
    """Sal do hash de dados pessoais (config_local.py, fora do git)."""
    try:
        import config_local
    except ImportError:
        raise SystemExit("Falta scripts/config_local.py: copie config_local.exemplo.py e troque o valor do sal.")
    return config_local.SAL_HASH_PII


# Calendário de dias úteis

def dias_uteis(ano, mes):
    """Dias de segunda a sexta do mês, sem feriados nacionais."""
    dia, dias = date(ano, mes, 1), []
    while dia.month == mes:
        if dia.weekday() < 5 and dia not in config.FERIADOS_NACIONAIS:
            dias.append(dia)
        dia += timedelta(days=1)
    return dias


def mes_seguinte(periodo):
    """'2021-12' -> (2022, 1)."""
    ano, mes = int(periodo[:4]), int(periodo[5:7])
    return (ano + 1, 1) if mes == 12 else (ano, mes + 1)


def calendario_de_distribuicao(periodos):
    """Dias úteis de M+1 para cada competência M (usado para espalhar o SIH pelos dias)."""
    linhas = []
    for periodo in sorted(set(periodos)):
        dias = dias_uteis(*mes_seguinte(periodo))
        linhas += [{"periodo": periodo, "idx": i, "dias": len(dias), "data": d} for i, d in enumerate(dias)]
    return pd.DataFrame(linhas)


def quinto_dia_util_do_mes_seguinte(periodo):
    """Data em que a foto da competência M (CNES, SIGTAP) chega na origem."""
    return dias_uteis(*mes_seguinte(periodo))[4]


def primeiro_dia_util_do_ano(ano):
    return dias_uteis(ano, 1)[0]


# DuckDB e SQL

def nome_sql(expr):
    """Nome de coluna entre aspas (há colunas com nome reservado, como NATURAL); expressões ficam como estão."""
    return f'"{expr}"' if expr.replace("_", "a").isalnum() else expr


def abrir_duckdb(nome):
    con = duckdb.connect()
    con.execute(f"SET memory_limit='{config.MEMORIA_DUCKDB}'")
    con.execute(f"SET threads={config.THREADS_DUCKDB}")
    temp = config.PASTA_TEMP_DUCKDB / f"origem_{nome}"
    temp.mkdir(parents=True, exist_ok=True)
    con.execute(f"SET temp_directory='{temp.as_posix()}'")
    return con


def sql_preenchido(expr):
    """Valor preenchido: não nulo, não vazio, nem só zeros, nem só noves (sentinelas)."""
    expr = nome_sql(expr)
    v = f"trim({expr})"
    return f"({expr} IS NOT NULL AND {v} <> '' AND NOT regexp_matches({v}, '^0+$') AND NOT regexp_matches({v}, '^9{{3,}}$'))"


def sql_hash(expr, sal):
    """sha256(sal + valor); vazio ou sentinela vira NULL."""
    return f"(CASE WHEN {sql_preenchido(expr)} THEN sha256('{sal}' || trim({nome_sql(expr)})) END)"


def sql_cpf_valido(expr):
    """O valor é um CPF válido (3 zeros + 11 dígitos com dígitos verificadores corretos; 7 zeros iniciais é CNES)."""
    s = f"trim({nome_sql(expr)})"
    d = [f"TRY_CAST(substr({s}, {i}, 1) AS INTEGER)" for i in range(4, 15)]
    soma1 = " + ".join(f"{d[i]} * {10 - i}" for i in range(9))
    soma2 = " + ".join(f"{d[i]} * {11 - i}" for i in range(10))
    return (f"(regexp_matches({s}, '^000[0-9]{{11}}$') AND NOT regexp_matches({s}, '^0{{7}}') "
            f"AND (({soma1}) * 10 % 11) % 10 = {d[9]} AND (({soma2}) * 10 % 11) % 10 = {d[10]})")


def expressao_da_coluna(sistema, grupo, coluna, sal):
    """A coluna como vai para a origem: com hash se for documento de pessoa."""
    if coluna in config.COLUNAS_COM_HASH.get((sistema, grupo), []):
        return sql_hash(coluna, sal)
    se_cpf = config.COLUNAS_COM_HASH_SE_CPF.get((sistema, grupo))
    if se_cpf and coluna == se_cpf[0]:
        condicao = se_cpf[1] or sql_cpf_valido(coluna)
        return f"(CASE WHEN {condicao} THEN {sql_hash(coluna, sal)} ELSE {nome_sql(coluna)} END)"
    return nome_sql(coluna)


# Mapa de assuntos

def ler_mapa():
    return pd.read_csv(config.RAIZ / "docs" / "mapa_assuntos.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)


def assuntos_do_grupo(mapa, sistema, grupo):
    """Assuntos do grupo que viram tabela, na ordem do mapa."""
    p = mapa[(mapa["sistema"] == sistema) & (mapa["grupo"] == grupo) & ~mapa["assunto"].isin(config.ASSUNTOS_FORA)]
    return list(dict.fromkeys(p["assunto"]))


def colunas_do_assunto(mapa, sistema, grupo, assunto):
    p = mapa[(mapa["sistema"] == sistema) & (mapa["grupo"] == grupo) & (mapa["assunto"] == assunto)]
    return list(p["coluna_original"])


# Domínios

def dominios_conceituais():
    """Tabela de domínio de cada coluna (docs/dominios_usados.csv): DataFrame com coluna, tabela, pacote, tipo e linhas.

    Quando a coluna tem mais de uma tabela, vale a oficial de código (CID-10, IBGE, SIGTAP) ou, nas outras, a mais detalhada (mais linhas).
    """
    usados = pd.read_csv(config.RAIZ / "docs" / "dominios_usados.csv", encoding="utf-8-sig")
    mapa = ler_mapa()
    assunto = dict(zip(zip(mapa["sistema"], mapa["grupo"], mapa["coluna_original"]), mapa["assunto"]))
    fora = {(s, g, c) for (s, g), cols in config.COLUNAS_FORA.items() for c in cols}
    fica = [(s, g, c) not in fora and assunto.get((s, g, c)) not in config.ASSUNTOS_FORA
            for s, g, c in zip(usados["sistema"], usados["grupo"], usados["coluna"])]
    usados = usados[fica & ~usados["tabela"].str.startswith("(NÃO ENCONTRADA)").to_numpy()].assign(coluna=lambda d: d["coluna"].str.lower(), linhas=lambda d: d["linhas"].fillna(0),
                                 por_codigo=lambda d: d["forma de ligação"].str.startswith("código"))
    principal = (usados.sort_values(["coluna", "por_codigo", "linhas", "tabela"], ascending=[True, False, False, True])
                 .drop_duplicates("coluna"))
    return principal[["coluna", "tabela", "pacote", "tipo", "linhas"]].reset_index(drop=True)


# Leitura dos Parquet baixados

def periodos_da_uf(sistema, grupo, uf):
    """Competências (AAAA-MM) ou anos (AAAA) que o grupo tem na UF."""
    return list(arquivos_da_uf(sistema, grupo, uf)["periodo"])


def arquivos_da_uf(sistema, grupo, uf, periodo=None):
    """Arquivos baixados do grupo na UF (pelo manifesto): caminho, nome, período e nome sem extensão."""
    m = ler_manifesto()
    m = m[(m["sistema"] == sistema) & (m["grupo"] == grupo) & (m["uf"] == uf)].drop_duplicates("arquivo", keep="last")
    m = m[m["periodo"].str[:4].astype(int).isin(config.ANOS)].sort_values("arquivo")
    linhas = []
    for _, r in m.iterrows():
        stem = r["arquivo"].rsplit(".", 1)[0]
        caminho = config.PASTA_RAW / sistema / grupo / (stem + ".parquet")
        if caminho.exists():
            linhas.append({"caminho": caminho.as_posix(), "nome": caminho.name, "periodo": r["periodo"], "stem": stem})
    arquivos = pd.DataFrame(linhas, columns=["caminho", "nome", "periodo", "stem"])
    return arquivos if periodo is None else arquivos[arquivos["periodo"] == periodo]


def carregar_bruto(con, sistema, grupo, uf, nome="bruto", periodo=None):
    """Carrega o grupo da UF (ou só uma competência) na tabela temporária `nome`, com período, arquivo e número da linha.
    Devolve quantas linhas carregou (0 quando não há arquivo ou ele está vazio)."""
    arquivos = arquivos_da_uf(sistema, grupo, uf, periodo)
    if arquivos.empty:
        return 0
    con.register("arquivos_tmp", arquivos)
    lista = ", ".join(f"'{c}'" for c in arquivos["caminho"])
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE {nome} AS
        SELECT o.* EXCLUDE (filename, file_row_number), a.periodo, a.stem, o.file_row_number AS linha
        FROM read_parquet([{lista}], union_by_name=true, filename=true, file_row_number=true) o
        JOIN arquivos_tmp a ON regexp_extract(o.filename, '([^/\\\\]+)$', 1) = a.nome""")
    return con.execute(f"SELECT count(*) FROM {nome}").fetchone()[0]


def sql_id_origem():
    """Identificador de linha sem chave natural: arquivo:linha (ex.: RDRR2101:000000012)."""
    return "stem || ':' || lpad(CAST(linha AS VARCHAR), 9, '0')"


# Gravação

def escrever_particoes(con, tabela_temp, destino, chave, limpar=True):
    """Grava um Parquet por mês de DT_TRANSACAO, ordenado pela chave (rodar de novo gera o mesmo arquivo). Devolve (linhas, meses)."""
    if limpar:
        shutil.rmtree(destino, ignore_errors=True)
    ordem = ", ".join(["DT_TRANSACAO"] + [nome_sql(c) for c in chave])
    meses = [r[0] for r in con.execute(f"SELECT DISTINCT strftime(DT_TRANSACAO, '%Y-%m') FROM {tabela_temp} ORDER BY 1").fetchall()]
    for mes in meses:
        pasta = destino / f"mes={mes}"
        pasta.mkdir(parents=True)
        con.execute(f"COPY (SELECT * FROM {tabela_temp} WHERE strftime(DT_TRANSACAO, '%Y-%m') = '{mes}' ORDER BY {ordem}) "
                    f"TO '{(pasta / 'dados.parquet').as_posix()}' (FORMAT parquet, COMPRESSION zstd)")
    return con.execute(f"SELECT count(*) FROM {tabela_temp}").fetchone()[0], len(meses)


def limpar_tabela(saida, sistema, grupo, assunto, uf):
    """Apaga a tabela da UF antes de gravá-la competência por competência."""
    shutil.rmtree(saida / sistema / grupo / assunto / f"uf={uf}", ignore_errors=True)


def gravar_tabela(con, tabela_temp, saida, sistema, grupo, assunto, uf, tipo, chave, pai="", acumular=False):
    """Grava a tabela do assunto na UF e registra no catálogo. Com acumular=True, soma à tabela já gravada (uma competência por vez)."""
    linhas, meses = escrever_particoes(con, tabela_temp, saida / sistema / grupo / assunto / f"uf={uf}", chave, limpar=not acumular)
    existente = next((c for c in CATALOGO if (c["sistema"], c["grupo"], c["assunto"], c["uf"]) == (sistema, grupo, assunto, uf)), None)
    if acumular and existente:
        existente["linhas"] += linhas
        existente["arquivos"] += meses
    else:
        CATALOGO.append({"sistema": sistema, "grupo": grupo, "assunto": assunto, "uf": uf, "tipo": tipo,
                         "chave": ",".join(chave), "pai": pai, "linhas": linhas, "arquivos": meses})
    if not acumular:
        print(f"  {sistema}/{grupo}/{assunto} ({uf}): {linhas:,} linhas em {meses} mês(es)")
    return linhas


def resumir_catalogo(uf, grupo=None):
    """Mostra o total de linhas das tabelas gravadas na UF."""
    for c in CATALOGO:
        if c["uf"] == uf and c["tipo"] != "dominio" and grupo in (None, c["grupo"]):
            print(f"  {c['sistema']}/{c['grupo']}/{c['assunto']} ({uf}): {c['linhas']:,} linhas em {c['arquivos']} mês(es)")


def montar_tabela(con, nome, base, sistema, grupo, colunas, sal, com_id=False, filtro=None, extras=None):
    """Monta a tabela do assunto a partir de `base`: chave do grupo, colunas do assunto (com hash quando preciso) e DT_TRANSACAO."""
    chave = config.CHAVE_REPETIDA[(sistema, grupo)]
    fora = config.COLUNAS_FORA.get((sistema, grupo), [])
    resto = [c for c in colunas if c not in chave and c not in fora]
    selecao = [nome_sql(c) for c in chave]
    if com_id:
        selecao.append(f"{sql_id_origem()} AS id_origem")
    selecao += [f"{expressao_da_coluna(sistema, grupo, c, sal)} AS {nome_sql(c)}" for c in resto]
    selecao += list(extras or []) + ["DT_TRANSACAO"]
    where = f"WHERE {filtro}" if filtro else ""
    con.execute(f"CREATE OR REPLACE TEMP TABLE {nome} AS SELECT {', '.join(selecao)} FROM {base} {where}")


def salvar_catalogo(saida, substituir_sistema=None):
    """Atualiza dados/origem/_catalogo.csv com as tabelas desta execução (`substituir_sistema` apaga antes as do sistema).
    Uma trava deixa só um processo por vez gravar, porque várias UFs podem ser geradas em paralelo."""
    saida.mkdir(parents=True, exist_ok=True)
    trava = saida / "_catalogo.lock"
    while True:
        try:
            os.close(os.open(trava, os.O_CREAT | os.O_EXCL))
            break
        except (FileExistsError, PermissionError):  # no Windows, a trava sendo apagada dá PermissionError
            time.sleep(0.2)
    try:
        arquivo = saida / "_catalogo.csv"
        novo = pd.DataFrame(CATALOGO)
        if arquivo.exists() and not novo.empty:
            antigo = pd.read_csv(arquivo, dtype=str, keep_default_na=False)
            antigo = antigo[antigo["sistema"] != substituir_sistema]
            chaves_novas = set(zip(novo["sistema"], novo["grupo"], novo["assunto"], novo["uf"]))
            antigo = antigo[[(s, g, a, u) not in chaves_novas for s, g, a, u in zip(antigo["sistema"], antigo["grupo"], antigo["assunto"], antigo["uf"])]]
            novo = pd.concat([antigo, novo.astype(str)], ignore_index=True)
        if not novo.empty:
            novo.sort_values(["sistema", "grupo", "assunto", "uf"]).to_csv(arquivo, index=False)
    finally:
        os.remove(trava)
    CATALOGO.clear()
