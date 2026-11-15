{{ config_cadastro('TERRITORIO', 'municipio_classificacao', ['codigo'], 'Município + classificações territoriais: Amazônia Legal, semiárido, fronteira, extrema pobreza, capital, PNDR, região metropolitana, território da cidadania.') }}
select t.*,
       {{ pertence('ibge_amazlegal', 't.codigo') }} as amazonia_legal,
       {{ pertence('ibge_semiarido', 't.codigo') }} as semiarido,
       {{ pertence('ibge_frontfaixa', 't.codigo') }} as faixa_de_fronteira,
       {{ pertence('ibge_extrpobrez', 't.codigo') }} as extrema_pobreza,
       exists (select 1 from {{ ref('int_cad_dominio_ibge_capital') }} c where c.codigo = t.codigo) as capital,
       {{ nome_da_descricao('pn.descricao') }} as regiao_pndr,
       {{ nome_da_descricao('rm.descricao') }} as regiao_metropolitana,
       {{ nome_da_descricao('tc.descricao') }} as territorio_cidadania
from {{ ref('int_cad_territorio_municipio_saude') }} t
left join {{ agrupamento_por_municipio('ibge_pndr') }} pn on pn.codigo = t.codigo
left join {{ agrupamento_por_municipio('ibge_regmetr') }} rm on rm.codigo = t.codigo
left join {{ agrupamento_por_municipio('ibge_terrcid') }} tc on tc.codigo = t.codigo
