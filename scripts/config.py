"""Configurações do projeto. Todos os scripts importam daqui."""

import os
from datetime import date
from pathlib import Path

# Pastas
# Os caminhos dos scripts são relativos à raiz do projeto; por isso a raiz vira o diretório de trabalho.
RAIZ = Path(__file__).resolve().parent.parent
os.chdir(RAIZ)
PASTA_RAW = RAIZ / "dados" / "raw"
ARQUIVO_MANIFESTO = RAIZ / "dados" / "manifesto.csv"
ARQUIVO_INVENTARIO = RAIZ / "docs" / "inventario.csv"
PASTA_EXPLORACAO = RAIZ / "docs" / "exploracao"

# Recorte
SISTEMAS_E_GRUPOS = {
    "SIH": ["RD", "SP", "RJ"],  # RD = internações, SP = atos profissionais, RJ = AIH rejeitadas
    "CNES": ["ST", "LT", "PF", "EQ", "SR", "HB", "EP", "DC", "RC", "IN", "GM", "EE", "EF"],
    "SIM": ["DO"],
    "SINASC": ["DN"],
}
ANOS = [2021, 2022]  # 2021 = carga inicial; 2022 = carga diária simulada
# Sem 'BR' (consolidado do país) e 'EX' (exterior), que existem no FTP do SIM e do SINASC.
UFS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
       "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]
AMOSTRA = {"ufs": ["SP", "PR", "RR"], "ano": 2022, "mes": 1}  # 02_baixar.py --amostra

# CNES vira stage de cadastro (stg_cad_); os demais, stage de movimento (stg_mov_).
TIPO_DO_SISTEMA = {"CNES": "cadastro", "SIH": "movimento", "SIM": "movimento", "SINASC": "movimento"}

# Domínios
# Arquivos baixados pelo 03_baixar_dominio.py. A CBO vem junto com a SIGTAP (o site do MTE exige captcha).
_FTP = "ftp://ftp.datasus.gov.br/dissemin/publicos"
DOMINIOS = [
    {"fonte": "sigtap", "periodo": "2022-12", "descricao": "Tabela Unificada SIGTAP, competência 12/2022 (procedimentos e tabelas relacionadas)",
     "url": "ftp://ftp2.datasus.gov.br/public/sistemas/tup/downloads/TabelaUnificada_202212_v2212051647.zip"},
    {"fonte": "cid10", "periodo": "", "descricao": "CID-10 em CSV: capítulos, grupos, categorias e subcategorias",
     "url": "http://www2.datasus.gov.br/cid10/V2008/downloads/CID10CSV.zip"},
    {"fonte": "cid10", "periodo": "", "descricao": "CID-10 no formato TabWin (DBF)", "url": f"{_FTP}/SIM/CID10/TABELAS/CID10.DBF"},
    {"fonte": "cid10", "periodo": "", "descricao": "Capítulos da CID-10 (DBF)", "url": f"{_FTP}/SIM/CID10/TABELAS/CIDCAP10.DBF"},
    {"fonte": "ibge", "periodo": "", "descricao": "Municípios (API de localidades do IBGE, código de 7 dígitos)",
     "url": "https://servicodados.ibge.gov.br/api/v1/localidades/municipios", "arquivo": "municipios_ibge.json"},
    {"fonte": "ibge", "periodo": "2021", "descricao": "População residente por município, sexo e idade (SVS), 2021", "url": f"{_FTP}/IBGE/POPSVS/POPSBR21.zip"},
    {"fonte": "ibge", "periodo": "2022", "descricao": "População residente por município, sexo e idade (SVS), 2022", "url": f"{_FTP}/IBGE/POPSVS/POPSBR22.zip"},
    {"fonte": "ibge", "periodo": "2021", "descricao": "População total por município (TCU), 2021", "url": f"{_FTP}/IBGE/POPTCU/POPTBR21.zip"},
    {"fonte": "ibge", "periodo": "2022", "descricao": "População total por município (TCU), 2022", "url": f"{_FTP}/IBGE/POPTCU/POPTBR22.zip"},
    {"fonte": "ibge", "periodo": "", "descricao": "Tabelas auxiliares TabWin da população", "url": f"{_FTP}/IBGE/Auxiliar/TAB_POP.zip"},
    {"fonte": "ibge", "periodo": "", "descricao": "Nota técnica da população residente 2000-2024", "url": f"{_FTP}/IBGE/doc/NT-POPULACAO-RESIDENTE-2000-2024.pdf"},
    {"fonte": "sih", "periodo": "", "descricao": "Tabelas auxiliares TabWin do SIH (.CNV, .DBF)", "url": f"{_FTP}/SIHSUS/200801_/Auxiliar/TAB_SIH.zip"},
    {"fonte": "sih", "periodo": "", "descricao": "Layout do SIH (instrução técnica)", "url": f"{_FTP}/SIHSUS/200801_/Doc/IT_SIHSUS_1603.pdf"},
    {"fonte": "cnes", "periodo": "", "descricao": "Tabelas auxiliares TabWin do CNES (.CNV, .DBF)", "url": f"{_FTP}/CNES/200508_/Auxiliar/TAB_CNES.zip"},
    {"fonte": "cnes", "periodo": "", "descricao": "Layout do CNES (instrução técnica)", "url": f"{_FTP}/CNES/200508_/Doc/IT_CNES_1706.pdf"},
    {"fonte": "sim", "periodo": "", "descricao": "Tabelas auxiliares TabWin do SIM", "url": f"{_FTP}/SIM/CID10/TAB/OBITOS_CID10_TAB.zip"},
    {"fonte": "sim", "periodo": "", "descricao": "Conversões TabWin da CID-10 (v2019)", "url": f"{_FTP}/SIM/CID10/TAB/CNVS_CID10_v2019.rar"},
    {"fonte": "sim", "periodo": "", "descricao": "Layout do SIM (estrutura 2025)", "url": f"{_FTP}/SIM/CID10/DOCS/Estrutura_do_SIM_2025.pdf"},
    {"fonte": "sim", "periodo": "", "descricao": "Layout do SIM (estrutura para CD)", "url": f"{_FTP}/SIM/CID10/DOCS/Estrutura_SIM_para_CD.pdf"},
    {"fonte": "sinasc", "periodo": "", "descricao": "Tabelas auxiliares TabWin do SINASC", "url": f"{_FTP}/SINASC/NOV/TAB/NASC_NOV_TAB.zip"},
    {"fonte": "sinasc", "periodo": "", "descricao": "Layout do SINASC (estrutura para CD)", "url": f"{_FTP}/SINASC/NOV/DOCS/Estrutura_SINASC_para_CD.pdf"},
]
SIGTAP_COMPETENCIAS = [f"{ano}{mes:02d}" for ano in ANOS for mes in range(1, 13)]  # uma SIGTAP por mês
SIGTAP_FTP = ("ftp2.datasus.gov.br", "/public/sistemas/tup/downloads")

