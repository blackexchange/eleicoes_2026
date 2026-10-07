# Tasks

## 1. Configuração do Ambiente e Estrutura

- [x] 1.1 Criar estrutura de diretórios do projeto (`src/`, `data/logs/`, `data/processed/`, `tests/`) e arquivo `requirements.txt` com `httpx`, `duckdb`, `pyarrow`, `tqdm` e `pytest`.
- [x] 1.2 Verificar instalação das dependências executando comando de importação em Python.

## 2. Downloader e Resolução de URLs TSE

- [x] 2.1 Implementar módulo `src/downloader.py` com gerador de URLs de dados abertos do TSE para os arquivos `.logjez`.
- [x] 2.2 Adicionar lógica de download assíncrono com controle de concorrência (`asyncio.Semaphore`), retries com backoff exponencial e cache local.
- [x] 2.3 Criar testes unitários em `tests/test_downloader.py` para validar construção de URLs e comportamento de cache.

## 3. Descompactação e Parser do LOGJEZ

- [x] 3.1 Implementar módulo `src/parser.py` para extrair e descompactar arquivos `logd.dat` a partir de streams/containers `.logjez`.
- [x] 3.2 Criar decodificador linha a linha que extrai timestamp, severidade, código do evento, texto descritivo e metadados de seção.
- [x] 3.3 Criar testes unitários em `tests/test_parser.py` com amostra sintética/real de `logd.dat` verificando extração correta de todos os campos.

## 4. Camada de Armazenamento e Exportação

- [x] 4.1 Implementar módulo `src/storage.py` para salvar eventos processados em formato Apache Parquet e registrar tabelas/views no DuckDB.
- [x] 4.2 Adicionar suporte a exportação para formato CSV e particionamento de arquivos por UF e Turno.
- [x] 4.3 Validar gravação e leitura de dados gerados através de teste em `tests/test_storage.py`.

## 5. Métricas de Auditoria e Interface CLI

- [x] 5.1 Implementar módulo `src/metrics.py` com cálculo de tempo médio de permanência na cabine de votação por eleitor e contagem de votos por faixa de horário.
- [x] 5.2 Implementar CLI unificada em `src/pipeline.py` suportando argumentos `--ano`, `--turno`, `--uf`, `--municipio`, `--zona`, `--secao` e `--format`.
- [x] 5.3 Realizar teste de ponta a ponta (E2E) com uma seção real para validar todo o fluxo de download, parsing, exportação e exibição de métricas.
