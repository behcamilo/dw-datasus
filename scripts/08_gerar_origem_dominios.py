"""Gera a origem simulada dos domínios: uma tabela por arquivo de origem, com o nome <fonte>_<arquivo> (ex.: sih_sexo, ibge_municipios).

Entram: os domínios usados pelas colunas (docs/dominios_usados.csv), menos as conversões de data do TabWin; as tabelas que completam
as hierarquias (SIGTAP inteira, CID-10, níveis do IBGE, agrupamentos territoriais do TabWin); e as séries de população.
Gera também docs/dominios_origem.csv (coluna -> domínio).
DT_TRANSACAO: 31/12/2021 nos domínios fixos; SIGTAP no 5º dia útil do mês seguinte à competência; população no 1º dia útil do ano.
"""

import json
import os
import re
import shutil
import tempfile
import zipfile

import pandas as pd
from dbfread import DBF

import config
import origem

PASTA = config.PASTA_RAW / "dominio"
FONTE_DO_PACOTE = {"CID10CSV.zip": "cid10", "NASC_NOV_TAB.zip": "sinasc", "OBITOS_CID10_TAB.zip": "sim", "TAB_CNES.zip": "cnes",
                   "TAB_SIH.zip": "sih", "municipios_ibge.json": "ibge", "TAB_POP.zip": "ibge"}


# Nome do domínio

def nome_do_dominio(pacote, tabela):
    """<fonte>_<arquivo>, minúsculo e só com letras, números e '_'. Ex.: (TAB_SIH.zip, CNV/SEXO.CNV) -> sih_sexo."""
    if pacote == "municipios_ibge.json":
        return "ibge_municipios"
    fonte = "sigtap" if pacote.startswith("TabelaUnificada") else FONTE_DO_PACOTE[pacote]
    arquivo = os.path.splitext(tabela.split("/")[-1])[0].lower()
    arquivo = re.sub(r"^(cid_10_|tb_|br_)", "", re.sub(r"[^a-z0-9]+", "_", arquivo)).strip("_")
    return f"{fonte}_{arquivo}" if not arquivo.startswith(fonte) else arquivo


# Leitores de cada formato

def caminho_do_pacote(pacote):
    return next(PASTA.rglob(pacote))


def ler_dbf(zip_path, membro):
    """DBF de dentro de um zip, tudo como texto."""
    with tempfile.TemporaryDirectory() as tmp:
        zipfile.ZipFile(zip_path).extract(membro, tmp)
        tabela = DBF(os.path.join(tmp, membro), encoding="latin-1", raw=True, ignore_missing_memofile=True)
        linhas = [{k: (v.decode("latin-1").strip() if isinstance(v, bytes) else str(v)) for k, v in r.items()} for r in tabela]
    return pd.DataFrame(linhas).drop_duplicates()  # alguns DBF repetem a mesma linha (ex.: TCHBR)


def ler_cnv(zip_path, membro):
    """Conversão do TabWin: cada linha é 'número  descrição  código1,código2'. Vira uma linha por código."""
    texto = zipfile.ZipFile(zip_path).read(membro).decode("latin-1").splitlines()[1:]  # a 1ª linha é o cabeçalho
    linhas = []
    for linha in texto:
        partes = re.split(r"\s{2,}", linha.strip())
        if len(partes) < 2:
            continue
        descricao = " ".join(partes[1:-1]) if len(partes) >= 3 else partes[1]
        codigos = [c for c in re.split(r"[,\s]+", partes[-1]) if c] if len(partes) >= 3 else []
        for codigo in (codigos or [""]):
            linhas.append({"SEQ": partes[0], "CODIGO": codigo, "DESCRICAO": descricao})
    return pd.DataFrame(linhas).drop_duplicates()  # alguns .CNV repetem a mesma linha


