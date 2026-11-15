{{ config(
    materialized='table', schema='dim', tags=['nacional', 'dim'],
    meta={'sistema_origem': 'DW', 'grupo': 'DIM', 'assunto': 'dim_sexo', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'cod_sexo',
          'descricao': 'Dimensão sexo (domínio do SIH), com o membro -1 não informado.'}
) }}

select row_number() over (order by codigo)::int as sk_sexo, codigo as cod_sexo, descricao as sexo, {{ dt_carga() }} as dt_carga
from (select distinct on (codigo) * from {{ ref('int_cad_dominio_sih_sexo') }} order by codigo, seq) d
union all
select -1, '-1', 'NÃO INFORMADO', {{ dt_carga() }}
