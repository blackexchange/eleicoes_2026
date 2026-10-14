# Spec Delta

## Purpose

Permite auditar de forma granular cada seção eleitoral, cruzando eventos operacionais dos logs das urnas (habilitação biométrica vs manual pelo mesário e horário pós-17h) com o comparecimento, abstenção e distribuição de votos por candidato.

## ADDED Requirements

### Requirement: Extração de Métricas Biométricas e Horárias dos Logs de Urna
O sistema SHALL processar o arquivo `logd.dat` de cada urna da eleição e extrair contadores exatos de eleitores habilitados com biometria, eleitores liberados manualmente pelo mesário com dado pessoal/ano de nascimento e quantidade de votos computados estritamente após as 17:00:00.

#### Scenario: Detecção de habilitações biométricas e manuais
- **WHEN** o parser processa os eventos de votação de uma seção no dia da eleição
- **THEN** o sistema contabiliza como biometria eventos do tipo `[biométrica]` e como manual eventos de confirmação de ano de nascimento / liberação manual pelo mesário

#### Scenario: Contabilização de votos pós-17h
- **WHEN** um eleitor tem seu voto computado com timestamp igual ou superior a `17:00:00`
- **THEN** o sistema incrementa o contador `votos_pos_17h` daquela seção específica

### Requirement: Cálculo de Indicadores e Score de Anomalia Operacional
O sistema SHALL consolidar os dados da seção (aptos, comparecimento, abstenção e votos nominais de presidente) com as métricas do log da urna, calculando a taxa de liberação manual e um Score Composto de Anomalia Operacional.

#### Scenario: Identificação de seção de alto risco operacional
- **WHEN** uma seção apresenta abstenção $\le 10\%$, taxa de liberação manual $\ge 20\%$ e votos registrados após as 17h00
- **THEN** o sistema classifica a seção com flag de anomalia elevada e calcula seu score composto

#### Scenario: Seção com fluxo normal
- **WHEN** uma seção apresenta abstenção dentro da média municipal e liberação manual inferior a 10% sem votos pós-17h
- **THEN** o sistema classifica a seção como padrão operacional regular

### Requirement: Painel e Filtros de Auditoria por Seção no Dashboard
O sistema SHALL prover interface interativa no dashboard com aba dedicada à auditoria de seções, permitindo buscar, ordenar e filtrar seções eleitorais por município, zona, colégio e limiares de anomalia (abstenção atípica, liberação manual e votos pós-17h).

#### Scenario: Filtragem por baixa abstenção e liberação manual
- **WHEN** o usuário seleciona o filtro de abstenção $\le 10\%$ e liberação manual elevada
- **THEN** a tabela e o mapa isolam exclusivamente as seções que atendem a ambos os critérios simultaneamente

#### Scenario: Inspeção detalhada da seção
- **WHEN** o usuário clica em uma seção na tabela de auditoria
- **THEN** o sistema exibe os detalhes da urna: horários de primeiro/último voto, total pós-17h, taxa de biometria e votação nominal dos candidatos

### Requirement: Exportação de Base de Dados Consolidada de Auditoria
O sistema SHALL exportar os dados tabulares auditados de todas as seções eleitorais em formato CSV e persistir a tabela consolidada no banco de dados DuckDB do projeto.

#### Scenario: Geração do arquivo CSV de auditoria
- **WHEN** o pipeline de exportação de mapas e dados é executado
- **THEN** o arquivo `auditoria_secoes_anomalias_BA_2026.csv` é gerado contendo todas as seções com métricas de votos, horários e biometria
