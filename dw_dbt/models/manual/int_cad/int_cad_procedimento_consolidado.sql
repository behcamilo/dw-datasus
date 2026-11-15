{{ config_cadastro('SIGTAP', 'procedimento_consolidado', ['codigo'], 'Procedimento consolidado da SIGTAP (hierarquia, financiamento, registro e compatibilidades). A INT_MOV valida o código de procedimento aqui.') }}
select p.co_procedimento as codigo, p.*,
       case p.tp_complexidade when '1' then 'ATENÇÃO BÁSICA' when '2' then 'MÉDIA COMPLEXIDADE' when '3' then 'ALTA COMPLEXIDADE'
            else 'NÃO SE APLICA' end as complexidade
from {{ ref('int_cad_sigtap_procedimento_compatibilidades') }} p
