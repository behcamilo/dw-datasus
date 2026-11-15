{{ config(
    materialized='incremental', incremental_strategy='merge', schema='int_mov', tags=['nacional', 'int_mov'],
    unique_key=['uf', 'n_aih', 'sequencia', 'ano_cmpt', 'mes_cmpt'],
    indexes=[{'columns': ['uf', 'n_aih', 'sequencia', 'ano_cmpt', 'mes_cmpt'], 'unique': True}],
    meta={'sistema_origem': 'SIH', 'grupo': 'RD', 'assunto': 'internacao_enriquecida', 'uf': 'BR', 'tipo_carga': 'MERGE',
          'chave_negocio': 'uf,n_aih,sequencia,ano_cmpt,mes_cmpt',
          'descricao': 'Internação enriquecida: junta as 6 tabelas do SIH-RD (movimento tratado) e consulta o cadastro (estabelecimento do CNES, município).'}
) }}
-- Uma linha por AIH. Lê só o que chegou desde a última carga (dt_carga maior que o já carregado).
with i as (
    select * from {{ ref('int_mov_nac_sih_rd_internacao') }}
    {% if is_incremental() %}where dt_carga > (select coalesce(max(dt_carga), date '1900-01-01') from {{ this }}){% endif %}
),
est as ({{ estabelecimento_atual() }}),
diag as (select * from {{ ref('int_mov_nac_sih_rd_diagnostico') }} where ordem = 0 and tipo = 'principal')
select
    i.uf, i.n_aih, i.sequencia, i.ano_cmpt, i.mes_cmpt,
    {{ data_sih('i.dt_inter') }} as dt_internacao, {{ data_sih('i.dt_saida') }} as dt_saida,
    i.dias_perm, i.morte, i.car_int, i.espec,
    p.munic_res as cod_municipio_residencia, mun.nome as municipio_residencia, p.sexo, p.idade, p.cod_idade, p.raca_cor,
    e.cnes, e.munic_mov as cod_municipio_movimento, c.tp_unid as tipo_unidade_cnes, c.nat_jur as natureza_juridica_cnes,
    pr.proc_rea, pr.complex, pr.financ,
    d.cid as cid_principal,
    {{ numero('v.val_tot') }} as val_tot, {{ numero('v.val_sh') }} as val_sh, {{ numero('v.val_sp') }} as val_sp, {{ numero('v.val_uti') }} as val_uti,
    i.dt_transacao, {{ dt_carga() }} as dt_carga
from i
left join {{ ref('int_mov_nac_sih_rd_paciente') }} p using (uf, n_aih, sequencia, ano_cmpt, mes_cmpt)
left join {{ ref('int_mov_nac_sih_rd_estabelecimento') }} e using (uf, n_aih, sequencia, ano_cmpt, mes_cmpt)
left join {{ ref('int_mov_nac_sih_rd_procedimento_financiamento') }} pr using (uf, n_aih, sequencia, ano_cmpt, mes_cmpt)
left join {{ ref('int_mov_nac_sih_rd_valores') }} v using (uf, n_aih, sequencia, ano_cmpt, mes_cmpt)
left join diag d using (uf, n_aih, sequencia, ano_cmpt, mes_cmpt)
left join est c on c.uf = i.uf and c.cnes = e.cnes
left join {{ ref('int_cad_municipio_consolidado') }} mun on mun.codigo = p.munic_res
