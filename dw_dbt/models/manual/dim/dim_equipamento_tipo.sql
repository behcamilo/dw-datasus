{{ config(
    materialized='table', schema='dim', tags=['nacional', 'dim'],
    meta={'sistema_origem': 'DW', 'grupo': 'DIM', 'assunto': 'dim_equipamento_tipo', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'cod_equipamento',
          'descricao': 'Dimensão tipo de equipamento (CNES-EQ), com o membro -1 não informado.'}
) }}

select row_number() over (order by codigo)::int as sk_equipamento_tipo, codigo as cod_equipamento, descricao as equipamento, {{ dt_carga() }} as dt_carga
from (select distinct on (codigo) * from {{ ref('int_cad_dominio_cnes_equipam2508') }} order by codigo, seq) d
union all
select -1, '-1', 'NÃO INFORMADO', {{ dt_carga() }}
