# Design: Urnas Log Pipeline

## Context

Para viabilizar análises temporais e auditoria do comportamento de votação nas urnas eletrônicas, o sistema precisa processar arquivos brutos `LOGJEZ` distribuídos na infraestrutura de dados abertos do TSE. A estrutura segue hierarquia por ano/eleição/turno/UF/município/zona/seção. Veja [proposal.md](file:///d:/Projetos/IA/eleicoes_2026/openspec/changes/pipeline-logs-urnas/proposal.md) para a motivação completa.

## Goals / Non-Goals

**Goals:**
- Implementar um cliente assíncrono para descoberta e download dos arquivos `.logjez` do TSE.
- Desenvolver um parser de alta performance em Python para descompactar e processar streams de texto de `logd.dat`.
- Estruturar os dados extraídos em esquema analítico tabular exportável para Parquet, DuckDB e CSV.
- Criar módulo de cálculo de métricas: tempo de permanência na cabine, contagem de votos/hora e registros de falhas/reinicializações.
- CLI amigável para execuções parciais (uma seção ou município) ou em lote (estado completo).

**Non-Goals:**
- Decodificação de arquivos criptográficos de assinatura digital do TSE (`.vsec`, `.chv`).
- Processamento de arquivos `.bu` (Boletim de Urna) ou `.rdv` (Registro Digital do Voto) nesta fase inicial.
- Interface gráfica web (o foco inicial é CLI e pipeline de dados).

## Decisions

### 1. Engine de Armazenamento: Parquet & DuckDB
- **Decisão:** Utilizar formato colunar Apache Parquet com integração direta ao DuckDB.
- **Racional:** Os arquivos de log de um estado inteiro como a Bahia geram dezenas de milhões de linhas de eventos. Parquet e DuckDB permitem compressão de ~85% e queries SQL analíticas em milissegundos sem necessidade de banco de dados servidor dedicado.
- **Alternativas consideradas:** SQLite (mais lento para agregações em larga escala) e PostgreSQL (dependência externa de infraestrutura).

### 2. Concorrência de Download: `httpx` / `asyncio` com Semáforo
- **Decisão:** Utilizar `asyncio` com semáforo configurável (padrão 10 conexões simultâneas) e retries exponenciais.
- **Racional:** Evita bloqueios de taxa (rate limiting/HTTP 429) nos servidores do TSE e otimiza o tempo de download de milhares de arquivos.
- **Alternativas consideradas:** `requests` síncrono (muito lento para lotes estaduais).

### 3. Estrutura Modular do Projeto
```
src/
  ├── pipeline.py          # Orquestrador do pipeline CLI
  ├── downloader.py        # Descoberta de URLs e download com cache
  ├── parser.py            # Descompactador .logjez e extrator de logd.dat
  ├── storage.py           # Gravador Parquet / DuckDB / CSV
  └── metrics.py           # Agregações de tempo de voto e anomalias
```

## Risks / Trade-offs

- **[Mudança de estrutura de URLs do TSE entre anos eleitorais]** → *Mitigação:* Isolar a lógica de resolução de URLs em adaptadores versionados (ex: `URLProvider2022`, `URLProvider2026`).
- **[Volume elevado de I/O em disco na descompactação]** → *Mitigação:* Processar arquivos `.logjez` em memória através de `io.BytesIO` / `zipfile` / `tarfile` sempre que possível, sem gravar temporários desnecessários em disco.
- **[Quedas intermitentes de conexão nos servidores públicos]** → *Mitigação:* Implementar política de retries com backoff exponencial e persistência de status de download em banco de cache SQLite/JSON.
