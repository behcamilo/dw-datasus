"""Gera as dimensões, os fatos e os agregados (além dos escritos à mão em dw_dbt/models/manual/).

São consultas simples sobre tabelas do DW: dão ao DW uma quantidade realista de tabelas e de dependências, sem criar dados.
  Dimensões: uma por domínio e uma por cadastro do CNES (por UF e nacional; as do CNES têm uma linha por versão).
  Fatos: um por grupo e UF, um nacional por grupo e alguns cruzados; alguns nacionais leem outros fatos (cadeias de até 4).
  Agregados: sobre fatos e dimensões nacionais.
As fontes de cada tabela são sorteadas com semente fixa; quantidades e distribuições vêm do config.py.
Gera: dw_dbt/models/gerados_negocio/dim, fct e agg.

Uso: python scripts/13_gerar_dim_fct_agg.py
"""

import math
import os
import random
import shutil

import pandas as pd

import config
import dw

PASTA_MODELOS = "dw_dbt/models/gerados_negocio"
GRUPOS_MOVIMENTO = [("SIH", "RD"), ("SIH", "SP"), ("SIH", "RJ"), ("SIM", "DO"), ("SINASC", "DN")]
# só os grupos que têm tabelas na origem
_EXISTEM = {(t["sistema"], t["grupo"]) for t in dw.ler_tabelas_da_origem()}
GRUPOS = GRUPOS_MOVIMENTO + [("CNES", g) for g in config.SISTEMAS_E_GRUPOS["CNES"] if ("CNES", g) in _EXISTEM]
TECNICAS = {"competen", "id_origem", "dt_transacao", "dt_carga", "mes", "uf"}


# Sorteio determinístico

def gerador(nome):
    """Sorteador próprio de cada tabela: a mesma tabela sempre recebe as mesmas fontes."""
    return random.Random(f"{config.SEMENTE_DW}|{nome}")


def quantidade(rng, media):
    """Inteiro com a média pedida (ex.: 3,4 vira 3 ou 4, com média 3,4)."""
    base = int(media)
    return base + (1 if rng.random() < media - base else 0)


def centrais_sorteadas(rng, vagas, usados=()):
    """Cadastros centrais que entram como fonte, cada um com a sua probabilidade, até `vagas`."""
    escolhidas = []
    for central, p in zip(config.INT_CAD_CENTRAIS, config.PROBABILIDADE_CENTRAIS):
        if len(escolhidas) < vagas and central not in usados and rng.random() < p:
            escolhidas.append(central)
    return escolhidas


def sortear(rng, pool, usados):
    candidatos = [p for p in pool if p not in usados]
    return rng.choices(candidatos, [1 / (i + 1) for i in range(len(candidatos))])[0] if candidatos else None


def compor(rng, n, categorias, usados=()):
    """Escolhe n tabelas diferentes: primeiro a categoria (pelo peso), depois a tabela (peso maior para as primeiras da lista)."""
    escolhidos = []
    for _ in range(50):
        if len(escolhidos) >= n:
            break
        pool = rng.choices([c[1] for c in categorias], [c[0] for c in categorias])[0]
        escolhida = sortear(rng, pool, set(usados) | set(escolhidos))
        if escolhida:
            escolhidos.append(escolhida)
    return escolhidos


# Inventário de tabelas já existentes

