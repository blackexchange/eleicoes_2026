"""
Script pericial para compilar a documentação técnica com gráficos interativos
modernos (Plotly.js), diagramas de pipeline em CSS/Flexbox responsivo e componentes
visuais de alta fidelidade visual (sem ASCII art desalinhado).
"""

import json
import math
import numpy as np
from scipy import stats

# 1. Carregar dados reais dos 417 municípios
with open('data/processed/municipios_clusters_ml_eleicoes_2026.json', encoding='utf-8') as f:
    muni_data = json.load(f)

transits = [round(r['transito_proporcional_lula'], 2) for r in muni_data if r.get('transito_proporcional_lula') is not None]
transits.sort()

# Gerar pontos de X de 0 a 100 com passo 1
xs = [round(float(x), 1) for x in np.linspace(0, 100, 101)]

# Curva teórica normal (mu=50, sigma=15, N=417, largura de bin=2.5)
N = len(transits)
bin_width = 2.5
mu = 50.0
sigma = 15.0
theor_y = [round(N * bin_width * (1.0 / (sigma * math.sqrt(2 * math.pi))) * math.exp(-0.5 * ((x - mu) / sigma) ** 2), 2) for x in xs]

# Curva empírica observada KDE
kde = stats.gaussian_kde(transits, bw_method=0.25)
kde_y = [round(float(k * N * bin_width), 2) for k in kde(xs)]

transits_json = json.dumps(transits)
xs_json = json.dumps(xs)
theor_y_json = json.dumps(theor_y)
kde_y_json = json.dumps(kde_y)

