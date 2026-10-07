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
    html_3d = f"""<!DOCTYPE html>
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
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }}
        body {{ width: 100vw; height: 100vh; overflow: hidden; background: #0b0f19; }}
        #container {{ width: 100%; height: 100%; position: relative; }}
        #panel {{
            position: absolute; top: 20px; left: 20px; z-index: 10;
            background: rgba(15, 23, 42, 0.94); backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 16px;
            padding: 20px 24px; color: #f8fafc; max-width: 360px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }}
        .badge {{
            display: inline-block; padding: 4px 10px; border-radius: 9999px;
            font-size: 0.75rem; font-weight: 700; background: #38bdf8; color: #000;
        }}
        h2 {{ font-size: 1.25rem; font-weight: 700; margin: 8px 0 4px 0; }}
        p {{ font-size: 0.85rem; color: #94a3b8; line-height: 1.4; }}
        select {{
            width: 100%; padding: 10px 12px; background: #1e293b; border: 1px solid #334155;
            border-radius: 8px; color: #f8fafc; font-size: 0.9rem; margin-top: 10px; outline: none;
        }}
        #tooltip {{
            position: absolute; z-index: 20; pointer-events: none;
            background: rgba(15, 23, 42, 0.95); color: #fff; padding: 12px 16px;
            border-radius: 10px; font-size: 0.85rem; border: 1px solid #38bdf8;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: none; max-width: 300px;
        }}
        .instructions {{ margin-top: 12px; font-size: 0.75rem; color: #cbd5e1; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px; }}
    </style>
</head>
<body>
    <div id="container">
        <div id="panel">
            <span class="badge">DEMOGRAFIA & RENDA 3D</span>
            <h2>Eleitorado da Bahia 3D</h2>
            <p>A altura tridimensional dos municípios representa a dimensão demográfica selecionada.</p>
            
            <select id="metricSelect">
                <option value="PCT_RENDA_ACIMA_4SM">💰 Renda > 4 Salários Mínimos (%)</option>
                <option value="SALARIO_MEDIO_SM">💵 Salário Médio Formal (SM)</option>
                <option value="PCT_SUPERIOR">🎓 Ensino Superior (%)</option>
                <option value="TOTAL_ELEITORES">👥 Total de Eleitores</option>
                <option value="PCT_FEM">👩 Percentual Feminino (%)</option>
                <option value="PCT_JOVENS">⚡ Jovens 16-24 anos (%)</option>
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
                    attribution: '© Esri World Street Map, © IBGE'
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
            if (metric === 'PCT_RENDA_ACIMA_4SM') return val * 4500;
            if (metric === 'SALARIO_MEDIO_SM') return val * 20000;
            return val * 1500;
        }}

        function getFillColor(feature, metric) {{
            const val = feature.properties[metric] || 0;
            if (metric === 'PCT_RENDA_ACIMA_4SM') {{
                if (val > 15) return [0, 109, 44, 230];
                if (val > 10) return [49, 163, 84, 220];
                if (val > 7) return [116, 196, 118, 220];
                return [186, 228, 179, 200];
            }}
            if (metric === 'TOTAL_ELEITORES') {{
                if (val > 100000) return [220, 38, 38, 220];
                if (val > 50000) return [234, 88, 12, 220];
                if (val > 25000) return [245, 158, 11, 220];
                if (val > 10000) return [14, 165, 233, 220];
                return [56, 189, 248, 200];
            }}
            if (metric === 'PCT_SUPERIOR') {{
                if (val > 16) return [106, 81, 163, 230];
                if (val > 12) return [158, 154, 200, 220];
                if (val > 8) return [188, 189, 220, 220];
                return [218, 218, 235, 200];
            }}
            return [56, 189, 248, 220];
        }}

        function initDeck() {{
            const metric = document.getElementById('metricSelect').value;

            const layer = new deck.GeoJsonLayer({{
                id: 'demographics-3d-layer',
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
                            <b>💰 Renda > 4 SM:</b> <span style="color:#22c55e;font-weight:bold;">${{p.PCT_RENDA_ACIMA_4SM}}%</span><br>
                            <b>💵 Salário Médio:</b> ${{p.SALARIO_MEDIO_SM}} SM<br>
                            <b>🎓 Ensino Superior:</b> ${{p.PCT_SUPERIOR}}%<br>
                            <b>👥 Eleitores:</b> ${{Number(p.TOTAL_ELEITORES).toLocaleString('pt-BR')}}<br>
                            <b>👩 Mulheres:</b> ${{p.PCT_FEM}}%<br>
                            <b>⚡ Jovens (16-24):</b> ${{p.PCT_JOVENS}}%
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
    print(f"[OK] Dashboard Demográfico e Renda 3D Deck.gl gerado: {output_path}")

if __name__ == "__main__":
    generate_demographics_dashboard()
