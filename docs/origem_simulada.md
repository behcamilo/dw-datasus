# Origem simulada: validação (27 UFs)

Gerado em 2026-11-14 por `09_validar_origem.py`. UFs: AC, AL, AM, AP, BA, CE, DF, ES, GO, MA, MG, MS, MT, PA, PB, PE, PI, PR, RJ, RN, RO, RR, RS, SC, SE, SP, TO.

**Resultado: TODAS as validações passaram.** 61 tabelas por UF (cada uma nas UFs em que o grupo existe); 235 tabelas de domínio.

## 1. Reconciliação com o arquivo original

'Esperado' é recalculado do arquivo original, UF por UF: todas as linhas nas tabelas planas; só as preenchidas nas esparsas e filhas; um por profissional distinto em `profissional`.

| tabela | tipo | UFs | arquivo original | origem | esperado | confere | % do original | UFs com diferença | como |
|---|---|---|---|---|---|---|---|---|---|
| CNES/DC/hemoterapia | plana | 27 | 75,544 | 75,544 | 75,544 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/DC/nefrologia_dialise | plana | 27 | 75,544 | 75,544 | 75,544 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/DC/radioterapia_quimioterapia | plana | 27 | 75,544 | 75,544 | 75,544 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/EF/estab_filantropico | plana | 22 | 16,461 | 16,461 | 16,461 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/EP/equipe | plana | 27 | 2,413,161 | 2,413,161 | 2,413,161 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/EP/populacao_atendida | plana | 27 | 2,413,161 | 2,413,161 | 2,413,161 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/EQ/equipamento | plana | 27 | 20,943,605 | 20,943,605 | 20,943,605 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/GM/gestao_metas | plana | 26 | 16,654 | 16,654 | 16,654 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/HB/habilitacao | plana | 27 | 580,451 | 580,451 | 580,451 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/IN/incentivo | plana | 27 | 223,801 | 223,801 | 223,801 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/LT/leito | plana | 27 | 1,236,264 | 1,236,264 | 1,236,264 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/PF/carga_horaria | plana | 27 | 121,489,381 | 121,489,381 | 121,489,381 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/PF/profissional | plana | 27 | 121,489,381 | 121,489,381 | 121,489,381 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/PF/vinculo | plana | 27 | 121,489,381 | 121,489,381 | 121,489,381 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/RC/regra_contratual | plana | 27 | 305,015 | 305,015 | 305,015 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/SR/servico_especializado | plana | 27 | 19,930,600 | 19,930,600 | 19,930,600 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/ST/atendimento_convenio | filha | 27 | 8,758,692 | 15,896,140 | 15,896,140 | SIM | 181.49 |  | um por item preenchido |
| CNES/ST/comissoes | filha | 27 | 8,758,692 | 2,323,315 | 2,323,315 | SIM | 26.53 |  | um por item preenchido |
| CNES/ST/contratos_alvara | plana | 27 | 8,758,692 | 8,758,692 | 8,758,692 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/ST/gestao_programas | plana | 27 | 8,758,692 | 8,758,692 | 8,758,692 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/ST/gestao_vinculo | plana | 27 | 8,758,692 | 8,758,692 | 8,758,692 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/ST/identificacao | plana | 27 | 8,758,692 | 8,758,692 | 8,758,692 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/ST/instalacoes | filha | 27 | 8,758,692 | 25,953,843 | 25,953,843 | SIM | 296.32 |  | um por item preenchido |
| CNES/ST/leitos_resumo | plana | 27 | 8,758,692 | 8,758,692 | 8,758,692 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/ST/regionalizacao | plana | 27 | 8,758,692 | 8,758,692 | 8,758,692 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/ST/residuos | plana | 27 | 8,758,692 | 8,758,692 | 8,758,692 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| CNES/ST/servicos_apoio | filha | 27 | 8,758,692 | 13,945,563 | 13,945,563 | SIM | 159.22 |  | um por item preenchido |
| SIH/RD/diagnostico | filha | 27 | 24,149,919 | 30,766,751 | 30,766,751 | SIM | 127.4 |  | um por diagnóstico preenchido |
| SIH/RD/estabelecimento | plana | 27 | 24,149,919 | 24,149,919 | 24,149,919 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIH/RD/gestacao | esparsa | 27 | 24,149,919 | 3,015,702 | 3,015,702 | SIM | 12.49 |  | linhas com algum conteúdo (sem contar valor padrão) |
| SIH/RD/gestor_auditoria | esparsa | 27 | 24,149,919 | 5,573,286 | 5,573,286 | SIM | 23.08 |  | linhas com algum conteúdo (sem contar valor padrão) |
| SIH/RD/internacao | plana | 27 | 24,149,919 | 24,149,919 | 24,149,919 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIH/RD/paciente | plana | 27 | 24,149,919 | 24,149,919 | 24,149,919 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIH/RD/procedimento_financiamento | plana | 27 | 24,149,919 | 24,149,919 | 24,149,919 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIH/RD/uti | esparsa | 27 | 24,149,919 | 2,378,664 | 2,378,664 | SIM | 9.85 |  | linhas com algum conteúdo (sem contar valor padrão) |
| SIH/RD/valores | plana | 27 | 24,149,919 | 24,149,919 | 24,149,919 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIH/RJ/diagnostico | filha | 27 | 1,680,709 | 1,699,246 | 1,699,246 | SIM | 101.1 |  | um por diagnóstico preenchido |
| SIH/RJ/estabelecimento | plana | 27 | 1,680,709 | 1,680,709 | 1,680,709 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIH/RJ/gestacao | esparsa | 25 | 1,680,709 | 162,487 | 162,487 | SIM | 9.67 |  | linhas com algum conteúdo (sem contar valor padrão) |
| SIH/RJ/gestor_auditoria | esparsa | 27 | 1,680,709 | 633,960 | 633,960 | SIM | 37.72 |  | linhas com algum conteúdo (sem contar valor padrão) |
| SIH/RJ/internacao | plana | 27 | 1,680,709 | 1,680,709 | 1,680,709 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIH/RJ/paciente | plana | 27 | 1,680,709 | 1,680,709 | 1,680,709 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIH/RJ/procedimento_financiamento | plana | 27 | 1,680,709 | 1,680,709 | 1,680,709 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIH/RJ/uti | esparsa | 27 | 1,680,709 | 409,886 | 409,886 | SIM | 24.39 |  | linhas com algum conteúdo (sem contar valor padrão) |
| SIH/RJ/valores | plana | 27 | 1,680,709 | 1,680,709 | 1,680,709 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIH/SP/ato_profissional | ato | 27 | 332,927,857 | 332,927,857 | 332,927,857 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIH/SP/profissional | profissional | 27 | 332,927,857 | 413,054 | 413,054 | SIM | 0.12 |  | um por profissional distinto (documento + CBO), sem versões |
| SIM/DO/assistencia | plana | 27 | 3,376,915 | 3,376,915 | 3,376,915 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIM/DO/atestado | plana | 27 | 3,376,915 | 3,376,915 | 3,376,915 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIM/DO/causa_morte | plana | 27 | 3,376,915 | 3,376,915 | 3,376,915 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIM/DO/controle_sistema | plana | 27 | 3,376,915 | 3,376,915 | 3,376,915 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIM/DO/falecido | plana | 27 | 3,376,915 | 3,376,915 | 3,376,915 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIM/DO/gestacao_parto | plana | 27 | 3,376,915 | 3,376,915 | 3,376,915 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIM/DO/investigacao | esparsa | 27 | 3,376,915 | 718,710 | 718,710 | SIM | 21.28 |  | linhas com algum conteúdo (sem contar valor padrão) |
| SIM/DO/mae | plana | 27 | 3,376,915 | 3,376,915 | 3,376,915 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SIM/DO/obito | plana | 27 | 3,376,915 | 3,376,915 | 3,376,915 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SINASC/DN/controle_sistema | plana | 27 | 5,239,023 | 5,239,023 | 5,239,023 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SINASC/DN/declarante | plana | 27 | 5,239,023 | 5,239,023 | 5,239,023 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SINASC/DN/gestacao_parto | plana | 27 | 5,239,023 | 5,239,023 | 5,239,023 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SINASC/DN/nascimento | plana | 27 | 5,239,023 | 5,239,023 | 5,239,023 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |
| SINASC/DN/pais | plana | 27 | 5,239,023 | 5,239,023 | 5,239,023 | SIM | 100.0 |  | todas as linhas do arquivo (1:1) |

