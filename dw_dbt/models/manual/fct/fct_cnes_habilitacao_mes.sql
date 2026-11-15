{{ config(
    materialized='table', schema='fct', tags=['nacional', 'fct'],
    meta={'sistema_origem': 'DW', 'grupo': 'FCT', 'assunto': 'fct_cnes_habilitacao_mes', 'uf': 'BR', 'tipo_carga': 'FOTO', 'chave_negocio': 'uf,cnes,sgruphab,competen',
          'descricao': 'Foto mensal de habilitações (CNES-HB) por estabelecimento e competência.'}
) }}
select h.uf, h.cnes, h.sgruphab, c.competen, {{ sk_ou_nao_informado('t.sk_tempo') }} as sk_tempo_competencia,
       {{ sk_ou_nao_informado('est.sk_estabelecimento') }} as sk_estabelecimento, {{ sk_ou_nao_informado('hab.sk_habilitacao') }} as sk_habilitacao,
       {{ numero('h.nuleitos') }} as nuleitos, h.dt_transacao, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_nac_cnes_hb_habilitacao') }} h
{{ competencias_da_versao('h') }}
left join {{ ref('dim_tempo') }} t on t.data = ctl.f_data(c.competen, 'YYYYMM')
left join {{ ref('dim_estabelecimento') }} est on est.cod_cnes = h.cnes
left join {{ ref('dim_habilitacao') }} hab on hab.cod_habilitacao = h.sgruphab
