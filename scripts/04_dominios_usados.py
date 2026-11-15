"""Liga cada coluna do recorte à tabela de domínio que ela usa e grava docs/dominios_usados.csv (usado pelo script 08).

Duas fontes: os arquivos .DEF do TabWin ("a coluna X usa a tabela Y") e, para CID, município, procedimento e CBO, o nome da coluna.
Recebe: docs/mapa_assuntos.csv e os pacotes de domínio em dados/raw/dominio/ (script 03).
"""

import json
import re
import struct
import zipfile

import pandas as pd

import config

PASTA_DOMINIO = config.PASTA_RAW / "dominio"

# Grupo -> (pacote, nome do .DEF dentro do pacote)
DEFS = {
    ("SIH", "RD"): ("sih/TAB_SIH.zip", "RD2008.DEF"), ("SIH", "SP"): ("sih/TAB_SIH.zip", "SP2008.DEF"),
    ("CNES", "ST"): ("cnes/TAB_CNES.zip", "Estabelecimento.def"), ("CNES", "LT"): ("cnes/TAB_CNES.zip", "Leitos_Especialidade.def"),
    ("CNES", "PF"): ("cnes/TAB_CNES.zip", "Profissional.def"), ("CNES", "EQ"): ("cnes/TAB_CNES.zip", "Equipamento.def"),
    ("CNES", "SR"): ("cnes/TAB_CNES.zip", "Servico_Especializado_200803_.def"), ("CNES", "HB"): ("cnes/TAB_CNES.zip", "Habilitacao.def"),
    ("CNES", "EP"): ("cnes/TAB_CNES.zip", "Equipes.def"), ("CNES", "DC"): ("cnes/TAB_CNES.zip", "DadosComplementares.def"),
    ("CNES", "RC"): ("cnes/TAB_CNES.zip", "Regras_Contratuais.def"), ("CNES", "IN"): ("cnes/TAB_CNES.zip", "Incentivos.def"),
    ("CNES", "GM"): ("cnes/TAB_CNES.zip", "Gestao_de_Metas.def"), ("CNES", "EE"): ("cnes/TAB_CNES.zip", "Estabel_Ensino.def"),
    ("CNES", "EF"): ("cnes/TAB_CNES.zip", "Estabel_Filantropico.def"),
    ("SIM", "DO"): ("sim/OBITOS_CID10_TAB.zip", "OBITOS_CID10_TAB/tabdo/Obito_1996_CID10.def"),
    ("SINASC", "DN"): ("sinasc/NASC_NOV_TAB.zip", "NASC_NOV_TAB/NASCIDO.def"),
}

# Ligações pelo nome da coluna (sem .DEF): tipo de ligação -> [(tipo, tabela, pacote)]
SIGTAP = "sigtap/TabelaUnificada_202212_v2212051647.zip"
TABELAS_POR_CODIGO = {
    "Município": [("json", "municipios_ibge.json", "ibge/municipios_ibge.json")],
    "CID (diagnóstico/causa)": [("csv", "CID-10-CATEGORIAS.CSV", "cid10/CID10CSV.zip"), ("csv", "CID-10-SUBCATEGORIAS.CSV", "cid10/CID10CSV.zip")],
    "Procedimento": [("txt (largura fixa)", "tb_procedimento.txt", SIGTAP)],
}
CBO_POR_SISTEMA = {  # no SIM e no SINASC a ocupação usa a tabela do próprio sistema
    "SIM": [("cnv", "OBITOS_CID10_TAB/tabdo/CBO2002.CNV", "sim/OBITOS_CID10_TAB.zip")],
    "SINASC": [("cnv", "NASC_NOV_TAB/CBO2002.CNV", "sinasc/NASC_NOV_TAB.zip")],
}
CBO_PADRAO = [("txt (largura fixa)", "tb_ocupacao.txt", SIGTAP)]
# Colunas que casam com os padrões de nome, mas não são município, procedimento nem CID.
NAO_E_LIGACAO = {"COMUNSVOIM", "NUM_PROC", "ACIDTRAB", "ALTCAUSA", "S_IMUNFE", "S_IMUNOH", "S_PROCES", "SP_QT_PROC"}
COLUNAS_CBO = r"^(CBOR|CBO|OCUP|OCUPMAE|CODOCUPMAE|SP_PF_CBO)$"


