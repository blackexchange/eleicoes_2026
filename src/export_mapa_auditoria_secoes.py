"""
Script de Geração do Mapa Interativo de Auditoria de Seções Eleitorais (Bahia 2026).
Visualização granular de biometria, liberação manual por mesário, votos pós-17h e Score de Anomalia.
Gera data/processed/google_maps/mapa_auditoria_secoes_BA.html e docs/mapa_auditoria_secoes_BA.html.
"""

import json
import os
import shutil
import duckdb
import pandas as pd


def export_mapa_auditoria_secoes():
    print("=== INICIANDO GERAÇÃO DO MAPA DE AUDITORIA DE SEÇÕES (BAHIA 2026) ===")
    output_dir = "data/processed/google_maps"
    os.makedirs(output_dir, exist_ok=True)
    docs_dir = "docs"
    os.makedirs(docs_dir, exist_ok=True)

    db_path = "data/processed/eleicoes.duckdb"
    if not os.path.exists(db_path):
        print(f"Erro: Banco de dados {db_path} não encontrado.")
        return

    con = duckdb.connect(db_path)

    # 1. Carregar contorno da Bahia
    bahia_geojson_str = "{}"
    geo_path = "data/geo/bahia_boundary.geojson"
    if os.path.exists(geo_path):
        with open(geo_path, "r", encoding="utf-8") as f:
            bahia_geojson_str = f.read()

    # 2. Consultar todas as seções auditadas e agrupar por local de votação
    print("[1/3] Extraindo 35.472 seções auditadas e consolidando por local de votação...")
    rows = con.execute("""
        SELECT 
            MUNICIPIO, LOCAL_VOTACAO, ENDERECO, BAIRRO, LATITUDE, LONGITUDE,
            ZONA, SECAO, MODELO_URNA, APTOS, COMPARECIMENTO, PCT_ABSTENCAO,
            PCT_MANUAL, QTD_MANUAL, VOTOS_POS_17H, VOTOS_POS_17H_MANUAL,
            PRIMEIRO_VOTO, ULTIMO_VOTO, VOTOS_13, VOTOS_22, PCT_VOTOS_13, PCT_VOTOS_22,
            SCORE_ANOMALIA, NIVEL_RISCO, VOTOS_POR_MINUTO, TEMPO_MEDIO_SEG,
            FLAG_BAIXA_ABSTENCAO, FLAG_ALTA_LIBERACAO_MANUAL, FLAG_VOTOS_POS_17H,
            VOTOS_VALIDOS, TOTAL_VOTOS,
            SECOES_AGREGADAS, IS_AGREGADA, DIF_MANUAL_LOCAL, MEDIA_MANUAL_LOCAL,
            PCT_POS_17H_MANUAL, FLAG_DESVIO_ESCOLA, FLAG_POS_17H_MANUAL_ALTO
        FROM auditoria_secoes_BA_2026
        ORDER BY SCORE_ANOMALIA DESC, PCT_MANUAL DESC, VOTOS_POS_17H DESC
    """).fetchall()

    locais_dict = {}
    for r in rows:
        mun = r[0]
        loc = r[1]
        lat = round(float(r[4]), 5) if r[4] is not None else 0.0
        lng = round(float(r[5]), 5) if r[5] is not None else 0.0
        loc_key = (mun, loc, lat, lng)

        if loc_key not in locais_dict:
            locais_dict[loc_key] = {
                "m": mun,
                "l": loc,
                "e": r[2] or "",
                "b": r[3] or "",
                "lat": lat,
                "lng": lng,
                "sc": int(r[22]),
                "risk": r[23],
                "s": []
            }
        
        # Se uma seção posterior tiver score maior, atualiza o max score do local
        if int(r[22]) > locais_dict[loc_key]["sc"]:
            locais_dict[loc_key]["sc"] = int(r[22])
            locais_dict[loc_key]["risk"] = r[23]

        # Compact array representation for each section
        # 0: zona, 1: secao, 2: modelo_urna, 3: aptos, 4: comparecimento, 5: pct_abstencao,
        # 6: pct_manual, 7: qtd_manual, 8: votos_pos_17h, 9: votos_pos_17h_manual,
        # 10: primeiro_voto, 11: ultimo_voto, 12: votos_13, 13: votos_22,
        # 14: pct_votos_13, 15: pct_votos_22, 16: score_anomalia, 17: nivel_risco,
        # 18: votos_por_minuto, 19: tempo_medio_seg, 20: f_abs, 21: f_man, 22: f_p17,
        # 23: votos_validos, 24: total_votos,
        # 25: secoes_agregadas, 26: is_agregada, 27: dif_manual_local, 28: media_manual_local,
        # 29: pct_pos_17h_manual, 30: f_desvio_escola, 31: f_pos17_manual_alto
        locais_dict[loc_key]["s"].append([
            int(r[6]), int(r[7]), str(r[8]), int(r[9]), int(r[10]),
            float(r[11]), float(r[12]), int(r[13]), int(r[14]), int(r[15]),
            str(r[16] or ""), str(r[17] or ""), int(r[18]), int(r[19]),
            float(r[20]), float(r[21]), int(r[22]), str(r[23]),
            float(r[24] or 0.0), float(r[25] or 0.0),
            int(r[26]), int(r[27]), int(r[28]),
            int(r[29] or 0), int(r[30] or 0),
            str(r[31] or ""), int(r[32] or 0), float(r[33] or 0.0), float(r[34] or 0.0),
            float(r[35] or 0.0), int(r[36] or 0), int(r[37] or 0)
        ])

    data_locais = list(locais_dict.values())
    data_json = json.dumps(data_locais, ensure_ascii=False)
    print(f"[OK] Total locais agrupados: {len(data_locais)} | Seções totais: {len(rows)}")

    # 3. Estatísticas globais do cabeçalho
    stats = {
        "total_secoes": len(rows),
        "total_locais": len(data_locais),
        "total_votantes": int(sum(r[10] for r in rows)),
        "media_pct_manual": round(float(sum(r[12] for r in rows) / len(rows)), 2),
        "total_pos_17h": int(sum(r[14] for r in rows)),
        "total_pos_17h_man": int(sum(r[15] for r in rows)),
        "secoes_critico": int(sum(1 for r in rows if r[22] >= 70)),
        "secoes_alto": int(sum(1 for r in rows if 50 <= r[22] < 70)),
        "secoes_medio": int(sum(1 for r in rows if 35 <= r[22] < 50)),
        "secoes_trifeta": int(sum(1 for r in rows if r[26] == 1 and r[27] == 1 and r[28] == 1)),
        "secoes_agregadas": int(sum(1 for r in rows if r[32] == 1)),
        "secoes_desvio_escola": int(sum(1 for r in rows if r[36] == 1))
    }
    stats_json = json.dumps(stats, ensure_ascii=False)

    # 4. Construir HTML da Aplicação
    print("[2/3] Renderizando aplicação interativa Leaflet + Heatmap + Painel de Auditoria...")
    html_content = build_html(data_json, stats_json, bahia_geojson_str)

    # 5. Salvar arquivos
    mapa_output = os.path.join(output_dir, "mapa_auditoria_secoes_BA.html")
    with open(mapa_output, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Mapa gerado em: {mapa_output}")

    docs_output = os.path.join(docs_dir, "mapa_auditoria_secoes_BA.html")
    with open(docs_output, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Mapa gerado em docs: {docs_output}")

    # Copia CSV consolidado para docs se não existir
    csv_src = os.path.join(output_dir, "auditoria_secoes_anomalias_BA_2026.csv")
    csv_dst = os.path.join(docs_dir, "auditoria_secoes_anomalias_BA_2026.csv")
    if os.path.exists(csv_src) and not os.path.exists(csv_dst):
        shutil.copy(csv_src, csv_dst)

    print("[3/3] Finalizado com sucesso!")


def build_html(data_json, stats_json, bahia_geojson_str):
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentinela Juris • Inteligência Forense e Auditoria de Urnas 2026</title>
    <!-- Leaflet & MarkerCluster CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.min.css" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.Default.min.css" />
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
    <style>
        :root {{
            --bg-main: #080c14;
            --bg-card: #111827;
            --bg-card-hover: #1f293d;
            --border-color: #1e293b;
            --border-highlight: #334155;
            --accent-red: #ef4444;
            --accent-orange: #f97316;
            --accent-amber: #f59e0b;
            --accent-blue: #3b82f6;
            --accent-sky: #38bdf8;
            --accent-emerald: #10b981;
            --accent-purple: #a855f7;
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

        /* Top Floating Navigation Bar */
        .top-navbar {{
            position: absolute;
            top: 14px;
            left: 20px;
            right: 20px;
            z-index: 1050;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(15, 23, 42, 0.92);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(51, 65, 85, 0.8);
            border-radius: 12px;
            padding: 8px 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            pointer-events: auto;
        }}
        .top-navbar-left {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .nav-brand {{
            font-size: 0.95rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            display: flex;
            align-items: center;
            gap: 8px;
            color: #fff;
        }}
        .nav-brand span {{
            color: #f59e0b;
            font-weight: 900;
        }}
        .nav-badge-pill {{
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.5);
            font-size: 0.68rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 20px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }}
        .nav-badge-pill.orange {{
            background: rgba(245, 158, 11, 0.2);
            color: #fde047;
            border-color: rgba(245, 158, 11, 0.5);
        }}
        .top-navbar-right {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .nav-btn {{
            background: #1e293b;
            border: 1px solid #334155;
            color: #f8fafc;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            text-decoration: none;
            transition: all 0.2s ease;
        }}
        .nav-btn:hover {{
            background: #334155;
            border-color: #38bdf8;
            color: #fff;
            transform: translateY(-1px);
        }}
        .nav-btn.primary {{
            background: linear-gradient(135deg, #0284c7, #2563eb);
            border-color: #38bdf8;
        }}
        .nav-btn.primary:hover {{
            background: linear-gradient(135deg, #0369a1, #1d4ed8);
        }}
        .nav-btn.danger {{
            background: rgba(239, 68, 68, 0.2);
            border-color: #ef4444;
            color: #fca5a5;
        }}

        /* Sidebar Styling */
        #sidebar {{
            width: 440px;
            min-width: 440px;
            background: var(--bg-card);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            padding: 70px 18px 18px 18px;
            box-shadow: 6px 0 30px rgba(0,0,0,0.6);
            z-index: 1000;
            overflow-y: auto;
            position: relative;
            transition: margin-left 0.35s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease;
            gap: 12px;
        }}
        #sidebar.collapsed {{
            margin-left: -440px;
            pointer-events: none;
            opacity: 0;
        }}
        #sidebar::-webkit-scrollbar {{ width: 6px; }}
        #sidebar::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}

        /* Map Container */
        #map-container {{
            flex: 1;
            height: 100%;
            position: relative;
        }}
        #map {{ width: 100%; height: 100%; background: #080c14; }}

        /* Sidebar Toggle Button */
        .sidebar-toggle-btn {{
            position: absolute;
            top: 76px;
            left: 20px;
            z-index: 1040;
            background: rgba(15, 23, 42, 0.94);
            backdrop-filter: blur(10px);
            border: 1px solid #334155;
            color: #f8fafc;
            height: 36px;
            padding: 0 12px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-size: 0.76rem;
            font-weight: 700;
            box-shadow: 0 6px 20px rgba(0,0,0,0.6);
            transition: all 0.2s ease;
        }}
        .sidebar-toggle-btn:hover {{
            background: #0284c7;
            border-color: #38bdf8;
            color: #fff;
        }}

        /* Filter Section Styles */
        .filter-group {{
            background: #0b0f19;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .filter-label {{
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .filter-input, .filter-select {{
            width: 100%;
            background: #151d30;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: #fff;
            padding: 7px 10px;
            font-size: 0.78rem;
            outline: none;
            transition: border-color 0.2s;
        }}
        .filter-input:focus, .filter-select:focus {{
            border-color: var(--accent-sky);
        }}

        /* KPI Grid in Sidebar */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }}
        .kpi-card {{
            background: #0b0f19;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px;
            display: flex;
            flex-direction: column;
        }}
        .kpi-title {{
            font-size: 0.68rem;
            font-weight: 700;
            color: var(--text-muted);
        }}
        .kpi-value {{
            font-size: 1.15rem;
            font-weight: 800;
            font-family: var(--font-mono);
            margin-top: 2px;
            color: #fff;
        }}
        .kpi-sub {{
            font-size: 0.65rem;
            color: #64748b;
            margin-top: 2px;
        }}

        /* Ranking List in Sidebar */
        .ranking-header {{
            font-size: 0.78rem;
            font-weight: 800;
            color: #f8fafc;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 4px;
        }}
        .ranking-container {{
            flex: 1;
            min-height: 280px;
            max-height: 480px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: #0b0f19;
            display: flex;
            flex-direction: column;
        }}
        .ranking-container::-webkit-scrollbar {{ width: 5px; }}
        .ranking-container::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
        
        .ranking-item {{
            padding: 9px 12px;
            border-bottom: 1px solid rgba(30, 41, 59, 0.8);
            cursor: pointer;
            transition: background 0.15s;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
        }}
        .ranking-item:hover {{
            background: rgba(56, 189, 248, 0.08);
        }}
        .rank-pos {{
            font-family: var(--font-mono);
            font-size: 0.72rem;
            font-weight: 800;
            color: var(--text-muted);
            min-width: 24px;
        }}
        .rank-info {{
            flex: 1;
            overflow: hidden;
        }}
        .rank-title {{
            font-size: 0.76rem;
            font-weight: 700;
            color: #fff;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .rank-sub {{
            font-size: 0.68rem;
            color: var(--text-muted);
            margin-top: 1px;
            display: flex;
            gap: 6px;
        }}
        .rank-score {{
            font-family: var(--font-mono);
            font-weight: 900;
            font-size: 0.78rem;
            padding: 2px 7px;
            border-radius: 4px;
            white-space: nowrap;
        }}

        /* Anomaly Badges */
        .badge-critico {{
            background: rgba(239, 68, 68, 0.25);
            color: #fca5a5;
            border: 1px solid #ef4444;
        }}
        .badge-alto {{
            background: rgba(249, 115, 22, 0.25);
            color: #fdba74;
            border: 1px solid #f97316;
        }}
        .badge-medio {{
            background: rgba(245, 158, 11, 0.25);
            color: #fde047;
            border: 1px solid #f59e0b;
        }}
        .badge-normal {{
            background: rgba(59, 130, 246, 0.2);
            color: #93c5fd;
            border: 1px solid #3b82f6;
        }}

        /* Sliding Detail Drawer */
        #detailDrawer {{
            position: absolute;
            top: 76px;
            right: 20px;
            width: 440px;
            max-height: calc(100vh - 96px);
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(14px);
            border: 1px solid rgba(51, 65, 85, 0.9);
            border-radius: 14px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.8);
            z-index: 1060;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transform: translateX(480px);
            transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        #detailDrawer.open {{
            transform: translateX(0);
        }}
        .drawer-header {{
            padding: 14px 18px;
            border-bottom: 1px solid var(--border-color);
            background: #0b0f19;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}
        .drawer-body {{
            padding: 16px 18px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .drawer-body::-webkit-scrollbar {{ width: 5px; }}
        .drawer-body::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
        .drawer-close-btn {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.1rem;
            cursor: pointer;
            padding: 4px;
        }}
        .drawer-close-btn:hover {{ color: #fff; }}

        /* Section Tabs in Drawer */
        .section-tabs-bar {{
            display: flex;
            gap: 6px;
            overflow-x: auto;
            padding-bottom: 4px;
            margin-bottom: 6px;
        }}
        .section-tab-btn {{
            background: #1e293b;
            border: 1px solid #334155;
            color: #cbd5e1;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.74rem;
            font-weight: 700;
            font-family: var(--font-mono);
            cursor: pointer;
            white-space: nowrap;
        }}
        .section-tab-btn.active {{
            background: #0284c7;
            border-color: #38bdf8;
            color: #fff;
        }}

        /* Score Thermometer in Drawer */
        .score-box {{
            background: #0b0f19;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .score-bar-bg {{
            height: 10px;
            background: #1e293b;
            border-radius: 5px;
            overflow: hidden;
            display: flex;
        }}
        .score-bar-fill {{
            height: 100%;
            border-radius: 5px;
            transition: width 0.4s ease;
        }}

        /* Marker Icons on Map */
        .marker-pin {{
            width: 32px;
            height: 32px;
            border-radius: 50% 50% 50% 0;
            background: #3b82f6;
            position: absolute;
            transform: rotate(-45deg);
            left: 50%;
            top: 50%;
            margin: -20px 0 0 -20px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 14px rgba(0,0,0,0.6);
            border: 2px solid #fff;
        }}
        .marker-pin span {{
            transform: rotate(45deg);
            font-size: 0.72rem;
            font-weight: 900;
            font-family: var(--font-mono);
            color: #fff;
        }}
        .marker-critico {{
            background: #ef4444 !important;
            animation: pulse-red 1.8s infinite;
        }}
        .marker-alto {{
            background: #f97316 !important;
        }}
        .marker-medio {{
            background: #f59e0b !important;
        }}
        .marker-normal {{
            background: #3b82f6 !important;
        }}

        @keyframes pulse-red {{
            0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.8); }}
            70% {{ box-shadow: 0 0 0 16px rgba(239, 68, 68, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
        }}

        /* Modal Metodologia */
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
        }}
        .modal-overlay.open {{ display: flex; }}
        .modal-card {{
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 14px;
            width: 90%;
            max-width: 640px;
            max-height: 85vh;
            overflow-y: auto;
            padding: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.8);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
    </style>
</head>
<body>

    <!-- Top Floating Navbar -->
    <div class="top-navbar">
        <div class="top-navbar-left">
            <div class="nav-brand">
                <i class="fa-solid fa-scale-balanced" style="color: #f59e0b;"></i>
                Sentinela Juris • <span>Inteligência Forense Eleitoral</span>
            </div>
            <div class="nav-badge-pill">
                <i class="fa-solid fa-triangle-exclamation"></i> Auditoria Pericial de Urnas
            </div>
            <div class="nav-badge-pill orange">
                <i class="fa-solid fa-shield-halved"></i> Instrução Probatória 2026
            </div>
        </div>
        <div class="top-navbar-right">
            <button class="nav-btn danger" id="btnDownloadFilteredCSV" title="Exportar o recorte pericial filtrado para importar no Google Meus Mapas">
                <i class="fa-solid fa-file-csv"></i> <span id="lblDownloadBtn">Baixar CSV Google Maps</span>
            </button>
            <a href="index.html" class="nav-btn primary">
                <i class="fa-solid fa-layer-group"></i> Painel Geral de Colégios
            </a>
            <a href="auditoria_secoes_anomalias_BA_2026.csv" download class="nav-btn" title="Baixar base pericial completa com todas as 35.472 seções para instrução probatória">
                <i class="fa-solid fa-database"></i> Base Pericial Completa
            </a>
            <button class="nav-btn" id="btnHelp">
                <i class="fa-solid fa-scale-balanced"></i> Metodologia &amp; Instrução Probatória
            </button>
        </div>
    </div>

    <!-- Toggle Sidebar Button -->
    <button class="sidebar-toggle-btn" id="btnToggleSidebar">
        <i class="fa-solid fa-sliders"></i> Painel de Filtros &amp; Ranking
    </button>

    <!-- Sidebar Lateral -->
    <div id="sidebar">
        <!-- Controles de Filtros -->
        <div class="filter-group">
            <div class="filter-label">
                <span><i class="fa-solid fa-city" style="color:#38bdf8;"></i> Município</span>
                <span id="labelTotalMun" style="color:#64748b; font-size:0.65rem;">417 municípios</span>
            </div>
            <select id="selectMunicipio" class="filter-select">
                <option value="">Toda a Bahia (Todos os Municípios)</option>
            </select>

            <div class="filter-label">
                <span><i class="fa-solid fa-landmark" style="color:#a855f7;"></i> Zona Eleitoral</span>
            </div>
            <select id="selectZona" class="filter-select">
                <option value="">Todas as Zonas do Município</option>
            </select>

            <div class="filter-label">
                <span><i class="fa-solid fa-filter" style="color:#f59e0b;"></i> Filtro de Anomalia</span>
            </div>
            <select id="selectAnomalia" class="filter-select">
                <option value="all">Todas as Seções Auditadas</option>
                <option value="critico">🔴 Risco Crítico (Score ≥ 70)</option>
                <option value="alto_plus">🚨 Risco Alto ou Crítico (Score ≥ 50)</option>
                <option value="desvio_escola">🏫 Desvio Intra-Colégio (≥ +25% vs outras salas)</option>
                <option value="pos_17h_manual">🌙 Pós-17h c/ Liberação Manual Concentrada</option>
                <option value="trifeta">⚠️ Trifeta: Baixa Abs + Alta Manual + Pós-17h</option>
                <option value="alta_manual">✋ Alta Liberação Manual Mesário (≥ 20%)</option>
                <option value="pos_17h">🌙 Votos Pós-17h (≥ 15 votos computados)</option>
                <option value="baixa_abs">📉 Baixa Abstenção Atípica (≤ 10% de aptos)</option>
                <option value="agregada">📦 Urnas com Seções Agregadas</option>
                <option value="ue2015">📟 Urnas Antigas &lt; UE2020 (UE2015/13/11)</option>
                <option value="ue2020">🖥️ Urnas UE2020+</option>
            </select>

            <div class="filter-label">
                <span>Score Mínimo: <strong id="lblScoreMin" style="color:#f59e0b; font-family:var(--font-mono);">0</strong></span>
            </div>
            <input type="range" id="rangeScoreMin" min="0" max="95" step="5" value="0" style="width: 100%; accent-color: #f59e0b; cursor: pointer;" />
        </div>

        <!-- Camadas do Mapa & Heatmap -->
        <div class="filter-group">
            <div class="filter-label">
                <span><i class="fa-solid fa-layer-group" style="color:#10b981;"></i> Camadas &amp; Heatmap</span>
            </div>
            <div style="display: flex; gap: 14px; font-size: 0.74rem;">
                <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                    <input type="checkbox" id="chkMarkers" checked style="accent-color:#0284c7;" /> Marcadores
                </label>
                <label style="display: flex; align-items: center; gap: 6px; cursor: pointer;">
                    <input type="checkbox" id="chkHeatmap" checked style="accent-color:#ef4444;" /> Heatmap
                </label>
            </div>
            <div class="filter-label" style="margin-top: 4px;">
                <span>Modo de Calor (Heatmap)</span>
            </div>
            <select id="selectHeatMode" class="filter-select">
                <option value="score">🎯 Score de Anomalia Operacional</option>
                <option value="manual">✋ % Liberação Manual pelo Mesário</option>
                <option value="pos17">🌙 Volume de Votos Computados Pós-17h</option>
                <option value="comparecimento">📉 Super-Comparecimento (Abstenção ≤ 10%)</option>
                <option value="voto13">🔴 Votos Lula (13)</option>
                <option value="voto22">🔵 Votos Bolsonaro (22)</option>
            </select>
        </div>

        <!-- KPIs Dinâmicos do Recorte Atual -->
        <div class="kpi-grid">
            <div class="kpi-card" style="border-left: 3px solid #38bdf8;">
                <div class="kpi-title">Locais / Seções</div>
                <div class="kpi-value" id="kpiSecCount">-</div>
                <div class="kpi-sub" id="kpiVotantesCount">- votantes</div>
            </div>
            <div class="kpi-card" style="border-left: 3px solid #f59e0b;">
                <div class="kpi-title">Média Lib. Manual</div>
                <div class="kpi-value" id="kpiMediaManual">-</div>
                <div class="kpi-sub">mesário s/ biometria</div>
            </div>
            <div class="kpi-card" style="border-left: 3px solid #c084fc;">
                <div class="kpi-title">Votos Pós-17h</div>
                <div class="kpi-value" id="kpiPos17Count">-</div>
                <div class="kpi-sub" id="kpiPos17ManCount">- manuais</div>
            </div>
            <div class="kpi-card" style="border-left: 3px solid #ef4444;">
                <div class="kpi-title">Placar Presidencial</div>
                <div class="kpi-value" id="kpiPlacar" style="font-size:0.95rem;">-</div>
                <div class="kpi-sub">Lula vs Bolsonaro</div>
            </div>
        </div>

        <!-- Ranking das Top Seções Mais Suspeitas -->
        <div class="ranking-header">
            <span><i class="fa-solid fa-ranking-star" style="color:#f59e0b;"></i> Top Seções c/ Maior Anomalia</span>
            <span id="rankCount" style="font-size:0.68rem; color:#64748b; font-family:var(--font-mono);">50 seções</span>
        </div>
        <div class="ranking-container" id="rankingList">
            <!-- Populado via JS -->
        </div>
    </div>

    <!-- Map Canvas -->
    <div id="map-container">
        <div id="map"></div>
    </div>

    <!-- Sliding Detail Drawer -->
    <div id="detailDrawer">
        <div class="drawer-header">
            <div>
                <div id="drawerLocalTitle" style="font-weight: 800; font-size: 0.95rem; color: #fff;">-</div>
                <div id="drawerLocalSub" style="font-size: 0.72rem; color: var(--text-muted); margin-top: 2px;">-</div>
            </div>
            <button class="drawer-close-btn" id="btnCloseDrawer" title="Fechar"><i class="fa-solid fa-xmark"></i></button>
        </div>
        <div class="drawer-body">
            <!-- Abas de Seções deste Local -->
            <div class="filter-label">Seções no Local de Votação:</div>
            <div class="section-tabs-bar" id="drawerSectionTabs">
                <!-- Abas inseridas via JS -->
            </div>

            <!-- Banner de Seção Agregada -->
            <div id="detAgregadaBanner" style="display:none; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 8px; padding: 8px 10px; font-size: 0.72rem; color: #93c5fd; margin-bottom: 8px;">
                <i class="fa-solid fa-layer-group" style="color: #60a5fa;"></i> <strong>Urna com Seções Agregadas:</strong> <span id="detAgregadaText"></span>
            </div>

            <!-- Box do Score de Anomalia -->
            <div class="score-box" id="drawerScoreBox">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.76rem; font-weight: 700; color: #94a3b8;">Score de Anomalia Operacional</span>
                    <span id="drawerScoreBadge" class="rank-score badge-critico">95 pts</span>
                </div>
                <div class="score-bar-bg">
                    <div id="drawerScoreFill" class="score-bar-fill" style="width: 95%; background: #ef4444;"></div>
                </div>
                <div id="drawerScoreDesc" style="font-size: 0.72rem; color: #cbd5e1; line-height: 1.4;">
                    <!-- Justificativa calculada -->
                </div>
            </div>

            <!-- Informações Operacionais da Seção -->
            <div style="background: #0b0f19; border: 1px solid var(--border-color); border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 8px;">
                <div style="font-size: 0.74rem; font-weight: 800; color: #f8fafc; display: flex; align-items: center; gap: 6px;">
                    <i class="fa-solid fa-microchip" style="color:#38bdf8;"></i> Dados da Urna e Fluxo de Votação
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.74rem;">
                    <div>Modelo Urna: <strong id="detUrna" style="color:#f59e0b;">-</strong></div>
                    <div>Abstenção: <strong id="detAbs" style="color:#f87171;">-</strong></div>
                    <div>Primeiro Voto: <strong id="detT1" style="color:#fff;">-</strong></div>
                    <div>Último Voto: <strong id="detT2" style="color:#fff;">-</strong></div>
                    <div style="grid-column: span 2;">Comparecimento: <strong id="detComp" style="color:#fff;">-</strong></div>
                    <div style="grid-column: span 2;">Ritmo de Fluxo: <strong id="detVpm" style="color:#38bdf8;">-</strong></div>
                </div>
            </div>

            <!-- Biometria vs Liberação Manual -->
            <div style="background: #0b0f19; border: 1px solid var(--border-color); border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 8px;">
                <div style="font-size: 0.74rem; font-weight: 800; color: #f8fafc; display: flex; align-items: center; gap: 6px;">
                    <i class="fa-solid fa-fingerprint" style="color:#f59e0b;"></i> Habilitação: Biometria vs Mesário
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: #94a3b8;">
                    <span>Biometria: <strong id="detBio" style="color:#10b981;">-</strong></span>
                    <span>Manual Mesário: <strong id="detMan" style="color:#ef4444;">-</strong></span>
                </div>
                <div class="score-bar-bg" style="height: 8px;">
                    <div id="detBioBar" style="background:#10b981; width:70%; height:100%;"></div>
                    <div id="detManBar" style="background:#ef4444; width:30%; height:100%;"></div>
                </div>
                <div style="font-size: 0.7rem; color: #94a3b8; display: flex; justify-content: space-between; border-top: 1px dashed rgba(51, 65, 85, 0.6); padding-top: 6px;" id="detDesvioEscolaRow">
                    <span>Desvio no Colégio:</span>
                    <strong id="detDesvioEscolaVal" style="color:#f59e0b;">-</strong>
                </div>
                <div style="font-size: 0.7rem; color: #94a3b8;" id="detPos17Txt">
                    Votos computados após 17:00:00: <strong id="detPos17Val" style="color:#c084fc;">-</strong>
                </div>
            </div>

            <!-- Votação Nominal para Presidente -->
            <div style="background: #0b0f19; border: 1px solid var(--border-color); border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 8px;">
                <div style="font-size: 0.74rem; font-weight: 800; color: #f8fafc; display: flex; align-items: center; gap: 6px;">
                    <i class="fa-solid fa-check-to-slot" style="color:#a855f7;"></i> Votação Presidencial na Seção
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.72rem;">
                    <span style="color:#f87171; font-weight:700;">Lula 13: <strong id="detV13">-</strong> (<span id="detP13">-%</span>)</span>
                    <span style="color:#60a5fa; font-weight:700;">Bolsonaro 22: <strong id="detV22">-</strong> (<span id="detP22">-%</span>)</span>
                </div>
                <div class="score-bar-bg" style="height: 10px;">
                    <div id="detV13Bar" style="background:#ef4444; width:50%; height:100%;"></div>
                    <div id="detV22Bar" style="background:#3b82f6; width:50%; height:100%;"></div>
                </div>
            </div>

            <!-- Botão Ver no Google Maps Externo -->
            <a id="btnGoogleMapsExt" href="#" target="_blank" class="nav-btn primary" style="justify-content: center; margin-top: 4px;">
                <i class="fa-solid fa-arrow-up-right-from-square"></i> Abrir Local no Google Maps
            </a>
        </div>
    </div>

    <!-- Modal Metodologia -->
    <div class="modal-overlay" id="modalMetodologia">
        <div class="modal-card">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 8px;">
                <h3 style="font-size: 1.05rem; font-weight: 800; color: #fff;"><i class="fa-solid fa-scale-balanced" style="color:#f59e0b;"></i> Sentinela Juris • Metodologia Forense &amp; Instrução Probatória</h3>
                <button class="drawer-close-btn" id="btnCloseHelp"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <div style="font-size: 0.78rem; color: #cbd5e1; line-height: 1.5; display: flex; flex-direction: column; gap: 10px;">
                <p>O <strong>Sentinela Juris</strong> estrutura a auditoria de cada urna através do <strong>Score de Anomalia Forense (0 a 100 pontos)</strong>, consolidado a partir dos registros oficiais de máquina (<code>logd.dat</code>, RDV, BU) e cadastro de aptos do TSE para fins de análise pericial e sustentação probatória.</p>
                <div style="background:#0b0f19; padding:10px; border-radius:8px; border-left:3px solid #ef4444;">
                    <strong>1. Abstenção Atípica Consolidada (Até 25 pts)</strong><br>
                    Calculada sobre a <em>capacidade real consolidada</em> da urna (incluindo eleitores de seções agregadas). Seções com abstenção real ≤ 5% ou ≤ 10% recebem pontuação por estarem muito distantes da média estadual (~20%).
                </div>
                <div style="background:#0b0f19; padding:10px; border-radius:8px; border-left:3px solid #f59e0b;">
                    <strong>2. Liberação Manual pelo Mesário sem Biometria (Até 25 pts)</strong><br>
                    A média estadual da Bahia é de 12% de votos manuais. Seções onde 25%, 35% ou mais de 50% dos eleitores foram liberados pelo mesário recebem pontuação elevada.
                </div>
                <div style="background:#0b0f19; padding:10px; border-radius:8px; border-left:3px solid #ec4899;">
                    <strong>3. Desvio Intra-Colégio / Sala Destoante (Até 25 pts)</strong><br>
                    Compara a taxa manual da urna contra a média das outras salas do <em>mesmo colégio eleitoral</em>. Se uma sala apresenta +20%, +30% ou +50% de liberações manuais que suas vizinhas no mesmo prédio, indica forte anomalia de conduta daquela mesa receptora.
                </div>
                <div style="background:#0b0f19; padding:10px; border-radius:8px; border-left:3px solid #a855f7;">
                    <strong>4. Votação Pós-17h com Liberação Manual Concentrada (Até 15 pts)</strong><br>
                    Contabiliza eleitores atendidos após as 17h e afere se houve concentração desproporcional de liberações manuais (≥ 70% sem biometria) na prorrogação da fila.
                </div>
                <div style="background:#0b0f19; padding:10px; border-radius:8px; border-left:3px solid #3b82f6;">
                    <strong>5. Polarização Extrema de Votação (Até 10 pts)</strong><br>
                    Seções onde um candidato atinge mais de 80%, 90% ou 95% dos votos válidos.
                </div>
                <div style="background:#0b0f19; padding:10px; border-radius:8px; border-left:3px solid #06b6d4; font-size: 0.72rem;">
                    <strong>ℹ️ Nota Técnica: Seções Agregadas &amp; Ritmo de Votação (VPM)</strong><br>
                    • <strong>Seções Agregadas:</strong> O TSE junta até 3 ou 4 seções na mesma urna física. O sistema consolida todos os aptos federais, eliminando falsos alarmes de "super-comparecimento".<br>
                    • <strong>Votos por Minuto (VPM):</strong> A média da Bahia é de <strong>0,45 vpm</strong> (1 voto a cada 2m13s). O máximo registrado em todo o estado foi de 1,00 vpm (60s por eleitor). Ter &gt; 30 vpm é fisicamente impossível (significaria 1 voto a cada 2 segundos!). Leituras de "35" decorrem de interpretação errônea de valores decimais como <code>0.35</code> por softwares de planilhas.
                </div>
                <div style="background:#0b0f19; padding:12px; border-radius:8px; border-left:3px solid #10b981; margin-top: 4px;">
                    <div style="font-weight: 700; color: #34d399; margin-bottom: 6px;">
                        <i class="fa-solid fa-map-location-dot"></i> Como Importar no Google Meus Mapas (Google My Maps):
                    </div>
                    <ol style="margin: 0; padding-left: 18px; display: flex; flex-direction: column; gap: 4px; font-size: 0.74rem;">
                        <li>Aplique os filtros desejados (município, zona ou risco) e clique em <strong>"Baixar CSV Google Maps"</strong>.</li>
                        <li>Acesse o <a href="https://www.google.com/mymaps" target="_blank" style="color:#38bdf8; text-decoration:underline; font-weight:700;">Google Meus Mapas (My Maps)</a> e clique em <em>"+ Criar um novo mapa"</em>.</li>
                        <li>Na camada do mapa, clique no link azul <strong>"Importar"</strong> e faça o upload do arquivo CSV baixado.</li>
                        <li>O Google Maps selecionará automaticamente as colunas <code>Latitude</code> e <code>Longitude</code>. Clique em <em>Continuar</em>.</li>
                        <li>Para o título do marcador, selecione a coluna <code>Nome</code> e clique em <em>Concluir</em>.</li>
                    </ol>
                    <div style="font-size: 0.68rem; color: #94a3b8; margin-top: 6px;">
                        💡 <em>Dica:</em> O Google My Maps recomenda até 2.000 pontos por camada. Se o seu filtro tiver mais de 2.000 seções, você pode segmentar por município ou risco para criar camadas organizadas.
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Scripts Leaflet e Lógica Interativa -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.heat/0.2.0/leaflet-heat.js"></script>
    <script>
        const locaisData = {data_json};
        const statsData = {stats_json};
        const bahiaBoundary = {bahia_geojson_str};

        const fmt = num => (num || 0).toLocaleString('pt-BR');

        // Inicializar Mapa centrado na Bahia
        const map = L.map('map', {{
            center: [-12.9714, -38.5014],
            zoom: 11,
            preferCanvas: true
        }});

        // Camadas Base 100% Livres e Gratuitas (Sem API Key, Sem Carto)
        const baseOsmHot = L.tileLayer('https://{{s}}.tile.openstreetmap.fr/hot/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles by HOT',
            maxZoom: 19
        }}).addTo(map);

        const baseOsmStandard = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }});

        const baseSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: 'Tiles &copy; Esri &mdash; Esri World Imagery',
            maxZoom: 18
        }});

        const baseStreet = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: 'Tiles &copy; Esri',
            maxZoom: 19
        }});

        const baseTopo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: 'Tiles &copy; Esri',
            maxZoom: 19
        }});

        const baseMaps = {{
            "OpenStreetMap HOT": baseOsmHot,
            "OpenStreetMap Padrão": baseOsmStandard,
            "Satélite Real (Esri Imagery)": baseSat,
            "Mapa de Ruas (Esri Street)": baseStreet,
            "Topográfico (Esri Topo)": baseTopo
        }};

        L.control.layers(baseMaps, null, {{ position: 'bottomleft' }}).addTo(map);

        // Contorno da Bahia
        if (bahiaBoundary && bahiaBoundary.type) {{
            L.geoJSON(bahiaBoundary, {{
                style: {{
                    color: '#38bdf8',
                    weight: 1.5,
                    fillOpacity: 0.02,
                    dashArray: '4, 4'
                }}
            }}).addTo(map);
        }}

        // Grupos de Camadas
        let markerClusterGroup = null;
        let heatLayer = null;

        // Referências do DOM
        const sidebar = document.getElementById('sidebar');
        const btnToggleSidebar = document.getElementById('btnToggleSidebar');
        const selectMunicipio = document.getElementById('selectMunicipio');
        const selectZona = document.getElementById('selectZona');
        const selectAnomalia = document.getElementById('selectAnomalia');
        const rangeScoreMin = document.getElementById('rangeScoreMin');
        const lblScoreMin = document.getElementById('lblScoreMin');
        const chkMarkers = document.getElementById('chkMarkers');
        const chkHeatmap = document.getElementById('chkHeatmap');
        const selectHeatMode = document.getElementById('selectHeatMode');

        const kpiSecCount = document.getElementById('kpiSecCount');
        const kpiVotantesCount = document.getElementById('kpiVotantesCount');
        const kpiMediaManual = document.getElementById('kpiMediaManual');
        const kpiPos17Count = document.getElementById('kpiPos17Count');
        const kpiPos17ManCount = document.getElementById('kpiPos17ManCount');
        const kpiPlacar = document.getElementById('kpiPlacar');
        const rankingList = document.getElementById('rankingList');
        const rankCount = document.getElementById('rankCount');

        const detailDrawer = document.getElementById('detailDrawer');
        const btnCloseDrawer = document.getElementById('btnCloseDrawer');
        const drawerLocalTitle = document.getElementById('drawerLocalTitle');
        const drawerLocalSub = document.getElementById('drawerLocalSub');
        const drawerSectionTabs = document.getElementById('drawerSectionTabs');
        const drawerScoreBadge = document.getElementById('drawerScoreBadge');
        const drawerScoreFill = document.getElementById('drawerScoreFill');
        const drawerScoreDesc = document.getElementById('drawerScoreDesc');

        const detUrna = document.getElementById('detUrna');
        const detVpm = document.getElementById('detVpm');
        const detT1 = document.getElementById('detT1');
        const detT2 = document.getElementById('detT2');
        const detComp = document.getElementById('detComp');
        const detAbs = document.getElementById('detAbs');
        const detBio = document.getElementById('detBio');
        const detMan = document.getElementById('detMan');
        const detBioBar = document.getElementById('detBioBar');
        const detManBar = document.getElementById('detManBar');
        const detPos17Val = document.getElementById('detPos17Val');
        const detAgregadaBanner = document.getElementById('detAgregadaBanner');
        const detAgregadaText = document.getElementById('detAgregadaText');
        const detDesvioEscolaRow = document.getElementById('detDesvioEscolaRow');
        const detDesvioEscolaVal = document.getElementById('detDesvioEscolaVal');
        const detV13 = document.getElementById('detV13');
        const detP13 = document.getElementById('detP13');
        const detV22 = document.getElementById('detV22');
        const detP22 = document.getElementById('detP22');
        const detV13Bar = document.getElementById('detV13Bar');
        const detV22Bar = document.getElementById('detV22Bar');
        const btnGoogleMapsExt = document.getElementById('btnGoogleMapsExt');

        const modalMetodologia = document.getElementById('modalMetodologia');
        const btnHelp = document.getElementById('btnHelp');
        const btnCloseHelp = document.getElementById('btnCloseHelp');

        const btnDownloadFilteredCSV = document.getElementById('btnDownloadFilteredCSV');
        const btnDownloadFilteredCSVSidebar = document.getElementById('btnDownloadFilteredCSVSidebar');
        const lblDownloadBtn = document.getElementById('lblDownloadBtn');
        const lblDownloadSidebar = document.getElementById('lblDownloadSidebar');
        let currentFilteredSecoes = [];

        // Modal Help Handlers
        btnHelp.addEventListener('click', () => modalMetodologia.classList.add('open'));
        btnCloseHelp.addEventListener('click', () => modalMetodologia.classList.remove('open'));
        modalMetodologia.addEventListener('click', (e) => {{
            if (e.target === modalMetodologia) modalMetodologia.classList.remove('open');
        }});

        // Sidebar Toggle
        btnToggleSidebar.addEventListener('click', () => {{
            sidebar.classList.toggle('collapsed');
            setTimeout(() => map.invalidateSize(), 360);
        }});

        // Preencher Lista de Municípios
        const municipiosSet = new Set();
        locaisData.forEach(d => municipiosSet.add(d.m));
        const sortedMun = Array.from(municipiosSet).sort();
        sortedMun.forEach(m => {{
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m;
            selectMunicipio.appendChild(opt);
        }});
        document.getElementById('labelTotalMun').textContent = `${{sortedMun.length}} municípios`;

        // Preencher Zonas quando mudar município
        function updateZonasSelect() {{
            const selMun = selectMunicipio.value;
            selectZona.innerHTML = '<option value="">Todas as Zonas do Município</option>';
            const zonasSet = new Set();
            locaisData.forEach(d => {{
                if (!selMun || d.m === selMun) {{
                    d.s.forEach(sec => zonasSet.add(sec[0]));
                }}
            }});
            const sortedZonas = Array.from(zonasSet).sort((a,b) => a - b);
            sortedZonas.forEach(z => {{
                const opt = document.createElement('option');
                opt.value = z;
                opt.textContent = `Zona ${{z}}`;
                selectZona.appendChild(opt);
            }});
        }}

        // Filtrar Dados
        function getFilteredLocais() {{
            const mun = selectMunicipio.value;
            const zona = selectZona.value ? parseInt(selectZona.value, 10) : null;
            const anom = selectAnomalia.value;
            const minScore = parseInt(rangeScoreMin.value, 10);

            let res = [];

            locaisData.forEach(loc => {{
                if (mun && loc.m !== mun) return;

                // Filtra as seções do local que atendem aos critérios
                const matchingSecs = loc.s.filter(sec => {{
                    // sec indices: 0:z, 1:s, 2:u, 5:pabs, 6:pman, 8:p17, 9:p17m, 16:sc, 20:f_abs, 21:f_man, 22:f_p17
                    if (zona && sec[0] !== zona) return false;
                    if (sec[16] < minScore) return false;

                    if (anom === 'critico') return sec[16] >= 70;
                    if (anom === 'alto_plus') return sec[16] >= 50;
                    if (anom === 'desvio_escola') return sec[30] === 1; // f_desvio_escola
                    if (anom === 'pos_17h_manual') return sec[31] === 1; // f_pos17_manual_alto
                    if (anom === 'trifeta') return sec[20] === 1 && sec[21] === 1 && sec[22] === 1;
                    if (anom === 'alta_manual') return sec[21] === 1; // pman >= 20
                    if (anom === 'pos_17h') return sec[8] >= 15;
                    if (anom === 'baixa_abs') return sec[20] === 1; // pabs <= 10
                    if (anom === 'agregada') return sec[26] === 1; // is_agregada
                    if (anom === 'ue2015') return sec[2].includes('2015') || sec[2].includes('2013') || sec[2].includes('2011');
                    if (anom === 'ue2020') return sec[2].includes('2020') || sec[2].includes('2022');

                    return true;
                }});

                if (matchingSecs.length > 0) {{
                    const maxSc = Math.max(...matchingSecs.map(s => s[16]));
                    res.push({{
                        ...loc,
                        sc: maxSc,
                        s: matchingSecs
                    }});
                }}
            }});

            return res;
        }}

        // Atualizar Mapa e Visualização
        function updateMap() {{
            const locais = getFilteredLocais();

            // 1. Atualizar KPIs do Painel
            let totalSecoes = 0;
            let totalVotantes = 0;
            let somaPctManual = 0;
            let totalPos17 = 0;
            let totalPos17Man = 0;
            let somaV13 = 0;
            let somaV22 = 0;
            let somaValidos = 0;
            let flatSecoes = [];

            locais.forEach(loc => {{
                loc.s.forEach(sec => {{
                    totalSecoes++;
                    totalVotantes += sec[4];
                    somaPctManual += sec[6];
                    totalPos17 += sec[8];
                    totalPos17Man += sec[9];
                    somaV13 += sec[12];
                    somaV22 += sec[13];
                    somaValidos += (sec[23] || (sec[12] + sec[13]));
                    flatSecoes.push({{
                        loc: loc,
                        sec: sec
                    }});
                }});
            }});

            kpiSecCount.textContent = `${{locais.length}} / ${{totalSecoes}}`;
            kpiVotantesCount.textContent = `${{fmt(totalVotantes)}} votantes`;
            kpiMediaManual.textContent = totalSecoes > 0 ? (somaPctManual / totalSecoes).toFixed(1) + '%' : '0.0%';
            kpiPos17Count.textContent = fmt(totalPos17);
            kpiPos17ManCount.textContent = `${{fmt(totalPos17Man)}} sem biometria`;

            if (somaValidos > 0) {{
                const p13 = ((somaV13 * 100) / somaValidos).toFixed(2);
                const p22 = ((somaV22 * 100) / somaValidos).toFixed(2);
                kpiPlacar.innerHTML = `<span style="color:#f87171;">${{p13}}%</span> vs <span style="color:#60a5fa;">${{p22}}%</span>`;
            }} else {{
                kpiPlacar.textContent = '-';
            }}

            // 2. Atualizar Ranking e Dados Exportáveis
            currentFilteredSecoes = flatSecoes;
            renderRanking(flatSecoes);

            const countTxt = fmt(flatSecoes.length);
            if (lblDownloadBtn) lblDownloadBtn.textContent = `Baixar CSV Google Maps (${{countTxt}})`;
            if (lblDownloadSidebar) lblDownloadSidebar.textContent = `Baixar CSV Google Maps (${{countTxt}})`;

            // 3. Atualizar Marcadores (Cluster)
            if (markerClusterGroup) {{
                map.removeLayer(markerClusterGroup);
            }}

            if (chkMarkers.checked) {{
                markerClusterGroup = L.markerClusterGroup({{
                    maxClusterRadius: 40,
                    spiderfyOnMaxZoom: true,
                    showCoverageOnHover: false,
                    iconCreateFunction: function(cluster) {{
                        const markers = cluster.getAllChildMarkers();
                        let maxSc = 0;
                        markers.forEach(m => {{
                            if (m.options.score > maxSc) maxSc = m.options.score;
                        }});
                        let clusterClass = 'badge-normal';
                        if (maxSc >= 70) clusterClass = 'badge-critico';
                        else if (maxSc >= 50) clusterClass = 'badge-alto';
                        else if (maxSc >= 35) clusterClass = 'badge-medio';

                        return L.divIcon({{
                            html: `<div style="width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:800; font-family:var(--font-mono); font-size:0.75rem;" class="${{clusterClass}}">${{cluster.getChildCount()}}</div>`,
                            className: 'custom-cluster-icon',
                            iconSize: [36, 36]
                        }});
                    }}
                }});

                locais.forEach(loc => {{
                    if (!loc.lat || !loc.lng) return;

                    let markerClass = 'marker-normal';
                    if (loc.sc >= 70) markerClass = 'marker-critico';
                    else if (loc.sc >= 50) markerClass = 'marker-alto';
                    else if (loc.sc >= 35) markerClass = 'marker-medio';

                    const icon = L.divIcon({{
                        className: 'custom-pin',
                        html: `<div class="marker-pin ${{markerClass}}"><span>${{loc.sc}}</span></div>`,
                        iconSize: [32, 32],
                        iconAnchor: [16, 32]
                    }});

                    const marker = L.marker([loc.lat, loc.lng], {{
                        icon: icon,
                        score: loc.sc
                    }});

                    marker.on('click', () => {{
                        openDrawer(loc);
                    }});

                    markerClusterGroup.addLayer(marker);
                }});

                map.addLayer(markerClusterGroup);
            }}

            // 4. Atualizar Heatmap
            if (heatLayer) {{
                map.removeLayer(heatLayer);
            }}

            if (chkHeatmap.checked) {{
                const heatMode = selectHeatMode.value;
                const heatPoints = [];

                locais.forEach(loc => {{
                    if (!loc.lat || !loc.lng) return;

                    let intensity = 0.5;
                    if (heatMode === 'score') {{
                        intensity = loc.sc / 100.0;
                    }} else if (heatMode === 'manual') {{
                        const avgMan = loc.s.reduce((acc, x) => acc + x[6], 0) / loc.s.length;
                        intensity = Math.min(1.0, avgMan / 40.0);
                    }} else if (heatMode === 'pos17') {{
                        const totP17 = loc.s.reduce((acc, x) => acc + x[8], 0);
                        intensity = Math.min(1.0, totP17 / 30.0);
                    }} else if (heatMode === 'comparecimento') {{
                        const avgAbs = loc.s.reduce((acc, x) => acc + x[5], 0) / loc.s.length;
                        intensity = Math.max(0.1, 1.0 - (avgAbs / 20.0));
                    }} else if (heatMode === 'voto13') {{
                        const p13 = loc.s.reduce((acc, x) => acc + x[14], 0) / loc.s.length;
                        intensity = p13 / 100.0;
                    }} else if (heatMode === 'voto22') {{
                        const p22 = loc.s.reduce((acc, x) => acc + x[15], 0) / loc.s.length;
                        intensity = p22 / 100.0;
                    }}

                    if (intensity > 0.05) {{
                        heatPoints.push([loc.lat, loc.lng, intensity]);
                    }}
                }});

                let gradient = {{ 0.2: '#3b82f6', 0.5: '#f59e0b', 0.8: '#ef4444', 1.0: '#b91c1c' }};
                if (heatMode === 'voto22') {{
                    gradient = {{ 0.2: '#0284c7', 0.6: '#2563eb', 1.0: '#1d4ed8' }};
                }} else if (heatMode === 'voto13') {{
                    gradient = {{ 0.2: '#f59e0b', 0.6: '#ef4444', 1.0: '#991b1b' }};
                }}

                heatLayer = L.heatLayer(heatPoints, {{
                    radius: 26,
                    blur: 18,
                    maxZoom: 14,
                    gradient: gradient
                }}).addTo(map);
            }}
        }}

        // Renderizar Lista Lateral de Ranking
        function renderRanking(flatSecoes) {{
            rankingList.innerHTML = '';

            // Ordena por Score descendente
            flatSecoes.sort((a, b) => b.sec[16] - a.sec[16] || b.sec[6] - a.sec[6]);

            const top50 = flatSecoes.slice(0, 50);
            rankCount.textContent = `${{top50.length}} de ${{fmt(flatSecoes.length)}}`;

            if (top50.length === 0) {{
                rankingList.innerHTML = '<div style="padding:15px; font-size:0.75rem; color:#94a3b8; text-align:center;">Nenhuma seção atende aos filtros atuais.</div>';
                return;
            }}

            top50.forEach((item, idx) => {{
                const loc = item.loc;
                const sec = item.sec;
                const div = document.createElement('div');
                div.className = 'ranking-item';

                let badgeClass = 'badge-normal';
                if (sec[16] >= 70) badgeClass = 'badge-critico';
                else if (sec[16] >= 50) badgeClass = 'badge-alto';
                else if (sec[16] >= 35) badgeClass = 'badge-medio';

                div.innerHTML = `
                    <div class="rank-pos">#${{idx + 1}}</div>
                    <div class="rank-info">
                        <div class="rank-title" title="${{loc.l}}">${{loc.l}}</div>
                        <div class="rank-sub">
                            <span>${{loc.m}}</span> • 
                            <span style="color:#cbd5e1; font-weight:700;">Z${{sec[0]}} S${{sec[1]}}</span> • 
                            <span style="color:#fbbf24;">${{sec[6].toFixed(1)}}% man</span> • 
                            <span style="color:#c084fc;">${{sec[8]}} pós-17h</span>
                        </div>
                    </div>
                    <div class="rank-score ${{badgeClass}}">${{sec[16]}} pts</div>
                `;

                div.addEventListener('click', () => {{
                    if (loc.lat && loc.lng) {{
                        map.flyTo([loc.lat, loc.lng], 16, {{ duration: 1.2 }});
                    }}
                    openDrawer(loc, sec[1]);
                }});

                rankingList.appendChild(div);
            }});
        }}

        // Abrir Drawer de Detalhes
        function openDrawer(loc, targetSecao = null) {{
            drawerLocalTitle.textContent = loc.l;
            drawerLocalSub.textContent = `${{loc.b ? loc.b + ', ' : ''}}${{loc.m}}`;

            // Construir abas de seções
            drawerSectionTabs.innerHTML = '';
            const sections = loc.s;

            let activeSec = sections[0];
            if (targetSecao) {{
                const found = sections.find(s => s[1] === targetSecao);
                if (found) activeSec = found;
            }}

            sections.forEach(sec => {{
                const btn = document.createElement('button');
                btn.className = `section-tab-btn ${{sec[1] === activeSec[1] ? 'active' : ''}}`;
                btn.textContent = `S${{sec[1]}} (${{sec[16]}}p)`;
                btn.addEventListener('click', () => {{
                    document.querySelectorAll('.section-tab-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    renderDrawerSectionDetails(loc, sec);
                }});
                drawerSectionTabs.appendChild(btn);
            }});

            renderDrawerSectionDetails(loc, activeSec);
            detailDrawer.classList.add('open');
        }}

        function renderDrawerSectionDetails(loc, sec) {{
            // sec: 0:z, 1:s, 2:u, 3:apt, 4:cmp, 5:pabs, 6:pman, 7:qman, 8:p17, 9:p17m,
            // 10:t1, 11:t2, 12:v13, 13:v22, 14:p13, 15:p22, 16:sc, 17:risk, 18:vpm, 19:t_med,
            // 20:f_abs, 21:f_man, 22:f_p17, 23:v_val, 24:v_tot, 25:sec_agr, 26:is_agr,
            // 27:dif_man, 28:med_man, 29:p_p17m, 30:f_desv, 31:f_p17_man
            const sc = sec[16];
            drawerScoreBadge.textContent = `${{sc}} pts (${{sec[17]}})`;
            drawerScoreFill.style.width = `${{Math.min(100, sc)}}%`;

            let badgeClass = 'badge-normal';
            let fillColor = '#3b82f6';
            if (sc >= 70) {{
                badgeClass = 'badge-critico';
                fillColor = '#ef4444';
            }} else if (sc >= 50) {{
                badgeClass = 'badge-alto';
                fillColor = '#f97316';
            }} else if (sc >= 35) {{
                badgeClass = 'badge-medio';
                fillColor = '#f59e0b';
            }}

            drawerScoreBadge.className = `rank-score ${{badgeClass}}`;
            drawerScoreFill.style.background = fillColor;

            // Seção Agregada Banner
            if (sec[26] === 1 && sec[25]) {{
                detAgregadaBanner.style.display = 'block';
                detAgregadaText.innerHTML = `Esta urna recebeu os eleitores da(s) seção(ões) <strong>${{sec[25]}}</strong>. Capacidade consolidada oficial do TSE: <strong>${{fmt(sec[3])}} aptos</strong>.`;
            }} else {{
                detAgregadaBanner.style.display = 'none';
            }}

            // Justificativa dos pontos
            let reasons = [];
            if (sec[26] === 1 && sec[25]) reasons.push(`Urna consolidada com seções agregadas: ${{sec[25]}} (${{fmt(sec[3])}} aptos reais)`);
            if (sec[5] <= 5.0) reasons.push("Comparecimento atípico massivo (abstenção consolidada ≤ 5,0%)");
            else if (sec[5] <= 10.0) reasons.push("Baixa abstenção atípica (≤ 10,0% de aptos)");

            if (sec[6] >= 50.0) reasons.push(`${{sec[6].toFixed(1)}}% de eleitores liberados manualmente pelo mesário (sem biometria)`);
            else if (sec[6] >= 30.0) reasons.push(`Alta taxa de liberação manual sem biometria (${{sec[6].toFixed(1)}}%)`);

            if (sec[27] >= 20.0) reasons.push(`Desvio Intra-Colégio: +${{sec[27].toFixed(1)}}% de liberações manuais acima da média das outras salas desta escola (${{sec[28].toFixed(1)}}%)`);

            if (sec[8] >= 10 && sec[29] >= 70.0) reasons.push(`Volume pós-17h com liberação manual concentrada (${{sec[8]}} votos, ${{sec[9]}} manuais — ${{sec[29].toFixed(1)}}%)`);
            else if (sec[8] >= 30) reasons.push(`Volume extremo de votos após 17h (${{sec[8]}} votos computados)`);
            else if (sec[8] > 0) reasons.push(`${{sec[8]}} votos registrados após as 17:00 (${{sec[9]}} manuais)`);

            const pMax = Math.max(sec[14], sec[15]);
            if (pMax >= 80.0) reasons.push(`Desproporção extrema de votos (${{pMax.toFixed(1)}}% para um candidato)`);

            drawerScoreDesc.innerHTML = reasons.length > 0
                ? `<ul style="padding-left:16px; margin:0;">${{reasons.map(r => `<li>${{r}}</li>`).join('')}}</ul>`
                : "Seção com padrões operacionais dentro das médias estatísticas estaduais.";

            // Informações Urna
            detUrna.textContent = sec[2];
            detT1.textContent = sec[10] || '--';
            detT2.textContent = sec[11] || '--';
            detComp.textContent = `${{fmt(sec[4])}} eleitores (${{fmt(sec[3])}} aptos consolid.)`;
            detAbs.textContent = `${{sec[5].toFixed(1)}}%`;

            // Ritmo de Votação (VPM formatado sem ambiguidades)
            const segPorVoto = sec[18] > 0 ? Math.round(60 / sec[18]) : 0;
            const minP = Math.floor(segPorVoto / 60);
            const secP = segPorVoto % 60;
            const tempoFluxoStr = minP > 0 ? `${{minP}}m${{secP < 10 ? '0' : ''}}${{secP}}s` : `${{secP}}s`;
            detVpm.textContent = `${{sec[18].toFixed(2)}} vpm (1 voto a cada ${{tempoFluxoStr}} | cabine: ${{sec[19].toFixed(1)}}s)`;
            detVpm.title = `Ritmo médio do fluxo: 1 voto a cada ${{tempoFluxoStr}}. Tempo médio na cabine: ${{sec[19].toFixed(1)}}s.`;

            // Biometria
            const bioCount = Math.max(0, sec[4] - sec[7]);
            detBio.textContent = `${{fmt(bioCount)}} (${{(100 - sec[6]).toFixed(1)}}%)`;
            detMan.textContent = `${{fmt(sec[7])}} (${{sec[6].toFixed(1)}}%)`;
            detBioBar.style.width = `${{100 - sec[6]}}%`;
            detManBar.style.width = `${{sec[6]}}%`;

            // Desvio Intra-Colégio
            if (sec[27] !== 0) {{
                detDesvioEscolaRow.style.display = 'flex';
                const sgn = sec[27] > 0 ? '+' : '';
                const color = sec[27] >= 20 ? '#ef4444' : (sec[27] >= 10 ? '#f59e0b' : '#94a3b8');
                detDesvioEscolaVal.innerHTML = `<span style="color:${{color}}; font-weight:700;">${{sgn}}${{sec[27].toFixed(1)}}%</span> vs média do colégio (${{sec[28].toFixed(1)}}%)`;
            }} else {{
                detDesvioEscolaRow.style.display = 'none';
            }}

            detPos17Val.textContent = `${{sec[8]}} votos (sendo ${{sec[9]}} manuais — ${{sec[29].toFixed(1)}}%)`;

            // Votação Nominal
            detV13.textContent = fmt(sec[12]);
            detP13.textContent = sec[14].toFixed(1) + '%';
            detV22.textContent = fmt(sec[13]);
            detP22.textContent = sec[15].toFixed(1) + '%';
            const sumPres = sec[12] + sec[13];
            if (sumPres > 0) {{
                detV13Bar.style.width = `${{(sec[12] * 100 / sumPres).toFixed(1)}}%`;
                detV22Bar.style.width = `${{(sec[13] * 100 / sumPres).toFixed(1)}}%`;
            }}

            // Link Google Maps
            btnGoogleMapsExt.href = `https://www.google.com/maps/search/?api=1&query=${{loc.lat}},${{loc.lng}}`;
        }}

        btnCloseDrawer.addEventListener('click', () => {{
            detailDrawer.classList.remove('open');
        }});

        // Exportar dados do filtro atual no formato oficial do Google Meus Mapas (Google My Maps)
        function downloadFilteredCSVForGoogleMaps() {{
            if (!currentFilteredSecoes || currentFilteredSecoes.length === 0) {{
                alert("Nenhuma seção encontrada com os filtros selecionados para exportar.");
                return;
            }}

            // Cabeçalho otimizado para o Google Meus Mapas
            // Colunas Latitude e Longitude são reconhecidas nativamente para plotar os marcadores.
            // Coluna Nome é selecionada como título exibido no mapa.
            const headers = [
                "Nome",
                "Latitude",
                "Longitude",
                "Score_Anomalia",
                "Nivel_Risco",
                "Municipio",
                "Zona",
                "Secao",
                "Secoes_Agregadas",
                "Local_Votacao",
                "Bairro",
                "Endereco",
                "Modelo_Urna",
                "Lib_Manual_Pct",
                "Media_Manual_Escola_Pct",
                "Desvio_Manual_Escola_Pct",
                "Qtd_Manual",
                "Votos_Pos_17h",
                "Votos_Pos_17h_Manual",
                "Pct_Pos_17h_Manual",
                "Abstencao_Pct",
                "Eleitores_Aptos_Reais",
                "Comparecimento",
                "Votos_Lula_13",
                "Votos_Bolsonaro_22",
                "Pct_Lula_Validos",
                "Pct_Bolsonaro_Validos",
                "Primeiro_Voto",
                "Ultimo_Voto",
                "Votos_Por_Minuto",
                "Ritmo_Fluxo_Extenso",
                "Tempo_Medio_Cabine_Seg",
                "Descricao"
            ];

            function escapeCSV(val) {{
                if (val === null || val === undefined) return '""';
                let str = String(val).replace(/"/g, '""');
                return '"' + str + '"';
            }}

            const rows = [headers.join(",")];

            currentFilteredSecoes.forEach(item => {{
                const loc = item.loc;
                const sec = item.sec;

                const lat = loc.lat ? loc.lat.toFixed(6) : "";
                const lng = loc.lng ? loc.lng.toFixed(6) : "";

                const segPorVoto = sec[18] > 0 ? Math.round(60 / sec[18]) : 0;
                const minP = Math.floor(segPorVoto / 60);
                const secP = segPorVoto % 60;
                const tempoFluxoStr = minP > 0 ? `${{minP}}m${{secP < 10 ? '0' : ''}}${{secP}}s` : `${{secP}}s`;
                const ritmoExtenso = `${{sec[18].toFixed(2)}} vpm (1 voto a cada ${{tempoFluxoStr}})`;

                // Título claro exibido no marcador do Google Maps
                let agrBadge = (sec[26] === 1 && sec[25]) ? " [Agregadas: " + sec[25] + "]" : "";
                const nome = "[Score " + sec[16] + " | " + sec[17] + "] Z " + sec[0] + " S " + sec[1] + agrBadge + " - " + loc.l + " (" + loc.m + ")";

                // Descrição formatada exibida no balão popup do Google Maps
                let desc = "[Sentinela Juris - Evidência Pericial]\\nMunicípio: " + loc.m + " | Zona: " + sec[0] + " | Seção: " + sec[1];
                if (sec[26] === 1 && sec[25]) {{
                    desc += " (Urna Agregada com Seções: " + sec[25] + ")";
                }}
                desc += "\\nLocal: " + loc.l + " (" + (loc.b || "Bairro N/I") + ")\\n" +
                    "Endereço: " + (loc.e || "N/A") + "\\n" +
                    "Score Anomalia: " + sec[16] + " pts (" + sec[17] + ")\\n" +
                    "Urna: " + sec[2] + "\\n" +
                    "Liberação Manual Mesário: " + sec[6].toFixed(1) + "% (" + sec[7] + " eleitores sem biometria)\\n";
                if (sec[27] !== 0) {{
                    desc += "Desvio Intra-Escola: " + (sec[27] > 0 ? "+" : "") + sec[27].toFixed(1) + "% vs média da escola (" + sec[28].toFixed(1) + "%)\\n";
                }}
                desc += "Votos Registrados Pós-17h: " + sec[8] + " (sendo " + sec[9] + " manuais — " + sec[29].toFixed(1) + "%)\\n" +
                    "Abstenção Real Consolidada: " + sec[5].toFixed(1) + "% (" + sec[4] + " votantes de " + sec[3] + " aptos)\\n" +
                    "Ritmo de Fluxo: " + ritmoExtenso + " (cabine: " + sec[19].toFixed(1) + "s)\\n" +
                    "Placar: Lula " + sec[12] + " (" + sec[14].toFixed(1) + "%) vs Bolsonaro " + sec[13] + " (" + sec[15].toFixed(1) + "%)\\n" +
                    "Horários: 1º voto às " + (sec[10] || "-") + ", encerramento às " + (sec[11] || "-");

                const rowData = [
                    escapeCSV(nome),
                    lat,
                    lng,
                    sec[16],
                    escapeCSV(sec[17]),
                    escapeCSV(loc.m),
                    sec[0],
                    sec[1],
                    escapeCSV(sec[25] || ""),
                    escapeCSV(loc.l),
                    escapeCSV(loc.b),
                    escapeCSV(loc.e),
                    escapeCSV(sec[2]),
                    escapeCSV(sec[6].toFixed(1) + "%"),
                    escapeCSV(sec[28].toFixed(1) + "%"),
                    escapeCSV((sec[27] > 0 ? "+" : "") + sec[27].toFixed(1) + "%"),
                    sec[7],
                    sec[8],
                    sec[9],
                    escapeCSV(sec[29].toFixed(1) + "%"),
                    escapeCSV(sec[5].toFixed(1) + "%"),
                    sec[3],
                    sec[4],
                    sec[12],
                    sec[13],
                    escapeCSV(sec[14].toFixed(1) + "%"),
                    escapeCSV(sec[15].toFixed(1) + "%"),
                    escapeCSV(sec[10]),
                    escapeCSV(sec[11]),
                    sec[18].toFixed(2),
                    escapeCSV(ritmoExtenso),
                    sec[19].toFixed(1),
                    escapeCSV(desc)
                ];

                rows.push(rowData.join(","));
            }});

            const csvContent = "\\ufeff" + rows.join("\\r\\n");
            const blob = new Blob([csvContent], {{ type: "text/csv;charset=utf-8;" }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");

            const mun = selectMunicipio.value ? "_" + selectMunicipio.value.toLowerCase().replace(/[^a-z0-9]/g, '_') : "";
            const anom = selectAnomalia.value !== 'all' ? "_" + selectAnomalia.value : "";
            const filename = "sentinela_juris_evidencias_forenses" + mun + anom + "_" + currentFilteredSecoes.length + "secoes.csv";

            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            if (currentFilteredSecoes.length > 2000) {{
                setTimeout(() => {{
                    alert("Arquivo \\"" + filename + "\\" baixado com sucesso com " + fmt(currentFilteredSecoes.length) + " seções!\\n\\nNota: O Google Meus Mapas recomenda até 2.000 pontos por camada. Caso queira importar sem restrições, você pode filtrar por município ou faixa de risco (ex: Risco Crítico ou Alto) para criar camadas separadas.");
                }}, 300);
            }}
        }}

        if (btnDownloadFilteredCSV) {{
            btnDownloadFilteredCSV.addEventListener('click', downloadFilteredCSVForGoogleMaps);
        }}
        if (btnDownloadFilteredCSVSidebar) {{
            btnDownloadFilteredCSVSidebar.addEventListener('click', downloadFilteredCSVForGoogleMaps);
        }}

        // Event Listeners dos Filtros
        selectMunicipio.addEventListener('change', () => {{
            updateZonasSelect();
            const mun = selectMunicipio.value;
            if (mun) {{
                const locs = locaisData.filter(d => d.m === mun);
                if (locs.length > 0) {{
                    const lats = locs.map(d => d.lat);
                    const lngs = locs.map(d => d.lng);
                    map.fitBounds([
                        [Math.min(...lats), Math.min(...lngs)],
                        [Math.max(...lats), Math.max(...lngs)]
                    ], {{ padding: [60, 60], maxZoom: 14 }});
                }}
            }} else {{
                map.flyTo([-12.9714, -38.5014], 11, {{ duration: 1.2 }});
            }}
            updateMap();
        }});

        selectZona.addEventListener('change', updateMap);
        selectAnomalia.addEventListener('change', updateMap);
        rangeScoreMin.addEventListener('input', () => {{
            lblScoreMin.textContent = rangeScoreMin.value;
            updateMap();
        }});
        chkMarkers.addEventListener('change', updateMap);
        chkHeatmap.addEventListener('change', updateMap);
        selectHeatMode.addEventListener('change', updateMap);

        // Inicialização
        updateZonasSelect();
        updateMap();
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    export_mapa_auditoria_secoes()