def inventario():
    tabelas = dw.ler_tabelas_da_origem()
    inv = {"int_cad_uf": {}, "int_mov_uf": {}, "int_cad_nac": [], "int_mov_nac": [], "principal": {}, "tabelas": tabelas,
           "dominios": dw.ler_dominios(), "colunas": {}}
    for t in tabelas:
        s, g, a = t["sistema"], t["grupo"], t["assunto"]
        cadastro = config.TIPO_DO_SISTEMA[s] == "cadastro" or (s, g, a) == ("SIH", "SP", "profissional")
        camada = "int_cad" if cadastro else "int_mov"
        inv["colunas"][(s, g, a)] = dw.colunas_da_tabela(t)
        for uf in dw.UFS:
            nome = f"int_cad_sih_sp_profissional_{uf}" if (s, g, a) == ("SIH", "SP", "profissional") else dw.nome_tabela(camada, s, g, a, uf)
            inv[camada + "_uf"].setdefault(uf, []).append(nome)
        inv[camada + "_nac"].append(dw.nome_tabela(camada + "_nac", s, g, a))
        if not t["pai"]:  # a tabela sem pai é a principal do grupo
            inv["principal"][(s, g)] = (camada, a)
    inv["int_cad_dom"] = {d["nome"]: f"int_cad_dominio_{d['nome']}" for d in inv["dominios"]}
    inv["manuais"] = {c: sorted(f[:-4] for f in os.listdir(f"dw_dbt/models/manual/{c}")) for c in ("dim", "fct", "agg", "int_cad", "int_mov")}
    for camada in ("int_cad", "int_mov"):
        for nome in sorted(f[:-4] for f in os.listdir(f"dw_dbt/models/gerados_derivados/{camada}")):
            if nome.startswith(f"{camada}_nac_"):
                inv[camada + "_nac"].append(nome)
            elif nome.rsplit("_", 1)[1] in dw.UFS:
                inv[camada + "_uf"][nome.rsplit("_", 1)[1]].append(nome)
        inv[camada + "_nac"] += inv["manuais"][camada]
    # colunas que usam cada domínio: a dimensão do domínio lê o cadastro que o usa
    usos = pd.read_csv("docs/dominios_origem.csv", encoding="utf-8-sig", keep_default_na=False)
    inv["colunas_do_dominio"] = usos[usos.fora == ""].groupby("dominio").coluna.apply(set).to_dict()
    return inv


# Escrita

def consulta_simples(principal, outras, agrupar):
    """Contagem sobre a fonte principal; as outras fontes entram numa condição sempre verdadeira (dependência real)."""
    condicoes = "\n  and ".join(f"(select count(*) from {{{{ ref('{o}') }}}}) >= 0" for o in outras)
    onde = f"where {condicoes}\n" if outras else ""
    colunas = ", ".join(f"m.{c}" for c in agrupar)
    return (f"select {colunas}, count(*) as qtd_registros\nfrom {{{{ ref('{principal}') }}}} m\n{onde}group by {colunas}")


def escrever(camada, nome, tags, meta, corpo, foto=False):
    """Grava o modelo: FULL (recriado) ou FOTO (um retrato por dia de carga)."""
    if foto:
        cab = dw.bloco_config(camada, tags, meta, "incremental", "delete+insert", ["dt_foto"], unico=False)
    else:
        cab = dw.bloco_config(camada, tags, meta)
    dw.escrever_modelo(PASTA_MODELOS, camada, nome, cab, corpo)


def versionado(s, g, inv):
    """A tabela principal do grupo tem histórico (config.HISTORICOS)?"""
    camada, assunto = inv["principal"][(s, g)]
    return f"{s}_{g}_{assunto}".lower() in {t for t, _, _ in config.HISTORICOS}


def consulta_foto(principal, outras, periodo="competen"):
    """Retrato do dia: contagem por período, com a data da carga."""
    condicoes = "\n  and ".join(f"(select count(*) from {{{{ ref('{o}') }}}}) >= 0" for o in outras)
    onde = f"where {condicoes}\n" if outras else ""
    return (f"select {{{{ dt_carga() }}}} as dt_foto, m.{periodo}, count(*) as qtd_registros\nfrom {{{{ ref('{principal}') }}}} m\n{onde}group by m.{periodo}")


def meta(sistema, grupo, assunto, uf, tipo, chave, descricao):
    return dw.meta_de(sistema, grupo, assunto, uf, tipo, chave, descricao)


def corpo_dimensao(nome, origem_ref, colunas, chave, extras):
    """Dimensão: uma linha por código distinto, mais o membro -1 'NÃO INFORMADO'."""
    condicoes = "".join(f"\n      and (select count(*) from {{{{ ref('{e}') }}}}) >= 0" for e in extras)
    cast = ",\n        ".join(f'cast(d."{c}" as text) as "{c}"' for c in colunas)
    lista = ", ".join(f'"{c}"' for c in colunas)
    ordem = ", ".join(f'"{c}"' for c in chave)
    membro = ", ".join(["'-1'" if i == 0 else "'NÃO INFORMADO'" if i == 1 else "null" for i in range(len(colunas))])
    return (f"select row_number() over (order by {ordem})::int as sk_{nome}, {lista}, {{{{ dt_carga() }}}} as dt_carga\n"
            f"from (\n    select distinct\n        {cast}\n    from {{{{ ref('{origem_ref}') }}}} d\n    where true{condicoes}\n) x\n"
            f"union all\nselect -1, {membro}, {{{{ dt_carga() }}}}")


# DIM

