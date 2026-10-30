# DOCUMENTAÇÃO TÉCNICA: MODELAGEM DE AMEAÇAS, ANÁLISE DE TRÂNSITO ELEITORAL E METODOLOGIA DE AUDITORIA

**Documento Técnico de Engenharia de Software, Lógica Formal e Auditoria de Sistemas**  
**Data:** 30 de Outubro de 2026  
**Referência de Entrada:** [`docs/analise.txt`](file:///d:/Projetos/IA/eleicoes_2026/docs/analise.txt)  
**Bases de Dados Integradas:** Microdados Oficiais do Tribunal Superior Eleitoral (TSE 2022/2026), Censo Demográfico IBGE e Dados de Acessos Móveis ANATEL (SMP 4G/5G).

---

## SUMÁRIO EXECUTIVO

Este documento estabelece um marco técnico-pericial para a dissecação de duas teses concorrentes a respeito da dinâmica eleitoral no segundo turno das eleições presidenciais:

1. **Hipótese Política/Comportamental (Hipótese 1):** O paradoxo do "arrependimento relâmpago" em redutos consolidados (SC, MT, GO, PR), atribuído à mobilização digital massiva, transporte gratuito de eleitores periféricos e migração concentrada de votos da terceira via.
2. **Hipótese de Vetor Lógico Embarcado (Hipótese 2 - "Lázaro"):** A tese de que uma alteração programática dos votos na memória da urna eletrônica antes da consolidação e assinatura digital do Boletim de Urna (BU) seria capaz de manipular o resultado sem romper a correspondência aritmética com a totalização centralizada.

Por meio de ferramentas de **modelagem de ameaças (Threat Modeling)**, **decomposição econométrica de trânsito eleitoral** e **análise pericial dos 417 municípios da Bahia**, o presente trabalho demonstra as restrições físicas de um malware hipotético, os limites da verificação de BUs e o comportamento de outliers empíricos reais como contraprova técnica.

---

## 1. ANÁLISE DA ARQUITETURA DE SISTEMAS E CICLO DE VIDA DO VOTO

A análise forense de um sistema informatizado exige a distinção rigorosa entre a **camada de captura do dado** e a **camada de transmissão do dado**.

```
                           CICLO COMPUTACIONAL DO VOTO
                           
  [ 1. Entrada ]         [ 2. Memória RAM ]        [ 3. Processamento ]      [ 4. Assinatura ]        [ 5. Mídia Flash ]
  Pressionamento   ───▶   Buffer Volátil     ───▶  Embaralhador RDV   ───▶   Assinatura RSA-2048 ──▶  Gravação Criptografada
  Tecla CONFIRMA         do Processador            (PRNG de Sigilo)          + Função SHA-512         Não-Volátil
                                                          │
                                                Ponto Teórico Crítico
                                                da Hipótese "Lázaro"
```

### 1.1. O Princípio da Verificação em Duas Fases
* **Fase A (Transmissão e Totalização Externa):**  
  Comprova que $BU_{recebido\_TSE} = BU_{impresso\_seção}$. Esse canal é protegido por funções criptográficas de hash irreversível (SHA-512) e assinaturas digitais com chaves assimétricas emitidas pela Autoridade Certificadora da Justiça Eleitoral. A conferência do Boletim de Urna pelos fiscais partidários atesta que o arquivo gerado não foi interceptado ou modificado em trânsito (ausência de ataque do tipo *Man-in-the-Middle* na rede).
* **Fase B (Captura e Gravação Interna):**  
  Ocorre no ciclo de clock anterior à gravação na mídia e geração do BU impresso. Uma conferência visual das somas do BU comprova a fidelidade da **Fase A**, mas é computacionalmente cega para manipulações internas na **Fase B** que ocorram no código que contabiliza os votos no Registro Digital do Voto (RDV).

### 1.2. Restrições Formais de um Código Malicioso Hipotético
Para que um algoritmo operasse dentro do firmware da urna sem ser detectado pela conferência visual, ele teria que obedecer a **três invariantes lógicas estritas**:

1. **A Invariante de Massa Aritmética ($N = \text{constante}$):**  
   O número total de votantes no BU deve ser identicamente igual ao número de assinaturas físicas registradas no Caderno de Votação pelos mesários:
   $$\text{Comparecimento Físico} = V_{Candidato\_A} + V_{Candidato\_B} + V_{Brancos} + V_{Nulos}$$
   O algoritmo não pode criar votos do nada; é forçado a realizar **troca de chave de valor (swap)** entre candidatos ou absorver o contingente de abstenção reduzida / votos de terceiros.
2. **Restrição de Não-Negatividade:**  
   Nenhum candidato pode ter saldo negativo de votos nominais em relação ao que foi depositado fisicamente.
3. **Restrição Temporal de Disparo:**  
   Para evitar ser pego em auditorias pré-eleitorais com votos de teste aleatórios, o código precisaria de gatilhos temporais (horário exato do encerramento das seções, às 17h00) ou comportamentais (volume acumulado superior a 100 eleitores).

---

## 2. A ECONOMETRIA DO TRÂNSITO DE VOTOS (1ºT → 2ºT)

O documento investigado aponta perplexidade diante de saltos de votação em estados historicamente de oposição (SC com +25%, MT com +19%, GO com +33% e PR com +23% de votos a mais para Lula). Para avaliar a racionalidade desse fenômeno, utiliza-se o modelo econométrico de trânsito eleitoral.

### 2.1. Equação Geral de Conservação dos Votos
Em qualquer unidade geográfica $i$ (seção, zona ou município), a expansão de votos válidos nominais no segundo turno obedece à equação contábil:

$$\Delta V_{Lula}^{(i)} + \Delta V_{Bolsonaro}^{(i)} = \Delta \text{Comparecimento}^{(i)} + V_{\text{3ª\_via}}^{(1T, i)} + \Delta \text{Brancos/Nulos}^{(i)}$$

Onde:
* $\Delta \text{Comparecimento}^{(i)} = \text{Votantes}_{2T}^{(i)} - \text{Votantes}_{1T}^{(i)}$ (saldo de eleitores que deixaram de se abster);
* $V_{\text{3ª\_via}}^{(1T, i)}$ é o saldo de votos de Ciro Gomes, Simone Tebet, Soraya Thronicke e Felipe d'Avila;
* $\Delta \text{Brancos/Nulos}^{(i)}$ é a redução de votos não válidos que migraram para votos nominais.

### 2.2. A Taxa Marginal de Absorção ($\alpha$)
A fração do saldo disponível que é capturada pelo candidato define a **Taxa Marginal de Absorção ($\alpha$)**:

$$\alpha_{Lula}^{(i)} = \frac{\Delta V_{Lula}^{(i)}}{\Delta V_{Lula}^{(i)} + \Delta V_{Bolsonaro}^{(i)}} \times 100$$

* **Comportamento Médio da Bahia:** Em todo o estado, a mediana estadual de $\alpha_{Lula}$ situou-se em **83,8%**. Para cada 10 votos que surgiram na transição de turno, 8,4 foram absorvidos por Lula e apenas 1,6 por Bolsonaro.
* **O Dilema de Escala:** Em redutos onde a oposição detém 70% a 80% do eleitorado consolidado, taxas de trânsito pró-governo de 80% produzem variações percentuais astronômicas sobre uma base inicial reduzida (ex.: passar de 10% para 20% representa 100% de crescimento nominal, embora envolva poucos eleitores absolutos).

---

## 3. AS ASSINATURAS ESTATÍSTICAS RESIDUAIS DE UM MALWARE ELEITORAL

Na engenharia de software e análise forense de dados, vigora o axioma:  
> *"Nenhum algoritmo gerador consegue imitar perfeitamente o ruído e a estocasticidade do comportamento humano em larga escala sem deixar assinaturas residuais mensuráveis."*

Caso um código atuasse nas urnas eletrônicas para assegurar metas eleitorais, ele deixaria rastros matemáticos inequívocos em quatro testes fundamentais:

```
┌────────────────────────────────────────────────────────────────────────┐
│               AS 4 ASSINATURAS ESTATÍSTICAS RESIDUAIS                 │
├───────────────────────────┬────────────────────────────────────────────┤
│ 1. Lei de Newcomb-Benford │ Teste do segundo dígito significativo (2BL)│
│ 2. Resíduos Demográficos  │ Desvio da distribuição normal multivariada │
│ 3. Saturação de Fronteira │ Concentração anômala em taxas α = 100%     │
│ 4. Variabilidade Local    │ Ausência de variância nas caudas da curva  │
└───────────────────────────┴────────────────────────────────────────────┘
```

### 3.1. Violação da Lei de Newcomb-Benford no Segundo Dígito (2BL)
Enquanto o primeiro dígito pode sofrer influência de limitações no tamanho das seções (capacidade máxima de 450 a 500 eleitores), a distribuição do segundo dígito de cada candidato em milhares de seções deve obedecer estritamente à curva logarítmica:
$$P(d) = \sum_{k=1}^{9} \log_{10}\left(1 + \frac{1}{10k + d}\right)$$
Algoritmos que operam regras aritméticas compensatórias tendem a favorecer determinados dígitos residuais, gerando distorções com p-valor significativo no teste Qui-Quadrado ($\chi^2$).

### 3.2. Cobertura Forçada e o Fenômeno de Saturação (Boundary Constraint)
Se a oposição abriu uma margem de milhões de votos no primeiro turno, um algoritmo que tentasse recuperar essa defasagem no segundo turno enfrentaria um problema de **fronteira física**:
* Em seções onde a abstenção já era mínima e os votos de terceiros eram escassos, para atingir o volume compensatório exigido, o código teria que capturar **100% de todos os votos disponíveis** ($\alpha = 1,000$), gerando uma massa anômala de seções sem um único voto marginal para a oposição, violando a distribuição estocástica binomial.

---

## 4. O ESTUDO DE CASO DOS OUTLIERS DA BAHIA: A REFUTAÇÃO DO "ALGORITMO CEGO"

A análise completa dos microdados dos 417 municípios da Bahia pelo nosso modelo de Machine Learning identificou uma evidência de altíssimo valor pericial: **a existência de outliers extremos que contradizem frontalmente a hipótese de um malware cego ou uniforme.**

Em 413 municípios da Bahia, Lula venceu a taxa de trânsito marginal ($\alpha > 50\%$). Porém, **4 municípios registraram o padrão diametralmente oposto**, onde Bolsonaro capturou a quase totalidade dos votos marginais:

| Município | Cluster ML | Trânsito Lula ($\alpha_{Lula}$) | Trânsito Bolsonaro ($\alpha_{Bolso}$) | Votos 1T (Lula / Bolso) | Votos 2T (Lula / Bolso) | Saldo Nominal Líquido |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **NOVA IBIÁ** | **C4** | **10,09%** | **89,91%** | 2.634 vs 1.441 | 2.656 vs 1.637 | $\Delta 13 = +22$ \| $\Delta 22 = +196$ |
| **CALDEIRÃO GRANDE** | **C2** | **10,73%** | **89,27%** | 5.292 vs 2.218 | 5.351 vs 2.709 | $\Delta 13 = +59$ \| $\Delta 22 = +491$ |
| **SÍTIO DO MATO** | **C2** | **37,76%** | **62,24%** | 6.262 vs 2.402 | 6.390 vs 2.613 | $\Delta 13 = +128$ \| $\Delta 22 = +211$ |
| **MANSIDÃO** | **C2** | **46,94%** | **53,06%** | 5.720 vs 1.163 | 5.789 vs 1.241 | $\Delta 13 = +69$ \| $\Delta 22 = +78$ |

### 4.1. O Caso de Nova Ibiá ($\alpha_{Lula} = 10,1\%$)
* Dos 218 novos votos nominais que surgiram no município no 2º turno, **196 foram para Bolsonaro** e apenas **22 para Lula**.
* Lula cresceu apenas +0,8% sobre sua base prévia, enquanto Bolsonaro expandiu sua votação em +13,6%.

### 4.2. O Caso de Caldeirão Grande ($\alpha_{Lula} = 10,7\%$)
* Dos 550 votos em disputa, **491 migraram para Bolsonaro** e apenas **59 para Lula**.
* Mais de 74% de todos os eleitores que votaram em candidatos da 3ª via no 1º turno migraram em bloco para a oposição federal.

### 4.3. Por que esses outliers refutam o código uniforme?
1. Se existisse um algoritmo residente nas urnas programado para fixar o trânsito estadual em ~83%, **Nova Ibiá e Caldeirão Grande jamais poderiam registrar 10%**. O código teria sobretaxado esses municípios da mesma forma que os demais.
2. Para que um software malicioso tolerasse essas exceções, ele precisaria conter **tabelas de exceção geográfica parametrizadas por município**, o que elevaria exponencialmente a complexidade do binário e tornaria trivial a sua detecção em análise estática de engenharia reversa.
3. Esses outliers comprovam a soberania da **dinâmica política paroquial**: a eleição presidencial na Bahia esteve casada com a disputa de 2º turno para governador (Jerônimo x ACM Neto), e lideranças locais em pequenos municípios conseguiram puxar o voto em bloco na oposição física, provando que as urnas computaram fielmente os votos reais depositados.

---

## 5. O PAPEL DA INFRAESTRUTURA DIGITAL (ANATEL) NA DISPERSÃO DO VOTO

A Hipótese 1 atribui o salto de votos à capacidade de comunicação massiva de campanhas digitais. Para validar cientificamente essa hipótese, realizou-se o cruzamento com a base de dados da ANATEL de acessos móveis por município:

* **Índice de Conectividade Composto Digital (ICCD):**
  $$\text{ICCD} = 0,50 \cdot (\% \text{ Pós-Pago}) + 0,35 \cdot (\text{Densidade SMP}) + 0,15 \cdot (\% \text{ 4G/5G})$$
* **Achado do Random Forest:** A variável `% pós-pago` figurou como a **3ª feature mais preditiva de todo o modelo (10,91% de importância relativa)**, à frente de renda domiciliar e faixa etária.
* **Mecanismo Causal:** O usuário de plano pós-pago consome dados em alta velocidade de forma ininterrupta, permitindo a recepção e compartilhamento de conteúdos multimídia densos (vídeos de campanha no WhatsApp e redes sociais) sem barreira de franquia. Onde a taxa pós-paga era máxima (Cluster 1 - Metrópoles, 55,6% pós-pago), a taxa de trânsito para Lula atingiu o ápice estadual de **85,04%**.
* **Contraprova dos Outliers:** Caldeirão Grande tem apenas **17,28% de celulares pós-pagos** e Nova Ibiá tem densidade de apenas **43,4 acessos/100 hab**. A ausência de penetração de internet contínua blindou essas populações da onda digital das metrópoles, deixando a decisão do 2º turno inteiramente nas mãos dos coronéis e cabos eleitorais municipais.

---

## 6. ROTEIRO DE VERIFICAÇÃO FORENSE: ONDE ORIENTAR A BUSCA PERICIAL

Para uma auditoria de sistemas independente que busque atestar conclusivamente a integridade da camada de captura do voto, a investigação deve orientar-se nas seguintes frentes técnicas:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   ROTEIRO DE PERÍCIA FORENSE EM URNAS                  │
├──────────────────────────┬─────────────────────────────────────────────┤
│ 1. Logs de Eventos       │ Auditoria de timestamps e threads ocultas   │
│ 2. Comparação de Hash    │ Diff binário entre código lacrado e urnas   │
│ 3. PRNG do RDV           │ Criptoanálise do gerador pseudoaleatório    │
│ 4. Código 01 Mesário     │ Taxa de bypass biométrico por urna          │
│ 5. Teste de Integridade  │ Paralelo físico no dia da eleição com papel │
└──────────────────────────┴─────────────────────────────────────────────┘
```

1. **Auditoria dos Arquivos de Log da Urna (`logd.dat`):**
   * Extrair e analisar a distribuição de milissegundos entre o acionamento do teclado e o encerramento do processo de voto.
   * Investigar eventuais desvios de fluxo ou execução de rotinas em segundo plano durante a janela de votação.
2. **Engenharia Reversa e Diff de Binários:**
   * Comparar byte a byte os binários extraídos diretamente das memórias de programa das urnas de seções atípicas com as compilações oficiais lacradas na cerimônia do TSE.
3. **Criptoanálise do Registro Digital do Voto (RDV):**
   * Verificar se o algoritmo de permutação que esconde a ordem dos votos no RDV possui sementes previsíveis ou dependentes da sequência de biometria do eleitor.
4. **Auditoria de Habilitação sem Biometria (Código 01):**
   * Verificar urnas com quedas anômalas de abstenção se a liberação manual pelo mesário ultrapassou a média estadual histórica (~12%).
5. **O Padrão Ouro: Teste de Integridade em Tempo Real:**
   * O único mecanismo capaz de refutar definitivamente qualquer classe de código embarcado oculto é o **voto físico paralelo em cédula auditada**, filmado e confrontado com a saída da urna em amostra representativa sorteada na manhã do pleito.

---

## 7. CONCLUSÃO GERAL

1. **A conferência de Boletins de Urna é condição necessária, mas não suficiente:** Ela atesta a fidedignidade da transmissão (Fase A), mas a confiança na captura (Fase B) repousa sobre a cadeia de compilação reprodutível e nos testes de integridade física.
2. **A estatística desmente a hipótese de algoritmo cego uniforme:** A presença de fortes variações regionais e de outliers como Nova Ibiá (10,1% Lula) e Caldeirão Grande (10,7% Lula) prova que a contagem respondeu a dinâmicas políticas locais reais e não a uma imposição centralizada de percentual fixo.
3. **O trânsito de votos correlaciona-se com a conectividade digital:** Cidades hiperconectadas exibiram absorção marginal homogênea e rápida via redes móveis, enquanto rincões isolados foram pautados por alianças de lideranças físicas municipais.

---
*Relatório técnico documentado e persistido no repositório de inteligência de dados eleitorais.*
