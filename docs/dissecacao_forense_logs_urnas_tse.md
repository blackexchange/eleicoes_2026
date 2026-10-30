# DISSECAÇÃO FORENSE DOS LOGS DA URNA ELETRÔNICA DO TSE (`logd.dat` / `.logjez`): LIMITES DE TIMING, ANÁLISE DE EVENTOS E MATRIZ DE IMPACTO AUDITÁVEL

**Documento Técnico de Engenharia de Sistemas Operacionais, Arquitetura de Software e Perícia Forense**  
**Data:** 30 de Outubro de 2026  
**Autor:** Equipe de Inteligência Pericial e Auditoria de Sistemas • Sentinela Juris  
**Bases Analisadas:** Amostra Oficial de Arquivos `.logjez` (TSE 2026 1º e 2º Turnos), Base Consolidada de 35.472 Urnas da Bahia (`data/processed/eleicoes.duckdb`) e Especificações Oficiais do Sistema Operacional Uenux.

---

## SUMÁRIO EXECUTIVO E VEREDITO PERICIAL

Este documento técnico disseca a estrutura interna, o conteúdo de eventos e a capacidade probatória dos arquivos de log gerados pelas urnas eletrônicas brasileiras (`logd.dat`, distribuídos no formato compactado `.logjez`).

A investigação responde com rigor à seguinte questão de auditoria de software:

> **Pergunta:** *É possível utilizar os logs oficiais da urna para realizar um "Timing Attack" (auditoria de latência de clock) e detectar se uma rotina maliciosa em memória volátil realizou o swap de votos entre a digitação do 2º dígito e a confirmação?*

### Veredito Pericial Sintético:

1. **Inviabilidade do Timing Attack de CPU via Log Público:**  
   O arquivo de log público da urna (`logd.dat`) **NÃO possui resolução temporal suficiente** para detectar desvios de microcódigo de CPU em nível de milissegundos ou microsegundos. Os timestamps do log são truncados em **segundos inteiros (1 Hz)**. Além disso, pelo imperativo constitucional do sigilo do voto, o log **não registra qual candidato recebeu o voto**, tornando impossível correlacionar tempos individuais a escolhas políticas específicas.
2. **Viabilidade Extrema de Auditoria Comportamental e Operacional:**  
   Embora o *timing attack* de CPU seja inviável pelo log, o `logd.dat` registra com precisão cirúrgica a **esteira de eventos administrativos, biométricos e de hardware**. Ele permite comprovar fraudes procedimentais materiais, tais como **votação em lote por terceiros**, **liberações manuais fraudulentas pelo mesário (Código 01)**, **votações fictícias pós-17h** e **discrepâncias de comportamento entre modelos de urnas**.

---

## 1. ANATOMIA E ARQUITETURA DO ARQUIVO `logd.dat`

O arquivo `logd.dat` é o diário operacional gravado em tempo real pelo daemon de logging (`LOGD`) do sistema operacional **Uenux** (distribuição Linux customizada pelo TSE com kernel de tempo real). Ele é encapsulado no pacote lacrado `[código_seção]-log.jez` (container 7-Zip ou Tar/bzip2 assinado digitalmente).

### 1.1. Estrutura de Cada Linha de Log
Cada evento registrado no `logd.dat` obedece rigorosamente a um esquema delimitado por tabulações (`\t`):

```
[TIMESTAMP] \t [SEVERIDADE] \t [CÓDIGO DE PROCESSO] \t [SUBSISTEMA] \t [MENSAGEM DO EVENTO] \t [HMAC / HASH]
```

Exemplo real extraído de urna da Bahia (Seção 0426, Zona 0028 - 2026):
```text
04/10/2026 08:04:09	INFO	02169513	VOTA	Voto confirmado para [Presidente]	6A59653DA29A308D
04/10/2026 08:04:10	INFO	02169513	VOTA	O voto do eleitor foi computado	93502053E2F15BE9
```

