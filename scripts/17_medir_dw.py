"""Resume as execuções em RR (tempos, linhas, espaço estimado para as 27 UFs) em docs/resultados_dw.md.

Recebe: dw_dbt/target/manifest.json, dados/origem/_catalogo.csv e, em docs/execucoes/, os run_results e as contagens
da carga inicial e do dia de teste.
Uso: python scripts/17_medir_dw.py
"""

import json
import os

import pandas as pd

import config

PASTA_EXEC = "docs/execucoes"
def tabela_md(cabecalho, linhas):
    texto = "| " + " | ".join(cabecalho) + " |\n|" + "---|" * len(cabecalho) + "\n"
    return texto + "\n".join("| " + " | ".join(str(c) for c in l) + " |" for l in linhas) + "\n"


def fmt(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if isinstance(x, float) else f"{x:,}".replace(",", ".")


# Tipo de carga de cada modelo

def tipos_de_carga():
    """Nome do modelo -> tipo de carga (meta do manifest do dbt)."""
    m = json.load(open("dw_dbt/target/manifest.json", encoding="utf-8"))
    return {v["name"]: (v.get("meta") or v.get("config", {}).get("meta") or {}).get("tipo_carga", "?")
            for v in m["nodes"].values() if v["resource_type"] == "model"}


# Execução

def tempos_por_modelo(arquivo, nome_para_tipo):
    r = json.load(open(arquivo, encoding="utf-8"))
    linhas = []
    for x in r["results"]:
        nome = x["unique_id"].split(".")[-1]
        linhas.append({"modelo": nome, "tipo": nome_para_tipo.get(nome, "?"), "segundos": x["execution_time"], "status": x["status"]})
    return pd.DataFrame(linhas)


def tabela_de_tempos(df):
    g = df.groupby("tipo").segundos.agg(["count", "sum", "mean", "max"]).reset_index()
    return tabela_md(["tipo de carga", "modelos", "total (s)", "média (s)", "máx (s)"],
                     [[r.tipo, r["count"], fmt(float(r["sum"])), fmt(float(r["mean"])), fmt(float(r["max"]))] for _, r in g.iterrows()])


def sistema_da_tabela(nome):
    """Sistema de origem de uma tabela pelo nome (para estimar o espaço)."""
    for chave, s in (("cnes", "CNES"), ("sih", "SIH"), ("sinasc", "SINASC"), ("sim_", "SIM"), ("internacao", "SIH"), ("obito", "SIM"),
                     ("nascimento", "SINASC"), ("leito", "CNES"), ("profissional", "CNES"), ("equipamento", "CNES"), ("habilitacao", "CNES"),
                     ("estabelecimento", "CNES")):
        if chave in nome:
            return s
    return None


def secao_execucao(nome_para_tipo):
    ini = tempos_por_modelo(f"{PASTA_EXEC}/run_results_carga_inicial_rr.json", nome_para_tipo)
    cont = json.load(open(f"{PASTA_EXEC}/contagens_carga_inicial.json"))
    tab = pd.DataFrame([{"tabela": k, "camada": k.split(".")[0], "linhas": v["linhas"], "bytes": v["bytes"]} for k, v in cont.items()])
    tab.sort_values(["camada", "bytes"], ascending=[True, False]).to_csv("docs/resultados_dw_tabelas.csv", index=False)

    t = "\n## 1. Carga inicial de RR (até 31/12/2021)\n\n"
    t += f"{len(ini)} modelos do dbt, {(ini.status == 'success').sum()} com sucesso. Tabela a tabela: `docs/resultados_dw_tabelas.csv`.\n\n"
    g = tab.groupby("camada").agg(tabelas=("tabela", "count"), linhas=("linhas", "sum"), bytes=("bytes", "sum")).reindex(["stg_cad", "stg_mov", "int_cad", "int_mov", "dim", "fct", "agg", "ctl"]).dropna()
    t += "### 1.1 Linhas e tamanho por camada (PostgreSQL)\n\n" + tabela_md(
        ["camada", "tabelas com dados", "linhas", "tamanho (MB)"], [[c.upper(), fmt(int(r.tabelas)), fmt(int(r.linhas)), fmt(r.bytes / 1e6)] for c, r in g.iterrows()])
    t += f"\nTotal: {fmt(int(tab.linhas.sum()))} linhas e {fmt(tab.bytes.sum() / 1e9)} GB.\n"
    maiores = tab[~tab.camada.isin(["stg_cad", "stg_mov"])].sort_values("bytes", ascending=False).head(12)
    t += "\n### 1.2 Maiores tabelas do DW (fora as stages)\n\n" + tabela_md(["tabela", "linhas", "MB"], [[r.tabela, fmt(int(r.linhas)), fmt(r.bytes / 1e6)] for r in maiores.itertuples()])

    t += "\n### 1.3 Tempo por tipo de carga\n\n"
    t += "Na carga inicial os modelos incrementais são criados do zero (o merge só acontece na carga diária, seção 2).\n\n"
    t += tabela_de_tempos(ini)
    top = ini.sort_values("segundos", ascending=False).head(12)
    t += "\nModelos mais lentos:\n\n" + tabela_md(["modelo", "tipo", "segundos"], [[r.modelo, r.tipo, fmt(float(r.segundos))] for r in top.itertuples()])
    t += f"\nSoma dos tempos dos modelos: {fmt(float(ini.segundos.sum()))} s (o dbt rodou 4 em paralelo).\n"

    # estimativa do espaço para as 27 UFs
    cat = pd.read_csv(f"{config.PASTA_ORIGEM}/_catalogo.csv").fillna("")
    cat = cat[cat.sistema != "DOMINIO"]
    fator = {}
    for s, grupo in cat.groupby("sistema"):
        fator[s] = grupo.linhas.sum() / max(grupo[grupo.uf == "RR"].linhas.sum(), 1)
    tab["sistema"] = tab.tabela.map(lambda x: sistema_da_tabela(x.split(".")[1]))
    escalavel = tab[tab.sistema.notna() & ~tab.camada.isin(["ctl", "dim"])].copy()
    escalavel["estimado"] = escalavel.apply(lambda r: r.bytes * fator[r.sistema], axis=1)
    fixo = tab[~tab.index.isin(escalavel.index)].bytes.sum()
    t += "\n### 1.4 Espaço estimado para as 27 UFs\n\n"
    t += ("Cada tabela de RR multiplicada pela razão entre as linhas das 27 UFs e as de RR no mesmo sistema; domínios e dimensões ficam como estão. "
          "É uma estimativa aproximada.\n\n")
    t += tabela_md(["sistema", "fator (27 UFs / RR)"], [[s, fmt(float(f))] for s, f in sorted(fator.items())])
    t += f"\nEstimativa para as 27 UFs: **{fmt((escalavel.estimado.sum() + fixo) / 1e9)} GB** no PostgreSQL (hoje: {fmt(tab.bytes.sum() / 1e9)} GB só com RR).\n"
    return t


def secao_dia(nome_para_tipo):
    arq = f"{PASTA_EXEC}/run_results_dia_20220103_rr.json"
    if not os.path.exists(arq):
        return "\n## 2. Carga diária (03/01/2022)\n\nNão executada.\n"
    dia = tempos_por_modelo(arq, nome_para_tipo)
    antes = json.load(open(f"{PASTA_EXEC}/contagens_carga_inicial.json"))
    depois = json.load(open(f"{PASTA_EXEC}/contagens_depois_dia.json"))
    linhas, tot_delta, tot_ins, tot_upd = [], 0, 0, 0
    for k, v in sorted(depois.items()):
        if not k.startswith(("int_mov.int_mov_", "int_cad.int_cad_")) or "_nac_" in k or "_enr_" in k or "dominio" in k or not k.endswith("_rr"):
            continue
        nome_stage = k.split(".")[1]
        for dw_, st_ in (("int_mov_", "stg_mov_"), ("int_cad_sih_sp_profissional", "stg_mov_sih_sp_profissional"), ("int_cad_", "stg_cad_")):
            if nome_stage.startswith(dw_):
                nome_stage = st_ + nome_stage[len(dw_):] if not dw_.endswith("profissional") else "stg_mov_sih_sp_profissional" + nome_stage[len(dw_):]
                break
        schema_stage = "_".join(nome_stage.split("_")[:2])  # stg_cad ou stg_mov
        stage = depois.get(f"{schema_stage}.{nome_stage}", {"linhas": 0})["linhas"]
        ins = v["linhas"] - antes[k]["linhas"]
        linhas.append((k.split(".")[1], stage, ins, max(stage - ins, 0)))
    for nome, stage, ins, upd in linhas:
        tot_delta, tot_ins, tot_upd = tot_delta + stage, tot_ins + ins, tot_upd + upd
    texto = "\n## 2. Carga diária de RR (03/01/2022)\n\n"
    texto += ("A stage recebeu as linhas com `31/12/2021 < DT_TRANSACAO <= 03/01/2022`, e o dbt rodou os mesmos modelos (merge e delete+insert).\n\n")
    texto += f"Delta total: {fmt(tot_delta)} linhas; inserções: {fmt(tot_ins)}; atualizações: {fmt(tot_upd)}.\n\n"
    principais = sorted(linhas, key=lambda x: -x[1])[:14]
    texto += tabela_md(["tabela do DW (RR)", "delta (stage)", "inserções", "atualizações"], [[n, fmt(s), fmt(i), fmt(u)] for n, s, i, u in principais])
    texto += "\n### Tempo por tipo de carga\n\n" + tabela_de_tempos(dia)
    texto += "\nModelos mais lentos:\n\n" + tabela_md(["modelo", "tipo", "segundos"], [[r.modelo, r.tipo, fmt(float(r.segundos))] for r in dia.sort_values("segundos", ascending=False).head(10).itertuples()])
    texto += f"\nSoma dos tempos dos modelos: {fmt(float(dia.segundos.sum()))} s.\n"
    return texto


def main():
    nome_para_tipo = tipos_de_carga()
    texto = "# Resultados do DW\n\nGerado por `17_medir_dw.py` a partir das execuções em RR.\n\n"
    texto += secao_execucao(nome_para_tipo) + secao_dia(nome_para_tipo)
    with open("docs/resultados_dw.md", "w", encoding="utf-8") as f:
        f.write(texto)
    print("docs/resultados_dw.md escrito")


if __name__ == "__main__":
    main()
