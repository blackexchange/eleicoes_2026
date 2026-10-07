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
    print("Consolidando votos para Presidente, demografia estratificada, renda e urnas no DuckDB...")

    # 1. Carregar dados de Renda
    with open("data/geo/renda_4sm_municipios_ba.json", "r", encoding="utf-8") as f:
        renda_dict = json.load(f)
    df_renda = pd.DataFrame(list(renda_dict.values()))
    df_renda["MUNICIPIO_NORM"] = df_renda["MUNICIPIO"].apply(normalize_name)
    con.register("df_renda_reg", df_renda)

    # 2. Criar Tabela Mestra Integrada com todas as estratificações
    con.execute("""
        CREATE OR REPLACE TABLE eleicoes_2026_consolidado_bahia AS
        WITH 
        -- Demografia TSE Estratificada
        demografia AS (
            SELECT 
                NM_MUNICIPIO AS MUNICIPIO,
                CAST(SUM(QT_ELEITORES) AS BIGINT) AS TOTAL_ELEITORES,
                
                -- Gênero
                CAST(SUM(CASE WHEN DS_GENERO = 'FEMININO' THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_FEM,
                CAST(SUM(CASE WHEN DS_GENERO = 'MASCULINO' THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_MASC,
                ROUND(SUM(CASE WHEN DS_GENERO = 'FEMININO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_FEM,
                ROUND(SUM(CASE WHEN DS_GENERO = 'MASCULINO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_MASC,
                
                -- Estado Civil
                CAST(SUM(CASE WHEN DS_ESTADO_CIVIL = 'SOLTEIRO' THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_SOLTEIROS,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL = 'SOLTEIRO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_SOLTEIROS,
                
                CAST(SUM(CASE WHEN DS_ESTADO_CIVIL = 'CASADO' THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_CASADOS,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL = 'CASADO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_CASADOS,

                CAST(SUM(CASE WHEN DS_ESTADO_CIVIL = 'DIVORCIADO' THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_DIVORCIADOS,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL = 'DIVORCIADO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_DIVORCIADOS,

                CAST(SUM(CASE WHEN DS_ESTADO_CIVIL LIKE 'VI%' THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_VIUVOS,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL LIKE 'VI%' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_VIUVOS,
                
                CAST(SUM(CASE WHEN DS_ESTADO_CIVIL IN ('DIVORCIADO', 'SEPARADO JUDICIALMENTE') OR DS_ESTADO_CIVIL LIKE 'VI%' THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_DIV_SEP_VIUVO,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL IN ('DIVORCIADO', 'SEPARADO JUDICIALMENTE') OR DS_ESTADO_CIVIL LIKE 'VI%' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_DIV_SEP_VIUVO,

                -- Idade / Faixas Etárias
                CAST(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('16 anos', '17 anos', '18 anos', '19 anos', '20 anos', '21 a 24 anos') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_JOVENS_16_24,
                ROUND(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('16 anos', '17 anos', '18 anos', '19 anos', '20 anos', '21 a 24 anos') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_JOVENS_16_24,
                
                CAST(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('25 a 29 anos', '30 a 34 anos', '35 a 39 anos') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_ADULTOS_25_39,
                ROUND(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('25 a 29 anos', '30 a 34 anos', '35 a 39 anos') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_ADULTOS_25_39,

                CAST(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('40 a 44 anos', '45 a 49 anos', '50 a 54 anos', '55 a 59 anos') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_ADULTOS_40_59,
                ROUND(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('40 a 44 anos', '45 a 49 anos', '50 a 54 anos', '55 a 59 anos') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_ADULTOS_40_59,

                CAST(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('60 a 64 anos', '65 a 69 anos', '70 a 74 anos', '75 a 79 anos', '80 a 84 anos', '85 a 89 anos', '90 a 94 anos', '95 a 99 anos', '100 anos ou mais') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_IDOSOS_60_MAIS,
                ROUND(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('60 a 64 anos', '65 a 69 anos', '70 a 74 anos', '75 a 79 anos', '80 a 84 anos', '85 a 89 anos', '90 a 94 anos', '95 a 99 anos', '100 anos ou mais') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_IDOSOS_60_MAIS,

                -- Escolaridade
                CAST(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE LIKE '%SUPERIOR%' THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_SUPERIOR,
                ROUND(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE LIKE '%SUPERIOR%' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_SUPERIOR,
                
                CAST(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('ANALFABETO', 'LÊ E ESCREVE') THEN QT_ELEITORES ELSE 0 END) AS BIGINT) AS ELEITORES_BAIXA_ESCOLARIDADE,
                ROUND(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('ANALFABETO', 'LÊ E ESCREVE') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_BAIXA_ESCOLARIDADE,

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
        -- Votos Presidente (Lula, Flávio Bolsonaro, e Outros [3ª Via + Brancos + Nulos])
        votos_pres AS (
            SELECT 
                NM_MUNICIPIO AS MUNICIPIO,
                CAST(SUM(QT_VOTOS) AS BIGINT) AS TOTAL_VOTOS_PRES,
                
                -- Lula
                CAST(SUM(CASE WHEN NM_VOTAVEL LIKE '%LULA%' THEN QT_VOTOS ELSE 0 END) AS BIGINT) AS VOTOS_LULA,
                ROUND(SUM(CASE WHEN NM_VOTAVEL LIKE '%LULA%' THEN QT_VOTOS ELSE 0 END) * 100.0 / SUM(QT_VOTOS), 2) AS PCT_LULA,
                
                -- Flávio Bolsonaro
                CAST(SUM(CASE WHEN NM_VOTAVEL LIKE '%BOLSONARO%' THEN QT_VOTOS ELSE 0 END) AS BIGINT) AS VOTOS_BOLSONARO,
                ROUND(SUM(CASE WHEN NM_VOTAVEL LIKE '%BOLSONARO%' THEN QT_VOTOS ELSE 0 END) * 100.0 / SUM(QT_VOTOS), 2) AS PCT_BOLSONARO,

                -- Outros (Demais Candidatos + Voto Branco + Voto Nulo)
                CAST(SUM(CASE WHEN NM_VOTAVEL NOT LIKE '%LULA%' AND NM_VOTAVEL NOT LIKE '%BOLSONARO%' THEN QT_VOTOS ELSE 0 END) AS BIGINT) AS VOTOS_OUTROS,
                ROUND(SUM(CASE WHEN NM_VOTAVEL NOT LIKE '%LULA%' AND NM_VOTAVEL NOT LIKE '%BOLSONARO%' THEN QT_VOTOS ELSE 0 END) * 100.0 / SUM(QT_VOTOS), 2) AS PCT_OUTROS,

                -- Margem Lula vs Flávio
                ROUND((SUM(CASE WHEN NM_VOTAVEL LIKE '%LULA%' THEN QT_VOTOS ELSE 0 END) - SUM(CASE WHEN NM_VOTAVEL LIKE '%BOLSONARO%' THEN QT_VOTOS ELSE 0 END)) * 100.0 / SUM(QT_VOTOS), 2) AS MARGEM_LULA_BOLSONARO
            FROM votacao_presidente_secao_2026_BA
            GROUP BY NM_MUNICIPIO
        )
        SELECT 
            d.MUNICIPIO,
            d.TOTAL_ELEITORES,
            
            -- Votos Presidente
            COALESCE(vp.TOTAL_VOTOS_PRES, 0) AS TOTAL_VOTOS_PRES,
            COALESCE(vp.VOTOS_LULA, 0) AS VOTOS_LULA,
            COALESCE(vp.PCT_LULA, 0.0) AS PCT_LULA,
            COALESCE(vp.VOTOS_BOLSONARO, 0) AS VOTOS_BOLSONARO,
            COALESCE(vp.PCT_BOLSONARO, 0.0) AS PCT_BOLSONARO,
            COALESCE(vp.VOTOS_OUTROS, 0) AS VOTOS_OUTROS,
            COALESCE(vp.PCT_OUTROS, 0.0) AS PCT_OUTROS,
            COALESCE(vp.MARGEM_LULA_BOLSONARO, 0.0) AS MARGEM_PRES,

            -- Classe Social e Renda
            COALESCE(r.PCT_RENDA_ACIMA_4SM, 5.0) AS PCT_RENDA_ACIMA_4SM,
            COALESCE(r.SALARIO_MEDIO_SM, 1.8) AS SALARIO_MEDIO_SM,
            COALESCE(r.RENDIMENTO_DOMICILIAR_RS, 1500.0) AS RENDIMENTO_DOMICILIAR_RS,
            d.PCT_SUPERIOR,
            d.PCT_BAIXA_ESCOLARIDADE,

            -- Gênero
            d.PCT_FEM,
            d.PCT_MASC,

            -- Estado Civil
            d.PCT_SOLTEIROS,
            d.PCT_CASADOS,
            d.PCT_DIVORCIADOS,
            d.PCT_VIUVOS,
            d.PCT_DIV_SEP_VIUVO,

            -- Faixas Etárias (Idade)
            d.PCT_JOVENS_16_24,
            d.PCT_ADULTOS_25_39,
            d.PCT_ADULTOS_40_59,
            d.PCT_IDOSOS_60_MAIS,

            -- Urnas & Biometria
            d.PCT_BIOMETRIA,
            COALESCE(u.TOTAL_URNAS, 0) AS TOTAL_URNAS,
            COALESCE(u.URNAS_UE2015, 0) AS URNAS_UE2015,
            COALESCE(u.URNAS_UE2020, 0) AS URNAS_UE2020,
            COALESCE(u.PCT_URNAS_UE2015, 0.0) AS PCT_URNAS_UE2015
        FROM demografia d
        LEFT JOIN urnas u ON d.MUNICIPIO = u.MUNICIPIO
        LEFT JOIN votos_pres vp ON d.MUNICIPIO = vp.MUNICIPIO
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
            
    print(f"[OK] {matched}/417 municípios combinados no GeoJSON com votos presidenciais e demografia completa.")
    
    enriched_geo_str = json.dumps(geo_data, ensure_ascii=False)
    
    # 4. Gerar Dashboards 2D e 3D Focados em Presidente e Estratificações
    gerar_dashboard_integrado_html(enriched_geo_str, df_master, os.path.join(output_dir, "mapa_eleicoes_2026_integrado_bahia.html"))
    gerar_dashboard_3d_integrado_html(enriched_geo_str, df_master, os.path.join(output_dir, "mapa_3d_eleicoes_2026_integrado_bahia.html"))

def gerar_dashboard_integrado_html(geo_json_str, df, output_path):
    total_bahia = int(df["TOTAL_ELEITORES"].sum())
    total_votos_pres = int(df["TOTAL_VOTOS_PRES"].sum())
    total_lula = int(df["VOTOS_LULA"].sum())
    pct_lula = round(total_lula * 100.0 / total_votos_pres, 2)
    total_bols = int(df["VOTOS_BOLSONARO"].sum())
    pct_bols = round(total_bols * 100.0 / total_votos_pres, 2)
    total_outros = int(df["VOTOS_OUTROS"].sum())
    pct_outros = round(total_outros * 100.0 / total_votos_pres, 2)
    
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eleições 2026 Presidente Bahia: Votos, Renda, Gênero, Estado Civil e Idade</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }}
        body {{ display: flex; height: 100vh; overflow: hidden; background: #0b0f19; color: #f8fafc; }}
        #sidebar {{
            width: 440px; background: #0f172a; padding: 22px; display: flex; flex-direction: column;
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
        .stats-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; }}
        .stat-card {{
            background: #1e293b; padding: 8px 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);
        }}
        .stat-card .val {{ font-size: 1.05rem; font-weight: 700; }}
        .stat-card .lbl {{ font-size: 0.68rem; color: #94a3b8; }}
        #muniDetails {{
            background: #1e293b; border-radius: 10px; padding: 14px; border: 1px solid #38bdf8;
            display: none;
        }}
        .section-title {{
            font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.5px;
            color: #94a3b8; font-weight: 700; margin-top: 8px; border-bottom: 1px solid rgba(255,255,255,0.08);
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
            <span class="badge">VOTAÇÃO PRESIDENTE & DEMOGRAFIA</span>
            <h1 style="font-size: 1.35rem; font-weight: 700; margin-top: 6px;">Bahia 2026: Presidente</h1>
            <p style="font-size: 0.8rem; color: #94a3b8;">1º Turno (04/10/2026) &bull; 417 Municípios Integrados</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card" onclick="setMetric('PCT_LULA')" style="cursor:pointer;" title="Clique para filtrar por Lula">
                <div class="val" style="color:#ef4444;">{pct_lula}%</div>
                <div class="lbl">🔴 Lula ({total_lula:,})</div>
            </div>
            <div class="stat-card" onclick="setMetric('PCT_BOLSONARO')" style="cursor:pointer;" title="Clique para filtrar por Flávio Bolsonaro">
                <div class="val" style="color:#3b82f6;">{pct_bols}%</div>
                <div class="lbl">🔵 Flávio ({total_bols:,})</div>
            </div>
            <div class="stat-card" onclick="setMetric('PCT_OUTROS')" style="cursor:pointer;" title="Clique para filtrar por Outros / 3ª Via">
                <div class="val" style="color:#94a3b8;">{pct_outros}%</div>
                <div class="lbl">⚪ Outros ({total_outros:,})</div>
            </div>
        </div>

        <div>
            <label style="font-size: 0.75rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Dimensão do Mapa:</label>
            <select id="metricSelect" class="metric-select" style="margin-top: 4px;">
                <optgroup label="🗳️ VOTAÇÃO PRESIDENTE (1º TURNO)">
                    <option value="PCT_LULA" selected>🔴 Lula Presidente (% Votos)</option>
                    <option value="PCT_BOLSONARO">🔵 Flávio Bolsonaro (% Votos)</option>
                    <option value="PCT_OUTROS">⚪ Outros (3ª Via, Brancos e Nulos) (% Votos)</option>
                    <option value="MARGEM_PRES">⚖️ Margem Lula vs Flávio (%)</option>
                </optgroup>
                <optgroup label="💰 CLASSE SOCIAL & RENDA">
                    <option value="PCT_RENDA_ACIMA_4SM">💎 Classe A/B (Renda > 4 SM) (%)</option>
                    <option value="SALARIO_MEDIO_SM">💵 Salário Médio Formal (SM)</option>
                    <option value="PCT_SUPERIOR">🎓 Ensino Superior (%)</option>
                    <option value="PCT_BAIXA_ESCOLARIDADE">📉 Baixa Escolaridade (Analf./Lê) (%)</option>
                </optgroup>
                <optgroup label="👥 GÊNERO">
                    <option value="PCT_FEM">👩 Mulheres (% Feminino)</option>
                    <option value="PCT_MASC">👨 Homens (% Masculino)</option>
                </optgroup>
                <optgroup label="💍 ESTADO CIVIL">
                    <option value="PCT_SOLTEIROS">👤 Solteiros (%)</option>
                    <option value="PCT_CASADOS">💍 Casados (%)</option>
                    <option value="PCT_DIVORCIADOS">💔 Divorciados (%)</option>
                    <option value="PCT_VIUVOS">🖤 Viúvos (%)</option>
                    <option value="PCT_DIV_SEP_VIUVO">🥀 Divorciados + Sep. + Viúvos (%)</option>
                </optgroup>
                <optgroup label="🎂 IDADE (FAIXAS ETÁRIAS)">
                    <option value="PCT_JOVENS_16_24">⚡ Jovens (16 a 24 anos) (%)</option>
                    <option value="PCT_ADULTOS_25_39">💼 Adultos Jovens (25 a 39 anos) (%)</option>
                    <option value="PCT_ADULTOS_40_59">👔 Adultos Meia-Idade (40 a 59 anos) (%)</option>
                    <option value="PCT_IDOSOS_60_MAIS">👴 Idosos (60+ anos) (%)</option>
                </optgroup>
                <optgroup label="⚙️ MODELOS DE URNA & AUDITORIA">
                    <option value="PCT_URNAS_UE2015">⚠️ Urnas UE2015 Anteriores (%)</option>
                    <option value="TOTAL_ELEITORES">👥 Total de Eleitores</option>
                </optgroup>
            </select>
        </div>

        <div>
            <label style="font-size: 0.75rem; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Buscar Município:</label>
            <input type="text" id="searchInput" class="search-input" placeholder="Digite o nome da cidade..." style="margin-top: 4px;" />
        </div>

        <div id="muniDetails">
            <h3 id="detNome" style="color: #38bdf8; font-size: 1.15rem; font-weight: 700; margin-bottom: 6px;">-</h3>
            <div id="detContent" style="font-size: 0.8rem; line-height: 1.45; color: #cbd5e1;"></div>
        </div>

        <div style="font-size: 0.7rem; color: #64748b; margin-top: auto; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px;">
            Fontes: TSE (Repositório de Dados Eleitorais 2026), IBGE Cidades.
        </div>
    </div>

    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        const geoData = {geo_json_str};

        const map = L.map('map', {{
            center: [-12.9, -39.2],
            zoom: 7,
            zoomControl: false
        }});
        L.control.zoom({{ position: 'topright' }}).addTo(map);

        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: '© Esri World Street Map, © TSE, © IBGE',
            maxZoom: 18
        }}).addTo(map);

        let geojsonLayer;
        let legendControl;

        const metricConfigs = {{
            'PCT_LULA': {{
                title: '🔴 Lula Presidente (%)',
                grades: [50, 60, 70, 80, 85],
                colors: ['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_BOLSONARO': {{
                title: '🔵 Flávio Bolsonaro (%)',
                grades: [15, 20, 30, 40, 50],
                colors: ['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_OUTROS': {{
                title: '⚪ Outros (3ª Via, Brancos, Nulos) (%)',
                grades: [6, 8, 10, 12, 15],
                colors: ['#f7f7f7', '#cccccc', '#969696', '#636363', '#252525'],
                format: v => v.toFixed(1) + '%'
            }},
            'MARGEM_PRES': {{
                title: '⚖️ Margem Lula vs Flávio (%)',
                grades: [0, 20, 40, 60, 75],
                colors: ['#bdd7e7', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
                format: v => (v > 0 ? '+' : '') + v.toFixed(1) + '%'
            }},
            'PCT_RENDA_ACIMA_4SM': {{
                title: '💎 Classe A/B (Renda > 4 SM) (%)',
                grades: [5, 7, 10, 15, 20],
                colors: ['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c'],
                format: v => v.toFixed(1) + '%'
            }},
            'SALARIO_MEDIO_SM': {{
                title: '💵 Salário Médio Formal (SM)',
                grades: [1.5, 1.8, 2.3, 3.0, 3.8],
                colors: ['#e0f3f8', '#99d5e4', '#45b4d3', '#157fad', '#08457e'],
                format: v => v.toFixed(1) + ' SM'
            }},
            'PCT_SUPERIOR': {{
                title: '🎓 Ensino Superior (%)',
                grades: [6, 8, 12, 16, 22],
                colors: ['#f2f0f7', '#cbc9e2', '#9e9ac8', '#756bb1', '#54278f'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_BAIXA_ESCOLARIDADE': {{
                title: '📉 Baixa Escolaridade (%)',
                grades: [10, 15, 20, 25, 30],
                colors: ['#fff5f0', '#fcbba1', '#fc9272', '#fb6a4a', '#cb181d'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_FEM': {{
                title: '👩 Mulheres (% Feminino)',
                grades: [50.0, 51.0, 52.0, 53.0, 54.0],
                colors: ['#fde0dd', '#fa9fb5', '#f768a1', '#c51b8a', '#7a0177'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_MASC': {{
                title: '👨 Homens (% Masculino)',
                grades: [46.0, 47.0, 48.0, 49.0, 50.0],
                colors: ['#f7fbff', '#c6dbef', '#6baed6', '#3182bd', '#08519c'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_SOLTEIROS': {{
                title: '👤 Solteiros (%)',
                grades: [55, 60, 65, 70, 75],
                colors: ['#ffffd4', '#fed98e', '#fe9929', '#d95f0e', '#993404'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_CASADOS': {{
                title: '💍 Casados (%)',
                grades: [20, 25, 30, 35, 40],
                colors: ['#e5f5e0', '#a1d99b', '#74c476', '#31a354', '#006d2c'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_DIVORCIADOS': {{
                title: '💔 Divorciados (%)',
                grades: [1.5, 2.5, 3.5, 4.5, 6.0],
                colors: ['#fef0d9', '#fdcc8a', '#fc8d59', '#e34a33', '#b30000'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_VIUVOS': {{
                title: '🖤 Viúvos (%)',
                grades: [1.5, 2.0, 2.5, 3.0, 4.0],
                colors: ['#f7f7f7', '#cccccc', '#969696', '#636363', '#252525'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_DIV_SEP_VIUVO': {{
                title: '🥀 Divorciados + Sep. + Viúvos (%)',
                grades: [4, 6, 8, 10, 13],
                colors: ['#f1eef6', '#d7b5d8', '#df65b0', '#dd1c77', '#980043'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_JOVENS_16_24': {{
                title: '⚡ Jovens (16 a 24 anos) (%)',
                grades: [12, 14, 16, 18, 20],
                colors: ['#ffffcc', '#c7e9b4', '#7fcdbb', '#41b6c4', '#225ea8'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_ADULTOS_25_39': {{
                title: '💼 Adultos Jovens (25 a 39 anos) (%)',
                grades: [25, 27, 29, 31, 34],
                colors: ['#edf8fb', '#b2e2e2', '#66c2a4', '#2ca25f', '#006d2c'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_ADULTOS_40_59': {{
                title: '👔 Adultos Meia-Idade (40 a 59 anos) (%)',
                grades: [32, 34, 36, 38, 40],
                colors: ['#fef0d9', '#fdcc8a', '#fc8d59', '#e34a33', '#b30000'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_IDOSOS_60_MAIS': {{
                title: '👴 Idosos (60+ anos) (%)',
                grades: [18, 22, 26, 30, 34],
                colors: ['#ffffd4', '#fed98e', '#fe9929', '#d95f0e', '#993404'],
                format: v => v.toFixed(1) + '%'
            }},
            'PCT_URNAS_UE2015': {{
                title: '⚠️ Urnas UE2015 Anteriores (%)',
                grades: [1, 20, 50, 80, 100],
                colors: ['#38bdf8', '#fed976', '#feb24c', '#fd8d3c', '#bd0026'],
                format: v => v.toFixed(1) + '%'
            }},
            'TOTAL_ELEITORES': {{
                title: '👥 Total de Eleitores',
                grades: [10000, 25000, 50000, 100000, 250000],
                colors: ['#edf8fb', '#b3cde3', '#8c96c6', '#8856a7', '#810f7c'],
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
                🔵 <b>Flávio Bolsonaro:</b> <span style="color:#3b82f6;font-weight:bold;">${{p.PCT_BOLSONARO}}%</span> (${{Number(p.VOTOS_BOLSONARO).toLocaleString('pt-BR')}} votos)<br>
                ⚪ <b>Outros (3ª Via, Brancos, Nulos):</b> <span style="color:#cbd5e1;font-weight:bold;">${{p.PCT_OUTROS}}%</span> (${{Number(p.VOTOS_OUTROS).toLocaleString('pt-BR')}} votos)<br>
                
                <div class="section-title">💰 CLASSE SOCIAL & RENDA</div>
                💎 <b>Classe A/B (Renda > 4 SM):</b> <span style="color:#22c55e;font-weight:bold;">${{p.PCT_RENDA_ACIMA_4SM}}%</span> | 💵 <b>Sal. Médio:</b> ${{p.SALARIO_MEDIO_SM}} SM<br>
                🎓 <b>Ensino Superior:</b> ${{p.PCT_SUPERIOR}}% | 📉 <b>Baixa Escol.:</b> ${{p.PCT_BAIXA_ESCOLARIDADE}}%<br>

                <div class="section-title">👥 GÊNERO & ESTADO CIVIL</div>
                👩 <b>Mulheres:</b> ${{p.PCT_FEM}}% | 👨 <b>Homens:</b> ${{p.PCT_MASC}}%<br>
                👤 <b>Solteiros:</b> ${{p.PCT_SOLTEIROS}}% | 💍 <b>Casados:</b> ${{p.PCT_CASADOS}}%<br>
                💔 <b>Divorciados:</b> ${{p.PCT_DIVORCIADOS}}% | 🖤 <b>Viúvos:</b> ${{p.PCT_VIUVOS}}%<br>

                <div class="section-title">🎂 FAIXAS ETÁRIAS (IDADE)</div>
                ⚡ <b>16-24 anos:</b> ${{p.PCT_JOVENS_16_24}}% | 💼 <b>25-39 anos:</b> ${{p.PCT_ADULTOS_25_39}}%<br>
                👔 <b>40-59 anos:</b> ${{p.PCT_ADULTOS_40_59}}% | 👴 <b>60+ anos:</b> ${{p.PCT_IDOSOS_60_MAIS}}%<br>

                <div class="section-title">⚙️ MODELOS DE URNA (AUDITORIA)</div>
                ⚠️ <b>Urnas UE2015 (Anteriores):</b> <span style="color:#f59e0b;font-weight:bold;">${{p.PCT_URNAS_UE2015}}%</span> (${{p.URNAS_UE2015}} de ${{p.TOTAL_URNAS}} seções)<br>
                ✅ <b>Urnas UE2020 (Novas):</b> ${{p.URNAS_UE2020}} seções | 👥 <b>Eleitores:</b> ${{Number(p.TOTAL_ELEITORES).toLocaleString('pt-BR')}}
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

        function setMetric(m) {{
            document.getElementById('metricSelect').value = m;
            updateMap();
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
    html_3d = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visualização 3D Presidente Bahia 2026: Votos, Renda, Gênero, Estado Civil e Idade</title>
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
            padding: 20px 24px; color: #f8fafc; max-width: 400px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }
        .badge {
            display: inline-block; padding: 4px 10px; border-radius: 9999px;
            font-size: 0.72rem; font-weight: 700; background: #38bdf8; color: #000;
        }
        h2 { font-size: 1.25rem; font-weight: 700; margin: 8px 0 4px 0; }
        p { font-size: 0.82rem; color: #94a3b8; line-height: 1.4; }
        select {
            width: 100%; padding: 10px 12px; background: #1e293b; border: 1px solid #334155;
            border-radius: 8px; color: #f8fafc; font-size: 0.88rem; margin-top: 10px; outline: none;
            font-weight: 600;
        }
        optgroup { font-weight: 700; color: #38bdf8; background: #0f172a; }
        option { font-weight: 400; color: #f8fafc; background: #1e293b; }
        #tooltip {
            position: absolute; z-index: 20; pointer-events: none;
            background: rgba(15, 23, 42, 0.95); color: #fff; padding: 12px 16px;
            border-radius: 10px; font-size: 0.82rem; border: 1px solid #38bdf8;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: none; max-width: 320px;
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
        .instructions { margin-top: 12px; font-size: 0.72rem; color: #cbd5e1; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px; }
    </style>
</head>
<body>
    <div id="container">
        <div id="panel">
            <span class="badge">3D ELEVAÇÃO GPU & COROPLÉTICO</span>
            <h2>Bahia 2026: Presidente 3D</h2>
            <p>Selecione a métrica abaixo ou use os botões rápidos para visualizar a elevação e cores dos 417 municípios.</p>
            
            <div style="display:flex;gap:6px;margin:10px 0;">
                <button onclick="set3DMetric('PCT_LULA')" style="flex:1;background:#450a0a;color:#f87171;border:1px solid #ef4444;border-radius:6px;padding:7px;font-weight:700;font-size:0.75rem;cursor:pointer;">🔴 Lula</button>
                <button onclick="set3DMetric('PCT_BOLSONARO')" style="flex:1;background:#172554;color:#60a5fa;border:1px solid #3b82f6;border-radius:6px;padding:7px;font-weight:700;font-size:0.75rem;cursor:pointer;">🔵 Flávio</button>
                <button onclick="set3DMetric('PCT_OUTROS')" style="flex:1;background:#1e293b;color:#cbd5e1;border:1px solid #64748b;border-radius:6px;padding:7px;font-weight:700;font-size:0.75rem;cursor:pointer;">⚪ Outros</button>
            </div>

            <select id="metricSelect">
                <optgroup label="🗳️ VOTAÇÃO PRESIDENTE (1º TURNO)">
                    <option value="PCT_LULA" selected>🔴 Lula Presidente (% Votos)</option>
                    <option value="PCT_BOLSONARO">🔵 Flávio Bolsonaro (% Votos)</option>
                    <option value="PCT_OUTROS">⚪ Outros (3ª Via, Brancos e Nulos) (% Votos)</option>
                    <option value="MARGEM_PRES">⚖️ Margem Lula vs Flávio (%)</option>
                </optgroup>
                <optgroup label="💰 CLASSE SOCIAL & RENDA">
                    <option value="PCT_RENDA_ACIMA_4SM">💎 Classe A/B (Renda > 4 SM) (%)</option>
                    <option value="SALARIO_MEDIO_SM">💵 Salário Médio Formal (SM)</option>
                    <option value="PCT_SUPERIOR">🎓 Ensino Superior (%)</option>
                    <option value="PCT_BAIXA_ESCOLARIDADE">📉 Baixa Escolaridade (Analf./Lê) (%)</option>
                </optgroup>
                <optgroup label="👥 GÊNERO">
                    <option value="PCT_FEM">👩 Mulheres (% Feminino)</option>
                    <option value="PCT_MASC">👨 Homens (% Masculino)</option>
                </optgroup>
                <optgroup label="💍 ESTADO CIVIL">
                    <option value="PCT_SOLTEIROS">👤 Solteiros (%)</option>
                    <option value="PCT_CASADOS">💍 Casados (%)</option>
                    <option value="PCT_DIVORCIADOS">💔 Divorciados (%)</option>
                    <option value="PCT_VIUVOS">🖤 Viúvos (%)</option>
                    <option value="PCT_DIV_SEP_VIUVO">🥀 Divorciados + Sep. + Viúvos (%)</option>
                </optgroup>
                <optgroup label="🎂 IDADE (FAIXAS ETÁRIAS)">
                    <option value="PCT_JOVENS_16_24">⚡ Jovens (16 a 24 anos) (%)</option>
                    <option value="PCT_ADULTOS_25_39">💼 Adultos Jovens (25 a 39 anos) (%)</option>
                    <option value="PCT_ADULTOS_40_59">👔 Adultos Meia-Idade (40 a 59 anos) (%)</option>
                    <option value="PCT_IDOSOS_60_MAIS">👴 Idosos (60+ anos) (%)</option>
                </optgroup>
                <optgroup label="⚙️ MODELOS DE URNA & AUDITORIA">
                    <option value="PCT_URNAS_UE2015">⚠️ Urnas UE2015 Anteriores (%)</option>
                    <option value="TOTAL_ELEITORES">👥 Total de Eleitores</option>
                </optgroup>
            </select>

            <div id="legendBox">
                <div id="legendTitle" style="font-weight: 700; color: #38bdf8;">🔴 Lula Presidente</div>
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
            'PCT_LULA': {
                name: '🔴 Lula Presidente (% Votos)',
                colors: ['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
                minLbl: '45%', midLbl: '65%', maxLbl: '85%+',
                getColor: v => {
                    if (v >= 80) return [165, 15, 21, 245];
                    if (v >= 70) return [222, 45, 38, 235];
                    if (v >= 60) return [251, 106, 74, 220];
                    if (v >= 50) return [252, 174, 145, 210];
                    return [254, 229, 217, 190];
                },
                getElevation: v => v * 1800
            },
            'PCT_BOLSONARO': {
                name: '🔵 Flávio Bolsonaro (% Votos)',
                colors: ['#eff3ff', '#bdd7e7', '#6baed6', '#3182bd', '#08519c'],
                minLbl: '10%', midLbl: '25%', maxLbl: '45%+',
                getColor: v => {
                    if (v >= 40) return [8, 81, 156, 245];
                    if (v >= 30) return [49, 130, 189, 235];
                    if (v >= 20) return [107, 174, 214, 220];
                    if (v >= 15) return [189, 215, 231, 210];
                    return [239, 243, 255, 190];
                },
                getElevation: v => v * 2800
            },
            'PCT_OUTROS': {
                name: '⚪ Outros (3ª Via, Brancos e Nulos) (% Votos)',
                colors: ['#f7f7f7', '#cccccc', '#969696', '#636363', '#252525'],
                minLbl: '5%', midLbl: '10%', maxLbl: '18%+',
                getColor: v => {
                    if (v >= 14) return [37, 37, 37, 245];
                    if (v >= 11) return [99, 99, 99, 235];
                    if (v >= 9) return [150, 150, 150, 220];
                    if (v >= 7) return [204, 204, 204, 210];
                    return [247, 247, 247, 190];
                },
                getElevation: v => v * 7500
            },
            'MARGEM_PRES': {
                name: '⚖️ Margem Lula vs Flávio (%)',
                colors: ['#bdd7e7', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15'],
                minLbl: '0%', midLbl: '+35%', maxLbl: '+75%+',
                getColor: v => {
                    if (v >= 65) return [165, 15, 21, 245];
                    if (v >= 50) return [222, 45, 38, 235];
                    if (v >= 35) return [251, 106, 74, 220];
                    if (v >= 15) return [252, 174, 145, 210];
                    return [189, 215, 231, 190];
                },
                getElevation: v => Math.max(v, 0) * 1800
            },
            'PCT_RENDA_ACIMA_4SM': {
                name: '💎 Classe A/B (Renda > 4 SM) (%)',
                colors: ['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c'],
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
            'PCT_BAIXA_ESCOLARIDADE': {
                name: '📉 Baixa Escolaridade (%)',
                colors: ['#fff5f0', '#fcbba1', '#fc9272', '#fb6a4a', '#cb181d'],
                minLbl: '8%', midLbl: '18%', maxLbl: '32%+',
                getColor: v => {
                    if (v >= 28) return [203, 24, 29, 245];
                    if (v >= 22) return [251, 106, 74, 235];
                    if (v >= 16) return [252, 146, 114, 220];
                    if (v >= 11) return [252, 187, 161, 210];
                    return [255, 245, 240, 190];
                },
                getElevation: v => v * 4000
            },
            'PCT_FEM': {
                name: '👩 Mulheres (% Feminino)',
                colors: ['#fde0dd', '#fa9fb5', '#f768a1', '#c51b8a', '#7a0177'],
                minLbl: '49%', midLbl: '52%', maxLbl: '55%+',
                getColor: v => {
                    if (v >= 53.5) return [122, 1, 119, 245];
                    if (v >= 52.5) return [197, 27, 138, 235];
                    if (v >= 51.5) return [247, 104, 161, 220];
                    if (v >= 50.5) return [250, 159, 181, 210];
                    return [253, 224, 221, 190];
                },
                getElevation: v => (v - 48) * 16000
            },
            'PCT_MASC': {
                name: '👨 Homens (% Masculino)',
                colors: ['#f7fbff', '#c6dbef', '#6baed6', '#3182bd', '#08519c'],
                minLbl: '45%', midLbl: '48%', maxLbl: '51%+',
                getColor: v => {
                    if (v >= 49.5) return [8, 81, 156, 245];
                    if (v >= 48.5) return [49, 130, 189, 235];
                    if (v >= 47.5) return [107, 174, 214, 220];
                    if (v >= 46.5) return [198, 219, 239, 210];
                    return [247, 251, 255, 190];
                },
                getElevation: v => (v - 44) * 16000
            },
            'PCT_SOLTEIROS': {
                name: '👤 Solteiros (%)',
                colors: ['#ffffd4', '#fed98e', '#fe9929', '#d95f0e', '#993404'],
                minLbl: '50%', midLbl: '65%', maxLbl: '78%+',
                getColor: v => {
                    if (v >= 72) return [153, 52, 4, 245];
                    if (v >= 66) return [217, 95, 14, 235];
                    if (v >= 60) return [254, 153, 41, 220];
                    if (v >= 55) return [254, 217, 142, 210];
                    return [255, 255, 212, 190];
                },
                getElevation: v => v * 1800
            },
            'PCT_CASADOS': {
                name: '💍 Casados (%)',
                colors: ['#e5f5e0', '#a1d99b', '#74c476', '#31a354', '#006d2c'],
                minLbl: '18%', midLbl: '28%', maxLbl: '42%+',
                getColor: v => {
                    if (v >= 35) return [0, 109, 44, 245];
                    if (v >= 30) return [49, 163, 84, 235];
                    if (v >= 25) return [116, 196, 118, 220];
                    if (v >= 20) return [161, 217, 155, 210];
                    return [229, 245, 224, 190];
                },
                getElevation: v => v * 3000
            },
            'PCT_DIVORCIADOS': {
                name: '💔 Divorciados (%)',
                colors: ['#fef0d9', '#fdcc8a', '#fc8d59', '#e34a33', '#b30000'],
                minLbl: '1.5%', midLbl: '3.0%', maxLbl: '6.0%+',
                getColor: v => {
                    if (v >= 5.0) return [179, 0, 0, 245];
                    if (v >= 4.0) return [227, 74, 51, 235];
                    if (v >= 3.0) return [252, 141, 89, 220];
                    if (v >= 2.0) return [253, 204, 138, 210];
                    return [254, 240, 217, 190];
                },
                getElevation: v => v * 15000
            },
            'PCT_VIUVOS': {
                name: '🖤 Viúvos (%)',
                colors: ['#f7f7f7', '#cccccc', '#969696', '#636363', '#252525'],
                minLbl: '1.5%', midLbl: '2.5%', maxLbl: '4.5%+',
                getColor: v => {
                    if (v >= 3.5) return [37, 37, 37, 245];
                    if (v >= 2.8) return [99, 99, 99, 235];
                    if (v >= 2.2) return [150, 150, 150, 220];
                    if (v >= 1.7) return [204, 204, 204, 210];
                    return [247, 247, 247, 190];
                },
                getElevation: v => v * 20000
            },
            'PCT_DIV_SEP_VIUVO': {
                name: '🥀 Divorciados + Sep. + Viúvos (%)',
                colors: ['#f1eef6', '#d7b5d8', '#df65b0', '#dd1c77', '#980043'],
                minLbl: '3%', midLbl: '7%', maxLbl: '14%+',
                getColor: v => {
                    if (v >= 10) return [152, 0, 67, 245];
                    if (v >= 8) return [221, 28, 119, 235];
                    if (v >= 6) return [223, 101, 176, 220];
                    if (v >= 4) return [215, 181, 216, 210];
                    return [241, 238, 246, 190];
                },
                getElevation: v => v * 9000
            },
            'PCT_JOVENS_16_24': {
                name: '⚡ Jovens (16 a 24 anos) (%)',
                colors: ['#ffffcc', '#c7e9b4', '#7fcdbb', '#41b6c4', '#225ea8'],
                minLbl: '11%', midLbl: '15%', maxLbl: '22%+',
                getColor: v => {
                    if (v >= 18) return [34, 94, 168, 245];
                    if (v >= 16) return [65, 182, 196, 235];
                    if (v >= 14) return [127, 205, 187, 220];
                    if (v >= 12) return [199, 233, 180, 210];
                    return [255, 255, 204, 190];
                },
                getElevation: v => v * 6000
            },
            'PCT_ADULTOS_25_39': {
                name: '💼 Adultos Jovens (25 a 39 anos) (%)',
                colors: ['#edf8fb', '#b2e2e2', '#66c2a4', '#2ca25f', '#006d2c'],
                minLbl: '24%', midLbl: '29%', maxLbl: '35%+',
                getColor: v => {
                    if (v >= 32) return [0, 109, 44, 245];
                    if (v >= 30) return [44, 162, 95, 235];
                    if (v >= 28) return [102, 194, 164, 220];
                    if (v >= 26) return [178, 226, 226, 210];
                    return [237, 248, 251, 190];
                },
                getElevation: v => v * 3500
            },
            'PCT_ADULTOS_40_59': {
                name: '👔 Adultos Meia-Idade (40 a 59 anos) (%)',
                colors: ['#fef0d9', '#fdcc8a', '#fc8d59', '#e34a33', '#b30000'],
                minLbl: '30%', midLbl: '36%', maxLbl: '42%+',
                getColor: v => {
                    if (v >= 39) return [179, 0, 0, 245];
                    if (v >= 37) return [227, 74, 51, 235];
                    if (v >= 35) return [252, 141, 89, 220];
                    if (v >= 33) return [253, 204, 138, 210];
                    return [254, 240, 217, 190];
                },
                getElevation: v => v * 3000
            },
            'PCT_IDOSOS_60_MAIS': {
                name: '👴 Idosos (60+ anos) (%)',
                colors: ['#ffffd4', '#fed98e', '#fe9929', '#d95f0e', '#993404'],
                minLbl: '16%', midLbl: '23%', maxLbl: '34%+',
                getColor: v => {
                    if (v >= 30) return [153, 52, 4, 245];
                    if (v >= 26) return [217, 95, 14, 235];
                    if (v >= 22) return [254, 153, 41, 220];
                    if (v >= 19) return [254, 217, 142, 210];
                    return [255, 255, 212, 190];
                },
                getElevation: v => v * 4000
            },
            'PCT_URNAS_UE2015': {
                name: '⚠️ Urnas UE2015 Anteriores (%)',
                colors: ['#38bdf8', '#fed976', '#feb24c', '#fd8d3c', '#bd0026'],
                minLbl: '0% (Novas)', midLbl: '50%', maxLbl: '100% (UE2015)',
                getColor: v => {
                    if (v >= 80) return [189, 0, 38, 250];
                    if (v >= 40) return [253, 141, 60, 240];
                    if (v >= 10) return [254, 178, 76, 230];
                    if (v > 0) return [254, 217, 118, 220];
                    return [56, 189, 248, 140];
                },
                getElevation: v => v * 1800
            },
            'TOTAL_ELEITORES': {
                name: '👥 Total de Eleitores',
                colors: ['#edf8fb', '#b3cde3', '#8c96c6', '#8856a7', '#810f7c'],
                minLbl: '5 mil', midLbl: '30 mil', maxLbl: '100 mil+',
                getColor: v => {
                    if (v >= 100000) return [129, 15, 124, 245];
                    if (v >= 50000) return [136, 86, 167, 235];
                    if (v >= 25000) return [140, 150, 198, 220];
                    if (v >= 10000) return [179, 205, 227, 210];
                    return [237, 248, 251, 190];
                },
                getElevation: v => Math.min(v * 0.07, 160000)
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
                    attribution: '© Esri World Street Map, © TSE, © IBGE'
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
        let currentMetric = 'PCT_LULA';

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
                id: 'bahia-3d-choropleth-layer',
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
                            🔴 <b>Lula:</b> <span style="color:#ef4444;font-weight:bold;">${p.PCT_LULA || 0}%</span> (${Number(p.VOTOS_LULA || 0).toLocaleString('pt-BR')} votos)<br>
                            🔵 <b>Flávio Bolsonaro:</b> <span style="color:#3b82f6;font-weight:bold;">${p.PCT_BOLSONARO || 0}%</span> (${Number(p.VOTOS_BOLSONARO || 0).toLocaleString('pt-BR')} votos)<br>
                            ⚪ <b>Outros (3ª Via, Brancos, Nulos):</b> <span style="color:#cbd5e1;font-weight:bold;">${p.PCT_OUTROS || 0}%</span> (${Number(p.VOTOS_OUTROS || 0).toLocaleString('pt-BR')} votos)<br>
                            <hr style="border:0;border-top:1px solid rgba(255,255,255,0.1);margin:4px 0;">
                            💎 <b>Classe A/B (>4 SM):</b> ${p.PCT_RENDA_ACIMA_4SM || 0}% | 💵 <b>Sal. Médio:</b> ${p.SALARIO_MEDIO_SM || 0} SM<br>
                            🎓 <b>Superior:</b> ${p.PCT_SUPERIOR || 0}% | 👩 <b>Mulheres:</b> ${p.PCT_FEM || 0}%<br>
                            👤 <b>Solteiros:</b> ${p.PCT_SOLTEIROS || 0}% | 💍 <b>Casados:</b> ${p.PCT_CASADOS || 0}%<br>
                            💔 <b>Divorciados:</b> ${p.PCT_DIVORCIADOS || 0}% | 🖤 <b>Viúvos:</b> ${p.PCT_VIUVOS || 0}%<br>
                            ⚡ <b>Jovens (16-24):</b> ${p.PCT_JOVENS_16_24 || 0}% | 👴 <b>Idosos (60+):</b> ${p.PCT_IDOSOS_60_MAIS || 0}%<br>
                            ⚠️ <b>Urnas UE2015:</b> <span style="color:#f59e0b;">${p.PCT_URNAS_UE2015 || 0}%</span> (${p.URNAS_UE2015 || 0}/${p.TOTAL_URNAS || 0} seções)
                        `;
                    } else {
                        tooltip.style.display = 'none';
                    }
                }
            });
        }

        function renderMap() {
            const selectEl = document.getElementById('metricSelect');
            currentMetric = selectEl ? selectEl.value : 'PCT_LULA';
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

        function set3DMetric(m) {
            const selectEl = document.getElementById('metricSelect');
            if (selectEl) selectEl.value = m;
            renderMap();
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
    print(f"[OK] Dashboard Integrado 3D Deck.gl gerado: {output_path}")

if __name__ == "__main__":
    generate_integrated_dashboard()