* **Timestamp:** `DD/MM/AAAA HH:MM:SS` (Resolução de **1 segundo inteiro**).
* **Severidade:** `INFO` (Operação normal), `ALERTA` (Avisos de bateria/leitura) ou `ERRO` (Falhas de hardware ou software).
* **Código de Processo:** Identificador numérico interno da instância em execução na memória.
* **Subsistema:** Identifica o módulo de software emissor:
  * `SCUE`: Sistema de Carga da Urna Eletrônica (pré-eleição).
  * `GAP`: Gerenciador de Aplicativos e Processos (segurança e integridade).
  * `INITJE`: Inicialização do Uenux e verificação de hardware.
  * `ATUE`: Autoteste da Urna Eletrônica (teclado, áudio, tela e impressora).
  * `VOTA`: O módulo principal de votação, recepção de votos e totalização.
  * `LOGD`: O próprio daemon de logging.
* **Mensagem:** Texto descritivo estruturado da ação realizada.
* **HMAC / Assinatura de Linha:** Código criptográfico de integridade encadeado, garantindo que nenhuma linha possa ser deletada ou injetada a posteriori sem quebrar a cadeia de custódia.

---

## 2. O CICLO DE VIDA COMPLETO DO PLEITO REGISTRADO NO LOG

A dissecação de milhares de arquivos de log do TSE revela cinco fases cronológicas perfeitamente delimitadas:

```
                          CICLO CRONOLÓGICO DOS LOGS DA URNA
                          
  [ 1. Preparação/Carga ] ──▶ [ 2. Abertura Matutina ] ──▶ [ 3. Votação (Eleitores) ] ──▶ [ 4. Encerramento ]
   • Geração de Mídias          • Zerésima impressa         • Identificação Mesário       • Votos pós-17h
   • Criptografia TPM           • Verificação Mesários      • Biometria (Scores 1-4)      • Emissão do BU
   • Autoteste Hardware         • Prontidão às 08:00        • Cabine e Confirmação        • Assinatura RSA
```

### Fase A: Preparação, Carga e Lacração (Dias anteriores ao pleito)
* Registro do computador que gerou as mídias: `Mídia de carga gerada pelo computador: ZBA028WKS01 - TPM: 679DD125`.
* Autoteste de periféricos: `Tecla pressionada: CONFIRMA`, teste de fone de ouvido, autoteste de impressora térmica e calibragem do sensor biométrico.
* Detecção do modelo físico de hardware: bibliotecas carregadas (`avusrlibue2020.vst`, `ue2015`, `ue2013`, `ue2022`).

### Fase B: Abertura da Seção e Zerésima (07:00 às 08:00 do dia da eleição)
* Inicialização do módulo `VOTA` e verificação da integridade do banco de dados de candidatos.
* Registro dos mesários presentes:
  * `Mesário 057259700540 não é eleitor da seção`
  * `Mesário 161356090558 é eleitor da seção`
* Emissão do comprovante físico de zerésima: `Aguardando confirmação para emissão da zerésima`.
* Liberação pontual para início dos trabalhos: `Urna pronta para receber votos` (tipicamente às 08:00:00).

### Fase C: O Ciclo Unitário de Cada Eleitor (08:00 às 17:00)
Para **cada um** dos centenas de cidadãos que comparecem à urna, o log registra o seguinte fluxo obrigatório:

1. **Recepção na Mesa:** `Aguardando digitação do identificador do eleitor`.
2. **Digitação do Título:** `Identificador do eleitor digitado pelo mesário`.
3. **Exibição Cadastral:** `Foto do eleitor apresentada` (no terminal do mesário).
4. **Tentativas Biométricas:**
   * `Solicita digital. Tentativa [1] de [4]`
   * `Capturada a digital. Tentativa [1] de [4]`
   * `Batimento de digitais retornou o score 118` (onde score $\ge 100$ indica reconhecimento com sucesso).
5. **Em caso de falha biométrica:**
   * `Ano de nascimento digitado é igual ao do cadastro` (confirmação do dado pessoal para liberação manual).
