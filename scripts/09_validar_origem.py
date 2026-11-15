"""Valida a origem simulada e escreve docs/origem_simulada.md.

Confere, UF por UF: linhas contra o arquivo original, chave única, registro pai, distribuição da DT_TRANSACAO, dados pessoais (só hash),
tamanho em disco e determinismo (gera algumas UFs de novo e compara o sha256 de cada arquivo).
As tabelas grandes são conferidas mês a mês, para caber na memória.

Uso:  python scripts/09_validar_origem.py [--ufs RR]
"""

import argparse
import hashlib
import shutil
import subprocess
import sys
from datetime import date

import pandas as pd

import config
import origem

SCRIPTS_DE_GERACAO = ["05_gerar_origem_sih.py", "06_gerar_origem_sim_sinasc.py", "07_gerar_origem_cnes.py", "08_gerar_origem_dominios.py"]
UFS_DO_TESTE_DE_DETERMINISMO = ["RR", "AC"]  # uma UF pequena e outra de porte médio
UF_DO_ARQUIVO = "substr(regexp_extract(filename, '([^/\\\\]+)$', 1), 3, 2)"  # RDRR2101 -> RR (as duas letras depois do grupo)
GRUPOS_POR_ANO = {("SIM", "DO"), ("SINASC", "DN")}  # arquivos anuais: um mês da origem mistura dois anos


def tabela_md(df):
    linhas = ["| " + " | ".join(str(c) for c in df.columns) + " |", "|" + "---|" * len(df.columns)]
    linhas += ["| " + " | ".join("" if pd.isna(v) else str(v) for v in linha) + " |" for linha in df.itertuples(index=False)]
    return "\n".join(linhas)


def mb(b):
    return f"{b / 1e6:,.0f} MB" if b < 1e9 else f"{b / 1e9:,.1f} GB"


def pasta_da_tabela(r):
    return (config.PASTA_ORIGEM / r.sistema / r.grupo / r.assunto).as_posix()


def le_origem(r, uf="*", mes="*"):
    """SQL que lê a tabela de origem (UF e mês opcionais)."""
    return f"read_parquet('{pasta_da_tabela(r)}/uf={uf}/mes={mes}/dados.parquet', hive_partitioning=true)"


def le_raw(sistema, grupo, ufs):
    lista = ", ".join(f"'{c}'" for uf in ufs for c in origem.arquivos_da_uf(sistema, grupo, uf)["caminho"])
    return f"read_parquet([{lista}], union_by_name=true, filename=true)"


def meses_da_tabela(r):
    return sorted({p.name.split("=")[1] for p in (config.PASTA_ORIGEM / r.sistema / r.grupo / r.assunto).glob("uf=*/mes=*")})


def por_mes_ou_inteiro(r, linhas_total):
    """Meses a consultar um por vez, ou [None] para uma consulta só (tabelas pequenas)."""
    grande = linhas_total > 5_000_000 and (r.sistema, r.grupo) not in GRUPOS_POR_ANO
    return meses_da_tabela(r) if grande else [None]


# 1. Reconciliação

def esperado_por_uf(con, r, mapa, ufs):
    """Linhas que a tabela deveria ter em cada UF, recalculadas do arquivo original."""
    s, g, a, tipo = r.sistema, r.grupo, r.assunto, r.tipo
    raw = le_raw(s, g, ufs)
    colunas = origem.colunas_do_assunto(mapa, s, g, a)
    consulta = lambda sql: con.execute(sql).df().set_index("uf")["n"]
    if tipo in ("plana", "ato"):
        return consulta(f"SELECT {UF_DO_ARQUIVO} AS uf, count(*) AS n FROM {raw} GROUP BY 1"), "todas as linhas do arquivo (1:1)"
    if tipo == "esparsa":
        padrao = config.COLUNAS_VALOR_PADRAO.get((s, g), [])
        filtro = " OR ".join(origem.sql_preenchido(c) for c in colunas if c not in padrao)
        return consulta(f"SELECT {UF_DO_ARQUIVO} AS uf, count(*) AS n FROM {raw} WHERE {filtro} GROUP BY 1"), "linhas com algum conteúdo (sem contar valor padrão)"
    if tipo == "filha":
        cols = [c for c in colunas if c.startswith("DIAG") or c == "CID_NOTIF"] if a == "diagnostico" else colunas
        soma = " + ".join(f"CASE WHEN {origem.sql_preenchido(c)} THEN 1 ELSE 0 END" for c in cols)
        return consulta(f"SELECT {UF_DO_ARQUIVO} AS uf, sum({soma}) AS n FROM {raw} GROUP BY 1"), \
            "um por diagnóstico preenchido" if a == "diagnostico" else "um por item preenchido"
    if tipo == "profissional":
        return consulta(f"""SELECT uf, count(*) AS n FROM (
                            SELECT DISTINCT {UF_DO_ARQUIVO} AS uf, SP_PF_DOC, SP_PF_CBO FROM {raw} WHERE {origem.sql_preenchido('SP_PF_DOC')}) GROUP BY 1"""), \
            "um por profissional distinto (documento + CBO), sem versões"
    raise ValueError(f"tipo de tabela sem regra de reconciliação: {tipo}")


