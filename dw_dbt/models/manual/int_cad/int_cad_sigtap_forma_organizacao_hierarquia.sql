{{ config_cadastro('SIGTAP', 'forma_organizacao_hierarquia', ['co_grupo', 'co_sub_grupo', 'co_forma_organizacao'], 'Forma de organização da SIGTAP com subgrupo e grupo (versão mais recente de cada código).') }}
select f.co_grupo, f.co_sub_grupo, f.co_forma_organizacao, f.no_forma_organizacao, s.no_sub_grupo, g.no_grupo,
       {{ dt_carga() }} as dt_carga
from {{ sigtap_atual('forma_organizacao', 'co_grupo, co_sub_grupo, co_forma_organizacao') }} f
left join {{ sigtap_atual('sub_grupo', 'co_grupo, co_sub_grupo') }} s using (co_grupo, co_sub_grupo)
left join {{ sigtap_atual('grupo', 'co_grupo') }} g using (co_grupo)
