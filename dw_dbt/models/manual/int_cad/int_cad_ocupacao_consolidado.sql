{{ config_cadastro('SIGTAP', 'ocupacao_consolidado', ['codigo'], 'Ocupação (CBO) consolidada: versão mais recente da SIGTAP + quantos procedimentos ela pode executar. A INT_MOV valida o CBO aqui.') }}
with procedimentos as (
    select co_ocupacao, count(*) as qtd_procedimentos from {{ sigtap_relacao_atual('rl_procedimento_ocupacao') }} group by co_ocupacao
)
select o.co_ocupacao as codigo, o.no_ocupacao, o.competencia as competencia_vigente,
       coalesce(p.qtd_procedimentos, 0) as qtd_procedimentos, {{ dt_carga() }} as dt_carga
from {{ sigtap_atual('ocupacao', 'co_ocupacao') }} o
left join procedimentos p using (co_ocupacao)