def reconciliar(con, tabelas, mapa, ufs):
    linhas = []
    for r in tabelas.itertuples():
        esp, como = esperado_por_uf(con, r, mapa, ufs)
        gerado = con.execute(f"SELECT uf, count(*) AS n FROM {le_origem(r)} GROUP BY 1").df().set_index("uf")["n"]
        original = con.execute(f"SELECT {UF_DO_ARQUIVO} AS uf, count(*) AS n FROM {le_raw(r.sistema, r.grupo, ufs)} GROUP BY 1").df().set_index("uf")["n"]
        ruins = sorted(u for u in set(gerado.index) | set(esp.index) if int(gerado.get(u, 0)) != int(esp.get(u, 0)))
        linhas.append({"tabela": f"{r.sistema}/{r.grupo}/{r.assunto}", "tipo": r.tipo, "UFs": len(gerado), "arquivo original": f"{int(original.sum()):,}",
                       "origem": f"{int(gerado.sum()):,}", "esperado": f"{int(esp.sum()):,}", "confere": "SIM" if not ruins else "NÃO",
                       "% do original": round(100 * gerado.sum() / original.sum(), 2), "UFs com diferença": ", ".join(ruins), "como": como})
    return pd.DataFrame(linhas)


# 2. Chave única e 3. Registro pai

def chaves_unicas(con, tabelas):
    linhas = []
    for r in tabelas.itertuples():
        tupla = ", ".join(["uf"] + [f'"{c}"' for c in r.chave.split(",")])
        total = distintas = 0
        for mes in por_mes_ou_inteiro(r, r.linhas):
            n, d = con.execute(f"SELECT count(*), count(DISTINCT ({tupla})) FROM {le_origem(r, mes=mes or '*')}").fetchone()
            total, distintas = total + n, distintas + d
        linhas.append({"tabela": f"{r.sistema}/{r.grupo}/{r.assunto}", "chave (por UF)": r.chave, "linhas": f"{total:,}", "repetidas": total - distintas,
                       "única": "SIM" if total == distintas else "NÃO"})
    return pd.DataFrame(linhas)


def colunas_de_ligacao(r):
    """(colunas do filho, colunas do pai) para a ligação com a tabela pai."""
    if (r.sistema, r.grupo) == ("SIH", "SP"):
        return config.CHAVE_REPETIDA[("SIH", "SP")], config.CHAVE_REPETIDA[("SIH", "RD")]
    if (r.sistema, r.grupo) in config.GRUPOS_COM_ID_ORIGEM:
        return ["id_origem"], ["id_origem"]
    return config.CHAVE_REPETIDA[(r.sistema, r.grupo)], config.CHAVE_REPETIDA[(r.sistema, r.grupo)]


