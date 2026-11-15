{{ config(
    materialized='table', schema='dim', tags=['nacional', 'dim'],
    meta={'sistema_origem': 'DW', 'grupo': 'DIM', 'assunto': 'dim_leito_tipo', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'cod_leito',
          'descricao': 'Dimensão tipo de leito (CNES-LT), com o membro -1 não informado.'}
) }}

select row_number() over (order by codigo)::int as sk_leito_tipo, codigo as cod_leito, descricao as leito, {{ dt_carga() }} as dt_carga
from (select distinct on (codigo) * from {{ ref('int_cad_dominio_cnes_esp_leit') }} order by codigo, seq) d
union all
select -1, '-1', 'NÃO INFORMADO', {{ dt_carga() }}
