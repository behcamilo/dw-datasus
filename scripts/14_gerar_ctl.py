"""Gera ctl_tabela e ctl_lineage a partir do manifest.json do dbt (depois, `dbt seed` carrega no schema ctl).

ctl_tabela: uma linha por tabela (stages e modelos). ctl_lineage: uma linha por dependência direta.
Uso: cd dw_dbt && dbt parse --profiles-dir . && cd .. && python scripts/14_gerar_ctl.py && cd dw_dbt && dbt seed --profiles-dir .
"""

import hashlib
import json
import os

import pandas as pd

import config  # noqa: F401  (usa a raiz do projeto como diretório de trabalho)

MANIFEST = "dw_dbt/target/manifest.json"
PASTA_SEEDS = "dw_dbt/seeds"
DATA_INCLUSAO = "2021-12-31"  # data da carga inicial; fixa para o arquivo ser reprodutível
COLUNAS_META = ["sistema_origem", "grupo", "assunto", "uf", "tipo_carga", "chave_negocio", "descricao"]

# as três tabelas de controle não estão no manifest
TABELAS_CTL = [
    ("ctl_tabela", "Cadastro de todas as tabelas do DW (gerado do manifest do dbt)."),
    ("ctl_lineage", "Linhagem: dependência direta entre tabelas do DW (gerado do manifest do dbt)."),
    ("ctl_processo_carga", "Log de execução das cargas (extração e dbt), por tabela."),
]


def codigo_da_tabela(nome):
    """Código que depende só do nome: não muda quando o DW ganha ou perde tabelas."""
    return int.from_bytes(hashlib.blake2b(nome.encode(), digest_size=6).digest(), "big")


def meta_do_no(no):
    meta = no.get("meta") or no.get("config", {}).get("meta") or {}
    return {c: meta.get(c, "") for c in COLUNAS_META}


def main():
    manifesto = json.load(open(MANIFEST, encoding="utf-8"))
    nos = {**{k: v for k, v in manifesto["nodes"].items() if v["resource_type"] == "model"}, **manifesto["sources"]}

    tabelas, nome_de = [], {}
    for id_no, no in nos.items():
        nome = no["name"]
        nome_de[id_no] = nome
        tabelas.append({"cod_tabela": codigo_da_tabela(nome), "nome_tabela": nome, "camada": no["schema"], **meta_do_no(no), "ativo": True})
    for nome, descricao in TABELAS_CTL:
        tabelas.append({"cod_tabela": codigo_da_tabela(nome), "nome_tabela": nome, "camada": "ctl", "sistema_origem": "DW", "grupo": "CTL",
                        "assunto": nome, "uf": "", "tipo_carga": "FULL" if nome != "ctl_processo_carga" else "LOG", "chave_negocio": "", "descricao": descricao, "ativo": True})

    arestas = []
    for id_no, no in nos.items():
        if no["resource_type"] != "model":
            continue
        for pai in no["depends_on"]["nodes"]:
            if pai in nome_de:
                arestas.append({"cod_tabela_origem": codigo_da_tabela(nome_de[pai]), "cod_tabela_destino": codigo_da_tabela(no["name"]),
                                "ativo": True, "dt_inclusao": DATA_INCLUSAO})

    tabela = pd.DataFrame(tabelas).sort_values(["camada", "nome_tabela"])
    lineage = pd.DataFrame(arestas).drop_duplicates().sort_values(["cod_tabela_destino", "cod_tabela_origem"])
    if tabela["cod_tabela"].duplicated().any():
        raise SystemExit("Colisão de cod_tabela: aumentar o digest_size.")
    os.makedirs(PASTA_SEEDS, exist_ok=True)  # os seeds ficam fora do git, então a pasta não vem no clone
    tabela.to_csv(f"{PASTA_SEEDS}/ctl_tabela.csv", index=False)
    lineage.to_csv(f"{PASTA_SEEDS}/ctl_lineage.csv", index=False)
    print(f"ctl_tabela: {len(tabela)} tabelas | ctl_lineage: {len(lineage)} dependências")
    print(tabela.groupby("camada").size().to_string())


if __name__ == "__main__":
    main()