def contar_linhas(pacote, membro, tipo):
    """Linhas de uma tabela de domínio (sem o cabeçalho, no CSV e no .CNV)."""
    caminho = PASTA_DOMINIO / pacote
    if tipo == "json":
        return len(json.load(open(caminho, encoding="utf-8")))
    zf = zipfile.ZipFile(caminho)
    if tipo == "dbf":
        with zf.open(membro) as f:
            return struct.unpack("<I", f.read(32)[4:8])[0]  # o cabeçalho do DBF guarda o número de linhas
    linhas = zf.read(membro).decode("latin-1").splitlines()
    return len(linhas) - 1 if tipo in ("csv", "cnv") else len(linhas)


def refs_do_def(pacote, nome_def):
    """[(coluna, arquivo citado, pasta do .DEF)] de um .DEF do TabWin, e a lista de arquivos do pacote."""
    zf = zipfile.ZipFile(PASTA_DOMINIO / pacote)
    nomes = zf.namelist()
    achado = [n for n in nomes if n.lower() == nome_def.lower()][0]
    pasta_do_def = achado.rsplit("/", 1)[0] + "/" if "/" in achado else ""
    refs = []
    for linha in zf.read(achado).decode("latin-1").splitlines():
        partes = [p.strip() for p in linha.split(",")]
        if not linha.startswith(";") and len(partes) >= 4 and re.search(r"\.(cnv|dbf)$", partes[-1], re.I):
            refs.append((partes[1], partes[-1].replace("\\", "/"), pasta_do_def))
    return refs, nomes


def resolver_membro(citado, pasta_do_def, nomes_do_zip):
    """Nome real do arquivo dentro do pacote (o .DEF não respeita maiúsculas nem a pasta)."""
    for candidato in (citado, pasta_do_def + citado):
        for n in nomes_do_zip:
            if n.lower() == candidato.lower():
                return n
    return None


def ligacao(sistema, grupo, coluna, forma, tipo, tabela, pacote, linhas):
    return {"sistema": sistema, "grupo": grupo, "coluna": coluna, "forma de ligação": forma, "tipo": tipo,
            "tabela": tabela, "pacote": pacote.split("/")[-1], "linhas": linhas}


def ligacoes_do_grupo(sistema, grupo, colunas):
    linhas = []
    if (sistema, grupo) in DEFS:
        pacote, nome_def = DEFS[(sistema, grupo)]
        refs, nomes = refs_do_def(pacote, nome_def)
        por_nome = {c.lower(): c for c in colunas}
        for coluna, citado, pasta in refs:
            if coluna.lower() not in por_nome:
                continue  # coluna de layout antigo, que não existe nos arquivos
            membro = resolver_membro(citado, pasta, nomes)
            tipo = citado.rsplit(".", 1)[-1].lower()
            linhas.append(ligacao(sistema, grupo, por_nome[coluna.lower()], "DEF do TabWin", tipo,
                                  membro or f"(NÃO ENCONTRADA) {citado}", pacote, contar_linhas(pacote, membro, tipo) if membro else None))
    for rotulo, padrao in config.PADROES_LIGACAO.items():
        for c in colunas:
            if rotulo in TABELAS_POR_CODIGO and re.search(padrao, c, re.I) and c not in NAO_E_LIGACAO:
                for tipo, tabela, pacote in TABELAS_POR_CODIGO[rotulo]:
                    linhas.append(ligacao(sistema, grupo, c, f"código ({rotulo})", tipo, tabela, pacote, contar_linhas(pacote, tabela, tipo)))
    for c in colunas:
        if re.match(COLUNAS_CBO, c):
            for tipo, tabela, pacote in CBO_POR_SISTEMA.get(sistema, CBO_PADRAO):
                linhas.append(ligacao(sistema, grupo, c, "código (CBO)", tipo, tabela, pacote, contar_linhas(pacote, tabela, tipo)))
    return linhas


def main():
    mapa = pd.read_csv("docs/mapa_assuntos.csv", encoding="utf-8-sig")
    linhas = []
    for (sistema, grupo), parte in mapa.groupby(["sistema", "grupo"]):
        linhas += ligacoes_do_grupo(sistema, grupo, list(parte["coluna_original"]))
    usadas = pd.DataFrame(linhas).drop_duplicates(["sistema", "grupo", "coluna", "tabela", "pacote"])
    usadas.to_csv("docs/dominios_usados.csv", index=False, encoding="utf-8-sig")
    print(f"{len(usadas)} ligações coluna -> tabela em docs/dominios_usados.csv")


if __name__ == "__main__":
    main()
