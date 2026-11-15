{{ config_cadastro('SIGTAP', 'procedimento_hierarquia', ['co_procedimento'], 'Procedimento da SIGTAP com grupo, subgrupo e forma de organização (os 6 primeiros dígitos do código).') }}
select p.co_procedimento, p.no_procedimento, p.tp_complexidade, p.tp_sexo, p.vl_idade_minima, p.vl_idade_maxima,
       p.qt_dias_permanencia, p.vl_sh, p.vl_sa, p.vl_sp, p.co_financiamento, p.co_rubrica, p.competencia as competencia_vigente,
       h.co_grupo, h.no_grupo, h.co_sub_grupo, h.no_sub_grupo, h.co_forma_organizacao, h.no_forma_organizacao,
       {{ dt_carga() }} as dt_carga
from {{ sigtap_atual('procedimento', 'co_procedimento') }} p
left join {{ ref('int_cad_sigtap_forma_organizacao_hierarquia') }} h
       on h.co_grupo = substr(p.co_procedimento, 1, 2) and h.co_sub_grupo = substr(p.co_procedimento, 3, 2)
      and h.co_forma_organizacao = substr(p.co_procedimento, 5, 2)
