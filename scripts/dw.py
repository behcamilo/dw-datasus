"""Funções usadas pelos scripts do DW (10 a 17): nomes de tabelas, conexão, inventário da origem e escrita de modelos dbt."""

import psycopg2

import config


def nome_tabela(camada, sistema, grupo, assunto, uf=None):
    """<camada>_<sistema>_<grupo>_<assunto>[_<uf>], minúsculo. Ex.: stg_cad_cnes_st_identificacao_rr."""
    partes = [camada, sistema, grupo, assunto] + ([uf] if uf else [])
    return "_".join(partes).lower()


def destino_da_stage(stage):
    """Tabela do DW que consome a stage (o profissional do SIH-SP é cadastro no DW, mas stage de movimento)."""
    camada_dw = "int_cad" if stage.startswith("stg_cad_") or stage.startswith("stg_mov_sih_sp_profissional_") else "int_mov"
    resto = stage.split("_", 2)[2]  # stg_cad_<resto> ou stg_mov_<resto>
    return camada_dw, f"{camada_dw}_{resto}"


def conectar():
    return psycopg2.connect(**config.DW_POSTGRES)


# Inventário da origem (usado pelos scripts 10 a 13)
import glob
import os

import duckdb
import pandas as pd

UFS = [uf.lower() for uf in config.UFS]


def ler_tabelas_da_origem():
    """Uma linha por (sistema, grupo, assunto), com tipo, chave e pai."""
    catalogo = pd.read_csv(f"{config.PASTA_ORIGEM}/_catalogo.csv").fillna("")
    catalogo = catalogo[catalogo.sistema != "DOMINIO"]  # os domínios são tratados à parte (ler_dominios)
    tabelas = catalogo.drop_duplicates(["sistema", "grupo", "assunto"])[["sistema", "grupo", "assunto", "tipo", "chave", "pai", "uf"]]
    return tabelas.sort_values(["sistema", "grupo", "assunto"]).to_dict("records")


def colunas_do_parquet(arquivo):
    con = duckdb.connect()
    return [c[0] for c in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{arquivo}', hive_partitioning=false)").fetchall()]


def colunas_da_tabela(tabela):
    """Colunas da tabela da origem (lidas de um arquivo de qualquer UF)."""
    arquivo = sorted(glob.glob(f"{config.PASTA_ORIGEM}/{tabela['sistema']}/{tabela['grupo']}/{tabela['assunto']}/uf={tabela['uf']}/*/dados.parquet"))[0]
    return [c.lower() for c in colunas_do_parquet(arquivo)]


def chave_do_dominio(colunas, nome=""):
    """Chave de uma tabela de domínio, pelo formato das colunas."""
    if nome in config.CHAVE_DOMINIO_EXCECAO:
        return config.CHAVE_DOMINIO_EXCECAO[nome]
    if nome in config.DOMINIOS_SEM_CHAVE:
        return [c.lower() for c in colunas if c != "DT_TRANSACAO"]
    if "SEQ" in colunas:
        return ["seq", "codigo"]  # conversão do TabWin: o mesmo código pode estar em mais de uma categoria (faixas que se sobrepõem)
    if "CODIGO" in colunas:
        return ["codigo"]
    if "COMPETENCIA" in colunas:
        # SIGTAP: códigos + competência; nas tabelas de relação (rl_), todos os códigos
        codigos = [c for c in colunas if c.startswith(("CO_", "NU_"))]
        if not nome.startswith("sigtap_rl_"):
            codigos = codigos[:next((i for i, c in enumerate(colunas) if not c.startswith(("CO_", "NU_"))), len(colunas))]
        return [c.lower() for c in codigos] + ["competencia"]
    if "CNPJ_MANT" in colunas:
        return ["cnpj_mant", "compet"]
    if "COD_MUN" in colunas:
        return ["cod_mun", "ano", "sexo", "idade"]
    if "MUNIC_RES" in colunas:
        return ["munic_res", "ano"]
    return [colunas[0].lower()]


def ler_dominios():
    dominios = []
    for pasta in sorted(glob.glob(f"{config.PASTA_ORIGEM}/DOMINIO/*")):
        colunas = colunas_do_parquet(sorted(glob.glob(pasta + "/*/dados.parquet"))[0])
        nome = os.path.basename(pasta)
        dominios.append({"nome": nome, "chave": chave_do_dominio(colunas, nome), "colunas": [c.lower() for c in colunas]})
    return dominios


# Escrita de modelos dbt (usada pelos scripts 11 a 13)
def bloco_config(camada, tags, meta, materializacao="table", estrategia=None, chave=None, unico=True):
    """Monta o {{ config(...) }} do modelo; nos incrementais, com índice único na chave."""
    linhas = [f"materialized='{materializacao}'", f"schema='{camada}'", f"tags={tags!r}"]
    if estrategia:
        linhas += [f"incremental_strategy='{estrategia}'", f"unique_key={chave!r}",
                   f"indexes=[{{'columns': {chave!r}, 'unique': {unico}}}]"]
    linhas.append(f"meta={meta!r}")
    return "{{ config(\n    " + ",\n    ".join(linhas) + "\n) }}\n"


def escrever_modelo(pasta_modelos, camada, nome, cabecalho, corpo):
    pasta = f"{pasta_modelos}/{camada}"
    os.makedirs(pasta, exist_ok=True)
    with open(f"{pasta}/{nome}.sql", "w", encoding="utf-8") as f:
        f.write(cabecalho + corpo.strip() + "\n")


def meta_de(sistema, grupo, assunto, uf, tipo_carga, chave, descricao):
    return {"sistema_origem": sistema, "grupo": grupo, "assunto": assunto, "uf": uf, "tipo_carga": tipo_carga,
            "chave_negocio": ",".join(chave), "descricao": descricao}



