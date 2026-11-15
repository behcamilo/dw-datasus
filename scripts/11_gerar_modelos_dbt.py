"""Gera os modelos dbt que se repetem por tabela da origem: stages (sources), cadastros e movimentos por UF e nacionais.

Gera: dw_dbt/models/gerados/fontes.yml, int_cad/*.sql e int_mov/*.sql.
- Cada stage tem um modelo no DW, carregado por merge na chave de negócio (atos e diagnósticos do SIH: delete+insert pela AIH).
- Cadastros mensais do CNES com histórico (config.HISTORICOS): uma linha por versão (SCD tipo 2).
- O movimento confere os códigos nos cadastros consolidados (veja docs/desenho_dw.md).

Uso: python scripts/11_gerar_modelos_dbt.py
"""

import glob
import os
import shutil

import pandas as pd

import config
import dw

PASTA_DBT = "dw_dbt"
PASTA_MODELOS = f"{PASTA_DBT}/models/gerados"
UFS = [uf.lower() for uf in config.UFS]
CHAVE_DOMINIO = {}  # nome do domínio -> coluna do código (preenchido no main)


def ler_codigos_a_validar():
    """Colunas que cada tabela de movimento confere no cadastro (docs/validacao_codigos.csv)."""
    df = pd.read_csv("docs/validacao_codigos.csv")
    resultado = {}
    for r in df[df.validar].itertuples():
        resultado.setdefault((r.sistema, r.grupo, r.assunto), {})[r.coluna] = r.cadastro
    return resultado


CODIGOS_A_VALIDAR = ler_codigos_a_validar()


# Modelos
def modelo_por_stage(camada_dw, stage, tabela, uf):
    """Modelo de uma stage da UF: lê o delta do dia e carrega por merge (ou delete+insert)."""
    s, g, a = tabela["sistema"], tabela["grupo"], tabela["assunto"]
    chave = tabela["chave"].lower().split(",")
    estrategia, unico = "merge", True
    entidade = ENTIDADE_SCD2.get(f"{s}_{g}_{a}".lower())
    if entidade:
        chave = entidade + ["valido_de"]
    if (s, g, a) == ("SIH", "SP", "ato_profissional"):
        # o ato é reenviado com a AIH: apaga os atos da AIH e insere os novos
        estrategia, chave, unico = "delete+insert", ["sp_naih", "sequencia"], False
    elif (s, g, a) in {("SIH", "RD", "diagnostico"), ("SIH", "RJ", "diagnostico")}:
        estrategia, chave, unico = "delete+insert", ["n_aih", "sequencia", "ano_cmpt", "mes_cmpt"], False
    fonte = "stg_cad" if camada_dw == "int_cad" else "stg_mov"
    nome = dw.nome_tabela(camada_dw, s, g, a, uf)
    descricao = (f"{s}-{g} {a} ({uf.upper()}): histórico SCD tipo 2 (uma linha por versão), merge na entidade + valido_de." if entidade else
                 f"{s}-{g} {a} ({uf.upper()}): cópia tipada da stage com DT_CARGA, carga por {estrategia} na chave de negócio.")
    meta = dw.meta_de(s, g, a, uf.upper(), estrategia.upper().replace("+", "_"), chave, descricao)
    cab = dw.bloco_config(camada_dw, [uf, camada_dw], meta, "incremental", estrategia, chave, unico)
    if camada_dw == "int_mov":
        corpo = corpo_com_validacao_de_codigos(tabela, stage, uf)
    elif entidade:
        corpo = corpo_scd2(tabela, stage, entidade)
    elif s == "CNES":
        # confere o estabelecimento no cadastro geral nacional do CNES
        corpo = (f"select s.*, (g.cnes is not null) as no_cadastro_geral, {{{{ dt_carga() }}}} as dt_carga\n"
                 f"from {{{{ source('{fonte}', '{stage}') }}}} s\n"
                 f"left join (select distinct cnes from {{{{ source('stg_cad', 'stg_cad_dominio_cnes_cadgerbr') }}}}) g on g.cnes = s.cnes")
    else:
        corpo = f"select s.*, {{{{ dt_carga() }}}} as dt_carga\nfrom {{{{ source('{fonte}', '{stage}') }}}} s"
    dw.escrever_modelo(PASTA_MODELOS, camada_dw, nome, cab, corpo)
    return nome