def sem_pai(con, tabelas):
    linhas = []
    for r in tabelas[tabelas["pai"] != ""].itertuples():
        ps, pg, pa = r.pai.split("/")
        pai = tabelas[(tabelas["sistema"] == ps) & (tabelas["grupo"] == pg) & (tabelas["assunto"] == pa)].iloc[0]
        filho_cols, pai_cols = colunas_de_ligacao(r)
        on = " AND ".join(["f.uf = p.uf"] + [f'f."{a}" = p."{b}"' for a, b in zip(filho_cols, pai_cols)])
        orfas = 0
        for mes in por_mes_ou_inteiro(r, r.linhas):
            m = mes or "*"
            orfas += con.execute(f"SELECT count(*) FROM {le_origem(r, mes=m)} f ANTI JOIN {le_origem(pai, mes=m)} p ON {on}").fetchone()[0]
        linhas.append({"filha": f"{r.sistema}/{r.grupo}/{r.assunto}", "pai": r.pai, "ligação (além da UF)": ", ".join(filho_cols), "linhas sem pai": orfas})
    # todo ato com profissional aponta para um profissional que existe
    ato = tabelas[(tabelas["grupo"] == "SP") & (tabelas["assunto"] == "ato_profissional")]
    prof = tabelas[(tabelas["grupo"] == "SP") & (tabelas["assunto"] == "profissional")]
    if not ato.empty and not prof.empty:
        a, p = ato.iloc[0], prof.iloc[0]
        n = con.execute(f"""SELECT count(*) FROM {le_origem(a)} f WHERE SP_PF_DOC IS NOT NULL
                            AND NOT EXISTS (SELECT 1 FROM {le_origem(p)} p WHERE p.uf = f.uf AND p.SP_PF_DOC = f.SP_PF_DOC AND p.SP_PF_CBO = f.SP_PF_CBO)""").fetchone()[0]
        linhas.append({"filha": "SIH/SP/ato_profissional (profissional não nulo)", "pai": "SIH/SP/profissional", "ligação (além da UF)": "SP_PF_DOC, SP_PF_CBO", "linhas sem pai": n})
        dif = con.execute(f"""SELECT count(*) FROM (SELECT uf, SP_PF_DOC, SP_PF_CBO, min(DT_TRANSACAO) d FROM {le_origem(a)} WHERE SP_PF_DOC IS NOT NULL GROUP BY ALL) x
                              JOIN (SELECT uf, SP_PF_DOC, SP_PF_CBO, DT_TRANSACAO d FROM {le_origem(p)}) y USING (uf, SP_PF_DOC, SP_PF_CBO) WHERE x.d <> y.d""").fetchone()[0]
        linhas.append({"filha": "profissional: DT_TRANSACAO = a do 1º ato em que aparece", "pai": "SIH/SP/ato_profissional", "ligação (além da UF)": "SP_PF_DOC, SP_PF_CBO", "linhas sem pai": dif})
    return pd.DataFrame(linhas)


# 4. Distribuição do DT_TRANSACAO

def distribuicao(con, tabelas):
    linhas = []
    for (s, g), grupo in tabelas.groupby(["sistema", "grupo"]):
        principal = grupo[grupo["assunto"] == config.ASSUNTO_PRINCIPAL[(s, g)]]
        if principal.empty:
            continue
        r = principal.iloc[0]
        d = con.execute(f"SELECT DT_TRANSACAO AS dia, count(*) AS n FROM {le_origem(r)} GROUP BY 1 ORDER BY 1").df()
        por_uf = con.execute(f"SELECT uf, count(*) AS n FROM {le_origem(r)} GROUP BY 1").df()
        d["dia"] = pd.to_datetime(d["dia"])
        util = d["dia"].dt.weekday.lt(5) & ~d["dia"].dt.date.isin(config.FERIADOS_NACIONAIS)
        total = int(d["n"].sum())
        antes, em22, em23 = (int(d.loc[d["dia"] <= pd.Timestamp(date(2021, 12, 31)), "n"].sum()),
                             int(d.loc[d["dia"].dt.year == 2022, "n"].sum()), int(d.loc[d["dia"].dt.year >= 2023, "n"].sum()))
        linhas.append({"grupo": f"{s}-{g}", "UFs": len(por_uf), "linhas": f"{total:,}", "dias": len(d), "mín/dia": int(d["n"].min()), "mediana/dia": int(d["n"].median()),
                       "máx/dia": int(d["n"].max()), "linhas por UF (mín–máx)": f"{int(por_uf['n'].min()):,} – {int(por_uf['n'].max()):,}",
                       "primeira": d["dia"].min().date(), "última": d["dia"].max().date(),
                       "até 31/12/2021": f"{antes:,} ({100 * antes / total:.1f}%)", "em 2022": f"{em22:,} ({100 * em22 / total:.1f}%)",
                       "em 2023": f"{em23:,} ({100 * em23 / total:.1f}%)", "% em dia útil": round(100 * d.loc[util, "n"].sum() / total, 1)})
    return pd.DataFrame(linhas)


# 5. Dados pessoais

