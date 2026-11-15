-- Um schema por camada do DW (ver docs/desenho_dw.md).
CREATE SCHEMA IF NOT EXISTS ctl;       -- controle (tabelas, linhagem, log de carga)
CREATE SCHEMA IF NOT EXISTS stg_cad;   -- stage de cadastro (foto atual da origem)
CREATE SCHEMA IF NOT EXISTS stg_mov;   -- stage de movimento (delta do dia)
CREATE SCHEMA IF NOT EXISTS int_cad;   -- cadastro tratado
CREATE SCHEMA IF NOT EXISTS int_mov;   -- movimento tratado
CREATE SCHEMA IF NOT EXISTS dim;       -- dimensões
CREATE SCHEMA IF NOT EXISTS fct;       -- fatos
CREATE SCHEMA IF NOT EXISTS agg;       -- agregados