6. **Classificação do Eleitor:**
   * `Tipo de habilitação do eleitor [biométrica]` **OU**
   * `Tipo de habilitação do eleitor [manual / código 01]`.
7. **Liberação da Cabine:** `Eleitor foi habilitado`.
8. **Pressionamento de Teclas:** Registra confirmações por cargo:
   * `Voto confirmado para [Deputado Federal]`
   * `Voto confirmado para [Presidente]`
   * `Tecla indevida pressionada` (caso o eleitor aperte teclas inválidas).
9. **Persistência Criptográfica:**
   * `O voto do eleitor foi computado` (commit no RDV em memória volátil e flash).
10. **Conclusão:** `Aguardando digitação do identificador do eleitor` (pronto para o próximo).

### Fase D: Monitoramento Ambiental e Telemetria de Hardware
Periodicamente (a cada dezenas de votos ou por hora), a urna executa auto-inspeção:
* Níveis de energia: `Urna ligada conectada na rede CA em [125.78V] e na Bateria Interna com [13.44V/0A]`.
* Memória não-volátil: `Espaço livre na MI [3.4 GB]`, `Espaço livre na MV [376.3 MB]`.
* Memória RAM: `Quantidade de memória usada [478.8 MB]`, `Quantidade de memória livre [3.2 GB]`.

### Fase E: Encerramento do Pleito e Consolidação (17:00 em diante)
* Identificação de votos após o fechamento dos portões (`Votos pós-17h`).
* Comando oficial de finalização pelo presidente de mesa.
* Emissão física do Boletim de Urna (BU impresso com QR Code).
* Assinatura digital dos arquivos finais com a chave privada ICP-Brasil da urna (RSA-2048 / SHA-512).
* Gravação da Mídia de Gravação dos Resultados (MR).

---

## 3. LIMITES EPISTEMOLÓGICOS DO LOG: POR QUE O TIMING ATTACK DE CPU É INVIÁVEL VIA `logd.dat`?

Retomando a dúvida técnica sobre a auditoria de hardware timers:

### 3.1. A Desproporção entre Ciclos de CPU e a Resolução do Log
Uma rotina de software de intercepção (como o pseudo-código `persist_vote` modelado no relatório de ameaças) executa um desvio de memória volátil:
```c
if (vote->candidate == CANDIDATE_BOLSONARO && draw() < 0.80) {
    vote->candidate = CANDIDATE_LULA; // Swap em RAM
}
```
* O tempo de execução dessa instrução condicional em um processador moderno de urna eletrônica (arquitetura x86 ou ARM rodando a 1.0 GHz ou mais) é de aproximadamente **50 a 200 nanossegundos** ($10^{-9}$ segundos).
* O timestamp do `logd.dat` registra apenas **segundos inteiros**.
* Em um único segundo do log ocorrem **1.000.000.000 (um bilhão) de nanossegundos**.
* **Evidência Empírica Direta:** Analisando os logs reais de 649 eleitores consecutivos de uma urna da Bahia (`o03221ba3069400280426-log.jez`), o tempo decorrido entre `Voto confirmado para [Presidente]` e `O voto do eleitor foi computado` resultou exatamente em:
  $$\Delta t = 0{,}0\text{ segundos (309 vezes)} \quad \Big| \quad \Delta t = 1{,}0\text{ segundo (340 vezes)}$$
  Não há valores intermediários (como 0,15s ou 0,38s). A alternância entre 0s e 1s é um mero artefato estatístico de quantização: depende exclusivamente de o relógio do sistema ter virado de segundo durante os ~200 milissegundos que a controladora flash levou para confirmar a gravação em disco.

### 3.2. A Blindagem do Sigilo do Voto
Para que um *timing attack* pudesse distinguir um voto legítimo de um voto alterado, o analista precisaria saber qual eleitor votou em qual candidato.
* No log, a linha é rigorosamente genérica: `Voto confirmado para [Presidente]`.
* O Registro Digital do Voto (RDV) embaralha os votos através de um gerador pseudoaleatório de permutação (*PRNG de sigilo*). Não há ponteiro cronológico entre a ordem dos votos no RDV e a ordem dos eleitores no `logd.dat`.
* Portanto, mesmo se houvesse micro-resolução temporal, o perito não saberia quais linhas de log corresponderiam aos eleitores da oposição e quais corresponderiam aos eleitores da situação.

