{{ config_cadastro('SIGTAP', 'procedimento_financiamento', ['co_procedimento'], 'Procedimento + tipo de financiamento e rubrica.') }}
select p.*, f.no_financiamento, r.no_rubrica
from {{ ref('int_cad_sigtap_procedimento_hierarquia') }} p
left join {{ sigtap_atual('financiamento', 'co_financiamento') }} f using (co_financiamento)
left join {{ sigtap_atual('rubrica', 'co_rubrica') }} r using (co_rubrica)
