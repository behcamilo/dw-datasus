"""Carrega as stages (schemas stg_cad e stg_mov) a partir da origem simulada: carga inicial ou delta do dia.

Uso:  python scripts/15_extrair_para_stage.py --data-ref 2021-12-31 --carga-inicial
      python scripts/15_extrair_para_stage.py --data-ref 2022-01-03 [--ufs RR SP]
      python scripts/15_extrair_para_stage.py --data-ref 2021-12-31 --carga-inicial --parte 2/4   # 2ª de 4 fatias, em paralelo

A data de referência é o DT_CARGA (dia da execução − 1).
  - movimento (stg_mov): linhas com DT_TRANSACAO depois da última carga (o maior DT_CARGA da tabela que consome a stage) e até a data.
    A última carga é lida aqui, fora do dbt, para a stage não depender do DW.
  - cadastro (stg_cad): a foto mais recente publicada até a data (na carga inicial, todas as fotos).
  - domínios: todas as versões publicadas até a data.
"""

import argparse
import glob
import os
import time

import pandas as pd

import config
import dw
import origem

TIPO_POSTGRES = {"VARCHAR": "text", "DATE": "date", "INTEGER": "integer", "BIGINT": "bigint", "DOUBLE": "double precision"}
PASTA_TMP = ".tmp"


def tabelas_da_uf(uf):
    """Stages da UF, pelo catálogo da origem."""
    catalogo = pd.read_csv(f"{config.PASTA_ORIGEM}/_catalogo.csv").fillna("")
    catalogo = catalogo[catalogo.sistema != "DOMINIO"]
    catalogo = catalogo[catalogo.linhas.astype(int) > 0]  # tabela sem linhas na UF vira stage vazia (abaixo)
    lista = []
    for linha in catalogo[catalogo.uf == uf].itertuples():
        cadastro = config.TIPO_DO_SISTEMA[linha.sistema] == "cadastro"
        camada = "stg_cad" if cadastro else "stg_mov"
        lista.append({"stage": dw.nome_tabela(camada, linha.sistema, linha.grupo, linha.assunto, uf.lower()), "camada": camada,
                      "arquivos": f"{config.PASTA_ORIGEM}/{linha.sistema}/{linha.grupo}/{linha.assunto}/uf={uf}/mes=*/dados.parquet"})
    # tabela que não existe na UF: stage vazia, com as colunas das outras UFs (o modelo do DW precisa dela)
    existentes = {(l.sistema, l.grupo, l.assunto) for l in catalogo[catalogo.uf == uf].itertuples()}
    for linha in catalogo.drop_duplicates(["sistema", "grupo", "assunto"]).itertuples():
        if (linha.sistema, linha.grupo, linha.assunto) not in existentes:
            camada = "stg_cad" if config.TIPO_DO_SISTEMA[linha.sistema] == "cadastro" else "stg_mov"
            lista.append({"stage": dw.nome_tabela(camada, linha.sistema, linha.grupo, linha.assunto, uf.lower()), "camada": camada, "vazia": True,
                          "arquivos": f"{config.PASTA_ORIGEM}/{linha.sistema}/{linha.grupo}/{linha.assunto}/uf={linha.uf}/mes=*/dados.parquet"})
    return lista


def dominios():
    lista = []
    for pasta in sorted(glob.glob(f"{config.PASTA_ORIGEM}/DOMINIO/*")):
        lista.append({"stage": "stg_cad_dominio_" + os.path.basename(pasta), "camada": "stg_cad", "dominio": True, "arquivos": pasta + "/mes=*/dados.parquet"})
    return lista


def marca_dagua(cur, stage):
    """Maior DT_CARGA da tabela do DW que consome a stage (None na carga inicial)."""
    schema, tabela = dw.destino_da_stage(stage)
    cur.execute("SELECT to_regclass(%s)", (f"{schema}.{tabela}",))
    if cur.fetchone()[0] is None:
        return None
    cur.execute(f"SELECT max(dt_carga) FROM {schema}.{tabela}")
    return cur.fetchone()[0]


