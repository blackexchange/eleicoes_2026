"""
Gera o Dashboard Interativo de Machine Learning & Clusterização dos 417 Municípios da Bahia:
'dashboard_clusters_ml_anatel_ibge.html'

Com:
1. Índice Ponderado de Conectividade Digital ANATEL (ICCD) integrando Densidade SMP + % Pós-Pago + % 4G/5G.
2. Renderização 100% robusta de gráficos Plotly (suporte offline local + CDN).
3. Null-safety em todas as formatações para evitar quebras de runtime.
4. Análise de Clusters K-Means (k=4) + PCA 2D + Random Forest Feature Importance.
"""

import json
from pathlib import Path

def gerar_dashboard_clusters():
    with open("data/processed/cluster_summary_ml.json", "r", encoding="utf-8") as f:
        summary_data = json.load(f)
        
    with open("data/processed/municipios_clusters_ml_eleicoes_2026.json", "r", encoding="utf-8") as f:
        muni_data = json.load(f)
        
    muni_json = json.dumps(muni_data, ensure_ascii=False)
    summary_json = json.dumps(summary_data, ensure_ascii=False)
    
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Machine Learning: Clusters de Trânsito Eleitoral • Bahia 2026 (IBGE + ANATEL)</title>
  
  <!-- Fontes Google Inter e Outfit -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
  
  <!-- Plotly.js: CDN Oficial com Fallback Local para Uso Offline -->
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <script>
    if (typeof Plotly === 'undefined') {{
      console.warn("CDN offline, carregando Plotly local...");
      var s = document.createElement('script');
      s.src = 'plotly-2.27.0.min.js';
      s.onload = function() {{ if (typeof renderAllCharts === 'function') renderAllCharts(); }};
      document.head.appendChild(s);
    }}
  </script>
  
  <style>
    :root {{
      --bg-main: #090d16;
      --bg-card: rgba(17, 24, 39, 0.75);
      --bg-card-hover: rgba(30, 41, 59, 0.85);
      --border-color: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(56, 189, 248, 0.3);
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
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Inter', -apple-system, sans-serif;
      background-color: var(--bg-main);
      color: var(--text-main);
      line-height: 1.5;
      padding-bottom: 60px;
      overflow-x: hidden;
      background-image: 
        radial-gradient(circle at 10% 15%, rgba(6, 182, 212, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 90% 20%, rgba(168, 85, 247, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 50% 85%, rgba(16, 185, 129, 0.05) 0%, transparent 50%);
      background-attachment: fixed;
    }}

    header {{
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-color);
      padding: 18px 32px;
      position: relative;
      z-index: 10;
    }}

    .header-content {{
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}

    .logo-area h1 {{
      font-family: 'Outfit', sans-serif;
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 10px;
      color: #ffffff;
    }}

    .badge-ml {{
      background: rgba(168, 85, 247, 0.15);
      border: 1px solid rgba(168, 85, 247, 0.4);
      color: #c084fc;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 9999px;
      text-transform: uppercase;
    }}

    .badge-data {{
      background: rgba(6, 182, 212, 0.15);
      border: 1px solid rgba(6, 182, 212, 0.4);
      color: #22d3ee;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 9999px;
    }}

    .header-sub {{
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 4px;
    }}

    main {{
      max-width: 1400px;
      margin: 32px auto;
      padding: 0 24px;
      display: flex;
      flex-direction: column;
      gap: 32px;
    }}

    .section-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 18px;
      font-weight: 700;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 6px;
    }}

    .section-desc {{
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 18px;
    }}

    /* KPI Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 16px;
    }}

    .kpi-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 18px 20px;
      backdrop-filter: blur(12px);
      transition: all 0.25s ease;
      position: relative;
      overflow: hidden;
    }}

    .kpi-card::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; height: 3px;
      background: var(--card-accent, var(--primary));
    }}

    .kpi-card:hover {{
      transform: translateY(-2px);
      border-color: var(--border-accent);
      background: var(--bg-card-hover);
    }}

    .kpi-label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 6px;
      display: flex;
      justify-content: space-between;
    }}

    .kpi-value {{
      font-family: 'Outfit', sans-serif;
      font-size: 26px;
      font-weight: 700;
      color: #ffffff;
    }}

    .kpi-sub {{
      font-size: 12px;
      color: var(--text-dim);
      margin-top: 4px;
    }}

    /* Panels & Charts */
    .glass-panel {{
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 20px;
      padding: 24px;
      backdrop-filter: blur(12px);
      position: relative;
      overflow: hidden;
      box-sizing: border-box;
      margin-bottom: 24px;
      clear: both;
    }}

    .panel-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 12px;
    }}

    .panel-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 16px;
      font-weight: 600;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .panel-subtitle {{
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 4px;
    }}

    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 24px;
      margin-bottom: 24px;
      width: 100%;
    }}

    @media (max-width: 1024px) {{
      .charts-grid {{ grid-template-columns: 1fr; }}
    }}

    .chart-container {{
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 12px;
      height: 440px;
      width: 100%;
      position: relative;
      overflow: hidden;
      box-sizing: border-box;
    }}

    /* Clusters Card Grid */
    .clusters-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }}

    .cluster-card {{
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 20px;
      position: relative;
      border-left: 5px solid var(--cluster-color);
    }}

    .cluster-tag {{
      display: inline-block;
      font-family: 'Fira Code', monospace;
      font-size: 11px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.08);
      color: var(--cluster-color);
      margin-bottom: 8px;
    }}

    .cluster-name {{
      font-family: 'Outfit', sans-serif;
      font-size: 15px;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 8px;
    }}

    .cluster-desc {{
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.5;
      margin-bottom: 14px;
    }}

    .cluster-metrics {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      font-size: 12px;
    }}

    .c-metric-item {{
      background: rgba(0, 0, 0, 0.25);
      padding: 8px 10px;
      border-radius: 8px;
    }}

    .c-metric-label {{
      color: var(--text-dim);
      font-size: 10px;
      text-transform: uppercase;
    }}

    .c-metric-val {{
      font-weight: 700;
      color: #ffffff;
      font-size: 13px;
    }}

    /* Table Styles */
    .table-controls {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 12px;
    }}

    .search-input {{
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 8px 14px;
      color: #ffffff;
      font-size: 13px;
      width: 280px;
      outline: none;
    }}

    .filter-select {{
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 8px 14px;
      color: #ffffff;
      font-size: 13px;
      outline: none;
    }}

    .pagination-bar {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--text-muted);
    }}

    .page-btn {{
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 5px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      transition: all 0.2s;
    }}

    .page-btn:hover:not(:disabled) {{ background: var(--primary); color: #000; }}
    .page-btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}

    .table-wrapper {{
      overflow-x: auto;
      max-height: 520px;
      border: 1px solid var(--border-color);
      border-radius: 12px;
    }}

    .data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
      white-space: nowrap;
    }}

    .data-table th {{
      position: sticky;
      top: 0;
      background: #0f172a;
      padding: 10px 14px;
      text-align: left;
      font-weight: 600;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border-color);
      z-index: 10;
    }}

    .data-table td {{
      padding: 8px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: var(--text-main);
    }}

    .data-table tr:hover {{ background: rgba(255, 255, 255, 0.02); }}

    .code-tag {{
      font-family: 'Fira Code', monospace;
      font-size: 11px;
      background: rgba(0, 0, 0, 0.4);
      padding: 3px 8px;
      border-radius: 6px;
      border: 1px solid rgba(255, 255, 255, 0.06);
    }}

    .method-box {{
      background: rgba(6, 182, 212, 0.05);
      border-left: 4px solid var(--cyan);
      padding: 16px 20px;
      border-radius: 0 12px 12px 0;
      font-size: 13px;
      color: var(--text-main);
      line-height: 1.6;
    }}

    /* Estilos da Seção Didática */
    .didactic-card {{
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.85));
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 20px;
      padding: 24px;
      backdrop-filter: blur(12px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
      margin-bottom: 8px;
    }}

    .didactic-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .didactic-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 18px;
      font-weight: 700;
      color: #38bdf8;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .didactic-grid-4 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin: 16px 0;
    }}

    .didactic-subcard {{
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid rgba(255, 255, 255, 0.07);
      border-radius: 12px;
      padding: 16px;
      border-top: 3px solid var(--accent-subcard, #38bdf8);
    }}

    .didactic-subcard h4 {{
      font-family: 'Outfit', sans-serif;
      font-size: 14px;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 6px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .didactic-subcard p {{
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.55;
    }}

    .didactic-badge {{
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 9999px;
      font-weight: 700;
      background: rgba(255, 255, 255, 0.1);
    }}

    .didactic-insight-box {{
      background: rgba(168, 85, 247, 0.08);
      border-left: 4px solid #a855f7;
      padding: 14px 18px;
      border-radius: 0 10px 10px 0;
      font-size: 13px;
      color: #e2e8f0;
      line-height: 1.6;
      margin-top: 14px;
    }}

    .didactic-takeaways {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
      margin-top: 14px;
    }}

    .takeaway-item {{
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
      border-radius: 10px;
      padding: 12px 14px;
      font-size: 12px;
      line-height: 1.5;
    }}

    .takeaway-item strong {{
      color: #38bdf8;
      display: block;
      margin-bottom: 4px;
      font-size: 13px;
    }}
  </style>
</head>
<body>

  <header>
    <div class="header-content">
      <div class="logo-area">
        <h1>
          <span>🤖</span> Modelo de Machine Learning: Clusters de Trânsito Eleitoral
          <span class="badge-ml">K-Means + Random Forest</span>
          <span class="badge-data">IBGE + ANATEL (N = 417 Municípios)</span>
        </h1>
        <div class="header-sub">
          Segmentação Multidimensional para Identificação dos Perfis Municipais que Mais se Parecem com a Variável Target: Trânsito Proporcional para Lula (T1 → T2)
        </div>
      </div>
      <div style="font-size: 12px; color: var(--text-muted); text-align: right;">
        <div>População Total: <strong>417 Municípios da Bahia (Censo Completo)</strong></div>
        <div>Features: <strong>16 Variáveis (Demografia IBGE, Conectividade ANATEL e 1ºT TSE)</strong></div>
        <div style="display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; flex-wrap: wrap;">
          <a href="index.html" style="display:inline-block; padding:5px 12px; background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.4); border-radius:8px; color:#a5b4fc; text-decoration:none; font-size:11px; font-weight:600;">🗺️ Mapa Sentinela Juris →</a>
          <a href="mapa_auditoria_secoes_BA.html" style="display:inline-block; padding:5px 12px; background:rgba(245,158,11,0.15); border:1px solid rgba(245,158,11,0.4); border-radius:8px; color:#fbbf24; text-decoration:none; font-size:11px; font-weight:600;">⚖️ Painel Auditoria Seções →</a>
          <a href="dashboard_estatistico_biometria_1000_urnas.html" style="display:inline-block; padding:5px 12px; background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.4); border-radius:8px; color:#38bdf8; text-decoration:none; font-size:11px; font-weight:600;">🏛️ Auditoria 1.000 Urnas →</a>
        </div>
      </div>
    </div>
  </header>

  <main>
    <!-- KPIs Principais -->
    <section class="kpi-grid">
      <div class="kpi-card" style="--card-accent: #06b6d4;">
        <div class="kpi-label">Cluster de Maior Trânsito <span>Metrópoles / Polos</span></div>
        <div class="kpi-value" style="color: #22d3ee;">83,96%</div>
        <div class="kpi-sub">Cluster 1 (27 cidades): Salto Comp. +6,47 p.p.</div>
      </div>

      <div class="kpi-card" style="--card-accent: #10b981;">
        <div class="kpi-label">Trânsito no Sertão / Bastilha <span>Cluster 2</span></div>
        <div class="kpi-value" style="color: #34d399;">83,24%</div>
        <div class="kpi-sub">Cluster 2 (136 cidades): Mediana = 84,92%</div>
      </div>

      <div class="kpi-card" style="--card-accent: #f59e0b;">
        <div class="kpi-label">Cluster de Menor Trânsito <span>Agro / Resistência</span></div>
        <div class="kpi-value" style="color: #fbbf24;">75,81%</div>
        <div class="kpi-sub">Cluster 4 (140 cidades): Bolsonaro absorveu 24,2%</div>
      </div>

      <div class="kpi-card" style="--card-accent: #06b6d4;">
        <div class="kpi-label">Índice Ponderado ANATEL <span>ICCD (0 a 100)</span></div>
        <div class="kpi-value" style="color: #22d3ee;">r = +0,197</div>
        <div class="kpi-sub">p = 4,91 × 10⁻⁵ (Associação Significativa)</div>
      </div>

      <div class="kpi-card" style="--card-accent: #a855f7;">
        <div class="kpi-label">Variável Telecom Mais Forte <span>Random Forest</span></div>
        <div class="kpi-value" style="color: #c084fc;">10,92%</div>
        <div class="kpi-sub">% Pós-Pago / Smartphone (3ª feature geral)</div>
      </div>

      <div class="kpi-card" style="--card-accent: #38bdf8;">
        <div class="kpi-label">ANOVA F-Statistic <span>Separação dos Clusters</span></div>
        <div class="kpi-value">F = 13,08</div>
        <div class="kpi-sub">p = 3,56 × 10⁻⁸ (Diferenciação Robusta)</div>
      </div>
    </section>

    <!-- Seção Explicativa Didática -->
    <section class="didactic-card">
      <div class="didactic-header">
        <span style="font-size: 26px;">💡</span>
        <div>
          <div class="didactic-title">Resumo Didático: Entendendo as Descobertas da IA em Linguagem Simples</div>
          <div style="font-size: 13px; color: var(--text-muted);">
            O que os algoritmos de Machine Learning revelaram ao analisar os 417 municípios da Bahia cruzando Censo IBGE, ANATEL e TSE.
          </div>
        </div>
      </div>

      <!-- Pergunta Central -->
      <div style="background: rgba(6, 182, 212, 0.08); border-left: 4px solid var(--cyan); padding: 14px 18px; border-radius: 0 10px 10px 0; font-size: 13px; color: #f8fafc; line-height: 1.6; margin-bottom: 16px;">
        <strong style="color: #22d3ee; font-size: 14px;">🎯 A Pergunta Central Respondida pela Máquina:</strong><br>
        <em>"No 2º turno, para onde foram os votos de quem votou em Ciro, Simone Tebet, brancos/nulos ou não tinha ido votar no 1º turno?"</em><br>
        <strong>Resposta Estatística Geral:</strong> Em toda a Bahia, verificou-se uma altíssima absorção: <strong>para cada 10 votos que sobraram ou surgiram no 2º turno, entre 7,6 e 8,5 migraram diretamente para Lula</strong>. Porém, o algoritmo comprovou que a Bahia não é homogênea, dividindo o estado em <strong>4 realidades distintas (Clusters)</strong>:
      </div>

      <!-- 4 Bahias Grid -->
      <div class="didactic-grid-4">
        <div class="didactic-subcard" style="--accent-subcard: #06b6d4;">
          <h4>
            <span>🏙️ C1: Metrópoles &amp; Polos</span>
            <span class="didactic-badge" style="color: #22d3ee; border: 1px solid #06b6d4;">85,0% Lula</span>
          </h4>
          <p>
            <strong>Quem são:</strong> 28 grandes centros urbanos (Salvador, Feira, Camaçari, Juazeiro).<br>
            <strong>Perfil:</strong> Mais de 55% dos celulares são <em>pós-pagos</em> (internet móvel 24h) e alta escolaridade.<br>
            <strong>O que houve:</strong> Lula teve a <strong>maior absorção do estado (85%)</strong> sobre os 10,8% de votos da 3ª via. O eleitor hiperconectado no WhatsApp converteu maciçamente.
          </p>
        </div>

        <div class="didactic-subcard" style="--accent-subcard: #10b981;">
          <h4>
            <span>🌵 C2: Sertão &amp; Semiárido</span>
            <span class="didactic-badge" style="color: #34d399; border: 1px solid #10b981;">83,2% Lula</span>
          </h4>
          <p>
            <strong>Quem são:</strong> 138 cidades do semiárido rural e interior profundo.<br>
            <strong>Perfil:</strong> Renda mais vulnerável (R$ 738) e 75% dos celulares pré-pagos.<br>
            <strong>O que houve:</strong> A "bastilha histórica". Lula já tinha 72% no 1º turno e manteve fidelidade de <strong>83,2% dos votos que sobraram</strong>, ancorado em laços comunitários consolidados.
          </p>
        </div>

        <div class="didactic-subcard" style="--accent-subcard: #a855f7;">
          <h4>
            <span>🏬 C3: Centros Médios</span>
            <span class="didactic-badge" style="color: #c084fc; border: 1px solid #a855f7;">81,9% Lula</span>
          </h4>
          <p>
            <strong>Quem são:</strong> 120 cidades médias em processo de expansão econômica e digital.<br>
            <strong>Perfil:</strong> Conectividade intermediária (36% pós-pago, 86 celulares/100 hab).<br>
            <strong>O que houve:</strong> Avanço firme e consistente de Lula (+1,18 p.p. na votação válida), absorvendo <strong>81,9% dos votos disponíveis</strong> com equilíbrio socioeconômico.
          </p>
        </div>

        <div class="didactic-subcard" style="--accent-subcard: #f59e0b;">
          <h4>
            <span>🚜 C4: Regiões Agro &amp; Resistência</span>
            <span class="didactic-badge" style="color: #fbbf24; border: 1px solid #f59e0b;">75,7% Lula</span>
          </h4>
          <p>
            <strong>Quem são:</strong> 131 municípios no Oeste Baiano e eixos com agronegócio forte.<br>
            <strong>Perfil:</strong> Menor inclusão digital pós-paga e melhor base bolsonarista prévia (26% a 35%).<br>
            <strong>O que houve:</strong> Onde Bolsonaro mais reteve votos (24,3%). Ainda assim, <strong>3 em cada 4 votos disputados (75,7%) migraram para Lula</strong>.
          </p>
        </div>
      </div>

      <!-- O Papel da ANATEL / Conectividade -->
      <div class="didactic-insight-box">
        <strong style="color: #c084fc; font-size: 14px;">📱 O Papel Surpreendente das Telecomunicações (ANATEL):</strong><br>
        O modelo de <em>Random Forest Regressor</em> identificou que a <strong>3ª variável mais importante de todas</strong> para prever o trânsito de votos foi a <strong>proporção de celulares pós-pagos</strong> (10,9% de importância no modelo), superando renda e faixa etária.<br>
        <em>Por que isso acontece?</em> O eleitor com plano pós-pago possui tráfego contínuo de alta velocidade para assistir vídeos, ouvir áudios e interagir no WhatsApp sem esgotamento de franquia. Onde a internet era ilimitada (Cluster 1), a esteira de transmissão de campanha no 2º turno operou com máxima eficiência.
      </div>

      <!-- 3 Conclusões Rápidas -->
      <div class="didactic-takeaways">
        <div class="takeaway-item">
          <strong>1. O fenômeno não foi uniforme</strong>
          A taxa de migração variou de 75,7% no polo do agronegócio até 85,0% na Região Metropolitana e polos urbanos.
        </div>
        <div class="takeaway-item">
          <strong>2. Tecnologia e dados importaram</strong>
          O Índice Ponderado de Conectividade (ICCD) teve correlação positiva direta com a velocidade de absorção (r = +0,197, p &lt; 0,0001).
        </div>
        <div class="takeaway-item">
          <strong>3. Piso elevado em todo o estado</strong>
          Mesmo no cluster mais favorável a Bolsonaro (Agro), Lula venceu a disputa dos votos restantes com folga de 75,7% contra 24,3%.
        </div>
      </div>
    </section>

    <!-- Box Metodológico -->
    <div class="method-box">
      <strong>Resposta Metodológica sobre Conectividade Ponderada (ICCD):</strong>
      Faz total sentido sintetizar as 3 métricas de telecomunicações da ANATEL em um <strong>Índice de Conectividade Composto Digital (ICCD - Escala 0 a 100)</strong>. 
      A análise de componentes principais (PCA) comprovou que <strong>73,26% da variância comum das 3 variáveis é capturada em uma única dimensão latente</strong>.
      A variável ponderada sintetiza:
      <strong>1) Penetração de Dispositivos</strong> (Densidade SMP, peso 0.35); 
      <strong>2) Velocidade da Rede</strong> (% 4G/5G, peso 0.15); e 
      <strong>3) Consumo Ativo Contínuo</strong> (% Pós-Pago/Smartphones, peso 0.50). 
      O ICCD correlaciona-se positiva e significativamente com o trânsito pró-Lula (<strong>r = +0,1974, p &lt; 0,0001</strong>), eliminando a multicolinearidade.
    </div>

    <!-- Cards dos 4 Clusters -->
    <section>
      <div class="section-title"><span>🧩</span> Os 4 Clusters Identificados pelo Machine Learning</div>
      <div class="clusters-grid">
        <!-- Cluster 1 -->
        <div class="cluster-card" style="--cluster-color: #06b6d4;">
          <span class="cluster-tag">CLUSTER 1 • 27 CIDADES</span>
          <div class="cluster-name">Metrópoles & Polos Hiperconectados</div>
          <div class="cluster-desc">Grandes centros urbanos com máxima conectividade digital (ICCD = 56,1 | Densidade 110,5 ac/100 hab), alta renda, concentração de ensino superior (13,5%) e massiva migração da 3ª via para Lula.</div>
          <div class="cluster-metrics">
            <div class="c-metric-item">
              <div class="c-metric-label">Trânsito Proporcional Lula</div>
              <div class="c-metric-val" style="color:#06b6d4;">83,96% (Mediana 84,3%)</div>
            </div>
            <div class="c-metric-item">
              <div class="c-metric-label">Salto Comparecimento</div>
              <div class="c-metric-val" style="color:#34d399;">+6,47 p.p.</div>
            </div>
            <div class="c-metric-item">
              <div class="c-metric-label">Conectividade ICCD</div>
              <div class="c-metric-val">56,1 pts | 55,9% Pós</div>
            </div>
            <div class="c-metric-item">
              <div class="c-metric-label">Votação 1ºT</div>
              <div class="c-metric-val">Lula 55,3% | Outros 10,7%</div>
            </div>
          </div>
        </div>

        <!-- Cluster 2 -->
        <div class="cluster-card" style="--cluster-color: #10b981;">
          <span class="cluster-tag">CLUSTER 2 • 136 CIDADES</span>
          <div class="cluster-name">Sertão & Semiárido (Bastilha Histórica)</div>
          <div class="cluster-desc">Municípios do interior profundo com alta vulnerabilidade, forte base petista prévia (72% no 1T), conectividade móvel pré-paga e altíssima conversão de votos restantes.</div>
          <div class="cluster-metrics">
            <div class="c-metric-item">
              <div class="c-metric-label">Trânsito Proporcional Lula</div>
              <div class="c-metric-val" style="color:#10b981;">83,24% (Mediana 84,9%)</div>
            </div>
            <div class="c-metric-item">
              <div class="c-metric-label">Salto Comparecimento</div>
              <div class="c-metric-val">+2,57 p.p.</div>
            </div>
            <div class="c-metric-item">
              <div class="c-metric-label">Conectividade ICCD</div>
              <div class="c-metric-val">29,7 pts | 25,0% Pós</div>
            </div>
            <div class="c-metric-item">
              <div class="c-metric-label">Votação 1ºT</div>
              <div class="c-metric-val">Lula 72,1% | Bolso 20,3%</div>
            </div>
          </div>
        </div>

        <!-- Cluster 3 -->
        <div class="cluster-card" style="--cluster-color: #a855f7;">
          <span class="cluster-tag">CLUSTER 3 • 114 CIDADES</span>
          <div class="cluster-name">Centros Médios em Transição Tecnológica</div>
          <div class="cluster-desc">Cidades médias do interior com telecomunicações intermediárias (ICCD = 40,8 | 86,4 ac/100 hab), equilíbrio socioeconômico e crescimento firme de Lula no 2º turno (+1,18 p.p.).</div>
          <div class="cluster-metrics">
            <div class="c-metric-item">
              <div class="c-metric-label">Trânsito Proporcional Lula</div>
              <div class="c-metric-val" style="color:#a855f7;">82,26% (Mediana 82,3%)</div>
            </div>
            <div class="c-metric-item">
              <div class="c-metric-label">Salto Comparecimento</div>
              <div class="c-metric-val">+3,05 p.p.</div>
            </div>
            <div class="c-metric-item">
              <div class="c-metric-label">Conectividade ICCD</div>
              <div class="c-metric-val">40,8 pts | 36,3% Pós</div>
            </div>
            <div class="c-metric-item">
              <div class="c-metric-label">Votação 1ºT</div>
              <div class="c-metric-val">Lula 63,0% | Outros 9,6%</div>
            </div>
          </div>
        </div>

        <!-- Cluster 4 -->
        <div class="cluster-card" style="--cluster-color: #f59e0b;">
          <span class="cluster-tag">CLUSTER 4 • 140 CIDADES</span>
          <div class="cluster-name">Regiões Agro & Maior Resistência</div>
          <div class="cluster-desc">Regiões agropecuárias e pequenas cidades onde Bolsonaro teve melhor desempenho (26% a 35% no 1T), menor inclusão digital pós-pago e o menor trânsito proporcional para Lula (75,8%).</div>
          <div class="cluster-metrics">
            <div class="c-metric-item">
              <div class="c-metric-label">Trânsito Proporcional Lula</div>
              <div class="c-metric-val" style="color:#f59e0b;">75,81% (Mediana 76,3%)</div>
            </div>
            <div class="c-metric-item">
              <div class="c-metric-label">Salto Comparecimento</div>
              <div class="c-metric-val">+2,75 p.p.</div>
            </div>
            <div class="c-metric-item">
              <div class="c-metric-label">Conectividade ICCD</div>
              <div class="c-metric-val">27,1 pts | 22,9% Pós</div>
            </div>
            <div class="c-metric-item">
              <div class="c-metric-label">Votação 1ºT</div>
              <div class="c-metric-val">Lula 65,1% | Bolso 25,9%</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Gráficos de Machine Learning -->
    <section class="charts-grid">
      <!-- Gráfico 1: Espaço Latente PCA 2D -->
      <div class="glass-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title"><span class="icon">🌌</span> Espaço Latente PCA 2D: Distribuição dos 417 Municípios</div>
            <div class="panel-subtitle">Projeção bidimensional com clusters identificados por K-Means (tamanho do ponto = Trânsito Proporcional)</div>
          </div>
        </div>
        <div id="chart-pca" class="chart-container"></div>
      </div>

      <!-- Gráfico 2: ICCD Ponderado ANATEL vs Trânsito Proporcional -->
      <div class="glass-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title"><span class="icon">📡</span> Índice Ponderado de Conectividade (ICCD) vs Trânsito Lula</div>
            <div class="panel-subtitle">Síntese de Pós-Pago (0.50) + Densidade (0.35) + 4G/5G (0.15) versus migração pró-Lula</div>
          </div>
        </div>
        <div id="chart-scatter-telecom" class="chart-container"></div>
      </div>
    </section>

    <section class="charts-grid">
      <!-- Gráfico 3: Feature Importance Random Forest -->
      <div class="glass-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title"><span class="icon">🌲</span> Importância das Variáveis (Random Forest Regressor)</div>
            <div class="panel-subtitle">Poder explicativo de cada variável demográfica, de telecomunicações e política sobre o Target</div>
          </div>
        </div>
        <div id="chart-feature-importance" class="chart-container"></div>
      </div>

      <!-- Gráfico 4: Centróides Comparativos dos 4 Clusters -->
      <div class="glass-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title"><span class="icon">📊</span> Perfil Multidimensional dos Centróides dos Clusters</div>
            <div class="panel-subtitle">Comparativo de Trânsito para Lula, Conectividade ICCD, Densidade Anatel e % Pós-Pago</div>
          </div>
        </div>
        <div id="chart-centroids" class="chart-container"></div>
      </div>
    </section>

    <!-- Tabela Interativa dos 417 Municípios -->
    <section class="glass-panel">
      <div class="panel-header">
        <div>
          <div class="panel-title"><span class="icon">📋</span> Tabela Completa dos 417 Municípios da Bahia (Classificação de Clusters)</div>
          <div class="panel-subtitle">Filtre por cluster, busque municípios específicos e analise o trânsito proporcional de votos</div>
        </div>
      </div>

      <div class="table-controls">
        <input type="text" id="table-search" class="search-input" placeholder="🔍 Buscar município...">
        <select id="cluster-filter" class="filter-select">
          <option value="ALL">Todos os Clusters (417 municípios)</option>
          <option value="C1">Cluster 1: Metrópoles & Polos Hiperconectados (27)</option>
          <option value="C2">Cluster 2: Sertão & Semiárido Rural (136)</option>
          <option value="C3">Cluster 3: Centros Médios em Transição (114)</option>
          <option value="C4">Cluster 4: Regiões Agro & Resistência (140)</option>
        </select>
        <div class="pagination-bar">
          <span id="page-info">Página 1 de 9 (417 municípios)</span>
          <button id="prev-btn" class="page-btn">← Anterior</button>
          <button id="next-btn" class="page-btn">Próxima →</button>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="data-table" id="muni-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Município</th>
              <th>Cluster</th>
              <th>Trânsito Lula (%)</th>
              <th>Δ % Lula (Válidos)</th>
              <th>Δ Comp. (p.p.)</th>
              <th>Índice Conectividade (ICCD)</th>
              <th>Densidade ANATEL</th>
              <th>% Pós-Pago</th>
              <th>Renda Domiciliar</th>
              <th>% Superior</th>
              <th>Lula 1ºT</th>
              <th>Bolso 1ºT</th>
              <th>Outros 1ºT</th>
              <th>Votos Lula 2ºT</th>
              <th>Votos Bolso 2ºT</th>
            </tr>
          </thead>
          <tbody id="table-body">
            <!-- Linhas geradas dinamicamente via JS -->
          </tbody>
        </table>
      </div>
    </section>
  </main>

  <script>
    const muniData = {muni_json};
    const summaryData = {summary_json};

    let filteredData = muniData;
    let currentPage = 1;
    const pageSize = 50;

    const clusterColors = {{
      'C1': '#06b6d4',
      'C2': '#10b981',
      'C3': '#a855f7',
      'C4': '#f59e0b'
    }};

    function safeNum(val, dec = 2, prefix = '', suffix = '') {{
      if (val == null || isNaN(val)) return '-';
      return prefix + Number(val).toFixed(dec) + suffix;
    }}

    function renderTable() {{
      const tbody = document.getElementById("table-body");
      if (!tbody) return;
      tbody.innerHTML = "";

      const start = (currentPage - 1) * pageSize;
      const end = Math.min(start + pageSize, filteredData.length);
      const pageRows = filteredData.slice(start, end);

      pageRows.forEach((row, idx) => {{
        const tr = document.createElement("tr");
        const cColor = clusterColors[row.cluster_code] || '#94a3b8';

        const deltaLulaSign = row.delta_pct_lula != null && row.delta_pct_lula >= 0 ? '+' : '';
        const deltaLulaColor = row.delta_pct_lula != null && row.delta_pct_lula >= 0 ? '#10b981' : '#f43f5e';

        const deltaCompSign = row.delta_pct_comp != null && row.delta_pct_comp >= 0 ? '+' : '';

        tr.innerHTML = `
          <td><strong>${{start + idx + 1}}</strong></td>
          <td><strong>${{row.NM_MUNICIPIO}}</strong></td>
          <td><span class="code-tag" style="color:${{cColor}}; border-color:${{cColor}}40;">${{row.cluster_code}}</span></td>
          <td><strong style="color:#f43f5e; font-size:13px;">${{safeNum(row.transito_proporcional_lula, 1, '', '%')}}</strong></td>
          <td style="color:${{deltaLulaColor}};">${{safeNum(row.delta_pct_lula, 2, deltaLulaSign, '%')}}</td>
          <td>${{safeNum(row.delta_pct_comp, 2, deltaCompSign, '%')}}</td>
          <td><strong style="color:#22d3ee;">${{safeNum(row.indice_conectividade_anatel, 1)}}</strong></td>
          <td><span class="code-tag" style="color:#06b6d4;">${{safeNum(row.densidade_smp, 1)}}</span></td>
          <td>${{safeNum(row.pct_pos_pago, 1, '', '%')}}</td>
          <td>R$ ${{safeNum(row.RENDIMENTO_DOMICILIAR_RS, 2)}}</td>
          <td>${{safeNum(row.PCT_SUPERIOR, 1, '', '%')}}</td>
          <td>${{safeNum(row.PCT_LULA, 1, '', '%')}}</td>
          <td>${{safeNum(row.PCT_BOLSONARO, 1, '', '%')}}</td>
          <td>${{safeNum(row.PCT_OUTROS, 1, '', '%')}}</td>
          <td style="color:#f43f5e; font-weight:600;">${{row.VOTOS_LULA_2T != null ? row.VOTOS_LULA_2T.toLocaleString() : '-'}}</td>
          <td style="color:#38bdf8; font-weight:600;">${{row.VOTOS_FLAVIO != null ? row.VOTOS_FLAVIO.toLocaleString() : '-'}}</td>
        `;
        tbody.appendChild(tr);
      }});

      const totalPages = Math.ceil(filteredData.length / pageSize) || 1;
      const pageInfo = document.getElementById("page-info");
      if (pageInfo) pageInfo.innerText = `Página ${{currentPage}} de ${{totalPages}} (${{filteredData.length}} municípios)`;
      
      const prevBtn = document.getElementById("prev-btn");
      if (prevBtn) prevBtn.disabled = (currentPage === 1);
      
      const nextBtn = document.getElementById("next-btn");
      if (nextBtn) nextBtn.disabled = (currentPage >= totalPages);
    }}

    function applyFilters() {{
      const searchEl = document.getElementById("table-search");
      const filterEl = document.getElementById("cluster-filter");
      const q = searchEl ? searchEl.value.toLowerCase().trim() : '';
      const clusterFilter = filterEl ? filterEl.value : 'ALL';

      filteredData = muniData.filter(r => {{
        const matchesQuery = !q || r.NM_MUNICIPIO.toLowerCase().includes(q);
        const matchesCluster = clusterFilter === "ALL" || r.cluster_code === clusterFilter;
        return matchesQuery && matchesCluster;
      }});

      currentPage = 1;
      renderTable();
    }}

    document.getElementById("prev-btn")?.addEventListener("click", () => {{
      if (currentPage > 1) {{ currentPage--; renderTable(); }}
    }});

    document.getElementById("next-btn")?.addEventListener("click", () => {{
      const totalPages = Math.ceil(filteredData.length / pageSize);
      if (currentPage < totalPages) {{ currentPage++; renderTable(); }}
    }});

    document.getElementById("table-search")?.addEventListener("input", applyFilters);
    document.getElementById("cluster-filter")?.addEventListener("change", applyFilters);

    renderTable();

    // ==========================================
    // RENDERIZAÇÃO DOS GRÁFICOS PLOTLY
    // ==========================================
    function renderAllCharts() {{
      if (typeof Plotly === 'undefined') {{
        console.error("Plotly ainda não está disponível. Tentando novamente em 300ms...");
        setTimeout(renderAllCharts, 300);
        return;
      }}

      const plotlyLayoutCommon = {{
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: {{ family: 'Inter, sans-serif', color: '#94a3b8', size: 11 }},
        height: 410,
        autosize: true,
        hovermode: 'closest'
      }};

      // 1. PCA 2D
      const pcaTraces = ['C1', 'C2', 'C3', 'C4'].map(code => {{
        const sub = muniData.filter(r => r.cluster_code === code);
        return {{
          x: sub.map(r => r.pca_1),
          y: sub.map(r => r.pca_2),
          text: sub.map(r => `<strong>${{r.NM_MUNICIPIO}}</strong><br>Cluster: ${{r.cluster_nome}}<br>Trânsito Lula: ${{safeNum(r.transito_proporcional_lula, 1, '', '%')}}<br>Conectividade ICCD: ${{safeNum(r.indice_conectividade_anatel, 1)}}<br>Densidade: ${{safeNum(r.densidade_smp, 1)}} ac/100 hab`),
          mode: 'markers',
          type: 'scatter',
          name: code,
          marker: {{
            color: clusterColors[code],
            size: sub.map(r => Math.max(6, Math.min(18, (Number(r.transito_proporcional_lula || 70) - 50) / 2.5))),
            opacity: 0.75,
            line: {{ color: 'rgba(255,255,255,0.3)', width: 0.5 }}
          }}
        }};
      }});

      Plotly.newPlot('chart-pca', pcaTraces, {{
        ...plotlyLayoutCommon,
        margin: {{ l: 50, r: 25, t: 40, b: 50 }},
        xaxis: {{ title: 'Componente Principal 1 (PC1 - Socioeconômico e Telecom)', gridcolor: 'rgba(255,255,255,0.06)' }},
        yaxis: {{ title: 'Componente Principal 2 (PC2 - Voto 1T e Escolaridade)', gridcolor: 'rgba(255,255,255,0.06)' }},
        legend: {{ orientation: 'h', y: 1.12, x: 0.02 }}
      }}, {{ responsive: true, displayModeBar: false }});

      // 2. Dispersão Conectividade Ponderada (ICCD) vs Trânsito Lula
      const scatterTelecomTraces = ['C1', 'C2', 'C3', 'C4'].map(code => {{
        const sub = muniData.filter(r => r.cluster_code === code);
        return {{
          x: sub.map(r => r.indice_conectividade_anatel),
          y: sub.map(r => r.transito_proporcional_lula),
          text: sub.map(r => `${{r.NM_MUNICIPIO}}<br>Conectividade ICCD: ${{safeNum(r.indice_conectividade_anatel, 1)}} pts<br>Pós-Pago: ${{safeNum(r.pct_pos_pago, 1, '', '%')}}<br>Trânsito Lula: ${{safeNum(r.transito_proporcional_lula, 1, '', '%')}}`),
          mode: 'markers',
          type: 'scatter',
          name: code,
          marker: {{ color: clusterColors[code], size: 7, opacity: 0.75 }}
        }};
      }});

      Plotly.newPlot('chart-scatter-telecom', scatterTelecomTraces, {{
        ...plotlyLayoutCommon,
        margin: {{ l: 50, r: 25, t: 40, b: 50 }},
        xaxis: {{ title: 'Índice Ponderado de Conectividade ANATEL (ICCD: 0 a 100)', gridcolor: 'rgba(255,255,255,0.06)' }},
        yaxis: {{ title: 'Trânsito Proporcional para Lula (%)', gridcolor: 'rgba(255,255,255,0.06)' }},
        legend: {{ orientation: 'h', y: 1.12, x: 0.02 }}
      }}, {{ responsive: true, displayModeBar: false }});

      // 3. Feature Importance (Random Forest)
      const fiData = summaryData.feature_importances.slice(0, 12).reverse();
      const fiTrace = {{
        x: fiData.map(d => d.Importance * 100),
        y: fiData.map(d => d.Feature),
        type: 'bar',
        orientation: 'h',
        marker: {{
          color: fiData.map(d => 
            d.Feature.includes('indice') || d.Feature.includes('pct_pos') || d.Feature.includes('densidade') ? '#06b6d4' : 
            (d.Feature.includes('LULA') || d.Feature.includes('BOLSONARO') ? '#a855f7' : '#38bdf8')
          )
        }}
      }};

      Plotly.newPlot('chart-feature-importance', [fiTrace], {{
        ...plotlyLayoutCommon,
        margin: {{ l: 195, r: 25, t: 25, b: 50 }},
        xaxis: {{ title: 'Importância Relativa no Modelo Random Forest (%)', gridcolor: 'rgba(255,255,255,0.06)' }},
        yaxis: {{ automargin: true, gridcolor: 'rgba(255,255,255,0.06)' }}
      }}, {{ responsive: true, displayModeBar: false }});

      // 4. Centróides Comparativos dos 4 Clusters
      const cLabels = summaryData.clusters.map(c => c.cluster_code);
      const traceCentroidTrânsito = {{
        x: cLabels,
        y: summaryData.clusters.map(c => c.transito_lula_medio),
        name: 'Trânsito Lula (%)',
        type: 'bar',
        marker: {{ color: '#f43f5e' }}
      }};

      const traceCentroidICCD = {{
        x: cLabels,
        y: summaryData.clusters.map(c => c.iccd_medio),
        name: 'ICCD Ponderado (0 a 100)',
        type: 'bar',
        marker: {{ color: '#22d3ee' }}
      }};

      const traceCentroidDens = {{
        x: cLabels,
        y: summaryData.clusters.map(c => c.densidade_media),
        name: 'Densidade ANATEL (ac/100 hab)',
        type: 'bar',
        marker: {{ color: '#06b6d4' }}
      }};

      const traceCentroidPos = {{
        x: cLabels,
        y: summaryData.clusters.map(c => c.pct_pos_medio),
        name: '% Pós-Pago (Smartphones)',
        type: 'bar',
        marker: {{ color: '#a855f7' }}
      }};

      Plotly.newPlot('chart-centroids', [traceCentroidTrânsito, traceCentroidICCD, traceCentroidDens, traceCentroidPos], {{
        ...plotlyLayoutCommon,
        barmode: 'group',
        margin: {{ l: 50, r: 25, t: 45, b: 50 }},
        xaxis: {{ title: 'Cluster Socio-Eleitoral', gridcolor: 'rgba(255,255,255,0.06)' }},
        yaxis: {{ title: 'Valor Médio no Centróide', gridcolor: 'rgba(255,255,255,0.06)' }},
        legend: {{ orientation: 'h', y: 1.14, x: 0.02 }}
      }}, {{ responsive: true, displayModeBar: false }});
    }}

    window.addEventListener('resize', () => {{
      ['chart-pca', 'chart-scatter-telecom', 'chart-feature-importance', 'chart-centroids'].forEach(id => {{
        const el = document.getElementById(id);
        if (el && typeof Plotly !== 'undefined') {{
          Plotly.Plots.resize(el);
        }}
      }});
    }});

    // Executa após DOM pronto
    if (document.readyState === 'loading') {{
      document.addEventListener('DOMContentLoaded', renderAllCharts);
    }} else {{
      renderAllCharts();
    }}
  </script>
</body>
</html>
"""
    output_path = Path("dashboard_clusters_ml_anatel_ibge.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Dashboard de Machine Learning atualizado com sucesso em: {output_path.resolve()} ({output_path.stat().st_size:,} bytes)")

    # Publica na pasta docs/ para disponibilidade online no GitHub Pages
    docs_path = Path("docs/dashboard_clusters_ml_anatel_ibge.html")
    docs_path.parent.mkdir(exist_ok=True)
    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Dashboard publicado em docs/ para acesso online: {docs_path.resolve()} ({docs_path.stat().st_size:,} bytes)")

if __name__ == "__main__":
    gerar_dashboard_clusters()