def ler_csv_cid(membro):
    """Um CSV da CID-10 (capítulos, grupos, categorias, subcategorias ou CID-O), com as colunas originais."""
    with zipfile.ZipFile(caminho_do_pacote("CID10CSV.zip")).open(membro) as f:
        d = pd.read_csv(f, sep=";", dtype=str, keep_default_na=False, encoding="latin-1", index_col=False)
    d = d[[c for c in d.columns if not c.startswith("Unnamed")]]  # cada linha termina com ';', o que cria uma coluna vazia
    return d.apply(lambda c: c.str.strip()).drop_duplicates()  # o CSV da CID-O repete linhas


def ler_ibge():
    """Municípios do IBGE e, do mesmo arquivo, os níveis acima deles (cada nível vira uma tabela).
    CODIGO tem 6 dígitos, como no DATASUS; CODIGO_IBGE, 7."""
    dados = json.load(open(caminho_do_pacote("municipios_ibge.json"), encoding="utf-8"))
    niveis = {n: {} for n in ["microrregioes", "mesorregioes", "regioes_imediatas", "regioes_intermediarias", "ufs", "regioes"]}
    municipios = []
    for m in dados:
        micro = m.get("microrregiao") or {}  # alguns municípios novos vêm sem microrregião na API
        imediata = m["regiao-imediata"]
        intermediaria = imediata["regiao-intermediaria"]
        uf = intermediaria["UF"]
        municipios.append({"CODIGO": str(m["id"])[:6], "CODIGO_IBGE": str(m["id"]), "NOME": m["nome"],
                           "ID_MICRORREGIAO": str(micro.get("id", "")), "ID_REGIAO_IMEDIATA": str(imediata["id"])})
        if micro:
            meso = micro["mesorregiao"]
            niveis["microrregioes"][micro["id"]] = {"ID": str(micro["id"]), "NOME": micro["nome"], "ID_MESORREGIAO": str(meso["id"])}
            niveis["mesorregioes"][meso["id"]] = {"ID": str(meso["id"]), "NOME": meso["nome"], "ID_UF": str(meso["UF"]["id"])}
        niveis["regioes_imediatas"][imediata["id"]] = {"ID": str(imediata["id"]), "NOME": imediata["nome"], "ID_REGIAO_INTERMEDIARIA": str(intermediaria["id"])}
        niveis["regioes_intermediarias"][intermediaria["id"]] = {"ID": str(intermediaria["id"]), "NOME": intermediaria["nome"], "ID_UF": str(uf["id"])}
        niveis["ufs"][uf["id"]] = {"ID": str(uf["id"]), "SIGLA": uf["sigla"], "NOME": uf["nome"], "ID_REGIAO": str(uf["regiao"]["id"])}
        niveis["regioes"][uf["regiao"]["id"]] = {"ID": str(uf["regiao"]["id"]), "SIGLA": uf["regiao"]["sigla"], "NOME": uf["regiao"]["nome"]}
    tabelas = {"ibge_municipios": pd.DataFrame(municipios)}
    tabelas.update({f"ibge_{n}": pd.DataFrame(sorted(v.values(), key=lambda x: x["ID"])) for n, v in niveis.items()})
    return tabelas


def ler_sigtap(zip_path, tabela):
    """Tabela de largura fixa da SIGTAP (as posições vêm do <tabela>_layout.txt)."""
    zf = zipfile.ZipFile(zip_path)
    layout = [l.split(",") for l in zf.read(tabela.replace(".txt", "_layout.txt")).decode("latin-1").splitlines()[1:] if l.strip()]
    linhas = []
    for linha in zf.read(tabela).decode("latin-1").splitlines():
        if linha.strip():
            linhas.append({nome: linha[int(ini) - 1:int(fim)].strip() for nome, _tam, ini, fim, _tipo in layout})
    return pd.DataFrame(linhas, columns=[c[0] for c in layout]).drop_duplicates()  # rl_procedimento_renases repete linhas


def ler_tabela_fixa(pacote, tabela, tipo):
    """Lê um domínio de foto única (CID-10, conversão do TabWin ou DBF)."""
    if tipo == "csv":
        return ler_csv_cid(tabela)
    if tipo == "cnv":
        return ler_cnv(caminho_do_pacote(pacote), tabela)
    if tipo == "dbf":
        return ler_dbf(caminho_do_pacote(pacote), tabela)
    raise ValueError(f"tipo de tabela não tratado: {tipo}")