# Domínios da origem (08_gerar_origem_dominios.py): uma tabela por arquivo.
DOMINIOS_DE_DATA = {"ANO", "ANOMES", "ANO_MES", "MESANO0020", "COMPETEN", "COMPT", "MESES", "HORAOBITO"}  # conversões de data: ficam fora
SIGTAP_TABELAS_FORA = {"tb_descricao", "tb_descricao_detalhe"}  # só textos longos
CID10_ARQUIVOS = ["CID-10-CAPITULOS.CSV", "CID-10-GRUPOS.CSV", "CID-10-CATEGORIAS.CSV", "CID-10-SUBCATEGORIAS.CSV",
                  "CID-O-GRUPOS.CSV", "CID-O-CATEGORIAS.CSV"]
# Agrupamentos de municípios do TabWin: cada linha liga um município a um grupo.
TERRITORIO_TAB_POP = ["br_regsaud.cnv", "br_macsaud.cnv", "br_regmetr.cnv", "br_divadm.cnv", "br_amazlegal.cnv", "br_semiarido.cnv",
                      "br_frontfaixa.cnv", "br_pndr.cnv", "br_extrpobrez.cnv", "br_terrcid.cnv", "br_capital.cnv"]
# O TabWin cita o cadastro geral de cada UF; o arquivo nacional tem todos os estabelecimentos.
DOMINIO_PREFERIDO = {"cnes": ("TAB_CNES.zip", "DBF/CADGERBR.dbf", "dbf")}
# Chaves que fogem da regra de dw.chave_do_dominio.
CHAVE_DOMINIO_EXCECAO = {
    "cid10_grupos": ["catinic", "catfim"],                                            # grupo = intervalo de categorias
    "sigtap_sia_sih": ["co_procedimento_sia_sih", "tp_procedimento", "competencia"],  # mesmo código no SIA e no SIH
    "cnes_populac": ["chave", "ds_pop"],                                              # mesmo código com duas descrições
}
# Sem chave natural (código repetido com descrições diferentes): a chave é a linha inteira.
DOMINIOS_SEM_CHAVE = {"cid10_cid_o_grupos", "cnes_atpres03", "cnes_atpres04", "cnes_atpres05", "sigtap_rl_procedimento_renases", "sim_cnes26"}

