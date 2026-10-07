# Proposal

## Why

A análise aprofundada do comportamento eleitoral, auditoria e fluxos de votação depende do acesso granular aos logs gerados pelas urnas eletrônicas (`LOGJEZ`). Atualmente, os arquivos de log do TSE estão distribuídos em múltiplos endpoints por Eleição, Turno, UF, Município, Zona e Seção, sem um pipeline automatizado para download em lote, descompactação, parsing do arquivo `logd.dat` e consolidação em formatos analíticos otimizados (Parquet/DuckDB/CSV).

Esta mudança cria um pipeline de dados em Python focado exclusivamente na extração, processamento e estruturação dos arquivos `LOGJEZ` do TSE.

## What Changes

- Implementação do módulo `tse_downloader` com suporte a URLs oficiais do TSE, download assíncrono/concorrente, controle de rate limit, retries e cache local para evitar downloads duplicados.
- Implementação do módulo `logjez_parser` para descompactar os containers `.logjez` e decodificar os registros do `logd.dat` (timestamps, código de eventos, severidade, mensagens).
- Criação de esquema de dados estruturado e exportação para formatos colunares (Parquet, DuckDB) e CSV.
- Interface de linha de comando (CLI) parametrizável por `--ano`, `--eleicao`, `--turno`, `--uf`, `--municipio`, `--zona`, `--secao`.
- Módulo de extração de métricas operacionais (tempo médio de votação por eleitor, fluxo de votação por hora e detecção de anomalias/travamentos).

## Capabilities

### New Capabilities
- `urnas-log-pipeline`: Pipeline de extração, descompactação, parsing de `LOGJEZ` do TSE e consolidação analítica de eventos por eleição, turno e UF.

### Modified Capabilities
*(Nenhuma capacidade modificada - repositório inicial)*

## Impact

- Código Python modular sob `src/` (downloader, parser, storage, cli).
- Dependências: `httpx` / `aiohttp`, `duckdb` / `pyarrow`, `tqdm`, `click` ou `argparse`.
- Saída de dados estruturados em diretório configurável (`data/logs/` e `data/processed/`).
