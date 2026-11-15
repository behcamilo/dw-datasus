{{ config(
    materialized='incremental', incremental_strategy='merge', schema='int_mov', tags=['nacional', 'int_mov'],
    unique_key=['uf', 'ano', 'contador'], indexes=[{'columns': ['uf', 'ano', 'contador'], 'unique': True}],
    meta={'sistema_origem': 'SIM', 'grupo': 'DO', 'assunto': 'obito_enriquecido', 'uf': 'BR', 'tipo_carga': 'MERGE',
          'chave_negocio': 'uf,ano,contador',
          'descricao': 'Óbito enriquecido: junta obito, falecido e causa_morte (movimento tratado) e consulta o cadastro (estabelecimento do CNES, município de residência).'}
) }}
with o as (
    select * from {{ ref('int_mov_nac_sim_do_obito') }}
    {% if is_incremental() %}where dt_carga > (select coalesce(max(dt_carga), date '1900-01-01') from {{ this }}){% endif %}
),
est as ({{ estabelecimento_atual() }})
select
    o.uf, o.ano, o.contador,
    {{ data_sim('o.dtobito') }} as dt_obito, o.tipobito, o.circobito, o.lococor, o.codestab, o.codmunocor,
    f.sexo, f.racacor, f.idade, {{ data_sim('f.dtnasc') }} as dt_nascimento_falecido, f.codmunres as cod_municipio_residencia, mun.nome as municipio_residencia,
    c.causabas as cid_causa_basica,
    e.tp_unid as tipo_unidade_cnes,
    o.dt_transacao, {{ dt_carga() }} as dt_carga
from o
left join {{ ref('int_mov_nac_sim_do_falecido') }} f using (uf, ano, contador)
left join {{ ref('int_mov_nac_sim_do_causa_morte') }} c using (uf, ano, contador)
left join est e on e.uf = o.uf and e.cnes = o.codestab
left join {{ ref('int_cad_municipio_consolidado') }} mun on mun.codigo = f.codmunres