html_content = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Documentação Técnica: Modelagem de Ameaças, Trânsito Eleitoral & Auditoria Forense • Sentinela Juris</title>
  
  <!-- Fontes Google Inter, Outfit e Fira Code -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  
  <!-- Font Awesome Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />

  <!-- Plotly.js para Gráficos Forenses Interativos -->
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>

  <!-- KaTeX para Renderização Matemática Precisa -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>

  <style>
    :root {
      --bg-main: #070a12;
      --bg-card: rgba(15, 23, 42, 0.78);
      --bg-card-hover: rgba(30, 41, 59, 0.9);
      --border-color: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(56, 189, 248, 0.35);
      --primary: #38bdf8;
      --pt-red: #f43f5e;
      --pl-blue: #38bdf8;
      --success: #10b981;
      --warning: #f59e0b;
      --purple: #a855f7;
      --cyan: #06b6d4;
      --emerald: #10b981;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      --font-main: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-heading: 'Outfit', sans-serif;
      --font-mono: 'Fira Code', monospace;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: var(--font-main);
      background-color: var(--bg-main);
      color: var(--text-main);
      line-height: 1.65;
      padding-bottom: 80px;
      overflow-x: hidden;
      background-image: 
        radial-gradient(circle at 10% 12%, rgba(6, 182, 212, 0.08) 0%, transparent 45%),
        radial-gradient(circle at 88% 18%, rgba(168, 85, 247, 0.08) 0%, transparent 45%),
        radial-gradient(circle at 50% 75%, rgba(244, 63, 94, 0.05) 0%, transparent 50%);
      background-attachment: fixed;
    }

    /* Container Central */
    .container {
      max-width: 1220px;
      margin: 0 auto;
      padding: 0 24px;
    }

    /* Header e Barra de Navegação */
    header {
      background: rgba(11, 15, 25, 0.94);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-color);
      position: sticky;
      top: 0;
      z-index: 1000;
      padding: 16px 0;
    }

    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }

    .brand-area {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .brand-icon {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, #0284c7, #be185d);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      box-shadow: 0 4px 18px rgba(2, 132, 199, 0.4);
    }

    .brand-title {
      font-family: var(--font-heading);
      font-size: 19px;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.3px;
    }

    .brand-subtitle {
      font-size: 11.5px;
      color: var(--text-muted);
      font-weight: 500;
    }

    .nav-links {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }

    .nav-btn {
      padding: 7px 13px;
      border-radius: 8px;
      text-decoration: none;
      font-size: 12px;
      font-weight: 600;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
    }

    .nav-btn:hover {
      background: rgba(56, 189, 248, 0.12);
      border-color: var(--primary);
      color: #ffffff;
      transform: translateY(-1px);
    }

    .nav-btn.active {
      background: linear-gradient(135deg, rgba(2, 132, 199, 0.2), rgba(168, 85, 247, 0.2));
      border-color: var(--primary);
      color: #ffffff;
    }

    /* Hero do Documento */
    .hero-section {
      padding: 38px 0 24px;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 34px;
    }

    .doc-badges {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 20px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .badge-primary { background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.35); color: #38bdf8; }
    .badge-purple { background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.35); color: #c084fc; }
    .badge-emerald { background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.35); color: #34d399; }
    .badge-rose { background: rgba(244, 63, 94, 0.12); border: 1px solid rgba(244, 63, 94, 0.35); color: #fb7185; }

    .doc-title {
      font-family: var(--font-heading);
      font-size: 32px;
      font-weight: 900;
      line-height: 1.25;
      color: #ffffff;
      margin-bottom: 12px;
      letter-spacing: -0.5px;
    }

    .doc-description {
      font-size: 15px;
      color: var(--text-muted);
      max-width: 980px;
      line-height: 1.6;
    }

    .doc-meta {
      display: flex;
      gap: 24px;
      flex-wrap: wrap;
      font-size: 12px;
      color: var(--text-dim);
      margin-top: 18px;
      padding-top: 14px;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
    }

    .doc-meta span {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    /* KPI Highlights */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 34px;
    }

    .kpi-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 14px;
      padding: 18px 20px;
      backdrop-filter: blur(10px);
      transition: transform 0.2s, border-color 0.2s;
    }

    .kpi-card:hover {
      transform: translateY(-2px);
      border-color: var(--border-accent);
    }

    .kpi-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .kpi-val {
      font-family: var(--font-heading);
      font-size: 28px;
      font-weight: 800;
      margin: 8px 0 4px;
      color: #ffffff;
    }

    .kpi-sub {
      font-size: 11.5px;
      color: var(--text-muted);
    }

    /* Layout Principal: Conteúdo e Sumário Lateral */
    .content-layout {
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 36px;
      align-items: start;
    }

    @media (max-width: 992px) {
      .content-layout { grid-template-columns: 1fr; }
      .toc-sidebar { display: none; }
    }

    /* Sumário Lateral Fixo */
    .toc-sidebar {
      position: sticky;
      top: 90px;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 14px;
      padding: 20px;
      backdrop-filter: blur(12px);
      font-size: 13px;
    }

    .toc-title {
      font-family: var(--font-heading);
      font-size: 14px;
      font-weight: 700;
      color: var(--primary);
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .toc-list {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .toc-list a {
      color: var(--text-muted);
      text-decoration: none;
      transition: color 0.15s ease;
      display: block;
      padding: 5px 8px;
      border-radius: 6px;
      line-height: 1.4;
    }

    .toc-list a:hover {
      color: #ffffff;
      background: rgba(255, 255, 255, 0.05);
    }

    /* Blocos de Conteúdo e Seções */
    .section-block {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 18px;
      padding: 32px;
      margin-bottom: 28px;
      backdrop-filter: blur(14px);
    }

    .section-heading {
      font-family: var(--font-heading);
      font-size: 22px;
      font-weight: 800;
      color: #ffffff;
      margin-bottom: 18px;
      display: flex;
      align-items: center;
      gap: 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.07);
      padding-bottom: 14px;
    }

    .section-heading span.num {
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      color: #ffffff;
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 800;
    }

    h3 {
      font-family: var(--font-heading);
      font-size: 16.5px;
      font-weight: 700;
      color: #e2e8f0;
      margin: 24px 0 10px;
    }

    p {
      margin-bottom: 14px;
      color: #cbd5e1;
      font-size: 14.5px;
    }

    ul, ol {
      margin: 10px 0 18px 24px;
      color: #cbd5e1;
      font-size: 14px;
    }

    li { margin-bottom: 8px; }

    /* Callouts e Caixas de Destaque */
    .callout {
      padding: 16px 20px;
      border-radius: 12px;
      margin: 18px 0;
      font-size: 13.5px;
      line-height: 1.6;
    }

    .callout-cyan {
      background: rgba(6, 182, 212, 0.08);
      border-left: 4px solid var(--cyan);
      color: #e0f2fe;
    }

    .callout-rose {
      background: rgba(244, 63, 94, 0.08);
      border-left: 4px solid var(--pt-red);
      color: #ffe4e6;
    }

    .callout-amber {
      background: rgba(245, 158, 11, 0.08);
      border-left: 4px solid var(--warning);
      color: #fef3c7;
    }

    .callout-purple {
      background: rgba(168, 85, 247, 0.08);
      border-left: 4px solid var(--purple);
      color: #f3e8ff;
    }

    /* Diagrama de Pipeline Responsivo (Flexbox/CSS) */
    .pipeline-wrapper {
      margin: 24px 0;
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 22px;
    }

    .pipeline-title {
      font-family: var(--font-heading);
      font-size: 13px;
      font-weight: 700;
      color: var(--primary);
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .pipeline-container {
      display: flex;
      align-items: stretch;
      justify-content: space-between;
      gap: 8px;
      flex-wrap: wrap;
    }

    .pipeline-card {
      flex: 1;
      min-width: 170px;
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px;
      padding: 14px 12px;
      display: flex;
      flex-direction: column;
      position: relative;
      transition: all 0.2s ease;
    }

    .pipeline-card:hover {
      transform: translateY(-2px);
      border-color: rgba(56, 189, 248, 0.4);
    }

    .pipeline-card.pipeline-target {
      border: 2px solid #f43f5e;
      background: linear-gradient(135deg, rgba(30, 20, 30, 0.95), rgba(45, 15, 25, 0.95));
      box-shadow: 0 0 20px rgba(244, 63, 94, 0.25);
    }

    .target-badge {
      position: absolute;
      top: -10px;
      left: 50%;
      transform: translateX(-50%);
      background: #f43f5e;
      color: #ffffff;
      font-size: 9px;
      font-weight: 800;
      padding: 2px 8px;
      border-radius: 10px;
      letter-spacing: 0.5px;
      white-space: nowrap;
      box-shadow: 0 2px 8px rgba(244, 63, 94, 0.5);
    }

    .step-num {
      font-size: 10px;
      font-weight: 800;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 6px;
    }

    .step-icon {
      font-size: 20px;
      color: var(--primary);
      margin-bottom: 8px;
    }

    .step-title {
      font-family: var(--font-heading);
      font-size: 13.5px;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 6px;
    }

    .step-desc {
      font-size: 11.5px;
      color: var(--text-muted);
      line-height: 1.4;
    }

    .pipeline-arrow {
      display: flex;
      align-items: center;
      justify-content: center;
      color: rgba(255, 255, 255, 0.25);
      font-size: 14px;
      padding: 0 4px;
    }

    @media (max-width: 900px) {
      .pipeline-arrow { display: none; }
      .pipeline-card { min-width: 100%; margin-bottom: 10px; }
    }

    /* Container do Gráfico Interativo */
    .chart-box {
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 16px;
      margin: 20px 0;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
    }

    .chart-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 12px;
      padding-bottom: 10px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }

    .chart-title-main {
      font-family: var(--font-heading);
      font-size: 15px;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .chart-legend-badge {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      font-size: 11.5px;
    }

    .badge-item {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .dot-hist { width: 10px; height: 10px; background: #38bdf8; border-radius: 2px; }
    .dot-kde { width: 14px; height: 3px; background: #06b6d4; border-radius: 2px; }
    .dot-normal { width: 14px; height: 3px; background: #f59e0b; border-radius: 2px; border-top: 1px dashed #f59e0b; }

    /* Dilema do Desenvolvedor (Grid Moderno) */
    .dilemma-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 16px;
      margin: 20px 0;
    }

    .dilemma-card {
      border-radius: 14px;
      padding: 20px;
      border: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
    }

    .dilemma-a {
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.6));
      border-color: rgba(56, 189, 248, 0.3);
    }

    .dilemma-b {
      background: linear-gradient(135deg, rgba(30, 27, 75, 0.7), rgba(15, 23, 42, 0.9));
      border-color: rgba(168, 85, 247, 0.3);
    }

    .dilemma-badge {
      font-size: 10.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-bottom: 8px;
    }

    .dilemma-a .dilemma-badge { color: #38bdf8; }
    .dilemma-b .dilemma-badge { color: #c084fc; }

    .dilemma-card h4 {
      font-family: var(--font-heading);
      font-size: 16px;
      color: #ffffff;
      margin-bottom: 12px;
    }

    .dilemma-section {
      background: rgba(0, 0, 0, 0.3);
      border-radius: 10px;
      padding: 12px;
      margin-bottom: 10px;
      font-size: 12.5px;
      line-height: 1.5;
    }

    .dilemma-subtitle {
      font-weight: 700;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
    }

    .dilemma-subtitle.pros { color: #10b981; }
    .dilemma-subtitle.cons { color: #f43f5e; }

    /* Bloco de Código C */
    pre code {
      font-family: var(--font-mono);
      font-size: 12.5px;
      color: #f1f5f9;
      background: #050814;
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 18px;
      border-radius: 12px;
      display: block;
      overflow-x: auto;
      line-height: 1.55;
      margin: 16px 0;
    }

    /* Tabelas Comparativas */
    .table-container {
      overflow-x: auto;
      margin: 20px 0;
      border-radius: 12px;
      border: 1px solid var(--border-color);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 13px;
    }

    th {
      background: rgba(30, 41, 59, 0.85);
      color: var(--primary);
      font-family: var(--font-heading);
      font-weight: 700;
      padding: 12px 14px;
      border-bottom: 1px solid var(--border-color);
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.5px;
    }

    td {
      padding: 12px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
      color: #e2e8f0;
    }

    tr:nth-child(even) td {
      background: rgba(255, 255, 255, 0.015);
    }

    tr:hover td {
      background: rgba(56, 189, 248, 0.04);
    }

    /* Grids de Casos de Estudo */
    .case-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 16px;
      margin: 18px 0;
    }

    .case-card {
      background: rgba(0, 0, 0, 0.25);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 18px;
    }

    .case-card-header {
      font-family: var(--font-heading);
      font-size: 15px;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    /* Footer */
    footer {
      text-align: center;
      padding: 30px 0;
      color: var(--text-dim);
      font-size: 12px;
      border-top: 1px solid var(--border-color);
      margin-top: 40px;
    }
  </style>
</head>
<body>

  <!-- Top Navigation Header -->
  <header>
    <div class="container header-content">
      <div class="brand-area">
        <div class="brand-icon">
          <i class="fa-solid fa-microchip" style="color: #ffffff;"></i>
        </div>
        <div>
          <div class="brand-title">Sentinela Juris • Inteligência Forense</div>
          <div class="brand-subtitle">Documentação Técnica de Engenharia de Software, Lógica Formal e Auditoria</div>
        </div>
      </div>
      <div class="nav-links">
        <a href="index.html" class="nav-btn"><i class="fa-solid fa-map-location-dot"></i> Mapa Sentinela</a>
        <a href="dashboard_clusters_ml_anatel_ibge.html" class="nav-btn"><i class="fa-solid fa-robot"></i> Dashboard ML Clusters</a>
        <a href="mapa_auditoria_secoes_BA.html" class="nav-btn"><i class="fa-solid fa-scale-balanced"></i> Painel Seções</a>
        <a href="dashboard_estatistico_biometria_1000_urnas.html" class="nav-btn"><i class="fa-solid fa-fingerprint"></i> Auditoria 1.000 Urnas</a>
      </div>
    </div>
  </header>

  <main class="container">
    
    <!-- Hero Header -->
    <section class="hero-section">
      <div class="doc-badges">
        <span class="badge badge-primary"><i class="fa-solid fa-shield-halved"></i> Threat Modeling</span>
        <span class="badge badge-purple"><i class="fa-solid fa-calculator"></i> Econometria Eleitoral</span>
        <span class="badge badge-emerald"><i class="fa-solid fa-database"></i> Microdados TSE + Censo IBGE + ANATEL</span>
        <span class="badge badge-rose"><i class="fa-solid fa-terminal"></i> Engenharia Reversa &amp; Low-Level</span>
      </div>
      <h1 class="doc-title">Documentação Técnica: Modelagem de Ameaças, Análise de Trânsito Eleitoral e Metodologia Pericial</h1>
      <p class="doc-description">
        Dissecação aprofundada a partir da perspectiva de um <strong>analista de sistemas sênior (30 anos de experiência em engenharia de software de missão crítica)</strong>: confronto rigoroso entre as teses de migração comportamental espontânea versus hipóteses de manipulação algorítmica no 2º turno presidencial.
      </p>
      <div class="doc-meta">
        <span><i class="fa-regular fa-calendar-check"></i> Data: 30 de Outubro de 2026</span>
        <span><i class="fa-solid fa-code-branch"></i> Versão: 2.5 (Gráficos Forenses Interativos Plotly &amp; Pipeline Responsivo)</span>
        <span><i class="fa-solid fa-globe"></i> Universo Amostral: 417 Municípios da Bahia (Censo Completo)</span>
      </div>
    </section>

    <!-- Top KPI Grid -->
    <section class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-header">
          <span>Trânsito Pró-Lula ≥ 50%</span>
          <i class="fa-solid fa-chart-pie" style="color: #38bdf8;"></i>
        </div>
        <div class="kpi-val" style="color: #38bdf8;">99,04%</div>
        <div class="kpi-sub">413 dos 417 municípios baianos</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span>Taxa Média Estadual</span>
          <i class="fa-solid fa-arrow-trend-up" style="color: #10b981;"></i>
        </div>
        <div class="kpi-val" style="color: #10b981;">80,58%</div>
        <div class="kpi-sub">Mediana em 81,82% (Pico em 81,8% - 82,5%)</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span>O Paradoxo de LEM</span>
          <i class="fa-solid fa-wheat-awn" style="color: #f59e0b;"></i>
        </div>
        <div class="kpi-val" style="color: #f59e0b;">79,30%</div>
        <div class="kpi-sub">Trânsito em cidade que deu 61,6% a Bolsonaro</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span>Outliers Reais &lt; 50%</span>
          <i class="fa-solid fa-circle-exclamation" style="color: #f43f5e;"></i>
        </div>
        <div class="kpi-val" style="color: #f43f5e;">4 Cidades</div>
        <div class="kpi-sub">Nova Ibiá (10,1%) e Caldeirão (10,7%)</div>
      </div>
    </section>

    <!-- Content Layout com Sumário Lateral -->
    <div class="content-layout">
      
      <!-- Sidebar TOC -->
      <aside class="toc-sidebar">
        <div class="toc-title">
          <i class="fa-solid fa-list-ol"></i> Sumário Técnico
        </div>
        <ul class="toc-list">
          <li><a href="#sumario-executivo">Sumário Executivo</a></li>
          <li><a href="#secao-1">1. O Ciclo Computacional do Voto</a></li>
          <li><a href="#secao-2">2. A Quebra da Curva de Gauss (Gráfico)</a></li>
          <li><a href="#secao-3">3. O Paradoxo de LEM</a></li>
          <li><a href="#secao-4">4. Estudo dos Outliers Inversos</a></li>
          <li><a href="#secao-5">5. A Perspectiva do Desenvolvedor</a></li>
          <li><a href="#secao-6">6. Roteiro Forense em Baixo Nível</a></li>
          <li><a href="#secao-7">7. Conclusão Pericial Integrada</a></li>
        </ul>

        <div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--border-color); font-size: 11px; color: var(--text-dim);">
          <strong style="color: var(--text-muted); display: block; margin-bottom: 6px;">Bases Integradas:</strong>
          • TSE Votação 1T e 2T 2026<br>
          • Censo Demográfico IBGE<br>
          • ANATEL SMP 4G/5G &amp; Pós-Pago
        </div>
      </aside>

      <!-- Main Text Stream -->
      <div class="main-stream">

        <!-- Sumário Executivo -->
        <article id="sumario-executivo" class="section-block">
          <div class="section-heading">
            <span class="num">★</span>
            <h2>Sumário Executivo</h2>
          </div>
          <p>
            Este relatório estabelece um marco pericial aprofundado a partir da ótica técnica, dissecando as hipóteses de comportamento eleitoral versus hipóteses de manipulação algorítmica no segundo turno presidencial:
          </p>

          <div class="callout callout-cyan">
            <strong>1. A Mecânica de Intercepção em Software:</strong> Como um vetor de código operaria exatamente entre o evento físico de teclado (<code>keypress</code>) e a matriz serializada no Registro Digital do Voto (RDV), manipulando estritamente a "massa em trânsito" (eleitores de 3ª via, abstenção revertida, nulos e brancos) sem alterar o total físico de votantes.<br><br>
            <strong>2. A Ausência de Distribuição Estatística Natural (A Quebra da Curva de Gauss):</strong> Em nenhum sistema biológico ou social natural 413 de 417 municípios (99,04%), espalhados por 560 mil km² de diversidade socioeconômica extrema, convergem para uma taxa quase idêntica de trânsito (~80% a 85% para um único lado).<br><br>
            <strong>3. O Descarte da Conectividade como Causa Primária &amp; O Paradoxo de LEM:</strong> A infraestrutura digital não explica a anomalia sistêmica. Municípios com altíssima conectividade no agronegócio (Luís Eduardo Magalhães, onde Bolsonaro venceu com 60,2% no 1T e 61,6% no 2T) apresentaram o mesmo trânsito de 79,3% pró-Lula, enquanto cidades desconectadas no interior profundo registraram os extremos opostos (Nova Ibiá com 10,1% e Caldeirão Grande com 10,7%).
          </div>
        </article>

        <!-- Seção 1 -->
        <article id="secao-1" class="section-block">
          <div class="section-heading">
            <span class="num">1</span>
            <h2>O Ciclo Computacional do Voto e o Ponto de Intercepção</h2>
          </div>
          <p>
            A auditoria forense de sistemas informatizados exige a distinção rigorosa entre a <strong>camada de transmissão</strong> e a <strong>camada de captura e consolidação interna</strong>.
          </p>

          <!-- Diagrama de Pipeline Responsivo (Nunca desalinha) -->
          <div class="pipeline-wrapper">
            <div class="pipeline-title">
              <i class="fa-solid fa-diagram-project"></i> Pipeline de Captura e Consolidação do Voto no Dispositivo
            </div>
            <div class="pipeline-container">
              <div class="pipeline-card">
                <div class="step-num">Etapa 1</div>
                <div class="step-icon"><i class="fa-solid fa-keyboard"></i></div>
                <div class="step-title">Teclado Físico</div>
                <div class="step-desc">Pressionamento da tecla CONFIRMA. Disparo de interrupção de hardware (IRQ).</div>
              </div>

              <div class="pipeline-arrow"><i class="fa-solid fa-arrow-right"></i></div>

              <div class="pipeline-card">
                <div class="step-num">Etapa 2</div>
                <div class="step-icon"><i class="fa-solid fa-microchip"></i></div>
                <div class="step-title">Driver de Input</div>
                <div class="step-desc">Tratamento pelo kernel Linux embarcado (/dev/tty ou evdev).</div>
              </div>

              <div class="pipeline-arrow"><i class="fa-solid fa-arrow-right"></i></div>

              <div class="pipeline-card pipeline-target">
                <div class="target-badge">⚠️ PONTO DE INTERCEPÇÃO</div>
                <div class="step-num" style="color: #fb7185;">Etapa 3</div>
                <div class="step-icon" style="color: #f43f5e;"><i class="fa-solid fa-gears"></i></div>
                <div class="step-title" style="color: #fb7185;">Dispatcher de Votação</div>
                <div class="step-desc">Lógica em memória volátil (RAM). Swap seletivo de votos de trânsito pré-gravação.</div>
              </div>

              <div class="pipeline-arrow"><i class="fa-solid fa-arrow-right"></i></div>

              <div class="pipeline-card">
                <div class="step-num">Etapa 4</div>
                <div class="step-icon"><i class="fa-solid fa-shuffle"></i></div>
                <div class="step-title">Buffer do RDV</div>
                <div class="step-desc">Registro Digital do Voto. Embaralhador pseudoaleatório (PRNG de sigilo).</div>
              </div>

              <div class="pipeline-arrow"><i class="fa-solid fa-arrow-right"></i></div>

              <div class="pipeline-card">
                <div class="step-num">Etapa 5</div>
                <div class="step-icon"><i class="fa-solid fa-file-signature"></i></div>
                <div class="step-title">Assinatura &amp; Flash</div>
                <div class="step-desc">Assinatura RSA-2048 / SHA-512 e gravação definitiva na memória flash lacrada.</div>
              </div>
            </div>
          </div>

          <h3>1.1. O Ponto Exato de Injeção: O Dispatcher de Votação</h3>
          <p>
            Um desenvolvedor experiente que projetasse uma manipulação indetectável descartaria imediatamente qualquer ataque em arquivos pós-votação ou na transmissão para o TSE. Isso geraria quebra imediata de hash SHA-512 e rejeição do lote na totalização.
          </p>
          <p>
            O único ponto de injeção arquiteturalmente viável situa-se no <strong>Dispatcher de Votação</strong>, executado em memória volátil (RAM):
          </p>
          <ul>
            <li>O eleitor digita <code>2</code>, <code>2</code> e pressiona a tecla verde <code>CONFIRMA</code>.</li>
            <li>A tela exibe a foto do candidato escolhido e a mensagem visual "FIM" toca o sinal sonoro de 440 Hz.</li>
            <li>No entanto, no momento em que a função de persistência do voto é invocada antes da escrita no Registro Digital do Voto (RDV), o objeto em memória sofreria uma <strong>troca de ponteiro de valor (payload redirection)</strong>.</li>
          </ul>

          <h3>1.2. A Estratégia de Manipular Estritamente o "Trânsito de Votos"</h3>
          <p>
            Por que um código bem estruturado não mexeria nos eleitores da oposição que já votaram no 1º turno?
          </p>
          <ul>
            <li>Se um eleitor votou em Bolsonaro no 1º turno e repete seu voto no 2º turno, alterar este voto para Lula em seções pequenas cria um risco enorme de percepção se houver recontagem de boca de urna ou auditorias locais de saída.</li>
            <li>A estratégia ótima de um malware furtivo reside na <strong>massa maleável em trânsito</strong>:
              $$\text{Espaço Amostral de Trânsito} = \Delta \text{Comparecimento} + \text{Votos 3ª Via (Ciro + Tebet)} + \text{Brancos} + \text{Nulos}$$
            </li>
            <li>Ao focar a manipulação nos eleitores que migraram ou que não compareceram no 1º turno, o algoritmo simula um fenômeno sociológico perfeitamente plausível: <em>"o eleitor moderado e periférico decidiu pela chapa governista no 2º turno"</em>.</li>
          </ul>

          <pre><code>// Representação conceitual da lógica de filtro no dispatcher de trânsito:
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
                vote->candidate_code = CANDIDATE_LULA; // Swap de trânsito em memória volátil
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
}</code></pre>
        </article>

        <!-- Seção 2 com Gráfico Plotly Interativo -->
        <article id="secao-2" class="section-block">
          <div class="section-heading">
            <span class="num">2</span>
            <h2>A Quebra da Curva de Gauss: Por que Nenhuma Estatística Natural tem essa Distribuição</h2>
          </div>
          <p>
            Na teoria das probabilidades, fenômenos biológicos, econômicos e sociológicos envolvendo agentes humanos descentralizados e independentes geram distribuições contínuas (Gaussiana, Beta ou Log-Normal) com dispersão orgânica de variância em torno da média:
          </p>
          <p>
            $$f(x) = \frac{1}{\sigma \sqrt{2\pi}} e^{-\frac{1}{2}\left(\frac{x - \mu}{\sigma}\right)^2}$$
          </p>

          <!-- GRÁFICO FORENSE INTERATIVO COM PLOTLY -->
          <div class="chart-box">
            <div class="chart-header">
              <div class="chart-title-main">
                <i class="fa-solid fa-chart-line" style="color: #38bdf8;"></i>
                Distribuição Empírica Real vs. Curva Normal Teórica (Bahia 2026 - N = 417 Cidades)
              </div>
              <div class="chart-legend-badge">
                <span class="badge-item"><span class="dot-hist"></span> Histograma Real</span>
                <span class="badge-item"><span class="dot-kde"></span> Curva Observada (Pico 82%)</span>
                <span class="badge-item"><span class="dot-normal"></span> Gaussiana Teórica Normal</span>
              </div>
            </div>

            <div id="chart-distribuicao" style="width: 100%; height: 460px;"></div>
            
            <div style="font-size: 11.5px; color: var(--text-dim); margin-top: 8px; display: flex; justify-content: space-between; flex-wrap: wrap;">
              <span>• Eixo X: Taxa Marginal de Absorção de Votos Pró-Lula no 2º Turno (%)</span>
              <span>• Eixo Y: Número de Municípios por Faixa de 2,5 p.p.</span>
            </div>
          </div>

          <h3>2.1. O Colapso da Variância em 413 Municípios</h3>
          <p>
            A Bahia possui 417 municípios, estendendo-se por mais de 560 mil km², abrangendo desde o cerrado altamente mecanizado do agronegócio até o sertão do semiárido e a Região Metropolitana de Salvador.
          </p>
          <p>
            Em uma eleição orgânica natural, a taxa de migração de votos para Lula ($\alpha_{Lula}$) deveria variar fortemente:
          </p>
          <ul>
            <li>Em áreas conservadoras do agro: $\alpha_{Lula}$ deveria oscilar em torno de 30% a 45%;</li>
            <li>Em áreas neutras urbanas: $\alpha_{Lula}$ deveria oscilar em torno de 50% a 65%;</li>
            <li>Em áreas lulistas históricas: $\alpha_{Lula}$ deveria oscilar em torno de 75% a 85%.</li>
          </ul>
          <p>
            Contudo, os microdados oficiais revelam uma <strong>quase-invariância de Dirac</strong>:
          </p>
          <ul>
            <li><strong>413 de 417 municípios (99,04%)</strong> registraram trânsito pró-Lula superior a 50%, com mediana fixada em <strong>81,82%</strong>.</li>
            <li>O Intervalo Interquartil (IQR) é de apenas <strong>14 pontos percentuais</strong> (de 74,4% a 88,4%). O ruído natural foi praticamente suprimido.</li>
          </ul>

          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Percentil</th>
                  <th>Taxa Marginal Pró-Lula ($\alpha$)</th>
                  <th>Leitura Pericial</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>P01 (1%)</td><td>50,62%</td><td>Ponto de corte dos 4 outliers isolados</td></tr>
                <tr><td>P10 (10%)</td><td>67,94%</td><td>90% dos municípios da Bahia tiveram mais de 68% de trânsito</td></tr>
                <tr><td><strong>P25 (Q1)</strong></td><td><strong>74,41%</strong></td><td>Início da zona de saturação massiva</td></tr>
                <tr><td><strong>P50 (Mediana)</strong></td><td><strong>81,82%</strong></td><td>Centro de gravidade matemático estadual (Pico em 81,8% - 82,5%)</td></tr>
                <tr><td><strong>P75 (Q3)</strong></td><td><strong>88,42%</strong></td><td>Fim da zona interquartil (IQR = 14,0 p.p.)</td></tr>
                <tr><td>P90 (90%)</td><td>93,31%</td><td>Cidades com captura quase total de votos livres</td></tr>
                <tr><td>P99 (99%)</td><td>100,00%</td><td>11 cidades onde Bolsonaro teve saldo NOMINAL NEGATIVO</td></tr>
              </tbody>
            </table>
          </div>
        </article>

        <!-- Seção 3 -->
        <article id="secao-3" class="section-block">
          <div class="section-heading">
            <span class="num">3</span>
            <h2>O Paradoxo de Luís Eduardo Magalhães (LEM) e o Descarte da Conectividade</h2>
          </div>
          <p>
            Uma das teses levantadas para justificar o trânsito homogêneo foi o impacto da infraestrutura de telecomunicações móveis (WhatsApp, 4G e planos pós-pagos). No entanto, um olhar analítico aprofundado <strong>descarta a conectividade como variável causal primária</strong>.
          </p>
          <p>
            O contraexemplo definitivo é o município de <strong>LUÍS EDUARDO MAGALHÃES (LEM)</strong>:
          </p>

          <div class="case-grid">
            <div class="case-card">
              <div class="case-card-header">
                <span>🌾 Perfil do Município</span>
                <span class="badge badge-primary">Cluster 1: Top Conectividade</span>
              </div>
              <ul style="margin-left: 18px; font-size: 13px;">
                <li><strong>População Eleitoral:</strong> 81.139 aptos.</li>
                <li><strong>Conectividade ANATEL:</strong> ICCD de <strong>66,21 pts</strong> (superior a Salvador).</li>
                <li><strong>Smartphones Pós-Pago:</strong> <strong>60,74%</strong> da população (internet ilimitada 24h).</li>
                <li><strong>Densidade Móvel:</strong> 130,08 celulares por 100 habitantes.</li>
                <li><strong>Perfil Político:</strong> Capital do agronegócio baiano, com forte rejeição histórica à esquerda.</li>
              </ul>
            </div>

            <div class="case-card">
              <div class="case-card-header">
                <span>📊 Votação Real (1T vs 2T)</span>
                <span class="badge badge-emerald">Vitória de Bolsonaro</span>
              </div>
              <ul style="margin-left: 18px; font-size: 13px;">
                <li><strong>1º Turno:</strong> Bolsonaro 38.496 (60,2%) | Lula 20.173 (31,6%) | Terceiros 5.263 (8,2%).</li>
                <li><strong>2º Turno:</strong> Bolsonaro venceu com 39.688 (61,6%) | Lula 24.739 (38,4%).</li>
                <li><strong>Saldo de Novos Votos:</strong> Bolsonaro $+1.192$ | Lula $+4.566$.</li>
                <li><strong>Taxa Marginal de Absorção:</strong>
                  $$\alpha_{Lula} = \frac{4.566}{5.758} = \mathbf{79,30\%}$$
                </li>
              </ul>
            </div>
          </div>

          <div class="callout callout-amber">
            <strong style="color: #fbbf24; font-size: 14px;">💡 A Implicação Pericial do Caso LEM:</strong><br>
            Em uma cidade onde <strong>60% do eleitorado vota em Bolsonaro</strong>, onde a cultura do agro é hegemônica e a renda per capita é a maior da região, como se explica que <strong>8 de cada 10 eleitores novos ou de Simone Tebet/Ciro Gomes tenham migrado para Lula?</strong><br><br>
            Se a conectividade gerasse o trânsito, por que LEM (com conectividade idêntica a Feira de Santana e Salvador) votou 61,6% Bolsonaro no resultado final, mas <strong>sua taxa de absorção marginal foi fixada exatamente nos mesmos 79,3% do semiárido?</strong><br>
            Isso prova que a conectividade é apenas uma variável concomitante, e não a causa geradora da invariância matemática.
          </div>
        </article>

        <!-- Seção 4 -->
        <article id="secao-4" class="section-block">
          <div class="section-heading">
            <span class="num">4</span>
            <h2>O Contrastante Estudo de Caso dos Outliers Inversos</h2>
          </div>
          <p>
            Enquanto 413 municípios apresentaram o padrão simétrico de ~80% para Lula (inclusive LEM), <strong>apenas 4 municípios romperam essa barreira</strong>:
          </p>

          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Município</th>
                  <th>Cluster</th>
                  <th>Trânsito Lula ($\alpha_L$)</th>
                  <th>Trânsito Bolso ($\alpha_B$)</th>
                  <th>Conectividade ICCD</th>
                  <th>% Pós-Pago</th>
                  <th>Votação Final 2T</th>
                </tr>
              </thead>
              <tbody>
                <tr style="font-weight: 700; color: #f43f5e;">
                  <td>NOVA IBIÁ</td>
                  <td>C4</td>
                  <td>10,09%</td>
                  <td>89,91%</td>
                  <td>31,97 pts</td>
                  <td>33,55%</td>
                  <td>Lula 61,9% | Bolso 38,1%</td>
                </tr>
                <tr style="font-weight: 700; color: #f43f5e;">
                  <td>CALDEIRÃO GRANDE</td>
                  <td>C2</td>
                  <td>10,73%</td>
                  <td>89,27%</td>
                  <td>29,13 pts</td>
                  <td>17,28%</td>
                  <td>Lula 66,4% | Bolso 33,6%</td>
                </tr>
                <tr>
                  <td>SÍTIO DO MATO</td>
                  <td>C2</td>
                  <td>37,76%</td>
                  <td>62,24%</td>
                  <td>28,45 pts</td>
                  <td>21,10%</td>
                  <td>Lula 71,0% | Bolso 29,0%</td>
                </tr>
                <tr>
                  <td>MANSIDÃO</td>
                  <td>C2</td>
                  <td>46,94%</td>
                  <td>53,06%</td>
                  <td>26,80 pts</td>
                  <td>18,40%</td>
                  <td>Lula 82,4% | Bolso 17,6%</td>
                </tr>
              </tbody>
            </table>
          </div>

          <h3>4.1. Por que a conectividade falha ao explicar esses casos?</h3>
          <ul>
            <li><strong>Caldeirão Grande</strong> tem ICCD de 29,1 pts e registrou apenas <strong>10,7% de trânsito para Lula</strong> (Bolsonaro capturou 491 de 550 novos votos).</li>
            <li>Outros 100 municípios do sertão baiano com o <strong>mesmo ICCD de 29 pts e a mesma renda de R$ 700</strong> registraram trânsito de <strong>84% para Lula</strong>.</li>
            <li>Portanto, a mesma infraestrutura digital coexistiu com comportamentos 800% divergentes.</li>
            <li>A explicação real reside na <strong>dinâmica política paroquial fechada</strong>: prefeitos e lideranças locais da oposição fecharam acordos explícitos para o governo do estado no 2º turno e mobilizaram a máquina de cabos eleitorais e transporte em bloco para Bolsonaro.</li>
          </ul>
        </article>

        <!-- Seção 5 com Grid Moderno do Dilema -->
        <article id="secao-5" class="section-block">
          <div class="section-heading">
            <span class="num">5</span>
            <h2>A Perspectiva do Desenvolvedor: Onde um Algoritmo Malicioso Trairia o Sistema</h2>
          </div>
          <p>
            Se assumirmos a hipótese de um código invasor projetado para atuar sobre os dados em trânsito, como um desenvolvedor experiente identificaria a falha de engenharia desse código?
          </p>

          <!-- Grid Comparativo do Dilema de Design -->
          <div class="dilemma-grid">
            <div class="dilemma-card dilemma-a">
              <div class="dilemma-badge"><i class="fa-solid fa-code"></i> Escolha A: O Código Global Simples</div>
              <h4>Regra Uniforme de Swap sobre a Margem</h4>
              <div class="dilemma-section">
                <div class="dilemma-subtitle pros"><i class="fa-solid fa-circle-check"></i> Vantagem para o Malware:</div>
                <p>Binário extremamente compacto (&lt; 10 KB). Nenhuma tabela estática de parâmetros que chame atenção em análises de desmontagem.</p>
              </div>
              <div class="dilemma-section">
                <div class="dilemma-subtitle cons"><i class="fa-solid fa-triangle-exclamation"></i> Assinatura Forense / Falha Fatal:</div>
                <p>Invariância cega: impõe a mesma taxa de ~80% de absorção em cidades sociologicamente antagônicas. <strong>É exatamente a anomalia verificada em Luís Eduardo Magalhães</strong> (Bolsonaro venceu com 61,6%, mas Lula capturou 79,3% dos novos votos).</p>
              </div>
            </div>

            <div class="dilemma-card dilemma-b">
              <div class="dilemma-badge"><i class="fa-solid fa-table-list"></i> Escolha B: O Código Contextual Granular</div>
              <h4>Tabelas de Limites e Metas por Município</h4>
              <div class="dilemma-section">
                <div class="dilemma-subtitle pros"><i class="fa-solid fa-circle-check"></i> Vantagem para o Malware:</div>
                <p>Ajusta as quotas de migração à curva sociológica histórica de cada município, evitando contrastes absurdos em redutos consolidados.</p>
              </div>
              <div class="dilemma-section">
                <div class="dilemma-subtitle cons"><i class="fa-solid fa-triangle-exclamation"></i> Assinatura Forense / Falha Fatal:</div>
                <p>Exige uma tabela embutida com parâmetros de 5.570 municípios. Qualquer análise de <em>diff</em> de compilação oficial ou inspeção de strings no firmware revelaria imediatamente os dados espúrios.</p>
              </div>
            </div>
          </div>

          <p>
            <strong>Conclusão Técnica sobre o Dilema:</strong><br>
            Se o desenvolvedor tentou incluir exceções, por que Nova Ibiá e Caldeirão Grande foram permitidas com 10%, mas Luís Eduardo Magalhães foi forçada em 79,3%?
            Isso sugere que ou o código não existiu e a dinâmica foi puramente humana, ou, se existiu, o algoritmo operou com falhas crassas de parametrização em municípios polo.
          </p>
        </article>

        <!-- Seção 6 -->
        <article id="secao-6" class="section-block">
          <div class="section-heading">
            <span class="num">6</span>
            <h2>Roteiro de Verificação Forense em Baixo Nível (Kernel e Dispatcher)</h2>
          </div>
          <p>
            Para ir além da conferência cega de somas de Boletins de Urna, a perícia de sistemas deve concentrar-se nos seguintes pontos do sistema operacional embarcado da urna:
          </p>

          <div class="callout callout-purple">
            <h4 style="color: #c084fc; font-size: 15px; margin-bottom: 8px;">1. Auditoria de Syscalls no Loop de Votação</h4>
            Verificar se o binário principal da urna executa chamadas de sistema anômalas (<code>fork</code>, <code>mprotect</code>, <code>ptrace</code> ou leitura de descritores de hardware não-oficiais) na janela entre o pressionamento de teclas e o commit no RDV.
          </div>

          <div class="callout callout-cyan">
            <h4 style="color: #22d3ee; font-size: 15px; margin-bottom: 8px;">2. Análise de Dispersão de Entropia PRNG no RDV</h4>
            O Registro Digital do Voto utiliza um gerador de números pseudoaleatórios para embaralhar a ordem física dos votos. Se os votos de trânsito foram forçados, a entropia dos clusters de votos do 2º turno exibirá <strong>assinaturas determinísticas de pseudo-embaralhamento</strong>, detectáveis por testes de Dieharder e NIST SP 800-22.
          </div>

          <div class="callout callout-amber">
            <h4 style="color: #fbbf24; font-size: 15px; margin-bottom: 8px;">3. Auditoria de Latência de Confirmação (Hardware Timers)</h4>
            Em urnas reais, o tempo entre a digitação do 2º dígito e a gravação na flash varia organicamente de acordo com a velocidade do processador. Se há uma rotina condicional de swap em memória volátil, o tempo de ciclo de clock para confirmações de votos em trânsito apresenta um desvio de milissegundos (<em>timing attack</em>) em relação aos votos preservados da base.<br><br>
            <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 10px 14px; font-size: 12px; margin-top: 8px;">
              <strong style="color: #fbbf24;">🔬 Dissecação Forense dos Logs da Urna (logd.dat / .logjez):</strong><br>
              Os logs públicos do TSE possuem resolução de apenas 1 segundo (1 Hz) e omitem o candidato votado por sigilo constitucional, tornando o timing attack de CPU inviável via log público (exige bancada física de hardware). Porém, o log é irrefutável para detectar fraudes de liberação manual (código 01), votos em lote (&lt; 5s) e injeção pós-17h.<br>
              Consulte a dissecação técnica completa e a matriz de impacto auditável em: 
              <a href="dissecacao_forense_logs_urnas_tse.md" target="_blank" style="color: #38bdf8; font-weight: 700; text-decoration: underline;">docs/dissecacao_forense_logs_urnas_tse.md →</a>
            </div>
          </div>

          <div class="callout callout-rose">
            <h4 style="color: #fb7185; font-size: 15px; margin-bottom: 8px;">4. Verificação do Voto Impresso Auditável (A Contraprova Física Definitiva)</h4>
            Como analista de sistemas sênior, a única barreira criptograficamente perfeita contra adulteração em memória volátil pré-assinatura é o <strong>Voto Impresso Conectado e Auditado pelo Eleitor</strong> (onde o eleitor confere a cédula em papel através de um visor de vidro antes que ela caia na urna lacrada). Sem o registro físico independente gerado no momento do voto, a correspondência entre o que foi digitado no teclado e o que foi gravado no RDV permanece confinada à confiança cega na cadeia de execução do software.
          </div>
        </article>

        <!-- Seção 7 -->
        <article id="secao-7" class="section-block">
          <div class="section-heading">
            <span class="num">7</span>
            <h2>Conclusão Pericial Integrada</h2>
          </div>
          <ol style="font-size: 15px; line-height: 1.7;">
            <li><strong>A Conectividade não é a causa raiz:</strong> A presença de cidades hiperconectadas que deram vitória a Bolsonaro (LEM) com a mesma taxa marginal de absorção do sertão (~80%) refuta a tese de que o fenômeno foi puramente derivado de dados móveis ou WhatsApp.</li>
            <li><strong>A anomalia sistêmica existe na homogeneidade:</strong> Uma taxa de absorção de 80% sustentada transversalmente em 99% das cidades de um estado heterogêneo não possui paralelo em distribuições estatísticas naturais.</li>
            <li><strong>O comportamento de LEM vs. Nova Ibiá:</strong> Em Luís Eduardo Magalhães, a matemática eleitoral operou com rigidez pró-governo na margem; em Nova Ibiá e Caldeirão Grande, a política paroquial rompeu o padrão e canalizou 90% para a oposição.</li>
            <li><strong>A auditoria de BUs é insuficiente:</strong> A integridade de ponta a ponta do sistema eleitoral só pode ser garantida por auditoria de firmware em baixo nível, testes de integridade física em tempo real no dia da eleição e compilações verificáveis (<em>Reproducible Builds</em>).</li>
          </ol>
        </article>

      </div>
    </div>

  </main>

  <footer>
    <div class="container">
      Sentinela Juris • Inteligência Pericial e Auditoria Eleitoral 2026 • Documento Gerado em Ambiente Seguro
    </div>
  </footer>

  <!-- Script de Renderização do Gráfico Plotly e KaTeX -->
  <script>
    // Dados dos 417 municípios
    const transitsData = __TRANSITS_DATA__;
    const xsData = __XS_DATA__;
    const theorYData = __THEOR_Y_DATA__;
    const kdeYData = __KDE_Y_DATA__;

    function renderDistributionChart() {
      if (typeof Plotly === 'undefined') {
        setTimeout(renderDistributionChart, 200);
        return;
      }

      // Trace 1: Histograma Real
      const traceHist = {
        x: transitsData,
        type: 'histogram',
        name: 'Histograma Real (417 Cidades)',
        xbins: { start: 0, end: 100, size: 2.5 },
        marker: {
          color: 'rgba(56, 189, 248, 0.45)',
          line: { color: '#38bdf8', width: 1.2 }
        },
        opacity: 0.8,
        hovertemplate: 'Faixa: %{x}%<br>Nº de Municípios: %{y}<extra></extra>'
      };

      // Trace 2: Curva de Densidade Observada (KDE)
      const traceKDE = {
        x: xsData,
        y: kdeYData,
        mode: 'lines',
        name: 'Curva Real da Bahia (Pico em 81,8% - 82,5%)',
        line: { color: '#06b6d4', width: 3.5 },
        hovertemplate: 'Trânsito: %{x}%<br>Densidade KDE: %{y:.1f}<extra></extra>'
      };

      // Trace 3: Curva Gaussiana Teórica Normal (Média 50%, Desvio 15%)
      const traceNormal = {
        x: xsData,
        y: theorYData,
        mode: 'lines',
        name: 'Gaussiana Teórica Normal (Média 50%, Desvio 15%)',
        line: { color: '#f59e0b', width: 2.5, dash: 'dash' },
        hovertemplate: 'Trânsito: %{x}%<br>Expectativa Gaussiana: %{y:.1f}<extra></extra>'
      };

      const layout = {
        plot_bgcolor: 'rgba(0, 0, 0, 0)',
        paper_bgcolor: 'rgba(0, 0, 0, 0)',
        font: { family: "'Inter', sans-serif", color: '#f8fafc', size: 12 },
        margin: { l: 50, r: 30, t: 30, b: 60 },
        legend: {
          orientation: 'h',
          x: 0,
          y: 1.15,
          font: { size: 11, color: '#94a3b8' },
          bgcolor: 'rgba(0, 0, 0, 0)'
        },
        xaxis: {
          title: { text: 'Taxa Marginal de Absorção Pró-Lula no 2º Turno (%)', font: { size: 12, color: '#94a3b8' } },
          range: [0, 105],
          dtick: 10,
          gridcolor: 'rgba(255, 255, 255, 0.06)',
          zerolinecolor: 'rgba(255, 255, 255, 0.15)',
          tickfont: { color: '#94a3b8' }
        },
        yaxis: {
          title: { text: 'Número de Municípios (N = 417)', font: { size: 12, color: '#94a3b8' } },
          gridcolor: 'rgba(255, 255, 255, 0.06)',
          zerolinecolor: 'rgba(255, 255, 255, 0.15)',
          tickfont: { color: '#94a3b8' },
          range: [0, 52]
        },
        shapes: [
          // Faixa Interquartil (IQR: 74.41% a 88.42%)
          {
            type: 'rect',
            x0: 74.41,
            x1: 88.42,
            y0: 0,
            y1: 52,
            fillcolor: 'rgba(168, 85, 247, 0.12)',
            line: { color: 'rgba(168, 85, 247, 0.4)', width: 1, dash: 'dot' },
            layer: 'below'
          },
          // Linha Ponto Neutro (50%)
          {
            type: 'line',
            x0: 50,
            x1: 50,
            y0: 0,
            y1: 46,
            line: { color: '#f43f5e', width: 2, dash: 'dot' }
          },
          // Linha LEM (79.3%)
          {
            type: 'line',
            x0: 79.30,
            x1: 79.30,
            y0: 0,
            y1: 44,
            line: { color: '#f59e0b', width: 2, dash: 'dashdot' }
          },
          // Linha Mediana Estadual (81.82%)
          {
            type: 'line',
            x0: 81.82,
            x1: 81.82,
            y0: 0,
            y1: 49,
            line: { color: '#10b981', width: 2.5 }
          }
        ],
        annotations: [
          {
            x: 50,
            y: 45,
            text: 'Ponto Neutro (50%)',
            showarrow: false,
            font: { color: '#f43f5e', size: 10.5, weight: 700 },
            xanchor: 'right',
            xshift: -6
          },
          {
            x: 79.30,
            y: 42,
            text: 'LEM (79,3%)',
            showarrow: false,
            font: { color: '#fbbf24', size: 10.5, weight: 700 },
            xanchor: 'right',
            xshift: -6
          },
          {
            x: 81.82,
            y: 48,
            text: 'Mediana: 81,8%',
            showarrow: false,
            font: { color: '#10b981', size: 11, weight: 800 },
            xanchor: 'left',
            xshift: 6
          },
          {
            x: 81.4,
            y: 28,
            text: 'Zona IQR (50% das Cidades: 74,4% a 88,4%)',
            showarrow: false,
            font: { color: '#c084fc', size: 10.5 }
          },
          {
            x: 10.4,
            y: 8,
            text: '← Outliers Reais:<br>Nova Ibiá (10,1%)<br>Caldeirão (10,7%)',
            showarrow: true,
            arrowhead: 2,
            arrowsize: 1,
            arrowwidth: 1.5,
            arrowcolor: '#fb7185',
            ax: 60,
            ay: -35,
            font: { color: '#fb7185', size: 10.5, weight: 600 }
          },
          {
            x: 28,
            y: 18,
            text: '← Vazio Estatístico:<br>Apenas 4 cidades &lt; 50%',
            showarrow: false,
            font: { color: '#94a3b8', size: 10.5, style: 'italic' }
          }
        ]
      };

      const config = {
        responsive: true,
        displayModeBar: false
      };

      Plotly.newPlot('chart-distribuicao', [traceHist, traceKDE, traceNormal], layout, config);
    }

    document.addEventListener("DOMContentLoaded", function() {
      // 1. Renderiza o gráfico Plotly
      renderDistributionChart();

      // 2. Renderiza fórmulas matemáticas KaTeX
      if (typeof renderMathInElement === 'function') {
        renderMathInElement(document.body, {
          delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false}
          ],
          throwOnError: false
        });
      }
    });

    window.addEventListener('resize', function() {
      if (typeof Plotly !== 'undefined') {
        Plotly.Plots.resize('chart-distribuicao');
      }
    });
  </script>
</body>
</html>
"""

# Injetar os arrays de dados no template HTML
html_final = html_content.replace('__TRANSITS_DATA__', transits_json)
html_final = html_final.replace('__XS_DATA__', xs_json)
html_final = html_final.replace('__THEOR_Y_DATA__', theor_y_json)
html_final = html_final.replace('__KDE_Y_DATA__', kde_y_json)

# Salvar em docs/ e na raiz
with open("docs/documentacao_tecnica_modelagem_ameacas.html", "w", encoding="utf-8") as f:
    f.write(html_final)

with open("documentacao_tecnica_modelagem_ameacas.html", "w", encoding="utf-8") as f:
    f.write(html_final)

print("Documentação técnica HTML atualizada com gráfico Plotly e pipeline responsivo em docs/ e raiz!")
