{{ config(
    materialized='table', schema='dim', tags=['nacional', 'dim'],
    meta={'sistema_origem': 'DW', 'grupo': 'DIM', 'assunto': 'dim_procedimento', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'cod_procedimento',
          'descricao': 'Dimensão procedimento (SIGTAP, versão mais recente de cada procedimento), com o membro -1 não informado.'}
) }}

select row_number() over (order by codigo)::int as sk_procedimento, codigo as cod_procedimento, no_procedimento as procedimento,
       tp_complexidade, vl_sh, vl_sa, vl_sp, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_procedimento_consolidado') }}
union all
select -1, '-1', 'NÃO INFORMADO', null, null, null, null, {{ dt_carga() }}
