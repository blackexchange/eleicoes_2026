import os
import duckdb
import pandas as pd
import json

def export_maps_data():
    output_dir = "data/processed/google_maps"
    os.makedirs(output_dir, exist_ok=True)
    
    con = duckdb.connect("data/processed/eleicoes.duckdb")
    
    # 1. Agrupamento completo por Local de Votação (Colégio / Escola) com contagem de votos para Presidente e Modelos de Urna
    print("[1/4] Extraindo dados agregados de votos e urnas por Colégio Eleitoral...")
    df_locais = con.execute("""
        WITH votos_agg AS (
            SELECT 
                NR_ZONA,
                NR_SECAO,
                SUM(CASE WHEN NR_VOTAVEL = 13 THEN QT_VOTOS ELSE 0 END) AS VOTOS_13,
                SUM(CASE WHEN NR_VOTAVEL = 22 THEN QT_VOTOS ELSE 0 END) AS VOTOS_22,
                SUM(CASE WHEN NR_VOTAVEL NOT IN (13, 22) THEN QT_VOTOS ELSE 0 END) AS VOTOS_OUTROS,
                SUM(QT_VOTOS) AS TOTAL_VOTOS
            FROM votacao_presidente_secao_2026_BA
            GROUP BY NR_ZONA, NR_SECAO
        ),
        corresp_info AS (
            SELECT 
                TRY_CAST(NR_ZONA AS BIGINT) AS NR_ZONA,
                TRY_CAST(NR_SECAO AS BIGINT) AS NR_SECAO,
                NR_URNA_ESPERADA,
                CASE 
                    WHEN TRY_CAST(NR_URNA_ESPERADA AS BIGINT) < 2000000 THEN 'UE2015'
                    ELSE 'UE2020+'
                END AS MODELO_URNA
            FROM correspondencias_2026_BA
        ),
        locais_clean AS (
            SELECT 
                TRY_CAST(NR_ZONA AS BIGINT) AS NR_ZONA,
                TRY_CAST(NR_SECAO AS BIGINT) AS NR_SECAO,
                NM_MUNICIPIO,
                NM_LOCAL_VOTACAO,
                DS_ENDERECO,
                NM_BAIRRO,
                NR_CEP,
                TRY_CAST(REPLACE(NR_LATITUDE, ',', '.') AS DOUBLE) AS LATITUDE,
                TRY_CAST(REPLACE(NR_LONGITUDE, ',', '.') AS DOUBLE) AS LONGITUDE
            FROM locais_votacao_2026_BA
            WHERE NR_TURNO = '1'
              AND NR_LATITUDE IS NOT NULL 
              AND NR_LONGITUDE IS NOT NULL
              AND TRY_CAST(REPLACE(NR_LATITUDE, ',', '.') AS DOUBLE) BETWEEN -19.0 AND -8.0
              AND TRY_CAST(REPLACE(NR_LONGITUDE, ',', '.') AS DOUBLE) BETWEEN -47.0 AND -37.0
        )
        SELECT 
            l.NM_MUNICIPIO AS MUNICIPIO,
            l.NM_LOCAL_VOTACAO AS LOCAL_VOTACAO,
            l.DS_ENDERECO AS ENDERECO,
            l.NM_BAIRRO AS BAIRRO,
            l.NR_CEP AS CEP,
            STRING_AGG(DISTINCT CAST(l.NR_ZONA AS VARCHAR), ', ') AS ZONAS,
            AVG(l.LATITUDE) AS LATITUDE,
            AVG(l.LONGITUDE) AS LONGITUDE,
            COUNT(DISTINCT l.NR_SECAO) AS QTD_SECOES,
            COALESCE(SUM(CASE WHEN c.MODELO_URNA = 'UE2015' THEN 1 ELSE 0 END), 0) AS URNAS_UE2015,
            COALESCE(SUM(CASE WHEN c.MODELO_URNA = 'UE2020+' THEN 1 ELSE 0 END), 0) AS URNAS_UE2020,
            COALESCE(SUM(v.VOTOS_13), 0) AS VOTOS_13,
            COALESCE(SUM(v.VOTOS_22), 0) AS VOTOS_22,
            COALESCE(SUM(v.VOTOS_OUTROS), 0) AS VOTOS_OUTROS,
            COALESCE(SUM(v.TOTAL_VOTOS), 0) AS TOTAL_VOTOS,
            ROUND(CASE WHEN SUM(v.TOTAL_VOTOS) > 0 THEN (SUM(v.VOTOS_13) * 100.0 / SUM(v.TOTAL_VOTOS)) ELSE 0 END, 2) AS PCT_VOTOS_13,
            ROUND(CASE WHEN SUM(v.TOTAL_VOTOS) > 0 THEN (SUM(v.VOTOS_22) * 100.0 / SUM(v.TOTAL_VOTOS)) ELSE 0 END, 2) AS PCT_VOTOS_22
        FROM locais_clean l
        LEFT JOIN votos_agg v ON l.NR_ZONA = v.NR_ZONA AND l.NR_SECAO = v.NR_SECAO
        LEFT JOIN corresp_info c ON l.NR_ZONA = c.NR_ZONA AND l.NR_SECAO = c.NR_SECAO
        GROUP BY l.NM_MUNICIPIO, l.NM_LOCAL_VOTACAO, l.DS_ENDERECO, l.NM_BAIRRO, l.NR_CEP
        ORDER BY VOTOS_13 DESC
    """).df()
    
    arquivo_locais = os.path.join(output_dir, "locais_votacao_heatmap_votos_urnas_BA_2026.csv")
    df_locais.to_csv(arquivo_locais, index=False, encoding="utf-8")
    print(f"[OK] CSV de Locais de Votação com Votos e Urnas gerado: {arquivo_locais} ({len(df_locais)} registros)")
    
    # 2. Gerar Mapa Interativo e Heatmap das Urnas e Votos (Arquivo Único Oficial)
    print("[2/4] Construindo Dashboard Interativo com Heatmap e Painel Detalhado de Urnas...")
    mapa_path = os.path.join(output_dir, "mapa_interativo_urnas_BA_2026.html")
    gerar_heatmap_dashboard_html(df_locais, mapa_path)
    print(f"[OK] Dashboard unificado disponível em: {mapa_path}")
    
    # 3. Gerar pasta docs/index.html para publicação automática no GitHub Pages
    docs_dir = "docs"
    os.makedirs(docs_dir, exist_ok=True)
    docs_path = os.path.join(docs_dir, "index.html")
    gerar_heatmap_dashboard_html(df_locais, docs_path)
    print(f"[OK] Arquivo para GitHub Pages gerado: {docs_path}")