def corpo_com_validacao_de_codigos(tabela, stage, uf):
    """Movimento com os códigos conferidos no cadastro: código que não existe vira -1 e a linha é mantida."""
    validadas = CODIGOS_A_VALIDAR.get((tabela["sistema"], tabela["grupo"], tabela["assunto"]), {})
    selecao, juncoes = [], []
    for coluna in dw.colunas_da_tabela(tabela):
        if coluna not in validadas:
            selecao.append(f"s.{coluna}")
            continue
        i = len(juncoes) + 1
        cadastro = validadas[coluna]
        if cadastro == "cnes_uf":
            ref, codigo = f"int_cad_estabelecimento_consolidado_{uf}", "cnes"
        elif cadastro.startswith("consolidado_"):
            ref, codigo = f"int_cad_{cadastro.replace('consolidado_', '', 1)}_consolidado", "codigo"
        else:
            dominio = cadastro.replace("dominio_", "", 1)
            ref, codigo = f"int_cad_dominio_{dominio}", CHAVE_DOMINIO[dominio]
        juncoes.append(f"left join (select distinct cast({codigo} as text) as cod from {{{{ ref('{ref}') }}}}) v{i} on v{i}.cod = s.{coluna}")
        selecao.append(f"case when v{i}.cod is null then '-1' else s.{coluna} end as {coluna}")
    return ("select\n    " + ",\n    ".join(selecao) + ",\n    {{ dt_carga() }} as dt_carga\n"
            f"from {{{{ source('stg_mov', '{stage}') }}}} s\n" + "\n".join(juncoes))


ENTIDADE_SCD2 = {tabela: entidade for tabela, entidade, _ in config.HISTORICOS}
CADASTRO_GERAL = "{{ source('stg_cad', 'stg_cad_dominio_cnes_cadgerbr') }}"


def corpo_scd2(tabela, stage, entidade):
    """Histórico no próprio cadastro: uma versão nova só quando algum campo muda.
    Na carga diária, a versão atual é comparada com a foto nova; se mudou, ela é fechada (valido_ate) e a nova entra."""
    ent = ", ".join(entidade)
    atributos = [c for c in dw.colunas_da_tabela(tabela) if c not in entidade + ["competen", "dt_transacao", "id_origem"]] + ["no_cadastro_geral"]
    att = ", ".join(atributos)
    janela = f"over (partition by {ent} order by competen)"
    return f"""with stage as (
    -- confere o estabelecimento no cadastro geral nacional do CNES
    select s.*, (g.cnes is not null) as no_cadastro_geral
    from {{{{ source('stg_cad', '{stage}') }}}} s
    left join (select distinct cnes from {CADASTRO_GERAL}) g on g.cnes = s.cnes
),
fotos_novas as (
    select distinct on ({ent}, competen) {ent}, competen, {att}, md5(row({att})::text) as versao, dt_transacao
    from stage order by {ent}, competen, dt_transacao desc
),
{{% if is_incremental() %}}
versao_atual as (select {ent}, valido_de as competen, {att}, versao, dt_transacao from {{{{ this }}}} where atual),
fotos as (
    select * from versao_atual
    union all
    select n.* from fotos_novas n left join versao_atual a using ({ent}) where a.competen is null or n.competen > a.competen
),
{{% else %}}
fotos as (select * from fotos_novas),
{{% endif %}}
mudancas as (select *, lag(versao) {janela} as versao_anterior from fotos),
versoes as (select * from mudancas where versao_anterior is distinct from versao)
select {ent}, {att}, versao, competen as valido_de,
       lead(competen) {janela} as valido_ate,
       lead(competen) {janela} is null as atual,
       dt_transacao, {{{{ dt_carga() }}}} as dt_carga
from versoes"""


def modelo_profissional(uf):
    """Profissional do SIH-SP: é cadastro, mas a origem o entrega como movimento (com a data do primeiro ato)."""
    nome = f"int_cad_sih_sp_profissional_{uf}"
    chave = ["sp_pf_doc", "sp_pf_cbo"]
    meta = dw.meta_de("SIH", "SP", "profissional", uf.upper(), "MERGE", chave,
                   f"Profissional do SIH-SP ({uf.upper()}): documento com hash + CBO.")
    cab = dw.bloco_config("int_cad", [uf, "int_cad"], meta, "incremental", "merge", chave)
    dw.escrever_modelo(PASTA_MODELOS, "int_cad", nome, cab,
                    f"select s.*, {{{{ dt_carga() }}}} as dt_carga\nfrom {{{{ source('stg_mov', 'stg_mov_sih_sp_profissional_{uf}') }}}} s")
    return nome


def modelo_dominio(dominio):
    """Domínio: a versão mais recente de cada chave, por merge (na SIGTAP a competência faz parte da chave)."""
    nome, chave = f"int_cad_dominio_{dominio['nome']}", dominio["chave"]
    meta = dw.meta_de("DOMINIO", dominio["nome"], "dominio", "", "MERGE", chave, f"Domínio {dominio['nome'].upper()}: estado atual (versão mais recente por chave).")
    cab = dw.bloco_config("int_cad", ["dominio", "int_cad"], meta, "incremental", "merge", chave)
    lista = ", ".join(chave)
    corpo = (f"select distinct on ({lista}) s.*, {{{{ dt_carga() }}}} as dt_carga\n"
             f"from {{{{ source('stg_cad', 'stg_cad_dominio_{dominio['nome']}') }}}} s\norder by {lista}, s.dt_transacao desc")
    dw.escrever_modelo(PASTA_MODELOS, "int_cad", nome, cab, corpo)


