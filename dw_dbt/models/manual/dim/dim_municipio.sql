{{ config(
    materialized='table', schema='dim', tags=['nacional', 'dim'],
    meta={'sistema_origem': 'DW', 'grupo': 'DIM', 'assunto': 'dim_municipio', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'cod_municipio',
          'descricao': 'Dimensão município (domínio de municípios, 6 dígitos), com o membro -1 não informado.'}
) }}

select row_number() over (order by codigo)::int as sk_municipio, codigo as cod_municipio, codigo_ibge, nome as municipio, uf, microrregiao, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_municipio_consolidado') }}
union all
select -1, '-1', null, 'NÃO INFORMADO', null, null, {{ dt_carga() }}
