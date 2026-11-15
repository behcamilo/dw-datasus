{{ config(
    materialized='table', schema='agg', tags=['nacional', 'agg'],
    meta={'sistema_origem': 'DW', 'grupo': 'AGG', 'assunto': 'agg_internacao_municipio_mes', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'sk_municipio_residencia,ano,mes',
          'descricao': 'Internações por município de residência e mês de internação: quantidade, dias de permanência, óbitos e valor total.'}
) }}
select f.sk_municipio_residencia, t.ano, t.mes, count(*) as internacoes, sum({{ numero('f.dias_perm') }}) as dias_permanencia,
       sum(case when f.morte = '1' then 1 else 0 end) as obitos_hospitalares, sum(f.val_tot) as valor_total, {{ dt_carga() }} as dt_carga
from {{ ref('fct_internacao') }} f
join {{ ref('dim_tempo') }} t on t.sk_tempo = f.sk_tempo_internacao
group by 1, 2, 3
