import os
import duckdb
import pandas as pd
import json

def export_maps_data():
    output_dir = "data/processed/google_maps"
    os.makedirs(output_dir, exist_ok=True)
    
    con = duckdb.connect("data/processed/eleicoes.duckdb")
    
    # 1. Agrupado por Local de Votação (Colégio / Escola) - Total 1.913 linhas (< 2.000)
    df_locais = con.execute("""
        SELECT 
            NM_MUNICIPIO AS MUNICIPIO,
            LOCAL_VOTACAO AS LOCAL_ESCOLA,
            ENDERECO,
            BAIRRO,
            CEP,
            LATITUDE,
            LONGITUDE,
            COUNT(*) AS QTD_URNAS_UE2015,
            SUM(TOTAL_ELEITORES) AS TOTAL_ELEITORES_UE2015,
            STRING_AGG(CAST(SECAO AS VARCHAR), ', ' ORDER BY SECAO) AS SECOES_UE2015,
            STRING_AGG(CAST(ZONA AS VARCHAR), ', ') AS ZONAS
        FROM urnas_anteriores_UE2020_BA_geo
        WHERE LATITUDE IS NOT NULL AND LONGITUDE IS NOT NULL
        GROUP BY NM_MUNICIPIO, LOCAL_VOTACAO, ENDERECO, BAIRRO, CEP, LATITUDE, LONGITUDE
        ORDER BY NM_MUNICIPIO, LOCAL_ESCOLA
    """).df()
    
    arquivo_locais = os.path.join(output_dir, "urnas_UE2015_BA_por_colegio_UNICO.csv")
    df_locais.to_csv(arquivo_locais, index=False, encoding="utf-8")
    print(f"[OK] Gerado arquivo agrupado por colégio (1 única camada): {arquivo_locais} ({len(df_locais)} registros)")

    # 2. Dividido em Partes de até 2.000 seções para camadas do Google My Maps
    df_secoes = con.execute("""
        SELECT 
            MODELO_URNA,
            NM_MUNICIPIO,
            ZONA,
            SECAO,
            NUMERO_URNA,
            LOCAL_VOTACAO,
            ENDERECO,
            BAIRRO,
            CEP,
            LATITUDE,
            LONGITUDE,
            TOTAL_ELEITORES,
            ACESSIBILIDADE,
            DATA_CARGA,
            CODIGO_CARGA
        FROM urnas_anteriores_UE2020_BA_geo
        WHERE LATITUDE IS NOT NULL AND LONGITUDE IS NOT NULL
        ORDER BY NM_MUNICIPIO, ZONA, SECAO
    """).df()
    
    chunk_size = 2000
    num_chunks = (len(df_secoes) + chunk_size - 1) // chunk_size
    
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(df_secoes))
        chunk_df = df_secoes.iloc[start_idx:end_idx]
        chunk_file = os.path.join(output_dir, f"urnas_UE2015_BA_secoes_parte_{i+1}_de_{num_chunks}.csv")
        chunk_df.to_csv(chunk_file, index=False, encoding="utf-8")
        print(f"[OK] Gerado lote {i+1}/{num_chunks}: {chunk_file} ({len(chunk_df)} seções)")

    # 3. Gerar Mapa Interativo HTML completo com Leaflet + MarkerCluster sem limites
    gerar_mapa_html(df_secoes, os.path.join(output_dir, "mapa_interativo_urnas_BA_2026.html"))

