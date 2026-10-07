import os
import duckdb
import json
import pandas as pd
import unicodedata

def normalize_name(text):
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', str(text).upper().strip())
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def generate_integrated_dashboard():
    output_dir = "data/processed/google_maps"
    os.makedirs(output_dir, exist_ok=True)
    
    con = duckdb.connect("data/processed/eleicoes.duckdb")
    print("Consolidando dados eleitorais, demográficos, renda e modelos de urna no DuckDB...")

    # 1. Carregar dados de Renda
    with open("data/geo/renda_4sm_municipios_ba.json", "r", encoding="utf-8") as f:
        renda_dict = json.load(f)
    df_renda = pd.DataFrame(list(renda_dict.values()))
    df_renda["MUNICIPIO_NORM"] = df_renda["MUNICIPIO"].apply(normalize_name)
    con.register("df_renda_reg", df_renda)

    # 2. Criar Tabela Mestra Integrada
    con.execute("""
        CREATE OR REPLACE TABLE eleicoes_2026_consolidado_bahia AS
        WITH 
        -- Demografia TSE
        demografia AS (
            SELECT 
                NM_MUNICIPIO AS MUNICIPIO,
                CAST(SUM(QT_ELEITORES) AS BIGINT) AS TOTAL_ELEITORES,
                CAST(SUM(CASE WHEN DS_GENERO = 'FEMININO' THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_FEM,
                CAST(SUM(CASE WHEN DS_GENERO = 'MASCULINO' THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_MASC,
                ROUND(SUM(CASE WHEN DS_GENERO = 'FEMININO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_FEM,
                
                CAST(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('SUPERIOR COMPLETO', 'SUPERIOR INCOMPLETO') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_SUPERIOR,
                ROUND(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('SUPERIOR COMPLETO', 'SUPERIOR INCOMPLETO') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_SUPERIOR,
                
                CAST(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('ANALFABETO', 'LÊ E ESCREVE') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_BAIXA_ESCOLARIDADE,
                ROUND(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('ANALFABETO', 'LÊ E ESCREVE') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_BAIXA_ESCOLARIDADE,

                CAST(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('16 ANOS', '17 ANOS', '18 A 20 ANOS', '21 A 24 ANOS') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_JOVENS,
                ROUND(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('16 ANOS', '17 ANOS', '18 A 20 ANOS', '21 A 24 ANOS') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_JOVENS,
                
                CAST(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('60 A 69 ANOS', '70 A 79 ANOS', '80 ANOS OU MAIS') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_IDOSOS,
                ROUND(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('60 A 69 ANOS', '70 A 79 ANOS', '80 ANOS OU MAIS') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_IDOSOS,

                ROUND(SUM(QT_ELEITORES_BIOMETRIA) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_BIOMETRIA
            FROM perfil_eleitorado_2026_BA
            GROUP BY NM_MUNICIPIO
        ),
        -- Modelos de Urna
        urnas AS (
            SELECT 
                NM_MUNICIPIO AS MUNICIPIO,
                COUNT(*) AS TOTAL_URNAS,
                CAST(SUM(CASE WHEN CAST(NR_URNA_ESPERADA AS BIGINT) < 2000000 THEN 1 ELSE 0 END) AS BIGINT) AS URNAS_UE2015,
                CAST(SUM(CASE WHEN CAST(NR_URNA_ESPERADA AS BIGINT) >= 2000000 THEN 1 ELSE 0 END) AS BIGINT) AS URNAS_UE2020,
                ROUND(SUM(CASE WHEN CAST(NR_URNA_ESPERADA AS BIGINT) < 2000000 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS PCT_URNAS_UE2015
            FROM correspondencias_2026_BA
            GROUP BY NM_MUNICIPIO
        ),
        -- Votos Presidente
        votos_pres AS (
            SELECT 
                NM_MUNICIPIO AS MUNICIPIO,
                CAST(SUM(QT_VOTOS) AS BIGINT) AS TOTAL_VOTOS_PRES,
                CAST(SUM(CASE WHEN NM_VOTAVEL LIKE '%LULA%' THEN QT_VOTOS ELSE 0 END) AS BIGINT) AS VOTOS_LULA,
                ROUND(SUM(CASE WHEN NM_VOTAVEL LIKE '%LULA%' THEN QT_VOTOS ELSE 0 END) * 100.0 / SUM(QT_VOTOS), 2) AS PCT_LULA,
                
                CAST(SUM(CASE WHEN NM_VOTAVEL LIKE '%BOLSONARO%' THEN QT_VOTOS ELSE 0 END) AS BIGINT) AS VOTOS_BOLSONARO,
                ROUND(SUM(CASE WHEN NM_VOTAVEL LIKE '%BOLSONARO%' THEN QT_VOTOS ELSE 0 END) * 100.0 / SUM(QT_VOTOS), 2) AS PCT_BOLSONARO,

                CAST(SUM(CASE WHEN NM_VOTAVEL LIKE '%CURY%' THEN QT_VOTOS ELSE 0 END) AS BIGINT) AS VOTOS_CURY,
                ROUND(SUM(CASE WHEN NM_VOTAVEL LIKE '%CURY%' THEN QT_VOTOS ELSE 0 END) * 100.0 / SUM(QT_VOTOS), 2) AS PCT_CURY,

                CAST(SUM(CASE WHEN NM_VOTAVEL LIKE '%CAIADO%' THEN QT_VOTOS ELSE 0 END) AS BIGINT) AS VOTOS_CAIADO,
                ROUND(SUM(CASE WHEN NM_VOTAVEL LIKE '%CAIADO%' THEN QT_VOTOS ELSE 0 END) * 100.0 / SUM(QT_VOTOS), 2) AS PCT_CAIADO,

                ROUND((SUM(CASE WHEN NM_VOTAVEL LIKE '%LULA%' THEN QT_VOTOS ELSE 0 END) - SUM(CASE WHEN NM_VOTAVEL LIKE '%BOLSONARO%' THEN QT_VOTOS ELSE 0 END)) * 100.0 / SUM(QT_VOTOS), 2) AS MARGEM_LULA_BOLSONARO
            FROM votacao_presidente_secao_2026_BA
            GROUP BY NM_MUNICIPIO
        ),
        -- Votos Governador
        votos_gov AS (
            SELECT 
                NM_MUNICIPIO AS MUNICIPIO,
                CAST(SUM(QT_VOTOS) AS BIGINT) AS TOTAL_VOTOS_GOV,
                CAST(SUM(CASE WHEN NM_VOTAVEL LIKE '%JERONIMO%' THEN QT_VOTOS ELSE 0 END) AS BIGINT) AS VOTOS_JERONIMO,
                ROUND(SUM(CASE WHEN NM_VOTAVEL LIKE '%JERONIMO%' THEN QT_VOTOS ELSE 0 END) * 100.0 / SUM(QT_VOTOS), 2) AS PCT_JERONIMO,
                
                CAST(SUM(CASE WHEN NM_VOTAVEL LIKE '%MAGALH%' OR NM_VOTAVEL LIKE '%NETO%' THEN QT_VOTOS ELSE 0 END) AS BIGINT) AS VOTOS_ACM_NETO,
                ROUND(SUM(CASE WHEN NM_VOTAVEL LIKE '%MAGALH%' OR NM_VOTAVEL LIKE '%NETO%' THEN QT_VOTOS ELSE 0 END) * 100.0 / SUM(QT_VOTOS), 2) AS PCT_ACM_NETO,

                ROUND((SUM(CASE WHEN NM_VOTAVEL LIKE '%JERONIMO%' THEN QT_VOTOS ELSE 0 END) - SUM(CASE WHEN NM_VOTAVEL LIKE '%MAGALH%' OR NM_VOTAVEL LIKE '%NETO%' THEN QT_VOTOS ELSE 0 END)) * 100.0 / SUM(QT_VOTOS), 2) AS MARGEM_JERONIMO_NETO
            FROM votacao_secao_2026_BA
            WHERE DS_CARGO = 'Governador'
            GROUP BY NM_MUNICIPIO
        )
        SELECT 
            d.MUNICIPIO,
            d.TOTAL_ELEITORES,
            d.PCT_FEM,
            d.PCT_SUPERIOR,
            d.PCT_BAIXA_ESCOLARIDADE,
            d.PCT_JOVENS,
            d.PCT_IDOSOS,
            d.PCT_BIOMETRIA,
            COALESCE(r.PCT_RENDA_ACIMA_4SM, 5.0) AS PCT_RENDA_ACIMA_4SM,
            COALESCE(r.SALARIO_MEDIO_SM, 1.8) AS SALARIO_MEDIO_SM,
            COALESCE(r.RENDIMENTO_DOMICILIAR_RS, 1500.0) AS RENDIMENTO_DOMICILIAR_RS,
            
            -- Urnas
            COALESCE(u.TOTAL_URNAS, 0) AS TOTAL_URNAS,
            COALESCE(u.URNAS_UE2015, 0) AS URNAS_UE2015,
            COALESCE(u.URNAS_UE2020, 0) AS URNAS_UE2020,
            COALESCE(u.PCT_URNAS_UE2015, 0.0) AS PCT_URNAS_UE2015,

            -- Votação Presidente
            COALESCE(vp.TOTAL_VOTOS_PRES, 0) AS TOTAL_VOTOS_PRES,
            COALESCE(vp.VOTOS_LULA, 0) AS VOTOS_LULA,
            COALESCE(vp.PCT_LULA, 0.0) AS PCT_LULA,
            COALESCE(vp.VOTOS_BOLSONARO, 0) AS VOTOS_BOLSONARO,
            COALESCE(vp.PCT_BOLSONARO, 0.0) AS PCT_BOLSONARO,
            COALESCE(vp.VOTOS_CURY, 0) AS VOTOS_CURY,
            COALESCE(vp.PCT_CURY, 0.0) AS PCT_CURY,
            COALESCE(vp.VOTOS_CAIADO, 0) AS VOTOS_CAIADO,
            COALESCE(vp.PCT_CAIADO, 0.0) AS PCT_CAIADO,
            COALESCE(vp.MARGEM_LULA_BOLSONARO, 0.0) AS MARGEM_PRES,

            -- Votação Governador
            COALESCE(vg.TOTAL_VOTOS_GOV, 0) AS TOTAL_VOTOS_GOV,
            COALESCE(vg.VOTOS_JERONIMO, 0) AS VOTOS_JERONIMO,
            COALESCE(vg.PCT_JERONIMO, 0.0) AS PCT_JERONIMO,
            COALESCE(vg.VOTOS_ACM_NETO, 0) AS VOTOS_ACM_NETO,
            COALESCE(vg.PCT_ACM_NETO, 0.0) AS PCT_ACM_NETO,
            COALESCE(vg.MARGEM_JERONIMO_NETO, 0.0) AS MARGEM_GOV
        FROM demografia d
        LEFT JOIN urnas u ON d.MUNICIPIO = u.MUNICIPIO
        LEFT JOIN votos_pres vp ON d.MUNICIPIO = vp.MUNICIPIO
        LEFT JOIN votos_gov vg ON d.MUNICIPIO = vg.MUNICIPIO
        LEFT JOIN df_renda_reg r ON d.MUNICIPIO = r.MUNICIPIO_NORM
        ORDER BY d.TOTAL_ELEITORES DESC
    """)

    df_master = con.execute("SELECT * FROM eleicoes_2026_consolidado_bahia").df()
    
    # Exportar arquivos analíticos
    csv_master = "data/processed/eleicoes_2026_consolidado_bahia.csv"
    parquet_master = "data/processed/eleicoes_2026_consolidado_bahia.parquet"
    df_master.to_csv(csv_master, index=False, encoding="utf-8")
    df_master.to_parquet(parquet_master, index=False)
    print(f"[OK] Base Mestra consolidada: {csv_master} e {parquet_master}")

    # 3. Cruzar com GeoJSON dos 417 municípios
    with open("data/geo/bahia_municipios.geojson", "r", encoding="utf-8") as f:
        geo_data = json.load(f)
    
    with open("data/geo/ibge_municipios_ba.json", "r", encoding="utf-8") as f:
        ibge_list = json.load(f)

    ibge_map = {str(item["id"]): normalize_name(item["nome"]) for item in ibge_list}
    ibge_display = {str(item["id"]): item["nome"] for item in ibge_list}

    tse_dict = {}
    for _, row in df_master.iterrows():
        norm_key = normalize_name(row["MUNICIPIO"])
        tse_dict[norm_key] = row.to_dict()

    matched = 0
    for feature in geo_data.get("features", []):
        props = feature.get("properties", {})
        code = str(props.get("codarea", ""))
        nome_norm = ibge_map.get(code, "")
        nome_display = ibge_display.get(code, "")
        
        data = tse_dict.get(nome_norm)
        if data:
            matched += 1
            for k, v in data.items():
                props[k] = v
        else:
            props["MUNICIPIO"] = nome_display
            props["TOTAL_ELEITORES"] = 0
            
    print(f"[OK] {matched}/417 municípios combinados no GeoJSON com todos os votos, urnas e demografia.")
    
    enriched_geo_str = json.dumps(geo_data, ensure_ascii=False)
    
    # 4. Gerar Dashboards 2D e 3D Integrados
    gerar_dashboard_integrado_html(enriched_geo_str, df_master, os.path.join(output_dir, "mapa_eleicoes_2026_integrado_bahia.html"))
    gerar_dashboard_3d_integrado_html(enriched_geo_str, df_master, os.path.join(output_dir, "mapa_3d_eleicoes_2026_integrado_bahia.html"))

