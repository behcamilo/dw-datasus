{{ config(
    materialized='table', schema='agg', tags=['nacional', 'agg'],
    meta={'sistema_origem': 'DW', 'grupo': 'AGG', 'assunto': 'agg_obito_municipio_mes', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'sk_municipio_residencia,ano,mes',
          'descricao': 'Óbitos por município de residência e mês do óbito.'}
) }}
select f.sk_municipio_residencia, t.ano, t.mes, count(*) as obitos, {{ dt_carga() }} as dt_carga
from {{ ref('fct_obito') }} f
join {{ ref('dim_tempo') }} t on t.sk_tempo = f.sk_tempo_obito
group by 1, 2, 3
