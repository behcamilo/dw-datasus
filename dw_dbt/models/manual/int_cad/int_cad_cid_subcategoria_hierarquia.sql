{{ config_cadastro('CID10', 'subcategoria_hierarquia', ['subcat'], 'Subcategoria da CID-10 (4 caracteres) com categoria, grupo e capítulo; restrição de sexo e se pode ser causa de óbito.') }}
select s.subcat, s.descricao as subcategoria, s.restrsexo, s.causaobito,
       c.cat, c.categoria, c.grupo, c.numcap, c.capitulo, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_dominio_cid10_subcategorias') }} s
left join {{ ref('int_cad_cid_categoria_hierarquia') }} c on c.cat = substr(s.subcat, 1, 3)
