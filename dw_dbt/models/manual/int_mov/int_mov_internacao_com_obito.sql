{{ config(
    materialized='table', schema='int_mov', tags=['nacional', 'int_mov'],
    meta={'sistema_origem': 'DW', 'grupo': 'INT_MOV', 'assunto': 'internacao_com_obito', 'uf': 'BR', 'tipo_carga': 'FULL',
          'chave_negocio': 'uf,n_aih,sequencia,ano_cmpt,mes_cmpt',
          'descricao': 'Óbito hospitalar: internações que terminaram em óbito, com causa (capítulo da CID), procedimento e perfil do estabelecimento.'}
) }}
select uf, n_aih, sequencia, ano_cmpt, mes_cmpt, dt_internacao, dt_saida, dias_perm, sexo, idade, munic_res,
       cid_principal, capitulo_cid, proc_rea, grupo_procedimento, complexidade, cnes, perfil_estabelecimento, tipo_unidade,
       (dt_saida - dt_internacao) <= 1 as obito_em_ate_24h, {{ dt_carga() }} as dt_carga
from {{ ref('int_mov_nac_internacao_classificada') }}
where morte = '1'
