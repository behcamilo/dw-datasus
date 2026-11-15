#!/usr/bin/env bash
# Constrói o DW no Linux, uma etapa por vez, na ordem abaixo (detalhes no README).
#
# Uso:  ./executar.sh <etapa> [data]
#   ambiente             cria .venv (scripts) e .venv-dbt (dbt) e sobe o PostgreSQL (docker compose)
#   baixar               baixa o recorte do FTP e os domínios: confirma uma vez e baixa em PARTES processos (padrão 8; pode ser retomado)
#   origem               gera a origem simulada das 27 UFs em 4 processos e valida (scripts 05 a 09)
#   estrutura            gera os modelos do DW, valida com dbt parse, gera o ctl e carrega os seeds (10 a 14)
#   carga_inicial        stages (PARTES processos, padrão 4) + dbt (THREADS_DBT, padrão 8) com tudo até 31/12/2021, nas 27 UFs
#   retomar_carga_inicial  se o dbt da carga inicial falhou: roda só os modelos que falharam ou ficaram para trás
#   dia AAAA-MM-DD       um dia de carga diária (delta + merge), nas 27 UFs
#
# Cada etapa grava o log em dados/logs/<etapa>.log e para no primeiro erro.

set -euo pipefail
cd "$(dirname "$0")"

PY=".venv/bin/python -X utf8 -u"   # -u: o log mostra o andamento na hora, não só no fim
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
    [ -f scripts/config_local.py ] || { echo "Falta scripts/config_local.py: copie scripts/config_local.exemplo.py e troque o sal."; exit 1; }
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

gerar_origem_das_ufs() {
    $PY scripts/05_gerar_origem_sih.py --ufs "$@" && $PY scripts/07_gerar_origem_cnes.py --ufs "$@"
}

origem() {
    # Grupos de UFs com volume parecido no manifesto; SP sozinho já é 1/4 do total.
    # Cada UF só lê os próprios arquivos, então o paralelismo não muda o resultado (o 09 confere).
    # Memória para 32 GB de RAM; se faltar, o DuckDB usa o disco.
    local grupos=("SP" "MG SC GO ES PB RN RO AC AP" "RJ BA CE PA DF MS AL TO" "PR RS PE MA MT AM PI SE RR") pids=()
    echo "== $(date '+%F %T')  SIH e CNES em ${#grupos[@]} processos (andamento em $LOGS/origem_parte_K.log)" | tee -a "$LOGS/origem.log"
    for i in "${!grupos[@]}"; do
        local memoria=3GB; [ "${grupos[$i]}" = "SP" ] && memoria=8GB
        MEMORIA_DUCKDB=$memoria gerar_origem_das_ufs ${grupos[$i]} > "$LOGS/origem_parte_$((i + 1)).log" 2>&1 &
        pids+=($!)
    done
    for pid in "${pids[@]}"; do
        wait "$pid" || { echo "A geração da origem falhou: veja $LOGS/origem_parte_*.log" | tee -a "$LOGS/origem.log"; exit 1; }
    done
    registrar origem $PY scripts/06_gerar_origem_sim_sinasc.py --todas
    registrar origem $PY scripts/08_gerar_origem_dominios.py
    registrar origem $PY scripts/09_validar_origem.py
}

estrutura() {
    registrar estrutura $PY scripts/10_medir_codigos.py
    registrar estrutura $PY scripts/11_gerar_modelos_dbt.py
    registrar estrutura $PY scripts/12_gerar_derivados.py
    registrar estrutura $PY scripts/13_gerar_dim_fct_agg.py
    registrar estrutura dbt_cmd parse
    registrar estrutura $PY scripts/14_gerar_ctl.py
    registrar estrutura dbt_cmd seed
}

carga_inicial() {
    local partes=${PARTES:-4} ufs pids=()
    ufs=$(todas_as_ufs)
    echo "== $(date '+%F %T')  extração em $partes processos (andamento em $LOGS/carga_inicial_extracao_K.log)" | tee -a "$LOGS/carga_inicial.log"
    for k in $(seq 1 "$partes"); do
        $PY scripts/15_extrair_para_stage.py --data-ref 2021-12-31 --carga-inicial --ufs $ufs --parte "$k/$partes" \
            > "$LOGS/carga_inicial_extracao_$k.log" 2>&1 &
        pids+=($!)
    done
    for pid in "${pids[@]}"; do
        wait "$pid" || { echo "A extração falhou: veja $LOGS/carga_inicial_extracao_*.log" | tee -a "$LOGS/carga_inicial.log"; exit 1; }
    done
    registrar carga_inicial dbt_cmd run --vars '{dt_carga: "2021-12-31"}' --threads "${THREADS_DBT:-8}"
    cp dw_dbt/target/run_results.json docs/execucoes/run_results_carga_inicial.json
    finalizar_carga_inicial
}

retomar_carga_inicial() {
    registrar carga_inicial dbt_cmd retry --threads "${THREADS_DBT:-8}"
    cp dw_dbt/target/run_results.json docs/execucoes/run_results_carga_inicial_retomada.json
    finalizar_carga_inicial
}

finalizar_carga_inicial() {
    registrar carga_inicial $PY scripts/16_contar_linhas.py carga_inicial
    # Sem isto, o autovacuum trabalharia nas tabelas novas durante as primeiras cargas diárias e mudaria os tempos medidos.
    registrar carga_inicial docker exec dw_datasus vacuumdb -U dw -d dw --analyze --jobs 8
    registrar carga_inicial docker exec dw_datasus psql -U dw -d dw -c "CHECKPOINT"
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
    ambiente|baixar|origem|estrutura|carga_inicial|retomar_carga_inicial) "$etapa" ;;
    dia) dia "${2:-}" ;;
    *) sed -n '2,14p' "$0"; exit 1 ;;
esac
