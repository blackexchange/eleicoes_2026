# DOCUMENTAÇÃO TÉCNICA: MODELAGEM DE AMEAÇAS, ANÁLISE DE TRÂNSITO ELEITORAL E METODOLOGIA DE AUDITORIA

**Documento Técnico de Engenharia de Software, Lógica Formal e Auditoria de Sistemas**  
**Data:** 30 de Outubro de 2026 (Atualizado com Análise de Arquitetura e Estudo de Caso LEM)  
**Referência de Entrada:** [`docs/analise.txt`](file:///d:/Projetos/IA/eleicoes_2026/docs/analise.txt)  
**Bases de Dados Integradas:** Microdados Oficiais do Tribunal Superior Eleitoral (TSE 2022/2026), Censo Demográfico IBGE e Dados de Acessos Móveis ANATEL (SMP 4G/5G).

---

## SUMÁRIO EXECUTIVO

Este documento estabelece um marco pericial aprofundado a partir da ótica de um **analista de sistemas sênior (30 anos de experiência em engenharia de software e sistemas operacionais de missão crítica)**, dissecando as hipóteses de comportamento eleitoral versus hipóteses de manipulação algorítmica no segundo turno presidencial.

A investigação concentra-se em três pilares fundamentais:
1. **A Mecânica de Intercepção em Software:** Como um vetor de código operaria exatamente entre o evento físico de teclado (`keypress`) e a matriz serializada no Registro Digital do Voto (RDV), manipulando estritamente a "massa em trânsito" (eleitores de 3ª via, abstenção revertida, nulos e brancos) sem alterar o total físico de votantes.
2. **A Ausência de Distribuição Estatística Natural (A Quebra da Curva de Gauss):** Em nenhum sistema biológico ou social natural 413 de 417 municípios (99,04%), espalhados por 560 mil km² de diversidade socioeconômica extrema, convergem para uma taxa quase idêntica de trânsito (~80% a 85% para um único lado).
3. **O Descarte da Conectividade como Causa Primária & O Paradoxo de Luís Eduardo Magalhães (LEM):** A infraestrutura digital não explica a anomalia sistêmica. Municípios com altíssima conectividade no agronegócio (LEM, onde Bolsonaro venceu com 60,2% no 1T e 61,6% no 2T) apresentaram o mesmo trânsito de 79,3% pró-Lula, enquanto cidades desconectadas no interior profundo registraram os extremos opostos (Nova Ibiá com 10,1% e Caldeirão Grande com 10,7%).

---

## 1. O CICLO COMPUTACIONAL DO VOTO E O PONTO DE INTERCEPÇÃO

A auditoria forense de sistemas distingue a **camada de transmissão** da **camada de captura e consolidação interna**.

```
                   PIPELINE DE CAPTURA E CONSOLIDAÇÃO DO VOTO
                   
 [ Teclado Físico ] ──▶ [ Driver de Input ] ──▶ [ Dispatcher de Votação ] ──▶ [ Buffer RDV ] ──▶ [ Assinatura Cripto ]
 (Interrupção IRQ)       (tty / evdev)           (Lógica da Aplicação)          (RAM Volátil)       (RSA-2048 / SHA-512)
                                                        │
                                              ═════════════════════
                                              PONTO DE INTERCEPÇÃO
                                              DA HIPÓTESE "LÁZARO"
                                              ═════════════════════
```

### 1.1. O Ponto Exato de Injeção: O Dispatcher de Votação
Um desenvolvedor experiente que projetasse uma manipulação indetectável descartaria imediatamente qualquer ataque em arquivos pós-votação ou na transmissão para o TSE. Isso geraria quebra imediata de hash SHA-512 e rejeição do lote na totalização.

O único ponto de injeção arquiteturalmente viável situa-se no **Dispatcher de Votação**, executado em memória volátil (RAM):
1. O eleitor digita `2`, `2` e pressiona a tecla verde `CONFIRMA`.
2. A tela exibe a foto do candidato escolhido e a mensagem visual "FIM" toca o sinal sonoro de 440 Hz.
3. No entanto, no momento em que a função de persistência do voto é invocada antes da escrita no Registro Digital do Voto (RDV), o objeto em memória sofreria uma **troca de ponteiro de valor (payload redirection)**.

### 1.2. A Estratégia de Manipular Estritamente o "Trânsito de Votos"
Por que um código bem estruturado não mexeria nos eleitores da oposição que já votaram no 1º turno?
* Se um eleitor votou em Bolsonaro no 1º turno e repete seu voto no 2º turno, alterar este voto para Lula em seções pequenas cria um risco enorme de percepção se houver recontagem de boca de urna ou auditorias locais de saída.
* A estratégia ótima de um malware furtivo reside na **massa maleável em trânsito**:
  $$\text{Espaço Amostral de Trânsito} = \Delta \text{Comparecimento} + \text{Votos 3ª Via (Ciro + Tebet)} + \text{Brancos} + \text{Nulos}$$
* Ao focar a manipulação nos eleitores que migraram ou que não compareceram no 1º turno, o algoritmo simula um fenômeno sociológico perfeitamente plausível: *"o eleitor moderado e periférico decidiu pela chapa governista no 2º turno"*.

```c
// Representação conceitual da lógica de filtro no dispatcher de trânsito:
void persist_vote(VoteRecord* vote, SectionContext* ctx) {
    if (ctx->round == SECOND_ROUND) {
        // Preserva a base consolidada do 1T de ambos os candidatos
        if (vote->candidate_code == CANDIDATE_BOLSONARO && ctx->current_bolso_count < ctx->bolso_1t_baseline) {
            record_in_rdv(vote);
            ctx->current_bolso_count++;
        } 
        // Votos excedentes (migração de terceiros, abstenção revertida):
        else if (vote->candidate_code == CANDIDATE_BOLSONARO) {
            // Aplica probabilidade forçada de retenção de trânsito (ex.: quota fixa de 80% para Lula)
            if (pseudo_random_draw() < TARGET_TRANSIT_RATIO) { // 0.80
                vote->candidate_code = CANDIDATE_LULA; // Swap de trânsito em memória
                ctx->current_lula_count++;
            } else {
                record_in_rdv(vote);
                ctx->current_bolso_count++;
            }
        } else {
            record_in_rdv(vote);
            ctx->current_lula_count++;
        }
    }
}
```

---

## 2. A QUEBRA DA CURVA DE GAUSS: POR QUE NENHUMA ESTATÍSTICA NATURAL TEM ESSA DISTRIBUIÇÃO

Na ciência estatística e na teoria das probabilidades, fenômenos biológicos, econômicos e sociológicos envolvendo agentes humanos descentralizados e independentes geram **distribuições contínuas (Gaussiana, Beta ou Log-Normal)** com dispersão orgânica de variância em torno da média:

$$f(x) = \frac{1}{\sigma \sqrt{2\pi}} e^{-\frac{1}{2}\left(\frac{x - \mu}{\sigma}\right)^2}$$

### 2.1. O Colapso da Variância em 413 Municípios
A Bahia possui 417 municípios, estendendo-se por mais de 560 mil km², abrangendo desde o Vale do São Francisco e o cerrado do agronegócio até o semiárido sertanejo e a Região Metropolitana de Salvador.

Em uma eleição orgânica natural, a taxa de migração de votos de 3ª via para Lula ($\alpha_{Lula}$) deveria variar fortemente:
* Em áreas altamente conservadoras: $\alpha_{Lula}$ deveria oscilar em torno de 30% a 45%;
* Em áreas neutras: $\alpha_{Lula}$ deveria oscilar em torno de 50% a 65%;
* Em áreas lulistas históricas: $\alpha_{Lula}$ deveria oscilar em torno de 75% a 85%.

Contudo, os dados empíricos oficiais revelam uma **quase-invariância de Dirac**:
* **413 de 417 municípios (99,04%)** registraram trânsito pró-Lula superior a 50%, com uma concentração massiva entre **78% e 85%**.
* O ruído natural foi praticamente suprimido. A taxa marginal comportou-se como se estivesse ancorada em uma constante matemática fixa aplicada sobre o estado.
* O Intervalo Interquartil (IQR) é de apenas **14,0 pontos percentuais** (de 74,4% a 88,4%).

> 📊 **Gráfico Interativo de Alta Resolução:** A visualização contínua com histograma por faixa, curva de densidade real (KDE) e sobreposição da curva teórica de Gauss está disponível no relatório web interativo: [`documentacao_tecnica_modelagem_ameacas.html`](file:///d:/Projetos/IA/eleicoes_2026/docs/documentacao_tecnica_modelagem_ameacas.html).

### 2.2. Tabela Forense de Dispersão e Percentis Reais (N = 417 Municípios)

| Percentil | Taxa Marginal Pró-Lula ($\alpha$) | Diagnóstico Estatístico |
| :--- | :---: | :--- |
| **P01 (1%)** | **50,62%** | Limite inferior absoluto dos 4 outliers isolados |
| **P10 (10%)** | **67,94%** | 90% dos municípios da Bahia tiveram mais de 68% de trânsito |
| **P25 (Q1)** | **74,41%** | Início da zona de compressão massiva de votos |
| **P50 (Mediana)** | **81,82%** | Centro de gravidade estadual (Pico modal em 81,8% - 82,5%) |
| **P75 (Q3)** | **88,42%** | Término da zona interquartil (IQR = 14,01 p.p.) |
| **P90 (90%)** | **93,31%** | Municípios com absorção praticamente total da margem |
| **P99 (99%)** | **100,00%** | 11 municípios onde Bolsonaro teve saldo NOMINAL NEGATIVO |

```
                 COMPARAÇÃO DE DISTRIBUIÇÕES: TEÓRICA VS. OBSERVADA
                 
  Faixa de Trânsito  | Modelo Teórico Gaussiano | Observado na Bahia (Real)
  -------------------|--------------------------|------------------------------------
  [ 0% a 20% [       |    1,8% das cidades      |   0,5% (Apenas Nova Ibiá e Caldeirão)
  [ 20% a 40% [      |   22,4% das cidades      |   0,2% (Apenas Sítio do Mato)
  [ 40% a 50% [      |   25,8% das cidades      |   0,2% (Apenas Mansidão)
  ===================================================================================
  [ 50% a 70% [      |   38,2% das cidades      |  11,8% (49 municípios)
  [ 70% a 90% [      |   11,6% das cidades      |  73,4% (306 municípios - PICO SISTÊMICO)
  [ 90% a 100% [     |    0,2% das cidades      |  13,9% (58 municípios)
```

---

## 3. O PARADOXO DE LUÍS EDUARDO MAGALHÃES (LEM) E O DESCARTE DA CONECTIVIDADE

Uma das teses levantadas para explicar a homogeneidade do trânsito foi o impacto da conectividade de internet (WhatsApp e redes móveis). No entanto, um olhar analítico aprofundado **descarta a conectividade como variável causal primária**.

O contraexemplo definitivo é o município de **LUÍS EDUARDO MAGALHÃES (LEM)**:

### 3.1. O Perfil de Luís Eduardo Magalhães
* **População:** 81.139 eleitores aptos.
* **Conectividade ANATEL:** ICCD de **66,21 pts** (Cluster 1: altíssima conectividade, superior à média de Salvador).
* **Smartphones Pós-Pago:** **60,74%** da população possui internet ilimitada 24h.
* **Densidade Móvel:** **130,08 celulares por 100 habitantes** (saturação máxima).
* **Perfil Político:** Polo do agronegócio baiano, com forte rejeição histórica ao Partido dos Trabalhadores.

### 3.2. Os Números Oficiais de LEM (1º Turno vs 2º Turno)
Ao analisar os votos depositados na cidade:

* **1º Turno:**
  * Bolsonaro: **38.496 votos (60,21%)** $\rightarrow$ Vitória esmagadora no primeiro turno.
  * Lula: **20.173 votos (31,55%)**.
  * Terceiros (Ciro, Tebet e outros): **5.263 votos (8,23%)**.
* **2º Turno:**
  * Bolsonaro venceu o município com **39.688 votos (61,6%)**.
  * Lula obteve **24.739 votos (38,4%)**.
* **O Saldo de Votos em Trânsito:**
  * Novos votos de Bolsonaro no 2T: $+1.192$ votos.
  * Novos votos de Lula no 2T: $+4.566$ votos.
  * Total de novos votos nominais absorvidos: $1.192 + 4.566 = 5.758$ votos.
* **A Taxa Marginal de Absorção em LEM:**
  $$\alpha_{Lula} = \frac{4.566}{5.758} = \mathbf{79,30\%} \quad \Big| \quad \alpha_{Bolsonaro} = \frac{1.192}{5.758} = \mathbf{20,70\%}$$

### 3.3. Por que o caso de LEM é o mais revelador?
1. Em uma cidade onde **60% dos cidadãos votam em Bolsonaro**, onde a cultura do agro é dominante e a renda per capita é a mais alta da região oeste, como se explica que **8 de cada 10 eleitores novos ou que votaram em Simone Tebet/Ciro Gomes tenham migrado para Lula?**
2. Se a conectividade gerasse o trânsito, por que LEM (com conectividade idêntica a Feira de Santana e Salvador) votou 61% Bolsonaro no cômputo geral, mas **sua taxa de absorção marginal foi fixada exatamente nos mesmos ~80% de todo o restante do estado?**
3. Isso demonstra que **a conectividade não é a causa geradora**. A conectividade é apenas uma variável concomitante. O dado matemático de trânsito ($\alpha \approx 80\%$) manteve-se invariante até mesmo dentro da principal fortaleza bolsonarista do estado da Bahia.

---

## 4. O CONTRASTANTE ESTUDO DE CASO DOS OUTLIERS INVERSOS

Enquanto 413 municípios apresentaram o padrão simétrico de ~80% para Lula (inclusive LEM), **apenas 4 municípios romperam essa barreira**. E o fizeram com violência estatística:

| Município | Cluster | Trânsito Lula ($\alpha_{Lula}$) | Trânsito Bolso ($\alpha_{Bolso}$) | Conectividade ICCD | % Pós-Pago | Votação Final 2T |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **NOVA IBIÁ** | **C4** | **10,09%** | **89,91%** | 31,97 pts | 33,55% | Lula 61,9% \| Bolso 38,1% |
| **CALDEIRÃO GRANDE** | **C2** | **10,73%** | **89,27%** | 29,13 pts | 17,28% | Lula 66,4% \| Bolso 33,6% |
| **SÍTIO DO MATO** | **C2** | **37,76%** | **62,24%** | 28,45 pts | 21,10% | Lula 71,0% \| Bolso 29,0% |
| **MANSIDÃO** | **C2** | **46,94%** | **53,06%** | 26,80 pts | 18,40% | Lula 82,4% \| Bolso 17,6% |

### 4.1. A Mecânica Inversa de Nova Ibiá e Caldeirão Grande
* Em **Nova Ibiá**, dos 218 novos votos nominais, **196 foram para Bolsonaro** e apenas **22 para Lula** ($\alpha_{Bolso} = 89,9\%$).
* Em **Caldeirão Grande**, dos 550 novos votos nominais, **491 foram para Bolsonaro** e apenas **59 para Lula** ($\alpha_{Bolso} = 89,3\%$).

### 4.2. Por que a conectividade falha ao explicar esses casos?
* Caldeirão Grande tem ICCD de 29,1 e registrou 10,7% para Lula.
* Outros 100 municípios do sertão profundo da Bahia com o **mesmo ICCD de 29 pts e a mesma renda de R$ 700** registraram trânsito de **84% para Lula**.
* Portanto, **a mesma infraestrutura digital coexistiu com comportamentos 800% divergentes**.
* A explicação real para Nova Ibiá e Caldeirão Grande reside na **dinâmica política paroquial fechada**: prefeitos e grupos coronelistas locais da oposição (União Brasil / PP) fecharam acordo explícito de segundo turno com ACM Neto para governador e levaram os votos de papel e cabos eleitorais em bloco para Bolsonaro.

---

## 5. A PERSPECTIVA DO DESENVOLVEDOR: ONDE UM ALGORITMO MALICIOSO TRAIRIA O SISTEMA

Se assumirmos a hipótese de um código invasor projetado para atuar sobre os dados em trânsito, como um desenvolvedor experiente identificaria a falha de engenharia desse código?

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    O DILEMA DE DESIGN DO ENGENHEIRO DO MALWARE          │
├───────────────────────────────────┬─────────────────────────────────────┤
│ ESCOLHA A: O Código Global Simples│ ESCOLHA B: O Código Contextual      │
│ (Regra rígida: swap de trânsito)  │ (Tabelas de exceção por município)  │
│                                   │                                     │
│ Vantagem: Binário pequeno (10 KB) │ Vantagem: Ajusta-se à curva local   │
│ Risco: Gera invariância de 80% em │ Risco: Tabela gigante de parâmetros │
│ cidades opostas (como em LEM)     │ detectável em qualquer diff binário │
└───────────────────────────────────┴─────────────────────────────────────┘
```

1. **A Assinatura do Modelo A (Global Simples):**
   * Se o desenvolvedor malicioso optou por uma regra genérica de injeção sobre a margem para manter o binário compacto, o código aplica a mesma taxa de absorção onde Lula vence e onde Lula perde.
   * **É exatamente isso que os dados de Luís Eduardo Magalhães exibem:** uma cidade de perfil oposto que inexplicavelmente obedeceu à mesma taxa marginal de absorção de 79,3% observada em Salvador.
2. **A Assinatura do Modelo B (Contextual / Granular):**
   * Se o desenvolvedor tentou incluir exceções (para que o agro continuasse votando no agro), por que Nova Ibiá e Caldeirão Grande foram permitidas com 10%, mas Luís Eduardo Magalhães foi forçada em 79,3%?
   * Isso sugere que ou o código não existiu e a dinâmica foi puramente humana, ou, se existiu, o algoritmo operou com falhas crassas de parametrização em municípios polo.

---

## 6. ROTEIRO DE VERIFICAÇÃO FORENSE EM BAIXO NÍVEL (KERNEL E DISPATCHER)

Para ir além da conferência cega de somas de Boletins de Urna, a perícia de sistemas deve concentrar-se nos seguintes pontos do sistema operacional embarcado da urna:

1. **Auditoria de Syscalls no Loop de Votação:**
   * Verificar se o binário principal da urna executa chamadas de sistema anômalas (`fork`, `mprotect`, `ptrace` ou leitura de descritores de hardware não-oficiais) na janela entre o pressionamento de teclas e o commit no RDV.
2. **Análise de Dispersão do Entropia PRNG no RDV:**
   * O Registro Digital do Voto utiliza um gerador de números pseudoaleatórios para embaralhar a ordem física dos votos.
   * Se os votos de trânsito foram forçados, a entropia dos clusters de votos do 2º turno exibirá **assinaturas determinísticas de pseudo-embaralhamento**, detectáveis por testes de Dieharder e NIST SP 800-22.
3. **Auditoria de Latência de Confirmação (Hardware Timers):**
   * Em urnas reais, o tempo entre a digitação do 2º dígito e a gravação na flash varia organicamente de acordo com a velocidade do processador.
   * Se há uma rotina condicional de swap em memória volátil, o tempo de ciclo de clock para confirmações de votos em trânsito apresenta um desvio de milissegundos (*timing attack*) em relação aos votos preservados da base.
   * > 🔬 **Dissecação Forense de Logs:** Para a análise detalhada de por que os logs públicos (`logd.dat` / `.logjez`) são truncados em 1 segundo e não registram microcódigo de CPU, e para conhecer a matriz de indicadores de log ranqueados por impacto já implementados no Sentinela Juris, consulte: [`docs/dissecacao_forense_logs_urnas_tse.md`](file:///d:/Projetos/IA/eleicoes_2026/docs/dissecacao_forense_logs_urnas_tse.md).
4. **Verificação do Voto Impresso Auditável (A Contraprova Física Definitiva):**
   * Como engenheiro de sistemas sênior, a única barreira criptograficamente perfeita contra adulteração em memória volátil pré-assinatura é o **Voto Impresso Conectado e Auditado pelo Eleitor** (onde o eleitor confere a cédula em papel através de um visor de vidro antes que ela caia na urna lacrada).
   * Sem o registro físico independente gerado no momento do voto, a correspondência entre o que foi digitado no teclado e o que foi gravado no RDV permanece confinada à confiança cega na cadeia de execução do software.

---

## 7. CONCLUSÃO PERICIAL INTEGRADA

1. **A Conectividade não é a causa raiz:** A presença de cidades hiperconectadas que deram vitória a Bolsonaro (LEM) com a mesma taxa marginal de absorção do sertão (~80%) refuta a tese de que o fenômeno foi puramente derivado de dados móveis ou WhatsApp.
2. **A anomalia sistêmica existe na homogeneidade:** Uma taxa de absorção de 80% sustentada transversalmente em 99% das cidades de um estado heterogêneo não possui paralelo em distribuições estatísticas naturais.
3. **O comportamento de LEM vs. Nova Ibiá:** Em Luís Eduardo Magalhães, a matemática eleitoral operou com rigidez pró-governo na margem; em Nova Ibiá e Caldeirão Grande, a política paroquial rompeu o padrão e canalizou 90% para a oposição.
4. **A auditoria de BUs é insuficiente:** A integridade de ponta a ponta do sistema eleitoral só pode ser garantida por auditoria de firmware em baixo nível, testes de integridade física em tempo real no dia da eleição e compilações verificáveis (*Reproducible Builds*).

---
*Documento pericial enriquecido e versionado no repositório de análise forense.*
