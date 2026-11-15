{{ config(
    materialized='table', schema='agg', tags=['nacional', 'agg'],
    meta={'sistema_origem': 'DW', 'grupo': 'AGG', 'assunto': 'agg_nascimento_municipio_mes', 'uf': 'BR', 'tipo_carga': 'FULL', 'chave_negocio': 'sk_municipio_residencia_mae,ano,mes',
          'descricao': 'Nascidos vivos por município de residência da mãe e mês do nascimento.'}
) }}
select f.sk_municipio_residencia_mae, t.ano, t.mes, count(*) as nascimentos, avg(f.peso) as peso_medio, {{ dt_carga() }} as dt_carga
from {{ ref('fct_nascimento') }} f
join {{ ref('dim_tempo') }} t on t.sk_tempo = f.sk_tempo_nascimento
group by 1, 2, 3
