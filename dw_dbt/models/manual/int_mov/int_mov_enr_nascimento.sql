{{ config(
    materialized='incremental', incremental_strategy='merge', schema='int_mov', tags=['nacional', 'int_mov'],
    unique_key=['uf', 'ano', 'contador'], indexes=[{'columns': ['uf', 'ano', 'contador'], 'unique': True}],
    meta={'sistema_origem': 'SINASC', 'grupo': 'DN', 'assunto': 'nascimento_enriquecido', 'uf': 'BR', 'tipo_carga': 'MERGE',
          'chave_negocio': 'uf,ano,contador',
          'descricao': 'Nascimento enriquecido: junta nascimento, gestacao_parto e pais (movimento tratado) e consulta o cadastro (estabelecimento do CNES, município da mãe).'}
) }}
with n as (
    select * from {{ ref('int_mov_nac_sinasc_dn_nascimento') }}
    {% if is_incremental() %}where dt_carga > (select coalesce(max(dt_carga), date '1900-01-01') from {{ this }}){% endif %}
),
est as ({{ estabelecimento_atual() }})
select
    n.uf, n.ano, n.contador,
    {{ data_sim('n.dtnasc') }} as dt_nascimento, n.sexo, n.racacor, {{ numero('n.peso') }} as peso, n.apgar5, n.locnasc, n.codestab, n.codmunnasc,
    g.consultas, g.gestacao, g.parto, g.semagestac,
    p.idademae, p.escmae, p.codmunres as cod_municipio_residencia, mun.nome as municipio_residencia,
    e.tp_unid as tipo_unidade_cnes,
    n.dt_transacao, {{ dt_carga() }} as dt_carga
from n
left join {{ ref('int_mov_nac_sinasc_dn_gestacao_parto') }} g using (uf, ano, contador)
left join {{ ref('int_mov_nac_sinasc_dn_pais') }} p using (uf, ano, contador)
left join est e on e.uf = n.uf and e.cnes = n.codestab
left join {{ ref('int_cad_municipio_consolidado') }} mun on mun.codigo = p.codmunres