def filtro_da_stage(item, data_ref, inicial, marca):
    if item.get("vazia"):
        return "false"
    if item["camada"] == "stg_mov":
        piso = f" AND DT_TRANSACAO > DATE '{marca}'" if marca and not inicial else ""
        return f"DT_TRANSACAO <= DATE '{data_ref}'{piso}"
    if item.get("dominio") or inicial:
        return f"DT_TRANSACAO <= DATE '{data_ref}'"
    # foto atual do CNES: só a competência mais recente já publicada na data de referência
    return (f"DT_TRANSACAO = (SELECT max(DT_TRANSACAO) FROM read_parquet('{item['arquivos']}', hive_partitioning=false)"
            f" WHERE DT_TRANSACAO <= DATE '{data_ref}')")


def carregar_stage(con, cur, item, filtro):
    """Recria a stage e copia as linhas (o DuckDB gera um CSV e o PostgreSQL lê com COPY)."""
    leitura = f"read_parquet('{item['arquivos']}', hive_partitioning=false, union_by_name=true)"
    colunas = con.execute(f"DESCRIBE SELECT * FROM {leitura}").fetchall()
    ddl = ", ".join(f'"{nome.lower()}" {TIPO_POSTGRES.get(tipo, "text")}' for nome, tipo, *_ in colunas)
    schema, stage = item["camada"], item["stage"]
    cur.execute(f"DROP TABLE IF EXISTS {schema}.{stage}")
    cur.execute(f"CREATE TABLE {schema}.{stage} ({ddl})")
    os.makedirs(PASTA_TMP, exist_ok=True)
    csv = os.path.abspath(f"{PASTA_TMP}/{stage}.csv").replace("\\", "/")
    # \N marca o NULL, para texto vazio e NULL continuarem diferentes
    con.execute(f"COPY (SELECT * FROM {leitura} WHERE {filtro}) TO '{csv}' (FORMAT csv, HEADER false, NULLSTR '\\N')")
    with open(csv, encoding="utf-8") as f:
        cur.copy_expert(f"COPY {schema}.{stage} FROM STDIN WITH (FORMAT csv, NULL '\\N')", f)
    os.remove(csv)
    cur.execute(f"SELECT count(*) FROM {schema}.{stage}")
    return cur.fetchone()[0]


def main():
    parser = argparse.ArgumentParser(description="Extrai a origem simulada para as stages do PostgreSQL.")
    parser.add_argument("--data-ref", required=True, help="Data de referência AAAA-MM-DD (vira DT_CARGA)")
    parser.add_argument("--carga-inicial", action="store_true", help="Carga inicial: ignora a marca d'água e leva todas as fotos do CNES")
    parser.add_argument("--ufs", nargs="+", default=["RR"])
    parser.add_argument("--parte", default="1/1", help="K/N: este processo carrega só a K-ésima de N fatias das stages. "
                                                       "Rode N processos juntos para usar vários núcleos")
    argumentos = parser.parse_args()
    k, n = map(int, argumentos.parte.split("/"))

    con = origem.abrir_duckdb(f"extracao_stage_{k}")  # processos em paralelo não podem dividir a pasta temporária
    conexao = dw.conectar()
    cur = conexao.cursor()
    itens = [i for uf in argumentos.ufs for i in tabelas_da_uf(uf.upper())] + dominios()
    # fatias intercaladas: as stages de uma UF grande ficam espalhadas entre os processos
    itens = itens[k - 1::n]
    total_linhas, inicio_geral = 0, time.time()
    for item in itens:
        inicio = time.time()
        marca = None if argumentos.carga_inicial else marca_dagua(cur, item["stage"]) if item["camada"] == "stg_mov" else None
        filtro = filtro_da_stage(item, argumentos.data_ref, argumentos.carga_inicial, marca)
        linhas = carregar_stage(con, cur, item, filtro)
        segundos = round(time.time() - inicio, 3)
        cur.execute("INSERT INTO ctl.ctl_processo_carga (dt_referencia, etapa, objeto, linhas, segundos) VALUES (%s, 'extracao', %s, %s, %s)",
                    (argumentos.data_ref, item["stage"], linhas, segundos))
        conexao.commit()
        total_linhas += linhas
        print(f"{item['stage']:<60} {linhas:>10,} linhas  {segundos:>7.1f}s" + (f"  (marca d'água {marca})" if marca else ""), flush=True)
    print(f"FIM: {len(itens)} stages, {total_linhas:,} linhas, {time.time() - inicio_geral:.0f}s")


if __name__ == "__main__":
    main()
