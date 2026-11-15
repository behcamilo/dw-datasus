"""Escolhe as colunas de código que o movimento confere no cadastro.

Para cada coluna do movimento ligada a um domínio, mede em RR a fração dos valores que existe no cadastro; só se confere a coluna com
fração >= config.TAXA_MINIMA_VALIDACAO (as outras não são códigos de verdade). Município, CID, procedimento e ocupação são medidos
contra o cadastro consolidado; estabelecimento, contra o CNES-ST da UF.
Gera: docs/validacao_codigos.csv (usado pelo script 11).
"""

import glob

import pandas as pd

import config
import dw
import origem

UF_MEDIDA = "RR"
# a coluna "cid" da tabela de diagnósticos usa a CID-10
DOMINIO_ALTERNATIVO = {("SIH", g, "diagnostico", "cid"): "cid10_subcategorias" for g in ["RD", "RJ"]}


def taxa(con, arquivos, coluna, codigos_sql):
    """Fração das linhas (com valor preenchido) cujo valor aparece entre os códigos do cadastro."""
    linha = con.execute(f"""
        SELECT sum(n) FILTER (WHERE c.cod IS NOT NULL) / sum(n)
        FROM (SELECT cast("{coluna}" AS VARCHAR) AS v, count(*) AS n
              FROM read_parquet({arquivos}, hive_partitioning=false) WHERE "{coluna}" IS NOT NULL AND cast("{coluna}" AS VARCHAR) <> '' GROUP BY 1) t
        LEFT JOIN ({codigos_sql}) c ON c.cod = t.v""").fetchone()
    return linha[0]


def coluna_do_codigo(dominio):
    """Coluna do código no domínio: 'codigo' no TabWin; senão a primeira da chave."""
    return "codigo" if "codigo" in dominio["chave"] else dominio["chave"][0]


def codigos_do_dominio(dominios, nome):
    """SQL com os códigos do domínio (ou de todos os domínios que o consolidado reúne)."""
    cadastro, reunidos = config.CONSOLIDADOS.get(nome, (None, [nome]))
    partes = []
    for d in reunidos:
        arquivos = sorted(glob.glob(f"{config.PASTA_ORIGEM}/DOMINIO/{d}/*/dados.parquet"))
        partes.append(f"SELECT DISTINCT cast({coluna_do_codigo(dominios[d])} AS VARCHAR) AS cod FROM read_parquet({arquivos}, hive_partitioning=false)")
    return (f"consolidado_{cadastro}" if cadastro else f"dominio_{nome}"), " UNION ".join(partes)


def main():
    con = origem.abrir_duckdb("codigos")
    dominios = {d["nome"]: d for d in dw.ler_dominios()}
    origem_csv = pd.read_csv("docs/dominios_origem.csv", encoding="utf-8-sig", keep_default_na=False)
    dominio_da_coluna = {c: d for c, d, f in zip(origem_csv.coluna, origem_csv.dominio, origem_csv.fora) if not f}  # sem as datas
    codigos_cnes = (f"SELECT DISTINCT cast(CNES AS VARCHAR) AS cod FROM read_parquet("
                    f"{sorted(glob.glob(f'{config.PASTA_ORIGEM}/CNES/ST/identificacao/uf={UF_MEDIDA}/*/dados.parquet'))}, hive_partitioning=false)")
    resultado = []
    for tabela in dw.ler_tabelas_da_origem():
        if config.TIPO_DO_SISTEMA[tabela["sistema"]] != "movimento":
            continue
        arquivos = sorted(glob.glob(f"{config.PASTA_ORIGEM}/{tabela['sistema']}/{tabela['grupo']}/{tabela['assunto']}/uf={UF_MEDIDA}/*/dados.parquet"))
        if not arquivos:
            continue
        chave = tabela["chave"].lower().split(",")
        for coluna in dw.colunas_do_parquet(arquivos[0]):
            nome = coluna.lower()
            if nome in chave or nome in ("dt_transacao", "id_origem"):
                continue
            nome_dom = DOMINIO_ALTERNATIVO.get((tabela["sistema"], tabela["grupo"], tabela["assunto"], nome), dominio_da_coluna.get(nome))
            if nome in config.COLUNAS_DE_ESTABELECIMENTO:
                cadastro, sql = "cnes_uf", codigos_cnes
            elif nome_dom in dominios:
                cadastro, sql = codigos_do_dominio(dominios, nome_dom)
            else:
                continue
            t = taxa(con, arquivos, coluna, sql)
            resultado.append({"sistema": tabela["sistema"], "grupo": tabela["grupo"], "assunto": tabela["assunto"], "coluna": nome,
                              "cadastro": cadastro, "taxa": round(t, 4) if t is not None else 0})
    df = pd.DataFrame(resultado)
    df["validar"] = df.taxa >= config.TAXA_MINIMA_VALIDACAO
    df.to_csv("docs/validacao_codigos.csv", index=False)
    print(f"{len(df)} colunas candidatas, {int(df.validar.sum())} serão validadas (taxa >= {config.TAXA_MINIMA_VALIDACAO})")
    print(df.groupby(["sistema", "grupo", "assunto"]).validar.agg(["sum", "count"]).to_string())


if __name__ == "__main__":
    main()
