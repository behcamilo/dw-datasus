"""Conta linhas e tamanho de todas as tabelas do PostgreSQL e salva em docs/execucoes/contagens_<rotulo>.json.

Uso: python scripts/16_contar_linhas.py carga_inicial
"""

import json
import os
import sys

import dw

SCHEMAS = ["stg_cad", "stg_mov", "int_cad", "int_mov", "dim", "fct", "agg", "expo", "ctl"]


def main():
    rotulo = sys.argv[1]
    conexao = dw.conectar()
    cur = conexao.cursor()
    cur.execute("""SELECT n.nspname, c.relname, pg_total_relation_size(c.oid)
                   FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE c.relkind = 'r' AND n.nspname = ANY(%s)""", (SCHEMAS,))
    resultado = {}
    for schema, tabela, bytes_ in cur.fetchall():
        cur.execute(f'SELECT count(*) FROM "{schema}"."{tabela}"')
        resultado[f"{schema}.{tabela}"] = {"linhas": cur.fetchone()[0], "bytes": bytes_}
    os.makedirs("docs/execucoes", exist_ok=True)
    with open(f"docs/execucoes/contagens_{rotulo}.json", "w") as f:
        json.dump(resultado, f)
    print(f"{len(resultado)} tabelas contadas -> contagens_{rotulo}.json")


if __name__ == "__main__":
    main()