### 3.3. O Jitter Biomecânico Humano
O tempo que um eleitor passa na cabine é governado pelo comportamento motor humano (andar, ler colinha, digitar, hesitar, confirmar), cuja variância é de **$\pm 15$ a $45$ segundos**. Essa dispersão biológica é ordens de magnitude maior do que qualquer anomalia de computação, soterrando qualquer sinal de microcódigo.

---

## 4. O QUE O LOG EFETIVAMENTE PERMITE AUDITAR COM ALTO IMPACTO?

Embora o *timing attack* de CPU seja inviável, o arquivo `logd.dat` é uma das ferramentas mais poderosas da perícia computacional para detectar **violações procedimentais, fraudes humanas e anomalias de execução de larga escala**.

Abaixo, as frentes periciais viáveis:

```
                            AS 4 FRENTES PERICIAIS DOS LOGS
                            
   ┌───────────────────────────┐                    ┌───────────────────────────┐
   │ 1. HABILITAÇÃO MANUAL     │                    │ 2. TEMPOS DE CABINE       │
   │ Código 01 sem biometria   │                    │ Votos em lote impossíveis │
   │ Desvio da média do colégio│                    │ Sessões < 5 segundos      │
   └─────────────┬─────────────┘                    └─────────────┬─────────────┘
                 │                                                │
                 ▼                                                ▼
   ┌───────────────────────────┐                    ┌───────────────────────────┐
   │ 3. VOTOS PÓS-17H          │                    │ 4. CADÊNCIA & HARDWARE    │
   │ Injeção crepuscular       │                    │ Ritmo artificial periódico│
   │ Filas legítimas vs fraude │                    │ Discrepância UE2020/2015  │
   └───────────────────────────┘                    └───────────────────────────┘
```

### 4.1. Auditoria de Habilitação sem Biometria (Código 01 / Ano de Nascimento)
Quando o leitor biométrico falha 4 vezes, o mesário pode liberar o voto digitando o ano de nascimento do eleitor.
* **Uso Legítimo:** Ocorre em idosos ou trabalhadores rurais com digitais desgastadas (~8% a 15% na média histórica).
* **Uso Fraudulento (Fraude de Mesário):** O mesário utiliza cadernos de eleitores faltosos para liberar votos sucessivos de pessoas ausentes. O log registra exatamente:
  `Tipo de habilitação do eleitor [manual]` + `Ano de nascimento digitado é igual ao do cadastro`.
* **Como auditar:** Se uma seção atinge 80% ou 90% de liberação manual enquanto as outras 5 seções do **mesmo colégio eleitoral** registram 15%, há prova técnica de desvio do operador da mesa.

### 4.2. Detecção de "Votos em Lote" (Tempos Humanamente Impossíveis)
A métrica temporal calculada entre `Eleitor foi habilitado` e `O voto do eleitor foi computado` define a permanência na cabine.
* **Limite Físico-Biomecânico:** No 2º turno, mesmo um eleitor ágil precisa de pelo menos **8 a 12 segundos** para dar passos até a cabine, digitar 2 dígitos, conferir a imagem de foto na tela e pressionar `CONFIRMA`.
* **A Prova Material:** Se o log registra uma sucessão de eleitores votando em **3 a 5 segundos** ininterruptos, é fisicamente impossível que eleitores reais tenham entrado e saído da cabine. Trata-se de uma pessoa parada em frente à urna apertando teclas em sequência (*ballot stuffing*).