def auditar_dados_pessoais(con, tabelas):
    """Colunas com hash só têm sha256 (ou NULL); NOMEPROF e CPF_AUT não existem."""
    linhas = []
    for (s, g), colunas in config.COLUNAS_COM_HASH.items():
        for r in tabelas[(tabelas["sistema"] == s) & (tabelas["grupo"] == g)].itertuples():
            nomes = [d[0] for d in con.execute(f"DESCRIBE SELECT * FROM {le_origem(r)}").fetchall()]
            for c in [c for c in colunas if c in nomes]:
                ruim, total, nulos = con.execute(
                    f"""SELECT count(*) FILTER (WHERE "{c}" IS NOT NULL AND NOT regexp_matches("{c}", '^[0-9a-f]{{64}}$')), count(*),
                               count(*) FILTER (WHERE "{c}" IS NULL) FROM {le_origem(r)}""").fetchone()
                linhas.append({"tabela": f"{s}/{g}/{r.assunto}", "coluna": c, "linhas": f"{total:,}", "NULL (vazio/sentinela)": f"{nulos:,} ({100 * nulos / total:.1f}%)",
                               "valores que NÃO são hash": ruim})
    # colunas com hash só quando o valor é CPF
    st = tabelas[(tabelas["grupo"] == "ST") & (tabelas["assunto"] == "identificacao")]
    if not st.empty:
        pf_sem_hash, pj_com_hash, pf_total = con.execute(
            f"""SELECT count(*) FILTER (WHERE PF_PJ = '1' AND CPF_CNPJ IS NOT NULL AND NOT regexp_matches(CPF_CNPJ, '^[0-9a-f]{{64}}$')),
                       count(*) FILTER (WHERE PF_PJ <> '1' AND regexp_matches(CPF_CNPJ, '^[0-9a-f]{{64}}$')),
                       count(*) FILTER (WHERE PF_PJ = '1') FROM {le_origem(st.iloc[0])}""").fetchone()
        linhas.append({"tabela": "CNES/ST/identificacao", "coluna": "CPF_CNPJ (só PF_PJ = 1)", "linhas": f"{pf_total:,} de pessoa física",
                       "NULL (vazio/sentinela)": f"{pj_com_hash} de pessoa jurídica com hash", "valores que NÃO são hash": pf_sem_hash})
    ato = tabelas[(tabelas["grupo"] == "SP") & (tabelas["assunto"] == "ato_profissional")]
    if not ato.empty:
        com_hash, total = con.execute(f"""SELECT count(*) FILTER (WHERE regexp_matches(SP_CPFCGC, '^[0-9a-f]{{64}}$')), count(*) FROM {le_origem(ato.iloc[0])}""").fetchone()
        linhas.append({"tabela": "SIH/SP/ato_profissional", "coluna": "SP_CPFCGC (só se parece CPF)", "linhas": f"{total:,}",
                       "NULL (vazio/sentinela)": f"{com_hash:,} com hash; o resto é CNES/CNPJ e fica como veio", "valores que NÃO são hash": 0})
    proibidas = []
    for (s, g), colunas in config.COLUNAS_FORA.items():
        for r in tabelas[(tabelas["sistema"] == s) & (tabelas["grupo"] == g)].itertuples():
            nomes = [d[0] for d in con.execute(f"DESCRIBE SELECT * FROM {le_origem(r)}").fetchall()]
            proibidas += [f"{s}/{g}/{r.assunto}.{c}" for c in colunas if c in nomes]
    return pd.DataFrame(linhas), proibidas


# 6. Tamanho em disco

def tamanho_em_disco():
    linhas, total = [], 0
    for pasta in sorted(p for p in config.PASTA_ORIGEM.iterdir() if p.is_dir()):
        arquivos = list(pasta.rglob("*.parquet"))
        tamanho = sum(f.stat().st_size for f in arquivos)
        total += tamanho
        linhas.append({"sistema": pasta.name, "arquivos": f"{len(arquivos):,}", "tamanho": mb(tamanho)})
    return pd.DataFrame(linhas), total


# 7. Determinismo

def sha256_do_arquivo(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def hashes_da_pasta(raiz, ufs):
    """sha256 de cada arquivo das UFs dadas e dos domínios (caminho relativo -> hash)."""
    saida = {}
    for f in sorted(raiz.rglob("*.parquet")):
        rel = f.relative_to(raiz).as_posix()
        if rel.startswith("DOMINIO/") or any(f"/uf={u}/" in f"/{rel}" for u in ufs):
            saida[rel] = sha256_do_arquivo(f)
    return saida


def testar_determinismo(ufs):
    teste = config.RAIZ / "dados" / "origem_verificacao"
    shutil.rmtree(teste, ignore_errors=True)
    for script in SCRIPTS_DE_GERACAO:
        args = [sys.executable, "-X", "utf8", str(config.RAIZ / "scripts" / script), "--ufs", *ufs, "--saida", str(teste)]
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL, cwd=config.RAIZ)
    a, b = hashes_da_pasta(config.PASTA_ORIGEM, ufs), hashes_da_pasta(teste, ufs)
    diferentes = sorted(k for k in a.keys() & b.keys() if a[k] != b[k])
    so_um_lado = sorted(a.keys() ^ b.keys())
    shutil.rmtree(teste, ignore_errors=True)
    return len(a), diferentes, so_um_lado