## 2. Chave única em cada tabela

A chave é conferida junto com a UF.

| tabela | chave (por UF) | linhas | repetidas | única |
|---|---|---|---|---|
| CNES/DC/hemoterapia | CNES,COMPETEN | 75,544 | 0 | SIM |
| CNES/DC/nefrologia_dialise | CNES,COMPETEN | 75,544 | 0 | SIM |
| CNES/DC/radioterapia_quimioterapia | CNES,COMPETEN | 75,544 | 0 | SIM |
| CNES/EF/estab_filantropico | CNES,COMPETEN,SGRUPHAB | 16,461 | 0 | SIM |
| CNES/EP/equipe | CNES,COMPETEN,IDEQUIPE | 2,413,161 | 0 | SIM |
| CNES/EP/populacao_atendida | CNES,COMPETEN,IDEQUIPE | 2,413,161 | 0 | SIM |
| CNES/EQ/equipamento | id_origem | 20,943,605 | 0 | SIM |
| CNES/GM/gestao_metas | CNES,COMPETEN,SGRUPHAB | 16,654 | 0 | SIM |
| CNES/HB/habilitacao | id_origem | 580,451 | 0 | SIM |
| CNES/IN/incentivo | CNES,COMPETEN,SGRUPHAB | 223,801 | 0 | SIM |
| CNES/LT/leito | CNES,COMPETEN,TP_LEITO,CODLEITO | 1,236,264 | 0 | SIM |
| CNES/PF/carga_horaria | id_origem | 121,489,381 | 0 | SIM |
| CNES/PF/profissional | id_origem | 121,489,381 | 0 | SIM |
| CNES/PF/vinculo | id_origem | 121,489,381 | 0 | SIM |
| CNES/RC/regra_contratual | id_origem | 305,015 | 0 | SIM |
| CNES/SR/servico_especializado | id_origem | 19,930,600 | 0 | SIM |
| CNES/ST/atendimento_convenio | CNES,COMPETEN,item | 15,896,140 | 0 | SIM |
| CNES/ST/comissoes | CNES,COMPETEN,item | 2,323,315 | 0 | SIM |
| CNES/ST/contratos_alvara | CNES,COMPETEN | 8,758,692 | 0 | SIM |
| CNES/ST/gestao_programas | CNES,COMPETEN | 8,758,692 | 0 | SIM |
| CNES/ST/gestao_vinculo | CNES,COMPETEN | 8,758,692 | 0 | SIM |
| CNES/ST/identificacao | CNES,COMPETEN | 8,758,692 | 0 | SIM |
| CNES/ST/instalacoes | CNES,COMPETEN,item | 25,953,843 | 0 | SIM |
| CNES/ST/leitos_resumo | CNES,COMPETEN | 8,758,692 | 0 | SIM |
| CNES/ST/regionalizacao | CNES,COMPETEN | 8,758,692 | 0 | SIM |
| CNES/ST/residuos | CNES,COMPETEN | 8,758,692 | 0 | SIM |
| CNES/ST/servicos_apoio | CNES,COMPETEN,item | 13,945,563 | 0 | SIM |
| SIH/RD/diagnostico | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT,ordem,tipo | 30,766,751 | 0 | SIM |
| SIH/RD/estabelecimento | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 24,149,919 | 0 | SIM |
| SIH/RD/gestacao | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 3,015,702 | 0 | SIM |
| SIH/RD/gestor_auditoria | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 5,573,286 | 0 | SIM |
| SIH/RD/internacao | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 24,149,919 | 0 | SIM |
| SIH/RD/paciente | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 24,149,919 | 0 | SIM |
| SIH/RD/procedimento_financiamento | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 24,149,919 | 0 | SIM |
| SIH/RD/uti | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 2,378,664 | 0 | SIM |
| SIH/RD/valores | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 24,149,919 | 0 | SIM |
| SIH/RJ/diagnostico | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT,ordem,tipo | 1,699,246 | 0 | SIM |
| SIH/RJ/estabelecimento | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 1,680,709 | 0 | SIM |
| SIH/RJ/gestacao | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 162,487 | 0 | SIM |
| SIH/RJ/gestor_auditoria | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 633,960 | 0 | SIM |
| SIH/RJ/internacao | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 1,680,709 | 0 | SIM |
| SIH/RJ/paciente | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 1,680,709 | 0 | SIM |
| SIH/RJ/procedimento_financiamento | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 1,680,709 | 0 | SIM |
| SIH/RJ/uti | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 409,886 | 0 | SIM |
| SIH/RJ/valores | N_AIH,SEQUENCIA,ANO_CMPT,MES_CMPT | 1,680,709 | 0 | SIM |
| SIH/SP/ato_profissional | id_origem | 332,927,857 | 0 | SIM |
| SIH/SP/profissional | SP_PF_DOC,SP_PF_CBO | 413,054 | 0 | SIM |
| SIM/DO/assistencia | ANO,CONTADOR | 3,376,915 | 0 | SIM |
| SIM/DO/atestado | ANO,CONTADOR | 3,376,915 | 0 | SIM |
| SIM/DO/causa_morte | ANO,CONTADOR | 3,376,915 | 0 | SIM |
| SIM/DO/controle_sistema | ANO,CONTADOR | 3,376,915 | 0 | SIM |
| SIM/DO/falecido | ANO,CONTADOR | 3,376,915 | 0 | SIM |
| SIM/DO/gestacao_parto | ANO,CONTADOR | 3,376,915 | 0 | SIM |
| SIM/DO/investigacao | ANO,CONTADOR | 718,710 | 0 | SIM |
| SIM/DO/mae | ANO,CONTADOR | 3,376,915 | 0 | SIM |
| SIM/DO/obito | ANO,CONTADOR | 3,376,915 | 0 | SIM |
| SINASC/DN/controle_sistema | ANO,CONTADOR | 5,239,023 | 0 | SIM |
| SINASC/DN/declarante | ANO,CONTADOR | 5,239,023 | 0 | SIM |
| SINASC/DN/gestacao_parto | ANO,CONTADOR | 5,239,023 | 0 | SIM |
| SINASC/DN/nascimento | ANO,CONTADOR | 5,239,023 | 0 | SIM |
| SINASC/DN/pais | ANO,CONTADOR | 5,239,023 | 0 | SIM |

