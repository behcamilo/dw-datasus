{{ config(
    materialized='table', schema='fct', tags=['nacional', 'fct'],
    meta={'sistema_origem': 'DW', 'grupo': 'FCT', 'assunto': 'fct_cnes_equipamento_mes', 'uf': 'BR', 'tipo_carga': 'FOTO', 'chave_negocio': 'uf,cnes,tipequip,codequip,competen',
          'descricao': 'Foto mensal de equipamentos (CNES-EQ): existentes e em uso por estabelecimento e competência.'}
) }}
select e.uf, e.cnes, e.tipequip, e.codequip, c.competen, {{ sk_ou_nao_informado('t.sk_tempo') }} as sk_tempo_competencia,
       {{ sk_ou_nao_informado('est.sk_estabelecimento') }} as sk_estabelecimento, {{ sk_ou_nao_informado('eq.sk_equipamento_tipo') }} as sk_equipamento_tipo,
       {{ numero('e.qt_exist') }} as qt_exist, {{ numero('e.qt_uso') }} as qt_uso, e.dt_transacao, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_nac_cnes_eq_equipamento') }} e
{{ competencias_da_versao('e') }}
left join {{ ref('dim_tempo') }} t on t.data = ctl.f_data(c.competen, 'YYYYMM')
left join {{ ref('dim_estabelecimento') }} est on est.cod_cnes = e.cnes
left join {{ ref('dim_equipamento_tipo') }} eq on eq.cod_equipamento = e.tipequip