# Relatório

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ufs", nargs="+", help="UFs a validar (padrão: todas as do catálogo)")
    catalogo = pd.read_csv(config.PASTA_ORIGEM / "_catalogo.csv", dtype=str, keep_default_na=False)
    ufs = parser.parse_args().ufs or sorted(u for u in catalogo["uf"].unique() if u)
    mapa = origem.ler_mapa()
    tabelas = (catalogo[catalogo["uf"].isin(ufs)].assign(linhas=lambda d: d["linhas"].astype(int))
               .groupby(["sistema", "grupo", "assunto", "tipo", "chave", "pai"], as_index=False)["linhas"].sum())
    dominios = catalogo[catalogo["tipo"] == "dominio"]
    con = origem.abrir_duckdb("validacao")

    print(f"validando {len(ufs)} UFs, {len(tabelas)} tabelas por UF")
    print("1/7 reconciliação");  rec = reconciliar(con, tabelas, mapa, ufs)
    print("2/7 chaves");         chaves = chaves_unicas(con, tabelas)
    print("3/7 registro pai");   pais = sem_pai(con, tabelas)
    print("4/7 DT_TRANSACAO");   dist = distribuicao(con, tabelas)
    print("5/7 dados pessoais"); pessoais, proibidas = auditar_dados_pessoais(con, tabelas)
    print("6/7 tamanho");        tam, total_bytes = tamanho_em_disco()
    testadas = [u for u in UFS_DO_TESTE_DE_DETERMINISMO if u in ufs]
    print(f"7/7 determinismo (gera {testadas} de novo numa pasta de teste)")
    n_arq, diferentes, so_um_lado = testar_determinismo(testadas)

    problemas = {"reconciliação": int((rec["confere"] == "NÃO").sum()), "chave repetida": int((chaves["única"] == "NÃO").sum()),
                 "linhas sem pai": int(pais["linhas sem pai"].sum()), "arquivos com hash diferente": len(diferentes) + len(so_um_lado),
                 "valores sem hash": int(pessoais["valores que NÃO são hash"].sum()), "colunas proibidas na origem": len(proibidas)}
    tudo_ok = not any(problemas.values())
    texto = "\n".join([
        f"# Origem simulada: validação ({len(ufs)} UFs)\n",
        f"Gerado em {date.today()} por `09_validar_origem.py`. UFs: {', '.join(ufs)}.\n",
        f"**Resultado: {'TODAS as validações passaram' if tudo_ok else 'HÁ PROBLEMAS: ' + str(problemas)}.** "
        f"{len(tabelas)} tabelas por UF (cada uma nas UFs em que o grupo existe); {len(dominios)} tabelas de domínio.\n",
        "## 1. Reconciliação com o arquivo original\n",
        "'Esperado' é recalculado do arquivo original, UF por UF: todas as linhas nas tabelas planas; só as preenchidas nas esparsas e filhas; "
        "um por profissional distinto em `profissional`.\n", tabela_md(rec), "",
        "## 2. Chave única em cada tabela\n",
        "A chave é conferida junto com a UF.\n", tabela_md(chaves), "",
        "## 3. Registro pai\n", tabela_md(pais), "",
        "## 4. Distribuição do DT_TRANSACAO (tabela principal de cada grupo, todas as UFs juntas)\n",
        "Linhas por dia. No SIH o volume é igual em todos os dias úteis de um mês; no SIM e no SINASC segue a data do evento.\n", tabela_md(dist), "",
        "## 5. Dados pessoais\n",
        f"Colunas com hash e quantos valores não são hash. Colunas que não podem estar na origem (NOMEPROF, CPF_AUT) encontradas: "
        f"**{proibidas or 'nenhuma'}**.\n", tabela_md(pessoais), "",
        "## 6. Tamanho em disco\n", tabela_md(tam), "",
        f"Total da origem: **{mb(total_bytes)}**.\n",
        "## 7. Determinismo\n",
        f"As UFs {', '.join(testadas)} foram geradas de novo numa pasta de teste e comparadas arquivo a arquivo (sha256): "
        f"**{n_arq} arquivos comparados, {len(diferentes)} diferentes, {len(so_um_lado)} presentes só de um lado.**",
        ("" if not diferentes and not so_um_lado else f"\nDiferentes: {diferentes[:20]}; só de um lado: {so_um_lado[:20]}"), "",
    ])
    (config.RAIZ / "docs" / "origem_simulada.md").write_text(texto, encoding="utf-8")
    print(texto[:900])


if __name__ == "__main__":
    main()
