{{ config(
    materialized='incremental', incremental_strategy='merge', schema='fct', tags=['nacional', 'fct'],
    unique_key=['uf', 'ano', 'contador'], indexes=[{'columns': ['uf', 'ano', 'contador'], 'unique': True}],
    meta={'sistema_origem': 'DW', 'grupo': 'FCT', 'assunto': 'fct_obito', 'uf': 'BR', 'tipo_carga': 'MERGE', 'chave_negocio': 'uf,ano,contador',
          'descricao': 'Fato óbito (grão: declaração de óbito), com chaves das dimensões (-1 = não informado).'}
) }}
select
    o.uf, o.ano, o.contador,
    {{ sk_ou_nao_informado('t.sk_tempo') }} as sk_tempo_obito, {{ sk_ou_nao_informado('m.sk_municipio') }} as sk_municipio_residencia,
    {{ sk_ou_nao_informado('est.sk_estabelecimento') }} as sk_estabelecimento, {{ sk_ou_nao_informado('c.sk_cid') }} as sk_cid_causa_basica,
    o.sexo, o.racacor, o.idade, o.tipobito, o.circobito,
    o.dt_transacao, {{ dt_carga() }} as dt_carga
from {{ ref('int_mov_enr_obito') }} o
left join {{ ref('dim_tempo') }} t on t.data = o.dt_obito
left join {{ ref('dim_municipio') }} m on m.cod_municipio = o.cod_municipio_residencia
left join {{ ref('dim_estabelecimento') }} est on est.cod_cnes = o.codestab
left join {{ ref('dim_cid') }} c on c.cod_cid = o.cid_causa_basica
{% if is_incremental() %}where o.dt_carga > (select coalesce(max(dt_carga), date '1900-01-01') from {{ this }}){% endif %}
