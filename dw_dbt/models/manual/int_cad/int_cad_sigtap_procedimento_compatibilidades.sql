{{ config_cadastro('SIGTAP', 'procedimento_compatibilidades', ['co_procedimento'], 'Procedimento + quantas compatibilidades ele tem na competência vigente: CID, ocupação (CBO), tipo de leito, serviço e habilitação.') }}
{% set relacoes = ['cid', 'ocupacao', 'leito', 'servico', 'habilitacao'] %}
with
{%- for r in relacoes %}
qtd_{{ r }} as (select co_procedimento, count(*) as qtd_{{ r }} from {{ sigtap_relacao_atual('rl_procedimento_' ~ r) }} group by co_procedimento){{ ',' if not loop.last }}
{%- endfor %}
select p.*
{%- for r in relacoes %}, coalesce(qtd_{{ r }}.qtd_{{ r }}, 0) as qtd_{{ r }}{% endfor %}
from {{ ref('int_cad_sigtap_procedimento_modalidade_registro') }} p
{%- for r in relacoes %}
left join qtd_{{ r }} using (co_procedimento)
{%- endfor %}
