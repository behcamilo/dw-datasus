{{ config(
    materialized='table', schema='dim', tags=['nacional', 'dim'],
    meta={'sistema_origem': 'DW', 'grupo': 'DIM', 'assunto': 'dim_profissional', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'doc_hash,cod_cbo',
          'descricao': 'Dimensão profissional do SIH-SP (documento com hash + CBO), com o membro -1 não informado.'}
) }}

select row_number() over (order by sp_pf_doc, sp_pf_cbo)::int as sk_profissional, sp_pf_doc as doc_hash, sp_pf_cbo as cod_cbo, {{ dt_carga() }} as dt_carga
from (select distinct sp_pf_doc, sp_pf_cbo from {{ ref('int_cad_nac_sih_sp_profissional') }}) p
union all
select -1, '-1', null, {{ dt_carga() }}
