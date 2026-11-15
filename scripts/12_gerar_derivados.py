"""Gera os cadastros e movimentos derivados que se repetem por UF.

Gera: dw_dbt/models/gerados_derivados/int_cad/*.sql e int_mov/*.sql.
  cadastro (merge):  estabelecimento: território -> gestão -> leitos -> habilitações -> serviços e equipamentos -> consolidado
                     profissional:    ocupação -> vínculo -> consolidado
                     capacidade instalada por estabelecimento
  movimento:         classificados por UF (internação, AIH rejeitada, óbito, nascimento; recriados a cada carga)
                     nacionais dos classificados e resumos mensais por UF (foto)

Uso: python scripts/12_gerar_derivados.py
"""

import os
import shutil

import config
import dw

PASTA_MODELOS = "dw_dbt/models/gerados_derivados"
UFS = [uf.lower() for uf in config.UFS]



# Escrita

def escrever(camada, nome, uf, assunto, tipo_carga, chave, descricao, corpo):
    """Grava o modelo com o tipo de carga: MERGE, FULL (recriado) ou FOTO (um retrato por dia de carga)."""
    meta = dw.meta_de("DW", camada.upper(), assunto, uf.upper(), tipo_carga, chave, descricao)
    tags = [uf if uf != "br" else "nacional", camada]
    if tipo_carga == "MERGE":
        cab = dw.bloco_config(camada, tags, meta, "incremental", "merge", chave)
    elif tipo_carga == "FOTO":
        cab = dw.bloco_config(camada, tags, meta, "incremental", "delete+insert", ["dt_carga"], unico=False)
    else:
        cab = dw.bloco_config(camada, tags, meta)
    dw.escrever_modelo(PASTA_MODELOS, camada, nome, cab, corpo)
    return nome


VERSIONADOS = {tabela for tabela, _, _ in config.HISTORICOS}


def ultima_foto(tabela, uf, chave="cnes"):
    """Estado atual de um cadastro do CNES: a versão atual ou a competência mais recente."""
    if tabela in VERSIONADOS:
        return f"(select * from {{{{ ref('int_cad_{tabela}_{uf}') }}}} where atual)"
    return (f"(select * from {{{{ ref('int_cad_{tabela}_{uf}') }}}} t where t.competen = "
            f"(select max(competen) from {{{{ ref('int_cad_{tabela}_{uf}') }}}} x where x.{chave} = t.{chave}))")


# Cadastro: estabelecimento (6 etapas)

