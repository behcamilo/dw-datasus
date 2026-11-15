{{ config_cadastro('CID10', 'grupo_capitulo', ['catinic', 'catfim'], 'Grupo da CID-10 (intervalo de categorias) com o capítulo a que pertence.') }}
select g.catinic, g.catfim, g.descricao as grupo, c.numcap, c.descricao as capitulo, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_dominio_cid10_grupos') }} g
left join {{ ref('int_cad_dominio_cid10_capitulos') }} c on g.catinic between c.catinic and c.catfim
