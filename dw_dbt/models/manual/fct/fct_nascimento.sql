{{ config(
    materialized='incremental', incremental_strategy='merge', schema='fct', tags=['nacional', 'fct'],
    unique_key=['uf', 'ano', 'contador'], indexes=[{'columns': ['uf', 'ano', 'contador'], 'unique': True}],
    meta={'sistema_origem': 'DW', 'grupo': 'FCT', 'assunto': 'fct_nascimento', 'uf': 'BR', 'tipo_carga': 'MERGE', 'chave_negocio': 'uf,ano,contador',
          'descricao': 'Fato nascimento (grão: declaração de nascido vivo), com chaves das dimensões (-1 = não informado).'}
) }}
select
    n.uf, n.ano, n.contador,
    {{ sk_ou_nao_informado('t.sk_tempo') }} as sk_tempo_nascimento, {{ sk_ou_nao_informado('m.sk_municipio') }} as sk_municipio_residencia_mae,
    {{ sk_ou_nao_informado('est.sk_estabelecimento') }} as sk_estabelecimento,
    n.sexo, n.racacor, n.peso, n.apgar5, n.consultas, n.gestacao, n.parto, n.idademae,
    n.dt_transacao, {{ dt_carga() }} as dt_carga
from {{ ref('int_mov_enr_nascimento') }} n
left join {{ ref('dim_tempo') }} t on t.data = n.dt_nascimento
left join {{ ref('dim_municipio') }} m on m.cod_municipio = n.cod_municipio_residencia
left join {{ ref('dim_estabelecimento') }} est on est.cod_cnes = n.codestab
{% if is_incremental() %}where n.dt_carga > (select coalesce(max(dt_carga), date '1900-01-01') from {{ this }}){% endif %}