# 04_dominios_usados.py: padrões de nome das colunas que ligam a cadastros.
PADROES_LIGACAO = {
    "CNES (estabelecimento)": r"CNES",
    "Município": r"MUN|CODUFMUN",
    "CID (diagnóstico/causa)": r"DIAG|CID|CAUSA",
    "Procedimento": r"PROC",
}

# Origem simulada
PASTA_ORIGEM = RAIZ / "dados" / "origem"
UFS_PADRAO_DA_ORIGEM = ["RR"]           # sem --todas, os scripts 05 a 07 geram só RR
DATA_CARGA_INICIAL = date(2021, 12, 31)  # DT_TRANSACAO dos domínios fixos
# Limite de memória do DuckDB; acima dele, grava temporários em disco. Grupos grandes (SIH-SP, CNES-PF): MEMORIA_DUCKDB=10GB.
MEMORIA_DUCKDB = os.environ.get("MEMORIA_DUCKDB", "2GB")
THREADS_DUCKDB = 4
PASTA_TEMP_DUCKDB = RAIZ / "dados" / "raw" / "_tmp_duckdb"

# Assuntos do mapa que não viram tabela: atributo do estabelecimento repetido em outro grupo do CNES, coluna vazia, coluna retirada.
ASSUNTOS_FORA = ["estabelecimento_replicado", "descartada", "fora"]
# Tabelas esparsas: só as linhas com algum dado preenchido.
TABELAS_ESPARSAS = {("SIH", "RD"): ["uti", "gestacao", "gestor_auditoria"], ("SIM", "DO"): ["investigacao"]}
# Colunas com valor padrão (não contam como "dado preenchido"): GESTRISCO vale '1' em quase todas as linhas.
COLUNAS_VALOR_PADRAO = {("SIH", "RD"): ["GESTRISCO"]}
# Filhas do CNES-ST: uma linha por item preenchido.
TABELAS_FILHAS_POR_ITEM = {("CNES", "ST"): ["instalacoes", "servicos_apoio", "comissoes", "atendimento_convenio"]}

# Dados pessoais. Nome de pessoa e coluna vazia ficam fora; documentos recebem hash sha256 com o sal de config_local.py
# (vazio ou sentinela vira NULL). CNPJ fica aberto.
COLUNAS_FORA = {("CNES", "PF"): ["NOMEPROF"], ("SIH", "RD"): ["CPF_AUT"]}
_CNS_DO_DC = ["CNS_NEFR", "CNS_ADM", "CNS_OPED", "CNS_CONC", "CNS_OCLIN", "CNS_MRAD", "CNS_FNUC", "CNS_HMTR", "CNS_HMTL", "CNS_CRES", "CNS_RTEC"]
COLUNAS_COM_HASH = {
    ("CNES", "PF"): ["CPF_PROF", "CNS_PROF", "REGISTRO"],
    ("CNES", "DC"): _CNS_DO_DC,
    ("SIH", "RD"): ["GESTOR_CPF"],
    ("SIH", "SP"): ["SP_PF_DOC"],
}
# Colunas que misturam CPF e CNPJ: hash só quando é CPF (no CNES-ST pelo indicador PF_PJ; no SIH-SP pelo formato do CPF).
COLUNAS_COM_HASH_SE_CPF = {("CNES", "ST"): ("CPF_CNPJ", "PF_PJ = '1'"), ("SIH", "SP"): ("SP_CPFCGC", None)}

# Usados para espalhar a DT_TRANSACAO pelos dias úteis.
FERIADOS_NACIONAIS = {
    date(2021, 1, 1), date(2021, 4, 2), date(2021, 4, 21), date(2021, 5, 1), date(2021, 9, 7), date(2021, 10, 12),
    date(2021, 11, 2), date(2021, 11, 15), date(2021, 12, 25),
    date(2022, 1, 1), date(2022, 4, 15), date(2022, 4, 21), date(2022, 5, 1), date(2022, 9, 7), date(2022, 10, 12),
    date(2022, 11, 2), date(2022, 11, 15), date(2022, 12, 25),
    date(2023, 1, 1), date(2023, 4, 7), date(2023, 4, 21), date(2023, 5, 1), date(2023, 9, 7), date(2023, 10, 12),
    date(2023, 11, 2), date(2023, 11, 15), date(2023, 12, 25),
}

