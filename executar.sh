#!/usr/bin/env bash
# Executa o DW num servidor Linux, uma etapa por vez (passo a passo em docs/execucao_remota.md).
#
# Uso:  ./executar.sh <etapa> [data]
#   ambiente             cria .venv (scripts) e .venv-dbt (dbt) e sobe o PostgreSQL (docker compose)
#   baixar               baixa o recorte do FTP e os domínios: confirma uma vez e baixa em PARTES processos (padrão 8; pode ser retomado)
#   origem               gera a origem simulada das 27 UFs e valida (scripts 05 a 09)
#   estrutura            gera os modelos do DW, valida com dbt parse, gera o ctl e carrega os seeds (10 a 14)
#   carga_inicial        stages + dbt com tudo até 31/12/2021, nas 27 UFs
#   dia AAAA-MM-DD       um dia de carga diária (delta + merge), nas 27 UFs
#
# Rode dentro do tmux, para continuar se a conexão SSH cair. Cada etapa grava o log em dados/logs/<etapa>.log e para no primeiro erro.

set -euo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python -X utf8"
DBT=".venv-dbt/bin/dbt"
LOGS=dados/logs
mkdir -p "$LOGS" docs/execucoes

# Roda um comando mostrando a saída na tela e guardando no log da etapa.
registrar() {
    local log="$LOGS/$1.log"; shift
    echo "== $(date '+%F %T')  $*" | tee -a "$log"
    "$@" 2>&1 | tee -a "$log"
}

todas_as_ufs() { $PY -c "import sys; sys.path.insert(0, 'scripts'); import config; print(' '.join(config.UFS))"; }

dbt_cmd() { (cd dw_dbt && ../$DBT "$@" --profiles-dir .); }

ambiente() {
    [ -f scripts/config_local.py ] || { echo "Falta scripts/config_local.py: copie o do PC original (o sal tem que ser o MESMO)."; exit 1; }
    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    python3 -m venv .venv-dbt && .venv-dbt/bin/pip install -r requirements-dbt.txt
    docker compose up -d
}

baixar() {
    local partes=${PARTES:-8}   # processos em paralelo (a conversão .dbc -> Parquet usa 1 núcleo por processo)
    registrar baixar $PY scripts/01_inventario.py
    # mostra quantos arquivos e MB faltam (respondendo "não"), e só então pergunta
    (echo n | $PY scripts/02_baixar.py --recorte 2>&1 || true) | grep -E "arquivos no recorte" | tee -a "$LOGS/baixar.log"  # o "n" faz o 02 sair com erro: esperado
    read -r -p "Baixar com $partes processos em paralelo? [s/N] " resposta
    [ "$resposta" = "s" ] || { echo "Cancelado."; exit 1; }
    for k in $(seq 1 "$partes"); do
        $PY scripts/02_baixar.py --recorte --confirmado --parte "$k/$partes" > "$LOGS/baixar_parte_$k.log" 2>&1 &
    done
    wait   # espera as partes; o andamento de cada uma está em dados/logs/baixar_parte_K.log
    # conferência: roda de novo em série; tem que dizer "0 a baixar" (se alguma parte falhou, ela baixa o que faltou)
    registrar baixar $PY scripts/02_baixar.py --recorte --confirmado
    registrar baixar $PY scripts/03_baixar_dominio.py
}

origem() {
    # SIH-SP e CNES-PF são grandes: o DuckDB pode usar mais memória (MEMORIA_DUCKDB=10GB ./executar.sh origem)
    registrar origem $PY scripts/05_gerar_origem_sih.py --todas
    registrar origem $PY scripts/06_gerar_origem_sim_sinasc.py --todas
    registrar origem $PY scripts/07_gerar_origem_cnes.py --todas
    registrar origem $PY scripts/08_gerar_origem_dominios.py
    registrar origem $PY scripts/09_validar_origem.py
}

estrutura() {
    registrar estrutura $PY scripts/10_medir_codigos.py
    registrar estrutura $PY scripts/11_gerar_modelos_dbt.py
    registrar estrutura $PY scripts/12_gerar_derivados.py
    registrar estrutura $PY scripts/13_gerar_dim_fato_agg.py
    registrar estrutura dbt_cmd parse
    registrar estrutura $PY scripts/14_gerar_ctl.py
    registrar estrutura dbt_cmd seed
}

carga_inicial() {
    registrar carga_inicial $PY scripts/15_extrair_para_stage.py --data-ref 2021-12-31 --carga-inicial --ufs $(todas_as_ufs)
    registrar carga_inicial dbt_cmd run --vars '{dt_carga: "2021-12-31"}'
    cp dw_dbt/target/run_results.json docs/execucoes/run_results_carga_inicial.json
    registrar carga_inicial $PY scripts/16_contar_linhas.py carga_inicial
}

dia() {
    local data=${1:?informe a data: ./executar.sh dia AAAA-MM-DD}
    registrar "dia_$data" $PY scripts/15_extrair_para_stage.py --data-ref "$data" --ufs $(todas_as_ufs)
    registrar "dia_$data" dbt_cmd run --vars "{dt_carga: \"$data\"}"
    cp dw_dbt/target/run_results.json "docs/execucoes/run_results_dia_${data//-/}.json"
    registrar "dia_$data" $PY scripts/16_contar_linhas.py "dia_${data//-/}"
}

etapa=${1:-}
case "$etapa" in
    ambiente|baixar|origem|estrutura|carga_inicial) "$etapa" ;;
    dia) dia "${2:-}" ;;
    *) sed -n '2,13p' "$0"; exit 1 ;;
esac
