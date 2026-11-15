{# O schema de cada modelo é o nome da camada (sem o prefixo que o dbt colocaria). #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}{{ target.schema }}{%- else -%}{{ custom_schema_name | trim }}{%- endif -%}
{%- endmacro %}

{# Data de referência da carga, gravada em DT_CARGA de toda tabela carregada. #}
{% macro dt_carga() -%}
    cast('{{ var("dt_carga") }}' as date)
{%- endmacro %}

{# União das tabelas de cada UF (prefixo_<uf>), com a coluna uf. O ref() de cada UF entra nas dependências do modelo. #}
{% macro uniao_ufs(prefixo) -%}
    {%- for uf in var('ufs') %}
    select '{{ uf | upper }}'::text as uf, t.* from {{ ref(prefixo ~ '_' ~ uf) }} t
    {%- if not loop.last %} union all {% endif %}
    {%- endfor %}
{%- endmacro %}

{# Datas do DATASUS são texto: formato AAAAMMDD (SIH), DDMMAAAA (SIM/SINASC). Inválida ou sentinela vira NULL. #}
{% macro data_sih(coluna) -%}ctl.f_data({{ coluna }}, 'YYYYMMDD'){%- endmacro %}
{% macro data_sim(coluna) -%}ctl.f_data({{ coluna }}, 'DDMMYYYY'){%- endmacro %}

{# Chave de dimensão: se a chave do fato não achou membro na dimensão (nula ou sentinela), usa o membro -1 "não informado". #}
{% macro sk_ou_nao_informado(coluna) -%}coalesce({{ coluna }}, -1){%- endmacro %}

{# Número em texto (valores do SIH) -> numeric; vazio ou inválido vira NULL em vez de derrubar a carga. #}
{% macro numero(coluna) -%}(case when {{ coluna }} ~ '^-?[0-9]+(\.[0-9]+)?$' then {{ coluna }}::numeric end){%- endmacro %}

{# Versão atual de cada estabelecimento no CNES-ST (SCD2): cadastro de referência para enriquecer movimento. #}
{% macro estabelecimento_atual() -%}
    select uf, cnes, tp_unid, nat_jur, codufmun, valido_de as competen
    from {{ ref('int_cad_nac_cnes_st_identificacao') }}
    where atual
{%- endmacro %}

{# Série mensal a partir do histórico: uma linha por competência em que a versão valeu.
   A versão atual vale até o mês anterior ao da carga, porque a foto do mês M só sai em M+1. #}
{% macro competencias_da_versao(v) -%}
    cross join lateral (
        select to_char(m, 'YYYYMM') as competen
        from generate_series(to_date({{ v }}.valido_de, 'YYYYMM'),
                             coalesce(to_date({{ v }}.valido_ate, 'YYYYMM') - interval '1 month', date_trunc('month', {{ dt_carga() }}) - interval '1 month'),
                             interval '1 month') m
    ) c
{%- endmacro %}