# Chave repetida em todas as tabelas do grupo (a UF vem da partição uf=XX).
CHAVE_REPETIDA = {
    ("SIH", "RD"): ["N_AIH", "SEQUENCIA", "ANO_CMPT", "MES_CMPT"],
    ("SIH", "SP"): ["SP_NAIH", "SEQUENCIA", "SP_AA", "SP_MM"],
    ("SIM", "DO"): ["ANO", "CONTADOR"],
    ("SINASC", "DN"): ["ANO", "CONTADOR"],
    **{("CNES", g): ["CNES", "COMPETEN"] for g in SISTEMAS_E_GRUPOS["CNES"]},
}
CHAVE_REPETIDA[("CNES", "EP")] = ["CNES", "COMPETEN", "IDEQUIPE"]

# Grupos sem chave natural: a origem cria id_origem = "<arquivo>:<linha>".
GRUPOS_COM_ID_ORIGEM = {("SIH", "SP"), ("CNES", "PF"), ("CNES", "SR"), ("CNES", "RC"), ("CNES", "EQ"), ("CNES", "HB")}

# Chave de uma linha das tabelas principais de cada grupo.
CHAVE_UNICA = {
    ("SIH", "RD"): ["N_AIH", "SEQUENCIA", "ANO_CMPT", "MES_CMPT"],
    ("SIM", "DO"): ["ANO", "CONTADOR"], ("SINASC", "DN"): ["ANO", "CONTADOR"],
    ("CNES", "ST"): ["CNES", "COMPETEN"], ("CNES", "DC"): ["CNES", "COMPETEN"],
    ("CNES", "LT"): ["CNES", "COMPETEN", "TP_LEITO", "CODLEITO"], ("CNES", "EP"): ["CNES", "COMPETEN", "IDEQUIPE"],
    **{("CNES", g): ["CNES", "COMPETEN", "SGRUPHAB"] for g in ["IN", "GM", "EF", "EE"]},
    **{g: ["id_origem"] for g in GRUPOS_COM_ID_ORIGEM},
}

# Assunto principal de cada grupo: o pai das tabelas esparsas e filhas.
ASSUNTO_PRINCIPAL = {
    ("SIH", "RD"): "internacao", ("SIH", "SP"): "ato_profissional", ("SIM", "DO"): "obito", ("SINASC", "DN"): "nascimento",
    ("CNES", "ST"): "identificacao", ("CNES", "PF"): "profissional", ("CNES", "DC"): "nefrologia_dialise", ("CNES", "EP"): "equipe",
    ("CNES", "EQ"): "equipamento", ("CNES", "HB"): "habilitacao", ("CNES", "LT"): "leito", ("CNES", "SR"): "servico_especializado",
    ("CNES", "RC"): "regra_contratual", ("CNES", "IN"): "incentivo", ("CNES", "GM"): "gestao_metas",
    ("CNES", "EE"): "estab_ensino", ("CNES", "EF"): "estab_filantropico",
}

# O SIH-RJ tem o mesmo layout do SIH-RD: usa as mesmas regras.
for _regras in [TABELAS_ESPARSAS, COLUNAS_VALOR_PADRAO, COLUNAS_FORA, COLUNAS_COM_HASH, CHAVE_REPETIDA, CHAVE_UNICA, ASSUNTO_PRINCIPAL]:
    _regras[("SIH", "RJ")] = _regras[("SIH", "RD")]

# DW
DW_POSTGRES = {"host": "localhost", "port": 5433, "user": "dw", "password": "dw_local", "dbname": "dw"}

# Validação de códigos no movimento: só se confere a coluna em que pelo menos esta fração dos valores existe no cadastro.
TAXA_MINIMA_VALIDACAO = 0.9
COLUNAS_DE_ESTABELECIMENTO = ["cnes", "codestab", "sp_cnes"]  # conferidas no estabelecimento consolidado da mesma UF
# Domínio da coluna -> (cadastro consolidado onde o código é conferido, domínios que ele reúne). O CID aceita categoria e subcategoria.
CONSOLIDADOS = {
    "ibge_municipios": ("municipio", ["ibge_municipios"]),
    "cid10_subcategorias": ("cid", ["cid10_categorias", "cid10_subcategorias"]),
    "sigtap_procedimento": ("procedimento", ["sigtap_procedimento"]),
    "sigtap_ocupacao": ("ocupacao", ["sigtap_ocupacao"]),
}