## 3. Registro pai

| filha | pai | ligação (além da UF) | linhas sem pai |
|---|---|---|---|
| CNES/DC/hemoterapia | CNES/DC/nefrologia_dialise | CNES, COMPETEN | 0 |
| CNES/DC/radioterapia_quimioterapia | CNES/DC/nefrologia_dialise | CNES, COMPETEN | 0 |
| CNES/EP/populacao_atendida | CNES/EP/equipe | CNES, COMPETEN, IDEQUIPE | 0 |
| CNES/PF/carga_horaria | CNES/PF/profissional | id_origem | 0 |
| CNES/PF/vinculo | CNES/PF/profissional | id_origem | 0 |
| CNES/ST/atendimento_convenio | CNES/ST/identificacao | CNES, COMPETEN | 0 |
| CNES/ST/comissoes | CNES/ST/identificacao | CNES, COMPETEN | 0 |
| CNES/ST/contratos_alvara | CNES/ST/identificacao | CNES, COMPETEN | 0 |
| CNES/ST/gestao_programas | CNES/ST/identificacao | CNES, COMPETEN | 0 |
| CNES/ST/gestao_vinculo | CNES/ST/identificacao | CNES, COMPETEN | 0 |
| CNES/ST/instalacoes | CNES/ST/identificacao | CNES, COMPETEN | 0 |
| CNES/ST/leitos_resumo | CNES/ST/identificacao | CNES, COMPETEN | 0 |
| CNES/ST/regionalizacao | CNES/ST/identificacao | CNES, COMPETEN | 0 |
| CNES/ST/residuos | CNES/ST/identificacao | CNES, COMPETEN | 0 |
| CNES/ST/servicos_apoio | CNES/ST/identificacao | CNES, COMPETEN | 0 |
| SIH/RD/diagnostico | SIH/RD/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RD/estabelecimento | SIH/RD/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RD/gestacao | SIH/RD/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RD/gestor_auditoria | SIH/RD/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RD/paciente | SIH/RD/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RD/procedimento_financiamento | SIH/RD/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RD/uti | SIH/RD/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RD/valores | SIH/RD/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RJ/diagnostico | SIH/RJ/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RJ/estabelecimento | SIH/RJ/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RJ/gestacao | SIH/RJ/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RJ/gestor_auditoria | SIH/RJ/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RJ/paciente | SIH/RJ/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RJ/procedimento_financiamento | SIH/RJ/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RJ/uti | SIH/RJ/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/RJ/valores | SIH/RJ/internacao | N_AIH, SEQUENCIA, ANO_CMPT, MES_CMPT | 0 |
| SIH/SP/ato_profissional | SIH/RD/internacao | SP_NAIH, SEQUENCIA, SP_AA, SP_MM | 0 |
| SIM/DO/assistencia | SIM/DO/obito | ANO, CONTADOR | 0 |
| SIM/DO/atestado | SIM/DO/obito | ANO, CONTADOR | 0 |
| SIM/DO/causa_morte | SIM/DO/obito | ANO, CONTADOR | 0 |
| SIM/DO/controle_sistema | SIM/DO/obito | ANO, CONTADOR | 0 |
| SIM/DO/falecido | SIM/DO/obito | ANO, CONTADOR | 0 |
| SIM/DO/gestacao_parto | SIM/DO/obito | ANO, CONTADOR | 0 |
| SIM/DO/investigacao | SIM/DO/obito | ANO, CONTADOR | 0 |
| SIM/DO/mae | SIM/DO/obito | ANO, CONTADOR | 0 |
| SINASC/DN/controle_sistema | SINASC/DN/nascimento | ANO, CONTADOR | 0 |
| SINASC/DN/declarante | SINASC/DN/nascimento | ANO, CONTADOR | 0 |
| SINASC/DN/gestacao_parto | SINASC/DN/nascimento | ANO, CONTADOR | 0 |
| SINASC/DN/pais | SINASC/DN/nascimento | ANO, CONTADOR | 0 |
| SIH/SP/ato_profissional (profissional não nulo) | SIH/SP/profissional | SP_PF_DOC, SP_PF_CBO | 0 |
| profissional: DT_TRANSACAO = a do 1º ato em que aparece | SIH/SP/ato_profissional | SP_PF_DOC, SP_PF_CBO | 0 |