def modelo_nacional(camada, tabela, prefixo_uf, prefixo_nacional):
    """União das UFs (var('ufs')): cadastro por merge, com a uf na chave; movimento recriado a cada carga."""
    s, g, a = tabela["sistema"], tabela["grupo"], tabela["assunto"]
    nome = dw.nome_tabela(prefixo_nacional, s, g, a)
    entidade = ENTIDADE_SCD2.get(f"{s}_{g}_{a}".lower())
    chave = ["uf"] + (entidade + ["valido_de"] if entidade else tabela["chave"].lower().split(","))
    if camada == "int_cad":
        meta = dw.meta_de(s, g, a, "BR", "MERGE", chave, f"Consolidação nacional de {s}-{g} {a}: união das UFs, com a coluna uf; merge na chave.")
        cab = dw.bloco_config(camada, ["nacional", camada], meta, "incremental", "merge", chave)
    else:
        meta = dw.meta_de(s, g, a, "BR", "FULL", chave, f"Consolidação nacional de {s}-{g} {a}: união das UFs, com a coluna uf.")
        cab = dw.bloco_config(camada, ["nacional", camada], meta)
    dw.escrever_modelo(PASTA_MODELOS, camada, nome, cab, f"{{{{ uniao_ufs('{dw.nome_tabela(prefixo_uf, s, g, a)}') }}}}")


def montar_fontes(fontes_stg_cad, fontes_stg_mov):
    """fontes.yml: as stages, que são carregadas pelo script 15, e não pelo dbt."""
    def bloco(nome, schema, descricao, tabelas):
        linhas = [f"  - name: {nome}", f"    schema: {schema}", f"    description: \"{descricao}\"", "    tables:"]
        for t in tabelas:
            linhas += [f"      - name: {t['nome']}", "        meta: " + repr(t["meta"]).replace("'", '"')]
        return "\n".join(linhas)
    texto = "version: 2\nsources:\n"
    texto += bloco("stg_cad", "stg_cad", "Stage de cadastro: foto atual da origem (CNES e domínios), cópia fiel de 1 origem.", fontes_stg_cad) + "\n"
    texto += bloco("stg_mov", "stg_mov", "Stage de movimento: delta do dia por DT_TRANSACAO (SIH, SIM, SINASC).", fontes_stg_mov) + "\n"
    with open(f"{PASTA_MODELOS}/fontes.yml", "w", encoding="utf-8") as f:
        f.write(texto)


def main():
    shutil.rmtree(PASTA_MODELOS, ignore_errors=True)
    os.makedirs(PASTA_MODELOS)
    tabelas, dominios = dw.ler_tabelas_da_origem(), dw.ler_dominios()
    # coluna do código de cada domínio: 'codigo' no TabWin; senão a primeira da chave
    CHAVE_DOMINIO.update({d["nome"]: ("codigo" if "codigo" in d["chave"] else d["chave"][0]) for d in dominios})
    fontes_stg_cad, fontes_stg_mov, contagem = [], [], {}

    for tabela in tabelas:
        s, g, a = tabela["sistema"], tabela["grupo"], tabela["assunto"]
        cadastro = config.TIPO_DO_SISTEMA[s] == "cadastro"
        profissional = (s, g, a) == ("SIH", "SP", "profissional")
        for uf in UFS:
            camada_st = "stg_cad" if cadastro else "stg_mov"
            stage = dw.nome_tabela(camada_st, s, g, a, uf)
            meta = dw.meta_de(s, g, a, uf.upper(), "FOTO" if cadastro else "DELTA", tabela["chave"].lower().split(","),
                           f"Stage {s}-{g} {a} ({uf.upper()}): " + ("foto atual" if cadastro else "delta do dia por DT_TRANSACAO") + ".")
            (fontes_stg_cad if cadastro else fontes_stg_mov).append({"nome": stage, "meta": meta})
            if profissional:
                modelo_profissional(uf)
            else:
                modelo_por_stage("int_cad" if cadastro else "int_mov", stage, tabela, uf)

        if profissional:
            modelo_nacional("int_cad", tabela, "int_cad", "int_cad_nac")
        elif cadastro:
            modelo_nacional("int_cad", tabela, "int_cad", "int_cad_nac")
        else:
            modelo_nacional("int_mov", tabela, "int_mov", "int_mov_nac")

    for dominio in dominios:
        meta = dw.meta_de("DOMINIO", dominio["nome"], "dominio", "", "FOTO", dominio["chave"], f"Stage do domínio {dominio['nome'].upper()}.")
        fontes_stg_cad.append({"nome": f"stg_cad_dominio_{dominio['nome']}", "meta": meta})
        modelo_dominio(dominio)

    montar_fontes(fontes_stg_cad, fontes_stg_mov)
    for camada in ("int_cad", "int_mov"):
        contagem[camada] = len(glob.glob(f"{PASTA_MODELOS}/{camada}/*.sql"))
    print(f"stg_cad: {len(fontes_stg_cad)} | stg_mov: {len(fontes_stg_mov)} | modelos gerados: {contagem}")


if __name__ == "__main__":
    main()
