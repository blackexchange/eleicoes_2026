import os
import duckdb
import json

def generate_3d_deckgl_map():
    output_dir = "data/processed/google_maps"
    os.makedirs(output_dir, exist_ok=True)
    
    con = duckdb.connect("data/processed/eleicoes.duckdb")
    
    df_secoes = con.execute("""
        SELECT LATITUDE, LONGITUDE, NM_MUNICIPIO, LOCAL_VOTACAO
        FROM urnas_anteriores_UE2020_BA_geo
        WHERE LATITUDE IS NOT NULL AND LONGITUDE IS NOT NULL
    """).df()
    
    df_escolas = con.execute("""
        SELECT 
            NM_MUNICIPIO,
            LOCAL_VOTACAO,
            ENDERECO,
            BAIRRO,
            LATITUDE,
            LONGITUDE,
            COUNT(*) AS QTD_URNAS_UE2015,
            SUM(TOTAL_ELEITORES) AS TOTAL_ELEITORES
        FROM urnas_anteriores_UE2020_BA_geo
        WHERE LATITUDE IS NOT NULL AND LONGITUDE IS NOT NULL
        GROUP BY NM_MUNICIPIO, LOCAL_VOTACAO, ENDERECO, BAIRRO, LATITUDE, LONGITUDE
    """).df()
    
    # Carregar GeoJSON da Bahia
    with open("data/geo/bahia_boundary.geojson", "r", encoding="utf-8") as f:
        bahia_geojson = json.load(f)
    bahia_geojson_str = json.dumps(bahia_geojson)
    
    secoes_data = []
    for _, r in df_secoes.iterrows():
        secoes_data.append([round(float(r['LONGITUDE']), 5), round(float(r['LATITUDE']), 5)])
    
    escolas_data = []
    for _, r in df_escolas.iterrows():
        escolas_data.append({
            'coords': [round(float(r['LONGITUDE']), 5), round(float(r['LATITUDE']), 5)],
            'm': r['NM_MUNICIPIO'],
            'l': r['LOCAL_VOTACAO'],
            'e': str(r['ENDERECO']) if r['ENDERECO'] else '',
            'b': str(r['BAIRRO']) if r['BAIRRO'] else '',
            'q': int(r['QTD_URNAS_UE2015']),
            'el': int(r['TOTAL_ELEITORES'])
        })
    
    secoes_json = json.dumps(secoes_data)
    escolas_json = json.dumps(escolas_data, ensure_ascii=False)
    
    html_3d = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visualização 3D Deck.gl - Urnas UE2015 Bahia 2026</title>
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
            background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 16px;
            padding: 20px 24px; color: #f8fafc; max-width: 360px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }}
        .badge {{
            display: inline-block; padding: 4px 10px; border-radius: 9999px;
            font-size: 0.75rem; font-weight: 700; background: #f59e0b; color: #000;
        }}
        h2 {{ font-size: 1.25rem; font-weight: 700; margin: 8px 0 4px 0; }}
        p {{ font-size: 0.85rem; color: #94a3b8; line-height: 1.4; }}
        .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 14px; }}
        .stat-box {{ background: rgba(0,0,0,0.4); padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); }}
        .stat-val {{ font-size: 1.3rem; font-weight: 700; color: #38bdf8; }}
        .stat-lbl {{ font-size: 0.75rem; color: #94a3b8; }}
        .instructions {{ margin-top: 14px; font-size: 0.75rem; color: #cbd5e1; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px; }}
        #tooltip {{
            position: absolute; z-index: 20; pointer-events: none;
            background: rgba(15, 23, 42, 0.95); color: #fff; padding: 12px 16px;
            border-radius: 10px; font-size: 0.85rem; border: 1px solid #38bdf8;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: none; max-width: 300px;
        }}
    </style>
</head>
<body>
    <div id="container">
        <div id="panel">
            <span class="badge">3D ELEVAÇÃO GPU</span>
            <h2>Urnas UE2015 na Bahia</h2>
            <p>A altura dos hexágonos 3D indica a concentração de seções eleitorais anteriores a 2020.</p>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-val">7.989</div>
                    <div class="stat-lbl">Seções UE2015</div>
                </div>
                <div class="stat-box">
                    <div class="stat-val">1.913</div>
                    <div class="stat-lbl">Colégios Eleitorais</div>
                </div>
            </div>
            <div class="instructions">
                🗺️ <b>Contornos:</b> Limite territorial da Bahia destacado em ciano.<br>
                🖱️ <b>Navegação 3D:</b><br>
                • <b>Botão Direito ou Ctrl + Arrastar:</b> Inclinar e girar em 3D<br>
                • <b>Botão Esquerdo:</b> Mover o mapa<br>
                • <b>Scroll:</b> Zoom
            </div>
        </div>
        <div id="tooltip"></div>
    </div>

    <script>
        const secoesPoints = {secoes_json};
        const escolasPoints = {escolas_json};
        const bahiaBoundary = {bahia_geojson_str};
        const tooltip = document.getElementById('tooltip');

        // Basemap MapLibre com Esri World Street (100% livre e sem chaves)
        const mapStyle = {{
            version: 8,
            sources: {{
                'esri-tiles': {{
                    type: 'raster',
                    tiles: [
                        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}'
                    ],
                    tileSize: 256,
                    attribution: '© Esri World Street Map'
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

        const deckgl = new deck.DeckGL({{
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
            layers: [
                // Camada do Limite Territorial da Bahia
                new deck.GeoJsonLayer({{
                    id: 'bahia-boundary-layer',
                    data: bahiaBoundary,
                    stroked: true,
                    filled: true,
                    lineWidthMinPixels: 2.5,
                    getLineColor: [56, 189, 248, 240], // Ciano luminoso
                    getFillColor: [56, 189, 248, 20],   // Preenchimento transparente sutil
                    pickable: false
                }}),
                // Camada Hexágonos 3D
                new deck.HexagonLayer({{
                    id: '3d-hex-layer',
                    data: secoesPoints,
                    getPosition: d => d,
                    radius: 4500,
                    elevationScale: 120,
                    elevationRange: [50, 4500],
                    extruded: true,
                    coverage: 0.92,
                    pickable: true,
                    autoHighlight: true,
                    colorRange: [
                        [56, 189, 248, 220],
                        [14, 165, 233, 220],
                        [2, 132, 199, 220],
                        [245, 158, 11, 230],
                        [234, 88, 12, 230],
                        [220, 38, 38, 240]
                    ],
                    onHover: info => {{
                        if (info.object) {{
                            tooltip.style.display = 'block';
                            tooltip.style.left = (info.x + 15) + 'px';
                            tooltip.style.top = (info.y + 15) + 'px';
                            tooltip.innerHTML = `<b>Concentração na Região:</b><br>🔥 <b>${{info.object.points.length}}</b> seções com urnas UE2015 nesta área`;
                        }} else {{
                            tooltip.style.display = 'none';
                        }}
                    }}
                }}),
                // Camada Colégios Eleitorais
                new deck.ScatterplotLayer({{
                    id: 'schools-layer',
                    data: escolasPoints,
                    getPosition: d => d.coords,
                    getRadius: d => 300 + (d.q * 150),
                    getFillColor: [245, 158, 11, 220],
                    getLineColor: [255, 255, 255, 255],
                    lineWidthMinPixels: 1.5,
                    stroked: true,
                    pickable: true,
                    autoHighlight: true,
                    onHover: info => {{
                        if (info.object) {{
                            const d = info.object;
                            tooltip.style.display = 'block';
                            tooltip.style.left = (info.x + 15) + 'px';
                            tooltip.style.top = (info.y + 15) + 'px';
                            tooltip.innerHTML = `
                                <b style="color:#f59e0b;font-size:1rem;">${{d.l}}</b><br>
                                <b>Município:</b> ${{d.m}}<br>
                                <b>Endereço:</b> ${{d.e}} - ${{d.b}}<br>
                                <b>Urnas UE2015:</b> <span style="color:#ef4444;font-weight:bold;">${{d.q}}</span><br>
                                <b>Eleitores:</b> ${{d.el.toLocaleString('pt-BR')}}
                            `;
                        }}
                    }}
                }})
            ]
        }});
    </script>
</body>
</html>"""

    output_path = os.path.join(output_dir, "mapa_3d_deckgl_bahia.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_3d)
    print(f"[OK] Mapa 3D Deck.gl gerado com contorno da Bahia: {output_path}")

if __name__ == "__main__":
    generate_3d_deckgl_map()