## 4. Distribuição do DT_TRANSACAO (tabela principal de cada grupo, todas as UFs juntas)

Linhas por dia. No SIH o volume é igual em todos os dias úteis de um mês; no SIM e no SINASC segue a data do evento.

| grupo | UFs | linhas | dias | mín/dia | mediana/dia | máx/dia | linhas por UF (mín–máx) | primeira | última | até 31/12/2021 | em 2022 | em 2023 | % em dia útil |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CNES-DC | 27 | 75,544 | 24 | 2734 | 3162 | 3239 | 144 – 17,670 | 2021-02-05 | 2023-01-06 | 34,295 (45.4%) | 38,010 (50.3%) | 3,239 (4.3%) | 100.0 |
| CNES-EF | 22 | 16,461 | 24 | 684 | 685 | 688 | 1 – 3,600 | 2021-02-05 | 2023-01-06 | 7,557 (45.9%) | 8,219 (49.9%) | 685 (4.2%) | 100.0 |
| CNES-EP | 27 | 2,413,161 | 24 | 95749 | 101138 | 104547 | 7,099 – 343,169 | 2021-02-05 | 2023-01-06 | 1,077,246 (44.6%) | 1,231,368 (51.0%) | 104,547 (4.3%) | 100.0 |
| CNES-EQ | 27 | 20,943,605 | 24 | 811010 | 873839 | 926832 | 55,075 – 4,849,421 | 2021-02-05 | 2023-01-06 | 9,256,031 (44.2%) | 10,760,742 (51.4%) | 926,832 (4.4%) | 100.0 |
| CNES-GM | 26 | 16,654 | 24 | 632 | 670 | 912 | 48 – 2,088 | 2021-02-05 | 2023-01-06 | 7,894 (47.4%) | 8,079 (48.5%) | 681 (4.1%) | 100.0 |
| CNES-HB | 27 | 580,451 | 24 | 23534 | 24169 | 24785 | 1,145 – 124,634 | 2021-02-05 | 2023-01-06 | 268,138 (46.2%) | 287,946 (49.6%) | 24,367 (4.2%) | 100.0 |
| CNES-IN | 27 | 223,801 | 24 | 7278 | 9015 | 11738 | 359 – 39,125 | 2021-02-05 | 2023-01-06 | 89,705 (40.1%) | 122,358 (54.7%) | 11,738 (5.2%) | 100.0 |
| CNES-LT | 27 | 1,236,264 | 24 | 50310 | 51854 | 52341 | 2,796 – 204,159 | 2021-02-05 | 2023-01-06 | 570,565 (46.2%) | 615,129 (49.8%) | 50,570 (4.1%) | 100.0 |
| CNES-PF | 27 | 121,489,381 | 24 | 4619533 | 5073195 | 5347351 | 376,658 – 29,058,140 | 2021-02-05 | 2023-01-06 | 53,725,137 (44.2%) | 62,416,893 (51.4%) | 5,347,351 (4.4%) | 100.0 |
| CNES-RC | 27 | 305,015 | 24 | 12499 | 12727 | 12893 | 729 – 54,379 | 2021-02-05 | 2023-01-06 | 139,118 (45.6%) | 153,004 (50.2%) | 12,893 (4.2%) | 100.0 |
| CNES-SR | 27 | 19,930,600 | 24 | 788310 | 830310 | 871690 | 42,198 – 3,329,779 | 2021-02-05 | 2023-01-06 | 8,879,511 (44.6%) | 10,179,399 (51.1%) | 871,690 (4.4%) | 100.0 |
| CNES-ST | 27 | 8,758,692 | 24 | 334702 | 365835 | 388398 | 18,927 – 1,921,690 | 2021-02-05 | 2023-01-06 | 3,856,829 (44.0%) | 4,513,465 (51.5%) | 388,398 (4.4%) | 100.0 |
| SIH-RD | 27 | 24,149,919 | 510 | 39423 | 47470 | 54692 | 81,179 – 4,912,909 | 2021-02-01 | 2023-01-31 | 10,642,048 (44.1%) | 12,450,911 (51.6%) | 1,056,960 (4.4%) | 100.0 |
| SIH-RJ | 27 | 1,680,709 | 510 | 2436 | 3069 | 5146 | 166 – 321,680 | 2021-02-01 | 2023-01-31 | 719,489 (42.8%) | 899,136 (53.5%) | 62,084 (3.7%) | 100.0 |
| SIH-SP | 27 | 332,927,857 | 510 | 410372 | 652212 | 855004 | 1,035,455 – 83,141,931 | 2021-02-01 | 2023-01-31 | 150,818,578 (45.3%) | 167,740,829 (50.4%) | 14,368,450 (4.3%) | 100.0 |
| SIM-DO | 27 | 3,376,915 | 730 | 3509 | 4324 | 7662 | 7,552 – 785,672 | 2021-01-31 | 2023-01-30 | 1,705,776 (50.5%) | 1,553,719 (46.0%) | 117,420 (3.5%) | 70.0 |
| SINASC-DN | 27 | 5,239,023 | 730 | 4377 | 7486 | 8789 | 26,992 – 1,037,759 | 2021-01-31 | 2023-01-30 | 2,467,339 (47.1%) | 2,561,354 (48.9%) | 210,330 (4.0%) | 68.2 |