### 4.3. Votação Noturna Pós-17h (Fila Real vs. Injeção de Ausentes)
A lei permite votar após as 17:00 apenas para quem já estava na fila e recebeu senha.
* **Fila Legítima:** Apresenta taxa normal de biometria e ritmo orgânico de chegada.
* **Injeção de Ausentes Pós-Fechamento:** Seções onde a votação pós-17h dispara e **100% dos votos noturnos são liberados por código manual sem biometria**, indicando que a mesa aproveitou o fechamento dos portões para esvaziar o caderno de ausentes.

### 4.4. Análise de Dispersão e Cadência Rítmica (Distribuição de Poisson)
O fluxo natural de chegada de eleitores a uma seção eleitoral segue um processo estocástico de Poisson (intervalos aleatórios entre chegadas).
* **Votação Humana:** Exibe intervalos irregulares (ex.: 2 min, 40s, 3 min, 15s).
* **Votação Artificial / Automatizada:** Se os registros exibem intervalos matematicamente periódicos (ex.: exatamente um voto a cada 45 segundos durante duas horas contínuas), o log denuncia acionamento metronômico sem presença humana variável.

---

## 5. MATRIZ E RANKING DE IMPACTO FORENSE DOS LOGS

A tabela a seguir consolida **todas as métricas auditáveis a partir do `logd.dat`**, ranqueadas por seu **potencial de impacto pericial (força probatória)**, acompanhadas do status de implementação no repositório **Sentinela Juris**:

| Rank | Indicador Forense | Evento Rastreado no `logd.dat` | Hipótese de Ameaça / Fraude Investigada | Grau de Impacto | Status no Repositório | Arquivo / Módulo Onde Foi Construído |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- |
| **01** | **Votação em Lote Impossível ($\Delta t < 5\text{s}$)** | `Eleitor foi habilitado` $\to$ `O voto foi computado` | Mesário votando por terceiros na cabine (*ballot stuffing*) | **CRÍTICO** | ⏳ **Parcial** | Métrica `tempo_min_segundos` calculada em `src/metrics.py`, flag $<5\text{s}$ requer filtro dedicado. |
| **02** | **Desvio de Liberação Manual no Local** | `Tipo de habilitação [manual]` vs média do local | Mesário liberando eleitores fantasmas ou ausentes via código 01 | **CRÍTICO** | ✅ **Implementado** | `DIF_MANUAL_LOCAL`, `FLAG_DESVIO_ESCOLA` em `auditoria_secoes_BA_2026` e no Mapa Sentinela. |
| **03** | **Injeção Manual Noturna Pós-17h** | Timestamp $\ge 17:00:00$ com `Tipo habilitação [manual]` | Votação forjada de eleitores ausentes após fechar os portões | **CRÍTICO** | ✅ **Implementado** | `VOTOS_POS_17H_MANUAL`, `PCT_POS_17H_MANUAL` em `auditoria_secoes_BA_2026`. |
| **04** | **Abstenção Quase Nula em Reduto Vulnerável** | Total de votos do BU comparado com eleitores aptos | Coação eleitoral física, transporte ilegal ou fraude no caderno | **ALTO** | ✅ **Implementado** | `FLAG_BAIXA_ABSTENCAO` (abstenção $< 10\%$) em `auditoria_secoes_BA_2026`. |
| **05** | **Score Composto de Anomalia Multicritério** | Confluência de Manual + Pós-17h + Abstenção + Margem | Identificação das seções mais anômalas do estado | **ALTO** | ✅ **Implementado** | `SCORE_ANOMALIA` e `NIVEL_RISCO` (Crítico/Alto) no Painel de Evidências Periciais. |
| **06** | **Discrepância entre Modelos de Urna** | `avusrlibue2020` vs `ue2013` / `ue2015` | Comportamento assimétrico de software entre gerações de urna | **ALTO** | ✅ **Implementado** | `MODELO_URNA` detectado em `src/parser.py` e cruzado com fluxo em DuckDB. |
| **07** | **Cadência Artificial / Desvio de Poisson** | Intervalo de tempo entre habilitações consecutivas | Liberação mecânica automatizada ou rotina contínua de fraude | **ALTO** | 🔬 **Proposto** | Requer módulo de autocorrelação temporal e teste de Kolmogorov-Smirnov. |
| **08** | **Distribuição de Scores Biométricos** | `Batimento de digitais retornou o score [X]` | Falha deliberada de captura para forçar código manual | **MÉDIO** | 🔬 **Proposto** | Logs contêm os scores (0 a 255); agregação em tabela DuckDB pendente. |
| **09** | **Latência de Commit de I/O em Flash** | `Voto confirmado` $\to$ `O voto foi computado` (0s vs 1s) | Gargalo de gravação ou execução de rotinas pesadas em segundo plano | **MÉDIO** | 🔬 **Proposto** | Validado em script de scratch; pendente de consolidação no pipeline. |
| **10** | **Reinicializações e Quedas de Bateria** | `Urna ligada conectada na Bateria Interna`, `reinício` | Tentativas de reinicialização forçada ou instabilidade física | **BAIXO** | ✅ **Implementado** | `ANOMALIA_KEYWORDS` monitoradas em `src/metrics.py`. |
| **--** | **Timing Attack de CPU (Nanossegundos)** | Registro microscópico entre 2º dígito e RAM swap | Detecção direta de malware alterando o voto na memória volátil | **NULO NO LOG** | ❌ **Inviável no Log** | Requer instrumentação física de laboratório (osciloscópio / probe em bus flash). |

