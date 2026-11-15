{{ config(
    materialized='incremental', incremental_strategy='merge', schema='fct', tags=['nacional', 'fct'],
    unique_key=['uf', 'n_aih', 'sequencia', 'ano_cmpt', 'mes_cmpt'],
    indexes=[{'columns': ['uf', 'n_aih', 'sequencia', 'ano_cmpt', 'mes_cmpt'], 'unique': True}],
    meta={'sistema_origem': 'DW', 'grupo': 'FCT', 'assunto': 'fct_internacao', 'uf': 'BR', 'tipo_carga': 'MERGE',
          'chave_negocio': 'uf,n_aih,sequencia,ano_cmpt,mes_cmpt',
          'descricao': 'Fato internação (grão: AIH), com chaves das dimensões (-1 = não informado) e os atos profissionais agregados do SIH-SP.'}
) }}
with i as (
    select * from {{ ref('int_mov_enr_internacao') }}
    {% if is_incremental() %}where dt_carga > (select coalesce(max(dt_carga), date '1900-01-01') from {{ this }}){% endif %}
),
atos as (
    select uf, sp_naih as n_aih, sequencia, sp_aa as ano_cmpt, sp_mm as mes_cmpt,
           count(*) as qtd_atos, sum({{ numero('sp_valato') }}) as val_atos, count(distinct sp_pf_doc) as qtd_profissionais
    from {{ ref('int_mov_nac_sih_sp_ato_profissional') }}
    group by 1, 2, 3, 4, 5
)
select
    i.uf, i.n_aih, i.sequencia, i.ano_cmpt, i.mes_cmpt,
    {{ sk_ou_nao_informado('t_int.sk_tempo') }} as sk_tempo_internacao, {{ sk_ou_nao_informado('t_sai.sk_tempo') }} as sk_tempo_saida,
    {{ sk_ou_nao_informado('m.sk_municipio') }} as sk_municipio_residencia, {{ sk_ou_nao_informado('est.sk_estabelecimento') }} as sk_estabelecimento,
    {{ sk_ou_nao_informado('c.sk_cid') }} as sk_cid_principal, {{ sk_ou_nao_informado('p.sk_procedimento') }} as sk_procedimento,
    i.dias_perm, i.morte, i.val_tot, i.val_sh, i.val_sp, i.val_uti,
    coalesce(a.qtd_atos, 0) as qtd_atos, a.val_atos, coalesce(a.qtd_profissionais, 0) as qtd_profissionais,
    i.dt_transacao, {{ dt_carga() }} as dt_carga
from i
left join atos a on a.uf = i.uf and a.n_aih = i.n_aih and a.sequencia = i.sequencia and a.ano_cmpt = i.ano_cmpt and a.mes_cmpt = i.mes_cmpt
left join {{ ref('dim_tempo') }} t_int on t_int.data = i.dt_internacao
left join {{ ref('dim_tempo') }} t_sai on t_sai.data = i.dt_saida
left join {{ ref('dim_municipio') }} m on m.cod_municipio = i.cod_municipio_residencia
left join {{ ref('dim_estabelecimento') }} est on est.cod_cnes = i.cnes
left join {{ ref('dim_cid') }} c on c.cod_cid = i.cid_principal
left join {{ ref('dim_procedimento') }} p on p.cod_procedimento = i.proc_rea