# Gravação

def gravar_dominio(con, df, saida, nome, data, origem_da_tabela):
    """Grava `df` como a tabela de domínio `nome`, toda com a mesma DT_TRANSACAO `data`."""
    gravar_dominio_com_fotos(con, [(df, data)], saida, nome, origem_da_tabela, grupo="fixo")


def gravar_dominio_com_fotos(con, fotos, saida, nome, origem_da_tabela, grupo="fotos"):
    """Grava um domínio com uma ou várias fotos: [(DataFrame, DT_TRANSACAO)]."""
    todos = pd.concat([df.assign(DT_TRANSACAO=pd.Timestamp(data)) for df, data in fotos], ignore_index=True)
    if todos.empty:
        raise ValueError("tabela vazia")
    con.register("df_tmp", todos)
    con.execute("CREATE OR REPLACE TEMP TABLE t AS SELECT * EXCLUDE (DT_TRANSACAO), CAST(DT_TRANSACAO AS DATE) AS DT_TRANSACAO FROM df_tmp")
    con.unregister("df_tmp")
    colunas = [c for c in todos.columns if c != "DT_TRANSACAO"]
    linhas, meses = origem.escrever_particoes(con, "t", saida / "DOMINIO" / nome, colunas)
    origem.CATALOGO.append({"sistema": "DOMINIO", "grupo": grupo, "assunto": nome, "uf": "", "tipo": "dominio",
                            "chave": ",".join(colunas), "pai": origem_da_tabela, "linhas": linhas, "arquivos": meses})
    return linhas


# Montagem

def fotos_da_sigtap(tabela):
    """Uma foto da tabela SIGTAP por competência."""
    fotos = []
    for competencia in config.SIGTAP_COMPETENCIAS:
        zips = sorted((PASTA / "sigtap").glob(f"TabelaUnificada_{competencia}_v*.zip"))
        periodo = f"{competencia[:4]}-{competencia[4:]}"
        d = ler_sigtap(zips[-1], tabela).assign(COMPETENCIA=periodo)
        fotos.append((d, origem.quinto_dia_util_do_mes_seguinte(periodo)))
    return fotos


def tabelas_da_sigtap():
    """Tabelas do pacote SIGTAP com dados, menos as de texto longo."""
    com_dados = set()
    for zip_path in (PASTA / "sigtap").glob("TabelaUnificada_*.zip"):
        com_dados |= {i.filename for i in zipfile.ZipFile(zip_path).infolist()
                      if i.filename.endswith(".txt") and not i.filename.endswith("layout.txt") and i.file_size > 0}  # layout.txt descreve o pacote
    return sorted(t for t in com_dados if os.path.splitext(t)[0] not in config.SIGTAP_TABELAS_FORA)


def fotos_da_populacao():
    """Séries SVS e TCU, uma foto por ano."""
    svs, tcu = [], []
    for ano in config.ANOS:
        yy = str(ano)[2:]
        pacote = caminho_do_pacote(f"POPSBR{yy}.zip")
        membro = next(n for n in zipfile.ZipFile(pacote).namelist() if n.lower().endswith(".dbf"))
        svs.append((ler_dbf(pacote, membro), origem.primeiro_dia_util_do_ano(ano)))
        pacote = caminho_do_pacote(f"POPTBR{yy}.zip")
        pedacos = [ler_dbf(pacote, n) for n in sorted(zipfile.ZipFile(pacote).namelist()) if n.lower().endswith(".dbf")]
        # o pacote de 2022 traz dois DBFs com as mesmas linhas: fica uma linha por município e ano
        tcu.append((pd.concat(pedacos, ignore_index=True).drop_duplicates(), origem.primeiro_dia_util_do_ano(ano)))
    return svs, tcu


