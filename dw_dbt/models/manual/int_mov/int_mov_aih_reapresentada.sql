{{ config(
    materialized='table', schema='int_mov', tags=['nacional', 'int_mov'],
    meta={'sistema_origem': 'DW', 'grupo': 'INT_MOV', 'assunto': 'aih_reapresentada', 'uf': 'BR', 'tipo_carga': 'FULL',
          'chave_negocio': 'uf,n_aih,ano_cmpt_rejeicao,mes_cmpt_rejeicao',
          'descricao': 'AIH rejeitada (SIH-RJ) que foi reapresentada e aprovada (SIH-RD): competência da rejeição, da aprovação e meses entre as duas.'}
) }}
-- Uma AIH pode ser rejeitada mais de uma vez; a aprovação considerada é a primeira depois da rejeição.
select distinct on (r.uf, r.n_aih, r.ano_cmpt, r.mes_cmpt)
       r.uf, r.n_aih, r.ano_cmpt as ano_cmpt_rejeicao, r.mes_cmpt as mes_cmpt_rejeicao, r.st_mot_blo as motivo_rejeicao,
       a.ano_cmpt as ano_cmpt_aprovacao, a.mes_cmpt as mes_cmpt_aprovacao,
       (a.ano_cmpt::int * 12 + a.mes_cmpt::int) - (r.ano_cmpt::int * 12 + r.mes_cmpt::int) as meses_ate_aprovacao,
       r.proc_rea, r.cnes, r.val_tot as valor_rejeitado, a.val_tot as valor_aprovado, {{ dt_carga() }} as dt_carga
from {{ ref('int_mov_nac_aih_rejeitada_classificada') }} r
join {{ ref('int_mov_nac_internacao_classificada') }} a
  on a.uf = r.uf and a.n_aih = r.n_aih and (a.ano_cmpt || a.mes_cmpt) >= (r.ano_cmpt || r.mes_cmpt)
order by r.uf, r.n_aih, r.ano_cmpt, r.mes_cmpt, a.ano_cmpt, a.mes_cmpt