def cadeia_estabelecimento(uf):
    d = "Estabelecimento ({uf}), etapa {n}: {o}."
    escrever("int_cad", f"int_cad_estab_territorio_{uf}", uf, "estab_territorio", "MERGE", ["cnes"],
             d.format(uf=uf.upper(), n=1, o="versão atual do CNES-ST com o município consolidado"), f"""
select i.cnes, i.valido_de as versao_desde, i.codufmun, i.tp_unid, i.tp_prest, i.nat_jur, i.pf_pj, i.niv_dep, i.cnpj_man,
       m.nome as municipio, m.uf, m.regiao_saude, m.macrorregiao_saude, m.porte_populacional, m.amazonia_legal, {{{{ dt_carga() }}}} as dt_carga
from {ultima_foto('cnes_st_identificacao', uf)} i
left join {{{{ ref('int_cad_municipio_consolidado') }}}} m on m.codigo = i.codufmun""")
    escrever("int_cad", f"int_cad_estab_gestao_{uf}", uf, "estab_gestao", "MERGE", ["cnes"],
             d.format(uf=uf.upper(), n=2, o="+ gestão, vínculo com o SUS e regionalização"), f"""
select e.*, g.vinc_sus, g.tpgestao, g.atividad, g.clientel, g.turno_at, r.regsaude, r.micr_reg, r.distrsan, r.distradm
from {{{{ ref('int_cad_estab_territorio_{uf}') }}}} e
left join {ultima_foto('cnes_st_gestao_vinculo', uf)} g using (cnes)
left join {ultima_foto('cnes_st_regionalizacao', uf)} r using (cnes)""")
    escrever("int_cad", f"int_cad_estab_leitos_{uf}", uf, "estab_leitos", "MERGE", ["cnes"],
             d.format(uf=uf.upper(), n=3, o="+ leitos existentes e SUS (CNES-LT)"), f"""
with leitos as (
    select cnes, count(distinct codleito) as tipos_de_leito, sum({{{{ numero('qt_exist') }}}}) as leitos_existentes,
           sum({{{{ numero('qt_sus') }}}}) as leitos_sus
    from {ultima_foto('cnes_lt_leito', uf)} l group by cnes
)
select e.*, coalesce(l.tipos_de_leito, 0) as tipos_de_leito, coalesce(l.leitos_existentes, 0) as leitos_existentes,
       coalesce(l.leitos_sus, 0) as leitos_sus
from {{{{ ref('int_cad_estab_gestao_{uf}') }}}} e
left join leitos l using (cnes)""")
    escrever("int_cad", f"int_cad_estab_habilitacoes_{uf}", uf, "estab_habilitacoes", "MERGE", ["cnes"],
             d.format(uf=uf.upper(), n=4, o="+ habilitações (CNES-HB)"), f"""
with hab as (
    select cnes, count(*) as qtd_habilitacoes, sum({{{{ numero('nuleitos') }}}}) as leitos_habilitados
    from {ultima_foto('cnes_hb_habilitacao', uf)} h group by cnes
)
select e.*, coalesce(h.qtd_habilitacoes, 0) as qtd_habilitacoes, coalesce(h.leitos_habilitados, 0) as leitos_habilitados
from {{{{ ref('int_cad_estab_leitos_{uf}') }}}} e
left join hab h using (cnes)""")
    escrever("int_cad", f"int_cad_estab_servicos_equipamentos_{uf}", uf, "estab_servicos_equipamentos", "MERGE", ["cnes"],
             d.format(uf=uf.upper(), n=5, o="+ serviços especializados (CNES-SR) e equipamentos (CNES-EQ)"), f"""
with srv as (select cnes, count(*) as qtd_servicos from {ultima_foto('cnes_sr_servico_especializado', uf)} s group by cnes),
     eqp as (select cnes, count(*) as tipos_de_equipamento, sum({{{{ numero('qt_exist') }}}}) as equipamentos_existentes
             from {ultima_foto('cnes_eq_equipamento', uf)} q group by cnes)
select e.*, coalesce(s.qtd_servicos, 0) as qtd_servicos, coalesce(q.tipos_de_equipamento, 0) as tipos_de_equipamento,
       coalesce(q.equipamentos_existentes, 0) as equipamentos_existentes
from {{{{ ref('int_cad_estab_habilitacoes_{uf}') }}}} e
left join srv s using (cnes)
left join eqp q using (cnes)""")
    escrever("int_cad", f"int_cad_estabelecimento_consolidado_{uf}", uf, "estabelecimento_consolidado", "MERGE", ["cnes"],
             d.format(uf=uf.upper(), n=6, o="consolidado, com nome e porte; o movimento da UF confere o estabelecimento aqui"), f"""
select e.*, n.fantasia as nome_fantasia, n.raz_soci as razao_social,
       case when e.leitos_existentes > 0 then 'COM INTERNAÇÃO' else 'SEM INTERNAÇÃO' end as perfil
from {{{{ ref('int_cad_estab_servicos_equipamentos_{uf}') }}}} e
left join {{{{ ref('int_cad_dominio_cnes_cadgerbr') }}}} n using (cnes)""")


# Cadastro: profissional (3 etapas) e capacidade

