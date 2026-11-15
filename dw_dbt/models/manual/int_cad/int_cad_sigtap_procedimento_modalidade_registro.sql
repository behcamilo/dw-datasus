{{ config_cadastro('SIGTAP', 'procedimento_modalidade_registro', ['co_procedimento'], 'Procedimento + modalidades de atendimento e instrumentos de registro em que pode ser lançado (AIH, BPA, APAC...).') }}
with modalidade as (
    select rl.co_procedimento, string_agg(m.no_modalidade, ' | ' order by m.no_modalidade) as modalidades
    from {{ sigtap_relacao_atual('rl_procedimento_modalidade') }} rl
    join {{ sigtap_atual('modalidade', 'co_modalidade') }} m using (co_modalidade)
    group by rl.co_procedimento
),
registro as (
    select rl.co_procedimento, string_agg(r.no_registro, ' | ' order by r.no_registro) as instrumentos_registro,
           bool_or(r.co_registro = '03') as registra_em_aih
    from {{ sigtap_relacao_atual('rl_procedimento_registro') }} rl
    join {{ sigtap_atual('registro', 'co_registro') }} r using (co_registro)
    group by rl.co_procedimento
)
select p.*, m.modalidades, r.instrumentos_registro, coalesce(r.registra_em_aih, false) as registra_em_aih
from {{ ref('int_cad_sigtap_procedimento_financiamento') }} p
left join modalidade m using (co_procedimento)
left join registro r using (co_procedimento)
