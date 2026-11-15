{{ config_cadastro('TERRITORIO', 'municipio_saude', ['codigo'], 'Município + região e macrorregião de saúde e divisão administrativa estadual (TabWin).') }}
select t.*,
       {{ codigo_da_descricao('rs.descricao') }} as cod_regiao_saude, {{ nome_da_descricao('rs.descricao') }} as regiao_saude,
       {{ codigo_da_descricao('ms.descricao') }} as cod_macrorregiao_saude, {{ nome_da_descricao('ms.descricao') }} as macrorregiao_saude,
       {{ codigo_da_descricao('da.descricao') }} as cod_divisao_administrativa, {{ nome_da_descricao('da.descricao') }} as divisao_administrativa
from {{ ref('int_cad_territorio_municipio_regioes') }} t
left join {{ agrupamento_por_municipio('ibge_regsaud') }} rs on rs.codigo = t.codigo
left join {{ agrupamento_por_municipio('ibge_macsaud') }} ms on ms.codigo = t.codigo
left join {{ agrupamento_por_municipio('ibge_divadm') }} da on da.codigo = t.codigo
