{{ config(
    materialized='table', schema='dim', tags=['nacional', 'dim'],
    meta={'sistema_origem': 'DW', 'grupo': 'DIM', 'assunto': 'dim_cid', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'cod_cid',
          'descricao': 'Dimensão CID-10 (diagnóstico principal), com o membro -1 não informado.'}
) }}

select row_number() over (order by codigo)::int as sk_cid, codigo as cod_cid, descricao as cid, nivel, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_cid_consolidado') }}
union all
select -1, '-1', 'NÃO INFORMADO', null, {{ dt_carga() }}
