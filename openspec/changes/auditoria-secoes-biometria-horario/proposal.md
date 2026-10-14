# Proposal

## Why

Auditorias eleitorais restritas exclusivamente à análise de código-fonte de sistemas deixam desassistida a principal frente de vulnerabilidade operacional: as ocorrências físicas nas mesas receptoras de votos durante o dia da eleição. A análise aprofundada de dados dos logs oficiais das urnas eletrônicas (`logd.dat`) revela que seções com comparecimento atipicamente elevado (abstenção abaixo de 5% a 10%), somadas a altas taxas de habilitação manual pelo mesário (sem reconhecimento biométrico) e registros de votação ocorrendo após as 17h00, configuram potenciais anomalias que demandam escrutínio detalhado e fiscalização presencial.

Faz-se necessária uma nova capacidade no pipeline e dashboard do projeto que processe, rankeie e evidencie de forma granular cada seção eleitoral da Bahia (e de outros estados analisados), permitindo investigar o impacto da fiscalização nas mesas e a correlação entre a liberação biométrica manual e discrepâncias nos resultados para presidente.

## What Changes

- **Extração de Métricas de Habilitação e Horário nos Logs da Urna (`logd.dat`)**:
  - Contabilizar por seção: total de eleitores habilitados via biometria com sucesso (`[biométrica]`).
  - Contabilizar por seção: total de eleitores liberados manualmente pelo mesário (código de ano de nascimento / dado pessoal após falha biométrica ou eleitor sem biometria).
  - Contabilizar por seção: total de eleitores que votaram estritamente após as 17h00 (horário oficial de encerramento dos portões).
  - Calcular o percentual de habilitações manuais sobre o total de votantes da seção.
- **Índice de Suspeita / Anomalia Operacional por Seção (Score de Anomalia)**:
  - Desenvolvimento de métrica composta ponderando:
    1. Abstenção atipicamente baixa (comparecimento $\ge 90\%$ ou abstenção $\le 10\%$).
    2. Elevada taxa de liberação manual sem biometria ($\ge 20\%$ ou $\ge 30\%$).
    3. Existência de votos registrados após as 17h00.
    4. Concentração desproporcional de votos para um candidato ($\ge 80\%$ ou $\ge 90\%$).
- **Módulo Granular de Auditoria por Seção no Dashboard Interativo**:
  - Nova visualização analítica focada em **Seções Eleitorais**, complementando a visão de Locais de Votação (Colégios) e Zonas.
  - Filtros interativos para isolar seções com:
    - *Abstenção Atípica ($\le 10\%$)*;
    - *Liberação Manual Elevada pelo Mesário*;
    - *Votação Pós-17h*;
    - *Filtro Combinado (Anomalia Operacional Completa)*.
  - Gráficos comparativos de distribuição de votos: votação em seções com 100% de biometria vs. seções com alta taxa de liberação manual.
  - Tabela detalhada com busca por Zona/Seção/Município/Colégio, com detalhamento dos horários de início e encerramento, primeiro e último voto, e botão para inspecionar no mapa.
- **Estruturação de Dados e Exportação de Relatórios de Auditoria**:
  - Geração de tabela `auditoria_secoes_BA_2026` em DuckDB.
  - Exportação de CSV completo de auditoria por seção para pesquisadores e auditores independentes.

## Capabilities

### New Capabilities
- `auditoria-secoes-eleitorais`: Auditoria granular e detecção de anomalias por seção eleitoral, cruzando abstenção atípica, taxa de habilitação manual pelo mesário (sem biometria) e votos computados após as 17h com o resultado eleitoral.

### Modified Capabilities
<!-- Nenhuma capacidade existente tem requisitos alterados -->

## Impact

- **Código e Scripts**:
  - `src/analyze_voting_flow.py`: ampliação do analisador de logs `.logjez` para capturar eventos de habilitação manual/biométrica e votos pós-17h.
  - `src/export_google_maps.py`: consolidação dos dados de seções com votos nominais (`votacao_secao_2026_BA`) e integração da nova aba analítica e filtros no dashboard HTML.
- **Banco de Dados (DuckDB)**:
  - Nova agregação de seções combinando `fluxo_votacao_urnas_BA_2026`, `votacao_secao_2026_BA`, `locais_votacao_2026_BA` e perfil biométrico.
- **Arquivos de Saída**:
  - `data/processed/google_maps/auditoria_secoes_anomalias_BA_2026.csv`
  - Atualização do `mapa_interativo_urnas_BA_2026.html` e `docs/index.html`.