---

## 6. ROTEIRO TÉCNICO PARA IMPLEMENTAÇÃO DOS ITENS PENDENTES

Para os três indicadores de alto e médio impacto marcados como **⏳ Parcial** ou **🔬 Proposto**, o pipeline do Sentinela Juris já possui a infraestrutura necessária para implementá-los:

### 1. Implementação da Flag de Votação em Lote Impossível (Rank 01):
* **Fórmula:** Identificar seções que registraram mais de 5 votos com duração de cabine $\le 5$ segundos.
* **Ação no código:** Adicionar coluna `QTD_VOTOS_ABAIXO_5S` na tabela `auditoria_secoes_BA_2026` a partir do `durations` em `src/metrics.py`.

### 2. Implementação do Teste de Cadência de Poisson (Rank 07):
* **Fórmula:** Calcular o coeficiente de variação ($CV = \sigma / \mu$) dos intervalos entre eleitores consecutivos. Em distribuições de Poisson naturais, $CV \approx 1$. Se $CV \to 0$, a chegada foi artificialmente cadenciada.

### 3. Extração e Mineração dos Scores Biométricos (Rank 08):
* **Extração:** Parsear a regex `r"Batimento de digitais retornou o score (\d+)"` em `src/parser.py`.
* **Análise:** Urnas com desvio na curva de scores biométricos (rejeição sistemática de digitais perfeitas) denunciam leitores descalibrados ou adulterados para forçar o desvio manual.

---

## 7. CONCLUSÃO INTEGRADA

1. **O Log não substitui o teste físico de hardware:** A ausência de milissegundos no `logd.dat` e o sigilo constitucional impedem que o log ateste se um voto individual foi alterado por código em RAM no momento da digitação. Essa comprovação depende exclusivamente do **Voto Físico Impresso Auditável pelo Eleitor** ou de **inspeção de hardware em bancada com osciloscópio**.
2. **O Log é devastador contra fraudes procedimentais humanas:** No nível macro, o `logd.dat` é irrefutável para provar seções onde mesários operaram sozinhos na cabine, onde eleitores foram liberados sem biometria em taxas aberrantes, ou onde houve injeção noturna pós-fechamento dos portões.
3. **Maturidade do Repositório Sentinela Juris:** A arquitetura atual já implementou com sucesso os principais indicadores críticos de habilitação manual, desvio de colégio eleitoral, abstenção anômala e votos pós-17h sobre as 35.472 seções da Bahia, estando perfeitamente posicionada para incorporar as análises complementares de cadência temporal e scores biométricos.

---
*Documento pericial elaborado, versionado e persistido no repositório analítico Sentinela Juris.*

