{{ config(
    materialized='table', schema='dim', tags=['nacional', 'dim'],
    meta={'sistema_origem': 'DW', 'grupo': 'DIM', 'assunto': 'dim_estabelecimento', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'cod_cnes',
          'descricao': 'Dimensão estabelecimento (CNES-ST, foto mais recente + nome do domínio CNES), com o membro -1 não informado.'}
) }}

select row_number() over (order by e.cnes)::int as sk_estabelecimento, e.cnes as cod_cnes, e.uf, d.fantasia as nome_fantasia, d.raz_soci as razao_social,
       e.tp_unid as tipo_unidade, e.nat_jur as natureza_juridica, e.codufmun as cod_municipio, {{ dt_carga() }} as dt_carga
from ({{ estabelecimento_atual() }}) e
left join {{ ref('int_cad_dominio_cnes_cadgerbr') }} d on d.cnes = e.cnes
union all
select -1, '-1', null, 'NÃO INFORMADO', null, null, null, null, {{ dt_carga() }}
