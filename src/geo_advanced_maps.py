import os
import duckdb
import pandas as pd
import json
import folium
from folium.plugins import MarkerCluster, HeatMap, MiniMap, Fullscreen
import plotly.express as px

def generate_all_advanced_maps():
    output_dir = "data/processed/google_maps"
    os.makedirs(output_dir, exist_ok=True)
    
    con = duckdb.connect("data/processed/eleicoes.duckdb")
    
    # Extrair dados georreferenciados
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
            TOTAL_ELEITORES
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
            SUM(TOTAL_ELEITORES) AS TOTAL_ELEITORES,
            STRING_AGG(CAST(SECAO AS VARCHAR), ', ' ORDER BY SECAO) AS SECOES
        FROM urnas_anteriores_UE2020_BA_geo
        WHERE LATITUDE IS NOT NULL AND LONGITUDE IS NOT NULL
        GROUP BY NM_MUNICIPIO, LOCAL_VOTACAO, ENDERECO, BAIRRO, LATITUDE, LONGITUDE
    """).df()
    
    # Carregar GeoJSON de fronteira da Bahia (IBGE)
    with open("data/geo/bahia_boundary.geojson", "r", encoding="utf-8") as f:
        bahia_geojson = json.load(f)
    
    print(f"Total seções: {len(df_secoes)} | Total escolas: {len(df_escolas)}")

    # -------------------------------------------------------------
    # 1. MAPA GIS MULTICAMADAS COM FOLIUM (Com Limite Territorial da Bahia)
    # -------------------------------------------------------------
    print("Gerando Mapa GIS Folium...")
    m = folium.Map(
        location=[-12.9714, -39.0],
        zoom_start=7,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Street Map",
        name="Mapa Urbano (Esri Street)",
        control_scale=True
    )
    
    # Esri Satélite
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satélite (Esri Sat)"
    ).add_to(m)
    
    # Esri Topográfico
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Topo Map",
        name="Topográfico (Esri Topo)"
    ).add_to(m)

    # Esri Dark Canvas
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Esri Dark Canvas",
        name="Tema Escuro (Esri Dark)"
    ).add_to(m)

    # Camada de Limite Territorial do Estado da Bahia (IBGE)
    folium.GeoJson(
        bahia_geojson,
        name="🛡️ Limite Territorial da Bahia",
        style_function=lambda x: {
            "color": "#0284c7",
            "weight": 3.5,
            "opacity": 0.95,
            "fillColor": "#38bdf8",
            "fillOpacity": 0.04
        }
    ).add_to(m)
    
    # Camada: HeatMap de Concentração de Urnas UE2015
    heat_data = [[row["LATITUDE"], row["LONGITUDE"], row["QTD_URNAS_UE2015"]] for _, row in df_escolas.iterrows()]
    heat_group = folium.FeatureGroup(name="🔥 Mapa de Calor (Densidade de Urnas)", show=True)
    HeatMap(heat_data, radius=18, blur=14, max_zoom=13).add_to(heat_group)
    heat_group.add_to(m)
    
    # Camada: MarkerCluster de Colégios Eleitorais
    cluster_group = folium.FeatureGroup(name="📍 Colégios com Urnas UE2015 (Agrupados)", show=True)
    marker_cluster = MarkerCluster().add_to(cluster_group)
    
    for _, row in df_escolas.iterrows():
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="margin:0 0 6px 0; color: #d97706;">{row['LOCAL_VOTACAO']}</h4>
            <p style="margin:0; font-size: 12px; color: #333;">
                <b>Município:</b> {row['NM_MUNICIPIO']}<br>
                <b>Endereço:</b> {row['ENDERECO']} - {row['BAIRRO']}<br>
                <b>Qtd Urnas UE2015:</b> <span style="font-weight:bold; color: #b91c1c;">{row['QTD_URNAS_UE2015']}</span><br>
                <b>Seções:</b> {row['SECOES']}<br>
                <b>Total Eleitores:</b> {int(row['TOTAL_ELEITORES']):,}
            </p>
        </div>
        """
        folium.CircleMarker(
            location=[row["LATITUDE"], row["LONGITUDE"]],
            radius=6 + min(row["QTD_URNAS_UE2015"] * 1.5, 14),
            color="#f59e0b",
            fill=True,
            fill_color="#f59e0b",
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(marker_cluster)
        
    cluster_group.add_to(m)
    
    Fullscreen(position="topright").add_to(m)
    MiniMap(toggle_display=True, position="bottomright").add_to(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)
    
    path_folium = os.path.join(output_dir, "mapa_gis_folium_bahia.html")
    m.save(path_folium)
    print(f"[OK] Mapa GIS Folium gerado com contorno da Bahia: {path_folium}")

    # -------------------------------------------------------------
    # 2. DASHBOARD WEBGL INTERATIVO COM PLOTLY (Com Contorno da Bahia)
    # -------------------------------------------------------------
    print("Gerando Mapa Interativo Plotly...")
    fig = px.scatter_map(
        df_escolas,
        lat="LATITUDE",
        lon="LONGITUDE",
        hover_name="LOCAL_VOTACAO",
        hover_data={
            "NM_MUNICIPIO": True,
            "QTD_URNAS_UE2015": True,
            "TOTAL_ELEITORES": ":,",
            "ENDERECO": True,
            "LATITUDE": False,
            "LONGITUDE": False
        },
        size="QTD_URNAS_UE2015",
        color="QTD_URNAS_UE2015",
        color_continuous_scale="Inferno",
        size_max=22,
        zoom=6.5,
        center={"lat": -12.9714, "lon": -39.0},
        title="<b>Distribuição Espacial de Urnas Anteriores a UE2020 na Bahia - Eleições 2026</b>"
    )
    
    fig.update_layout(
        map=dict(
            style="white-bg",
            layers=[
                # Camada Esri Base
                {
                    "below": "traces",
                    "sourcetype": "raster",
                    "source": [
                        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
                    ]
                },
                # Camada Contorno da Bahia
                {
                    "below": "traces",
                    "sourcetype": "geojson",
                    "source": bahia_geojson,
                    "type": "line",
                    "color": "#0284c7",
                    "line": {"width": 3}
                },
                {
                    "below": "traces",
                    "sourcetype": "geojson",
                    "source": bahia_geojson,
                    "type": "fill",
                    "color": "rgba(56, 189, 248, 0.05)"
                }
            ],
            center={"lat": -12.9714, "lon": -39.0},
            zoom=6.5
        ),
        margin={"r": 0, "t": 45, "l": 0, "b": 0}
    )
    
    path_plotly = os.path.join(output_dir, "mapa_plotly_densidade_bahia.html")
    fig.write_html(path_plotly)
    print(f"[OK] Mapa Plotly gerado com contorno da Bahia: {path_plotly}")

if __name__ == "__main__":
    generate_all_advanced_maps()