def cadeia_profissional(uf):
    d = "Profissional do CNES ({uf}), etapa {n}: {o}. Só a competência mais recente."
    escrever("int_cad", f"int_cad_prof_ocupacao_{uf}", uf, "prof_ocupacao", "MERGE", ["id_origem"],
             d.format(uf=uf.upper(), n=1, o="profissional com a ocupação (CBO) consolidada"), f"""
select p.id_origem, p.cnes, p.competen, p.cns_prof, p.cbo, o.no_ocupacao as ocupacao, p.conselho, p.ufmunres, {{{{ dt_carga() }}}} as dt_carga
from {{{{ ref('int_cad_cnes_pf_profissional_{uf}') }}}} p
left join {{{{ ref('int_cad_ocupacao_consolidado') }}}} o on o.codigo = p.cbo
where p.competen = (select max(competen) from {{{{ ref('int_cad_cnes_pf_profissional_{uf}') }}}})""")
    escrever("int_cad", f"int_cad_prof_vinculo_{uf}", uf, "prof_vinculo", "MERGE", ["id_origem"],
             d.format(uf=uf.upper(), n=2, o="+ vínculo empregatício e atendimento SUS"), f"""
select p.*, v.vinculac, v.prof_sus, v.profnsus
from {{{{ ref('int_cad_prof_ocupacao_{uf}') }}}} p
left join {{{{ ref('int_cad_cnes_pf_vinculo_{uf}') }}}} v using (id_origem)""")
    escrever("int_cad", f"int_cad_profissional_consolidado_{uf}", uf, "profissional_consolidado", "MERGE", ["id_origem"],
             d.format(uf=uf.upper(), n=3, o="CONSOLIDADO: + carga horária e o município do estabelecimento"), f"""
select p.*, {{{{ numero('c.horaoutr') }}}} as horas_outras, {{{{ numero('c.horahosp') }}}} as horas_hospital,
       {{{{ numero('c.hora_amb') }}}} as horas_ambulatorio, e.codufmun as municipio_estabelecimento
from {{{{ ref('int_cad_prof_vinculo_{uf}') }}}} p
left join {{{{ ref('int_cad_cnes_pf_carga_horaria_{uf}') }}}} c using (id_origem)
left join {{{{ ref('int_cad_estab_territorio_{uf}') }}}} e on e.cnes = p.cnes""")


def capacidade(uf):
    escrever("int_cad", f"int_cad_estab_capacidade_{uf}", uf, "estab_capacidade", "MERGE", ["cnes"],
             f"Capacidade instalada por estabelecimento ({uf.upper()}): leitos, equipamentos, profissionais e horas.", f"""
with prof as (
    select cnes, count(*) as profissionais, sum(coalesce(horas_hospital, 0) + coalesce(horas_ambulatorio, 0) + coalesce(horas_outras, 0)) as horas_semanais
    from {{{{ ref('int_cad_profissional_consolidado_{uf}') }}}} group by cnes
)
select e.cnes, e.codufmun, e.perfil, e.leitos_existentes, e.leitos_sus, e.equipamentos_existentes, e.qtd_servicos,
       coalesce(p.profissionais, 0) as profissionais, coalesce(p.horas_semanais, 0) as horas_semanais, {{{{ dt_carga() }}}} as dt_carga
from {{{{ ref('int_cad_estabelecimento_consolidado_{uf}') }}}} e
left join prof p using (cnes)""")


# Movimento: classificados por UF e resumos

AIH = "n_aih, sequencia, ano_cmpt, mes_cmpt"


