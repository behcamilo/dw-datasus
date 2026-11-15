{# Configuração dos cadastros nacionais em cadeia (território, SIGTAP, CID): merge na chave. #}
{% macro config_cadastro(grupo, assunto, chave, descricao) -%}
    {{ config(materialized='incremental', incremental_strategy='merge', schema='int_cad', tags=['nacional', 'int_cad', grupo | lower],
              unique_key=chave, indexes=[{'columns': chave, 'unique': True}],
              meta={'sistema_origem': 'DW', 'grupo': grupo, 'assunto': assunto, 'uf': 'BR', 'tipo_carga': 'MERGE',
                    'chave_negocio': chave | join(','), 'descricao': descricao}) }}
{%- endmacro %}

{# O município (6 dígitos) pertence a um agrupamento "Sim/Não" do TabWin (Amazônia Legal, semiárido...)? #}
{% macro pertence(dominio, municipio) -%}
    exists (select 1 from {{ ref('int_cad_dominio_' ~ dominio) }} x where x.codigo = {{ municipio }} and x.descricao = 'Sim')
{%- endmacro %}

{# Agrupamento do TabWin cuja descrição é "<código> <nome>" (ex.: '12001 Alto Acre'): separa o código e o nome. #}
{% macro codigo_da_descricao(coluna) -%}substring({{ coluna }} from '^([0-9]+) '){%- endmacro %}
{% macro nome_da_descricao(coluna) -%}regexp_replace({{ coluna }}, '^[0-9]+ ', ''){%- endmacro %}

{# Uma linha por município num agrupamento do TabWin. #}
{% macro agrupamento_por_municipio(dominio) -%}
    (select distinct on (codigo) * from {{ ref('int_cad_dominio_' ~ dominio) }} order by codigo, seq)
{%- endmacro %}

{# Última versão de cada código de uma tabela da SIGTAP (a competência faz parte da chave do domínio). #}
{% macro sigtap_atual(dominio, chave) -%}
    (select distinct on ({{ chave }}) * from {{ ref('int_cad_dominio_sigtap_' ~ dominio) }} order by {{ chave }}, competencia desc)
{%- endmacro %}

{# Linhas da competência mais recente de uma tabela de relação da SIGTAP (rl_...). #}
{% macro sigtap_relacao_atual(dominio) -%}
    (select * from {{ ref('int_cad_dominio_sigtap_' ~ dominio) }}
     where competencia = (select max(competencia) from {{ ref('int_cad_dominio_sigtap_' ~ dominio) }}))
{%- endmacro %}
