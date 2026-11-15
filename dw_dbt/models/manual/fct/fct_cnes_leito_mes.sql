{{ config(
    materialized='table', schema='fct', tags=['nacional', 'fct'],
    meta={'sistema_origem': 'DW', 'grupo': 'FCT', 'assunto': 'fct_cnes_leito_mes', 'uf': 'BR', 'tipo_carga': 'FOTO', 'chave_negocio': 'uf,cnes,competen,tp_leito,codleito',
          'descricao': 'Foto mensal de leitos (CNES-LT): existentes e SUS por estabelecimento, tipo de leito e competência.'}
) }}
select l.uf, l.cnes, c.competen, l.tp_leito, l.codleito, {{ sk_ou_nao_informado('t.sk_tempo') }} as sk_tempo_competencia,
       {{ sk_ou_nao_informado('est.sk_estabelecimento') }} as sk_estabelecimento, {{ sk_ou_nao_informado('lt.sk_leito_tipo') }} as sk_leito_tipo,
       {{ numero('l.qt_exist') }} as qt_exist, {{ numero('l.qt_sus') }} as qt_sus, l.dt_transacao, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_nac_cnes_lt_leito') }} l
{{ competencias_da_versao('l') }}
left join {{ ref('dim_tempo') }} t on t.data = ctl.f_data(c.competen, 'YYYYMM')
left join {{ ref('dim_estabelecimento') }} est on est.cod_cnes = l.cnes
left join {{ ref('dim_leito_tipo') }} lt on lt.cod_leito = l.codleito
