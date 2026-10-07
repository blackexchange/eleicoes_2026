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

def generate_demographics_dashboard():
    output_dir = "data/processed/google_maps"
    os.makedirs(output_dir, exist_ok=True)
    
    con = duckdb.connect("data/processed/eleicoes.duckdb")
    
    # 1. Carregar dados de Renda e Salários Oficiais IBGE
    with open("data/geo/renda_4sm_municipios_ba.json", "r", encoding="utf-8") as f:
        renda_dict = json.load(f)
        
    df_renda = pd.DataFrame(list(renda_dict.values()))
    df_renda["MUNICIPIO_NORM"] = df_renda["MUNICIPIO"].apply(normalize_name)
    con.register("df_renda_temp", df_renda)

    # 2. Agregação rica do Eleitorado + Renda no DuckDB
    con.execute("""
        CREATE OR REPLACE TABLE perfil_demografico_municipios_BA_2026 AS
        WITH tse_agg AS (
            SELECT 
                NM_MUNICIPIO AS MUNICIPIO,
                CAST(SUM(QT_ELEITORES) AS BIGINT) AS TOTAL_ELEITORES,
                CAST(SUM(CASE WHEN DS_GENERO = 'FEMININO' THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_FEM,
                CAST(SUM(CASE WHEN DS_GENERO = 'MASCULINO' THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_MASC,
                ROUND(SUM(CASE WHEN DS_GENERO = 'FEMININO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_FEM,
                ROUND(SUM(CASE WHEN DS_GENERO = 'MASCULINO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_MASC,
                
                -- Escolaridade
                CAST(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('SUPERIOR COMPLETO', 'SUPERIOR INCOMPLETO') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_SUPERIOR,
                ROUND(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('SUPERIOR COMPLETO', 'SUPERIOR INCOMPLETO') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_SUPERIOR,
                
                CAST(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('ANALFABETO', 'LÊ E ESCREVE') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_BAIXA_ESCOLARIDADE,
                ROUND(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('ANALFABETO', 'LÊ E ESCREVE') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_BAIXA_ESCOLARIDADE,

                CAST(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('ENSINO MÉDIO COMPLETO', 'ENSINO MÉDIO INCOMPLETO') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_MEDIO,
                ROUND(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('ENSINO MÉDIO COMPLETO', 'ENSINO MÉDIO INCOMPLETO') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_MEDIO,

                -- Idade
                CAST(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('16 ANOS', '17 ANOS', '18 A 20 ANOS', '21 A 24 ANOS') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_JOVENS,
                ROUND(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('16 ANOS', '17 ANOS', '18 A 20 ANOS', '21 A 24 ANOS') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_JOVENS,
                
                CAST(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('60 A 69 ANOS', '70 A 79 ANOS', '80 ANOS OU MAIS') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_IDOSOS,
                ROUND(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('60 A 69 ANOS', '70 A 79 ANOS', '80 ANOS OU MAIS') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_IDOSOS,

                -- Biometria e Deficiência
                CAST(SUM(QT_ELEITORES_BIOMETRIA) AS BIGINT) AS ELEITORES_BIOMETRIA,
                ROUND(SUM(QT_ELEITORES_BIOMETRIA) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_BIOMETRIA,
                
                CAST(SUM(QT_ELEITORES_DEFICIENCIA) AS BIGINT) AS ELEITORES_DEFICIENCIA,
                ROUND(SUM(QT_ELEITORES_DEFICIENCIA) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_DEFICIENCIA
            FROM perfil_eleitorado_2026_BA
            GROUP BY NM_MUNICIPIO
        )
        SELECT 
            t.*,
            COALESCE(r.PCT_RENDA_ACIMA_4SM, 5.0) AS PCT_RENDA_ACIMA_4SM,
            COALESCE(r.SALARIO_MEDIO_SM, 1.8) AS SALARIO_MEDIO_SM,
            COALESCE(r.RENDIMENTO_DOMICILIAR_RS, 1500.0) AS RENDIMENTO_DOMICILIAR_RS
        FROM tse_agg t
        LEFT JOIN df_renda_temp r ON t.MUNICIPIO = r.MUNICIPIO_NORM
        ORDER BY t.TOTAL_ELEITORES DESC
    """)
    
    df_muni = con.execute("SELECT * FROM perfil_demografico_municipios_BA_2026").df()
    
    # Exportar CSV e Parquet
    csv_path = "data/processed/perfil_demografico_municipios_BA_2026.csv"
    parquet_path = "data/processed/perfil_demografico_municipios_BA_2026.parquet"
    df_muni.to_csv(csv_path, index=False, encoding="utf-8")
    df_muni.to_parquet(parquet_path, index=False)
    print(f"[OK] Exportados dados demográficos municipais com renda: {csv_path} e {parquet_path}")

    # 3. Carregar GeoJSON dos 417 municípios e lista IBGE
    with open("data/geo/bahia_municipios.geojson", "r", encoding="utf-8") as f:
        geo_data = json.load(f)
    
    with open("data/geo/ibge_municipios_ba.json", "r", encoding="utf-8") as f:
        ibge_list = json.load(f)

    ibge_map = {str(item["id"]): normalize_name(item["nome"]) for item in ibge_list}
    ibge_display = {str(item["id"]): item["nome"] for item in ibge_list}

    tse_dict = {}
    for _, row in df_muni.iterrows():
        norm_key = normalize_name(row["MUNICIPIO"])
        tse_dict[norm_key] = row.to_dict()
    
    # Enriquecer propriedades do GeoJSON
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
            
    print(f"[OK] {matched}/417 municípios combinados com sucesso na malha geográfica.")
    
    enriched_geo_str = json.dumps(geo_data, ensure_ascii=False)
    
    # 4. Gerar Dashboards Coropléticos
    gerar_dashboard_html(enriched_geo_str, df_muni, os.path.join(output_dir, "mapa_demografico_bahia_2026.html"))
    gerar_3d_demografico_html(enriched_geo_str, df_muni, os.path.join(output_dir, "mapa_3d_demografico_bahia.html"))

