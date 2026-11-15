{{ config(
    materialized='table', schema='agg', tags=['nacional', 'agg'],
    meta={'sistema_origem': 'DW', 'grupo': 'AGG', 'assunto': 'agg_leito_uf_mes', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'uf,competen',
          'descricao': 'Leitos existentes e leitos SUS por UF e competência (CNES-LT).'}
) }}
select uf, competen, sum(qt_exist) as leitos_existentes, sum(qt_sus) as leitos_sus, count(distinct cnes) as estabelecimentos, {{ dt_carga() }} as dt_carga
from {{ ref('fct_cnes_leito_mes') }}
group by 1, 2