def gerar_dim(inv):
    compartilhados = [inv["int_cad_dom"][d] for d in config.DOMINIOS_COMPARTILHADOS if d in inv["int_cad_dom"]]
    comuns_nac = ["int_cad_nac_cnes_st_identificacao", "int_cad_nac_sih_sp_profissional"] + [n for n in inv["int_cad_nac"] if n not in ("int_cad_nac_cnes_st_identificacao",)]
    lista, dims = {"uf": {}, "dom": [], "nac": []}, []

    # (a) uma por domínio
    colunas_nac = {n: inv["colunas"][(s, g, a)] for (s, g, a) in inv["colunas"] if (n := dw.nome_tabela("int_cad_nac", s, g, a)) in inv["int_cad_nac"]}
    for d in inv["dominios"]:
        nome = f"dim_dom_{d['nome']}"
        rng = gerador(nome)
        n_int_cad = rng.choices([q for q, _ in config.INT_CAD_POR_DIM], [p for _, p in config.INT_CAD_POR_DIM])[0]
        que_usam = [n for n, cols in colunas_nac.items() if inv["colunas_do_dominio"].get(d["nome"], set()) & set(cols)]
        extras = compor(rng, n_int_cad - 1, [(1.0, que_usam + comuns_nac)], usados={inv["int_cad_dom"][d["nome"]]})
        if rng.random() < config.PROBABILIDADE_INT_MOV_EM_DIM:
            extras.append(rng.choice(inv["int_mov_nac"]))
        colunas = [c for c in d["colunas"] if c != "dt_transacao"]
        escrever("dim", nome, ["dominio", "dim"], meta("DOMINIO", d["nome"], nome, "", "FULL", d["chave"], f"Dimensão do domínio {d['nome'].upper()}, com o membro -1."),
                 corpo_dimensao(nome, inv["int_cad_dom"][d["nome"]], colunas, d["chave"], extras))
        lista["dom"].append(nome)

    # (b) cadastros do CNES, por UF e nacionais
    historicos = {t: (ent, att) for t, ent, att in config.HISTORICOS}
    for grupo, assunto in config.DIMENSOES_CNES:
        colunas = [c for c in inv["colunas"][("CNES", grupo, assunto)] if c not in TECNICAS][:2]
        tabela = f"cnes_{grupo}_{assunto}".lower()
        nome_nac = f"dim_nac_cnes_{grupo}_{assunto}".lower()
        for uf in dw.UFS + [None]:
            nome = f"dim_cnes_{grupo}_{assunto}_{uf}".lower() if uf else nome_nac
            rng = gerador(nome)
            principal = dw.nome_tabela("int_cad", "CNES", grupo, assunto, uf) if uf else dw.nome_tabela("int_cad_nac", "CNES", grupo, assunto)
            colunas_dim = colunas
            if tabela in historicos:
                # o cadastro tem histórico: uma linha por versão
                ent, att = historicos[tabela]
                colunas_dim = ent + att[:1] + ["valido_de"]
            n_int_cad = rng.choices([q for q, _ in config.INT_CAD_POR_DIM], [p for _, p in config.INT_CAD_POR_DIM])[0]
            cadastro_uf = [x for x in inv["int_cad_uf"][uf] if x != principal] if uf else comuns_nac
            ordem_uf = ([f"int_cad_cnes_st_identificacao_{uf}"] if uf else []) + cadastro_uf
            extras = compor(rng, n_int_cad - 1, [(0.6, ordem_uf), (0.4, compartilhados)], usados={principal})
            if rng.random() < config.PROBABILIDADE_INT_MOV_EM_DIM:
                extras.append(rng.choice(inv["int_mov_uf"][uf] if uf else inv["int_mov_nac"]))
            escrever("dim", nome, [uf or "nacional", "dim"],
                     meta("CNES", grupo, nome, (uf or "BR").upper(), "FULL", colunas_dim, f"Dimensão de cadastro CNES-{grupo} {assunto} ({(uf or 'BR').upper()}), com o membro -1."),
                     corpo_dimensao(nome, principal, colunas_dim, colunas_dim, extras))
            if uf:
                lista["uf"].setdefault(uf, []).append(nome)
            else:
                lista["nac"].append(nome)
    return lista


# FCT

def fonte_principal(inv, s, g, uf):
    camada, assunto = inv["principal"][(s, g)]
    return dw.nome_tabela(camada if uf else camada + "_nac", s, g, assunto, uf)


