# Design

## Context

O projeto dispõe do arquivo oficial de logs das urnas da Bahia (`data/logs/bu_imgbu_logjez_rdv_vscmr_2026_1t_BA.zip`), totalizando 35.472 urnas, além das tabelas relacionais em DuckDB com a votação nominal por seção (`votacao_secao_2026_BA`), dados de aptos e comparecimento (`locais_votacao_2026_BA`) e métricas de fluxo (`fluxo_votacao_urnas_BA_2026`).

O módulo atual em `src/analyze_voting_flow.py` calcula os tempos médios de cabine e votos por minuto, mas ainda não contabiliza os eventos específicos de habilitação (biometria aceita vs. liberação manual com ano de nascimento pelo mesário) nem discrimina votos registrados estritamente após o fechamento oficial dos portões (17:00:00).

## Goals / Non-Goals

**Goals:**
- Estender o parser de logs `logd.dat` em `src/analyze_voting_flow.py` para capturar:
  - `qtd_biometria_sucesso`: eleitores habilitados com reconhecimento biométrico.
  - `qtd_liberacao_manual`: eleitores liberados manualmente pelo mesário (código de ano de nascimento / dado pessoal após falha ou ausência de biometria).
  - `pct_liberacao_manual`: percentual de eleitores liberados manualmente na seção.
  - `votos_pos_17h`: contagem de votos computados a partir das 17:00:00.
- Integrar os novos indicadores em DuckDB com a votação nominal de presidente (votos 13, 22, outros) e aptos/abstenção por seção.
- Modelar o **Score de Anomalia Operacional** por seção eleitoral para ranquear mesas com padrões atípicos combinados.
- Implementar no dashboard HTML interativo uma aba dedicada à **Auditoria Detalhada de Seções**, com filtros de suspeita, tabela com ordenação e busca por Zona/Seção/Município/Colégio.
- Exportar arquivo CSV consolidado `auditoria_secoes_anomalias_BA_2026.csv`.

**Non-Goals:**
- Não expor dados confidenciais do eleitor (o log da urna do TSE já é público e anonimizado, sem identificar a escolha de cada cidadão).
- Não inferir juízo de mérito jurídico definitivo no código: o sistema fornece métricas estatísticas, evidências empíricas e ranking de prioridade para fiscalização e auditoria partidária/cidadã.

## Decisions

### Decisão 1: Extração por análise textual concorrente do `logd.dat`
- **Abordagem**: Utilizar o mesmo pipeline concorrente multithread com `ZipFile` e expressões regulares otimizadas em Python.
- **Alternativas consideradas**: Utilizar decodificadores ASN.1 para arquivos `.rdv`.
- **Justificativa**: O `logd.dat` já contém em texto legível as mensagens de log de controle da urna emitidas pelo subsistema `VOTA`, processando mais de 80 urnas por segundo sem dependências externas complexas.

### Decisão 2: Identificação precisa dos eventos de habilitação
- **Habilitação Biométrica**:
  - `Tipo de habilitação do eleitor [biométrica]`
- **Habilitação Manual pelo Mesário**:
  - `Ano de nascimento digitado é igual ao do cadastro`
  - `Solicitação de dado pessoal do eleitor para habilitação manual`
- **Votos Pós-17h**:
  - Timestamp de `O voto do eleitor foi computado` com hora $\ge \text{17:00:00}$ no dia da eleição.

### Decisão 3: Fórmula do Score Composto de Anomalia
- A anomalia é caracterizada pela confluência de fatores atípicos:
  $$\text{Score} = w_{\text{abs}} \cdot f(\text{Abstenção}) + w_{\text{man}} \cdot f(\text{Liberação Manual}) + w_{\text{hor}} \cdot f(\text{Votos Pós-17h}) + w_{\text{pol}} \cdot f(\text{Unilateralidade})$$
  - Seções com abstenção $< 10\%$, liberação manual $> 25\%$, votos após as 17h e votação superior a $80\%$ para um candidato recebem as maiores pontuações de anomalia.

### Decisão 4: Estratégia de exibição no Dashboard HTML
- **Abordagem**: Criar no modal analítico a aba **Auditoria por Seção Eleitoral**, com capacidade de:
  - Filtrar por Município e Zona.
  - Filtrar pelo seletor de Anomalia (Todas, Abstenção $\le 10\%$, Liberação Manual $\ge 20\%$, Votação Pós-17h, ou Anomalia Máxima Combinada).
  - Listar as seções em tabela com botão "Ver Colégio no Mapa".

## Risks / Trade-offs

- **[Volume de 35.472 seções no navegador]** → Para não sobrecarregar a memória do navegador no cliente, o dashboard carregará as seções agregadas sob demanda pelo município selecionado ou exibirá o ranking das seções com maior score de anomalia do estado, além de disponibilizar o CSV completo para download.
- **[Filas legítimas após 17h]** → Zonas urbanas movimentadas podem ter filas naturais após 17h com senha. O cruzamento com a taxa de liberação manual e a taxa de abstenção serve exatamente para distinguir filas legítimas (onde a biometria é coletada normalmente) de anomalias operacionais suspeitas.
