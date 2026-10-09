import os
import duckdb
import pandas as pd
import json

def export_maps_data():
    output_dir = "data/processed/google_maps"
    os.makedirs(output_dir, exist_ok=True)
    
    con = duckdb.connect("data/processed/eleicoes.duckdb")
    
    # 1. Agrupamento completo por Local de Votação (Colégio / Escola) com contagem de votos, abstenções, urnas e demografia
    print("[1/4] Extraindo dados de votos, abstenção, urnas e perfil demográfico por Colégio Eleitoral...")
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
        demo_agg AS (
            SELECT 
                NR_ZONA,
                NR_SECAO,
                SUM(CASE WHEN DS_GENERO LIKE '%FEMININO%' THEN QT_ELEITORES ELSE 0 END) AS DEMO_FEM,
                SUM(CASE WHEN DS_GENERO LIKE '%MASCULINO%' THEN QT_ELEITORES ELSE 0 END) AS DEMO_MASC,
                
                SUM(CASE WHEN DS_FAIXA_ETARIA IN ('16 anos', '17 anos', '18 anos', '19 anos', '20 anos', '21 a 24 anos') THEN QT_ELEITORES ELSE 0 END) AS DEMO_JOVENS,
                SUM(CASE WHEN DS_FAIXA_ETARIA IN ('25 a 29 anos', '30 a 34 anos', '35 a 39 anos', '40 a 44 anos') THEN QT_ELEITORES ELSE 0 END) AS DEMO_ADULTOS,
                SUM(CASE WHEN DS_FAIXA_ETARIA IN ('45 a 49 anos', '50 a 54 anos', '55 a 59 anos') THEN QT_ELEITORES ELSE 0 END) AS DEMO_MADUROS,
                SUM(CASE WHEN DS_FAIXA_ETARIA IN ('60 a 64 anos', '65 a 69 anos', '70 a 74 anos', '75 a 79 anos', '80 a 84 anos', '85 a 89 anos', '90 a 94 anos', '95 a 99 anos', '100 anos ou mais') THEN QT_ELEITORES ELSE 0 END) AS DEMO_IDOSOS,
                
                SUM(CASE WHEN DS_ESTADO_CIVIL LIKE '%SOLTEIRO%' THEN QT_ELEITORES ELSE 0 END) AS DEMO_SOLTEIROS,
                SUM(CASE WHEN DS_ESTADO_CIVIL LIKE '%CASADO%' THEN QT_ELEITORES ELSE 0 END) AS DEMO_CASADOS,
                SUM(CASE WHEN DS_ESTADO_CIVIL LIKE '%DIVORCIADO%' OR DS_ESTADO_CIVIL LIKE '%SEPARADO%' THEN QT_ELEITORES ELSE 0 END) AS DEMO_DIVORCIADOS,
                SUM(CASE WHEN DS_ESTADO_CIVIL LIKE '%VI%' THEN QT_ELEITORES ELSE 0 END) AS DEMO_VIUVOS,
                
                SUM(CASE WHEN DS_GRAU_ESCOLARIDADE LIKE '%SUPERIOR%' THEN QT_ELEITORES ELSE 0 END) AS DEMO_SUPERIOR,
                SUM(CASE WHEN DS_GRAU_ESCOLARIDADE LIKE '%MEDIO%' OR DS_GRAU_ESCOLARIDADE LIKE '%M_DIO%' THEN QT_ELEITORES ELSE 0 END) AS DEMO_MEDIO,
                SUM(CASE WHEN DS_GRAU_ESCOLARIDADE LIKE '%FUNDAMENTAL%' THEN QT_ELEITORES ELSE 0 END) AS DEMO_FUNDAMENTAL,
                SUM(CASE WHEN DS_GRAU_ESCOLARIDADE LIKE '%ANALFABETO%' OR DS_GRAU_ESCOLARIDADE LIKE '%ESCREVE%' THEN QT_ELEITORES ELSE 0 END) AS DEMO_BAIXA_ESCOLARIDADE,
                
                SUM(QT_ELEITORES) AS DEMO_TOTAL_ELEITORES
            FROM perfil_eleitorado_2026_BA
            GROUP BY NR_ZONA, NR_SECAO
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
                TRY_CAST(QT_ELEITOR_SECAO AS BIGINT) AS APTOS,
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
            COALESCE(SUM(l.APTOS), 0) AS TOTAL_APTOS,
            COALESCE(SUM(CASE WHEN c.MODELO_URNA = 'UE2015' THEN 1 ELSE 0 END), 0) AS URNAS_UE2015,
            COALESCE(SUM(CASE WHEN c.MODELO_URNA = 'UE2020+' THEN 1 ELSE 0 END), 0) AS URNAS_UE2020,
            COALESCE(SUM(v.VOTOS_13), 0) AS VOTOS_13,
            COALESCE(SUM(v.VOTOS_22), 0) AS VOTOS_22,
            COALESCE(SUM(v.VOTOS_OUTROS), 0) AS VOTOS_OUTROS,
            COALESCE(SUM(v.TOTAL_VOTOS), 0) AS TOTAL_VOTOS,
            GREATEST(0, COALESCE(SUM(l.APTOS), 0) - COALESCE(SUM(v.TOTAL_VOTOS), 0)) AS TOTAL_ABSTENCOES,
            ROUND(CASE WHEN SUM(l.APTOS) > 0 THEN (GREATEST(0, SUM(l.APTOS) - SUM(v.TOTAL_VOTOS)) * 100.0 / SUM(l.APTOS)) ELSE 0 END, 2) AS PCT_ABSTENCAO,
            ROUND(CASE WHEN SUM(v.TOTAL_VOTOS) > 0 THEN (SUM(v.VOTOS_13) * 100.0 / SUM(v.TOTAL_VOTOS)) ELSE 0 END, 2) AS PCT_VOTOS_13,
            ROUND(CASE WHEN SUM(v.TOTAL_VOTOS) > 0 THEN (SUM(v.VOTOS_22) * 100.0 / SUM(v.TOTAL_VOTOS)) ELSE 0 END, 2) AS PCT_VOTOS_22,
            
            -- Demografia
            COALESCE(SUM(d.DEMO_FEM), 0) AS DEMO_FEM,
            COALESCE(SUM(d.DEMO_MASC), 0) AS DEMO_MASC,
            COALESCE(SUM(d.DEMO_JOVENS), 0) AS DEMO_JOVENS,
            COALESCE(SUM(d.DEMO_ADULTOS), 0) AS DEMO_ADULTOS,
            COALESCE(SUM(d.DEMO_MADUROS), 0) AS DEMO_MADUROS,
            COALESCE(SUM(d.DEMO_IDOSOS), 0) AS DEMO_IDOSOS,
            COALESCE(SUM(d.DEMO_SOLTEIROS), 0) AS DEMO_SOLTEIROS,
            COALESCE(SUM(d.DEMO_CASADOS), 0) AS DEMO_CASADOS,
            COALESCE(SUM(d.DEMO_DIVORCIADOS), 0) AS DEMO_DIVORCIADOS,
            COALESCE(SUM(d.DEMO_VIUVOS), 0) AS DEMO_VIUVOS,
            COALESCE(SUM(d.DEMO_SUPERIOR), 0) AS DEMO_SUPERIOR,
            COALESCE(SUM(d.DEMO_MEDIO), 0) AS DEMO_MEDIO,
            COALESCE(SUM(d.DEMO_FUNDAMENTAL), 0) AS DEMO_FUNDAMENTAL,
            COALESCE(SUM(d.DEMO_BAIXA_ESCOLARIDADE), 0) AS DEMO_BAIXA_ESCOLARIDADE,
            COALESCE(SUM(d.DEMO_TOTAL_ELEITORES), 0) AS DEMO_TOTAL_ELEITORES
        FROM locais_clean l
        LEFT JOIN votos_agg v ON l.NR_ZONA = v.NR_ZONA AND l.NR_SECAO = v.NR_SECAO
        LEFT JOIN corresp_info c ON l.NR_ZONA = c.NR_ZONA AND l.NR_SECAO = c.NR_SECAO
        LEFT JOIN demo_agg d ON l.NR_ZONA = d.NR_ZONA AND l.NR_SECAO = d.NR_SECAO
        GROUP BY l.NM_MUNICIPIO, l.NM_LOCAL_VOTACAO, l.DS_ENDERECO, l.NM_BAIRRO, l.NR_CEP
        ORDER BY VOTOS_13 DESC
    """).df()
    
    arquivo_locais = os.path.join(output_dir, "locais_votacao_heatmap_votos_urnas_BA_2026.csv")
    df_locais.to_csv(arquivo_locais, index=False, encoding="utf-8")
    print(f"[OK] CSV de Locais de Votação com Votos, Urnas e Demografia gerado: {arquivo_locais} ({len(df_locais)} registros)")
    
    # 2. Gerar Mapa Interativo e Heatmap das Urnas e Votos (Arquivo Único Oficial)
    print("[2/4] Construindo Dashboard Interativo com Heatmap, Abstenção, Demografia e Filtro de Candidato...")
    mapa_path = os.path.join(output_dir, "mapa_interativo_urnas_BA_2026.html")
    gerar_heatmap_dashboard_html(df_locais, mapa_path)
    print(f"[OK] Dashboard unificado disponível em: {mapa_path}")
    
    # Também gera heatmap_votos_13_urnas_BA.html para compatibilidade
    legacy_path = os.path.join(output_dir, "heatmap_votos_13_urnas_BA.html")
    gerar_heatmap_dashboard_html(df_locais, legacy_path)
    print(f"[OK] Arquivo espelho para compatibilidade: {legacy_path}")
    
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
            "apt": int(row["TOTAL_APTOS"]),
            "abs": int(row["TOTAL_ABSTENCOES"]),
            "pabs": float(row["PCT_ABSTENCAO"]),
            "u15": int(row["URNAS_UE2015"]),
            "u20": int(row["URNAS_UE2020"]),
            "v13": int(row["VOTOS_13"]),
            "v22": int(row["VOTOS_22"]),
            "vo": int(row["VOTOS_OUTROS"]),
            "vt": int(row["TOTAL_VOTOS"]),
            "p13": float(row["PCT_VOTOS_13"]),
            "p22": float(row["PCT_VOTOS_22"]),
            # Demografia
            "fem": int(row["DEMO_FEM"]),
            "mas": int(row["DEMO_MASC"]),
            "jov": int(row["DEMO_JOVENS"]),
            "adu": int(row["DEMO_ADULTOS"]),
            "mad": int(row["DEMO_MADUROS"]),
            "ido": int(row["DEMO_IDOSOS"]),
            "sol": int(row["DEMO_SOLTEIROS"]),
            "cas": int(row["DEMO_CASADOS"]),
            "div": int(row["DEMO_DIVORCIADOS"]),
            "viu": int(row["DEMO_VIUVOS"]),
            "sup": int(row["DEMO_SUPERIOR"]),
            "med": int(row["DEMO_MEDIO"]),
            "fun": int(row["DEMO_FUNDAMENTAL"]),
            "bax": int(row["DEMO_BAIXA_ESCOLARIDADE"]),
            "del": int(row["DEMO_TOTAL_ELEITORES"])
        })
    
    data_json = json.dumps(records, ensure_ascii=False)
    
    bahia_geojson_str = "{}"
    if os.path.exists("data/geo/bahia_boundary.geojson"):
        with open("data/geo/bahia_boundary.geojson", "r", encoding="utf-8") as f:
            bahia_geojson_str = f.read()

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bahia à Direita • Mapeamento Eleitoral 2026</title>
    <!-- Leaflet & MarkerCluster CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.min.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.Default.min.css" />
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
    <!-- Chart.js CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
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
            --accent-purple: #a855f7;
            --accent-pink: #ec4899;
            --accent-orange: #f97316;
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
        /* Sidebar Styling & Collapse Animation */
        #sidebar {{
            width: 460px;
            min-width: 460px;
            background: var(--bg-card);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 20px;
            box-shadow: 6px 0 30px rgba(0,0,0,0.6);
            z-index: 1000;
            overflow-y: auto;
            position: relative;
            transition: margin-left 0.35s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease;
        }}
        #sidebar.collapsed {{
            margin-left: -460px;
            pointer-events: none;
            opacity: 0;
        }}
        #sidebar::-webkit-scrollbar {{ width: 6px; }}
        #sidebar::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
        
        #map-container {{
            flex: 1;
            height: 100%;
            position: relative;
        }}
        #map {{ width: 100%; height: 100%; background: #080c14; }}

        /* Floating Sidebar Toggle Button */
        .sidebar-toggle-btn {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 1050;
            background: rgba(15, 23, 42, 0.94);
            backdrop-filter: blur(10px);
            border: 1px solid #334155;
            color: #f8fafc;
            height: 38px;
            padding: 0 14px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-size: 0.78rem;
            font-weight: 700;
            box-shadow: 0 6px 20px rgba(0,0,0,0.6);
            transition: all 0.2s ease;
        }}
        .sidebar-toggle-btn:hover {{
            background: #0284c7;
            border-color: #38bdf8;
            color: #ffffff;
            transform: translateY(-1px);
        }}

        /* Title Header */
        .title-container {{
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
        }}
        h1 {{
            font-size: 1.6rem;
            font-weight: 900;
            line-height: 1.15;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #60a5fa 0%, #38bdf8 50%, #ffffff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .title-subtitle {{
            font-size: 1.05rem;
            font-weight: 700;
            color: #38bdf8;
            margin-top: 2px;
            letter-spacing: -0.01em;
        }}
        .subtitle {{
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-top: 4px;
            line-height: 1.35;
        }}

        /* KPI Cards Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }}
        .kpi-card {{
            background: var(--bg-main);
            padding: 9px 12px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
            position: relative;
            overflow: hidden;
            transition: transform 0.2s, border-color 0.2s;
        }}
        .kpi-card:hover {{
            transform: translateY(-2px);
            border-color: #38bdf8;
        }}
        .kpi-card.pl-glow {{
            border-color: rgba(59, 130, 246, 0.4);
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.08);
        }}
        .kpi-card.pt-glow {{
            border-color: rgba(239, 68, 68, 0.4);
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.08);
        }}
        .kpi-title {{
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--text-muted);
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .kpi-val {{
            font-size: 1.25rem;
            font-weight: 800;
            font-family: var(--font-mono);
            color: #ffffff;
            margin-top: 3px;
        }}
        .kpi-val.red {{ color: #f87171; }}
        .kpi-val.blue {{ color: #60a5fa; }}
        .kpi-val.amber {{ color: #fbbf24; }}
        .kpi-val.emerald {{ color: #34d399; }}
        .kpi-val.purple {{ color: #c084fc; }}
        .kpi-val.pink {{ color: #f472b6; }}
        .kpi-val.orange {{ color: #fb923c; }}
        .kpi-sub {{
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-top: 2px;
        }}

        /* Section Panels */
        .control-panel {{
            background: var(--bg-main);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .panel-header {{
            font-size: 0.76rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94a3b8;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        /* Mode Selector Buttons Grid */
        .mode-selector {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 6px;
        }}
        .mode-btn {{
            background: #111827;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 8px 10px;
            color: #cbd5e1;
            cursor: pointer;
            text-align: left;
            font-size: 0.74rem;
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
            background: rgba(59, 130, 246, 0.15);
            border-color: #3b82f6;
            color: #ffffff;
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.25);
        }}

        /* Inputs & Controls */
        label {{
            font-size: 0.74rem;
            font-weight: 600;
            color: #94a3b8;
            display: block;
            margin-bottom: 3px;
        }}
        select, input[type="text"] {{
            width: 100%;
            padding: 8px 12px;
            background: #0b0f19;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: #f8fafc;
            font-size: 0.82rem;
            outline: none;
            transition: border-color 0.2s;
        }}
        select:focus, input[type="text"]:focus {{
            border-color: #38bdf8;
        }}

        /* Range Slider */
        .range-container {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        input[type="range"] {{
            flex: 1;
            accent-color: #38bdf8;
            height: 6px;
            background: #1e293b;
            border-radius: 3px;
        }}
        .range-val {{
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: #38bdf8;
            font-weight: 700;
            min-width: 45px;
            text-align: right;
        }}

        /* Top Hotspots List */
        .hotspot-item {{
            background: #0d1322;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 8px 10px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            flex-direction: column;
            gap: 3px;
        }}
        .hotspot-item:hover {{
            background: #182238;
            border-color: #38bdf8;
            transform: translateX(3px);
        }}
        .hotspot-title {{
            font-size: 0.8rem;
            font-weight: 700;
            color: #f8fafc;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .hotspot-sub {{
            font-size: 0.7rem;
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

        /* Slide-in Detail Drawer for Polling Place, Urnas & Demographics */
        #detailDrawer {{
            position: absolute;
            top: 20px;
            right: -520px;
            width: 480px;
            max-height: calc(100vh - 40px);
            background: rgba(15, 23, 42, 0.97);
            backdrop-filter: blur(14px);
            border: 1px solid #334155;
            border-radius: 16px;
            box-shadow: -10px 15px 40px rgba(0,0,0,0.7);
            z-index: 1200;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
            transition: right 0.35s cubic-bezier(0.16, 1, 0.3, 1);
            padding: 20px;
            gap: 12px;
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
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .detail-card-title {{
            font-size: 0.74rem;
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
            padding: 8px 12px;
            border-radius: 8px;
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

        .demo-bar-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.76rem;
            color: #cbd5e1;
            margin-bottom: 2px;
        }}
        .demo-bar-track {{
            width: 100%;
            height: 6px;
            background: #1f2937;
            border-radius: 3px;
            overflow: hidden;
            display: flex;
            margin-top: 2px;
            margin-bottom: 6px;
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
            gap: 6px;
            min-width: 280px;
            max-width: 320px;
        }}
        .popup-school {{
            font-size: 0.92rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.3;
        }}
        .popup-city {{
            font-size: 0.74rem;
            color: #94a3b8;
            margin-top: 1px;
        }}
        .popup-metric-row {{
            display: flex;
            justify-content: space-between;
            font-size: 0.78rem;
            padding: 2px 0;
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
            font-size: 0.78rem;
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

        /* Botão de Ajuda / Metodologia */
        .btn-help {{
            padding: 5px 10px;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            color: #38bdf8;
            font-size: 0.76rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
            white-space: nowrap;
        }}
        .btn-help:hover {{
            background: #0284c7;
            border-color: #38bdf8;
            color: #ffffff;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
        }}

        /* Modal Overlay & Card */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.78);
            backdrop-filter: blur(8px);
            z-index: 2000;
            display: none;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.25s ease;
        }}
        .modal-overlay.open {{
            display: flex;
            opacity: 1;
        }}
        .modal-content {{
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 16px;
            width: 92%;
            max-width: 740px;
            max-height: 86vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 25px 60px rgba(0,0,0,0.85);
            overflow: hidden;
            transform: scale(0.95);
            transition: transform 0.25s ease;
        }}
        .modal-overlay.open .modal-content {{
            transform: scale(1);
        }}
        .modal-header {{
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #0b0f19;
        }}
        .modal-header h2 {{
            font-size: 1.15rem;
            font-weight: 800;
            color: #f8fafc;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .modal-body {{
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            font-size: 0.84rem;
            line-height: 1.5;
            color: #cbd5e1;
        }}
        .modal-body::-webkit-scrollbar {{ width: 6px; }}
        .modal-body::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
        
        .guide-card {{
            background: #0b0f19;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .guide-card-title {{
            font-size: 0.88rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .modal-footer {{
            padding: 12px 20px;
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: flex-end;
            background: #0b0f19;
        }}

        /* Analytics Modal & Chart Styling */
        .modal-content-large {{
            max-width: 980px;
            width: 95%;
        }}
        .analytics-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
        }}
        @media (max-width: 860px) {{
            .analytics-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        .chart-box {{
            background: #0b0f19;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-height: 300px;
        }}
        .chart-box-title {{
            font-size: 0.82rem;
            font-weight: 800;
            color: #f8fafc;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
    </style>
</head>
<body>
    <div id="sidebar">
        <!-- Title Header Impactante c/ Botões de Gráficos e Ajuda -->
        <div class="title-container">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
                <div>
                    <h1>Bahia à Direita</h1>
                    <div class="title-subtitle">Mapeamento Eleitoral 2026</div>
                </div>
                <div style="display: flex; gap: 6px;">
                    <button id="btnOpenAnalytics" class="btn-help" style="background:#1e1b4b; border-color:#6366f1; color:#a5b4fc;" title="Gráficos de Correlação: Ensino Superior x Zonas Eleitorais">
                        <i class="fa-solid fa-chart-line"></i> Gráficos
                    </button>
                    <button id="btnOpenHelp" class="btn-help" title="Entenda todos os indicadores e a metodologia">
                        <i class="fa-solid fa-circle-question"></i> Guia
                    </button>
                </div>
            </div>
            <p class="subtitle">Análise geoespacial de urnas, votação presidencial, abstenção e perfil demográfico.</p>
        </div>

        <!-- KPIs Eleitorais & Abstenção -->
        <div>
            <div class="kpi-grid">
                <div class="kpi-card pl-glow">
                    <div class="kpi-title">Votos 22 (Flávio) <i class="fa-solid fa-flag" style="color:#60a5fa;"></i></div>
                    <div class="kpi-val blue" id="kpiVotos22">-</div>
                    <div class="kpi-sub" id="kpiPct22">- dos válidos</div>
                </div>
                <div class="kpi-card pt-glow">
                    <div class="kpi-title">Votos 13 (Lula) <i class="fa-solid fa-fire" style="color:#f87171;"></i></div>
                    <div class="kpi-val red" id="kpiVotos13">-</div>
                    <div class="kpi-sub" id="kpiPct13">- dos válidos</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">Abstenção Eleitoral <i class="fa-solid fa-user-xmark" style="color:#fb923c;"></i></div>
                    <div class="kpi-val orange" id="kpiPctAbs">-</div>
                    <div class="kpi-sub" id="kpiTotalAbs">- não votaram</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">Locais & Urnas <i class="fa-solid fa-school" style="color:#38bdf8;"></i></div>
                    <div class="kpi-val emerald" id="kpiLocais">-</div>
                    <div class="kpi-sub" id="kpiSecoes">- seções</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">Ensino Superior <i class="fa-solid fa-graduation-cap" style="color:#c084fc;"></i></div>
                    <div class="kpi-val purple" id="kpiPctSup">-</div>
                    <div class="kpi-sub" id="kpiTotalSup">- c/ Superior</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-title">Mulheres (Gênero) <i class="fa-solid fa-venus" style="color:#f472b6;"></i></div>
                    <div class="kpi-val pink" id="kpiPctFem">-</div>
                    <div class="kpi-sub" id="kpiTotalFem">- eleitoras</div>
                </div>
            </div>
        </div>

        <!-- Filtros de Exploração (Candidato e Município) -->
        <div class="control-panel">
            <div class="panel-header"><i class="fa-solid fa-sliders"></i> Filtros de Exploração</div>
            
            <div>
                <label><i class="fa-solid fa-user-check" style="color:#38bdf8;"></i> Filtrar por Candidato:</label>
                <select id="candidatoSelect">
                    <option value="all" selected>Todos os Candidatos (Votação Geral)</option>
                    <option value="22">🔵 Flávio Bolsonaro (22) - Vitória / Maioria</option>
                    <option value="13">🔴 Lula (13) - Vitória / Maioria</option>
                    <option value="pct22_30">🔵 Flávio Bolsonaro (22) &gt; 30% dos Votos</option>
                    <option value="pct22_40">🔵 Flávio Bolsonaro (22) &gt; 40% dos Votos</option>
                    <option value="pct13_30">🔴 Lula (13) &gt; 30% dos Votos</option>
                    <option value="pct13_40">🔴 Lula (13) &gt; 40% dos Votos</option>
                    <option value="pct13_50">🔴 Lula (13) &gt; 50% dos Votos</option>
                    <option value="pct13_70">🔴 Lula (13) &gt; 70% dos Votos</option>
                    <option value="outros_exp">⚪ Outros Candidatos / 3ª Via &gt; 8% dos Votos</option>
                    <option value="outros_top">⚪ Outros Candidatos / 3ª Via &gt; 10% dos Votos</option>
                    <option value="zero_22">🚫 Bolsonaro (22) = 0 Votos (Zerar Bolsonaro)</option>
                    <option value="zero_13">🚫 Lula (13) = 0 Votos (Zerar Lula)</option>
                    <option value="zero_outros">⚡ Polarização Pura (Outros = 0 Votos)</option>
                </select>
            </div>

            <div>
                <label><i class="fa-solid fa-city"></i> Município:</label>
                <select id="municipioSelect">
                    <option value="SALVADOR" selected>SALVADOR (Padrão)</option>
                    <option value="">Todos os 417 Municípios da Bahia</option>
                </select>
            </div>

            <div>
                <label><i class="fa-solid fa-landmark"></i> Zona Eleitoral:</label>
                <select id="zonaSelect">
                    <option value="">Todas as Zonas Eleitorais</option>
                </select>
            </div>

            <div>
                <label><i class="fa-solid fa-users-line"></i> Faixa Etária:</label>
                <select id="idadeFilter">
                    <option value="all" selected>Todas as Faixas Etárias (Geral)</option>
                    <option value="jovens">🧒 Jovens (16 a 24 anos)</option>
                    <option value="adultos">👔 Adultos Jovens (25 a 44 anos)</option>
                    <option value="maduros">💼 Meia-Idade / Maduros (45 a 59 anos)</option>
                    <option value="idosos">👴 Idosos (60+ anos)</option>
                </select>
            </div>

            <div>
                <label><i class="fa-solid fa-venus-mars"></i> Gênero Predominante:</label>
                <select id="generoFilter">
                    <option value="all" selected>Todos os Gêneros (Geral)</option>
                    <option value="fem">👩 Maioria Feminina (Mulheres)</option>
                    <option value="mas">👨 Maioria Masculina (Homens)</option>
                </select>
            </div>

            <div>
                <label><i class="fa-solid fa-graduation-cap"></i> Grau de Escolaridade (Ensino):</label>
                <select id="ensinoFilter">
                    <option value="all" selected>Todos os Níveis de Ensino (Geral)</option>
                    <option value="sup_alta">🎓 Ensino Superior - Alta Presença (&gt; 10%)</option>
                    <option value="sup_top">⭐ Polo Universitário / Classe Alta (&gt; 20%)</option>
                    <option value="medio">📚 Ensino Médio Predominante (&gt; 42%)</option>
                    <option value="fundamental">🏫 Ensino Fundamental Predominante (&gt; 30%)</option>
                    <option value="baixa">✏️ Baixa Escolaridade / Analfabeto (&gt; 28%)</option>
                </select>
            </div>

            <div>
                <label><i class="fa-solid fa-heart"></i> Estado Civil:</label>
                <select id="estadoCivilFilter">
                    <option value="all" selected>Todos os Estados Civis (Geral)</option>
                    <option value="solteiros">💍 Solteiros Predominantes (&gt; 70%)</option>
                    <option value="casados">👥 Casados / Famílias Tradicionais (&gt; 30%)</option>
                    <option value="divorciados">💔 Divorciados / Separados (&gt; 4%)</option>
                    <option value="viuvos">🕊️ Viúvos (&gt; 3%)</option>
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
            <div style="border-top: 1px solid var(--border-color); padding-top: 8px; margin-top: 2px;">
                <div class="panel-header" style="margin-bottom: 6px;"><i class="fa-solid fa-wand-magic-sparkles" style="color:#f59e0b;"></i> Calibração Térmica</div>
                
                <div style="margin-bottom: 6px;">
                    <label><i class="fa-solid fa-chart-line"></i> Escala de Comparação:</label>
                    <select id="scaleModeSelect">
                        <option value="relativo" selected>🎯 Relativa ao Filtro Atual (Recomendado)</option>
                        <option value="sqrt">⚡ Raiz Quadrada / Alta Sensibilidade</option>
                        <option value="global">🌐 Escala Global (Bahia Inteira)</option>
                    </select>
                </div>

                <div style="margin-bottom: 6px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <label style="margin: 0;"><i class="fa-solid fa-bolt" style="color:#38bdf8;"></i> Sensibilidade / Ganho Térmico:</label>
                        <span class="range-val" id="gainLabel">1.8x</span>
                    </div>
                    <div class="range-container" style="margin-top: 3px;">
                        <input type="range" id="gainSlider" min="0.5" max="4.0" step="0.1" value="1.8" />
                    </div>
                </div>

                <div style="margin-bottom: 6px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <label style="margin: 0;"><i class="fa-solid fa-circle-dot" style="color:#38bdf8;"></i> Raio de Dispersão:</label>
                        <span class="range-val" id="radiusLabel">15px</span>
                    </div>
                    <div class="range-container" style="margin-top: 3px;">
                        <input type="range" id="radiusSlider" min="15" max="80" value="15" />
                    </div>
                </div>

                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <label style="margin: 0;" id="minVotesTitle"><i class="fa-solid fa-filter-circle-dollar"></i> Mínimo de Votos:</label>
                        <span class="range-val" id="minVotesLabel">0</span>
                    </div>
                    <div class="range-container" style="margin-top: 3px;">
                        <input type="range" id="minVotesSlider" min="0" max="2500" step="50" value="0" />
                    </div>
                </div>
            </div>

            <button class="toggle-layer-btn active" id="toggleMarkersBtn" style="margin-top: 4px;">
                <span><i class="fa-solid fa-location-dot"></i> Exibir Marcadores / Colégios</span>
                <i class="fa-solid fa-eye" id="markersEyeIcon"></i>
            </button>
        </div>

        <!-- Seletor de Camada Heatmap (Eleitoral, Abstenção + Demográfico) -->
        <div class="control-panel">
            <div class="panel-header"><i class="fa-solid fa-layer-group"></i> Camada Ativa do Heatmap</div>
            <div class="mode-selector">
                <button class="mode-btn active" data-mode="votos22" id="btnMode22">
                    <span><i class="fa-solid fa-chart-column" style="color:#3b82f6; margin-right:4px;"></i> Votos no 22</span>
                    <i class="fa-solid fa-check"></i>
                </button>
                <button class="mode-btn" data-mode="pct22" id="btnModePct22">
                    <span><i class="fa-solid fa-percent" style="color:#60a5fa; margin-right:4px;"></i> % Direita (Flávio)</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="mode-btn" data-mode="votos13" id="btnMode13">
                    <span><i class="fa-solid fa-fire" style="color:#ef4444; margin-right:4px;"></i> Votos no 13</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="mode-btn" data-mode="pct13" id="btnModePct13">
                    <span><i class="fa-solid fa-percent" style="color:#f87171; margin-right:4px;"></i> % Esquerda (Lula)</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="mode-btn" data-mode="abstencao" id="btnModeAbs">
                    <span><i class="fa-solid fa-user-slash" style="color:#fb923c; margin-right:4px;"></i> Abstenção (%)</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="mode-btn" data-mode="demoSuperior" id="btnModeSup">
                    <span><i class="fa-solid fa-graduation-cap" style="color:#a855f7; margin-right:4px;"></i> Ensino Superior</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="mode-btn" data-mode="demoJovens" id="btnModeJov">
                    <span><i class="fa-solid fa-child-reaching" style="color:#38bdf8; margin-right:4px;"></i> Jovens (16-24a)</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="mode-btn" data-mode="demoAdultos" id="btnModeAdu">
                    <span><i class="fa-solid fa-user-tie" style="color:#06b6d4; margin-right:4px;"></i> Adultos (25-44a)</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="mode-btn" data-mode="demoMaduros" id="btnModeMad">
                    <span><i class="fa-solid fa-briefcase" style="color:#10b981; margin-right:4px;"></i> Maduros (45-59a)</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="mode-btn" data-mode="demoIdosos" id="btnModeIdo">
                    <span><i class="fa-solid fa-person-cane" style="color:#f59e0b; margin-right:4px;"></i> Idosos (60+a)</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="mode-btn" data-mode="demoFem" id="btnModeFem">
                    <span><i class="fa-solid fa-venus" style="color:#ec4899; margin-right:4px;"></i> Mulheres (%)</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
                <button class="mode-btn" data-mode="urnasUE2015" id="btnModeU15">
                    <span><i class="fa-solid fa-box-archive" style="color:#f59e0b; margin-right:4px;"></i> Urnas UE2015</span>
                    <i class="fa-solid fa-chevron-right"></i>
                </button>
            </div>
        </div>

        <!-- Top Hotspots por Candidato Selecionado -->
        <div class="control-panel">
            <div class="panel-header" id="hotspotsHeader"><i class="fa-solid fa-trophy" style="color:#3b82f6;"></i> Top Colégios - Bolsonaro (22)</div>
            <div id="hotspotsList" style="display: flex; flex-direction: column; gap: 6px;">
                <!-- Dinâmico via JS -->
            </div>
        </div>

        <div style="margin-top: auto; font-size: 0.72rem; color: #64748b; line-height: 1.5; padding-top: 10px; border-top: 1px solid var(--border-color); display: flex; flex-direction: column; gap: 4px;">
            <div><i class="fa-solid fa-shield-halved"></i> <strong>Fonte Oficial:</strong> Dados Abertos do TSE 2026 (Boletins de Urna, Comparecimento/Abstenção, Perfil Eleitorado e Correspondências).</div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px; padding-top: 4px; border-top: 1px dashed #1e293b;">
                <span style="color: #94a3b8;"><i class="fa-solid fa-code" style="color:#38bdf8;"></i> Desenvolvido por: <strong style="color: #f8fafc;">By Neville</strong></span>
                <a href="mailto:rodvillex@gmail.com" style="color: #38bdf8; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; font-weight: 600;" title="Enviar e-mail">
                    <i class="fa-solid fa-envelope"></i> rodvillex@gmail.com
                </a>
            </div>
        </div>
    </div>

    <div id="map-container">
        <div id="map"></div>
        
        <!-- Botão Flutuante de Ocultar / Exibir Painel Estatístico -->
        <button class="sidebar-toggle-btn" id="btnToggleSidebar" title="Ocultar ou Exibir Painel Lateral">
            <i class="fa-solid fa-bars" id="toggleSidebarIcon"></i>
            <span id="toggleSidebarText">Painel</span>
        </button>
        
        <!-- Legend Overlay -->
        <div class="map-legend">
            <div class="legend-title" id="legendTitle">Densidade Relativa de Votos (22)</div>
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
                <h2 id="drawerSchoolName" style="font-size: 1.2rem; font-weight: 800; line-height: 1.3;">-</h2>
                <p id="drawerAddress" style="font-size: 0.82rem; color: #94a3b8; margin-top: 4px;"><i class="fa-solid fa-location-dot"></i> -</p>
                <p id="drawerZones" style="font-size: 0.75rem; color: #64748b; margin-top: 2px;"><i class="fa-solid fa-landmark"></i> Zonas: -</p>
            </div>

            <!-- Modelos de Urna, Seções e Abstenção -->
            <div class="detail-card">
                <div class="detail-card-title"><i class="fa-solid fa-box-archive" style="color:#fbbf24;"></i> Urnas, Seções e Comparecimento</div>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px;">
                    <div style="background:#111827; padding:6px 8px; border-radius:8px; text-align:center;">
                        <div style="font-size:0.65rem; color:#94a3b8;">Seções</div>
                        <div id="drawerSecVal" style="font-size:1.05rem; font-weight:800; color:#ffffff; font-family:var(--font-mono);">0</div>
                    </div>
                    <div style="background:#111827; padding:6px 8px; border-radius:8px; text-align:center;">
                        <div style="font-size:0.65rem; color:#38bdf8;">Eleitores Aptos</div>
                        <div id="drawerAptVal" style="font-size:1.05rem; font-weight:800; color:#38bdf8; font-family:var(--font-mono);">0</div>
                    </div>
                    <div style="background:#111827; padding:6px 8px; border-radius:8px; text-align:center; border: 1px solid rgba(251, 146, 60, 0.3);">
                        <div style="font-size:0.65rem; color:#fb923c;">Abstenção</div>
                        <div id="drawerAbsVal" style="font-size:1.05rem; font-weight:800; color:#fb923c; font-family:var(--font-mono);">0%</div>
                    </div>
                    <div style="background:#111827; padding:6px 8px; border-radius:8px; text-align:center; border: 1px solid rgba(245, 158, 11, 0.3);">
                        <div style="font-size:0.65rem; color:#fbbf24;">Urnas UE2015</div>
                        <div id="drawerU15Val" style="font-size:1.05rem; font-weight:800; color:#fbbf24; font-family:var(--font-mono);">0</div>
                    </div>
                </div>
            </div>

            <!-- Placar de Votos Presidente -->
            <div class="detail-card">
                <div class="detail-card-title"><i class="fa-solid fa-chart-pie" style="color:#3b82f6;"></i> Votação para Presidente no Local</div>
                
                <div style="display: flex; flex-direction: column; gap: 6px;">
                    <div class="candidate-card bolsonaro">
                        <div>
                            <div style="font-size: 0.82rem; font-weight: 800; color: #60a5fa;"><i class="fa-solid fa-circle-check"></i> Bolsonaro (22) - PL</div>
                            <div style="font-size: 0.7rem; color: #94a3b8;">Votos válidos recebidos</div>
                        </div>
                        <div style="text-align: right;">
                            <div id="drawerV22Val" style="font-size: 1.1rem; font-weight: 800; color: #60a5fa; font-family: var(--font-mono);">0</div>
                            <div id="drawerP22Val" style="font-size: 0.74rem; font-weight: 700; color: #93c5fd;">0%</div>
                        </div>
                    </div>

                    <div class="candidate-card lula">
                        <div>
                            <div style="font-size: 0.82rem; font-weight: 800; color: #f87171;"><i class="fa-solid fa-circle-check"></i> Lula (13) - PT</div>
                            <div style="font-size: 0.7rem; color: #94a3b8;">Votos válidos recebidos</div>
                        </div>
                        <div style="text-align: right;">
                            <div id="drawerV13Val" style="font-size: 1.1rem; font-weight: 800; color: #f87171; font-family: var(--font-mono);">0</div>
                            <div id="drawerP13Val" style="font-size: 0.74rem; font-weight: 700; color: #fca5a5;">0%</div>
                        </div>
                    </div>

                    <div class="candidate-card" style="background:#111827;">
                        <div>
                            <div style="font-size: 0.82rem; font-weight: 700; color: #cbd5e1;"><i class="fa-solid fa-circle-minus"></i> Outros / Brancos / Nulos</div>
                            <div style="font-size: 0.7rem; color: #94a3b8;">Demais votos registrados</div>
                        </div>
                        <div style="text-align: right;">
                            <div id="drawerVoVal" style="font-size: 1.1rem; font-weight: 800; color: #cbd5e1; font-family: var(--font-mono);">0</div>
                            <div id="drawerPoVal" style="font-size: 0.74rem; font-weight: 700; color: #94a3b8;">0%</div>
                        </div>
                    </div>
                </div>

                <!-- Barra Visual -->
                <div style="margin-top: 2px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.72rem; font-weight:700; color:#94a3b8; margin-bottom:3px;">
                        <span>Total de Votos no Local:</span>
                        <span id="drawerVtVal" style="color:#ffffff; font-family:var(--font-mono);">0</span>
                    </div>
                    <div class="vote-bar-container" style="height: 8px;">
                        <div class="vote-bar-22" id="drawerBar22" style="width: 0%;"></div>
                        <div class="vote-bar-13" id="drawerBar13" style="width: 0%;"></div>
                        <div class="vote-bar-outros" id="drawerBarOutros" style="width: 0%;"></div>
                    </div>
                </div>
            </div>

            <!-- Perfil Demográfico do Colégio -->
            <div class="detail-card">
                <div class="detail-card-title"><i class="fa-solid fa-users" style="color:#a855f7;"></i> Perfil Demográfico do Eleitorado Local</div>
                
                <!-- Gênero -->
                <div>
                    <div class="demo-bar-row">
                        <span><i class="fa-solid fa-venus" style="color:#f472b6;"></i> Mulheres: <strong id="drawerFemVal">0%</strong></span>
                        <span><i class="fa-solid fa-mars" style="color:#60a5fa;"></i> Homens: <strong id="drawerMascVal">0%</strong></span>
                    </div>
                    <div class="demo-bar-track">
                        <div id="drawerBarFem" style="background:#ec4899; width:50%;"></div>
                        <div id="drawerBarMasc" style="background:#3b82f6; width:50%;"></div>
                    </div>
                </div>

                <!-- Faixa Etária -->
                <div style="margin-top: 4px;">
                    <div style="font-size:0.72rem; font-weight:700; color:#94a3b8; margin-bottom:3px;"><i class="fa-solid fa-cake-candles"></i> Faixa Etária:</div>
                    <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:4px; text-align:center; font-size:0.68rem;">
                        <div style="background:#111827; padding:4px; border-radius:6px;">
                            <div style="color:#38bdf8;">Jovens (16-24)</div>
                            <strong id="drawerJovVal" style="color:#fff;">0%</strong>
                        </div>
                        <div style="background:#111827; padding:4px; border-radius:6px;">
                            <div style="color:#34d399;">Adultos (25-44)</div>
                            <strong id="drawerAduVal" style="color:#fff;">0%</strong>
                        </div>
                        <div style="background:#111827; padding:4px; border-radius:6px;">
                            <div style="color:#fbbf24;">Maduros (45-59)</div>
                            <strong id="drawerMadVal" style="color:#fff;">0%</strong>
                        </div>
                        <div style="background:#111827; padding:4px; border-radius:6px;">
                            <div style="color:#f87171;">Idosos (60+)</div>
                            <strong id="drawerIdoVal" style="color:#fff;">0%</strong>
                        </div>
                    </div>
                </div>

                <!-- Escolaridade & Estado Civil -->
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:6px; margin-top:4px; font-size:0.72rem;">
                    <div style="background:#111827; padding:6px 8px; border-radius:8px;">
                        <div style="color:#c084fc; font-weight:700;"><i class="fa-solid fa-graduation-cap"></i> Ensino Superior:</div>
                        <div id="drawerSupVal" style="font-size:0.9rem; font-weight:800; color:#fff; font-family:var(--font-mono); margin-top:2px;">0%</div>
                    </div>
                    <div style="background:#111827; padding:6px 8px; border-radius:8px;">
                        <div style="color:#fbbf24; font-weight:700;"><i class="fa-solid fa-ring"></i> Solteiros:</div>
                        <div id="drawerSolVal" style="font-size:0.9rem; font-weight:800; color:#fff; font-family:var(--font-mono); margin-top:2px;">0%</div>
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

    <!-- Modal Guia dos Indicadores e Metodologia -->
    <div class="modal-overlay" id="helpModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fa-solid fa-circle-info" style="color: #38bdf8;"></i> Guia dos Indicadores & Metodologia</h2>
                <button class="drawer-close-btn" id="btnCloseHelp" title="Fechar"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="modal-body">
                <div class="guide-card" style="border-left: 4px solid #3b82f6;">
                    <div class="guide-title" style="color: #60a5fa;"><i class="fa-solid fa-chart-simple"></i> 1. Votos Absolutos vs. % Domínio (% Direita / % Esquerda)</div>
                    <p><strong>• Votos Absolutos (Votos 22 / Votos 13):</strong> Reflete o <em>tamanho do colégio eleitoral</em> e o volume bruto de votos. Um colégio gigante com 4.000 eleitores terá uma mancha térmica forte mesmo que o percentual seja moderado.</p>
                    <p><strong>• % Direita (Flávio) / % Esquerda (Lula):</strong> Mede a <em>taxa de conversão e preferência política</em> da comunidade local (% sobre os votos válidos). Um colégio com 300 eleitores onde a Direita fez 65% acende com intensidade máxima, revelando redutos de forte fidelidade ideológica.</p>
                </div>

                <div class="guide-card" style="border-left: 4px solid #c084fc;">
                    <div class="guide-title" style="color: #c084fc;"><i class="fa-solid fa-graduation-cap"></i> 2. Ensino Superior & Correlação Sociodemográfica</div>
                    <p>Métrica extraída do <strong>Perfil do Eleitorado Oficial do TSE</strong> (cadastro biométrico). Mostra a concentração de eleitores com formação superior completa/incompleta.</p>
                    <p style="color: #94a3b8; font-size: 0.78rem;"><em>💡 Nota de Análise:</em> Na Bahia e em Salvador, as áreas de maior concentração de ensino superior (bairros nobres e classe média) coincidem fortemente com as maiores votações de Flávio Bolsonaro (22).</p>
                </div>

                <div class="guide-card" style="border-left: 4px solid #fb923c;">
                    <div class="guide-title" style="color: #fb923c;"><i class="fa-solid fa-user-xmark"></i> 3. Abstenção Eleitoral (%)</div>
                    <p>Calculado como <code>(Eleitores Aptos - Votos Totais) / Eleitores Aptos</code>. Identifica a taxa de eleitores que não compareceram às urnas em cada colégio. Varia de 16% a mais de 35%, mapeando zonas de desmobilização cívica.</p>
                </div>

                <div class="guide-card" style="border-left: 4px solid #f59e0b;">
                    <div class="guide-title" style="color: #f59e0b;"><i class="fa-solid fa-box-archive"></i> 4. Modelos de Urna (UE2015 vs UE2020+)</div>
                    <p>Mapeia a distribuição logística das urnas eletrônicas fornecidas pelo TRE. Separa os modelos anteriores a 2020 (UE2015/UE2013/UE2009) dos modelos mais recentes com processadores atualizados (UE2020 e UE2022).</p>
                </div>

                <div class="guide-card" style="border-left: 4px solid #f472b6;">
                    <div class="guide-title" style="color: #f472b6;"><i class="fa-solid fa-venus"></i> 5. Mulheres / Gênero (%)</div>
                    <p>Percentual de eleitoras do gênero feminino cadastradas no colégio. Na Bahia, a maioria esmagadora das seções tem entre <strong>51% e 56%</strong> de mulheres, resultando em uma distribuição geográfica quase homogênea.</p>
                </div>

                <div class="guide-card" style="border-left: 4px solid #10b981;">
                    <div class="guide-title" style="color: #34d399;"><i class="fa-solid fa-sliders"></i> 6. Filtro de Candidatos & Dominância</div>
                    <p>Use o seletor <strong>Filtrar por Candidato</strong> para isolar seções onde um candidato obteve maioria dos votos válidos (vitória no colégio) ou atingiu patamares como ≥ 40%, ≥ 50% ou ≥ 70%.</p>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-action" id="btnModalOk" style="background: #0284c7; border-color: #38bdf8; padding: 8px 20px;"><i class="fa-solid fa-check"></i> Entendi</button>
            </div>
        </div>
    </div>

    <!-- Modal de Gráficos e Analytics (Ensino Superior x Zonas x Votos) -->
    <div class="modal-overlay" id="analyticsModal">
        <div class="modal-content modal-content-large">
            <div class="modal-header">
                <h2><i class="fa-solid fa-chart-line" style="color: #6366f1;"></i> Correlação: Ensino Superior vs. Votação por Zona</h2>
                <button class="drawer-close-btn" id="btnCloseAnalytics" title="Fechar"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div class="modal-body">
                <!-- Barra de Controle do Gráfico -->
                <div style="display: flex; justify-content: space-between; align-items: center; background: #0b0f19; padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border-color); flex-wrap: wrap; gap: 8px;">
                    <div style="font-size: 0.82rem; color: #94a3b8;">
                        <i class="fa-solid fa-filter" style="color:#38bdf8;"></i> Recorte Geográfico das Zonas:
                    </div>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn-action" id="btnScopeMun" style="background:#0284c7; border-color:#38bdf8; font-size:0.75rem; padding:6px 12px;"><i class="fa-solid fa-city"></i> Município Selecionado</button>
                        <button class="btn-action" id="btnScopeBahia" style="background:#1e293b; border-color:#334155; font-size:0.75rem; padding:6px 12px;"><i class="fa-solid fa-earth-americas"></i> Toda a Bahia</button>
                    </div>
                </div>

                <!-- Cards com Destaques Estatísticos -->
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                    <div class="guide-card" style="border-left: 4px solid #3b82f6;">
                        <div style="font-size:0.72rem; font-weight:700; color:#94a3b8;">Correlação c/ Direita (Flávio)</div>
                        <div id="statCorr22" style="font-size:1.1rem; font-weight:800; color:#60a5fa; font-family:var(--font-mono); margin-top:2px;">Forte Positiva (+)</div>
                        <div style="font-size:0.68rem; color:#64748b;">Mais escolaridade ➔ Mais votos no 22</div>
                    </div>
                    <div class="guide-card" style="border-left: 4px solid #ef4444;">
                        <div style="font-size:0.72rem; font-weight:700; color:#94a3b8;">Correlação c/ Esquerda (Lula)</div>
                        <div id="statCorr13" style="font-size:1.1rem; font-weight:800; color:#f87171; font-family:var(--font-mono); margin-top:2px;">Forte Negativa (-)</div>
                        <div style="font-size:0.68rem; color:#64748b;">Mais escolaridade ➔ Menos votos no 13</div>
                    </div>
                    <div class="guide-card" style="border-left: 4px solid #a855f7;">
                        <div style="font-size:0.72rem; font-weight:700; color:#94a3b8;">Zona Líder em Superior</div>
                        <div id="statTopSupZone" style="font-size:0.92rem; font-weight:800; color:#c084fc; margin-top:2px;">Zona 1</div>
                        <div id="statTopSupPct" style="font-size:0.68rem; color:#cbd5e1;">41.8% com Ensino Superior</div>
                    </div>
                </div>

                <!-- Grid com 2 Gráficos -->
                <div class="analytics-grid">
                    <!-- Gráfico 1: Scatter Plot -->
                    <div class="chart-box">
                        <div class="chart-box-title">
                            <span><i class="fa-solid fa-braille" style="color:#38bdf8;"></i> Dispersão: % Ensino Superior x % Votos</span>
                            <span style="font-size:0.7rem; color:#94a3b8; font-weight:normal;">Cada ponto = 1 Zona</span>
                        </div>
                        <div style="position: relative; flex: 1; min-height: 250px;">
                            <canvas id="scatterChartCanvas"></canvas>
                        </div>
                    </div>

                    <!-- Gráfico 2: Ranking por Zona -->
                    <div class="chart-box">
                        <div class="chart-box-title">
                            <span><i class="fa-solid fa-ranking-star" style="color:#a855f7;"></i> Votos por Zona (Ordenadas por % Superior)</span>
                            <span style="font-size:0.7rem; color:#94a3b8; font-weight:normal;">Maior % Superior ➔ Menor</span>
                        </div>
                        <div style="position: relative; flex: 1; min-height: 250px;">
                            <canvas id="rankingChartCanvas"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-action" id="btnAnalyticsOk" style="background: #0284c7; border-color: #38bdf8; padding: 8px 20px;"><i class="fa-solid fa-check"></i> Fechar Gráficos</button>
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

        // Inicializar Mapa centrado em Salvador (Padrão)
        const map = L.map('map', {{
            center: [-12.9714, -38.5014],
            zoom: 12,
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
        let currentMode = 'votos22'; // Padrão: Votos 22
        let showMarkers = true;
        let currentRadius = 15;
        let selectedItem = null;

        // Elementos DOM
        const candidatoSelect = document.getElementById('candidatoSelect');
        const munSelect = document.getElementById('municipioSelect');
        const zonaSelect = document.getElementById('zonaSelect');
        const idadeFilter = document.getElementById('idadeFilter');
        const generoFilter = document.getElementById('generoFilter');
        const ensinoFilter = document.getElementById('ensinoFilter');
        const estadoCivilFilter = document.getElementById('estadoCivilFilter');
        const urnaFilter = document.getElementById('urnaFilter');
        const searchInput = document.getElementById('searchInput');
        const scaleModeSelect = document.getElementById('scaleModeSelect');
        const gainSlider = document.getElementById('gainSlider');
        const gainLabel = document.getElementById('gainLabel');
        const radiusSlider = document.getElementById('radiusSlider');
        const radiusLabel = document.getElementById('radiusLabel');
        const minVotesSlider = document.getElementById('minVotesSlider');
        const minVotesLabel = document.getElementById('minVotesLabel');
        const minVotesTitle = document.getElementById('minVotesTitle');
        const toggleMarkersBtn = document.getElementById('toggleMarkersBtn');
        const markersEyeIcon = document.getElementById('markersEyeIcon');
        const legendTitle = document.getElementById('legendTitle');
        const legendBar = document.getElementById('legendBar');
        const hotspotsHeader = document.getElementById('hotspotsHeader');
        const hotspotsList = document.getElementById('hotspotsList');

        // Drawer DOM Elements
        const detailDrawer = document.getElementById('detailDrawer');
        const drawerCloseBtn = document.getElementById('drawerCloseBtn');
        const drawerSchoolName = document.getElementById('drawerSchoolName');
        const drawerAddress = document.getElementById('drawerAddress');
        const drawerZones = document.getElementById('drawerZones');
        const drawerSecVal = document.getElementById('drawerSecVal');
        const drawerAptVal = document.getElementById('drawerAptVal');
        const drawerAbsVal = document.getElementById('drawerAbsVal');
        const drawerU15Val = document.getElementById('drawerU15Val');
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
        
        // Demografia Drawer Elements
        const drawerFemVal = document.getElementById('drawerFemVal');
        const drawerMascVal = document.getElementById('drawerMascVal');
        const drawerBarFem = document.getElementById('drawerBarFem');
        const drawerBarMasc = document.getElementById('drawerBarMasc');
        const drawerJovVal = document.getElementById('drawerJovVal');
        const drawerAduVal = document.getElementById('drawerAduVal');
        const drawerMadVal = document.getElementById('drawerMadVal');
        const drawerIdoVal = document.getElementById('drawerIdoVal');
        const drawerSupVal = document.getElementById('drawerSupVal');
        const drawerSolVal = document.getElementById('drawerSolVal');

        const drawerCenterBtn = document.getElementById('drawerCenterBtn');
        const drawerGmapsBtn = document.getElementById('drawerGmapsBtn');

        // Preencher Dropdown de Municípios com Salvador pré-selecionado
        const municipios = [...new Set(rawData.map(d => d.m))].sort();
        munSelect.innerHTML = '<option value="SALVADOR" selected>SALVADOR (Padrão)</option><option value="">Todos os 417 Municípios da Bahia</option>';
        municipios.forEach(m => {{
            if (m !== 'SALVADOR') {{
                const opt = document.createElement('option');
                opt.value = m;
                opt.textContent = m;
                munSelect.appendChild(opt);
            }}
        }});

        // Preencher Dropdown de Zonas Eleitorais dinamicamente pelo Município selecionado
        function populateZonas() {{
            const selectedMun = munSelect.value.toLowerCase();
            const relevantData = selectedMun ? rawData.filter(d => d.m.toLowerCase() === selectedMun) : rawData;
            
            const allZones = new Set();
            relevantData.forEach(d => {{
                if (d.z) {{
                    d.z.split(',').forEach(z => {{
                        const cleanZ = z.trim();
                        if (cleanZ && !isNaN(cleanZ)) {{
                            allZones.add(parseInt(cleanZ, 10));
                        }}
                    }});
                }}
            }});
            
            const sortedZones = Array.from(allZones).sort((a, b) => a - b);
            const prevVal = zonaSelect.value;
            
            const countLabel = sortedZones.length > 0 ? ` (${{sortedZones.length}} zonas)` : '';
            zonaSelect.innerHTML = `<option value="">Todas as Zonas Eleitorais${{countLabel}}</option>`;
            
            sortedZones.forEach(z => {{
                const opt = document.createElement('option');
                opt.value = z.toString();
                opt.textContent = `Zona ${{z}}`;
                if (prevVal === z.toString()) {{
                    opt.selected = true;
                }}
                zonaSelect.appendChild(opt);
            }});
        }}

        // Gradiente Térmico Unificado (Azul para Vermelho) para Todos os Heatmaps
        const thermalBlueToRed = {{
            0.15: '#1e3a8a', // Azul Profundo (baixa concentração / frio)
            0.35: '#06b6d4', // Ciano
            0.55: '#10b981', // Verde Esmeralda
            0.75: '#fbbf24', // Amarelo
            0.90: '#f97316', // Laranja
            1.00: '#ef4444'  // Vermelho Vivo (alta concentração / calor máximo)
        }};

        const gradients = {{
            votos22: thermalBlueToRed,
            pct22: thermalBlueToRed,
            votos13: thermalBlueToRed,
            pct13: thermalBlueToRed,
            abstencao: thermalBlueToRed,
            demoSuperior: thermalBlueToRed,
            demoJovens: thermalBlueToRed,
            demoAdultos: thermalBlueToRed,
            demoMaduros: thermalBlueToRed,
            demoIdosos: thermalBlueToRed,
            demoFem: thermalBlueToRed,
            urnasUE2015: thermalBlueToRed
        }};

        // Função para Abrir Detalhes da Urna/Colégio
        function openItemDetails(d, flyTo = true) {{
            selectedItem = d;

            drawerSchoolName.textContent = d.l;
            drawerAddress.innerHTML = `<i class="fa-solid fa-location-dot"></i> ${{d.b ? d.b + ', ' : ''}}${{d.m}} &bull; ${{d.e || 'Endereço não informado'}}`;
            drawerZones.innerHTML = `<i class="fa-solid fa-landmark"></i> Zonas Eleitorais: <strong>${{d.z || 'N/A'}}</strong>`;
            
            drawerSecVal.textContent = d.sec;
            drawerAptVal.textContent = fmt(d.apt);
            drawerAbsVal.textContent = d.pabs + '% (' + fmt(d.abs) + ')';
            drawerU15Val.textContent = d.u15;

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

            // Dados Demográficos do Colégio
            const totalEleit = d.del > 0 ? d.del : (d.fem + d.mas);
            const pFem = totalEleit > 0 ? ((d.fem / totalEleit) * 100).toFixed(1) : '0.0';
            const pMasc = totalEleit > 0 ? ((d.mas / totalEleit) * 100).toFixed(1) : '0.0';
            const pJov = totalEleit > 0 ? ((d.jov / totalEleit) * 100).toFixed(1) : '0.0';
            const pAdu = totalEleit > 0 ? ((d.adu / totalEleit) * 100).toFixed(1) : '0.0';
            const pMad = totalEleit > 0 ? ((d.mad / totalEleit) * 100).toFixed(1) : '0.0';
            const pIdo = totalEleit > 0 ? ((d.ido / totalEleit) * 100).toFixed(1) : '0.0';
            const pSup = totalEleit > 0 ? ((d.sup / totalEleit) * 100).toFixed(1) : '0.0';
            const pSol = totalEleit > 0 ? ((d.sol / totalEleit) * 100).toFixed(1) : '0.0';

            drawerFemVal.textContent = pFem + '% (' + fmt(d.fem) + ')';
            drawerMascVal.textContent = pMasc + '% (' + fmt(d.mas) + ')';
            drawerBarFem.style.width = pFem + '%';
            drawerBarMasc.style.width = pMasc + '%';

            drawerJovVal.textContent = pJov + '%';
            drawerAduVal.textContent = pAdu + '%';
            drawerMadVal.textContent = pMad + '%';
            drawerIdoVal.textContent = pIdo + '%';

            drawerSupVal.textContent = pSup + '% (' + fmt(d.sup) + ')';
            drawerSolVal.textContent = pSol + '% (' + fmt(d.sol) + ')';

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
            const selectedCand = candidatoSelect.value;
            const selectedMun = munSelect.value.toLowerCase();
            const selectedZona = zonaSelect.value;
            const selectedUrna = urnaFilter.value;
            const searchVal = searchInput.value.toLowerCase().trim();
            const scaleMode = scaleModeSelect.value;
            const gain = parseFloat(gainSlider.value);
            const minVotes = parseInt(minVotesSlider.value);

            // Filtrar Dados (Efetivo)
            const filtered = rawData.filter(d => {{
                if (selectedMun && d.m.toLowerCase() !== selectedMun) return false;
                if (selectedZona) {{
                    const zonesList = (d.z || '').split(',').map(s => s.trim());
                    if (!zonesList.includes(selectedZona)) return false;
                }}
                if (selectedUrna === 'ue2015' && d.u15 === 0) return false;
                if (selectedUrna === 'ue2020' && d.u20 === 0) return false;
                
                // Filtro Efetivo por Candidato / Vitória / Limiares Reais
                if (selectedCand === '22' && d.v22 <= d.v13) return false;
                if (selectedCand === '13' && d.v13 <= d.v22) return false;
                if (selectedCand === 'pct22_30' && d.p22 < 30) return false;
                if (selectedCand === 'pct22_40' && d.p22 < 40) return false;
                if (selectedCand === 'pct13_30' && d.p13 < 30) return false;
                if (selectedCand === 'pct13_40' && d.p13 < 40) return false;
                if (selectedCand === 'pct13_50' && d.p13 < 50) return false;
                if (selectedCand === 'pct13_70' && d.p13 < 70) return false;

                const pOutros = d.vt > 0 ? (d.vo / d.vt) * 100 : 0;
                if (selectedCand === 'outros_exp' && pOutros < 8) return false;
                if (selectedCand === 'outros_top' && pOutros < 10) return false;
                if (selectedCand === 'zero_22' && d.v22 > 0) return false;
                if (selectedCand === 'zero_13' && d.v13 > 0) return false;
                if (selectedCand === 'zero_outros' && d.vo > 0) return false;

                // Filtro de Votos Mínimos
                if (minVotes > 0) {{
                    if (selectedCand.includes('22') && d.v22 < minVotes) return false;
                    if (selectedCand.includes('13') && d.v13 < minVotes) return false;
                    if (d.vt < minVotes) return false;
                }}

                // Filtro por Faixa Etária (filtra colégios e votos por perfil etário predominante)
                const selectedIdade = idadeFilter.value;
                if (selectedIdade !== 'all') {{
                    const totalEl = d.del > 0 ? d.del : (d.fem + d.mas);
                    if (totalEl > 0) {{
                        const pJov = d.jov / totalEl;
                        const pAdu = d.adu / totalEl;
                        const pMad = d.mad / totalEl;
                        const pIdo = d.ido / totalEl;

                        if (selectedIdade === 'jovens' && pJov < 0.15) return false;
                        if (selectedIdade === 'adultos' && pAdu < 0.40) return false;
                        if (selectedIdade === 'maduros' && pMad < 0.27) return false;
                        if (selectedIdade === 'idosos' && pIdo < 0.24) return false;
                    }}
                }}

                // Filtro por Gênero
                const selectedGenero = generoFilter.value;
                if (selectedGenero === 'fem' && d.fem <= d.mas) return false;
                if (selectedGenero === 'mas' && d.mas <= d.fem) return false;

                // Filtro por Grau de Escolaridade (Ensino)
                const selectedEnsino = ensinoFilter.value;
                if (selectedEnsino !== 'all') {{
                    const totalEl = d.del > 0 ? d.del : (d.fem + d.mas);
                    if (totalEl > 0) {{
                        const pSup = d.sup / totalEl;
                        const pMed = d.med / totalEl;
                        const pFun = d.fun / totalEl;
                        const pBax = d.bax / totalEl;

                        if (selectedEnsino === 'sup_alta' && pSup < 0.10) return false;
                        if (selectedEnsino === 'sup_top' && pSup < 0.20) return false;
                        if (selectedEnsino === 'medio' && pMed < 0.42) return false;
                        if (selectedEnsino === 'fundamental' && pFun < 0.30) return false;
                        if (selectedEnsino === 'baixa' && pBax < 0.28) return false;
                    }}
                }}

                // Filtro por Estado Civil
                const selectedCivil = estadoCivilFilter.value;
                if (selectedCivil !== 'all') {{
                    const totalEl = d.del > 0 ? d.del : (d.fem + d.mas);
                    if (totalEl > 0) {{
                        const pSol = d.sol / totalEl;
                        const pCas = d.cas / totalEl;
                        const pDiv = d.div / totalEl;
                        const pViu = d.viu / totalEl;

                        if (selectedCivil === 'solteiros' && pSol < 0.70) return false;
                        if (selectedCivil === 'casados' && pCas < 0.30) return false;
                        if (selectedCivil === 'divorciados' && pDiv < 0.04) return false;
                        if (selectedCivil === 'viuvos' && pViu < 0.03) return false;
                    }}
                }}

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
            const totalSec = filtered.reduce((acc, c) => acc + c.sec, 0);
            const totalApt = filtered.reduce((acc, c) => acc + c.apt, 0);
            const totalAbs = filtered.reduce((acc, c) => acc + c.abs, 0);
            
            const totalEleitRecorte = filtered.reduce((acc, c) => acc + (c.del > 0 ? c.del : (c.fem + c.mas)), 0);
            const totalFemRecorte = filtered.reduce((acc, c) => acc + c.fem, 0);
            const totalSupRecorte = filtered.reduce((acc, c) => acc + c.sup, 0);

            document.getElementById('kpiVotos13').textContent = fmt(totalV13);
            document.getElementById('kpiVotos22').textContent = fmt(totalV22);
            document.getElementById('kpiLocais').textContent = fmt(filtered.length);
            document.getElementById('kpiSecoes').textContent = fmt(totalSec) + ' seções';

            const pct13 = totalGeral > 0 ? ((totalV13 / totalGeral) * 100).toFixed(1) : '0.0';
            const pct22 = totalGeral > 0 ? ((totalV22 / totalGeral) * 100).toFixed(1) : '0.0';
            const pctAbs = totalApt > 0 ? ((totalAbs / totalApt) * 100).toFixed(1) : '0.0';

            document.getElementById('kpiPct13').textContent = pct13 + '% dos válidos';
            document.getElementById('kpiPct22').textContent = pct22 + '% dos válidos';
            document.getElementById('kpiPctAbs').textContent = pctAbs + '%';
            document.getElementById('kpiTotalAbs').textContent = fmt(totalAbs) + ' abstenções';

            const pctFem = totalEleitRecorte > 0 ? ((totalFemRecorte / totalEleitRecorte) * 100).toFixed(1) : '0.0';
            const pctSup = totalEleitRecorte > 0 ? ((totalSupRecorte / totalEleitRecorte) * 100).toFixed(1) : '0.0';

            document.getElementById('kpiPctFem').textContent = pctFem + '%';
            document.getElementById('kpiTotalFem').textContent = fmt(totalFemRecorte) + ' eleitoras';

            document.getElementById('kpiPctSup').textContent = pctSup + '%';
            document.getElementById('kpiTotalSup').textContent = fmt(totalSupRecorte) + ' c/ Superior';

            // Preparar Pontos do Heatmap com Normalização Relativa ao Filtro Aplicado
            const heatPoints = [];

            if (currentMode === 'votos22') {{
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
                legendTitle.textContent = "Densidade de Votos (22 - Bolsonaro)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
            }} else if (currentMode === 'pct22') {{
                filtered.forEach(d => {{
                    if (d.vt >= 20) {{
                        const norm = Math.pow(d.p22 / 100, 1.3);
                        const intensity = Math.min(1.0, norm * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "% Direita (Flávio Bolsonaro)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
            }} else if (currentMode === 'votos13') {{
                const vals = filtered.map(d => d.v13).filter(v => v > 0).sort((a, b) => a - b);
                const maxVal = vals.length > 0 ? vals[vals.length - 1] : 100;
                const p85 = vals.length > 0 ? vals[Math.floor(vals.length * 0.85)] : 100;
                const refBase = scaleMode === 'relativo' ? Math.max(p85, 80) : (scaleMode === 'global' ? 6000 : maxVal);

                filtered.forEach(d => {{
                    if (d.v13 > 0) {{
                        let norm = scaleMode === 'sqrt' ? Math.sqrt(d.v13 / maxVal) : Math.pow(d.v13 / refBase, 0.75);
                        const intensity = Math.min(1.0, norm * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Densidade de Votos (13 - Lula)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
            }} else if (currentMode === 'pct13') {{
                filtered.forEach(d => {{
                    if (d.vt >= 20) {{
                        const norm = Math.pow(d.p13 / 100, 1.3);
                        const intensity = Math.min(1.0, norm * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "% Esquerda (Lula / PT)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
            }} else if (currentMode === 'abstencao') {{
                filtered.forEach(d => {{
                    if (d.apt >= 50) {{
                        const norm = Math.pow(d.pabs / 40.0, 1.2);
                        const intensity = Math.min(1.0, norm * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Concentração de Abstenção Eleitoral (%)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
            }} else if (currentMode === 'demoSuperior') {{
                const vals = filtered.map(d => d.sup).filter(v => v > 0).sort((a, b) => a - b);
                const maxVal = vals.length > 0 ? vals[vals.length - 1] : 50;
                const p85 = vals.length > 0 ? vals[Math.floor(vals.length * 0.85)] : 50;
                filtered.forEach(d => {{
                    if (d.sup > 0) {{
                        const norm = Math.pow(d.sup / Math.max(p85, 20), 0.75);
                        const intensity = Math.min(1.0, norm * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Concentração de Ensino Superior (Classe Média/Alta)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
            }} else if (currentMode === 'demoJovens') {{
                const vals = filtered.map(d => d.jov).filter(v => v > 0).sort((a, b) => a - b);
                const maxVal = vals.length > 0 ? vals[vals.length - 1] : 50;
                const p85 = vals.length > 0 ? vals[Math.floor(vals.length * 0.85)] : 50;
                filtered.forEach(d => {{
                    if (d.jov > 0) {{
                        const norm = Math.pow(d.jov / Math.max(p85, 20), 0.75);
                        const intensity = Math.min(1.0, norm * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Concentração de Eleitorado Jovem (16 a 24 anos)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
            }} else if (currentMode === 'demoAdultos') {{
                const vals = filtered.map(d => d.adu).filter(v => v > 0).sort((a, b) => a - b);
                const maxVal = vals.length > 0 ? vals[vals.length - 1] : 100;
                const p85 = vals.length > 0 ? vals[Math.floor(vals.length * 0.85)] : 100;
                filtered.forEach(d => {{
                    if (d.adu > 0) {{
                        const norm = Math.pow(d.adu / Math.max(p85, 40), 0.75);
                        const intensity = Math.min(1.0, norm * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Concentração de Adultos Jovens (25 a 44 anos)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
            }} else if (currentMode === 'demoMaduros') {{
                const vals = filtered.map(d => d.mad).filter(v => v > 0).sort((a, b) => a - b);
                const maxVal = vals.length > 0 ? vals[vals.length - 1] : 50;
                const p85 = vals.length > 0 ? vals[Math.floor(vals.length * 0.85)] : 50;
                filtered.forEach(d => {{
                    if (d.mad > 0) {{
                        const norm = Math.pow(d.mad / Math.max(p85, 20), 0.75);
                        const intensity = Math.min(1.0, norm * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Concentração de Meia-Idade / Maduros (45 a 59 anos)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
            }} else if (currentMode === 'demoIdosos') {{
                const vals = filtered.map(d => d.ido).filter(v => v > 0).sort((a, b) => a - b);
                const maxVal = vals.length > 0 ? vals[vals.length - 1] : 50;
                const p85 = vals.length > 0 ? vals[Math.floor(vals.length * 0.85)] : 50;
                filtered.forEach(d => {{
                    if (d.ido > 0) {{
                        const norm = Math.pow(d.ido / Math.max(p85, 20), 0.75);
                        const intensity = Math.min(1.0, norm * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Concentração de Eleitorado Idoso (60+ anos)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
            }} else if (currentMode === 'demoFem') {{
                filtered.forEach(d => {{
                    const totalEl = d.del > 0 ? d.del : (d.fem + d.mas);
                    if (totalEl > 20) {{
                        const pFemLocal = d.fem / totalEl;
                        const intensity = Math.min(1.0, Math.pow(pFemLocal, 1.5) * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Densidade de Eleitorado Feminino (Mulheres)";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
            }} else if (currentMode === 'urnasUE2015') {{
                const maxU15 = Math.max(...filtered.map(d => d.u15), 1);
                filtered.forEach(d => {{
                    if (d.u15 > 0) {{
                        const intensity = Math.min(1.0, (d.u15 / maxU15) * gain);
                        heatPoints.push([d.lat, d.lng, intensity]);
                    }}
                }});
                legendTitle.textContent = "Concentração Relativa de Urnas UE2015";
                legendBar.style.background = "linear-gradient(to right, #1e3a8a, #06b6d4, #10b981, #fbbf24, #f97316, #ef4444)";
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
                gradient: gradients[currentMode] || gradients.votos22
            }}).addTo(map);

            // Renderizar Marcadores Cluster com evento de clique e Drawer
            markersCluster.clearLayers();
            if (showMarkers) {{
                const markerList = [];
                filtered.forEach(d => {{
                    let dotColor = '#f59e0b';
                    if (d.p22 > d.p13) {{
                        dotColor = '#3b82f6';
                    }} else if (d.p13 > d.p22) {{
                        dotColor = '#ef4444';
                    }}

                    const marker = L.circleMarker([d.lat, d.lng], {{
                        radius: 6,
                        fillColor: dotColor,
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
                            
                            <div style="background:#0f172a; padding:6px 10px; border-radius:8px; border:1px solid #1f293d; margin-top:3px;">
                                <div class="popup-metric-row">
                                    <span style="color:#94a3b8;">Aptos / Comparecimento:</span>
                                    <span style="font-weight:700;">${{fmt(d.apt)}} / ${{fmt(d.vt)}}</span>
                                </div>
                                <div class="popup-metric-row">
                                    <span style="color:#fb923c;">Abstenção: <strong>${{d.pabs}}%</strong></span>
                                    <span style="color:#fbbf24;">Urnas 15: <strong>${{d.u15}}</strong></span>
                                </div>
                            </div>

                            <div style="margin-top:2px;">
                                <div class="popup-metric-row">
                                    <span style="color:#60a5fa; font-weight:700;"><i class="fa-solid fa-square" style="color:#3b82f6;"></i> Bolsonaro (22):</span>
                                    <span style="font-weight:800; color:#60a5fa;">${{fmt(d.v22)}} (${{d.p22}}%)</span>
                                </div>
                                <div class="popup-metric-row">
                                    <span style="color:#f87171; font-weight:700;"><i class="fa-solid fa-square" style="color:#ef4444;"></i> Lula (13):</span>
                                    <span style="font-weight:800; color:#f87171;">${{fmt(d.v13)}} (${{d.p13}}%)</span>
                                </div>

                                <div class="vote-bar-container">
                                    <div class="vote-bar-22" style="width: ${{d.p22}}%;"></div>
                                    <div class="vote-bar-13" style="width: ${{d.p13}}%;"></div>
                                    <div class="vote-bar-outros" style="width: ${{Math.max(0, 100 - d.p13 - d.p22)}}%;"></div>
                                </div>
                            </div>

                            <button onclick="window.openItemDrawerFromPopup('${{d.lat}}', '${{d.lng}}')" style="margin-top:6px; padding:6px 10px; background:#0284c7; border:none; border-radius:6px; color:#fff; font-size:0.74rem; font-weight:700; cursor:pointer; width:100%; display:flex; align-items:center; justify-content:center; gap:6px;">
                                <i class="fa-solid fa-folder-open"></i> Ver Detalhes e Demografia
                            </button>
                        </div>
                    `;
                    marker.bindPopup(popupContent);
                    
                    marker.on('click', () => {{
                        openItemDetails(d, false);
                    }});

                    markerList.push(marker);
                }});
                markersCluster.addLayers(markerList);
            }}

            // Atualizar Top Hotspots de acordo com o candidato selecionado
            renderHotspotsList(filtered);

            // Ajustar visualização se filtrar município ou zona
            if ((selectedZona || selectedMun) && filtered.length > 0) {{
                const group = new L.featureGroup(filtered.map(d => L.marker([d.lat, d.lng])));
                map.fitBounds(group.getBounds().pad(0.08));
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
            
            let closest = null;
            let minDist = 999999;

            rawData.forEach(d => {{
                const dist = Math.hypot(d.lat - clickLat, d.lng - clickLng);
                if (dist < minDist) {{
                    minDist = dist;
                    closest = d;
                }}
            }});

            if (closest && minDist < 0.04) {{
                openItemDetails(closest, true);
            }}
        }});

        // Renderizar Lista dos Top Colégios por Candidato Selecionado
        function renderHotspotsList(filtered) {{
            hotspotsList.innerHTML = '';
            const selectedCand = candidatoSelect.value;
            let sorted = [...filtered];
            let candColor = '#38bdf8';

            if (selectedCand === '22' || selectedCand.startsWith('pct22')) {{
                sorted.sort((a, b) => b.v22 - a.v22);
                candColor = '#60a5fa';
                hotspotsHeader.innerHTML = `<i class="fa-solid fa-trophy" style="color:#3b82f6;"></i> Top Colégios - Bolsonaro (22)`;
            }} else if (selectedCand === '13' || selectedCand.startsWith('pct13')) {{
                sorted.sort((a, b) => b.v13 - a.v13);
                candColor = '#f87171';
                hotspotsHeader.innerHTML = `<i class="fa-solid fa-trophy" style="color:#ef4444;"></i> Top Colégios - Lula (13)`;
            }} else {{
                sorted.sort((a, b) => b.vt - a.vt);
                candColor = '#38bdf8';
                hotspotsHeader.innerHTML = `<i class="fa-solid fa-trophy" style="color:#38bdf8;"></i> Top Colégios do Filtro (Votos)`;
            }}

            const top6 = sorted.slice(0, 6);
            
            top6.forEach((d, idx) => {{
                let valToShow = d.vt;
                let pctToShow = '100';
                if (selectedCand === '22' || selectedCand.startsWith('pct22')) {{
                    valToShow = d.v22;
                    pctToShow = d.p22;
                }} else if (selectedCand === '13' || selectedCand.startsWith('pct13')) {{
                    valToShow = d.v13;
                    pctToShow = d.p13;
                }}

                const item = document.createElement('div');
                item.className = 'hotspot-item';
                item.innerHTML = `
                    <div class="hotspot-title">#${{idx + 1}} ${{d.l}}</div>
                    <div class="hotspot-sub">
                        <span><i class="fa-solid fa-location-dot"></i> ${{d.b ? d.b + ', ' : ''}}${{d.m}}</span>
                        <span style="color:${{candColor}}; font-weight:700;">${{fmt(valToShow)}} votos (${{pctToShow}}%)</span>
                    </div>
                `;
                item.addEventListener('click', () => {{
                    openItemDetails(d, true);
                }});
                hotspotsList.appendChild(item);
            }});
        }}

        // Eventos dos Controles
        candidatoSelect.addEventListener('change', () => {{
            const val = candidatoSelect.value;
            if (val === '22' || val.startsWith('pct22') || val === 'zero_13') {{
                currentMode = 'votos22';
            }} else if (val === '13' || val.startsWith('pct13') || val === 'zero_22') {{
                currentMode = 'votos13';
            }}
            
            // Atualizar botões de modo do Heatmap
            document.querySelectorAll('.mode-btn').forEach(b => {{
                if (b.dataset.mode === currentMode) {{
                    b.classList.add('active');
                    const icon = b.querySelector('.fa-chevron-right, .fa-check');
                    if (icon) icon.className = 'fa-solid fa-check';
                }} else {{
                    b.classList.remove('active');
                    const icon = b.querySelector('.fa-check, .fa-chevron-right');
                    if (icon) icon.className = 'fa-solid fa-chevron-right';
                }}
            }});
            updateDashboard();
        }});

        // Seletor de Modo de Heatmap
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

        munSelect.addEventListener('change', () => {{
            populateZonas();
            zonaSelect.value = '';
            if (!munSelect.value) {{
                map.flyTo([-12.9714, -41.5000], 7, {{ duration: 1.2 }});
            }}
            updateDashboard();
        }});
        zonaSelect.addEventListener('change', updateDashboard);
        idadeFilter.addEventListener('change', updateDashboard);
        generoFilter.addEventListener('change', updateDashboard);
        ensinoFilter.addEventListener('change', updateDashboard);
        estadoCivilFilter.addEventListener('change', updateDashboard);
        urnaFilter.addEventListener('change', updateDashboard);
        searchInput.addEventListener('input', updateDashboard);

        // Controle do Modal de Ajuda / Metodologia
        const helpModal = document.getElementById('helpModal');
        const btnOpenHelp = document.getElementById('btnOpenHelp');
        const btnCloseHelp = document.getElementById('btnCloseHelp');
        const btnModalOk = document.getElementById('btnModalOk');

        function openModal() {{
            helpModal.classList.add('open');
        }}
        function closeModal() {{
            helpModal.classList.remove('open');
        }}

        btnOpenHelp.addEventListener('click', openModal);
        btnCloseHelp.addEventListener('click', closeModal);
        btnModalOk.addEventListener('click', closeModal);

        helpModal.addEventListener('click', (e) => {{
            if (e.target === helpModal) {{
                closeModal();
            }}
        }});

        window.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape' && helpModal.classList.contains('open')) {{
                closeModal();
            }}
        }});

        // Controle de Ocultar / Exibir Barra Lateral (Painel Estatístico)
        const btnToggleSidebar = document.getElementById('btnToggleSidebar');
        const sidebar = document.getElementById('sidebar');
        const toggleSidebarIcon = document.getElementById('toggleSidebarIcon');
        const toggleSidebarText = document.getElementById('toggleSidebarText');

        btnToggleSidebar.addEventListener('click', () => {{
            sidebar.classList.toggle('collapsed');
            const isCollapsed = sidebar.classList.contains('collapsed');
            if (isCollapsed) {{
                toggleSidebarIcon.className = 'fa-solid fa-chart-simple';
                toggleSidebarText.textContent = 'Exibir Painel';
                btnToggleSidebar.title = 'Exibir Painel Estatístico';
            }} else {{
                toggleSidebarIcon.className = 'fa-solid fa-bars';
                toggleSidebarText.textContent = 'Painel';
                btnToggleSidebar.title = 'Ocultar Painel Estatístico';
            }}
            setTimeout(() => {{
                map.invalidateSize();
            }}, 360);
        }});

        // ==========================================
        // MÓDULO DE ANALYTICS & GRÁFICOS (CHART.JS)
        // ==========================================
        const analyticsModal = document.getElementById('analyticsModal');
        const btnOpenAnalytics = document.getElementById('btnOpenAnalytics');
        const btnCloseAnalytics = document.getElementById('btnCloseAnalytics');
        const btnAnalyticsOk = document.getElementById('btnAnalyticsOk');
        const btnScopeMun = document.getElementById('btnScopeMun');
        const btnScopeBahia = document.getElementById('btnScopeBahia');

        let scatterChartInst = null;
        let rankingChartInst = null;
        let chartScopeMunOnly = true;

        function getZoneAnalytics(scopeMunOnly = true) {{
            const selectedMun = munSelect.value.toLowerCase();
            const relevantData = (scopeMunOnly && selectedMun) ? rawData.filter(d => d.m.toLowerCase() === selectedMun) : rawData;
            
            const zonesMap = {{}};
            relevantData.forEach(d => {{
                if (!d.z) return;
                const zList = d.z.split(',').map(s => s.trim()).filter(s => s && !isNaN(s));
                zList.forEach(zStr => {{
                    const z = parseInt(zStr, 10);
                    if (!zonesMap[z]) {{
                        zonesMap[z] = {{
                            zona: z,
                            v13: 0,
                            v22: 0,
                            vt: 0,
                            sup: 0,
                            del: 0,
                            mun: d.m
                        }};
                    }}
                    zonesMap[z].v13 += (d.v13 / zList.length);
                    zonesMap[z].v22 += (d.v22 / zList.length);
                    zonesMap[z].vt += (d.vt / zList.length);
                    zonesMap[z].sup += (d.sup / zList.length);
                    const totalEl = d.del > 0 ? d.del : (d.fem + d.mas);
                    zonesMap[z].del += (totalEl / zList.length);
                }});
            }});

            const zoneList = Object.values(zonesMap).map(z => {{
                const p13 = z.vt > 0 ? (z.v13 / z.vt) * 100 : 0;
                const p22 = z.vt > 0 ? (z.v22 / z.vt) * 100 : 0;
                const pSup = z.del > 0 ? (z.sup / z.del) * 100 : 0;
                return {{
                    zona: z.zona,
                    label: `Zona ${{z.zona}} (${{z.mun}})`,
                    p13: parseFloat(p13.toFixed(1)),
                    p22: parseFloat(p22.toFixed(1)),
                    pSup: parseFloat(pSup.toFixed(1)),
                    vt: Math.round(z.vt),
                    v22: Math.round(z.v22),
                    v13: Math.round(z.v13),
                    sup: Math.round(z.sup),
                    mun: z.mun
                }};
            }});

            return zoneList;
        }}

        function renderAnalyticsCharts() {{
            const data = getZoneAnalytics(chartScopeMunOnly);
            if (!data || data.length === 0) return;

            // Ordenar para Ranking (Maior % Superior ➔ Menor)
            const sortedBySup = [...data].sort((a, b) => b.pSup - a.pSup);
            const topSup = sortedBySup[0];

            document.getElementById('statTopSupZone').textContent = topSup ? `Zona ${{topSup.zona}} (${{topSup.mun}})` : '-';
            document.getElementById('statTopSupPct').textContent = topSup ? `${{topSup.pSup}}% c/ Ensino Superior` : '-';

            // 1. Gráfico de Dispersão (Scatter Plot)
            const scatterCtx = document.getElementById('scatterChartCanvas').getContext('2d');
            if (scatterChartInst) {{
                scatterChartInst.destroy();
            }}

            const scatter22Data = data.map(d => ({{ x: d.pSup, y: d.p22, zona: d.zona, mun: d.mun }}));
            const scatter13Data = data.map(d => ({{ x: d.pSup, y: d.p13, zona: d.zona, mun: d.mun }}));

            scatterChartInst = new Chart(scatterCtx, {{
                type: 'scatter',
                data: {{
                    datasets: [
                        {{
                            label: '🔵 Flávio Bolsonaro (22)',
                            data: scatter22Data,
                            backgroundColor: '#3b82f6',
                            borderColor: '#60a5fa',
                            pointRadius: 7,
                            pointHoverRadius: 10
                        }},
                        {{
                            label: '🔴 Lula (13)',
                            data: scatter13Data,
                            backgroundColor: '#ef4444',
                            borderColor: '#f87171',
                            pointRadius: 7,
                            pointHoverRadius: 10
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            title: {{ display: true, text: '% Eleitores com Ensino Superior na Zona', color: '#94a3b8' }},
                            grid: {{ color: '#1e293b' }},
                            ticks: {{ color: '#cbd5e1', callback: v => v + '%' }}
                        }},
                        y: {{
                            title: {{ display: true, text: '% Votos Válidos do Candidato', color: '#94a3b8' }},
                            grid: {{ color: '#1e293b' }},
                            ticks: {{ color: '#cbd5e1', callback: v => v + '%' }},
                            min: 0,
                            max: 100
                        }}
                    }},
                    plugins: {{
                        legend: {{ labels: {{ color: '#f8fafc', font: {{ family: 'Outfit', weight: 'bold' }} }} }},
                        tooltip: {{
                            callbacks: {{
                                label: ctx => {{
                                    const p = ctx.raw;
                                    return `Zona ${{p.zona}} (${{p.mun}}): ${{p.x}}% Sup ➔ ${{p.y}}% Votos`;
                                }}
                            }}
                        }}
                    }}
                }}
            }});

            // 2. Gráfico de Ranking de Zonas (Barras Divergentes)
            const rankingCtx = document.getElementById('rankingChartCanvas').getContext('2d');
            if (rankingChartInst) {{
                rankingChartInst.destroy();
            }}

            const topSlice = sortedBySup.slice(0, 19);
            const labels = topSlice.map(d => `Z${{d.zona}} (${{d.pSup}}% Sup)`);
            const p22Vals = topSlice.map(d => d.p22);
            const p13Vals = topSlice.map(d => d.p13);

            rankingChartInst = new Chart(rankingCtx, {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [
                        {{
                            label: '% Direita (22)',
                            data: p22Vals,
                            backgroundColor: '#3b82f6',
                            borderRadius: 4
                        }},
                        {{
                            label: '% Esquerda (13)',
                            data: p13Vals,
                            backgroundColor: '#ef4444',
                            borderRadius: 4
                        }}
                    ]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            stacked: false,
                            grid: {{ color: '#1e293b' }},
                            ticks: {{ color: '#cbd5e1', callback: v => v + '%' }},
                            max: 100
                        }},
                        y: {{
                            grid: {{ color: '#1e293b' }},
                            ticks: {{ color: '#cbd5e1', font: {{ size: 10 }} }}
                        }}
                    }},
                    plugins: {{
                        legend: {{ labels: {{ color: '#f8fafc', font: {{ family: 'Outfit', weight: 'bold' }} }} }}
                    }}
                }}
            }});
        }}

        function openAnalyticsModal() {{
            analyticsModal.classList.add('open');
            setTimeout(() => {{
                renderAnalyticsCharts();
            }}, 150);
        }}
        function closeAnalyticsModal() {{
            analyticsModal.classList.remove('open');
        }}

        btnOpenAnalytics.addEventListener('click', openAnalyticsModal);
        btnCloseAnalytics.addEventListener('click', closeAnalyticsModal);
        btnAnalyticsOk.addEventListener('click', closeAnalyticsModal);

        btnScopeMun.addEventListener('click', () => {{
            chartScopeMunOnly = true;
            btnScopeMun.style.background = '#0284c7';
            btnScopeMun.style.borderColor = '#38bdf8';
            btnScopeBahia.style.background = '#1e293b';
            btnScopeBahia.style.borderColor = '#334155';
            renderAnalyticsCharts();
        }});

        btnScopeBahia.addEventListener('click', () => {{
            chartScopeMunOnly = false;
            btnScopeBahia.style.background = '#0284c7';
            btnScopeBahia.style.borderColor = '#38bdf8';
            btnScopeMun.style.background = '#1e293b';
            btnScopeMun.style.borderColor = '#334155';
            renderAnalyticsCharts();
        }});

        analyticsModal.addEventListener('click', (e) => {{
            if (e.target === analyticsModal) {{
                closeAnalyticsModal();
            }}
        }});

        window.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape' && analyticsModal.classList.contains('open')) {{
                closeAnalyticsModal();
            }}
        }});

        // Renderização Inicial com foco em Salvador e suas Zonas
        populateZonas();
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