def quantas_fontes(rng):
    """Quantas tabelas o fato lê: lognormal com a mediana e o p90 configurados."""
    sigma = math.log(config.FONTES_FCT_P90 / config.FONTES_FCT_MEDIANA) / 1.2816  # 1,2816 = quantil 90% da normal padrão
    return min(config.FONTES_FCT_MAX, max(1, round(rng.lognormvariate(math.log(config.FONTES_FCT_MEDIANA), sigma))))


def planejar_pais_de_fato(ordem):
    """Escolhe os fatos nacionais que leem outros fatos, em níveis 2 a 4 (config.FATOS_DERIVADOS_POR_NIVEL).
    Cada um lê um fato do nível logo abaixo e alguns de níveis menores, sempre criados antes dele (sem ciclo)."""
    rng = random.Random(f"{config.SEMENTE_DW}|plano_fato")
    nacionais = [o[0] for o in ordem if o[3] is None]
    nivel = {n: 1 for n in nacionais}
    derivados = nacionais[-sum(config.FATOS_DERIVADOS_POR_NIVEL.values()):]
    i = 0
    for n_nivel, qtd in sorted(config.FATOS_DERIVADOS_POR_NIVEL.items()):
        for nome in derivados[i:i + qtd]:
            nivel[nome] = n_nivel
        i += qtd
    pais = {}
    for nome in derivados:
        anteriores = nacionais[:nacionais.index(nome)]
        lidos = [rng.choice([a for a in anteriores if nivel[a] == nivel[nome] - 1])]
        outros = [a for a in anteriores if nivel[a] < nivel[nome] and a not in lidos]
        lidos += rng.sample(outros, min(len(outros), max(0, quantidade(rng, config.FATOS_LIDOS_POR_DERIVADO) - 1)))
        pais[nome] = lidos
    return pais, nivel


def sortear_por_tipo(rng, n):
    """Reparte n fontes entre cadastro, movimento e dimensão pelos pesos configurados."""
    tipos = rng.choices(list(config.PESO_FONTE_FCT), list(config.PESO_FONTE_FCT.values()), k=n)
    return {t: tipos.count(t) for t in config.PESO_FONTE_FCT}


def gerar_fato(inv, dims):
    compartilhados = [inv["int_cad_dom"][d] for d in config.DOMINIOS_COMPARTILHADOS if d in inv["int_cad_dom"]]
    dim_comum = inv["manuais"]["dim"] + [f"dim_dom_{d}" for d in config.DOMINIOS_COMPARTILHADOS if f"dim_dom_{d}" in dims["dom"]] + dims["nac"]
    fatos = {"uf": {}, "nac": [], "nivel": {}}
    # ordem de criação: por UF, depois nacionais por grupo, depois os cruzados
    ordem = [(f"fct_{s}_{g}_{uf}".lower(), s, g, uf) for uf in dw.UFS for s, g in GRUPOS]
    ordem += [(f"fct_nac_{s}_{g}".lower(), s, g, None) for s, g in GRUPOS]
    ordem += [(f"fct_nac_cruzado_{i:02d}", *GRUPOS_MOVIMENTO[(i - 1) % len(GRUPOS_MOVIMENTO)], None) for i in range(1, config.FATOS_NACIONAIS_CRUZADOS + 1)]
    pais_de_fato, fatos["nivel"] = planejar_pais_de_fato(ordem)

    for nome, s, g, uf in ordem:
        rng = gerador(nome)
        movimento = (s, g) in GRUPOS_MOVIMENTO
        principal = fonte_principal(inv, s, g, uf)
        if uf:
            cat_int_cad = [(0.8, [f"int_cad_estabelecimento_consolidado_{uf}"] + inv["int_cad_uf"][uf]), (0.1, compartilhados), (0.1, inv["int_cad_nac"])]
            cat_int_mov = [(0.6, inv["int_mov_uf"][uf]), (0.4, inv["int_mov_nac"])]
            cat_dim = [(0.5, dims["uf"][uf]), (0.5, dim_comum)]
        else:
            cat_int_cad = [(0.6, inv["int_cad_nac"]), (0.4, compartilhados)]
            cat_int_mov = [(1.0, inv["int_mov_nac"])]
            cat_dim = [(1.0, dim_comum)]
        fatos_lidos = pais_de_fato.get(nome, [])
        n = sortear_por_tipo(rng, max(1, quantas_fontes(rng) - len(fatos_lidos)))
        usados = {principal}
        vagas_int_cad = n["int_cad"] - (0 if movimento else 1)  # a fonte principal ocupa uma vaga do seu tipo
        int_cad = centrais_sorteadas(rng, vagas_int_cad, usados)
        int_cad += compor(rng, vagas_int_cad - len(int_cad), cat_int_cad, usados | set(int_cad))
        int_mov = compor(rng, n["int_mov"] - (1 if movimento else 0), cat_int_mov, usados)
        dim = compor(rng, n["dim"], cat_dim)
        foto = s == "CNES" and uf is None and g in config.FATOS_FOTO_CNES
        periodo = "valido_de" if versionado(s, g, inv) else "competen"
        if foto:
            descricao = f"Fato de {s}-{g} (BR): retrato diário (FOTO) da contagem de registros por competência."
            corpo, chave = consulta_foto(principal, int_cad + int_mov + dim + fatos_lidos, periodo), ["dt_foto", periodo]
        else:
            agrupar = ["dt_carga"] if movimento else [periodo, "dt_carga"]
            descricao = f"Fato de {s}-{g} ({(uf or 'BR').upper()}): contagem de registros por " + ("carga." if movimento else "competência.")
            corpo, chave = consulta_simples(principal, int_cad + int_mov + dim + fatos_lidos, agrupar), agrupar
        escrever("fct", nome, [uf or "nacional", "fct"], meta(s, g, nome, (uf or "BR").upper(), "FOTO" if foto else "FULL", chave, descricao),
                 corpo, foto=foto)
        (fatos["uf"].setdefault(uf, []) if uf else fatos["nac"]).append(nome)
    return fatos


