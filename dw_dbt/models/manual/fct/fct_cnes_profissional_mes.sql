{{ config(
    materialized='table', schema='fct', tags=['nacional', 'fct'],
    meta={'sistema_origem': 'DW', 'grupo': 'FCT', 'assunto': 'fct_cnes_profissional_mes', 'uf': 'BR', 'tipo_carga': 'FOTO', 'chave_negocio': 'uf,id_origem',
          'descricao': 'Foto mensal de profissionais (CNES-PF): vínculo e carga horária por estabelecimento e competência.'}
) }}
select p.uf, p.id_origem, p.cnes, p.competen, {{ sk_ou_nao_informado('t.sk_tempo') }} as sk_tempo_competencia,
       {{ sk_ou_nao_informado('est.sk_estabelecimento') }} as sk_estabelecimento, {{ sk_ou_nao_informado('o.sk_ocupacao') }} as sk_ocupacao,
       v.vinculac, {{ numero('ch.hora_amb') }} as hora_amb, {{ numero('ch.horahosp') }} as horahosp, {{ numero('ch.horaoutr') }} as horaoutr,
       p.dt_transacao, {{ dt_carga() }} as dt_carga
from {{ ref('int_cad_nac_cnes_pf_profissional') }} p
left join {{ ref('int_cad_nac_cnes_pf_vinculo') }} v on v.uf = p.uf and v.id_origem = p.id_origem
left join {{ ref('int_cad_nac_cnes_pf_carga_horaria') }} ch on ch.uf = p.uf and ch.id_origem = p.id_origem
left join {{ ref('dim_tempo') }} t on t.data = ctl.f_data(p.competen, 'YYYYMM')
left join {{ ref('dim_estabelecimento') }} est on est.cod_cnes = p.cnes
left join {{ ref('dim_ocupacao') }} o on o.cod_ocupacao = p.cbo