def dominios_das_colunas():
    """Domínio de cada coluna (sem as conversões de data); grava docs/dominios_origem.csv."""
    principais = origem.dominios_conceituais()
    for coluna, (pacote, tabela, tipo) in config.DOMINIO_PREFERIDO.items():
        principais.loc[principais.coluna == coluna, ["pacote", "tabela", "tipo"]] = [pacote, tabela, tipo]
    principais["dominio"] = [nome_do_dominio(p, t) for p, t in zip(principais["pacote"], principais["tabela"])]
    data = principais["tabela"].map(lambda t: os.path.splitext(t.split("/")[-1])[0].upper() in config.DOMINIOS_DE_DATA)
    principais["fora"] = data.map({True: "conversão de data (vira o calendário)", False: ""})
    principais.to_csv(config.RAIZ / "docs" / "dominios_origem.csv", index=False, encoding="utf-8-sig")
    return principais[~data]


def gravar(con, saida, nome, ler, origem_da_tabela, problemas, fotos=False):
    """Lê e grava um domínio uma vez só. Um domínio com erro vai para o relatório e não para os outros."""
    if any(c["assunto"] == nome for c in origem.CATALOGO):
        return
    try:
        if fotos:
            gravar_dominio_com_fotos(con, ler(), saida, nome, origem_da_tabela)
        else:
            gravar_dominio(con, ler(), saida, nome, config.DATA_CARGA_INICIAL, origem_da_tabela)
    except Exception as erro:
        problemas.append((nome, origem_da_tabela, str(erro)[:100]))


def main():
    _ufs, saida = origem.ler_argumentos("Gera a origem simulada dos domínios (não depende de UF).")
    con = origem.abrir_duckdb("dominios")
    shutil.rmtree(saida / "DOMINIO", ignore_errors=True)
    problemas = []

    # 1. domínios usados pelas colunas
    usados = dominios_das_colunas().drop_duplicates("dominio")
    sigtap = set()
    for r in usados.itertuples():
        if r.tipo == "txt (largura fixa)":
            sigtap.add(r.tabela)  # gravada no passo 2
        elif r.tipo == "json":
            continue              # IBGE: passo 2
        else:
            gravar(con, saida, r.dominio, lambda r=r: ler_tabela_fixa(r.pacote, r.tabela, r.tipo), f"{r.pacote}:{r.tabela}", problemas)
    print(f"{len(usados)} domínios usados pelas colunas (um por arquivo de origem)")

    # 2. hierarquias
    for tabela in sorted(sigtap | set(tabelas_da_sigtap())):
        gravar(con, saida, nome_do_dominio("TabelaUnificada", tabela), lambda t=tabela: fotos_da_sigtap(t), f"TabelaUnificada:{tabela}", problemas, fotos=True)
    for membro in config.CID10_ARQUIVOS:
        gravar(con, saida, nome_do_dominio("CID10CSV.zip", membro), lambda m=membro: ler_csv_cid(m), f"CID10CSV.zip:{membro}", problemas)
    for nome, df in ler_ibge().items():
        gravar(con, saida, nome, lambda df=df: df, "municipios_ibge.json", problemas)
    pacote_pop = caminho_do_pacote("TAB_POP.zip")
    for arquivo in config.TERRITORIO_TAB_POP:
        membro = next(n for n in zipfile.ZipFile(pacote_pop).namelist() if n.lower().endswith("/" + arquivo))
        gravar(con, saida, nome_do_dominio("TAB_POP.zip", arquivo), lambda m=membro: ler_cnv(pacote_pop, m), f"TAB_POP.zip:{membro}", problemas)

    svs, tcu = fotos_da_populacao()
    gravar(con, saida, "populacao_svs", lambda: svs, "POPSBR21/22.zip", problemas, fotos=True)
    gravar(con, saida, "populacao_tcu", lambda: tcu, "POPTBR21/22.zip", problemas, fotos=True)

    print(f"{len(origem.CATALOGO)} domínios gravados em {saida / 'DOMINIO'}")
    for p in problemas:
        print("  PROBLEMA:", p)
    origem.salvar_catalogo(saida, substituir_sistema="DOMINIO")


if __name__ == "__main__":
    main()
