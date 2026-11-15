{{ config(
    materialized='table', schema='fct', tags=['nacional', 'fct'],
    meta={'sistema_origem': 'DW', 'grupo': 'FCT', 'assunto': 'fct_cnes_estabelecimento_mes', 'uf': 'BR', 'tipo_carga': 'FOTO', 'chave_negocio': 'uf,cnes,competen',
          'descricao': 'Foto mensal do estabelecimento (CNES-ST): um registro por estabelecimento e competência.'}
) }}
select s.uf, s.cnes, c.competen, {{ sk_ou_nao_informado('t.sk_tempo') }} as sk_tempo_competencia, {{ sk_ou_nao_informado('est.sk_estabelecimento') }} as sk_estabelecimento,
       s.tp_unid, s.nat_jur, s.codufmun, s.dt_transacao, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_nac_cnes_st_identificacao') }} s
{{ competencias_da_versao('s') }}
left join {{ ref('dim_tempo') }} t on t.data = ctl.f_data(c.competen, 'YYYYMM')
left join {{ ref('dim_estabelecimento') }} est on est.cod_cnes = s.cnes
