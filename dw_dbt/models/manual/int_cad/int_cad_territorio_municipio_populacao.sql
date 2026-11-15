{{ config_cadastro('TERRITORIO', 'municipio_populacao', ['codigo'], 'Município + população do ano mais recente (TCU) e população por sexo (SVS).') }}
with tcu as (
    select distinct on (munic_res) munic_res, ano, {{ numero('populacao') }} as populacao
    from {{ ref('int_cad_dominio_populacao_tcu') }} order by munic_res, ano desc
),
svs as (
    select cod_mun, sum({{ numero('pop') }}) filter (where sexo = '1') as populacao_masculina,
           sum({{ numero('pop') }}) filter (where sexo = '2') as populacao_feminina
    from {{ ref('int_cad_dominio_populacao_svs') }}
    where ano = (select max(ano) from {{ ref('int_cad_dominio_populacao_svs') }})
    group by cod_mun
)
select t.*, tcu.ano as ano_populacao, tcu.populacao, svs.populacao_masculina, svs.populacao_feminina
from {{ ref('int_cad_territorio_municipio_classificacao') }} t
left join tcu on tcu.munic_res = t.codigo_ibge
left join svs on svs.cod_mun = t.codigo_ibge