def gerar_mapa_html(df, output_path):
    # Prepare compact JSON data for web map
    records = []
    for _, row in df.iterrows():
        records.append({
            "m": row["NM_MUNICIPIO"],
            "z": int(row["ZONA"]),
            "s": int(row["SECAO"]),
            "u": str(row["NUMERO_URNA"]),
            "l": str(row["LOCAL_VOTACAO"]),
            "e": str(row["ENDERECO"]) if pd.notna(row["ENDERECO"]) else "",
            "b": str(row["BAIRRO"]) if pd.notna(row["BAIRRO"]) else "",
            "lat": round(float(row["LATITUDE"]), 6),
            "lng": round(float(row["LONGITUDE"]), 6),
            "el": int(row["TOTAL_ELEITORES"]) if pd.notna(row["TOTAL_ELEITORES"]) else 0,
            "mod": str(row["MODELO_URNA"])
        })
    
    data_json = json.dumps(records, ensure_ascii=False)
    
    # Carregar GeoJSON da Bahia
    with open("data/geo/bahia_boundary.geojson", "r", encoding="utf-8") as f:
        bahia_geojson = json.load(f)
    bahia_geojson_str = json.dumps(bahia_geojson)
    
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mapa de Urnas UE2015 (Anteriores a 2020) - Bahia 2026</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }}
        body {{ display: flex; height: 100vh; overflow: hidden; background: #0f172a; color: #f8fafc; }}
        #sidebar {{
            width: 380px; background: #1e293b; padding: 24px; display: flex; flex-direction: column;
            gap: 16px; box-shadow: 4px 0 24px rgba(0,0,0,0.4); z-index: 1000; overflow-y: auto;
        }}
        #map {{ flex: 1; height: 100%; }}
        .badge {{
            display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem;
            font-weight: 700; text-transform: uppercase; background: #f59e0b; color: #000;
        }}
        .stat-card {{
            background: #0f172a; padding: 14px; border-radius: 12px; border: 1px solid #334155;
        }}
        .stat-card .val {{ font-size: 1.5rem; font-weight: 700; color: #38bdf8; }}
        .stat-card .lbl {{ font-size: 0.8rem; color: #94a3b8; }}
        input, select {{
            width: 100%; padding: 10px 14px; background: #0f172a; border: 1px solid #334155;
            border-radius: 8px; color: #f8fafc; font-size: 0.9rem; outline: none;
        }}
        input:focus, select:focus {{ border-color: #38bdf8; }}
        .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
        .leaflet-popup-content-wrapper {{
            background: #1e293b; color: #f8fafc; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }}
        .leaflet-popup-tip {{ background: #1e293b; }}
        .popup-title {{ font-size: 1rem; font-weight: 700; color: #f59e0b; margin-bottom: 6px; }}
        .popup-info {{ font-size: 0.85rem; color: #cbd5e1; line-height: 1.4; }}
    </style>
</head>
<body>
    <div id="sidebar">
        <div>
            <span class="badge">Eleições 2026 - 1º Turno</span>
            <h2 style="font-size: 1.3rem; margin-top: 8px; font-weight: 700;">Urnas UE2015 na Bahia</h2>
            <p style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">Urnas de modelos anteriores à UE2020 geolocalizadas</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="val">7.989</div>
                <div class="lbl">Total de Seções UE2015</div>
            </div>
            <div class="stat-card">
                <div class="val">1.913</div>
                <div class="lbl">Colégios / Locais</div>
            </div>
        </div>

        <div>
            <label style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 4px; display: block;">Filtrar por Município:</label>
            <select id="municipioSelect">
                <option value="">Todos os Municípios (89)</option>
            </select>
        </div>

        <div>
            <label style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 4px; display: block;">Buscar Colégio ou Seção:</label>
            <input type="text" id="searchInput" placeholder="Digite nome da escola, bairro ou seção..." />
        </div>

        <div style="margin-top: auto; font-size: 0.75rem; color: #64748b; line-height: 1.4;">
            Fonte: Dados Abertos TSE (Correspondências Esperadas e Perfil Eleitorado 2026).
        </div>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.js"></script>
    <script>
        const data = {data_json};
        const bahiaBoundary = {bahia_geojson_str};

        const map = L.map('map').setView([-12.9714, -38.5014], 7);
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: '&copy; Esri World Street Map',
            maxZoom: 19
        }}).addTo(map);

        // Desenhar contorno da Bahia
        L.geoJSON(bahiaBoundary, {{
            style: {{
                color: '#0284c7',
                weight: 3,
                opacity: 0.95,
                fillColor: '#38bdf8',
                fillOpacity: 0.04
            }}
        }}).addTo(map);

        const markers = L.markerClusterGroup({{
            chunkedLoading: true,
            maxClusterRadius: 50
        }});

        const munSelect = document.getElementById('municipioSelect');
        const searchInput = document.getElementById('searchInput');

        const municipios = [...new Set(data.map(d => d.m))].sort();
        municipios.forEach(m => {{
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m;
            munSelect.appendChild(opt);
        }});

        function renderMarkers(filteredData) {{
            markers.clearLayers();
            const markerList = [];
            filteredData.forEach(d => {{
                const marker = L.marker([d.lat, d.lng]);
                marker.bindPopup(`
                    <div class="popup-title">${{d.l}}</div>
                    <div class="popup-info">
                        <strong>Município:</strong> ${{d.m}}<br>
                        <strong>Zona:</strong> ${{d.z}} | <strong>Seção:</strong> ${{d.s}}<br>
                        <strong>Modelo Urna:</strong> <span style="color:#f59e0b;font-weight:bold;">${{d.mod}}</span> (Nº ${{d.u}})<br>
                        <strong>Eleitores Aptos:</strong> ${{d.el.toLocaleString('pt-BR')}}<br>
                        <strong>Endereço:</strong> ${{d.e}}<br>
                        <strong>Bairro:</strong> ${{d.b}}
                    </div>
                `);
                markerList.push(marker);
            }});
            markers.addLayers(markerList);
            map.addLayer(markers);

            if (filteredData.length > 0 && filteredData.length < data.length) {{
                const group = new L.featureGroup(markerList);
                map.fitBounds(group.getBounds().pad(0.1));
            }}
        }}

        renderMarkers(data);

        function filterData() {{
            const selectedMun = munSelect.value.toLowerCase();
            const searchVal = searchInput.value.toLowerCase().trim();

            const filtered = data.filter(d => {{
                const matchMun = !selectedMun || d.m.toLowerCase() === selectedMun;
                const matchSearch = !searchVal || 
                    d.l.toLowerCase().includes(searchVal) ||
                    d.e.toLowerCase().includes(searchVal) ||
                    d.b.toLowerCase().includes(searchVal) ||
                    d.s.toString() === searchVal;
                return matchMun && matchSearch;
            }});

            renderMarkers(filtered);
        }}

        munSelect.addEventListener('change', filterData);
        searchInput.addEventListener('input', filterData);
    </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Gerado mapa interativo Leaflet HTML: {output_path}")

if __name__ == "__main__":
    export_maps_data()