def gerar_dashboard_html(geo_json_str, df_muni, output_path):
    total_bahia = int(df_muni["TOTAL_ELEITORES"].sum())
    total_fem = int(df_muni["ELEITORES_FEM"].sum())
    pct_fem = round(total_fem * 100.0 / total_bahia, 2)
    total_sup = int(df_muni["ELEITORES_SUPERIOR"].sum())
    pct_sup = round(total_sup * 100.0 / total_bahia, 2)
    media_renda_4sm = round(float(df_muni["PCT_RENDA_ACIMA_4SM"].mean()), 2)
    
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perfil Demográfico e Socioeconômico - Bahia 2026</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }}
        body {{ display: flex; height: 100vh; overflow: hidden; background: #0b0f19; color: #f8fafc; }}
        #sidebar {{
            width: 400px; background: #0f172a; padding: 22px; display: flex; flex-direction: column;
            gap: 14px; box-shadow: 4px 0 24px rgba(0,0,0,0.5); z-index: 1000; overflow-y: auto;
            border-right: 1px solid rgba(255,255,255,0.08);
        }}
        #map {{ flex: 1; height: 100%; }}
        .badge {{
            display: inline-block; padding: 4px 10px; border-radius: 9999px;
            font-size: 0.75rem; font-weight: 700; background: #38bdf8; color: #000;
        }}
        .metric-select, .search-input {{
            width: 100%; padding: 10px 12px; background: #1e293b; border: 1px solid #334155;
            border-radius: 8px; color: #f8fafc; font-size: 0.9rem; font-weight: 600; outline: none;
            transition: 0.2s;
        }}
        .metric-select:focus, .search-input:focus {{ border-color: #38bdf8; }}
        .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
        .stat-card {{
            background: #1e293b; padding: 10px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);
        }}
        .stat-card .val {{ font-size: 1.25rem; font-weight: 700; color: #38bdf8; }}
        .stat-card .lbl {{ font-size: 0.75rem; color: #94a3b8; }}
        #muniDetails {{
            background: #1e293b; border-radius: 10px; padding: 14px; border: 1px solid #38bdf8;
            display: none;
        }}
        .legend {{
            padding: 10px 14px; background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(8px);
            border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); color: #fff; font-size: 0.8rem;
            line-height: 1.6; box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }}
        .legend i {{ width: 16px; height: 16px; float: left; margin-right: 8px; opacity: 0.85; border-radius: 3px; }}
    </style>
</head>
<body>
    <div id="sidebar">
        <div>
            <span class="badge">ELEIÇÕES 2026 - DEMOGRAFIA & RENDA</span>
            <h2 style="font-size: 1.3rem; margin-top: 6px; font-weight: 700;">Eleitorado da Bahia</h2>
            <p style="font-size: 0.8rem; color: #94a3b8; margin-top: 2px;">Mapa Coroplético Interativo (417 municípios)</p>
        </div>

        <div>
            <label style="font-size: 0.78rem; color: #94a3b8; margin-bottom: 4px; display: block; font-weight: 600;">Selecione o Indicador Temático:</label>
            <select id="metricSelect" class="metric-select">
                <option value="PCT_RENDA_ACIMA_4SM">💰 Renda Acima de 4 Salários Mínimos (%)</option>
                <option value="SALARIO_MEDIO_SM">💵 Salário Médio Formal (em SM)</option>
                <option value="PCT_SUPERIOR">🎓 Ensino Superior Completo/Incomp. (%)</option>
                <option value="TOTAL_ELEITORES">👥 Total de Eleitores Aptos</option>
                <option value="PCT_FEM">👩 Percentual Feminino (%)</option>
                <option value="PCT_BAIXA_ESCOLARIDADE">📖 Analfabetos e Lê/Escreve (%)</option>
                <option value="PCT_JOVENS">⚡ Jovens de 16 a 24 anos (%)</option>
                <option value="PCT_IDOSOS">👴 Idosos 60+ anos (%)</option>
                <option value="PCT_BIOMETRIA">👆 Biometria Cadastrada (%)</option>
            </select>
        </div>

        <div>
            <label style="font-size: 0.78rem; color: #94a3b8; margin-bottom: 4px; display: block; font-weight: 600;">Buscar Município:</label>
            <input type="text" id="searchInput" class="search-input" placeholder="Digite o nome da cidade..." />
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="val">{total_bahia:,}</div>
                <div class="lbl">Eleitorado BA</div>
            </div>
            <div class="stat-card">
                <div class="val">{pct_sup}%</div>
                <div class="lbl">Ensino Superior</div>
            </div>
            <div class="stat-card">
                <div class="val">{pct_fem}%</div>
                <div class="lbl">Mulheres BA</div>
            </div>
            <div class="stat-card">
                <div class="val">{media_renda_4sm}%</div>
                <div class="lbl">Média Renda > 4 SM</div>
            </div>
        </div>

        <div id="muniDetails">
            <h3 id="detNome" style="color:#38bdf8; font-size:1.1rem; margin-bottom:4px;">Nome do Município</h3>
            <div id="detContent" style="font-size:0.82rem; color:#cbd5e1; line-height:1.45;"></div>
        </div>

        <div style="font-size: 0.72rem; color: #64748b; line-height: 1.4; margin-top: auto;">
            Fontes: Microdados TSE (Perfil Eleitorado 2026), Censo Demográfico & Pesquisa RAIS/Cidades IBGE.
        </div>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const geoData = {geo_json_str};

        const map = L.map('map').setView([-12.9714, -39.5014], 7);
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: '&copy; Esri World Street Map, &copy; IBGE',
            maxZoom: 18
        }}).addTo(map);

        let geojsonLayer;
        let legendControl;

        const metricConfigs = {{
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
            'TOTAL_ELEITORES': {{
                title: 'Total de Eleitores',
                grades: [10000, 25000, 50000, 100000, 250000],
                colors: ['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c'],
                format: v => v.toLocaleString('pt-BR')
            }},
            'PCT_FEM': {{
                title: '% Mulheres',
                grades: [48, 50, 52, 54, 56],
                colors: ['#fde0dd', '#fa9fb5', '#f768a1', '#c51b8a', '#7a0177'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_BAIXA_ESCOLARIDADE': {{
                title: '% Analfabetos / Lê e Escreve',
                grades: [10, 15, 20, 25, 30],
                colors: ['#feedde', '#fdd0a2', '#fdae6b', '#f16913', '#d94801'],
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
            'PCT_BIOMETRIA': {{
                title: '% Biometria',
                grades: [80, 85, 90, 93, 96],
                colors: ['#e5f5f9', '#99d8c9', '#41ae76', '#238b45', '#005824'],
                format: v => v.toFixed(1) + '%'
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

        function showDetails(props) {{
            const box = document.getElementById('muniDetails');
            const detNome = document.getElementById('detNome');
            const detContent = document.getElementById('detContent');
            box.style.display = 'block';
            detNome.textContent = props.MUNICIPIO;
            detContent.innerHTML = `
                <b>💰 Renda > 4 Salários Mínimos:</b> <span style="color:#22c55e;font-weight:bold;">${{props.PCT_RENDA_ACIMA_4SM}}%</span><br>
                <b>💵 Salário Médio Formal:</b> ${{props.SALARIO_MEDIO_SM}} SM<br>
                <b>🎓 Ensino Superior:</b> ${{props.PCT_SUPERIOR}}%<br>
                <b>👥 Total Eleitores:</b> ${{Number(props.TOTAL_ELEITORES).toLocaleString('pt-BR')}}<br>
                <b>👩 Mulheres:</b> ${{props.PCT_FEM}}% (${{Number(props.ELEITORES_FEM).toLocaleString('pt-BR')}})<br>
                <b>👨 Homens:</b> ${{props.PCT_MASC}}% (${{Number(props.ELEITORES_MASC).toLocaleString('pt-BR')}})<br>
                <b>📖 Analfabetos / Lê e Escreve:</b> ${{props.PCT_BAIXA_ESCOLARIDADE}}%<br>
                <b>⚡ Jovens (16-24):</b> ${{props.PCT_JOVENS}}%<br>
                <b>👴 Idosos (60+):</b> ${{props.PCT_IDOSOS}}%<br>
                <b>👆 Biometria:</b> ${{props.PCT_BIOMETRIA}}%
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
    print(f"[OK] Dashboard Coroplético Demográfico & Renda gerado: {output_path}")

def gerar_3d_demografico_html(geo_json_str, df_muni, output_path):
    html_3d = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Demografia e Renda 3D - Municípios da Bahia 2026</title>
    <script src="https://unpkg.com/deck.gl@8.9.35/dist.min.js"></script>
    <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
    <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }
        body { width: 100vw; height: 100vh; overflow: hidden; background: #0b0f19; }
        #container { width: 100%; height: 100%; position: relative; }
        #panel {
            position: absolute; top: 20px; left: 20px; z-index: 10;
            background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 16px;
            padding: 20px 24px; color: #f8fafc; max-width: 360px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }
        .badge {
            display: inline-block; padding: 4px 10px; border-radius: 9999px;
            font-size: 0.75rem; font-weight: 700; background: #38bdf8; color: #000;
        }
        h2 { font-size: 1.25rem; font-weight: 700; margin: 8px 0 4px 0; }
        p { font-size: 0.85rem; color: #94a3b8; line-height: 1.4; }
        select {
            width: 100%; padding: 10px 12px; background: #1e293b; border: 1px solid #334155;
            border-radius: 8px; color: #f8fafc; font-size: 0.9rem; margin-top: 10px; outline: none;
        }
        #tooltip {
            position: absolute; z-index: 20; pointer-events: none;
            background: rgba(15, 23, 42, 0.95); color: #fff; padding: 12px 16px;
            border-radius: 10px; font-size: 0.85rem; border: 1px solid #38bdf8;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: none; max-width: 300px;
        }
        #legendBox {
            margin-top: 12px; padding: 12px; background: rgba(0,0,0,0.35);
            border-radius: 10px; border: 1px solid rgba(255,255,255,0.08); font-size: 0.78rem;
        }
        .color-ramp {
            height: 10px; border-radius: 5px; margin: 6px 0;
            display: flex; overflow: hidden;
        }
        .color-ramp span { flex: 1; height: 100%; }
        .ramp-labels { display: flex; justify-content: space-between; font-size: 0.72rem; color: #94a3b8; }
        .instructions { margin-top: 12px; font-size: 0.75rem; color: #cbd5e1; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px; }
    </style>
</head>
<body>
    <div id="container">
        <div id="panel">
            <span class="badge">DEMOGRAFIA & RENDA 3D GPU</span>
            <h2>Eleitorado da Bahia 3D</h2>
            <p>A elevação e as cores dos 417 municípios reagem dinamicamente à métrica selecionada.</p>
            
            <select id="metricSelect">
                <option value="PCT_RENDA_ACIMA_4SM">💰 Renda > 4 Salários Mínimos (%)</option>
                <option value="SALARIO_MEDIO_SM">💵 Salário Médio Formal (SM)</option>
                <option value="PCT_SUPERIOR">🎓 Ensino Superior (%)</option>
                <option value="TOTAL_ELEITORES">👥 Total de Eleitores</option>
                <option value="PCT_FEM">👩 Percentual Feminino (%)</option>
                <option value="PCT_JOVENS">⚡ Jovens 16-24 anos (%)</option>
                <option value="PCT_IDOSOS">👴 Idosos 60+ anos (%)</option>
                <option value="PCT_BIOMETRIA">👆 Biometria Cadastrada (%)</option>
            </select>

            <div id="legendBox">
                <div id="legendTitle" style="font-weight: 700; color: #38bdf8;">💰 Renda > 4 Salários Mínimos</div>
                <div class="color-ramp" id="legendRamp"></div>
                <div class="ramp-labels">
                    <span id="legendMin">Min</span>
                    <span id="legendMid">Média</span>
                    <span id="legendMax">Max</span>
                </div>
            </div>

            <div class="instructions">
                🖱️ <b>Navegação 3D:</b><br>
                • <b>Botão Direito ou Ctrl + Arrastar:</b> Inclinar e girar em 3D<br>
                • <b>Botão Esquerdo:</b> Mover o mapa<br>
                • <b>Scroll:</b> Zoom in/out
            </div>
        </div>
        <div id="tooltip"></div>
    </div>

    <script>
        const geoData = __GEO_DATA__;
        const tooltip = document.getElementById('tooltip');

        const METRIC_CONFIGS = {
            'PCT_RENDA_ACIMA_4SM': {
                name: '💰 Renda > 4 Salários Mínimos (%)',
                colors: ['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c'],
                scale: 5500,
                minLbl: '3%', midLbl: '8%', maxLbl: '18%+',
                getColor: v => {
                    if (v >= 15) return [0, 109, 44, 245];
                    if (v >= 10) return [49, 163, 84, 235];
                    if (v >= 7) return [116, 196, 118, 220];
                    if (v >= 5) return [186, 228, 179, 210];
                    return [237, 248, 233, 190];
                },
                getElevation: v => v * 5500
            },
            'SALARIO_MEDIO_SM': {
                name: '💵 Salário Médio Formal (SM)',
                colors: ['#e0f3f8', '#99d5e4', '#45b4d3', '#157fad', '#08457e'],
                scale: 35000,
                minLbl: '1.2 SM', midLbl: '2.0 SM', maxLbl: '3.8+ SM',
                getColor: v => {
                    if (v >= 3.0) return [8, 69, 126, 245];
                    if (v >= 2.3) return [21, 127, 173, 235];
                    if (v >= 1.8) return [69, 180, 211, 220];
                    if (v >= 1.5) return [153, 213, 228, 210];
                    return [224, 243, 248, 190];
                },
                getElevation: v => v * 35000
            },
            'PCT_SUPERIOR': {
                name: '🎓 Ensino Superior (%)',
                colors: ['#f2f0f7', '#cbc9e2', '#9e9ac8', '#756bb1', '#54278f'],
                scale: 5500,
                minLbl: '4%', midLbl: '10%', maxLbl: '22%+',
                getColor: v => {
                    if (v >= 16) return [84, 39, 143, 245];
                    if (v >= 12) return [117, 107, 177, 235];
                    if (v >= 8) return [158, 154, 200, 220];
                    if (v >= 6) return [203, 201, 226, 210];
                    return [242, 240, 247, 190];
                },
                getElevation: v => v * 5500
            },
            'TOTAL_ELEITORES': {
                name: '👥 Total de Eleitores',
                colors: ['#edf8fb', '#b3cde3', '#8c96c6', '#8856a7', '#810f7c'],
                scale: 0.07,
                minLbl: '5 mil', midLbl: '30 mil', maxLbl: '100 mil+',
                getColor: v => {
                    if (v >= 100000) return [129, 15, 124, 245];
                    if (v >= 50000) return [136, 86, 167, 235];
                    if (v >= 25000) return [140, 150, 198, 220];
                    if (v >= 10000) return [179, 205, 227, 210];
                    return [237, 248, 251, 190];
                },
                getElevation: v => Math.min(v * 0.07, 160000)
            },
            'PCT_FEM': {
                name: '👩 Percentual Feminino (%)',
                colors: ['#fde0dd', '#fa9fb5', '#f768a1', '#c51b8a', '#7a0177'],
                scale: 2500,
                minLbl: '48%', midLbl: '52%', maxLbl: '55%+',
                getColor: v => {
                    if (v >= 53.5) return [122, 1, 119, 245];
                    if (v >= 52.5) return [197, 27, 138, 235];
                    if (v >= 51.5) return [247, 104, 161, 220];
                    if (v >= 50.5) return [250, 159, 181, 210];
                    return [253, 224, 221, 190];
                },
                getElevation: v => (v - 48) * 15000
            },
            'PCT_JOVENS': {
                name: '⚡ Jovens 16-24 anos (%)',
                colors: ['#ffffcc', '#c7e9b4', '#7fcdbb', '#41b6c4', '#225ea8'],
                scale: 5000,
                minLbl: '12%', midLbl: '17%', maxLbl: '24%+',
                getColor: v => {
                    if (v >= 20) return [34, 94, 168, 245];
                    if (v >= 18) return [65, 182, 196, 235];
                    if (v >= 16) return [127, 205, 187, 220];
                    if (v >= 14) return [199, 233, 180, 210];
                    return [255, 255, 204, 190];
                },
                getElevation: v => v * 5000
            },
            'PCT_IDOSOS': {
                name: '👴 Idosos 60+ anos (%)',
                colors: ['#ffffd4', '#fed98e', '#fe9929', '#d95f0e', '#993404'],
                scale: 4500,
                minLbl: '18%', midLbl: '25%', maxLbl: '34%+',
                getColor: v => {
                    if (v >= 30) return [153, 52, 4, 245];
                    if (v >= 26) return [217, 95, 14, 235];
                    if (v >= 22) return [254, 153, 41, 220];
                    if (v >= 19) return [254, 217, 142, 210];
                    return [255, 255, 212, 190];
                },
                getElevation: v => v * 4500
            },
            'PCT_BIOMETRIA': {
                name: '👆 Biometria Cadastrada (%)',
                colors: ['#ece7f2', '#d0d1e6', '#a6bddb', '#67a9cf', '#02818a'],
                scale: 1800,
                minLbl: '75%', midLbl: '88%', maxLbl: '98%+',
                getColor: v => {
                    if (v >= 95) return [2, 129, 138, 245];
                    if (v >= 90) return [103, 169, 207, 235];
                    if (v >= 85) return [166, 189, 219, 220];
                    if (v >= 80) return [208, 209, 230, 210];
                    return [236, 231, 242, 190];
                },
                getElevation: v => v * 1800
            }
        };

        const mapStyle = {
            version: 8,
            sources: {
                'esri-tiles': {
                    type: 'raster',
                    tiles: [
                        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}'
                    ],
                    tileSize: 256,
                    attribution: '© Esri World Street Map, © IBGE'
                }
            },
            layers: [
                {
                    id: 'esri-tiles-layer',
                    type: 'raster',
                    source: 'esri-tiles',
                    minzoom: 0,
                    maxzoom: 19
                }
            ]
        };

        let deckgl = null;
        let currentMetric = 'PCT_RENDA_ACIMA_4SM';

        function updateLegend(metric) {
            const conf = METRIC_CONFIGS[metric];
            if (!conf) return;
            document.getElementById('legendTitle').textContent = conf.name;
            document.getElementById('legendMin').textContent = conf.minLbl;
            document.getElementById('legendMid').textContent = conf.midLbl;
            document.getElementById('legendMax').textContent = conf.maxLbl;
            
            const ramp = document.getElementById('legendRamp');
            ramp.innerHTML = conf.colors.map(c => `<span style="background:${c}"></span>`).join('');
        }

        function createDeckLayer(metric) {
            const conf = METRIC_CONFIGS[metric];
            return new deck.GeoJsonLayer({
                id: 'bahia-3d-demographics-layer',
                data: geoData,
                extruded: true,
                filled: true,
                stroked: true,
                lineWidthMinPixels: 1.2,
                getLineColor: [15, 23, 42, 255],
                getElevation: f => {
                    const val = Number(f.properties ? f.properties[metric] : 0) || 0;
                    return conf.getElevation(val);
                },
                getFillColor: f => {
                    const val = Number(f.properties ? f.properties[metric] : 0) || 0;
                    return conf.getColor(val);
                },
                updateTriggers: {
                    getElevation: [metric],
                    getFillColor: [metric]
                },
                transitions: {
                    getElevation: 700,
                    getFillColor: 700
                },
                pickable: true,
                autoHighlight: true,
                highlightColor: [255, 255, 255, 120],
                onHover: info => {
                    if (info.object && info.object.properties) {
                        const p = info.object.properties;
                        tooltip.style.display = 'block';
                        tooltip.style.left = (info.x + 15) + 'px';
                        tooltip.style.top = (info.y + 15) + 'px';
                        tooltip.innerHTML = `
                            <b style="color:#38bdf8;font-size:1.05rem;">${p.MUNICIPIO || 'Município'}</b><br>
                            <b>💰 Renda > 4 SM:</b> <span style="color:#22c55e;font-weight:bold;">${p.PCT_RENDA_ACIMA_4SM || 0}%</span><br>
                            <b>💵 Salário Médio:</b> ${p.SALARIO_MEDIO_SM || 0} SM<br>
                            <b>🎓 Ensino Superior:</b> ${p.PCT_SUPERIOR || 0}%<br>
                            <b>👥 Eleitores:</b> ${Number(p.TOTAL_ELEITORES || 0).toLocaleString('pt-BR')}<br>
                            <b>👩 Mulheres:</b> ${p.PCT_FEM || 0}%<br>
                            <b>⚡ Jovens (16-24):</b> ${p.PCT_JOVENS || 0}%<br>
                            <b>👴 Idosos (60+):</b> ${p.PCT_IDOSOS || 0}%
                        `;
                    } else {
                        tooltip.style.display = 'none';
                    }
                }
            });
        }

        function renderMap() {
            const selectEl = document.getElementById('metricSelect');
            currentMetric = selectEl ? selectEl.value : 'PCT_RENDA_ACIMA_4SM';
            updateLegend(currentMetric);

            const layer = createDeckLayer(currentMetric);

            if (!deckgl) {
                deckgl = new deck.DeckGL({
                    container: 'container',
                    map: maplibregl,
                    mapStyle: mapStyle,
                    initialViewState: {
                        longitude: -39.2,
                        latitude: -12.9,
                        zoom: 6.8,
                        pitch: 52,
                        bearing: -15,
                        maxPitch: 85
                    },
                    controller: true,
                    layers: [layer]
                });
            } else {
                deckgl.setProps({ layers: [layer] });
                if (typeof deckgl.redraw === 'function') {
                    deckgl.redraw(true);
                }
            }
        }

        const sel = document.getElementById('metricSelect');
        sel.addEventListener('change', renderMap);
        sel.addEventListener('input', renderMap);

        // Render inicial
        renderMap();
    </script>
</body>
</html>""".replace("__GEO_DATA__", geo_json_str)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_3d)
    print(f"[OK] Dashboard Demográfico e Renda 3D Deck.gl gerado: {output_path}")

if __name__ == "__main__":
    generate_demographics_dashboard()

