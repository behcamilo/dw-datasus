# Desenho do DW

## Visão geral

```
FTP do DATASUS -> dados/raw -> dados/origem -> stages (stg_cad, stg_mov) -> DW (int_cad, int_mov -> dim, fct, agg)
  scripts 01-03     Parquet    origem simulada     script 15            dbt (modelos gerados pelos scripts 11, 12, 13)
```

- **Recorte:** 2021–2022, 27 UFs. SIH (RD internações, SP atos profissionais, RJ AIH rejeitadas), CNES (13 grupos), SIM (óbitos), SINASC (nascimentos).
  2021 é a carga inicial; 2022 é simulado dia a dia.
- Todo arquivo baixado fica registrado em `dados/manifesto.csv` (sha256 e data), porque o DATASUS pode republicar um arquivo com o mesmo nome.

## Origem simulada

Os arquivos do DATASUS são fotos mensais. Para simular um sistema de origem, cada arquivo vira tabelas por assunto (`docs/mapa_assuntos.csv`),
particionadas por UF e mês, e cada linha ganha `DT_TRANSACAO`, a data em que ela "chega" na origem:

| sistema | DT_TRANSACAO |
|---|---|
| SIH (RD, RJ) | espalhada pelos dias úteis do mês seguinte à competência |
| SIH-SP | a da AIH correspondente |
| SIM, SINASC | data do evento + 30 dias |
| CNES, SIGTAP | 5º dia útil do mês seguinte |
| demais domínios | 31/12/2021 |

- Domínios: uma tabela por arquivo de origem (SIGTAP, CID-10, IBGE, tabelas do TabWin, população). Conversões de data do TabWin ficam fora.
- Dados pessoais: nomes e CPF_AUT saem; documentos de pessoas recebem hash sha256 com um sal guardado fora do git (`scripts/config_local.py`).
- A geração é determinística e validada pelo script 09 (`docs/origem_simulada.md`).

## Camadas

| camada | o que guarda | carga |
|---|---|---|
| stg_cad | foto atual do CNES e dos domínios | script 15 (completa) |
| stg_mov | movimento novo desde a última carga | script 15 (delta) |
| int_cad | cadastros tratados e consolidados | merge |
| int_mov | movimentos tratados, classificados e resumos | merge, completa ou foto |
| dim | dimensões, com o membro `-1` "NÃO INFORMADO" | completa |
| fct, agg | fatos e agregados | completa ou foto |
| ctl | catálogo de tabelas, dependências e log de carga | script 14 / seeds |

Nome das tabelas: `<camada>_<sistema>_<grupo>_<assunto>[_<uf>]`. Toda tabela carregada tem `DT_CARGA` (data de referência da carga).

## Carga

- Data de referência = `DT_CARGA` = dia da execução − 1.
- **Carga inicial** (31/12/2021): leva tudo até a data.
- **Carga diária:** a stage de movimento recebe só as linhas com `DT_TRANSACAO` depois da última carga (o maior `DT_CARGA` da tabela que a consome)
  e até a data de referência. A stage de cadastro recebe a foto mais recente publicada.
- Merge na chave de negócio, com índice único. Atos do SIH-SP e diagnósticos do SIH usam delete+insert pela AIH, porque são reenviados com ela.
- Foto: a tabela guarda um retrato por dia de carga (delete+insert no dia).
- Exclusões na origem são ignoradas.

## Cadastro tratado (int_cad)

O cadastro passa por etapas até um **consolidado**, que é o que o movimento e os fatos usam:

| cadeia | etapas |
|---|---|
| município (nacional) | microrregião → regiões geográficas e UF → região de saúde → classificações (Amazônia Legal, semiárido...) → população → `int_cad_municipio_consolidado` |
| procedimento (nacional) | hierarquia da SIGTAP → financiamento → modalidade e registro → compatibilidades → `int_cad_procedimento_consolidado` (e `int_cad_ocupacao_consolidado`) |
| CID-10 (nacional) | grupo e capítulo → categoria → subcategoria → `int_cad_cid_consolidado` |
| estabelecimento (por UF) | território → gestão → leitos → habilitações → serviços e equipamentos → `int_cad_estabelecimento_consolidado_<uf>` |
| profissional (por UF) | ocupação → vínculo → `int_cad_profissional_consolidado_<uf>` |

Os cadastros do CNES por UF conferem o estabelecimento no cadastro geral nacional (`CADGERBR`).

**Histórico (SCD tipo 2).** Oito cadastros mensais do CNES (`config.HISTORICOS`) guardam uma linha por versão, com `valido_de`, `valido_ate` e `atual`.
Quando a foto nova muda algum campo, o merge fecha a versão anterior e insere a nova. Quem precisa do estado atual lê `where atual`;
os fatos mensais expandem cada versão nos meses em que ela valeu.

## Movimento tratado (int_mov)

- **Por UF:** a stage com os códigos conferidos. Município, CID, procedimento e ocupação são conferidos no cadastro consolidado; o estabelecimento,
  no consolidado da mesma UF; os demais códigos, no domínio. Código inexistente vira `-1` e a linha é mantida.
  Só se confere a coluna em que pelo menos 90% dos valores existem no cadastro (`docs/validacao_codigos.csv`).
- **Nacionais:** união das UFs.
- **Classificados:** internação, AIH rejeitada, óbito e nascimento com as classificações dos cadastros (grupo do procedimento, capítulo da CID...).
- **Derivados:** AIH rejeitada que depois foi aprovada; óbito hospitalar; óbitos infantis e nascidos vivos por município.
- **Resumos mensais:** internações por estabelecimento e óbitos por município (foto).

## Dimensões e fatos

- Dimensões de cada domínio e dos cadastros do CNES (as do CNES têm uma linha por versão), além de algumas escritas à mão (tempo, município, CID...).
- Fatos por grupo e UF, nacionais e fatos que leem outros fatos. Os escritos à mão são internação, óbito, nascimento e as fotos mensais do CNES.
- Os gerados pelo script 13 são consultas simples sobre o DW, que aumentam o número de tabelas e de dependências entre as camadas.
  As fontes são sorteadas com semente fixa; quantidades e distribuições ficam no `config.py`.

## Controle (ctl)

O script 14 lê o `manifest.json` do dbt e gera `ctl_tabela` (uma linha por tabela) e `ctl_lineage` (uma linha por dependência).
`ctl_processo_carga` registra cada extração.

## Limitações

- As chaves das dimensões são `row_number()`, recalculadas a cada carga.
- Quem sai do CNES continua com a última versão marcada como atual (exclusões são ignoradas).
- Os domínios da SIGTAP entram com todas as competências, e o merge relê tudo a cada dia.
- As consolidações nacionais de movimento são recriadas a cada carga.
- Os blocos por dia útil deixam o volume do SIH igual em todos os dias do mês.
- A defasagem de 30 dias do SIM e do SINASC é uma suposição.
- Não há testes do dbt (`dbt test`).
