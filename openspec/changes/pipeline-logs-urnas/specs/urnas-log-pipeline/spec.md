# Spec Delta: urnas-log-pipeline

## Purpose

Permite baixar, descompactar, analisar e consolidar em formato colunar analítico os arquivos de log de eventos das urnas eletrônicas (`LOGJEZ` contendo `logd.dat`) disponibilizados pelo Tribunal Superior Eleitoral (TSE).

## ADDED Requirements

### Requirement: Download Automatizado de LOGJEZ com Cache Local
O sistema SHALL permitir o download resiliente e assíncrono dos arquivos `.logjez` a partir dos repositórios oficiais do TSE para uma combinação parametrizada de ano, turno, UF, município, zona e seção.

#### Scenario: Download com filtros especificados
- **WHEN** o usuário executa o pipeline informando `--ano 2022 --turno 1 --uf BA`
- **THEN** o sistema descobre os endpoints válidos das seções e faz o download dos arquivos `.logjez` correspondentes salvando no diretório de dados brutos.

#### Scenario: Uso de cache para evitar requisições redundantes
- **WHEN** um arquivo `.logjez` de uma seção já existir localmente e for íntegro
- **THEN** o sistema pula o download dessa seção e utiliza o arquivo local no processamento.

### Requirement: Descompactação e Parsing de Eventos do logd.dat
O sistema SHALL descompactar os arquivos `.logjez` e decodificar os registros contidos no arquivo `logd.dat`, extraindo timestamp, severidade, código do evento e mensagem descritiva.

#### Scenario: Parsing com extração completa de campos
- **WHEN** um arquivo `logd.dat` válido é processado
- **THEN** o sistema extrai cada linha como um registro contendo data, hora com precisão de segundos, código de evento, severidade, texto descritivo e metadados de localização (UF, município, zona, seção).

#### Scenario: Resiliência contra arquivos corrompidos
- **WHEN** um arquivo `.logjez` estiver corrompido ou truncado
- **THEN** o sistema registra o erro no log de execução, marca o arquivo como inválido e continua o processamento das demais seções sem interromper o lote.

### Requirement: Exportação e Armazenamento Analítico
O sistema SHALL consolidar os eventos parseados em datasets otimizados para consulta analítica em formatos Parquet, DuckDB e CSV.

#### Scenario: Exportação colunar particionada
- **WHEN** o processamento de um lote de seções é finalizado
- **THEN** o sistema grava os dados em arquivos Parquet particionados por UF e Turno ou em uma tabela DuckDB indexada por zona e seção.

### Requirement: Extração de Métricas de Votação e Auditoria
O sistema SHALL calcular métricas operacionais agregadas a partir dos eventos registrados na urna, incluindo tempo médio de votação por eleitor e horários de pico.

#### Scenario: Cálculo de tempo de votação por eleitor
- **WHEN** são detectados pares de eventos de habilitação do eleitor e confirmação de voto
- **THEN** o sistema calcula o tempo em segundos gasto por cada eleitor na cabine de votação e calcula a média e desvio padrão da seção.
