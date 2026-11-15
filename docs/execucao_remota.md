# Execução num servidor Linux

Para as 27 UFs, num servidor acessado por SSH. Cada etapa do `executar.sh` grava o log em `dados/logs/<etapa>.log` e para no primeiro erro.

## Espaço

| item | tamanho aproximado |
|---|---|
| `dados/raw` | 28 GB |
| `dados/origem` | 17 GB |
| PostgreSQL (27 UFs) | 420 GB (estimado a partir de uma carga de teste só com RR) |

O volume do Docker fica em `/var/lib/docker`: confira o espaço com `df -h /var/lib/docker`.

## Preparar

```bash
git clone <repositório> dw && cd dw
# copie do outro computador o scripts/config_local.py (o mesmo sal)
sudo apt install python3-venv tmux
chmod +x executar.sh
./executar.sh ambiente        # .venv, .venv-dbt e PostgreSQL
```

## Rodar

Dentro do `tmux`, para a execução continuar se a conexão cair (`tmux attach -t dw` para voltar; `Ctrl+b d` para sair sem parar):

```bash
tmux new -s dw
./executar.sh baixar                       # confirma uma vez e baixa em 8 processos (PARTES=N muda)
MEMORIA_DUCKDB=10GB ./executar.sh origem    # a etapa mais demorada
./executar.sh estrutura
./executar.sh carga_inicial
./executar.sh dia 2022-01-03               # um dia por vez, em ordem
```

## Conferir

- `docs/origem_simulada.md` deve dizer "TODAS as validações passaram".
- O download grava o sha256 de cada arquivo em `dados/manifesto.csv`; se o DATASUS tiver republicado algum, as duas versões ficam registradas.
- `docs/execucoes/` guarda os tempos (`run_results_*.json`) e as contagens de cada carga.
