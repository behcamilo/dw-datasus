# DW DATASUS

Data warehouse em PostgreSQL 17 + dbt construído com dados públicos do DATASUS (FTP oficial).
Os arquivos são transformados num sistema de origem simulado e carregados em camadas (stage, cadastro, movimento, dimensão e fato),
com carga inicial e carga diária. Recorte: 2021–2022, 27 UFs, SIH (RD, SP, RJ), CNES (13 grupos), SIM e SINASC.

Como o DW é construído: `docs/desenho_dw.md`. Execução num servidor Linux: `docs/execucao_remota.md`.

## Preparação

```
python -m venv .venv && .venv/bin/pip install -r requirements.txt
python -m venv .venv-dbt && .venv-dbt/bin/pip install -r requirements-dbt.txt     # dbt em ambiente separado
cp scripts/config_local.exemplo.py scripts/config_local.py                        # e preencha o sal (instruções no arquivo)
docker compose up -d                                                              # PostgreSQL na porta 5433
```

No Windows, troque `.venv/bin/` por `.venv\Scripts\`. O `scripts/config_local.py` fica fora do git: tem o sal do hash de dados pessoais
(não pode mudar depois de gerar a origem) e pode trocar qualquer valor do `config.py`.

## Execução

Com `./executar.sh <etapa>` (Linux) ou script a script, a partir de qualquer pasta:

| etapa | scripts | o que faz |
|---|---|---|
| `baixar` | 01, 02, 03 | lista o FTP, baixa o recorte e os domínios em `dados/raw/` (retomável) |
| `origem` | 05 a 09 | gera a origem simulada em `dados/origem/` e valida (`docs/origem_simulada.md`) |
| `estrutura` | 10 a 14 | gera os modelos dbt, valida com `dbt parse`, gera o catálogo (ctl) |
| `carga_inicial` | 15, 16 | stages e `dbt run` com tudo até 31/12/2021 |
| `dia AAAA-MM-DD` | 15, 16 | um dia de carga diária |

Exemplo só com RR:

```
python scripts/15_extrair_para_stage.py --data-ref 2021-12-31 --carga-inicial
cd dw_dbt && dbt run --profiles-dir . --select tag:rr tag:dominio tag:nacional --vars '{ufs: [rr], dt_carga: "2021-12-31"}'
```

Medições das execuções: `python scripts/17_medir_dw.py` (`docs/resultados_dw.md`).

## Scripts

| script | o que faz |
|---|---|
| `01_inventario.py` | lista os arquivos do recorte no FTP |
| `02_baixar.py` | baixa os `.dbc`, converte para Parquet e registra no manifesto (`--parte K/N` para rodar em paralelo) |
| `03_baixar_dominio.py` | baixa SIGTAP, CID-10, IBGE e tabelas do TabWin |
| `04_dominios_usados.py` | opcional: liga cada coluna à sua tabela de domínio (`docs/dominios_usados.csv`, já versionado) |
| `05` a `08_gerar_origem_*.py` | geram a origem simulada (SIH; SIM e SINASC; CNES; domínios) |
| `09_validar_origem.py` | confere linhas, chaves, registro pai, dados pessoais e determinismo |
| `10_medir_codigos.py` | escolhe as colunas de código que o movimento confere no cadastro |
| `11_gerar_modelos_dbt.py` | stages, cadastros e movimentos por UF e nacionais |
| `12_gerar_derivados.py` | cadeias por UF (estabelecimento, profissional), classificados e resumos |
| `13_gerar_dim_fct_agg.py` | dimensões, fatos e agregados |
| `14_gerar_ctl.py` | catálogo de tabelas e dependências a partir do `manifest.json` do dbt |
| `15_extrair_para_stage.py` | carrega as stages (carga inicial ou delta do dia) |
| `16_contar_linhas.py` | linhas e tamanho de cada tabela |
| `17_medir_dw.py` | resume as execuções |

Módulos de apoio: `config.py` (todas as configurações), `origem.py`, `dw.py`, `manifesto.py`, `ftp_datasus.py`.

## Pastas

```
scripts/        scripts e configurações
dw_dbt/         projeto dbt (macros e models/manual/; os demais modelos são gerados)
docker/init/    criação dos schemas e da tabela de log
docs/           desenho, validação da origem, resultados e tabelas de apoio (mapa de assuntos, domínios)
dados/          fora do git, exceto os manifestos: raw/, origem/, logs/
```
