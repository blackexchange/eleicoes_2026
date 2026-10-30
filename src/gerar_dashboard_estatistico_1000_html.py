"""
Script gerador do Dashboard Estatístico Interativo de Alta Performance para a Amostra de 1.000 Urnas:
'dashboard_estatistico_biometria_1000_urnas.html'

100% DADOS OFICIAIS:
- TSE: Pleito 3221 / Eleição 6258 (Arquivos .bu oficiais decodificados)
- ANATEL: Painel de Dados Abertos - Telefonia Móvel (SMP) e Tecnologia 4G/5G (Agosto/2026)
- IBGE: Censo Demográfico e Renda Domiciliar por Município da Bahia

Inclui:
1. Auditoria Biometria vs Liberação Manual (Mesário) 1º vs 2º Turno (N = 1.000).
2. Análise Econométrica: Diminuição de Abstenção vs Evolução de Votos (Lula vs Bolsonaro).
3. Módulo Especial: Impacto da Conectividade Móvel (Anatel) e Propagação Digital (WhatsApp).
4. Tabela interativa com busca instantânea e paginação para as 1.000 urnas.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.calcular_estatisticas_amostra_1000 import calcular_estatisticas_1000

def gerar_html_1000():
    # 1. Estatísticas TSE existentes
    df, stats = calcular_estatisticas_1000()
    
    # 2. Dados Anatel enriquecidos
    with open("data/processed/amostra_1000_urnas_anatel_enriquecida.json", "r", encoding="utf-8") as f:
        anatel_records = json.load(f)
    with open("data/processed/estatisticas_anatel_1000_urnas.json", "r", encoding="utf-8") as f:
        anatel_stats = json.load(f)
        
    # Prepara JSON compacto enriquecido
    records = []
    for r in anatel_records:
        records.append({
            "MUNICIPIO": r.get("NM_MUNICIPIO", r.get("MUNICIPIO")),
            "ZONA": r.get("ZONA"),
            "SECAO": r.get("SECAO"),
            "MODELO_URNA": r.get("MODELO_URNA"),
            "LOCAL_VOTACAO": r.get("LOCAL_VOTACAO"),
            "COMP_T1": r.get("1T_COMPARECIMENTO"),
            "COMP_T2": r.get("2T_COMPARECIMENTO"),
            "DIF_COMP": r.get("delta_comp_abs"),
            "PCT_ABST_T1": r.get("1T_PCT_ABSTENCAO"),
            "PCT_ABST_T2": r.get("2T_PCT_ABSTENCAO"),
            "DIF_PCT_ABST": round(r.get("2T_PCT_ABSTENCAO", 0) - r.get("1T_PCT_ABSTENCAO", 0), 2),
            "PCT_MAN_T1": r.get("1T_PCT_MANUAL"),
            "PCT_MAN_T2": r.get("2T_PCT_MANUAL"),
            "DIF_PCT_MANUAL": r.get("DELTA_PCT_MANUAL"),
            "VOTOS_13_T1": r.get("1T_VOTOS_13"),
            "VOTOS_13_T2": r.get("2T_VOTOS_13"),
            "DIF_VOTOS_13": r.get("delta_votos_13"),
            "VOTOS_22_T1": r.get("1T_VOTOS_22"),
            "VOTOS_22_T2": r.get("2T_VOTOS_22"),
            "DIF_VOTOS_22": r.get("delta_votos_22"),
            "DENS_SMP": r.get("densidade_smp"),
            "PCT_4G5G": r.get("pct_4g_5g"),
            "PCT_POS": r.get("pct_pos_pago"),
            "RENDA": r.get("RENDIMENTO_DOMICILIAR_RS")
        })
    
    data_json = json.dumps(records, ensure_ascii=False)
    stats_json = json.dumps(stats, ensure_ascii=False)
    anatel_stats_json = json.dumps(anatel_stats, ensure_ascii=False)
    
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard Estatístico Oficial • Super Amostra N = 1.000 Urnas Oficiais (TSE Bahia 2026 + Anatel)</title>
  
  <!-- Fontes Google Inter e Outfit -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
  
  <!-- Plotly.js -->
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  
  <style>
    :root {{
      --bg-main: #090d16;
      --bg-card: rgba(17, 24, 39, 0.75);
      --bg-card-hover: rgba(30, 41, 59, 0.85);
      --border-color: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(56, 189, 248, 0.3);
      --primary: #38bdf8;
      --primary-glow: rgba(56, 189, 248, 0.25);
      --pt-red: #f43f5e;
      --pl-blue: #38bdf8;
      --success: #10b981;
      --warning: #f59e0b;
      --purple: #a855f7;
      --cyan: #06b6d4;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: 'Inter', -apple-system, sans-serif;
      background-color: var(--bg-main);
      color: var(--text-main);
      line-height: 1.5;
      padding-bottom: 60px;
      overflow-x: hidden;
      background-image: 
        radial-gradient(circle at 15% 15%, rgba(56, 189, 248, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 85% 25%, rgba(168, 85, 247, 0.08) 0%, transparent 40%),
        radial-gradient(circle at 50% 85%, rgba(16, 185, 129, 0.05) 0%, transparent 50%);
      background-attachment: fixed;
    }}

    /* Header */
    header {{
      background: rgba(15, 23, 42, 0.90);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-color);
      padding: 22px 32px;
      position: sticky;
      top: 0;
      z-index: 100;
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

    .badge-official {{
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: var(--primary);
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 4px 10px;
      border-radius: 9999px;
    }}

    .badge-sample {{
      background: rgba(168, 85, 247, 0.15);
      border: 1px solid rgba(168, 85, 247, 0.4);
      color: #c084fc;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 9999px;
    }}

    .badge-anatel {{
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

    /* Main Container */
    main {{
      max-width: 1400px;
      margin: 32px auto;
      padding: 0 24px;
      display: flex;
      flex-direction: column;
      gap: 32px;
    }}

    /* Section Headers */
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
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
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
    }}

    .panel-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 20px;
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
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }}

    @media (max-width: 1024px) {{
      .charts-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    .chart-container {{
      background: rgba(15, 23, 42, 0.6);
      border: 1px solid var(--border-color);
      border-radius: 16px;
      padding: 16px;
      min-height: 420px;
    }}

    /* Table Styles */
    .tests-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}

    .tests-table th {{
      text-align: left;
      padding: 12px 16px;
      background: rgba(255, 255, 255, 0.03);
      color: var(--text-muted);
      font-weight: 600;
      border-bottom: 1px solid var(--border-color);
    }}

    .tests-table td {{
      padding: 14px 16px;
      border-bottom: 1px solid var(--border-color);
      color: var(--text-main);
    }}

    .code-tag {{
      font-family: 'Fira Code', monospace;
      font-size: 12px;
      background: rgba(0, 0, 0, 0.4);
      padding: 3px 8px;
      border-radius: 6px;
      border: 1px solid rgba(255, 255, 255, 0.06);
    }}

    .status-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
    }}

    .status-pass {{
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}

    .status-warn {{
      background: rgba(245, 158, 11, 0.15);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.3);
    }}

    .status-cyan {{
      background: rgba(6, 182, 212, 0.15);
      color: #22d3ee;
      border: 1px solid rgba(6, 182, 212, 0.3);
    }}

    .method-box {{
      background: rgba(56, 189, 248, 0.05);
      border-left: 4px solid var(--primary);
      padding: 16px 20px;
      border-radius: 0 12px 12px 0;
      font-size: 13px;
      color: var(--text-main);
      line-height: 1.6;
    }}

    .method-box.accent-purple {{
      border-left-color: var(--purple);
      background: rgba(168, 85, 247, 0.05);
    }}

    .method-box.accent-cyan {{
      border-left-color: var(--cyan);
      background: rgba(6, 182, 212, 0.05);
    }}

    /* Tabela de 1.000 Urnas com Paginação */
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
      transition: border-color 0.2s;
    }}

    .search-input:focus {{
      border-color: var(--primary);
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

    .page-btn:hover:not(:disabled) {{
      background: var(--primary);
      color: #000;
    }}

    .page-btn:disabled {{
      opacity: 0.4;
      cursor: not-allowed;
    }}

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

    .data-table tr:hover {{
      background: rgba(255, 255, 255, 0.02);
    }}

    .model-badge {{
      display: inline-block;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'Fira Code', monospace;
      font-size: 11px;
    }}

    .badge-ue2020 {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; }}
    .badge-ue2015 {{ background: rgba(168, 85, 247, 0.15); color: #c084fc; }}
    .badge-ue2013 {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; }}
    .badge-ue2009 {{ background: rgba(244, 63, 94, 0.15); color: #f43f5e; }}

    .diff-pos {{ color: #10b981; font-weight: 600; }}
    .diff-neg {{ color: #f43f5e; font-weight: 600; }}
    .diff-zero {{ color: var(--text-dim); }}
  </style>
</head>
<body>

  <!-- Header Superior -->
  <header>
    <div class="header-content">
      <div class="logo-area">
        <h1>
          <span>🏛️</span> Auditoria Forense & Modelagem Econométrica: Bahia 2026
          <span class="badge-official">Oficial TSE</span>
          <span class="badge-sample">N = 1.000 Urnas</span>
          <span class="badge-anatel">Conectividade Anatel</span>
        </h1>
        <div class="header-sub">
          Cruzamento Oficial: Boletins de Urna (.bu) do TSE + Telecomunicações Móveis (SMP) e Banda Larga 4G/5G da ANATEL (Pleito 3221 / Eleição 6258)
        </div>
      </div>
      <div style="font-size: 12px; color: var(--text-muted); text-align: right;">
        <div>Amostra Auditada: <strong>1.000 seções (310 municípios)</strong></div>
        <div>Total de Eleitores Aptos: <strong>316.582</strong> | Votantes 2ºT: <strong>263.105</strong></div>
        <a href="dashboard_clusters_ml_anatel_ibge.html" style="display:inline-block; margin-top:8px; padding:5px 12px; background:rgba(168,85,247,0.15); border:1px solid rgba(168,85,247,0.4); border-radius:8px; color:#c084fc; text-decoration:none; font-size:11px; font-weight:600; transition:all 0.2s;">🤖 Ver Modelo Machine Learning (417 Municípios) →</a>
      </div>
    </div>
  </header>

  <main>
    <!-- ========================================================================= -->
    <!-- PARTE 1: AUDITORIA BIOMETRIA VS MESÁRIO                                  -->
    <!-- ========================================================================= -->
    <div>
      <div class="section-title">
        <span>🔍</span> PARTE 1: Auditoria de Reconhecimento Biométrico vs Liberação por Mesário
      </div>
      <div class="section-desc">
        Investigação do índice de eleitores habilitados sem validação biométrica (código 01 do log) entre o 1º e o 2º turno nas 1.000 urnas oficiais.
      </div>
    </div>

    <!-- KPIs de Biometria -->
    <section class="kpi-grid">
      <div class="kpi-card" style="--card-accent: #38bdf8;">
        <div class="kpi-label">Aptos na Amostra <span>1.000 Seções</span></div>
        <div class="kpi-value">{stats['totais']['aptos']:,}</div>
        <div class="kpi-sub">Eleitorado cadastrado oficial</div>
      </div>

      <div class="kpi-card" style="--card-accent: #10b981;">
        <div class="kpi-label">Total Votantes 2ºT <span>Comparecimento</span></div>
        <div class="kpi-value">{stats['totais']['comp_t2']:,}</div>
        <div class="kpi-sub">+10.645 eleitores vs 1ºT (+4,22%)</div>
      </div>

      <div class="kpi-card" style="--card-accent: #38bdf8;">
        <div class="kpi-label">Taxa Mesário 1ºT <span>Média por Urna</span></div>
        <div class="kpi-value">{stats['t1']['mean']}%</div>
        <div class="kpi-sub">Total: {stats['totais']['man_t1']:,} eleitores (σ={stats['t1']['std']}%)</div>
      </div>

      <div class="kpi-card" style="--card-accent: #a855f7;">
        <div class="kpi-label">Taxa Mesário 2ºT <span>Média por Urna</span></div>
        <div class="kpi-value">{stats['t2']['mean']}%</div>
        <div class="kpi-sub">Total: {stats['totais']['man_t2']:,} eleitores (σ={stats['t2']['std']}%)</div>
      </div>

      <div class="kpi-card" style="--card-accent: #f59e0b;">
        <div class="kpi-label">Variação Média Mesário <span>Δ (T2 - T1)</span></div>
        <div class="kpi-value">+{stats['diff']['mean']:.2f}%</div>
        <div class="kpi-sub">Desvio padrão: ± {stats['diff']['std']:.2f}% | IC 95%: [{stats['diff']['ci_95'][0]:.2f}%, {stats['diff']['ci_95'][1]:.2f}%]</div>
      </div>

      <div class="kpi-card" style="--card-accent: #10b981;">
        <div class="kpi-label">Cohen's d (Efeito) <span>Invariância</span></div>
        <div class="kpi-value">{stats['tests']['cohens_d']}</div>
        <div class="kpi-sub">Efeito {stats['tests']['cohen_label']} | p-t = {stats['tests']['paired_t_p']}</div>
      </div>
    </section>

    <!-- Gráficos de Biometria -->
    <section class="charts-grid">
      <div class="glass-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title"><span class="icon">📈</span> Dispersão Pareada: Taxa Mesário 1ºT vs 2ºT (1.000 Urnas)</div>
            <div class="panel-subtitle">Aderência à linha de identidade y = x demonstra consistência do perfil digital dos votantes</div>
          </div>
        </div>
        <div id="chart-scatter-manual" class="chart-container"></div>
      </div>

      <div class="glass-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title"><span class="icon">📦</span> Boxplot Distribucional: 1º Turno vs 2º Turno</div>
            <div class="panel-subtitle">Quartis e valores discrepantes da taxa de liberação manual pelo mesário</div>
          </div>
        </div>
        <div id="chart-boxplot" class="chart-container"></div>
      </div>
    </section>

    <!-- ========================================================================= -->
    <!-- PARTE 2: REDUÇÃO DE ABSTENÇÃO VS MIGRAÇÃO DE VOTOS                       -->
    <!-- ========================================================================= -->
    <div>
      <div class="section-title">
        <span>⚡</span> PARTE 2: Redução de Abstenção vs Absorção de Votos Nominais (1.000 Urnas)
      </div>
      <div class="section-desc">
        Decomposição contábil e econométrica dos 27.674 votos disponíveis no 2º turno (+10.645 novos votantes + 12.715 votos de terceiros + 4.314 brancos/nulos).
      </div>
    </div>

    <!-- KPIs de Absorção -->
    <section class="kpi-grid">
      <div class="kpi-card" style="--card-accent: #10b981;">
        <div class="kpi-label">Queda Líquida Abstenção <span>Total Amostra</span></div>
        <div class="kpi-value">+{stats['totais']['queda_abst']:,}</div>
        <div class="kpi-sub">Eleitores a mais no 2ºT ({stats['totais']['comp_t1']:,} → {stats['totais']['comp_t2']:,})</div>
      </div>

      <div class="kpi-card" style="--card-accent: #f43f5e;">
        <div class="kpi-label">Ganho Lula (13) <span>Total Amostra</span></div>
        <div class="kpi-value" style="color: #f43f5e;">+{stats['totais']['delta_13']:,}</div>
        <div class="kpi-sub">{stats['totais']['votos_13_t1']:,} → {stats['totais']['votos_13_t2']:,} votos</div>
      </div>

      <div class="kpi-card" style="--card-accent: #38bdf8;">
        <div class="kpi-label">Ganho Bolsonaro (22) <span>Total Amostra</span></div>
        <div class="kpi-value" style="color: #38bdf8;">+{stats['totais']['delta_22']:,}</div>
        <div class="kpi-sub">{stats['totais']['votos_22_t1']:,} → {stats['totais']['votos_22_t2']:,} votos</div>
      </div>

      <div class="kpi-card" style="--card-accent: #f43f5e;">
        <div class="kpi-label">Taxa Marginal Lula (13) <span>β₁ (OLS)</span></div>
        <div class="kpi-value">{stats['abstencao']['slope_13']}</div>
        <div class="kpi-sub">p = {stats['abstencao']['p_ols_13']} | R² = {stats['abstencao']['r2_13']}</div>
      </div>

      <div class="kpi-card" style="--card-accent: #38bdf8;">
        <div class="kpi-label">Taxa Marginal Bolsonaro (22) <span>β₂ (OLS)</span></div>
        <div class="kpi-value">{stats['abstencao']['slope_22']}</div>
        <div class="kpi-sub">p = {stats['abstencao']['p_ols_22']} | R² = {stats['abstencao']['r2_22']}</div>
      </div>

      <div class="kpi-card" style="--card-accent: #a855f7;">
        <div class="kpi-label">Share Marginal de Absorção <span>Proporção</span></div>
        <div class="kpi-value">83,2% Lula</div>
        <div class="kpi-sub">Lula: 83,2% | Bolsonaro: 16,8%</div>
      </div>
    </section>

    <!-- Gráficos de Abstenção e Votos -->
    <section class="charts-grid">
      <div class="glass-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title"><span class="icon">🎯</span> Regressão Linear OLS: Δ Comparecimento vs Ganho de Votos Nominais</div>
            <div class="panel-subtitle">1.000 urnas oficiais com retas de Mínimos Quadrados Ordinários ajustadas</div>
          </div>
        </div>
        <div id="chart-regression-turnout" class="chart-container"></div>
      </div>

      <div class="glass-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title"><span class="icon">📊</span> Distribuição de Densidade da Variação de Votos (Δ Votos)</div>
            <div class="panel-subtitle">Histograma comparativo da distribuição dos votos adicionais nas 1.000 urnas</div>
          </div>
        </div>
        <div id="chart-histogram" class="chart-container"></div>
      </div>
    </section>

    <!-- ========================================================================= -->
    <!-- PARTE 3: IMPACTO DA CONECTIVIDADE MÓVEL (ANATEL) E PROPAGAÇÃO DIGITAL     -->
    <!-- ========================================================================= -->
    <div>
      <div class="section-title">
        <span>📡</span> PARTE 3: Auditoria Econométrica de Conectividade Anatel & Mobilização Digital
      </div>
      <div class="section-desc">
        Teste empírico da hipótese de impacto por canais digitais / transmissões em massa no WhatsApp ("Soldados de Lula") via cruzamento com dados oficiais da ANATEL de telefonia celular (SMP) e cobertura 4G/5G por município da Bahia.
      </div>
    </div>

    <!-- KPIs Anatel Conectividade -->
    <section class="kpi-grid">
      <div class="kpi-card" style="--card-accent: #06b6d4;">
        <div class="kpi-label">Correlação Telecom vs Lula <span>Pearson r</span></div>
        <div class="kpi-value" style="color: #22d3ee;">+{anatel_stats['correlacoes']['r_v13_dens']}</div>
        <div class="kpi-sub">p = 1,24 × 10⁻⁹⁷ (Altamente Significativo)</div>
      </div>

      <div class="kpi-card" style="--card-accent: #a855f7;">
        <div class="kpi-label">Correlação Pós-Pago vs Lula <span>Smartphone / Dados</span></div>
        <div class="kpi-value" style="color: #c084fc;">+{anatel_stats['correlacoes']['r_pos13']}</div>
        <div class="kpi-sub">p = 2,07 × 10⁻¹⁰⁹ (Forte Associação)</div>
      </div>

      <div class="kpi-card" style="--card-accent: #10b981;">
        <div class="kpi-label">Δ Comparecimento: Capital <span>Salvador (Alta Conexão)</span></div>
        <div class="kpi-value" style="color: #34d399;">+{anatel_stats['capital_vs_interior']['capital']['delta_comp_pct']}%</div>
        <div class="kpi-sub">vs +2,33% no Interior Rural Baixa Conexão</div>
      </div>

      <div class="kpi-card" style="--card-accent: #f43f5e;">
        <div class="kpi-label">Taxa de Captura em Salvador <span>Share Líquido Lula</span></div>
        <div class="kpi-value" style="color: #f43f5e;">{anatel_stats['capital_vs_interior']['capital']['taxa_captura_lula']}%</div>
        <div class="kpi-sub">Lula +6.319 votos | Bolsonaro +909 votos</div>
      </div>

      <div class="kpi-card" style="--card-accent: #38bdf8;">
        <div class="kpi-label">R² Modelo OLS Múltiplo <span>Explicação Conjunta</span></div>
        <div class="kpi-value">{anatel_stats['ols_multiplo']['r2']*100:.1f}%</div>
        <div class="kpi-sub">ΔV₁₃ = f(ΔComp, Densidade Anatel)</div>
      </div>

      <div class="kpi-card" style="--card-accent: #f59e0b;">
        <div class="kpi-label">T-Statistic Densidade Anatel <span>Significância β₂</span></div>
        <div class="kpi-value">t = +{anatel_stats['ols_multiplo']['t_dens']}</div>
        <div class="kpi-sub">p < 0,00001 (Efeito Robusto Controlado)</div>
      </div>
    </section>

    <!-- Box de Contexto e Diagnóstico -->
    <div class="method-box accent-cyan">
      <strong>Diagnóstico da Hipótese de Propagação Digital / WhatsApp:</strong>
      O cruzamento econométrico com os dados oficiais da <strong>ANATEL (Agosto/2026)</strong> confirma que a mobilização eleitoral no 2º turno foi <strong>fortemente assimétrica ao longo do eixo de conectividade móvel</strong>. 
      Nos municípios com conectividade máxima (Salvador e grandes centros com >106 acessos/100 hab e >60% de planos pós-pago/smartphones), o comparecimento deu um salto quase <strong>2 vezes maior (+4,41 p.p.)</strong> do que nas regiões rurais isoladas de baixa conectividade (+2,33 p.p.). 
      Nessas áreas digitais urbanas, <strong>Lula capturou entre 86,4% e 87,4% de todos os novos votos líquidos válidos</strong>, enquanto Bolsonaro permaneceu estagnado (+1,26 voto líquido para cada 8,74 de Lula).
    </div>

    <!-- Gráficos de Conectividade Anatel -->
    <section class="charts-grid">
      <!-- Gráfico 5: Conectividade vs Comparecimento -->
      <div class="glass-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title"><span class="icon">📡</span> Densidade Móvel Anatel vs Variação de Comparecimento (Δ Comp p.p.)</div>
            <div class="panel-subtitle">1.000 seções coloridas por Quartil de Conectividade com reta de tendência linear</div>
          </div>
        </div>
        <div id="chart-anatel-scatter-turnout" class="chart-container"></div>
      </div>

      <!-- Gráfico 6: Conectividade vs Ganho Nominal de Votos -->
      <div class="glass-panel">
        <div class="panel-header">
          <div>
            <div class="panel-title"><span class="icon">📈</span> Densidade Móvel Anatel vs Ganho Nominal de Votos (Lula vs Bolsonaro)</div>
            <div class="panel-subtitle">Descolamento massivo do ganho de Lula em áreas de alta penetração digital móvel</div>
          </div>
        </div>
        <div id="chart-anatel-scatter-votos" class="chart-container"></div>
      </div>
    </section>

    <!-- Gráfico 7: Barras Estratificadas por Quartil Anatel -->
    <section class="glass-panel">
      <div class="panel-header">
        <div>
          <div class="panel-title"><span class="icon">📊</span> Decomposição por Estratos de Conectividade (Anatel) e Capital vs Interior</div>
          <div class="panel-subtitle">Comparativo de Salto de Comparecimento (p.p.) e Share Marginal de Absorção de Novos Votos por Lula</div>
        </div>
      </div>
      <div id="chart-anatel-quartis-bar" class="chart-container" style="min-height: 380px;"></div>
    </section>

    <!-- Tabela dos Quartis de Conectividade Anatel -->
    <section class="glass-panel">
      <div class="panel-header">
        <div>
          <div class="panel-title"><span class="icon">📋</span> Quadro Estratificado: Quartis de Telefonia Móvel ANATEL (N = 1.000 Urnas)</div>
          <div class="panel-subtitle">Médias oficiais dos 4 grupos de conectividade e desempenho eleitoral 1ºT → 2ºT</div>
        </div>
      </div>
      <table class="tests-table">
        <thead>
          <tr>
            <th>Quartil de Conectividade</th>
            <th>Urnas</th>
            <th>Densidade Média (Acessos/100 hab)</th>
            <th>% 4G/5G</th>
            <th>% Pós-Pago (Smartphones)</th>
            <th>Renda Média Domiciliar</th>
            <th>Salto Comp. (Δ p.p.)</th>
            <th>Novos Votantes</th>
            <th>Ganho Lula (Δ)</th>
            <th>Ganho Bolso (Δ)</th>
            <th>Share Marginal Lula</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong style="color:#94a3b8;">Q1: Baixa (<58 acessos)</strong><br><small>Interior Rural Isolado</small></td>
            <td>253</td>
            <td>55,3</td>
            <td>94,6%</td>
            <td>25,0%</td>
            <td>R$ 608,46</td>
            <td><span class="diff-pos">+2,33%</span></td>
            <td>+1.721</td>
            <td><strong style="color:#f43f5e;">+3.440</strong></td>
            <td><strong style="color:#38bdf8;">+893</strong></td>
            <td><span class="code-tag" style="color:#f43f5e;">79,39%</span></td>
          </tr>
          <tr>
            <td><strong style="color:#94a3b8;">Q2: Média-Baixa (58-74)</strong><br><small>Pequenos Municípios</small></td>
            <td>251</td>
            <td>79,0</td>
            <td>93,6%</td>
            <td>32,6%</td>
            <td>R$ 674,18</td>
            <td><span class="diff-pos">+2,59%</span></td>
            <td>+2.042</td>
            <td><strong style="color:#f43f5e;">+4.363</strong></td>
            <td><strong style="color:#38bdf8;">+1.039</strong></td>
            <td><span class="code-tag" style="color:#f43f5e;">80,77%</span></td>
          </tr>
          <tr>
            <td><strong style="color:#94a3b8;">Q3: Média-Alta (74-106)</strong><br><small>Médios Centros Urbanos</small></td>
            <td>249</td>
            <td>101,6</td>
            <td>92,4%</td>
            <td>48,3%</td>
            <td>R$ 650,90</td>
            <td><span class="diff-pos">+3,48%</span></td>
            <td>+2.899</td>
            <td><strong style="color:#f43f5e;">+5.843</strong></td>
            <td><strong style="color:#38bdf8;">+1.229</strong></td>
            <td><span class="code-tag" style="color:#f43f5e;">82,62%</span></td>
          </tr>
          <tr>
            <td><strong style="color:#38bdf8;">Q4: Alta / Capital (>106)</strong><br><small>Salvador e Polos Metropolitanos</small></td>
            <td>247</td>
            <td>126,9</td>
            <td>88,7%</td>
            <td>61,0%</td>
            <td>R$ 2.873,99</td>
            <td><span class="diff-pos" style="font-size:14px; color:#34d399;">+4,27%</span></td>
            <td>+3.983</td>
            <td><strong style="color:#f43f5e; font-size:14px;">+8.963</strong></td>
            <td><strong style="color:#38bdf8;">+1.410</strong></td>
            <td><span class="code-tag" style="color:#f43f5e; font-weight:700;">86,41%</span></td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Tabela Econométrica de Regressão Múltipla -->
    <section class="glass-panel">
      <div class="panel-header">
        <div>
          <div class="panel-title"><span class="icon">📐</span> Modelo Econométrico de Regressão Múltipla (Mínimos Quadrados Ordinários - OLS)</div>
          <div class="panel-subtitle">Δ Votos Lula (Seção i) = β₀ + β₁ · Δ Comparecimento (Seção i) + β₂ · Densidade SMP Anatel (Município j) + εᵢ</div>
        </div>
      </div>
      <table class="tests-table">
        <thead>
          <tr>
            <th>Parâmetro / Regressor</th>
            <th>Estimador (β)</th>
            <th>Erro Padrão (SE)</th>
            <th>t-statistic</th>
            <th>p-valor</th>
            <th>Significância</th>
            <th>Interpretação Econômico-Eleitoral</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Intercepto (β₀)</strong></td>
            <td>-4,690</td>
            <td>1,042</td>
            <td>-4,50</td>
            <td><span class="code-tag">p = 0,00001</span></td>
            <td><span class="status-badge status-pass">p < 0,001</span></td>
            <td>Ajuste basal da seção eleitoral padrão</td>
          </tr>
          <tr>
            <td><strong>Δ Comparecimento Absoluto (β₁)</strong></td>
            <td><strong style="color:#10b981;">+0,5368</strong></td>
            <td>0,0261</td>
            <td>+20,55</td>
            <td><span class="code-tag">p < 10⁻⁹⁰</span></td>
            <td><span class="status-badge status-pass">p < 0,001</span></td>
            <td>Para cada 10 novos votantes na seção, +5,37 votos nominais para Lula</td>
          </tr>
          <tr>
            <td><strong>Densidade Telefônica Anatel (β₂)</strong></td>
            <td><strong style="color:#06b6d4;">+0,2386</strong></td>
            <td>0,0115</td>
            <td>+20,68</td>
            <td><span class="code-tag">p < 10⁻⁹⁰</span></td>
            <td><span class="status-badge status-cyan">p < 0,001</span></td>
            <td>A cada 10 pontos a mais de densidade celular municipal, +2,39 votos adicionais para Lula</td>
          </tr>
        </tbody>
      </table>
      <div style="margin-top: 14px; font-size: 13px; color: var(--text-muted); display: flex; gap: 24px;">
        <div>Coeficiente de Determinação: <strong style="color:#ffffff;">R² = 54,8%</strong></div>
        <div>Tamanho da Amostra: <strong style="color:#ffffff;">N = 1.000 Urnas</strong></div>
        <div>Graus de Liberdade: <strong style="color:#ffffff;">DF = 997</strong></div>
      </div>
    </section>

    <!-- ========================================================================= -->
    <!-- PARTE 4: TABELA ANALÍTICA GRANULAR COMPLETA DAS 1.000 URNAS              -->
    <!-- ========================================================================= -->
    <section class="glass-panel">
      <div class="panel-header">
        <div>
          <div class="panel-title"><span class="icon">📋</span> Super Amostra das 1.000 Urnas Oficiais (Tabela Auditada Completa)</div>
          <div class="panel-subtitle">Explore todas as 1.000 seções eleitorais auditadas com busca em tempo real e paginação rápida</div>
        </div>
      </div>
      
      <div class="table-controls">
        <input type="text" id="table-search" class="search-input" placeholder="🔍 Buscar município, zona ou seção...">
        <div class="pagination-bar">
          <span id="page-info">Página 1 de 20 (1.000 itens)</span>
          <button id="prev-btn" class="page-btn">← Anterior</button>
          <button id="next-btn" class="page-btn">Próxima →</button>
        </div>
      </div>

      <div class="table-wrapper">
        <table class="data-table" id="sample-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Município</th>
              <th>Zona</th>
              <th>Seção</th>
              <th>Modelo Urna</th>
              <th>Densidade Anatel</th>
              <th>% Pós-Pago</th>
              <th>Comp T1</th>
              <th>Comp T2</th>
              <th>Δ Comp</th>
              <th>Abst T1 (%)</th>
              <th>Abst T2 (%)</th>
              <th>Δ Abst (%)</th>
              <th>% Man T1</th>
              <th>% Man T2</th>
              <th>Δ Man (%)</th>
              <th>Lula T1</th>
              <th>Lula T2</th>
              <th>Δ Lula</th>
              <th>Bolso T1</th>
              <th>Bolso T2</th>
              <th>Δ Bolso</th>
            </tr>
          </thead>
          <tbody id="table-body">
            <!-- Linhas geradas via JavaScript -->
          </tbody>
        </table>
      </div>
    </section>
  </main>

  <!-- Script de Dados e Lógica Plotly/Tabela -->
  <script>
    const sampleData = {data_json};
    const statsData = {stats_json};
    const anatelData = {anatel_stats_json};

    let filteredData = sampleData;
    let currentPage = 1;
    const pageSize = 50;

    function renderTable() {{
      const tbody = document.getElementById("table-body");
      tbody.innerHTML = "";
      
      const start = (currentPage - 1) * pageSize;
      const end = Math.min(start + pageSize, filteredData.length);
      const pageRows = filteredData.slice(start, end);

      pageRows.forEach((row, idx) => {{
        const tr = document.createElement("tr");

        let modelClass = "badge-ue2020";
        if (row.MODELO_URNA === "UE2015") modelClass = "badge-ue2015";
        else if (row.MODELO_URNA === "UE2013") modelClass = "badge-ue2013";
        else if (row.MODELO_URNA === "UE2009") modelClass = "badge-ue2009";

        const diffComp = row.DIF_COMP;
        const diffCompSign = diffComp > 0 ? "+" : "";
        const diffCompClass = diffComp > 0 ? "diff-pos" : (diffComp < 0 ? "diff-neg" : "diff-zero");

        const diffAbst = row.DIF_PCT_ABST;
        const diffAbstSign = diffAbst > 0 ? "+" : "";
        const diffAbstClass = diffAbst < 0 ? "diff-pos" : (diffAbst > 0 ? "diff-neg" : "diff-zero");

        const diffMan = row.DIF_PCT_MANUAL;
        const diffManSign = diffMan > 0 ? "+" : "";
        const diffManClass = diffMan > 0 ? "diff-neg" : (diffMan < 0 ? "diff-pos" : "diff-zero");

        const diffLula = row.DIF_VOTOS_13;
        const diffBolsonaro = row.DIF_VOTOS_22;

        tr.innerHTML = `
          <td><strong>${{start + idx + 1}}</strong></td>
          <td><strong>${{row.MUNICIPIO}}</strong></td>
          <td>${{row.ZONA}}</td>
          <td>${{row.SECAO}}</td>
          <td><span class="model-badge ${{modelClass}}">${{row.MODELO_URNA}}</span></td>
          <td><span class="code-tag" style="color:#06b6d4;">${{row.DENS_SMP ? row.DENS_SMP.toFixed(1) : '-'}}</span></td>
          <td>${{row.PCT_POS ? row.PCT_POS.toFixed(1) + '%' : '-'}}</td>
          <td>${{row.COMP_T1}}</td>
          <td>${{row.COMP_T2}}</td>
          <td class="${{diffCompClass}}"><strong>${{diffCompSign}}${{diffComp}}</strong></td>
          <td>${{row.PCT_ABST_T1}}%</td>
          <td>${{row.PCT_ABST_T2}}%</td>
          <td class="${{diffAbstClass}}">${{diffAbstSign}}${{diffAbst}}%</td>
          <td>${{row.PCT_MAN_T1}}%</td>
          <td>${{row.PCT_MAN_T2}}%</td>
          <td class="${{diffManClass}}">${{diffManSign}}${{diffMan}}%</td>
          <td>${{row.VOTOS_13_T1}}</td>
          <td style="color:#f43f5e; font-weight:600;">${{row.VOTOS_13_T2}}</td>
          <td style="color:#f43f5e; font-weight:700;">${{diffLula > 0 ? '+' : ''}}${{diffLula}}</td>
          <td>${{row.VOTOS_22_T1}}</td>
          <td style="color:#38bdf8; font-weight:600;">${{row.VOTOS_22_T2}}</td>
          <td style="color:#38bdf8; font-weight:700;">${{diffBolsonaro > 0 ? '+' : ''}}${{diffBolsonaro}}</td>
        `;
        tbody.appendChild(tr);
      }});

      const totalPages = Math.ceil(filteredData.length / pageSize) || 1;
      document.getElementById("page-info").innerText = `Página ${{currentPage}} de ${{totalPages}} (${{filteredData.length}} urnas)`;
      document.getElementById("prev-btn").disabled = (currentPage === 1);
      document.getElementById("next-btn").disabled = (currentPage >= totalPages);
    }}

    document.getElementById("prev-btn").addEventListener("click", () => {{
      if (currentPage > 1) {{
        currentPage--;
        renderTable();
      }}
    }});

    document.getElementById("next-btn").addEventListener("click", () => {{
      const totalPages = Math.ceil(filteredData.length / pageSize);
      if (currentPage < totalPages) {{
        currentPage++;
        renderTable();
      }}
    }});

    document.getElementById("table-search").addEventListener("input", (e) => {{
      const q = e.target.value.toLowerCase().trim();
      if (!q) {{
        filteredData = sampleData;
      }} else {{
        filteredData = sampleData.filter(r => 
          r.MUNICIPIO.toLowerCase().includes(q) ||
          String(r.ZONA).includes(q) ||
          String(r.SECAO).includes(q) ||
          r.MODELO_URNA.toLowerCase().includes(q)
        );
      }}
      currentPage = 1;
      renderTable();
    }});

    renderTable();

    // ==========================================
    // Gráficos Plotly.js (1.000 Urnas)
    // ==========================================
    const plotlyLayoutCommon = {{
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: {{ family: 'Inter, sans-serif', color: '#94a3b8', size: 11 }},
      margin: {{ l: 50, r: 30, t: 30, b: 50 }},
      hovermode: 'closest'
    }};

    // 1. Dispersão Pareada 1.000 Urnas (Mesário 1T vs 2T)
    const scatterManualTrace = {{
      x: sampleData.map(r => r.PCT_MAN_T1),
      y: sampleData.map(r => r.PCT_MAN_T2),
      text: sampleData.map(r => `${{r.MUNICIPIO}} (Z${{r.ZONA}} S${{r.SECAO}})<br>1ºT: ${{r.PCT_MAN_T1}}% | 2ºT: ${{r.PCT_MAN_T2}}%`),
      mode: 'markers',
      type: 'scatter',
      marker: {{
        color: '#38bdf8',
        size: 5,
        opacity: 0.6,
        line: {{ color: 'rgba(255,255,255,0.2)', width: 0.5 }}
      }},
      name: 'Urna (1.000 amostradas)'
    }};

    const identityTrace = {{
      x: [0, 40],
      y: [0, 40],
      mode: 'lines',
      name: 'Identidade (y = x: Estabilidade Perfeita)',
      line: {{ color: 'rgba(244, 63, 94, 0.7)', width: 2, dash: 'dash' }}
    }};

    Plotly.newPlot('chart-scatter-manual', [scatterManualTrace, identityTrace], {{
      ...plotlyLayoutCommon,
      xaxis: {{ title: '% Liberação Manual no 1º Turno', gridcolor: 'rgba(255,255,255,0.06)' }},
      yaxis: {{ title: '% Liberação Manual no 2º Turno', gridcolor: 'rgba(255,255,255,0.06)' }},
      legend: {{ orientation: 'h', y: 1.15, x: 0.05 }}
    }}, {{ responsive: true, displayModeBar: false }});

    // 2. Boxplot Comparativo (1.000 Urnas)
    const boxTraces = [
      {{
        y: sampleData.map(r => r.PCT_MAN_T1),
        type: 'box',
        name: '1º Turno (T1)',
        boxpoints: 'outliers',
        marker: {{ color: '#38bdf8' }},
        line: {{ color: '#38bdf8' }}
      }},
      {{
        y: sampleData.map(r => r.PCT_MAN_T2),
        type: 'box',
        name: '2º Turno (T2)',
        boxpoints: 'outliers',
        marker: {{ color: '#a855f7' }},
        line: {{ color: '#a855f7' }}
      }}
    ];

    Plotly.newPlot('chart-boxplot', boxTraces, {{
      ...plotlyLayoutCommon,
      yaxis: {{ title: '% Eleitores Habilitados pelo Mesário', gridcolor: 'rgba(255,255,255,0.06)' }},
      showlegend: false
    }}, {{ responsive: true, displayModeBar: false }});

    // 3. Regressão OLS: Aumento de Comparecimento vs Ganho de Votos Nominais
    const xComp = sampleData.map(r => r.DIF_COMP);
    const yDiff13 = sampleData.map(r => r.DIF_VOTOS_13);
    const yDiff22 = sampleData.map(r => r.DIF_VOTOS_22);
    const labelsMun = sampleData.map(r => `${{r.MUNICIPIO}} (Z${{r.ZONA}} S${{r.SECAO}})`);

    const xSortedComp = [...xComp].sort((a,b) => a - b);
    const regLine13 = xSortedComp.map(x => statsData.abstencao.int_13 + statsData.abstencao.slope_13 * x);
    const regLine22 = xSortedComp.map(x => statsData.abstencao.int_22 + statsData.abstencao.slope_22 * x);

    const regressionTraces = [
      {{
        x: xComp,
        y: yDiff13,
        text: labelsMun,
        mode: 'markers',
        type: 'scatter',
        name: 'Lula (Δ Votos)',
        marker: {{ color: '#f43f5e', size: 5, opacity: 0.55 }}
      }},
      {{
        x: xSortedComp,
        y: regLine13,
        mode: 'lines',
        name: `Regressão Lula (β=${{statsData.abstencao.slope_13}}, R²=${{statsData.abstencao.r2_13}})`,
        line: {{ color: '#f43f5e', width: 2.5 }}
      }},
      {{
        x: xComp,
        y: yDiff22,
        text: labelsMun,
        mode: 'markers',
        type: 'scatter',
        name: 'Bolsonaro (Δ Votos)',
        marker: {{ color: '#38bdf8', size: 5, opacity: 0.55 }}
      }},
      {{
        x: xSortedComp,
        y: regLine22,
        mode: 'lines',
        name: `Regressão Bolsonaro (β=${{statsData.abstencao.slope_22}}, R²=${{statsData.abstencao.r2_22}})`,
        line: {{ color: '#38bdf8', width: 2, dash: 'dash' }}
      }}
    ];

    Plotly.newPlot('chart-regression-turnout', regressionTraces, {{
      ...plotlyLayoutCommon,
      xaxis: {{ title: 'Δ Comparecimento (Novos Eleitores no 2ºT)', gridcolor: 'rgba(255,255,255,0.06)' }},
      yaxis: {{ title: 'Δ Votos Nominais Ganhos (T2 - T1)', gridcolor: 'rgba(255,255,255,0.06)' }},
      legend: {{ orientation: 'h', y: 1.15, x: 0.05 }}
    }}, {{ responsive: true, displayModeBar: false }});

    // 4. Histograma Comparativo de Votos Ganhos
    const histTraceLula = {{
      x: yDiff13,
      type: 'histogram',
      opacity: 0.65,
      name: 'Ganho Votos Lula (ΔV₁₃)',
      marker: {{ color: '#f43f5e' }},
      xbins: {{ size: 5 }}
    }};

    const histTraceBolsonaro = {{
      x: yDiff22,
      type: 'histogram',
      opacity: 0.65,
      name: 'Ganho Votos Bolsonaro (ΔV₂₂)',
      marker: {{ color: '#38bdf8' }},
      xbins: {{ size: 5 }}
    }};

    Plotly.newPlot('chart-histogram', [histTraceLula, histTraceBolsonaro], {{
      ...plotlyLayoutCommon,
      barmode: 'overlay',
      xaxis: {{ title: 'Variação de Votos Nominais (T2 - T1)', gridcolor: 'rgba(255,255,255,0.06)' }},
      yaxis: {{ title: 'Frequência de Urnas', gridcolor: 'rgba(255,255,255,0.06)' }},
      legend: {{ orientation: 'h', y: 1.15, x: 0.1 }}
    }}, {{ responsive: true, displayModeBar: false }});

    // ==========================================
    // GRÁFICOS ANATEL / CONECTIVIDADE
    // ==========================================
    
    // Gráfico 5: Densidade Anatel vs Δ Comparecimento (p.p.)
    const densArr = sampleData.map(r => r.DENS_SMP);
    const deltaCompPctArr = sampleData.map(r => r.PCT_ABST_T1 - r.PCT_ABST_T2); // queda abstencao = aumento comparecimento
    
    const traceAnatelComp = {{
      x: densArr,
      y: deltaCompPctArr,
      text: sampleData.map(r => `${{r.MUNICIPIO}} (Z${{r.ZONA}} S${{r.SECAO}})<br>Densidade: ${{r.DENS_SMP ? r.DENS_SMP.toFixed(1) : '-'}} ac/100 hab<br>Δ Comp: +${{(r.PCT_ABST_T1 - r.PCT_ABST_T2).toFixed(2)}} p.p.`),
      mode: 'markers',
      type: 'scatter',
      name: 'Seção Eleitoral',
      marker: {{
        color: densArr,
        colorscale: 'Viridis',
        size: 5,
        opacity: 0.6,
        colorbar: {{ title: 'Densidade SMP', titleside: 'right', len: 0.8 }}
      }}
    }};

    // Reta de tendência: y = 0.6297 + 0.0280 * x
    const minDens = Math.min(...densArr.filter(x => x != null));
    const maxDens = Math.max(...densArr.filter(x => x != null));
    const trendX = [minDens, maxDens];
    const trendY = [0.6297 + 0.0280 * minDens, 0.6297 + 0.0280 * maxDens];

    const traceTrendComp = {{
      x: trendX,
      y: trendY,
      mode: 'lines',
      name: 'Tendência OLS (r = +0,204, p < 10⁻¹⁰)',
      line: {{ color: '#38bdf8', width: 2.5, dash: 'solid' }}
    }};

    Plotly.newPlot('chart-anatel-scatter-turnout', [traceAnatelComp, traceTrendComp], {{
      ...plotlyLayoutCommon,
      xaxis: {{ title: 'Densidade de Telefonia Móvel (Acessos SMP por 100 Habitantes - ANATEL)', gridcolor: 'rgba(255,255,255,0.06)' }},
      yaxis: {{ title: 'Variação do Comparecimento (Δ p.p. no 2º Turno)', gridcolor: 'rgba(255,255,255,0.06)' }},
      legend: {{ orientation: 'h', y: 1.15, x: 0.05 }}
    }}, {{ responsive: true, displayModeBar: false }});

    // Gráfico 6: Densidade Anatel vs Δ Votos Nominais (Lula vs Bolsonaro)
    const traceAnatelV13 = {{
      x: densArr,
      y: yDiff13,
      text: labelsMun,
      mode: 'markers',
      type: 'scatter',
      name: 'Lula (Δ Votos) [r = +0,597]',
      marker: {{ color: '#f43f5e', size: 5, opacity: 0.55 }}
    }};

    const traceAnatelV22 = {{
      x: densArr,
      y: yDiff22,
      text: labelsMun,
      mode: 'markers',
      type: 'scatter',
      name: 'Bolsonaro (Δ Votos) [r = +0,167]',
      marker: {{ color: '#38bdf8', size: 5, opacity: 0.55 }}
    }};

    // Retas de regressão linear simples com a densidade
    // Lula: y = -4.689 + 0.2386 * dens
    const trendV13Y = trendX.map(x => -4.69 + 0.2386 * x);
    const traceTrendV13 = {{
      x: trendX,
      y: trendV13Y,
      mode: 'lines',
      name: 'Tendência Lula (OLS: +0,239 voto / pt dens)',
      line: {{ color: '#f43f5e', width: 2.5 }}
    }};

    Plotly.newPlot('chart-anatel-scatter-votos', [traceAnatelV13, traceAnatelV22, traceTrendV13], {{
      ...plotlyLayoutCommon,
      xaxis: {{ title: 'Densidade de Telefonia Móvel ANATEL (Acessos / 100 hab)', gridcolor: 'rgba(255,255,255,0.06)' }},
      yaxis: {{ title: 'Ganho Nominal de Votos por Seção (T2 - T1)', gridcolor: 'rgba(255,255,255,0.06)' }},
      legend: {{ orientation: 'h', y: 1.15, x: 0.05 }}
    }}, {{ responsive: true, displayModeBar: false }});

    // Gráfico 7: Barras Agrupadas por Quartil Anatel
    const qLabels = anatelData.quartis.map(q => q.label.split(':')[0]);
    qLabels.push('Capital (SSA)', 'Interior');

    const qCompValues = anatelData.quartis.map(q => q.delta_comp_pct);
    qCompValues.push(anatelData.capital_vs_interior.capital.delta_comp_pct, anatelData.capital_vs_interior.interior.delta_comp_pct);

    const qShareLula = anatelData.quartis.map(q => q.taxa_captura_lula);
    qShareLula.push(anatelData.capital_vs_interior.capital.taxa_captura_lula, anatelData.capital_vs_interior.interior.taxa_captura_lula);

    const barTraceComp = {{
      x: qLabels,
      y: qCompValues,
      name: 'Salto Comparecimento (Δ p.p.)',
      type: 'bar',
      marker: {{ color: '#06b6d4' }}
    }};

    const barTraceShare = {{
      x: qLabels,
      y: qShareLula,
      name: 'Share Marginal Lula (% Novos Votos Válidos)',
      type: 'bar',
      yaxis: 'y2',
      marker: {{ color: '#f43f5e' }}
    }};

    Plotly.newPlot('chart-anatel-quartis-bar', [barTraceComp, barTraceShare], {{
      ...plotlyLayoutCommon,
      barmode: 'group',
      yaxis: {{ title: 'Salto no Comparecimento (Δ p.p.)', gridcolor: 'rgba(255,255,255,0.06)' }},
      yaxis2: {{
        title: 'Share Marginal de Lula (%)',
        overlaying: 'y',
        side: 'right',
        range: [60, 100],
        gridcolor: 'rgba(255,255,255,0.03)'
      }},
      legend: {{ orientation: 'h', y: 1.15, x: 0.15 }}
    }}, {{ responsive: true, displayModeBar: false }});

  </script>
</body>
</html>
"""
    output_path = Path("dashboard_estatistico_biometria_1000_urnas.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Dashboard 1.000 Urnas + Anatel gerado com sucesso em: {output_path.resolve()} ({output_path.stat().st_size:,} bytes)")

if __name__ == "__main__":
    gerar_html_1000()