def internacao_classificada(uf, grupo):
    """AIH aprovada (RD) ou rejeitada (RJ) com procedimento, diagnóstico, município e estabelecimento classificados."""
    rj = grupo == "rj"
    nome = f"int_mov_aih_rejeitada_classificada_{uf}" if rj else f"int_mov_internacao_classificada_{uf}"
    extra_sel = ", i.st_situac, i.st_bloq, i.st_mot_blo, (aprov.n_aih is not null) as reapresentada_e_aprovada" if rj else ""
    extra_join = (f"\nleft join (select distinct n_aih from {{{{ ref('int_mov_sih_rd_internacao_{uf}') }}}}) aprov on aprov.n_aih = i.n_aih" if rj else "")
    o = "AIH rejeitada" if rj else "Internação"
    return escrever("int_mov", nome, uf, nome.replace(f"_{uf}", "").replace("int_mov_", ""), "FULL", AIH.split(", "),
                    f"{o} classificada ({uf.upper()}): procedimento, CID, município e estabelecimento pelos cadastros consolidados. "
                    "Recalculada a cada carga com o cadastro do dia.", f"""
select i.{AIH.replace(', ', ', i.')}, {{{{ data_sih('i.dt_inter') }}}} as dt_internacao, {{{{ data_sih('i.dt_saida') }}}} as dt_saida,
       i.dias_perm, i.morte, i.car_int, i.espec, pa.sexo, pa.idade, pa.munic_res,
       mr.regiao_saude as regiao_saude_residencia, mr.porte_populacional as porte_municipio_residencia,
       pr.proc_rea, pc.no_grupo as grupo_procedimento, pc.complexidade, pc.no_financiamento as financiamento,
       d.cid as cid_principal, c.capitulo as capitulo_cid, c.grupo as grupo_cid,
       es.cnes, ec.perfil as perfil_estabelecimento, ec.tp_unid as tipo_unidade,
       {{{{ numero('v.val_tot') }}}} as val_tot{extra_sel}, i.dt_transacao, {{{{ dt_carga() }}}} as dt_carga
from {{{{ ref('int_mov_sih_{grupo}_internacao_{uf}') }}}} i
left join {{{{ ref('int_mov_sih_{grupo}_paciente_{uf}') }}}} pa using ({AIH})
left join {{{{ ref('int_mov_sih_{grupo}_procedimento_financiamento_{uf}') }}}} pr using ({AIH})
left join {{{{ ref('int_mov_sih_{grupo}_estabelecimento_{uf}') }}}} es using ({AIH})
left join {{{{ ref('int_mov_sih_{grupo}_valores_{uf}') }}}} v using ({AIH})
left join (select * from {{{{ ref('int_mov_sih_{grupo}_diagnostico_{uf}') }}}} where ordem = 0) d using ({AIH})
left join {{{{ ref('int_cad_procedimento_consolidado') }}}} pc on pc.codigo = pr.proc_rea
left join {{{{ ref('int_cad_cid_consolidado') }}}} c on c.codigo = d.cid
left join {{{{ ref('int_cad_municipio_consolidado') }}}} mr on mr.codigo = pa.munic_res
left join {{{{ ref('int_cad_estabelecimento_consolidado_{uf}') }}}} ec on ec.cnes = es.cnes{extra_join}""")


def obito_classificado(uf):
    return escrever("int_mov", f"int_mov_obito_classificado_{uf}", uf, "obito_classificado", "FULL", ["ano", "contador"],
                    f"Óbito classificado ({uf.upper()}): causa básica pela CID consolidada, município e estabelecimento de ocorrência.", f"""
select o.ano, o.contador, {{{{ data_sim('o.dtobito') }}}} as dt_obito, o.tipobito, o.lococor, o.codestab, o.codmunocor, o.circobito,
       f.sexo, f.idade, f.racacor, f.codmunres, m.regiao_saude as regiao_saude_residencia, m.uf as uf_residencia,
       c.causabas, cid.capitulo as capitulo_causa, cid.grupo as grupo_causa, ec.perfil as perfil_estabelecimento,
       (left(f.idade, 1) in ('0', '1', '2', '3')) as obito_infantil, o.dt_transacao, {{{{ dt_carga() }}}} as dt_carga
from {{{{ ref('int_mov_sim_do_obito_{uf}') }}}} o
left join {{{{ ref('int_mov_sim_do_falecido_{uf}') }}}} f using (ano, contador)
left join {{{{ ref('int_mov_sim_do_causa_morte_{uf}') }}}} c using (ano, contador)
left join {{{{ ref('int_cad_cid_consolidado') }}}} cid on cid.codigo = c.causabas
left join {{{{ ref('int_cad_municipio_consolidado') }}}} m on m.codigo = f.codmunres
left join {{{{ ref('int_cad_estabelecimento_consolidado_{uf}') }}}} ec on ec.cnes = o.codestab""")


