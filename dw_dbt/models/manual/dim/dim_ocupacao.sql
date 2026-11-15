{{ config(
    materialized='table', schema='dim', tags=['nacional', 'dim'],
    meta={'sistema_origem': 'DW', 'grupo': 'DIM', 'assunto': 'dim_ocupacao', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'cod_ocupacao',
          'descricao': 'Dimensão ocupação (CBO, versão mais recente), com o membro -1 não informado.'}
) }}

select row_number() over (order by codigo)::int as sk_ocupacao, codigo as cod_ocupacao, no_ocupacao as ocupacao, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_ocupacao_consolidado') }}
union all
select -1, '-1', 'NÃO INFORMADO', {{ dt_carga() }}