## 5. Dados pessoais

Colunas com hash e quantos valores não são hash. Colunas que não podem estar na origem (NOMEPROF, CPF_AUT) encontradas: **nenhuma**.

| tabela | coluna | linhas | NULL (vazio/sentinela) | valores que NÃO são hash |
|---|---|---|---|---|
| CNES/PF/profissional | CPF_PROF | 121,489,381 | 0 (0.0%) | 0 |
| CNES/PF/profissional | CNS_PROF | 121,489,381 | 7,381 (0.0%) | 0 |
| CNES/PF/profissional | REGISTRO | 121,489,381 | 34,477,198 (28.4%) | 0 |
| CNES/DC/hemoterapia | CNS_HMTR | 75,544 | 54,774 (72.5%) | 0 |
| CNES/DC/hemoterapia | CNS_HMTL | 75,544 | 60,381 (79.9%) | 0 |
| CNES/DC/hemoterapia | CNS_CRES | 75,544 | 55,278 (73.2%) | 0 |
| CNES/DC/hemoterapia | CNS_RTEC | 75,544 | 62,451 (82.7%) | 0 |
| CNES/DC/nefrologia_dialise | CNS_NEFR | 75,544 | 50,954 (67.4%) | 0 |
| CNES/DC/radioterapia_quimioterapia | CNS_ADM | 75,544 | 57,505 (76.1%) | 0 |
| CNES/DC/radioterapia_quimioterapia | CNS_OPED | 75,544 | 70,505 (93.3%) | 0 |
| CNES/DC/radioterapia_quimioterapia | CNS_CONC | 75,544 | 64,388 (85.2%) | 0 |
| CNES/DC/radioterapia_quimioterapia | CNS_OCLIN | 75,544 | 59,356 (78.6%) | 0 |
| CNES/DC/radioterapia_quimioterapia | CNS_MRAD | 75,544 | 68,565 (90.8%) | 0 |
| CNES/DC/radioterapia_quimioterapia | CNS_FNUC | 75,544 | 68,810 (91.1%) | 0 |
| SIH/RD/gestor_auditoria | GESTOR_CPF | 5,573,286 | 0 (0.0%) | 0 |
| SIH/SP/ato_profissional | SP_PF_DOC | 332,927,857 | 228,171,233 (68.5%) | 0 |
| SIH/SP/profissional | SP_PF_DOC | 413,054 | 0 (0.0%) | 0 |
| SIH/RJ/gestor_auditoria | GESTOR_CPF | 633,960 | 0 (0.0%) | 0 |
| CNES/ST/identificacao | CPF_CNPJ (só PF_PJ = 1) | 2,614,546 de pessoa física | 0 de pessoa jurídica com hash | 0 |
| SIH/SP/ato_profissional | SP_CPFCGC (só se parece CPF) | 332,927,857 | 0 com hash; o resto é CNES/CNPJ e fica como veio | 0 |

## 6. Tamanho em disco

| sistema | arquivos | tamanho |
|---|---|---|
| CNES | 17,317 | 11.5 GB |
| DOMINIO | 1,111 | 54 MB |
| SIH | 12,729 | 5.9 GB |
| SIM | 6,075 | 239 MB |
| SINASC | 3,375 | 203 MB |

Total da origem: **17.9 GB**.

## 7. Determinismo

As UFs RR, AC foram geradas de novo numa pasta de teste e comparadas arquivo a arquivo (sha256): **3950 arquivos comparados, 0 diferentes, 0 presentes só de um lado.**

