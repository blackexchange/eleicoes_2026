# Tasks

## 1. Extração de Eventos Biométricos e Horários nos Logs da Urna

- [x] 1.1 Atualizar `src/analyze_voting_flow.py` para extrair eventos de habilitação biométrica (`[biométrica]`) e habilitação manual por mesário (ano de nascimento / dado pessoal) por seção, verificando a contagem em uma amostra de seções.
- [x] 1.2 Adicionar detecção de votos computados a partir das 17:00:00 (`votos_pos_17h`) em `src/analyze_voting_flow.py`, verificando a identificação de votos tardios.
- [x] 1.3 Executar o processamento dos logs e atualizar a tabela de fluxo no DuckDB com os novos campos biométricos e horários, verificando a presença das colunas preenchidas via query SQL.

## 2. Consolidação de Dados e Modelagem do Score de Anomalia

- [x] 2.1 Criar rotina de cruzamento entre as métricas dos logs, votação nominal para presidente (`votacao_secao_2026_BA`) e dados de aptos/abstenção (`locais_votacao_2026_BA`) por seção.
- [x] 2.2 Implementar a fórmula do Score Composto de Anomalia Operacional (baixa abstenção + alta liberação manual + votos pós-17h + unilateralidade de votos) e validar a distribuição dos scores no DuckDB.
- [x] 2.3 Exportar a base consolidada de auditoria para `data/processed/google_maps/auditoria_secoes_anomalias_BA_2026.csv` e verificar a integridade das seções exportadas.

## 3. Interface Visual e Auditoria Granular no Dashboard

- [x] 3.1 Adicionar a aba "Auditoria por Seção Eleitoral" no modal analítico do dashboard em `src/export_google_maps.py`.
- [x] 3.2 Implementar tabela interativa de seções com paginação, busca e colunas detalhadas (Município, Zona, Seção, Escola, Aptos, Comparecimento, Abstenção, % Manual, Votos Pós-17h, Votos 13/22 e Score).
- [x] 3.3 Adicionar seletores de filtros de anomalia (Abstenção $\le 10\%$, Liberação Manual $\ge 20\%$, Votação Pós-17h, Score Elevado) e integrar o botão "Ver no Mapa" para focar no colégio correspondente.
- [x] 3.4 Adicionar cards de resumo e gráficos comparativos (ex: votação dos candidatos por faixa de liberação manual e por horário de votação).

## 4. Integração, Validação e Geração dos Artefatos

- [x] 4.1 Executar a compilação completa via `python src/export_google_maps.py` gerando os mapas e dashboards atualizados em `data/processed/google_maps/` e `docs/index.html`.
- [x] 4.2 Validar a visualização e filtragem interativa no navegador para garantir desempenho e responsividade.