def nascimento_classificado(uf):
    return escrever("int_mov", f"int_mov_nascimento_classificado_{uf}", uf, "nascimento_classificado", "FULL", ["ano", "contador"],
                    f"Nascimento classificado ({uf.upper()}): gestação e parto, anomalia pela CID consolidada, município e estabelecimento.", f"""
select n.ano, n.contador, {{{{ data_sim('n.dtnasc') }}}} as dt_nascimento, n.sexo, n.peso, n.racacor, n.locnasc, n.codestab, n.codmunnasc,
       g.gestacao, g.gravidez, g.parto, g.consultas, g.tprobson, (n.idanomal = '1') as com_anomalia, cid.capitulo as capitulo_anomalia,
       m.regiao_saude, m.porte_populacional, ec.perfil as perfil_estabelecimento,
       ({{{{ numero('n.peso') }}}} < 2500) as baixo_peso, n.dt_transacao, {{{{ dt_carga() }}}} as dt_carga
from {{{{ ref('int_mov_sinasc_dn_nascimento_{uf}') }}}} n
left join {{{{ ref('int_mov_sinasc_dn_gestacao_parto_{uf}') }}}} g using (ano, contador)
left join {{{{ ref('int_cad_cid_consolidado') }}}} cid on cid.codigo = n.codanomal
left join {{{{ ref('int_cad_municipio_consolidado') }}}} m on m.codigo = n.codmunnasc
left join {{{{ ref('int_cad_estabelecimento_consolidado_{uf}') }}}} ec on ec.cnes = n.codestab""")


def resumos(uf):
    """Resumos mensais por UF, gravados como foto (um retrato por dia de carga)."""
    escrever("int_mov", f"int_mov_internacao_estab_mes_{uf}", uf, "internacao_estab_mes", "FOTO", ["dt_carga", "cnes", "ano_cmpt", "mes_cmpt"],
             f"Retrato diário das internações por estabelecimento e competência ({uf.upper()}).", f"""
select {{{{ dt_carga() }}}} as dt_carga, cnes, ano_cmpt, mes_cmpt, count(*) as internacoes, count(*) filter (where morte = '1') as obitos,
       sum(val_tot) as valor_total, avg({{{{ numero('dias_perm') }}}}) as media_permanencia
from {{{{ ref('int_mov_internacao_classificada_{uf}') }}}}
group by cnes, ano_cmpt, mes_cmpt""")
    escrever("int_mov", f"int_mov_obito_municipio_mes_{uf}", uf, "obito_municipio_mes", "FOTO", ["dt_carga", "codmunres", "mes"],
             f"Retrato diário dos óbitos por município de residência e mês ({uf.upper()}).", f"""
select {{{{ dt_carga() }}}} as dt_carga, codmunres, to_char(dt_obito, 'YYYY-MM') as mes, count(*) as obitos,
       count(*) filter (where obito_infantil) as obitos_infantis
from {{{{ ref('int_mov_obito_classificado_{uf}') }}}}
group by codmunres, to_char(dt_obito, 'YYYY-MM')""")


def nacional_classificado(prefixo, chave, descricao):
    escrever("int_mov", f"int_mov_nac_{prefixo}", "br", f"nac_{prefixo}", "FULL", ["uf"] + chave, descricao, f"{{{{ uniao_ufs('int_mov_{prefixo}') }}}}")


# Main

def main():
    shutil.rmtree(PASTA_MODELOS, ignore_errors=True)
    os.makedirs(PASTA_MODELOS)
    for uf in UFS:
        cadeia_estabelecimento(uf)
        cadeia_profissional(uf)
        capacidade(uf)
        internacao_classificada(uf, "rd")
        internacao_classificada(uf, "rj")
        obito_classificado(uf)
        nascimento_classificado(uf)
        resumos(uf)
    for prefixo, chave, o in [("internacao_classificada", AIH.split(", "), "internações"), ("aih_rejeitada_classificada", AIH.split(", "), "AIH rejeitadas"),
                              ("obito_classificado", ["ano", "contador"], "óbitos"), ("nascimento_classificado", ["ano", "contador"], "nascimentos")]:
        nacional_classificado(prefixo, chave, f"Consolidação nacional dos {o} classificados (união das UFs).")
    for camada in ("int_cad", "int_mov"):
        print(camada, len(os.listdir(f"{PASTA_MODELOS}/{camada}")), "modelos")


if __name__ == "__main__":
    main()