# AGG

def gerar_agg(inv, dims, fatos):
    compartilhados = [inv["int_cad_dom"][d] for d in config.DOMINIOS_COMPARTILHADOS if d in inv["int_cad_dom"]]
    dim_comum = inv["manuais"]["dim"] + [f"dim_dom_{d}" for d in config.DOMINIOS_COMPARTILHADOS if f"dim_dom_{d}" in dims["dom"]] + dims["nac"]
    # o agregado lê só fatos de nível 1
    fatos_nac = inv["manuais"]["fct"] + [f for f in fatos["nac"] if fatos["nivel"].get(f, 1) == 1]
    fatos_foto = {f"fct_nac_cnes_{g.lower()}" for g in config.FATOS_FOTO_CNES}
    anteriores = list(inv["manuais"]["agg"])
    for i in range(1, config.AGG_NOVOS + 1):
        nome = f"agg_nac_{i:02d}"
        rng = gerador(nome)
        fatos_lidos = compor(rng, max(quantidade(rng, config.MEDIAS_AGG["fct"]), 1), [(1.0, fatos_nac)])
        # o agregado agrupa por dt_carga, que o fato FOTO não tem
        fatos_lidos.sort(key=lambda f: f in fatos_foto)
        if fatos_lidos[0] in fatos_foto:
            raise SystemExit(f"{nome}: todos os fatos lidos são FOTO; não há dt_carga para agrupar.")
        dim = compor(rng, quantidade(rng, config.MEDIAS_AGG["dim"]), [(1.0, dim_comum)])
        int_cad = compor(rng, quantidade(rng, config.MEDIAS_AGG["int_cad"]), [(0.5, inv["int_cad_nac"]), (0.5, compartilhados)])
        int_mov = compor(rng, quantidade(rng, config.MEDIAS_AGG["int_mov"]), [(1.0, inv["int_mov_nac"])])
        agg = compor(rng, quantidade(rng, config.MEDIAS_AGG["agg"]), [(1.0, anteriores)])
        escrever("agg", nome, ["nacional", "agg"], meta("DW", "AGG", nome, "BR", "FULL", ["dt_carga"], "Agregado nacional: contagem de registros do fato por carga."),
                 consulta_simples(fatos_lidos[0], fatos_lidos[1:] + dim + int_cad + int_mov + agg, ["dt_carga"]))
        anteriores.append(nome)


def main():
    shutil.rmtree(PASTA_MODELOS, ignore_errors=True)
    inv = inventario()
    dims = gerar_dim(inv)
    fatos = gerar_fato(inv, dims)
    gerar_agg(inv, dims, fatos)
    for camada in ("dim", "fct", "agg"):
        print(camada, len(os.listdir(f"{PASTA_MODELOS}/{camada}")), "gerados +", len(inv["manuais"][camada]), "manuais")


if __name__ == "__main__":
    main()
