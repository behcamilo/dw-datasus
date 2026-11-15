{{ config_cadastro('TERRITORIO', 'municipio_micro', ['codigo'], 'Município do IBGE com microrregião e mesorregião (1ª etapa da cadeia do território).') }}
select m.codigo, m.codigo_ibge, m.nome, m.id_regiao_imediata,
       mi.id as id_microrregiao, mi.nome as microrregiao, me.id as id_mesorregiao, me.nome as mesorregiao,
       {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_dominio_ibge_municipios') }} m
left join {{ ref('int_cad_dominio_ibge_microrregioes') }} mi on mi.id = m.id_microrregiao
left join {{ ref('int_cad_dominio_ibge_mesorregioes') }} me on me.id = mi.id_mesorregiao