# Cadastros mensais do CNES com histórico (SCD tipo 2): (tabela, entidade, atributos que a dimensão mostra).
HISTORICOS = [
    ("cnes_st_identificacao", ["cnes"], ["codufmun", "tp_unid", "tp_prest", "nat_jur", "pf_pj", "niv_dep", "cnpj_man"]),
    ("cnes_st_gestao_vinculo", ["cnes"], ["vinc_sus", "tpgestao", "atividad", "clientel", "turno_at"]),
    ("cnes_st_regionalizacao", ["cnes"], ["regsaude", "micr_reg", "distrsan", "distradm"]),
    ("cnes_lt_leito", ["cnes", "tp_leito", "codleito"], ["qt_exist", "qt_contr", "qt_sus", "qt_nsus"]),
    ("cnes_eq_equipamento", ["cnes", "tipequip", "codequip"], ["qt_exist", "qt_uso", "ind_sus", "ind_nsus"]),
    ("cnes_sr_servico_especializado", ["cnes", "serv_esp", "class_sr"], ["srvunico", "caracter", "amb_nsus", "amb_sus", "hosp_nsus", "hosp_sus"]),
    ("cnes_hb_habilitacao", ["cnes", "sgruphab"], ["cmpt_ini", "cmpt_fim", "portaria", "nuleitos"]),
    ("cnes_ep_equipe", ["cnes", "idequipe"], ["tipo_eqp", "id_area", "id_segm", "tiposegm", "dt_ativa", "dt_desat"]),
]

# Dimensões e fatos gerados (13_gerar_dim_fct_agg.py)
SEMENTE_DW = 20261021  # mesma semente, mesmo DW
# Cadastros do CNES com uma dimensão por UF e uma nacional.
DIMENSOES_CNES = [("ST", "identificacao"), ("ST", "gestao_vinculo"), ("ST", "regionalizacao"), ("ST", "contratos_alvara"), ("LT", "leito"),
                  ("EQ", "equipamento"), ("HB", "habilitacao"), ("SR", "servico_especializado"), ("PF", "vinculo"), ("EP", "equipe"),
                  ("IN", "incentivo"), ("GM", "gestao_metas"), ("RC", "regra_contratual")]
# Domínios que muitas tabelas consultam.
DOMINIOS_COMPARTILHADOS = ["ibge_municipios", "sigtap_ocupacao", "cid10_subcategorias", "sigtap_procedimento", "cnes_tp_estab", "cnes_natjur",
                           "sih_sexo", "sih_racacor", "sim_cnes26", "cnes_habilita", "cnes_equipam2508", "cnes_esp_leit", "cnes_vinculo",
                           "cnes_cadgerbr", "sih_municgestor", "sinasc_raca", "sih_leitos"]
# Cadastros que muitas dimensões e fatos leem, com a probabilidade de cada um entrar como fonte.
INT_CAD_CENTRAIS = ["int_cad_municipio_consolidado", "int_cad_nac_cnes_st_identificacao", "int_cad_procedimento_consolidado", "int_cad_ocupacao_consolidado",
                 "int_cad_cid_consolidado", "int_cad_dominio_cnes_tp_estab", "int_cad_dominio_cnes_natjur", "int_cad_dominio_sih_sexo"]
PROBABILIDADE_CENTRAIS = [1.0, 0.5, 0.3, 0.2, 0.15, 0.1, 0.1, 0.1]
FATOS_FOTO_CNES = ["ST", "LT", "EQ", "PF", "SR", "HB"]  # fatos nacionais do CNES gravados como foto diária
# Quantidades do gerador de dimensões e fatos.
MEDIAS_AGG = {"dim": 2.0, "fct": 1.0, "int_cad": 1.0, "int_mov": 0.5, "agg": 0.0}  # dependências médias de cada agregado, por camada
INT_CAD_POR_DIM = [(1, 0.5), (2, 0.5)]   # (cadastros lidos pela dimensão, probabilidade)
PROBABILIDADE_INT_MOV_EM_DIM = 0.05      # chance de uma dimensão ler também um movimento
FATOS_NACIONAIS_CRUZADOS = 20            # fatos nacionais além de um por grupo
AGG_NOVOS = 5                            # agregados gerados, além dos escritos à mão
FONTES_FCT_MEDIANA, FONTES_FCT_P90, FONTES_FCT_MAX = 4, 8, 16  # quantas tabelas cada fato lê (lognormal)
PESO_FONTE_FCT = {"int_cad": 0.5, "int_mov": 0.4, "dim": 0.1}  # de que tipo é cada tabela lida
FATOS_DERIVADOS_POR_NIVEL = {2: 10, 3: 3, 4: 1}                # fatos nacionais que leem fatos, por nível
FATOS_LIDOS_POR_DERIVADO = 3

# Configuração local (scripts/config_local.py, fora do git): o sal e, se quiser, valores que substituem qualquer um dos de cima.
try:
    from config_local import *  # noqa: F401,F403
except ImportError:
    pass
