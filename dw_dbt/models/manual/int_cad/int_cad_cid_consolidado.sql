{{ config_cadastro('CID10', 'cid_consolidado', ['codigo'], 'CID-10 consolidada: categorias (3 caracteres) e subcategorias (4), com a hierarquia completa. A INT_MOV valida o CID aqui (o movimento usa os dois tamanhos).') }}
select cat as codigo, 'categoria' as nivel, categoria as descricao, null::text as restrsexo, null::text as causaobito,
       cat, categoria, grupo, numcap, capitulo, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_cid_categoria_hierarquia') }}
-- categoria sem subdivisão já vem no arquivo de subcategorias com o mesmo código de 3 caracteres (ex.: N12): fica só a de lá
where cat not in (select subcat from {{ ref('int_cad_cid_subcategoria_hierarquia') }})
union all
select subcat, 'subcategoria', subcategoria, restrsexo, causaobito, cat, categoria, grupo, numcap, capitulo, {{ dt_carga() }}
from {{ ref('int_cad_cid_subcategoria_hierarquia') }}
