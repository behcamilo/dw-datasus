{{ config(
    materialized='table', schema='dim', tags=['nacional', 'dim'],
    meta={'sistema_origem': 'DW', 'grupo': 'DIM', 'assunto': 'dim_habilitacao', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'cod_habilitacao',
          'descricao': 'Dimensão habilitação (CNES-HB), com o membro -1 não informado.'}
) }}

select row_number() over (order by cd_habilit)::int as sk_habilitacao, cd_habilit as cod_habilitacao, ds_habil as habilitacao, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_dominio_cnes_habilita') }}
union all
select -1, '-1', 'NÃO INFORMADO', {{ dt_carga() }}
