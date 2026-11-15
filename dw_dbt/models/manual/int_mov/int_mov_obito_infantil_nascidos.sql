{{ config(
    materialized='table', schema='int_mov', tags=['nacional', 'int_mov'],
    meta={'sistema_origem': 'DW', 'grupo': 'INT_MOV', 'assunto': 'obito_infantil_nascidos', 'uf': 'BR', 'tipo_carga': 'FULL',
          'chave_negocio': 'cod_municipio,ano',
          'descricao': 'Óbitos de menores de 1 ano (SIM) e nascidos vivos (SINASC) por município de residência e ano: a base da taxa de mortalidade infantil.'}
) }}
with obitos as (
    select codmunres as cod_municipio, extract(year from dt_obito)::int as ano, count(*) as obitos_infantis
    from {{ ref('int_mov_nac_obito_classificado') }} where obito_infantil group by 1, 2
),
nascidos as (
    select codmunnasc as cod_municipio, extract(year from dt_nascimento)::int as ano, count(*) as nascidos_vivos
    from {{ ref('int_mov_nac_nascimento_classificado') }} group by 1, 2
)
select cod_municipio, ano, coalesce(o.obitos_infantis, 0) as obitos_infantis, coalesce(n.nascidos_vivos, 0) as nascidos_vivos,
       round(1000.0 * coalesce(o.obitos_infantis, 0) / nullif(n.nascidos_vivos, 0), 2) as taxa_por_mil, {{ dt_carga() }} as dt_carga
from obitos o full join nascidos n using (cod_municipio, ano)
where ano is not null
