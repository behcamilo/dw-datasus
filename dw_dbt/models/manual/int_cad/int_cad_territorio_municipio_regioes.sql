{{ config_cadastro('TERRITORIO', 'municipio_regioes', ['codigo'], 'Município + regiões geográficas imediata e intermediária, UF e grande região.') }}
select t.*, ri.nome as regiao_imediata, rt.id as id_regiao_intermediaria, rt.nome as regiao_intermediaria,
       u.sigla as uf, u.nome as nome_uf, r.sigla as sigla_regiao, r.nome as regiao
from {{ ref('int_cad_territorio_municipio_micro') }} t
left join {{ ref('int_cad_dominio_ibge_regioes_imediatas') }} ri on ri.id = t.id_regiao_imediata
left join {{ ref('int_cad_dominio_ibge_regioes_intermediarias') }} rt on rt.id = ri.id_regiao_intermediaria
left join {{ ref('int_cad_dominio_ibge_ufs') }} u on u.id = rt.id_uf
left join {{ ref('int_cad_dominio_ibge_regioes') }} r on r.id = u.id_regiao
