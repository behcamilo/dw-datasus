{{ config(
    materialized='table', schema='dim', tags=['nacional', 'dim'],
    meta={'sistema_origem': 'DW', 'grupo': 'DIM', 'assunto': 'dim_tempo', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'data',
          'descricao': 'Dimensão tempo (um dia por linha, 2015 a 2023), gerada pelo próprio DW, com o membro -1 não informado.'}
) }}
select to_char(d, 'YYYYMMDD')::int as sk_tempo, d::date as data, extract(year from d)::int as ano, extract(month from d)::int as mes,
       extract(quarter from d)::int as trimestre, extract(isodow from d)::int as dia_semana, {{ dt_carga() }} as dt_carga
from generate_series(date '2015-01-01', date '2023-12-31', interval '1 day') d
union all
select -1, null, null, null, null, null, {{ dt_carga() }}