def gerar_dashboard_integrado_html(geo_json_str, df, output_path):
    total_bahia = int(df["TOTAL_ELEITORES"].sum())
    total_lula = int(df["VOTOS_LULA"].sum())
    pct_lula = round(total_lula * 100.0 / int(df["TOTAL_VOTOS_PRES"].sum()), 2)
    total_bols = int(df["VOTOS_BOLSONARO"].sum())
    pct_bols = round(total_bols * 100.0 / int(df["TOTAL_VOTOS_PRES"].sum()), 2)
    total_ue2015 = int(df["URNAS_UE2015"].sum())
    pct_ue2015 = round(total_ue2015 * 100.0 / int(df["TOTAL_URNAS"].sum()), 2)
    
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel Integrado: Votos, Urnas e Demografia - Bahia 2026</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }}
        body {{ display: flex; height: 100vh; overflow: hidden; background: #0b0f19; color: #f8fafc; }}
        #sidebar {{
            width: 420px; background: #0f172a; padding: 22px; display: flex; flex-direction: column;
            gap: 12px; box-shadow: 4px 0 24px rgba(0,0,0,0.5); z-index: 1000; overflow-y: auto;
            border-right: 1px solid rgba(255,255,255,0.08);
        }}
        #map {{ flex: 1; height: 100%; }}
        .badge {{
            display: inline-block; padding: 4px 10px; border-radius: 9999px;
            font-size: 0.72rem; font-weight: 700; background: #38bdf8; color: #000;
        }}
        .metric-select, .search-input {{
            width: 100%; padding: 10px 12px; background: #1e293b; border: 1px solid #334155;
            border-radius: 8px; color: #f8fafc; font-size: 0.88rem; font-weight: 600; outline: none;
            transition: 0.2s;
        }}
        .metric-select:focus, .search-input:focus {{ border-color: #38bdf8; }}
        .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
        .stat-card {{
            background: #1e293b; padding: 10px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);
        }}
        .stat-card .val {{ font-size: 1.2rem; font-weight: 700; }}
        .stat-card .lbl {{ font-size: 0.72rem; color: #94a3b8; }}
        #muniDetails {{
            background: #1e293b; border-radius: 10px; padding: 14px; border: 1px solid #38bdf8;
            display: none;
        }}
        .section-title {{
            font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.5px;
            color: #94a3b8; font-weight: 700; margin-top: 6px; border-bottom: 1px solid rgba(255,255,255,0.08);
            padding-bottom: 2px;
        }}
        .legend {{
            padding: 10px 14px; background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(8px);
            border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); color: #fff; font-size: 0.78rem;
            line-height: 1.5; box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }}
        .legend i {{ width: 14px; height: 14px; float: left; margin-right: 8px; opacity: 0.85; border-radius: 3px; }}
    </style>
</head>
<body>
    <div id="sidebar">
        <div>
            <span class="badge">PAINEL INTEGRADO ELEIÇÕES 2026</span>
            <h2 style="font-size: 1.25rem; margin-top: 6px; font-weight: 700;">Bahia: Votos, Urnas & Demografia</h2>
            <p style="font-size: 0.78rem; color: #94a3b8; margin-top: 2px;">Cruzamento Multidimensional (417 municípios)</p>
        </div>

        <div>
            <label style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 4px; display: block; font-weight: 600;">Selecione a Camada Temática do Mapa:</label>
            <select id="metricSelect" class="metric-select">
                <optgroup label="🗳️ Votação Presidencial (1º Turno 2026)">
                    <option value="PCT_LULA" selected>🔴 Lula (% Votos)</option>
                    <option value="PCT_BOLSONARO">🔵 Flávio Bolsonaro (% Votos)</option>
                    <option value="MARGEM_PRES">⚖️ Margem Presidencial (Lula - Bolsonaro %)</option>
                    <option value="PCT_CURY">🟡 Augusto Cury (% Votos)</option>
                    <option value="PCT_CAIADO">🟢 Ronaldo Caiado (% Votos)</option>
                </optgroup>
                <optgroup label="🏛️ Votação para Governador (1º Turno 2026)">
                    <option value="PCT_JERONIMO">🔴 Jerônimo Rodrigues (% Votos)</option>
                    <option value="PCT_ACM_NETO">🔵 ACM Neto (% Votos)</option>
                    <option value="MARGEM_GOV">⚖️ Margem Governador (Jerônimo - ACM Neto %)</option>
                </optgroup>
                <optgroup label="⚙️ Modelos de Urna Eletrônica (Hardware)">
                    <option value="PCT_URNAS_UE2015">⚠️ Urnas UE2015 (Anteriores a 2020) (%)</option>
                    <option value="URNAS_UE2015">📟 Qtd de Urnas UE2015</option>
                    <option value="TOTAL_URNAS">🗳️ Total de Urnas por Município</option>
                </optgroup>
                <optgroup label="💰 Socioeconomia & Renda">
                    <option value="PCT_RENDA_ACIMA_4SM">💵 Renda Familiar > 4 Salários Mínimos (%)</option>
                    <option value="SALARIO_MEDIO_SM">💼 Salário Médio Formal (em SM)</option>
                </optgroup>
                <optgroup label="👥 Demografia & Escolaridade">
                    <option value="PCT_SUPERIOR">🎓 Ensino Superior Completo/Incomp. (%)</option>
                    <option value="PCT_BAIXA_ESCOLARIDADE">📖 Analfabetos e Lê/Escreve (%)</option>
                    <option value="PCT_FEM">👩 Percentual Feminino (%)</option>
                    <option value="PCT_JOVENS">⚡ Jovens 16-24 anos (%)</option>
                    <option value="PCT_IDOSOS">👴 Idosos 60+ anos (%)</option>
                    <option value="TOTAL_ELEITORES">👥 Total de Eleitores Aptos</option>
                </optgroup>
            </select>
        </div>

        <div>
            <label style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 4px; display: block; font-weight: 600;">Buscar Município:</label>
            <input type="text" id="searchInput" class="search-input" placeholder="Digite nome da cidade (ex: Salvador, Feira...)" />
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="val" style="color:#ef4444;">{pct_lula}%</div>
                <div class="lbl">Lula na Bahia</div>
            </div>
            <div class="stat-card">
                <div class="val" style="color:#3b82f6;">{pct_bols}%</div>
                <div class="lbl">Bolsonaro na Bahia</div>
            </div>
            <div class="stat-card">
                <div class="val" style="color:#f59e0b;">{pct_ue2015}%</div>
                <div class="lbl">Urnas UE2015 (7.989)</div>
            </div>
            <div class="stat-card">
                <div class="val" style="color:#38bdf8;">{total_bahia:,}</div>
                <div class="lbl">Eleitores Aptos</div>
            </div>
        </div>

        <div id="muniDetails">
            <h3 id="detNome" style="color:#38bdf8; font-size:1.1rem; margin-bottom:4px;">Nome do Município</h3>
            <div id="detContent" style="font-size:0.8rem; color:#cbd5e1; line-height:1.45;"></div>
        </div>

        <div style="font-size: 0.7rem; color: #64748b; line-height: 1.3; margin-top: auto;">
            Fontes Integradas: TSE (Votação Nominal 2026, Correspondências e Perfil Eleitorado) e IBGE.
        </div>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const geoData = {geo_json_str};

        const map = L.map('map').setView([-12.9714, -39.5014], 7);
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: '&copy; Esri World Street Map, &copy; TSE, &copy; IBGE',
            maxZoom: 18
        }}).addTo(map);

        let geojsonLayer;
        let legendControl;

        const metricConfigs = {{
            'PCT_LULA': {{
                title: '% Lula (Presidente)',
                grades: [50, 60, 70, 80, 88],
                colors: ['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_BOLSONARO': {{
                title: '% Bolsonaro (Presidente)',
                grades: [15, 20, 25, 35, 45],
                colors: ['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c'],
                format: v => v.toFixed(1) + '%'
            }},
            'MARGEM_PRES': {{
                title: 'Margem Lula x Bolsonaro (%)',
                grades: [20, 35, 50, 65, 75],
                colors: ['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
                format: v => (v > 0 ? '+' : '') + v.toFixed(1) + '%'
            }},
            'PCT_CURY': {{
                title: '% Augusto Cury',
                grades: [1.0, 1.8, 2.5, 3.5, 5.0],
                colors: ['#ffffd4', '#fed98e', '#fe9929', '#d95f0e', '#993404'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_CAIADO': {{
                title: '% Ronaldo Caiado',
                grades: [0.5, 1.0, 1.5, 2.2, 3.5],
                colors: ['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_JERONIMO': {{
                title: '% Jerônimo (Governador)',
                grades: [40, 50, 60, 70, 80],
                colors: ['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_ACM_NETO': {{
                title: '% ACM Neto (Governador)',
                grades: [20, 30, 40, 50, 60],
                colors: ['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c'],
                format: v => v.toFixed(1) + '%'
            }},
            'MARGEM_GOV': {{
                title: 'Margem Jerônimo x ACM Neto (%)',
                grades: [-10, 5, 20, 35, 50],
                colors: ['#bdd7e7', '#fee5d9', '#fcae91', '#de2d26', '#a50f15'],
                format: v => (v > 0 ? '+' : '') + v.toFixed(1) + '%'
            }},
            'PCT_URNAS_UE2015': {{
                title: '% Urnas UE2015 (Anteriores)',
                grades: [1, 20, 50, 80, 100],
                colors: ['#f0fdf4', '#fed7aa', '#fb923c', '#ea580c', '#c2410c'],
                format: v => v.toFixed(1) + '%'
            }},
            'URNAS_UE2015': {{
                title: 'Qtd Urnas UE2015',
                grades: [1, 50, 150, 300, 600],
                colors: ['#fef3c7', '#fde68a', '#f59e0b', '#d97706', '#b45309'],
                format: v => v.toLocaleString('pt-BR')
            }},
            'TOTAL_URNAS': {{
                title: 'Total de Urnas',
                grades: [30, 60, 120, 250, 600],
                colors: ['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c'],
                format: v => v.toLocaleString('pt-BR')
            }},
            'PCT_RENDA_ACIMA_4SM': {{
                title: '% Renda > 4 Salários Mínimos',
                grades: [4, 7, 10, 15, 20],
                colors: ['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c'],
                format: v => v.toFixed(1) + '%'
            }},
            'SALARIO_MEDIO_SM': {{
                title: 'Salário Médio Formal (SM)',
                grades: [1.6, 2.0, 2.5, 3.0, 3.5],
                colors: ['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c'],
                format: v => v.toFixed(1) + ' SM'
            }},
            'PCT_SUPERIOR': {{
                title: '% Ensino Superior',
                grades: [5, 8, 12, 16, 22],
                colors: ['#f2f0f7', '#dadaeb', '#bcbddc', '#9e9ac8', '#6a51a3'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_BAIXA_ESCOLARIDADE': {{
                title: '% Analfabetos / Lê e Escreve',
                grades: [10, 15, 20, 25, 30],
                colors: ['#feedde', '#fdd0a2', '#fdae6b', '#f16913', '#d94801'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_FEM': {{
                title: '% Mulheres',
                grades: [48, 50, 52, 54, 56],
                colors: ['#fde0dd', '#fa9fb5', '#f768a1', '#c51b8a', '#7a0177'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_JOVENS': {{
                title: '% Jovens (16-24 anos)',
                grades: [12, 14, 16, 18, 20],
                colors: ['#fff7bc', '#fee391', '#fec44f', '#fe9929', '#cc4c02'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_IDOSOS': {{
                title: '% Idosos (60+ anos)',
                grades: [18, 22, 26, 30, 34],
                colors: ['#ffffd4', '#fed98e', '#fe9929', '#d95f0e', '#993404'],
                format: v => v.toFixed(1) + '%'
            }},
            'TOTAL_ELEITORES': {{
                title: 'Total de Eleitores',
                grades: [10000, 25000, 50000, 100000, 250000],
                colors: ['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c'],
                format: v => v.toLocaleString('pt-BR')
            }}
        }};

        function getColor(val, config) {{
            const grades = config.grades;
            const colors = config.colors;
            if (val >= grades[4]) return colors[4];
            if (val >= grades[3]) return colors[3];
            if (val >= grades[2]) return colors[2];
            if (val >= grades[1]) return colors[1];
            return colors[0];
        }}

        function style(feature) {{
            const metric = document.getElementById('metricSelect').value;
            const config = metricConfigs[metric];
            const val = feature.properties[metric] || 0;
            return {{
                fillColor: getColor(val, config),
                weight: 1.2,
                opacity: 0.9,
                color: '#1e293b',
                fillOpacity: 0.84
            }};
        }}

        function showDetails(p) {{
            const box = document.getElementById('muniDetails');
            const detNome = document.getElementById('detNome');
            const detContent = document.getElementById('detContent');
            box.style.display = 'block';
            detNome.textContent = p.MUNICIPIO;
            detContent.innerHTML = `
                <div class="section-title">🗳️ VOTAÇÃO PRESIDENTE (1º TURNO)</div>
                🔴 <b>Lula:</b> <span style="color:#ef4444;font-weight:bold;">${{p.PCT_LULA}}%</span> (${{Number(p.VOTOS_LULA).toLocaleString('pt-BR')}} votos)<br>
                🔵 <b>Bolsonaro:</b> <span style="color:#3b82f6;font-weight:bold;">${{p.PCT_BOLSONARO}}%</span> (${{Number(p.VOTOS_BOLSONARO).toLocaleString('pt-BR')}} votos)<br>
                🟡 <b>Cury:</b> ${{p.PCT_CURY}}% | 🟢 <b>Caiado:</b> ${{p.PCT_CAIADO}}%<br>
                
                <div class="section-title">🏛️ VOTAÇÃO GOVERNADOR</div>
                🔴 <b>Jerônimo:</b> ${{p.PCT_JERONIMO}}% (${{Number(p.VOTOS_JERONIMO).toLocaleString('pt-BR')}} votos)<br>
                🔵 <b>ACM Neto:</b> ${{p.PCT_ACM_NETO}}% (${{Number(p.VOTOS_ACM_NETO).toLocaleString('pt-BR')}} votos)<br>

                <div class="section-title">⚙️ MODELOS DE URNA (AUDITORIA)</div>
                ⚠️ <b>Urnas UE2015 (Anteriores):</b> <span style="color:#f59e0b;font-weight:bold;">${{p.PCT_URNAS_UE2015}}%</span> (${{p.URNAS_UE2015}} de ${{p.TOTAL_URNAS}} seções)<br>
                ✅ <b>Urnas UE2020 (Novas):</b> ${{p.URNAS_UE2020}} seções<br>

                <div class="section-title">💰 RENDA & DEMOGRAFIA</div>
                💵 <b>Renda > 4 SM:</b> <span style="color:#22c55e;font-weight:bold;">${{p.PCT_RENDA_ACIMA_4SM}}%</span> | <b>Sal. Médio:</b> ${{p.SALARIO_MEDIO_SM}} SM<br>
                🎓 <b>Ensino Superior:</b> ${{p.PCT_SUPERIOR}}% | <b>Analf./Lê:</b> ${{p.PCT_BAIXA_ESCOLARIDADE}}%<br>
                👥 <b>Eleitorado Apto:</b> ${{Number(p.TOTAL_ELEITORES).toLocaleString('pt-BR')}} | 👩 <b>Mulheres:</b> ${{p.PCT_FEM}}%
            `;
        }}

        function onEachFeature(feature, layer) {{
            layer.on({{
                mouseover: e => {{
                    const l = e.target;
                    l.setStyle({{ weight: 3, color: '#38bdf8', fillOpacity: 0.95 }});
                    l.bringToFront();
                    showDetails(feature.properties);
                }},
                mouseout: e => {{
                    geojsonLayer.resetStyle(e.target);
                }},
                click: e => {{
                    map.fitBounds(e.target.getBounds());
                    showDetails(feature.properties);
                }}
            }});
        }}

        function updateMap() {{
            if (geojsonLayer) map.removeLayer(geojsonLayer);
            if (legendControl) map.removeControl(legendControl);

            geojsonLayer = L.geoJson(geoData, {{
                style: style,
                onEachFeature: onEachFeature
            }}).addTo(map);

            const metric = document.getElementById('metricSelect').value;
            const config = metricConfigs[metric];

            legendControl = L.control({{ position: 'bottomright' }});
            legendControl.onAdd = function() {{
                const div = L.DomUtil.create('div', 'legend');
                const grades = config.grades;
                const colors = config.colors;
                div.innerHTML = `<b>${{config.title}}</b><br>`;
                div.innerHTML += `<i style="background:${{colors[0]}}"></i> < ${{grades[0]}}<br>`;
                for (let i = 0; i < grades.length - 1; i++) {{
                    div.innerHTML += `<i style="background:${{colors[i+1]}}"></i> ${{grades[i]}} &ndash; ${{grades[i+1]}}<br>`;
                }}
                div.innerHTML += `<i style="background:${{colors[4]}}"></i> ≥ ${{grades[4]}}<br>`;
                return div;
            }};
            legendControl.addTo(map);
        }}

        document.getElementById('metricSelect').addEventListener('change', updateMap);
        
        document.getElementById('searchInput').addEventListener('input', function(e) {{
            const searchVal = e.target.value.toLowerCase().trim();
            if (!searchVal) return;
            geojsonLayer.eachLayer(layer => {{
                const name = (layer.feature.properties.MUNICIPIO || '').toLowerCase();
                if (name.includes(searchVal)) {{
                    map.fitBounds(layer.getBounds());
                    layer.fire('mouseover');
                }}
            }});
        }});

        updateMap();
    </script>
</body>
</html>"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Dashboard Integrado 2D gerado: {output_path}")

def gerar_dashboard_3d_integrado_html(geo_json_str, df, output_path):
    html_3d = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visualização 3D Integrada: Votos, Urnas & Demografia - Bahia 2026</title>
    <script src="https://unpkg.com/deck.gl@8.9.35/dist.min.js"></script>
    <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
    <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }}
        body {{ width: 100vw; height: 100vh; overflow: hidden; background: #0b0f19; }}
        #container {{ width: 100%; height: 100%; position: relative; }}
        #panel {{
            position: absolute; top: 20px; left: 20px; z-index: 10;
            background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 16px;
            padding: 20px 24px; color: #f8fafc; max-width: 380px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }}
        .badge {{
            display: inline-block; padding: 4px 10px; border-radius: 9999px;
            font-size: 0.72rem; font-weight: 700; background: #38bdf8; color: #000;
        }}
        h2 {{ font-size: 1.25rem; font-weight: 700; margin: 8px 0 4px 0; }}
        p {{ font-size: 0.82rem; color: #94a3b8; line-height: 1.4; }}
        select {{
            width: 100%; padding: 10px 12px; background: #1e293b; border: 1px solid #334155;
            border-radius: 8px; color: #f8fafc; font-size: 0.88rem; margin-top: 10px; outline: none;
        }}
        #tooltip {{
            position: absolute; z-index: 20; pointer-events: none;
            background: rgba(15, 23, 42, 0.95); color: #fff; padding: 12px 16px;
            border-radius: 10px; font-size: 0.82rem; border: 1px solid #38bdf8;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: none; max-width: 320px;
        }}
        .instructions {{ margin-top: 12px; font-size: 0.72rem; color: #cbd5e1; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px; }}
    </style>
</head>
<body>
    <div id="container">
        <div id="panel">
            <span class="badge">3D ELEVAÇÃO & COROPLÉTICO</span>
            <h2>Eleições Bahia 2026 3D</h2>
            <p>A elevação tridimensional e as cores dos 417 municípios representam a dimensão selecionada.</p>
            
            <select id="metricSelect">
                <option value="PCT_LULA">🔴 Lula Presidente (% Votos)</option>
                <option value="PCT_BOLSONARO">🔵 Flávio Bolsonaro (% Votos)</option>
                <option value="PCT_URNAS_UE2015">⚠️ Urnas UE2015 Anteriores (%)</option>
                <option value="PCT_RENDA_ACIMA_4SM">💰 Renda > 4 Salários Mínimos (%)</option>
                <option value="PCT_SUPERIOR">🎓 Ensino Superior (%)</option>
                <option value="TOTAL_ELEITORES">👥 Total de Eleitores (Elevação)</option>
            </select>

            <div class="instructions">
                🖱️ <b>Navegação 3D:</b><br>
                • <b>Botão Direito ou Ctrl + Arrastar:</b> Inclinar e girar em 3D<br>
                • <b>Botão Esquerdo:</b> Mover o mapa<br>
                • <b>Scroll:</b> Zoom
            </div>
        </div>
        <div id="tooltip"></div>
    </div>

    <script>
        const geoData = {geo_json_str};
        const tooltip = document.getElementById('tooltip');

        const mapStyle = {{
            version: 8,
            sources: {{
                'esri-tiles': {{
                    type: 'raster',
                    tiles: [
                        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}'
                    ],
                    tileSize: 256,
                    attribution: '© Esri World Street Map, © TSE, © IBGE'
                }}
            }},
            layers: [
                {{
                    id: 'esri-tiles-layer',
                    type: 'raster',
                    source: 'esri-tiles',
                    minzoom: 0,
                    maxzoom: 19
                }}
            ]
        }};

        let deckgl;

        function getElevation(feature, metric) {{
            const val = feature.properties[metric] || 0;
            if (metric === 'TOTAL_ELEITORES') return Math.min(val * 0.04, 150000);
            if (metric === 'PCT_URNAS_UE2015') return val * 1500;
            if (metric === 'PCT_RENDA_ACIMA_4SM') return val * 4500;
            return val * 1500;
        }}

        function getFillColor(feature, metric) {{
            const val = feature.properties[metric] || 0;
            if (metric === 'PCT_LULA') {{
                if (val > 80) return [165, 15, 21, 230];
                if (val > 70) return [222, 45, 38, 220];
                if (val > 60) return [251, 106, 74, 220];
                if (val > 50) return [252, 174, 145, 200];
                return [254, 229, 217, 180];
            }}
            if (metric === 'PCT_BOLSONARO') {{
                if (val > 40) return [8, 81, 156, 230];
                if (val > 30) return [49, 130, 189, 220];
                if (val > 20) return [107, 174, 214, 220];
                return [189, 215, 231, 180];
            }}
            if (metric === 'PCT_URNAS_UE2015') {{
                if (val > 80) return [194, 65, 12, 230];
                if (val > 40) return [234, 88, 12, 220];
                if (val > 1) return [245, 158, 11, 220];
                return [56, 189, 248, 120];
            }}
            if (metric === 'PCT_RENDA_ACIMA_4SM') {{
                if (val > 15) return [0, 109, 44, 230];
                if (val > 10) return [49, 163, 84, 220];
                if (val > 7) return [116, 196, 118, 220];
                return [186, 228, 179, 200];
            }}
            return [56, 189, 248, 220];
        }}

        function initDeck() {{
            const metric = document.getElementById('metricSelect').value;

            const layer = new deck.GeoJsonLayer({{
                id: 'integrated-3d-layer',
                data: geoData,
                extruded: true,
                filled: true,
                stroked: true,
                lineWidthMinPixels: 1.5,
                getLineColor: [15, 23, 42, 255],
                getElevation: f => getElevation(f, metric),
                getFillColor: f => getFillColor(f, metric),
                pickable: true,
                autoHighlight: true,
                highlightColor: [255, 255, 255, 100],
                onHover: info => {{
                    if (info.object) {{
                        const p = info.object.properties;
                        tooltip.style.display = 'block';
                        tooltip.style.left = (info.x + 15) + 'px';
                        tooltip.style.top = (info.y + 15) + 'px';
                        tooltip.innerHTML = `
                            <b style="color:#38bdf8;font-size:1.05rem;">${{p.MUNICIPIO}}</b><br>
                            🔴 <b>Lula:</b> ${{p.PCT_LULA}}% (${{Number(p.VOTOS_LULA).toLocaleString('pt-BR')}} votos)<br>
                            🔵 <b>Bolsonaro:</b> ${{p.PCT_BOLSONARO}}% (${{Number(p.VOTOS_BOLSONARO).toLocaleString('pt-BR')}} votos)<br>
                            ⚠️ <b>Urnas UE2015:</b> ${{p.PCT_URNAS_UE2015}}% (${{p.URNAS_UE2015}} de ${{p.TOTAL_URNAS}} seções)<br>
                            💰 <b>Renda > 4 SM:</b> ${{p.PCT_RENDA_ACIMA_4SM}}%<br>
                            🎓 <b>Superior:</b> ${{p.PCT_SUPERIOR}}% | 👥 <b>Eleitores:</b> ${{Number(p.TOTAL_ELEITORES).toLocaleString('pt-BR')}}
                        `;
                    }} else {{
                        tooltip.style.display = 'none';
                    }}
                }}
            }});

            if (!deckgl) {{
                deckgl = new deck.DeckGL({{
                    container: 'container',
                    map: maplibregl,
                    mapStyle: mapStyle,
                    initialViewState: {{
                        longitude: -39.2,
                        latitude: -12.9,
                        zoom: 6.8,
                        pitch: 52,
                        bearing: -15,
                        maxPitch: 85
                    }},
                    controller: true,
                    layers: [layer]
                }});
            }} else {{
                deckgl.setProps({{ layers: [layer] }});
            }}
        }}

        document.getElementById('metricSelect').addEventListener('change', initDeck);
        initDeck();
    </script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_3d)
    print(f"[OK] Dashboard Integrado 3D Deck.gl gerado: {output_path}")

if __name__ == "__main__":
    generate_integrated_dashboard()
