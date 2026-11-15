{{ config_cadastro('CID10', 'categoria_hierarquia', ['cat'], 'Categoria da CID-10 (3 caracteres) com grupo e capítulo.') }}
select distinct on (c.cat) c.cat, c.descricao as categoria, c.classif, g.catinic as grupo_inicio, g.catfim as grupo_fim, g.grupo,
       g.numcap, g.capitulo, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_dominio_cid10_categorias') }} c
left join {{ ref('int_cad_cid_grupo_capitulo') }} g on c.cat between g.catinic and g.catfim
order by c.cat, g.catinic desc  -- grupos aninhados: fica o mais específico (o que começa mais perto da categoria)