def gerar_heatmap_dashboard_html(df, output_path):
    records = []
    for _, row in df.iterrows():
        records.append({
            "m": str(row["MUNICIPIO"]),
            "l": str(row["LOCAL_VOTACAO"]),
            "e": str(row["ENDERECO"]) if pd.notna(row["ENDERECO"]) else "",
            "b": str(row["BAIRRO"]) if pd.notna(row["BAIRRO"]) else "",
            "z": str(row["ZONAS"]) if pd.notna(row["ZONAS"]) else "",
            "lat": round(float(row["LATITUDE"]), 6),
            "lng": round(float(row["LONGITUDE"]), 6),
            "sec": int(row["QTD_SECOES"]),
            "u15": int(row["URNAS_UE2015"]),
            "u20": int(row["URNAS_UE2020"]),
            "v13": int(row["VOTOS_13"]),
            "v22": int(row["VOTOS_22"]),
            "vo": int(row["VOTOS_OUTROS"]),
            "vt": int(row["TOTAL_VOTOS"]),
            "p13": float(row["PCT_VOTOS_13"]),
            "p22": float(row["PCT_VOTOS_22"])
        })
    
    data_json = json.dumps(records, ensure_ascii=False)
    
    bahia_geojson_str = "{}"
    if os.path.exists("data/geo/bahia_boundary.geojson"):
        with open("data/geo/bahia_boundary.geojson", "r", encoding="utf-8") as f:
            bahia_geojson_str = f.read()
    
    total_locais = len(df)
    total_secoes = int(df["QTD_SECOES"].sum())
    total_ue2015 = int(df["URNAS_UE2015"].sum())
    total_ue2020 = int(df["URNAS_UE2020"].sum())
    total_votos_13 = int(df["VOTOS_13"].sum())
    total_votos_22 = int(df["VOTOS_22"].sum())
    total_votos_geral = int(df["TOTAL_VOTOS"].sum())
    pct_13_global = round((total_votos_13 / total_votos_geral) * 100, 1) if total_votos_geral > 0 else 0

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel Interativo de Urnas e Heatmap de Votos - Bahia 2026</title>
    <!-- Leaflet & MarkerCluster CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.min.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.Default.min.css" />
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
    <style>
        :root {{
            --bg-main: #0b0f19;
            --bg-card: #151d30;
            --bg-card-hover: #1c2640;
            --border-color: #23314e;
            --accent-pt: #ef4444;
            --accent-pl: #3b82f6;
            --accent-amber: #f59e0b;
            --accent-emerald: #10b981;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --font-main: 'Outfit', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: var(--font-main); }}
        body {{
            display: flex;
            height: 100vh;
            width: 100vw;
            overflow: hidden;
            background: var(--bg-main);
            color: var(--text-main);
        }}
        /* Sidebar Styling */
        #sidebar {{
            width: 440px;
            min-width: 440px;
            background: var(--bg-card);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            gap: 14px;
            padding: 20px;
            box-shadow: 6px 0 30px rgba(0,0,0,0.6);
            z-index: 1000;
            overflow-y: auto;
            position: relative;
        }}
        #sidebar::-webkit-scrollbar {{ width: 6px; }}
        #sidebar::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
        
        #map-container {{
            flex: 1;
            height: 100%;
            position: relative;
        }}
        #map {{ width: 100%; height: 100%; background: #080c14; }}

        /* Header Elements */
        .badge-header {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}
        .badge-amber {{
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border-color: rgba(245, 158, 11, 0.3);
        }}
        h1 {{
            font-size: 1.35rem;
            font-weight: 800;
            line-height: 1.25;
            margin-top: 8px;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{
            font-size: 0.82rem;
            color: var(--text-muted);
            margin-top: 4px;
            line-height: 1.4;
        }}

        /* KPI Cards Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }}
        .kpi-card {{
            background: var(--bg-main);
            padding: 12px 14px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            position: relative;
            overflow: hidden;
            transition: transform 0.2s, border-color 0.2s;
        }}
        .kpi-card:hover {{
            transform: translateY(-2px);
            border-color: #3b82f6;
        }}
        .kpi-card.pt-glow {{
            border-color: rgba(239, 68, 68, 0.4);
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.08);
        }}
        .kpi-title {{
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--text-muted);
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .kpi-val {{
            font-size: 1.35rem;
            font-weight: 800;
            font-family: var(--font-mono);
            color: #ffffff;
            margin-top: 4px;
        }}
        .kpi-val.red {{ color: #f87171; }}
        .kpi-val.blue {{ color: #60a5fa; }}
        .kpi-val.amber {{ color: #fbbf24; }}
        .kpi-val.emerald {{ color: #34d399; }}
        .kpi-sub {{
            font-size: 0.72rem;
            color: var(--text-muted);
            margin-top: 2px;
        }}

        /* Section Panels */
        .control-panel {{
            background: var(--bg-main);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .panel-header {{
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94a3b8;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        /* Mode Selector Buttons */
        .mode-selector {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 6px;
        }}
        .mode-btn {{
            background: #111827;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 12px;
            color: #cbd5e1;
            cursor: pointer;
            text-align: left;
            font-size: 0.82rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.2s;
        }}
        .mode-btn:hover {{
            background: #1f293d;
            border-color: #475569;
            color: #ffffff;
        }}
        .mode-btn.active {{
            background: rgba(239, 68, 68, 0.15);
            border-color: #ef4444;
            color: #ffffff;
            box-shadow: 0 0 12px rgba(239, 68, 68, 0.25);
        }}
        .mode-btn.active.mode-22 {{
            background: rgba(59, 130, 246, 0.15);
            border-color: #3b82f6;
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.25);
        }}
        .mode-btn.active.mode-u15 {{
            background: rgba(245, 158, 11, 0.15);
            border-color: #f59e0b;
            box-shadow: 0 0 12px rgba(245, 158, 11, 0.25);
        }}

        /* Inputs & Controls */
        label {{
            font-size: 0.75rem;
            font-weight: 600;
            color: #94a3b8;
            display: block;
            margin-bottom: 4px;
        }}
        select, input[type="text"] {{
            width: 100%;
            padding: 9px 12px;
            background: #0b0f19;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: #f8fafc;
            font-size: 0.85rem;
            outline: none;
            transition: border-color 0.2s;
        }}
        select:focus, input[type="text"]:focus {{
            border-color: #ef4444;
        }}

        /* Range Slider */
        .range-container {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        input[type="range"] {{
            flex: 1;
            accent-color: #ef4444;
            height: 6px;
            background: #1e293b;
            border-radius: 3px;
        }}
        .range-val {{
            font-family: var(--font-mono);
            font-size: 0.78rem;
            color: #f87171;
            font-weight: 700;
            min-width: 45px;
            text-align: right;
        }}

        /* Top Hotspots List */
        .hotspot-item {{
            background: #0d1322;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 10px 12px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .hotspot-item:hover {{
            background: #182238;
            border-color: #ef4444;
            transform: translateX(3px);
        }}
        .hotspot-title {{
            font-size: 0.82rem;
            font-weight: 700;
            color: #f8fafc;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .hotspot-sub {{
            font-size: 0.72rem;
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
        }}

        /* Toggle Layer Pill */
        .toggle-layer-btn {{
            padding: 8px 12px;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 6px;
            color: #cbd5e1;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.2s;
        }}
        .toggle-layer-btn.active {{
            background: #0284c7;
            border-color: #38bdf8;
            color: #ffffff;
        }}

        /* Map Legend Overlay */
        .map-legend {{
            position: absolute;
            bottom: 24px;
            right: 24px;
            background: rgba(15, 23, 42, 0.92);
            backdrop-filter: blur(8px);
            border: 1px solid var(--border-color);
            padding: 14px 18px;
            border-radius: 12px;
            z-index: 1000;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-width: 220px;
        }}
        .legend-title {{
            font-size: 0.75rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #f8fafc;
        }}
        .gradient-bar {{
            height: 12px;
            border-radius: 6px;
            width: 100%;
            background: linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444);
        }}
        .legend-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.7rem;
            color: #94a3b8;
            font-family: var(--font-mono);
        }}

        /* Slide-in Detail Drawer for Polling Place & Urnas */
        #detailDrawer {{
            position: absolute;
            top: 20px;
            right: -480px;
            width: 440px;
            max-height: calc(100vh - 40px);
            background: rgba(15, 23, 42, 0.96);
            backdrop-filter: blur(12px);
            border: 1px solid #334155;
            border-radius: 16px;
            box-shadow: -10px 15px 40px rgba(0,0,0,0.7);
            z-index: 1200;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            transition: right 0.35s cubic-bezier(0.16, 1, 0.3, 1);
            padding: 20px;
            gap: 14px;
        }}
        #detailDrawer.open {{
            right: 20px;
        }}
        #detailDrawer::-webkit-scrollbar {{ width: 6px; }}
        #detailDrawer::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}

        .drawer-close-btn {{
            position: absolute;
            top: 16px;
            right: 16px;
            background: #1e293b;
            border: 1px solid #334155;
            color: #cbd5e1;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .drawer-close-btn:hover {{
            background: #ef4444;
            color: #ffffff;
            border-color: #ef4444;
        }}

        .detail-card {{
            background: #0b0f19;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .detail-card-title {{
            font-size: 0.75rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94a3b8;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .candidate-card {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
            background: #111827;
        }}
        .candidate-card.lula {{
            border-color: rgba(239, 68, 68, 0.4);
            background: rgba(239, 68, 68, 0.08);
        }}
        .candidate-card.bolsonaro {{
            border-color: rgba(59, 130, 246, 0.4);
            background: rgba(59, 130, 246, 0.08);
        }}

        /* Custom Leaflet Popups */
        .leaflet-popup-content-wrapper {{
            background: #111827;
            color: #f8fafc;
            border-radius: 14px;
            border: 1px solid #374151;
            box-shadow: 0 15px 35px rgba(0,0,0,0.7);
            padding: 6px;
        }}
        .leaflet-popup-tip {{ background: #111827; }}
        .popup-card {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-width: 280px;
            max-width: 320px;
        }}
        .popup-school {{
            font-size: 0.95rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.3;
        }}
        .popup-city {{
            font-size: 0.75rem;
            color: #94a3b8;
            margin-top: 2px;
        }}
        .popup-metric-row {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            padding: 3px 0;
        }}
        .vote-bar-container {{
            width: 100%;
            height: 8px;
            background: #1f2937;
            border-radius: 4px;
            overflow: hidden;
            display: flex;
            margin-top: 4px;
        }}
        .vote-bar-13 {{ background: #ef4444; height: 100%; }}
        .vote-bar-22 {{ background: #3b82f6; height: 100%; }}
        .vote-bar-outros {{ background: #6b7280; height: 100%; }}
        
        .btn-action {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 8px 12px;
            border-radius: 8px;
            background: #1e293b;
            color: #f8fafc;
            text-decoration: none;
            font-size: 0.8rem;
            font-weight: 600;
            border: 1px solid #334155;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .btn-action:hover {{
            background: #334155;
            border-color: #38bdf8;
            color: #38bdf8;
        }}
    </style>
</head>
<body>
    <div id="sidebar">
        <!-- Header -->
        <div>
            <div style="display: flex; gap: 8px;">
                <span class="badge-header"><i class="fa-solid fa-fire"></i> Heatmap 2026</span>
                <span class="badge-header badge-amber"><i class="fa-solid fa-check-to-slot"></i> Urnas Eleitorais</span>
            </div>
            <h1>Concentração de Votos (13) & Urnas</h1>
            <p class="subtitle">Clique em qualquer urna ou ponto no mapa para inspecionar os votos e modelos de urna.</p>
        </div>

        <!-- KPI Cards -->
        <div class="kpi-grid">
            <div class="kpi-card pt-glow">
                <div class="kpi-title">Votos 13 (Lula / PT) <i class="fa-solid fa-fire" style="color:#f87171;"></i></div>
                <div class="kpi-val red" id="kpiVotos13">{total_votos_13:,}</div>
                <div class="kpi-sub" id="kpiPct13">{pct_13_global}% dos votos válidos</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Votos 22 (Flávio / PL) <i class="fa-solid fa-flag" style="color:#60a5fa;"></i></div>
                <div class="kpi-val blue" id="kpiVotos22">{total_votos_22:,}</div>
                <div class="kpi-sub" id="kpiPct22">{round((total_votos_22/total_votos_geral)*100, 1)}% dos válidos</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Locais Mapeados <i class="fa-solid fa-school" style="color:#38bdf8;"></i></div>
                <div class="kpi-val emerald" id="kpiLocais">{total_locais:,}</div>
                <div class="kpi-sub" id="kpiSecoes">{total_secoes:,} seções eleitorais</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Urnas UE2015 <i class="fa-solid fa-box-archive" style="color:#fbbf24;"></i></div>
                <div class="kpi-val amber" id="kpiUE2015">{total_ue2015:,}</div>
                <div class="kpi-sub" id="kpiUE2020">{total_ue2020:,} urnas UE2020+</div>
            </div>
        </div>

        <!-- Seletor de Camada Heatmap -->
        <div class="control-panel">
            <div class="panel-header"><i class="fa-solid fa-layer-group"></i> Camada do Heatmap</div>
            <div class="mode-selector">
                <button class="mode-btn active" data-mode="votos13" id="btnMode13">
                    <span><i class="fa-solid fa-fire text-red-500" style="color:#ef4444; margin-right:6px;"></i> Volume Total de Votos no 13</span>
                    <i class="fa-solid fa-check"></i>
                </button>
                <button class="mode-btn" data-mode="pct13" id="btnModePct13">
                    <span><i class="fa-solid fa-percent" style="color:#f87171; margin-right:6px;"></i> Intensidade de Domínio (% Votos 13)</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="mode-btn mode-22" data-mode="votos22" id="btnMode22">
                    <span><i class="fa-solid fa-chart-column" style="color:#3b82f6; margin-right:6px;"></i> Volume Total de Votos no 22</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="mode-btn mode-u15" data-mode="urnasUE2015" id="btnModeU15">
                    <span><i class="fa-solid fa-box-archive" style="color:#f59e0b; margin-right:6px;"></i> Concentração de Urnas UE2015</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
            </div>
        </div>

        <!-- Filtros e Ajustes -->
        <div class="control-panel">
            <div class="panel-header"><i class="fa-solid fa-sliders"></i> Filtros de Exploração</div>
            
            <div>
                <label><i class="fa-solid fa-city"></i> Município:</label>
                <select id="municipioSelect">
                    <option value="">Todos os 417 Municípios da Bahia</option>
                </select>
            </div>

            <div>
                <label><i class="fa-solid fa-filter"></i> Modelo de Urna:</label>
                <select id="urnaFilter">
                    <option value="all">Todos os Modelos de Urna</option>
                    <option value="ue2015">Apenas Locais com Urnas UE2015 (Anteriores a 2020)</option>
                    <option value="ue2020">Apenas Locais com Urnas UE2020+</option>
                </select>
            </div>

            <div>
                <label><i class="fa-solid fa-magnifying-glass"></i> Busca Rápida de Escola/Bairro:</label>
                <input type="text" id="searchInput" placeholder="Digite nome da escola, bairro, endereço..." />
            </div>

            <!-- Calibração de Sensibilidade do Heatmap -->
            <div style="border-top: 1px solid var(--border-color); padding-top: 10px; margin-top: 4px;">
                <div class="panel-header" style="margin-bottom: 8px;"><i class="fa-solid fa-wand-magic-sparkles" style="color:#f59e0b;"></i> Calibração do Heatmap</div>
                
                <div style="margin-bottom: 8px;">
                    <label><i class="fa-solid fa-chart-line"></i> Escala de Comparação:</label>
                    <select id="scaleModeSelect">
                        <option value="relativo" selected>🎯 Relativa ao Filtro Atual (Recomendado)</option>
                        <option value="sqrt">⚡ Raiz Quadrada / Alta Sensibilidade</option>
                        <option value="global">🌐 Escala Global (Bahia Inteira)</option>
                    </select>
                </div>

                <div style="margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <label style="margin: 0;"><i class="fa-solid fa-bolt" style="color:#ef4444;"></i> Sensibilidade / Ganho Térmico:</label>
                        <span class="range-val" id="gainLabel">1.8x</span>
                    </div>
                    <div class="range-container" style="margin-top: 4px;">
                        <input type="range" id="gainSlider" min="0.5" max="4.0" step="0.1" value="1.8" />
                    </div>
                </div>

                <div style="margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <label style="margin: 0;"><i class="fa-solid fa-circle-dot" style="color:#38bdf8;"></i> Raio de Dispersão:</label>
                        <span class="range-val" id="radiusLabel">35px</span>
                    </div>
                    <div class="range-container" style="margin-top: 4px;">
                        <input type="range" id="radiusSlider" min="15" max="80" value="35" />
                    </div>
                </div>

                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <label style="margin: 0;"><i class="fa-solid fa-filter-circle-dollar"></i> Mínimo de Votos no 13:</label>
                        <span class="range-val" id="minVotesLabel">0</span>
                    </div>
                    <div class="range-container" style="margin-top: 4px;">
                        <input type="range" id="minVotesSlider" min="0" max="2500" step="50" value="0" />
                    </div>
                </div>
            </div>

            <button class="toggle-layer-btn active" id="toggleMarkersBtn" style="margin-top: 6px;">
                <span><i class="fa-solid fa-location-dot"></i> Exibir Marcadores / Colégios</span>
                <i class="fa-solid fa-eye" id="markersEyeIcon"></i>
            </button>
        </div>

        <!-- Top Hotspots Votos 13 -->
        <div class="control-panel">
            <div class="panel-header"><i class="fa-solid fa-trophy" style="color:#ef4444;"></i> Top Colégios em Votos (13)</div>
            <div id="hotspotsList" style="display: flex; flex-direction: column; gap: 8px;">
                <!-- Dinâmico via JS -->
            </div>
        </div>

        <div style="margin-top: auto; font-size: 0.72rem; color: #64748b; line-height: 1.4; padding-top: 10px; border-top: 1px solid var(--border-color);">
            <i class="fa-solid fa-shield-halved"></i> <strong>Fonte Oficial:</strong> Dados Abertos do TSE 2026 (Boletins de Urna, Locais de Votação e Correspondências de Urnas).
        </div>
    </div>

    <div id="map-container">
        <div id="map"></div>
        
        <!-- Legend Overlay -->
        <div class="map-legend">
            <div class="legend-title" id="legendTitle">Densidade Relativa de Votos (13)</div>
            <div class="gradient-bar" id="legendBar"></div>
            <div class="legend-labels">
                <span>Baixa Concentração</span>
                <span>Alta Densidade</span>
            </div>
        </div>

        <!-- Slide-in Detail Drawer -->
        <div id="detailDrawer">
            <button class="drawer-close-btn" id="drawerCloseBtn" title="Fechar"><i class="fa-solid fa-xmark"></i></button>
            
            <div>
                <span class="badge-header" id="drawerBadge"><i class="fa-solid fa-school"></i> Colégio Eleitoral</span>
                <h2 id="drawerSchoolName" style="font-size: 1.15rem; font-weight: 800; margin-top: 6px; line-height: 1.3;">-</h2>
                <p id="drawerAddress" style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;"><i class="fa-solid fa-location-dot"></i> -</p>
                <p id="drawerZones" style="font-size: 0.75rem; color: #64748b; margin-top: 2px;"><i class="fa-solid fa-landmark"></i> Zonas: -</p>
            </div>

            <!-- Modelos de Urna e Seções -->
            <div class="detail-card">
                <div class="detail-card-title"><i class="fa-solid fa-box-archive" style="color:#fbbf24;"></i> Urnas e Seções do Local</div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
                    <div style="background:#111827; padding:8px 10px; border-radius:8px; text-align:center;">
                        <div style="font-size:0.7rem; color:#94a3b8;">Seções</div>
                        <div id="drawerSecVal" style="font-size:1.15rem; font-weight:800; color:#ffffff; font-family:var(--font-mono);">0</div>
                    </div>
                    <div style="background:#111827; padding:8px 10px; border-radius:8px; text-align:center; border: 1px solid rgba(245, 158, 11, 0.3);">
                        <div style="font-size:0.7rem; color:#fbbf24;">Urnas UE2015</div>
                        <div id="drawerU15Val" style="font-size:1.15rem; font-weight:800; color:#fbbf24; font-family:var(--font-mono);">0</div>
                    </div>
                    <div style="background:#111827; padding:8px 10px; border-radius:8px; text-align:center; border: 1px solid rgba(56, 189, 248, 0.3);">
                        <div style="font-size:0.7rem; color:#38bdf8;">Urnas UE2020+</div>
                        <div id="drawerU20Val" style="font-size:1.15rem; font-weight:800; color:#38bdf8; font-family:var(--font-mono);">0</div>
                    </div>
                </div>
            </div>

            <!-- Placar de Votos Presidente -->
            <div class="detail-card">
                <div class="detail-card-title"><i class="fa-solid fa-chart-pie" style="color:#ef4444;"></i> Votação para Presidente no Local</div>
                
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div class="candidate-card lula">
                        <div>
                            <div style="font-size: 0.85rem; font-weight: 800; color: #f87171;"><i class="fa-solid fa-circle-check"></i> Lula (13) - PT</div>
                            <div style="font-size: 0.72rem; color: #94a3b8;">Votos válidos recebidos</div>
                        </div>
                        <div style="text-align: right;">
                            <div id="drawerV13Val" style="font-size: 1.15rem; font-weight: 800; color: #f87171; font-family: var(--font-mono);">0</div>
                            <div id="drawerP13Val" style="font-size: 0.75rem; font-weight: 700; color: #fca5a5;">0%</div>
                        </div>
                    </div>

                    <div class="candidate-card bolsonaro">
                        <div>
                            <div style="font-size: 0.85rem; font-weight: 800; color: #60a5fa;"><i class="fa-solid fa-circle-check"></i> Bolsonaro (22) - PL</div>
                            <div style="font-size: 0.72rem; color: #94a3b8;">Votos válidos recebidos</div>
                        </div>
                        <div style="text-align: right;">
                            <div id="drawerV22Val" style="font-size: 1.15rem; font-weight: 800; color: #60a5fa; font-family: var(--font-mono);">0</div>
                            <div id="drawerP22Val" style="font-size: 0.75rem; font-weight: 700; color: #93c5fd;">0%</div>
                        </div>
                    </div>

                    <div class="candidate-card" style="background:#111827;">
                        <div>
                            <div style="font-size: 0.85rem; font-weight: 700; color: #cbd5e1;"><i class="fa-solid fa-circle-minus"></i> Outros / Brancos / Nulos</div>
                            <div style="font-size: 0.72rem; color: #94a3b8;">Demais votos registrados</div>
                        </div>
                        <div style="text-align: right;">
                            <div id="drawerVoVal" style="font-size: 1.15rem; font-weight: 800; color: #cbd5e1; font-family: var(--font-mono);">0</div>
                            <div id="drawerPoVal" style="font-size: 0.75rem; font-weight: 700; color: #94a3b8;">0%</div>
                        </div>
                    </div>
                </div>

                <!-- Barra Visual -->
                <div style="margin-top: 4px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.75rem; font-weight:700; color:#94a3b8; margin-bottom:4px;">
                        <span>Total de Votos no Local:</span>
                        <span id="drawerVtVal" style="color:#ffffff; font-family:var(--font-mono);">0</span>
                    </div>
                    <div class="vote-bar-container" style="height: 10px;">
                        <div class="vote-bar-13" id="drawerBar13" style="width: 0%;"></div>
                        <div class="vote-bar-22" id="drawerBar22" style="width: 0%;"></div>
                        <div class="vote-bar-outros" id="drawerBarOutros" style="width: 0%;"></div>
                    </div>
                </div>
            </div>

            <!-- Botões de Ação -->
            <div style="display: flex; gap: 8px; margin-top: auto;">
                <button class="btn-action" id="drawerCenterBtn" style="flex:1;"><i class="fa-solid fa-crosshairs"></i> Focar no Mapa</button>
                <a class="btn-action" id="drawerGmapsBtn" target="_blank" style="flex:1;"><i class="fa-solid fa-arrow-up-right-from-square"></i> Google Maps</a>
            </div>
        </div>
    </div>

    <!-- Scripts (CDNJS & Leaflet Heat) -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.heat/0.2.0/leaflet-heat.js"></script>
    <script>
        const rawData = {data_json};
        const bahiaBoundary = {bahia_geojson_str};

        // Formatação de números padrão BR
        const fmt = num => (num || 0).toLocaleString('pt-BR');

        // Inicializar Mapa centrado na Bahia
        const map = L.map('map', {{
            center: [-12.9714, -38.5014],
            zoom: 7,
            preferCanvas: true
        }});

        // Camadas Base 100% livres, sem bloqueio de referer e sem API Key
        const baseOsmHot = L.tileLayer('https://{{s}}.tile.openstreetmap.fr/hot/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles by HOT',
            maxZoom: 19
        }});
        const baseOsmStandard = L.tileLayer('https://{{s}}.tile.openstreetmap.fr/osmfr/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap France',
            maxZoom: 19
        }});
        const baseStreet = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: '&copy; Esri, HERE, Garmin, USGS',
            maxZoom: 19
        }});
        const baseSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: '&copy; Esri World Imagery',
            maxZoom: 18
        }});
        const baseTopo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: '&copy; Esri Topo Map',
            maxZoom: 19
        }});

        // Adicionar OpenStreetMap por padrão
        baseOsmHot.addTo(map);

        // Seletor de Camadas Base no Mapa
        L.control.layers({{
            "🗺️ OpenStreetMap (HOT)": baseOsmHot,
            "🗺️ OpenStreetMap (Padrão)": baseOsmStandard,
            "🏢 Urbano (Esri)": baseStreet,
            "🛰️ Imagem Satélite": baseSat,
            "🏔️ Topográfico": baseTopo
        }}, null, {{ position: 'topright' }}).addTo(map);

        // Contorno da Bahia
        if (bahiaBoundary && bahiaBoundary.type) {{
            L.geoJSON(bahiaBoundary, {{
                style: {{
                    color: '#38bdf8',
                    weight: 2,
                    opacity: 0.8,
                    fillColor: '#0284c7',
                    fillOpacity: 0.03
                }}
            }}).addTo(map);
        }}

        // Instâncias das Camadas
        let heatLayer = null;
        let activeHighlightRing = null;

        const markersCluster = L.markerClusterGroup({{
            chunkedLoading: true,
            maxClusterRadius: 40,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false
        }});
        map.addLayer(markersCluster);

        // Estado Global
        let currentMode = 'votos13';
        let showMarkers = true;
        let currentRadius = 35;
        let selectedItem = null;

        // Elementos DOM
        const munSelect = document.getElementById('municipioSelect');
        const urnaFilter = document.getElementById('urnaFilter');
        const searchInput = document.getElementById('searchInput');
        const scaleModeSelect = document.getElementById('scaleModeSelect');
        const gainSlider = document.getElementById('gainSlider');
        const gainLabel = document.getElementById('gainLabel');
        const radiusSlider = document.getElementById('radiusSlider');
        const radiusLabel = document.getElementById('radiusLabel');
        const minVotesSlider = document.getElementById('minVotesSlider');
        const minVotesLabel = document.getElementById('minVotesLabel');
        const toggleMarkersBtn = document.getElementById('toggleMarkersBtn');
        const markersEyeIcon = document.getElementById('markersEyeIcon');
        const legendTitle = document.getElementById('legendTitle');
        const legendBar = document.getElementById('legendBar');
        const hotspotsList = document.getElementById('hotspotsList');

        // Drawer DOM Elements
        const detailDrawer = document.getElementById('detailDrawer');
        const drawerCloseBtn = document.getElementById('drawerCloseBtn');
        const drawerSchoolName = document.getElementById('drawerSchoolName');
        const drawerAddress = document.getElementById('drawerAddress');
        const drawerZones = document.getElementById('drawerZones');
        const drawerSecVal = document.getElementById('drawerSecVal');
        const drawerU15Val = document.getElementById('drawerU15Val');
        const drawerU20Val = document.getElementById('drawerU20Val');
        const drawerV13Val = document.getElementById('drawerV13Val');
        const drawerP13Val = document.getElementById('drawerP13Val');
        const drawerV22Val = document.getElementById('drawerV22Val');
        const drawerP22Val = document.getElementById('drawerP22Val');
        const drawerVoVal = document.getElementById('drawerVoVal');
        const drawerPoVal = document.getElementById('drawerPoVal');
        const drawerVtVal = document.getElementById('drawerVtVal');
        const drawerBar13 = document.getElementById('drawerBar13');
        const drawerBar22 = document.getElementById('drawerBar22');
        const drawerBarOutros = document.getElementById('drawerBarOutros');
        const drawerCenterBtn = document.getElementById('drawerCenterBtn');
        const drawerGmapsBtn = document.getElementById('drawerGmapsBtn');

        // Preencher Dropdown de Municípios
        const municipios = [...new Set(rawData.map(d => d.m))].sort();
        municipios.forEach(m => {{
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m;
            munSelect.appendChild(opt);
        }});

        // Gradients para Heatmaps
        const gradients = {{
            votos13: {{
                0.15: '#1e3a8a',
                0.35: '#06b6d4',
                0.55: '#10b981',
                0.75: '#fbbf24',
                0.90: '#f97316',
                1.00: '#ef4444'
            }},
            pct13: {{
                0.20: '#1e3a8a',
                0.45: '#9333ea',
                0.70: '#f43f5e',
                1.00: '#ef4444'
            }},
            votos22: {{
                0.20: '#1e1b4b',
                0.45: '#3b82f6',
                0.75: '#60a5fa',
                1.00: '#93c5fd'
            }},
            urnasUE2015: {{
                0.20: '#78350f',
                0.50: '#d97706',
                0.80: '#f59e0b',
                1.00: '#fef08a'
            }}
        }};

        // Função para Abrir Detalhes da Urna/Colégio
        function openItemDetails(d, flyTo = true) {{
            selectedItem = d;

            drawerSchoolName.textContent = d.l;
            drawerAddress.innerHTML = `<i class="fa-solid fa-location-dot"></i> ${{d.b ? d.b + ', ' : ''}}${{d.m}} &bull; ${{d.e || 'Endereço não informado'}}`;
            drawerZones.innerHTML = `<i class="fa-solid fa-landmark"></i> Zonas Eleitorais: <strong>${{d.z || 'N/A'}}</strong>`;
            
            drawerSecVal.textContent = d.sec;
            drawerU15Val.textContent = d.u15;
            drawerU20Val.textContent = d.u20;

            drawerV13Val.textContent = fmt(d.v13);
            drawerP13Val.textContent = d.p13 + '%';

            drawerV22Val.textContent = fmt(d.v22);
            drawerP22Val.textContent = d.p22 + '%';

            drawerVoVal.textContent = fmt(d.vo);
            const poPct = d.vt > 0 ? ((d.vo / d.vt) * 100).toFixed(1) : '0.0';
            drawerPoVal.textContent = poPct + '%';

            drawerVtVal.textContent = fmt(d.vt);

            drawerBar13.style.width = d.p13 + '%';
            drawerBar22.style.width = d.p22 + '%';
            drawerBarOutros.style.width = Math.max(0, 100 - d.p13 - d.p22) + '%';

            drawerGmapsBtn.href = `https://www.google.com/maps?q=${{d.lat}},${{d.lng}}`;

            // Destacar ponto com anel de pulso
            if (activeHighlightRing) {{
                map.removeLayer(activeHighlightRing);
            }}
            activeHighlightRing = L.circleMarker([d.lat, d.lng], {{
                radius: 14,
                color: '#38bdf8',
                weight: 3,
                opacity: 0.9,
                fillColor: '#38bdf8',
                fillOpacity: 0.25
            }}).addTo(map);

            detailDrawer.classList.add('open');

            if (flyTo) {{
                map.flyTo([d.lat, d.lng], 16, {{ duration: 1.0 }});
            }}
        }}

        drawerCloseBtn.addEventListener('click', () => {{
            detailDrawer.classList.remove('open');
            if (activeHighlightRing) {{
                map.removeLayer(activeHighlightRing);
                activeHighlightRing = null;
            }}
        }});

        drawerCenterBtn.addEventListener('click', () => {{
            if (selectedItem) {{
                map.flyTo([selectedItem.lat, selectedItem.lng], 17, {{ duration: 0.8 }});
            }}
        }});

        // Renderizar Mapa (Heatmap + Marcadores)
        function updateDashboard() {{
            const selectedMun = munSelect.value.toLowerCase();
            const selectedUrna = urnaFilter.value;
            const searchVal = searchInput.value.toLowerCase().trim();
            const scaleMode = scaleModeSelect.value;
            const gain = parseFloat(gainSlider.value);
            const minVotes = parseInt(minVotesSlider.value);

            // Filtrar Dados
            const filtered = rawData.filter(d => {{
                if (selectedMun && d.m.toLowerCase() !== selectedMun) return false;
                if (selectedUrna === 'ue2015' && d.u15 === 0) return false;
                if (selectedUrna === 'ue2020' && d.u20 === 0) return false;
                if (minVotes > 0 && d.v13 < minVotes) return false;
                if (searchVal) {{
                    const fullText = (d.l + ' ' + d.e + ' ' + d.b + ' ' + d.m).toLowerCase();
                    if (!fullText.includes(searchVal)) return false;
                }}
                return true;
            }});

            // Atualizar KPIs
            const totalV13 = filtered.reduce((acc, c) => acc + c.v13, 0);
            const totalV22 = filtered.reduce((acc, c) => acc + c.v22, 0);
            const totalGeral = filtered.reduce((acc, c) => acc + c.vt, 0);
            const totalU15 = filtered.reduce((acc, c) => acc + c.u15, 0);
            const totalU20 = filtered.reduce((acc, c) => acc + c.u20, 0);
            const totalSec = filtered.reduce((acc, c) => acc + c.sec, 0);

            document.getElementById('kpiVotos13').textContent = fmt(totalV13);
            document.getElementById('kpiVotos22').textContent = fmt(totalV22);
            document.getElementById('kpiLocais').textContent = fmt(filtered.length);
            document.getElementById('kpiSecoes').textContent = fmt(totalSec) + ' seções eleitorais';
            document.getElementById('kpiUE2015').textContent = fmt(totalU15);
            document.getElementById('kpiUE2020').textContent = fmt(totalU20) + ' urnas UE2020+';

            const pct13 = totalGeral > 0 ? ((totalV13 / totalGeral) * 100).toFixed(1) : '0.0';
            const pct22 = totalGeral > 0 ? ((totalV22 / totalGeral) * 100).toFixed(1) : '0.0';
            document.getElementById('kpiPct13').textContent = pct13 + '% dos votos válidos';
            document.getElementById('kpiPct22').textContent = pct22 + '% dos válidos';

            // Preparar Pontos do Heatmap com Normalização Relativa ao Filtro Aplicado
            const heatPoints = [];

            if (currentMode === 'votos13') {{
                const vals = filtered.map(d => d.v13).filter(v => v > 0).sort((a, b) => a - b);
                const maxVal = vals.length > 0 ? vals[vals.length - 1] : 100;
                const p85 = vals.length > 0 ? vals[Math.floor(vals.length * 0.85)] : 100;
                const refBase = scaleMode === 'relativo' ? Math.max(p85, 80) : (scaleMode === 'global' ? 6000 : maxVal);

                filtered.forEach(d => {{
                    if (d.v13 > 0) {{
                        let norm = 0;
                        if (scaleMode === 'sqrt') {{
                            norm = Math.sqrt(d.v13 / maxVal);
                        }} else {{
                            norm = Math.pow(d.v13 / refBase, 0.75);
                        }}
                        const intensity = Math.min(1.0, norm * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Densidade Relativa de Votos (13 - Lula)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
            }} else if (currentMode === 'pct13') {{
                filtered.forEach(d => {{
                    if (d.vt >= 20) {{
                        const norm = Math.pow(d.p13 / 100, 1.3);
                        const intensity = Math.min(1.0, norm * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Percentual de Domínio (13 / PT)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #9333ea, #f43f5e, #ef4444)";
            }} else if (currentMode === 'votos22') {{
                const vals = filtered.map(d => d.v22).filter(v => v > 0).sort((a, b) => a - b);
                const maxVal = vals.length > 0 ? vals[vals.length - 1] : 100;
                const p85 = vals.length > 0 ? vals[Math.floor(vals.length * 0.85)] : 100;
                const refBase = scaleMode === 'relativo' ? Math.max(p85, 80) : (scaleMode === 'global' ? 4000 : maxVal);

                filtered.forEach(d => {{
                    if (d.v22 > 0) {{
                        let norm = scaleMode === 'sqrt' ? Math.sqrt(d.v22 / maxVal) : Math.pow(d.v22 / refBase, 0.75);
                        const intensity = Math.min(1.0, norm * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Densidade Relativa de Votos (22 - Bolsonaro)";
                legendBar.style.background = "linear-gradient(to right, #1e1b4b, #3b82f6, #60a5fa, #93c5fd)";
            }} else if (currentMode === 'urnasUE2015') {{
                const maxU15 = Math.max(...filtered.map(d => d.u15), 1);
                filtered.forEach(d => {{
                    if (d.u15 > 0) {{
                        const intensity = Math.min(1.0, (d.u15 / maxU15) * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Concentração Relativa de Urnas UE2015";
                legendBar.style.background = "linear-gradient(to right, #78350f, #d97706, #f59e0b, #fef08a)";
            }}

            // Renderizar / Atualizar Heatmap Layer
            if (heatLayer) {{
                map.removeLayer(heatLayer);
            }}
            heatLayer = L.heatLayer(heatPoints, {{
                radius: currentRadius,
                blur: Math.round(currentRadius * 0.65),
                minOpacity: 0.35,
                maxZoom: 16,
                max: 1.0,
                gradient: gradients[currentMode] || gradients.votos13
            }}).addTo(map);

            // Renderizar Marcadores Cluster com evento de clique e Drawer
            markersCluster.clearLayers();
            if (showMarkers) {{
                const markerList = [];
                filtered.forEach(d => {{
                    const marker = L.circleMarker([d.lat, d.lng], {{
                        radius: 6,
                        fillColor: d.p13 >= 65 ? '#ef4444' : (d.p22 >= 50 ? '#3b82f6' : '#f59e0b'),
                        color: '#ffffff',
                        weight: 1,
                        opacity: 0.9,
                        fillOpacity: 0.85
                    }});

                    const popupContent = `
                        <div class="popup-card">
                            <div class="popup-header">
                                <div class="popup-school">${{d.l}}</div>
                                <div class="popup-city"><i class="fa-solid fa-map-pin"></i> ${{d.b ? d.b + ', ' : ''}}${{d.m}}</div>
                            </div>
                            
                            <div style="font-size:0.75rem; color:#cbd5e1; margin-top:2px;">
                                <strong>Endereço:</strong> ${{d.e || 'Não informado'}}
                            </div>

                            <div style="background:#0f172a; padding:8px 10px; border-radius:8px; border:1px solid #1f293d; margin-top:4px;">
                                <div class="popup-metric-row">
                                    <span style="color:#94a3b8;">Total de Seções:</span>
                                    <span style="font-weight:700;">${{d.sec}}</span>
                                </div>
                                <div class="popup-metric-row">
                                    <span style="color:#f59e0b;">Urnas UE2015:</span>
                                    <span style="font-weight:700; color:#fbbf24;">${{d.u15}}</span>
                                </div>
                                <div class="popup-metric-row">
                                    <span style="color:#38bdf8;">Urnas UE2020+:</span>
                                    <span style="font-weight:700; color:#38bdf8;">${{d.u20}}</span>
                                </div>
                                <div class="popup-metric-row" style="border-top:1px solid #23314e; padding-top:4px; margin-top:4px;">
                                    <span style="font-weight:700;">Total Votos Presidente:</span>
                                    <span style="font-weight:800; font-family:var(--font-mono);">${{fmt(d.vt)}}</span>
                                </div>
                            </div>

                            <div style="margin-top:4px;">
                                <div class="popup-metric-row">
                                    <span style="color:#f87171; font-weight:700;"><i class="fa-solid fa-square" style="color:#ef4444;"></i> Lula (13):</span>
                                    <span style="font-weight:800; color:#f87171;">${{fmt(d.v13)}} (${{d.p13}}%)</span>
                                </div>
                                <div class="popup-metric-row">
                                    <span style="color:#60a5fa; font-weight:700;"><i class="fa-solid fa-square" style="color:#3b82f6;"></i> Bolsonaro (22):</span>
                                    <span style="font-weight:800; color:#60a5fa;">${{fmt(d.v22)}} (${{d.p22}}%)</span>
                                </div>
                                <div class="popup-metric-row">
                                    <span style="color:#94a3b8;">Outros / Nulos:</span>
                                    <span style="color:#cbd5e1;">${{fmt(d.vo)}}</span>
                                </div>

                                <div class="vote-bar-container">
                                    <div class="vote-bar-13" style="width: ${{d.p13}}%;"></div>
                                    <div class="vote-bar-22" style="width: ${{d.p22}}%;"></div>
                                    <div class="vote-bar-outros" style="width: ${{Math.max(0, 100 - d.p13 - d.p22)}}%;"></div>
                                </div>
                            </div>

                            <button onclick="window.openItemDrawerFromPopup('${{d.lat}}', '${{d.lng}}')" style="margin-top:8px; padding:6px 10px; background:#0284c7; border:none; border-radius:6px; color:#fff; font-size:0.75rem; font-weight:700; cursor:pointer; width:100%; display:flex; align-items:center; justify-content:center; gap:6px;">
                                <i class="fa-solid fa-folder-open"></i> Ver Detalhes Completos da Urna
                            </button>
                        </div>
                    `;
                    marker.bindPopup(popupContent);
                    
                    // Clique no marcador abre o drawer
                    marker.on('click', () => {{
                        openItemDetails(d, false);
                    }});

                    markerList.push(marker);
                }});
                markersCluster.addLayers(markerList);
            }}

            // Atualizar Top Hotspots na Sidebar
            renderHotspotsList(filtered);

            // Ajustar visualização se filtrar município
            if (selectedMun && filtered.length > 0) {{
                const group = new L.featureGroup(filtered.map(d => L.marker([d.lat, d.lng])));
                map.fitBounds(group.getBounds().pad(0.1));
            }}
        }}

        // Função global para acionar o Drawer a partir de botões ou popups
        window.openItemDrawerFromPopup = function(lat, lng) {{
            const target = rawData.find(d => Math.abs(d.lat - parseFloat(lat)) < 0.00001 && Math.abs(d.lng - parseFloat(lng)) < 0.00001);
            if (target) {{
                openItemDetails(target, false);
            }}
        }};

        // Clique no Mapa encontra a urna/colégio mais próximo
        map.on('click', (e) => {{
            const clickLat = e.latlng.lat;
            const clickLng = e.latlng.lng;
            
            // Encontrar ponto mais próximo em um raio de ~3km
            let closest = null;
            let minDist = 999999;

            rawData.forEach(d => {{
                const dist = Math.hypot(d.lat - clickLat, d.lng - clickLng);
                if (dist < minDist) {{
                    minDist = dist;
                    closest = d;
                }}
            }});

            // Se o clique foi próximo (aprox. 0.03 graus ~ 3km)
            if (closest && minDist < 0.04) {{
                openItemDetails(closest, true);
            }}
        }});

        // Renderizar Lista dos Top Colégios com maior concentração de votos no 13
        function renderHotspotsList(filtered) {{
            hotspotsList.innerHTML = '';
            const top10 = [...filtered].sort((a, b) => b.v13 - a.v13).slice(0, 6);
            
            top10.forEach((d, idx) => {{
                const item = document.createElement('div');
                item.className = 'hotspot-item';
                item.innerHTML = `
                    <div class="hotspot-title">#${{idx + 1}} ${{d.l}}</div>
                    <div class="hotspot-sub">
                        <span><i class="fa-solid fa-location-dot"></i> ${{d.m}}</span>
                        <span style="color:#f87171; font-weight:700;">${{fmt(d.v13)}} votos (${{d.p13}}%)</span>
                    </div>
                `;
                item.addEventListener('click', () => {{
                    openItemDetails(d, true);
                }});
                hotspotsList.appendChild(item);
            }});
        }}

        // Eventos dos Controles
        document.querySelectorAll('.mode-btn').forEach(btn => {{
            btn.addEventListener('click', (e) => {{
                document.querySelectorAll('.mode-btn').forEach(b => {{
                    b.classList.remove('active');
                    const icon = b.querySelector('.fa-check, .fa-chevron-right');
                    if (icon) {{
                        icon.className = 'fa-solid fa-chevron-right';
                    }}
                }});
                const target = e.currentTarget;
                target.classList.add('active');
                const checkIcon = target.querySelector('.fa-chevron-right');
                if (checkIcon) {{
                    checkIcon.className = 'fa-solid fa-check';
                }}
                currentMode = target.dataset.mode;
                updateDashboard();
            }});
        }});

        radiusSlider.addEventListener('input', (e) => {{
            currentRadius = parseInt(e.target.value);
            radiusLabel.textContent = currentRadius + 'px';
            if (heatLayer) {{
                heatLayer.setOptions({{
                    radius: currentRadius,
                    blur: Math.round(currentRadius * 0.65)
                }});
            }}
        }});

        gainSlider.addEventListener('input', (e) => {{
            gainLabel.textContent = parseFloat(e.target.value).toFixed(1) + 'x';
            updateDashboard();
        }});

        minVotesSlider.addEventListener('input', (e) => {{
            minVotesLabel.textContent = fmt(parseInt(e.target.value));
            updateDashboard();
        }});

        scaleModeSelect.addEventListener('change', updateDashboard);

        toggleMarkersBtn.addEventListener('click', () => {{
            showMarkers = !showMarkers;
            if (showMarkers) {{
                toggleMarkersBtn.classList.add('active');
                markersEyeIcon.className = 'fa-solid fa-eye';
                map.addLayer(markersCluster);
            }} else {{
                toggleMarkersBtn.classList.remove('active');
                markersEyeIcon.className = 'fa-solid fa-eye-slash';
                map.removeLayer(markersCluster);
            }}
            updateDashboard();
        }});

        munSelect.addEventListener('change', updateDashboard);
        urnaFilter.addEventListener('change', updateDashboard);
        searchInput.addEventListener('input', updateDashboard);

        // Renderização Inicial
        updateDashboard();
    </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Dashboard Heatmap Leaflet HTML gerado: {output_path}")

if __name__ == "__main__":
    export_maps_data()
