import os
import duckdb
import pandas as pd
import json

def export_salvador_zona_7():
    output_dir = "data/processed/salvador_zona_7"
    os.makedirs(output_dir, exist_ok=True)
    
    con = duckdb.connect("data/processed/eleicoes.duckdb")
    print("Gerando tabelas de Salvador - Zona 7 (Votos Presidente + Perfil Demográfico Completo)...")

    # 1. Tabela por Seção Eleitoral
    df_secoes = con.execute("""
        WITH demog_sec AS (
            SELECT 
                NR_ZONA,
                NR_SECAO,
                FIRST(NR_LOCAL_VOTACAO) AS NR_LOCAL_VOTACAO,
                FIRST(NM_LOCAL_VOTACAO) AS NM_LOCAL_VOTACAO,
                SUM(QT_ELEITORES) AS TOTAL_ELEITORES,
                
                -- Gênero
                SUM(CASE WHEN DS_GENERO = 'FEMININO' THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_FEM,
                SUM(CASE WHEN DS_GENERO = 'MASCULINO' THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_MASC,
                ROUND(SUM(CASE WHEN DS_GENERO = 'FEMININO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_FEM,
                ROUND(SUM(CASE WHEN DS_GENERO = 'MASCULINO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_MASC,
                
                -- Estado Civil Detalhado
                SUM(CASE WHEN DS_ESTADO_CIVIL = 'SOLTEIRO' THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_SOLTEIROS,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL = 'SOLTEIRO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_SOLTEIROS,
                
                SUM(CASE WHEN DS_ESTADO_CIVIL = 'CASADO' THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_CASADOS,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL = 'CASADO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_CASADOS,
                
                SUM(CASE WHEN DS_ESTADO_CIVIL = 'DIVORCIADO' THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_DIVORCIADOS,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL = 'DIVORCIADO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_DIVORCIADOS,
                
                SUM(CASE WHEN DS_ESTADO_CIVIL LIKE 'VI%' THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_VIUVOS,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL LIKE 'VI%' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_VIUVOS,

                SUM(CASE WHEN DS_ESTADO_CIVIL = 'SEPARADO JUDICIALMENTE' THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_SEPARADOS,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL = 'SEPARADO JUDICIALMENTE' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_SEPARADOS,

                SUM(CASE WHEN DS_ESTADO_CIVIL IN ('DIVORCIADO', 'SEPARADO JUDICIALMENTE') OR DS_ESTADO_CIVIL LIKE 'VI%' THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_DIV_SEP_VIUVO,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL IN ('DIVORCIADO', 'SEPARADO JUDICIALMENTE') OR DS_ESTADO_CIVIL LIKE 'VI%' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_DIV_SEP_VIUVO,

                -- Escolaridade
                SUM(CASE WHEN DS_GRAU_ESCOLARIDADE LIKE '%SUPERIOR%' THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_SUPERIOR,
                ROUND(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE LIKE '%SUPERIOR%' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_SUPERIOR,
                SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('ANALFABETO', 'LÊ E ESCREVE') THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_BAIXA_ESCOLARIDADE,
                ROUND(SUM(CASE WHEN DS_GRAU_ESCOLARIDADE IN ('ANALFABETO', 'LÊ E ESCREVE') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_BAIXA_ESCOLARIDADE,

                -- Faixas Etárias (Idade)
                SUM(CASE WHEN DS_FAIXA_ETARIA IN ('16 anos', '17 anos', '18 anos', '19 anos', '20 anos', '21 a 24 anos') THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_JOVENS_16_24,
                ROUND(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('16 anos', '17 anos', '18 anos', '19 anos', '20 anos', '21 a 24 anos') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_JOVENS_16_24,

                SUM(CASE WHEN DS_FAIXA_ETARIA IN ('25 a 29 anos', '30 a 34 anos', '35 a 39 anos') THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_ADULTOS_25_39,
                ROUND(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('25 a 29 anos', '30 a 34 anos', '35 a 39 anos') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_ADULTOS_25_39,

                SUM(CASE WHEN DS_FAIXA_ETARIA IN ('40 a 44 anos', '45 a 49 anos', '50 a 54 anos', '55 a 59 anos') THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_ADULTOS_40_59,
                ROUND(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('40 a 44 anos', '45 a 49 anos', '50 a 54 anos', '55 a 59 anos') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_ADULTOS_40_59,

                SUM(CASE WHEN DS_FAIXA_ETARIA IN ('60 a 64 anos', '65 a 69 anos', '70 a 74 anos', '75 a 79 anos', '80 a 84 anos', '85 a 89 anos', '90 a 94 anos', '95 a 99 anos', '100 anos ou mais') THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_IDOSOS_60_MAIS,
                ROUND(SUM(CASE WHEN DS_FAIXA_ETARIA IN ('60 a 64 anos', '65 a 69 anos', '70 a 74 anos', '75 a 79 anos', '80 a 84 anos', '85 a 89 anos', '90 a 94 anos', '95 a 99 anos', '100 anos ou mais') THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_IDOSOS_60_MAIS,

                SUM(QT_ELEITORES_BIOMETRIA) AS ELEITORES_BIOMETRIA,
                ROUND(SUM(QT_ELEITORES_BIOMETRIA) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_BIOMETRIA
            FROM perfil_eleitorado_2026_BA
            WHERE NM_MUNICIPIO = 'SALVADOR' AND CAST(NR_ZONA AS BIGINT) = 7
            GROUP BY NR_ZONA, NR_SECAO
        ),
        votos_sec AS (
            SELECT 
                NR_ZONA,
                NR_SECAO,
                CAST(SUM(QT_VOTOS) AS BIGINT) AS TOTAL_VOTOS,
                CAST(SUM(CASE WHEN NM_VOTAVEL LIKE '%LULA%' THEN QT_VOTOS ELSE 0 END) AS BIGINT) AS VOTOS_LULA,
                ROUND(SUM(CASE WHEN NM_VOTAVEL LIKE '%LULA%' THEN QT_VOTOS ELSE 0 END) * 100.0 / SUM(QT_VOTOS), 2) AS PCT_LULA,
                CAST(SUM(CASE WHEN NM_VOTAVEL LIKE '%BOLSONARO%' THEN QT_VOTOS ELSE 0 END) AS BIGINT) AS VOTOS_BOLSONARO,
                ROUND(SUM(CASE WHEN NM_VOTAVEL LIKE '%BOLSONARO%' THEN QT_VOTOS ELSE 0 END) * 100.0 / SUM(QT_VOTOS), 2) AS PCT_BOLSONARO,
                CAST(SUM(CASE WHEN NM_VOTAVEL NOT LIKE '%LULA%' AND NM_VOTAVEL NOT LIKE '%BOLSONARO%' THEN QT_VOTOS ELSE 0 END) AS BIGINT) AS VOTOS_OUTROS,
                ROUND(SUM(CASE WHEN NM_VOTAVEL NOT LIKE '%LULA%' AND NM_VOTAVEL NOT LIKE '%BOLSONARO%' THEN QT_VOTOS ELSE 0 END) * 100.0 / SUM(QT_VOTOS), 2) AS PCT_OUTROS
            FROM votacao_presidente_secao_2026_BA
            WHERE NM_MUNICIPIO = 'SALVADOR' AND CAST(NR_ZONA AS BIGINT) = 7
            GROUP BY NR_ZONA, NR_SECAO
        ),
        urnas_sec AS (
            SELECT 
                NR_ZONA,
                NR_SECAO,
                CAST(NR_URNA_ESPERADA AS BIGINT) AS MODELO_URNA_NUM,
                CASE WHEN CAST(NR_URNA_ESPERADA AS BIGINT) < 2000000 THEN 'UE2015' ELSE 'UE2020' END AS MODELO_URNA
            FROM correspondencias_2026_BA
            WHERE NM_MUNICIPIO = 'SALVADOR' AND CAST(NR_ZONA AS BIGINT) = 7
        )
        SELECT 
            d.NR_ZONA,
            d.NR_SECAO,
            d.NR_LOCAL_VOTACAO,
            d.NM_LOCAL_VOTACAO,
            COALESCE(u.MODELO_URNA, 'UE2020') AS MODELO_URNA,
            d.TOTAL_ELEITORES,
            COALESCE(v.TOTAL_VOTOS, 0) AS TOTAL_VOTOS,
            COALESCE(v.VOTOS_LULA, 0) AS VOTOS_LULA,
            COALESCE(v.PCT_LULA, 0.0) AS PCT_LULA,
            COALESCE(v.VOTOS_BOLSONARO, 0) AS VOTOS_BOLSONARO,
            COALESCE(v.PCT_BOLSONARO, 0.0) AS PCT_BOLSONARO,
            COALESCE(v.VOTOS_OUTROS, 0) AS VOTOS_OUTROS,
            COALESCE(v.PCT_OUTROS, 0.0) AS PCT_OUTROS,
            d.PCT_FEM,
            d.PCT_MASC,
            d.PCT_SOLTEIROS,
            d.PCT_CASADOS,
            d.PCT_DIVORCIADOS,
            d.PCT_VIUVOS,
            d.PCT_SEPARADOS,
            d.PCT_DIV_SEP_VIUVO,
            d.PCT_SUPERIOR,
            d.PCT_BAIXA_ESCOLARIDADE,
            d.PCT_JOVENS_16_24,
            d.PCT_ADULTOS_25_39,
            d.PCT_ADULTOS_40_59,
            d.PCT_IDOSOS_60_MAIS,
            d.PCT_BIOMETRIA
        FROM demog_sec d
        LEFT JOIN votos_sec v ON d.NR_ZONA = v.NR_ZONA AND d.NR_SECAO = v.NR_SECAO
        LEFT JOIN urnas_sec u ON d.NR_ZONA = u.NR_ZONA AND d.NR_SECAO = u.NR_SECAO
        ORDER BY d.NR_SECAO
    """).df()

    # Salvar tabela de seções
    csv_secoes = os.path.join(output_dir, "salvador_zona_7_presidente_por_secao.csv")
    parquet_secoes = os.path.join(output_dir, "salvador_zona_7_presidente_por_secao.parquet")
    df_secoes.to_csv(csv_secoes, index=False, encoding="utf-8")
    df_secoes.to_parquet(parquet_secoes, index=False)
    print(f"[OK] 247 Seções da Zona 7 exportadas: {csv_secoes}")

    # 2. Tabela Agrupada por Local de Votação (Colégio Eleitoral)
    df_locais = con.execute("""
        SELECT 
            NR_LOCAL_VOTACAO,
            NM_LOCAL_VOTACAO,
            COUNT(DISTINCT NR_SECAO) AS QTD_SECOES,
            SUM(TOTAL_ELEITORES) AS TOTAL_ELEITORES,
            SUM(TOTAL_VOTOS) AS TOTAL_VOTOS,
            SUM(VOTOS_LULA) AS VOTOS_LULA,
            ROUND(SUM(VOTOS_LULA) * 100.0 / SUM(TOTAL_VOTOS), 2) AS PCT_LULA,
            SUM(VOTOS_BOLSONARO) AS VOTOS_BOLSONARO,
            ROUND(SUM(VOTOS_BOLSONARO) * 100.0 / SUM(TOTAL_VOTOS), 2) AS PCT_BOLSONARO,
            SUM(VOTOS_OUTROS) AS VOTOS_OUTROS,
            ROUND(SUM(VOTOS_OUTROS) * 100.0 / SUM(TOTAL_VOTOS), 2) AS PCT_OUTROS,
            SUM(CASE WHEN MODELO_URNA = 'UE2015' THEN 1 ELSE 0 END) AS URNAS_UE2015,
            SUM(CASE WHEN MODELO_URNA = 'UE2020' THEN 1 ELSE 0 END) AS URNAS_UE2020,
            ROUND(SUM(CASE WHEN MODELO_URNA = 'UE2015' THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT NR_SECAO), 2) AS PCT_URNAS_UE2015,
            
            -- Médias Ponderadas Demográficas
            ROUND(SUM(PCT_FEM * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_FEM,
            ROUND(SUM(PCT_MASC * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_MASC,
            ROUND(SUM(PCT_SOLTEIROS * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_SOLTEIROS,
            ROUND(SUM(PCT_CASADOS * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_CASADOS,
            ROUND(SUM(PCT_DIVORCIADOS * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_DIVORCIADOS,
            ROUND(SUM(PCT_VIUVOS * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_VIUVOS,
            ROUND(SUM(PCT_SEPARADOS * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_SEPARADOS,
            ROUND(SUM(PCT_DIV_SEP_VIUVO * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_DIV_SEP_VIUVO,
            ROUND(SUM(PCT_SUPERIOR * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_SUPERIOR,
            ROUND(SUM(PCT_BAIXA_ESCOLARIDADE * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_BAIXA_ESCOLARIDADE,
            ROUND(SUM(PCT_JOVENS_16_24 * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_JOVENS_16_24,
            ROUND(SUM(PCT_ADULTOS_25_39 * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_ADULTOS_25_39,
            ROUND(SUM(PCT_ADULTOS_40_59 * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_ADULTOS_40_59,
            ROUND(SUM(PCT_IDOSOS_60_MAIS * TOTAL_ELEITORES) / SUM(TOTAL_ELEITORES), 2) AS PCT_IDOSOS_60_MAIS
        FROM df_secoes
        GROUP BY NR_LOCAL_VOTACAO, NM_LOCAL_VOTACAO
        ORDER BY TOTAL_ELEITORES DESC
    """).df()

    csv_locais = os.path.join(output_dir, "salvador_zona_7_presidente_por_local.csv")
    parquet_locais = os.path.join(output_dir, "salvador_zona_7_presidente_por_local.parquet")
    df_locais.to_csv(csv_locais, index=False, encoding="utf-8")
    df_locais.to_parquet(parquet_locais, index=False)
    print(f"[OK] 20 Locais de Votação da Zona 7 exportados: {csv_locais}")

    # 3. Gerar Relatório HTML Interativo com DataTables e visualização premium
    gerar_relatorio_html(df_locais, df_secoes, os.path.join(output_dir, "relatorio_salvador_zona_7_eleicoes_2026.html"))

def gerar_relatorio_html(df_locais, df_secoes, output_path):
    tot_eleitores = int(df_locais["TOTAL_ELEITORES"].sum())
    tot_votos = int(df_locais["TOTAL_VOTOS"].sum())
    tot_lula = int(df_locais["VOTOS_LULA"].sum())
    pct_lula = round(tot_lula * 100.0 / tot_votos, 2)
    tot_bols = int(df_locais["VOTOS_BOLSONARO"].sum())
    pct_bols = round(tot_bols * 100.0 / tot_votos, 2)
    tot_outros = int(df_locais["VOTOS_OUTROS"].sum())
    pct_outros = round(tot_outros * 100.0 / tot_votos, 2)
    
    # Médias da Zona 7
    pct_solt = round((df_locais["PCT_SOLTEIROS"] * df_locais["TOTAL_ELEITORES"]).sum() / tot_eleitores, 2)
    pct_cas = round((df_locais["PCT_CASADOS"] * df_locais["TOTAL_ELEITORES"]).sum() / tot_eleitores, 2)
    pct_div = round((df_locais["PCT_DIVORCIADOS"] * df_locais["TOTAL_ELEITORES"]).sum() / tot_eleitores, 2)
    pct_viu = round((df_locais["PCT_VIUVOS"] * df_locais["TOTAL_ELEITORES"]).sum() / tot_eleitores, 2)

    # Preparar JSON para a tabela interativa
    locais_json = df_locais.to_json(orient="records", force_ascii=False)
    secoes_json = df_secoes.to_json(orient="records", force_ascii=False)

    template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Salvador - Zona Eleitoral 007: Votos Presidente e Demografia 2026</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }
        body { background: #0b0f19; color: #f8fafc; padding: 24px; }
        .header { margin-bottom: 20px; }
        .badge { display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; background: #38bdf8; color: #000; }
        h1 { font-size: 1.6rem; font-weight: 700; margin: 8px 0 4px 0; }
        p { color: #94a3b8; font-size: 0.88rem; }
        
        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 16px 0 20px 0; }
        .kpi-card { background: #0f172a; padding: 12px 14px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); transition: transform 0.2s; }
        .kpi-card:hover { transform: translateY(-2px); border-color: rgba(56, 189, 248, 0.4); }
        .kpi-val { font-size: 1.3rem; font-weight: 700; }
        .kpi-lbl { font-size: 0.72rem; color: #94a3b8; }

        /* Filter Controls Panel */
        .filter-panel {
            background: #0f172a; border-radius: 14px; padding: 18px; border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .filter-section-title {
            font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.6px;
            color: #38bdf8; font-weight: 700; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;
        }
        .filter-groups {
            display: flex; flex-wrap: wrap; gap: 14px; align-items: center; justify-content: space-between;
        }
        .filter-chips {
            display: flex; flex-wrap: wrap; gap: 8px;
        }
        .filter-chip {
            background: #1e293b; border: 1px solid #334155; color: #cbd5e1;
            padding: 7px 14px; border-radius: 8px; font-size: 0.82rem; font-weight: 600;
            cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 6px;
        }
        .filter-chip:hover { background: #334155; color: #fff; }
        .filter-chip.active-all { background: #38bdf8; color: #000; border-color: #38bdf8; }
        .filter-chip.active-lula { background: #ef4444; color: #fff; border-color: #ef4444; }
        .filter-chip.active-bols { background: #3b82f6; color: #fff; border-color: #3b82f6; }
        .filter-chip.active-outros { background: #64748b; color: #fff; border-color: #94a3b8; }

        .custom-range-box {
            display: flex; align-items: center; gap: 12px; background: #1e293b;
            padding: 8px 14px; border-radius: 8px; border: 1px solid #334155;
        }
        .custom-range-box label { font-size: 0.78rem; font-weight: 600; color: #94a3b8; }
        .custom-range-box select {
            background: #0f172a; border: 1px solid #475569; color: #f8fafc;
            padding: 4px 8px; border-radius: 6px; font-size: 0.82rem; font-weight: 600; outline: none;
        }

        .filter-status-banner {
            margin-top: 12px; padding: 8px 12px; background: rgba(56, 189, 248, 0.08);
            border-left: 3px solid #38bdf8; border-radius: 4px; font-size: 0.8rem; color: #93c5fd;
            display: flex; justify-content: space-between; align-items: center;
        }

        .tabs { display: flex; gap: 10px; margin-bottom: 16px; }
        .tab-btn { background: #1e293b; border: 1px solid #334155; color: #f8fafc; padding: 10px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.2s; }
        .tab-btn.active { background: #38bdf8; color: #000; border-color: #38bdf8; }
        
        .table-container { background: #0f172a; border-radius: 14px; padding: 18px; border: 1px solid rgba(255,255,255,0.08); overflow-x: auto; }
        table.dataTable { width: 100% !important; background: transparent; color: #f8fafc; font-size: 0.82rem; }
        table.dataTable thead th { background: #1e293b; color: #38bdf8; font-weight: 700; border-bottom: 1px solid #334155 !important; padding: 10px 8px; text-align: left; }
        table.dataTable tbody td { border-bottom: 1px solid rgba(255,255,255,0.05); padding: 8px; }
        table.dataTable tbody tr:hover { background: rgba(56, 189, 248, 0.08); }
        .dataTables_wrapper .dataTables_length, .dataTables_wrapper .dataTables_filter, .dataTables_wrapper .dataTables_info, .dataTables_wrapper .dataTables_paginate { color: #94a3b8 !important; font-size: 0.8rem; margin: 10px 0; }
        .dataTables_wrapper .dataTables_filter input { background: #1e293b; border: 1px solid #334155; border-radius: 6px; color: #fff; padding: 6px 10px; outline: none; }
        .pct-pill { display: inline-block; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
    </style>
</head>
<body>
    <div class="header">
        <span class="badge">ZONA ELEITORAL 007 &bull; SALVADOR / BA</span>
        <h1>Votação para Presidente & Estratificação Demográfica Completa</h1>
        <p>Eleições Gerais 2026 (1º Turno) &bull; Cruzamento Seção a Seção com o Perfil do Eleitorado TSE</p>
    </div>

    <!-- KPIs -->
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-val" style="color: #38bdf8;">__TOT_ELEITORES__</div>
            <div class="kpi-lbl">👥 Eleitores Aptos</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #ef4444;">__PCT_LULA__%</div>
            <div class="kpi-lbl">🔴 Lula (__TOT_LULA__ votos)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #3b82f6;">__PCT_BOLS__%</div>
            <div class="kpi-lbl">🔵 Flávio (__TOT_BOLS__ votos)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #cbd5e1;">__PCT_OUTROS__%</div>
            <div class="kpi-lbl">⚪ Outros (__TOT_OUTROS__ votos)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #fbbf24;">__PCT_SOLT__%</div>
            <div class="kpi-lbl">👤 Solteiros</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #34d399;">__PCT_CAS__%</div>
            <div class="kpi-lbl">💍 Casados</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #f472b6;">__PCT_DIV__%</div>
            <div class="kpi-lbl">💔 Divorciados</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #a78bfa;">__PCT_VIU__%</div>
            <div class="kpi-lbl">🕯️ Viúvos</div>
        </div>
    </div>

    <!-- Interactive Demographic Cross-Selector & Ecological Inference Tool -->
    <div class="filter-panel" style="border: 1px solid #38bdf8; background: linear-gradient(180deg, #0f172a 0%, #131d35 100%);">
        <div class="filter-section-title" style="font-size: 0.92rem; color: #38bdf8; border-bottom: 1px solid rgba(56, 189, 248, 0.2); padding-bottom: 8px;">
            <span>🔬 CRUZAMENTO DEMOGRÁFICO & DISTRIBUIÇÃO ESTIMADA DO VOTO (INFERÊNCIA ECOLÓGICA)</span>
        </div>
        <p style="font-size: 0.8rem; color: #94a3b8; margin: 6px 0 14px 0;">
            O voto individual na urna é secreto. Para descobrir <b>qual % de mulheres, divorciados ou pessoas com ensino superior votaram em cada candidato</b>, utilizamos <b>Regressão Ecológica e Mínimos Quadrados Ponderados</b> cruzando as 247 seções eleitorais de Salvador (Zona 7).
        </p>

        <div style="display: flex; flex-wrap: wrap; gap: 14px; align-items: center; margin-bottom: 16px;">
            <div style="flex: 1; min-width: 220px;">
                <label style="font-size: 0.75rem; font-weight: 700; color: #cbd5e1; text-transform: uppercase;">1. Escolha o Candidato:</label>
                <select id="crossCandidate" class="custom-range-box" style="width: 100%; margin-top: 4px; padding: 8px 12px; font-size: 0.88rem;" onchange="updateCrossAnalysis()">
                    <option value="PCT_BOLSONARO" selected>🔵 Flávio Bolsonaro</option>
                    <option value="PCT_LULA">🔴 Lula</option>
                    <option value="PCT_OUTROS">⚪ Outros (3ª Via, Brancos e Nulos)</option>
                </select>
            </div>

            <div style="flex: 1; min-width: 260px;">
                <label style="font-size: 0.75rem; font-weight: 700; color: #cbd5e1; text-transform: uppercase;">2. Escolha o Segmento Demográfico:</label>
                <select id="crossDemog" class="custom-range-box" style="width: 100%; margin-top: 4px; padding: 8px 12px; font-size: 0.88rem;" onchange="updateCrossAnalysis()">
                    <optgroup label="👥 Gênero">
                        <option value="PCT_FEM" selected>👩 Mulheres (% Feminino)</option>
                        <option value="PCT_MASC">👨 Homens (% Masculino)</option>
                    </optgroup>
                    <optgroup label="💍 Estado Civil">
                        <option value="PCT_DIVORCIADOS">💔 Divorciados (%)</option>
                        <option value="PCT_CASADOS">💍 Casados (%)</option>
                        <option value="PCT_SOLTEIROS">👤 Solteiros (%)</option>
                        <option value="PCT_VIUVOS">🕯️ Viúvos (%)</option>
                    </optgroup>
                    <optgroup label="🎓 Escolaridade">
                        <option value="PCT_SUPERIOR">🎓 Ensino Superior (%)</option>
                        <option value="PCT_BAIXA_ESCOLARIDADE">📉 Baixa Escolaridade (%)</option>
                    </optgroup>
                    <optgroup label="🎂 Faixas Etárias (Idade)">
                        <option value="PCT_JOVENS_16_24">⚡ Jovens (16 a 24 anos) (%)</option>
                        <option value="PCT_IDOSOS_60_MAIS">👴 Idosos (60+ anos) (%)</option>
                    </optgroup>
                </select>
            </div>
        </div>

        <!-- Cross Analysis Dynamic KPI Cards -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-bottom: 16px;">
            <div class="kpi-card" style="background: rgba(30, 41, 59, 0.7); border-color: rgba(56, 189, 248, 0.3);">
                <div class="kpi-lbl" id="crossResLbl">🎯 VOTO ESTIMADO NO SEGMENTO</div>
                <div class="kpi-val" id="crossResVal" style="color: #38bdf8;">--%</div>
                <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 4px;" id="crossResSub">Regressão Ecológica ponderada por votos</div>
            </div>

            <div class="kpi-card" style="background: rgba(30, 41, 59, 0.7);">
                <div class="kpi-lbl">📊 COMPARAÇÃO POR CONCENTRAÇÃO</div>
                <div style="font-size: 0.8rem; margin-top: 6px; line-height: 1.4;" id="crossBinsVal">
                    • Baixa Concentração: <b>--%</b><br>
                    • Média Concentração: <b>--%</b><br>
                    • Alta Concentração: <b>--%</b>
                </div>
            </div>

            <div class="kpi-card" style="background: rgba(30, 41, 59, 0.7);">
                <div class="kpi-lbl">📈 CORRELAÇÃO LINEAR (R)</div>
                <div class="kpi-val" id="crossCorrVal" style="color: #f59e0b;">+0.00</div>
                <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 4px;" id="crossCorrDesc">Impacto estatístico da demografia</div>
            </div>
        </div>

        <!-- Scatter Plot Canvas -->
        <div style="background: #0b0f19; border-radius: 10px; padding: 14px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 12px;">
            <div style="font-size: 0.76rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 8px;">
                📉 Gráfico de Dispersão Seção a Seção (247 Seções da Zona 7) &bull; Linha de Tendência
            </div>
            <div style="height: 240px; position: relative;">
                <canvas id="crossScatterChart"></canvas>
            </div>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 8px;">
            <button onclick="filterByHighDemog()" style="background: #1e293b; border: 1px solid #38bdf8; color: #38bdf8; padding: 6px 14px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; cursor: pointer; transition: 0.2s;">
                ⚡ Filtrar na tabela seções com alta concentração deste segmento
            </button>
        </div>
    </div>

    <!-- Interactive Candidate Filter Panel -->
    <div class="filter-panel">
        <div class="filter-section-title">
            <span>🔍 FILTRAR POR CANDIDATO & DESEMPENHO PRESIDENCIAL:</span>
        </div>
        <div class="filter-groups">
            <div class="filter-chips">
                <button class="filter-chip active-all" id="btn-all" onclick="setCandidateFilter('all')">🌟 Todos os Registros</button>
                <button class="filter-chip" id="btn-lula-60" onclick="setCandidateFilter('lula_60')">🔴 Lula &ge; 60%</button>
                <button class="filter-chip" id="btn-lula-65" onclick="setCandidateFilter('lula_65')">🔴 Lula &ge; 65% (Forte)</button>
                <button class="filter-chip" id="btn-bols-25" onclick="setCandidateFilter('bols_25')">🔵 Bolsonaro &ge; 25%</button>
                <button class="filter-chip" id="btn-bols-30" onclick="setCandidateFilter('bols_30')">🔵 Bolsonaro &ge; 30% (Destaque)</button>
                <button class="filter-chip" id="btn-outros-13" onclick="setCandidateFilter('outros_13')">⚪ Outros &ge; 13%</button>
                <button class="filter-chip" id="btn-outros-15" onclick="setCandidateFilter('outros_15')">⚪ Outros &ge; 15% (3ª Via Forte)</button>
            </div>

            <div class="custom-range-box">
                <label>🎯 Filtro Customizado:</label>
                <select id="selectCandidateFilter" onchange="onCustomSelectChange(this.value)">
                    <option value="all">Selecione um filtro rápido...</option>
                    <optgroup label="🔴 Lula Presidente">
                        <option value="lula_max">Top 10 Maior % Lula</option>
                        <option value="lula_55">Lula &ge; 55%</option>
                        <option value="lula_60">Lula &ge; 60%</option>
                        <option value="lula_65">Lula &ge; 65%</option>
                    </optgroup>
                    <optgroup label="🔵 Flávio Bolsonaro">
                        <option value="bols_max">Top 10 Maior % Flávio Bolsonaro</option>
                        <option value="bols_20">Flávio Bolsonaro &ge; 20%</option>
                        <option value="bols_25">Flávio Bolsonaro &ge; 25%</option>
                        <option value="bols_30">Flávio Bolsonaro &ge; 30%</option>
                    </optgroup>
                    <optgroup label="⚪ Outros (3ª Via, Brancos, Nulos)">
                        <option value="outros_max">Top 10 Maior % Outros</option>
                        <option value="outros_12">Outros &ge; 12%</option>
                        <option value="outros_15">Outros &ge; 15%</option>
                        <option value="outros_18">Outros &ge; 18%</option>
                    </optgroup>
                    <optgroup label="💍 Demografia / Estado Civil">
                        <option value="div_5">Divorciados &ge; 5%</option>
                        <option value="cas_30">Casados &ge; 30%</option>
                        <option value="sup_40">Ensino Superior &ge; 40%</option>
                    </optgroup>
                </select>
            </div>
        </div>

        <div class="filter-status-banner">
            <span id="filterStatusText">Exibindo todos os registros sem restrições.</span>
            <button onclick="setCandidateFilter('all')" style="background:transparent;border:none;color:#38bdf8;font-weight:700;cursor:pointer;text-decoration:underline;font-size:0.75rem;">Limpar Filtros</button>
        </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
        <button class="tab-btn active" onclick="showTab('locais')">🏫 Visão por Local de Votação (20 Colégios)</button>
        <button class="tab-btn" onclick="showTab('secoes')">🗳️ Visão por Seção Eleitoral (247 Seções)</button>
    </div>

    <!-- Tab Locais -->
    <div id="tabLocais" class="table-container">
        <table id="tableLocais" class="display" style="width:100%">
            <thead>
                <tr>
                    <th>Local / Colégio</th>
                    <th>Seções</th>
                    <th>Eleitores</th>
                    <th>Votos</th>
                    <th>Lula (%)</th>
                    <th>Flávio (%)</th>
                    <th>Outros (%)</th>
                    <th>Mulheres (%)</th>
                    <th>Solteiros (%)</th>
                    <th>Casados (%)</th>
                    <th>Divorciados (%)</th>
                    <th>Viúvos (%)</th>
                    <th>Superior (%)</th>
                    <th>Jovens 16-24 (%)</th>
                    <th>Idosos 60+ (%)</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>

    <!-- Tab Seções -->
    <div id="tabSecoes" class="table-container" style="display:none;">
        <table id="tableSecoes" class="display" style="width:100%">
            <thead>
                <tr>
                    <th>Seção</th>
                    <th>Local de Votação</th>
                    <th>Urna</th>
                    <th>Eleitores</th>
                    <th>Votos</th>
                    <th>Lula (%)</th>
                    <th>Flávio (%)</th>
                    <th>Outros (%)</th>
                    <th>Mulheres (%)</th>
                    <th>Solteiros (%)</th>
                    <th>Casados (%)</th>
                    <th>Divorciados (%)</th>
                    <th>Viúvos (%)</th>
                    <th>Superior (%)</th>
                    <th>Jovens 16-24 (%)</th>
                    <th>Idosos 60+ (%)</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>

    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const locaisData = __LOCAIS_JSON__;
        const secoesData = __SECOES_JSON__;

        let dtLocais = null;
        let dtSecoes = null;
        let currentFilter = 'all';
        let crossChart = null;

        const DEMOG_LABELS = {
            'PCT_FEM': 'Mulheres',
            'PCT_MASC': 'Homens',
            'PCT_DIVORCIADOS': 'Divorciados',
            'PCT_CASADOS': 'Casados',
            'PCT_SOLTEIROS': 'Solteiros',
            'PCT_VIUVOS': 'Viúvos',
            'PCT_SUPERIOR': 'Ensino Superior',
            'PCT_BAIXA_ESCOLARIDADE': 'Baixa Escolaridade',
            'PCT_JOVENS_16_24': 'Jovens (16-24 anos)',
            'PCT_IDOSOS_60_MAIS': 'Idosos (60+ anos)'
        };

        const CAND_LABELS = {
            'PCT_BOLSONARO': 'Flávio Bolsonaro',
            'PCT_LULA': 'Lula',
            'PCT_OUTROS': 'Outros (3ª Via, Brancos e Nulos)'
        };

        function updateCrossAnalysis() {
            const cand = $('#crossCandidate').val();
            const demog = $('#crossDemog').val();

            const candName = CAND_LABELS[cand];
            const demogName = DEMOG_LABELS[demog];

            // 1. Extrair pontos das seções
            const points = [];
            let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0, sumW = 0;
            let n = secoesData.length;

            const demogVals = [];

            secoesData.forEach(s => {
                const x = parseFloat(s[demog]) || 0;
                const y = parseFloat(s[cand]) || 0;
                const w = parseFloat(s.TOTAL_VOTOS) || 1;

                points.push({ x: x, y: y, secao: s.NR_SECAO, local: s.NM_LOCAL_VOTACAO, votos: s.TOTAL_VOTOS });
                demogVals.push(x);

                sumX += x * w;
                sumY += y * w;
                sumXY += x * y * w;
                sumX2 += x * x * w;
                sumY2 += y * y * w;
                sumW += w;
            });

            // Regressão Ponderada (WLS)
            const meanX = sumX / sumW;
            const meanY = sumY / sumW;
            const beta = (sumXY - sumW * meanX * meanY) / (sumX2 - sumW * meanX * meanX);
            const alpha = meanY - beta * meanX;

            // Coeficiente de Correlação R de Pearson
            const unweightedX = points.map(p => p.x);
            const unweightedY = points.map(p => p.y);
            const avgX = unweightedX.reduce((a, b) => a + b, 0) / n;
            const avgY = unweightedY.reduce((a, b) => a + b, 0) / n;
            let numCorr = 0, denX = 0, denY = 0;
            for (let i = 0; i < n; i++) {
                const dx = unweightedX[i] - avgX;
                const dy = unweightedY[i] - avgY;
                numCorr += dx * dy;
                denX += dx * dx;
                denY += dy * dy;
            }
            const rCorr = denX > 0 && denY > 0 ? (numCorr / Math.sqrt(denX * denY)) : 0;

            // 2. Cálculo dos Tercis (Baixa, Média e Alta Concentração)
            demogVals.sort((a, b) => a - b);
            const q33 = demogVals[Math.floor(n * 0.33)];
            const q67 = demogVals[Math.floor(n * 0.67)];

            let lowVotes = 0, lowTot = 0;
            let midVotes = 0, midTot = 0;
            let highVotes = 0, highTot = 0;

            secoesData.forEach(s => {
                const x = parseFloat(s[demog]) || 0;
                const tot = parseFloat(s.TOTAL_VOTOS) || 0;
                let v = 0;
                if (cand === 'PCT_LULA') v = parseFloat(s.VOTOS_LULA) || 0;
                else if (cand === 'PCT_BOLSONARO') v = parseFloat(s.VOTOS_BOLSONARO) || 0;
                else v = parseFloat(s.VOTOS_OUTROS) || 0;

                if (x <= q33) { lowVotes += v; lowTot += tot; }
                else if (x >= q67) { highVotes += v; highTot += tot; }
                else { midVotes += v; midTot += tot; }
            });

            const pctLow = lowTot > 0 ? ((lowVotes * 100.0) / lowTot).toFixed(1) : '0.0';
            const pctMid = midTot > 0 ? ((midVotes * 100.0) / midTot).toFixed(1) : '0.0';
            const pctHigh = highTot > 0 ? ((highVotes * 100.0) / highTot).toFixed(1) : '0.0';

            // Atualizar KPIs
            $('#crossResLbl').text(`🎯 VOTO ESTIMADO DE ${demogName.toUpperCase()} EM ${candName.toUpperCase()}`);
            $('#crossResVal').text(`${pctHigh}%`);
            $('#crossResSub').text(`Média real ponderada nas seções de maior concentração de ${demogName} (> ${q67.toFixed(1)}%)`);

            $('#crossBinsVal').html(`
                • <b>Baixa Concentração (&le; ${q33.toFixed(1)}%):</b> <span style="color:#cbd5e1;font-weight:bold;">${pctLow}%</span> votos<br>
                • <b>Média Concentração (${q33.toFixed(1)}% a ${q67.toFixed(1)}%):</b> <span style="color:#cbd5e1;font-weight:bold;">${pctMid}%</span> votos<br>
                • <b>Alta Concentração (&ge; ${q67.toFixed(1)}%):</b> <span style="color:#38bdf8;font-weight:bold;">${pctHigh}%</span> votos
            `);

            let corrColor = '#f59e0b';
            let corrText = 'Correlação Neutra';
            if (rCorr >= 0.5) { corrColor = '#22c55e'; corrText = 'Forte Correlação Positiva ↗️'; }
            else if (rCorr >= 0.2) { corrColor = '#38bdf8'; corrText = 'Moderada Correlação Positiva ↗️'; }
            else if (rCorr <= -0.5) { corrColor = '#ef4444'; corrText = 'Forte Correlação Negativa ↘️'; }
            else if (rCorr <= -0.2) { corrColor = '#f97316'; corrText = 'Moderada Correlação Negativa ↘️'; }

            $('#crossCorrVal').html(`<span style="color:${corrColor}">${rCorr >= 0 ? '+' : ''}${rCorr.toFixed(2)}</span>`);
            $('#crossCorrDesc').text(corrText);

            // 3. Atualizar / Renderizar Scatter Plot com Chart.js
            const minX = Math.min(...unweightedX);
            const maxX = Math.max(...unweightedX);
            const trendLine = [
                { x: minX, y: alpha + beta * minX },
                { x: maxX, y: alpha + beta * maxX }
            ];

            let pointColor = 'rgba(56, 189, 248, 0.6)';
            if (cand === 'PCT_LULA') pointColor = 'rgba(239, 68, 68, 0.6)';
            else if (cand === 'PCT_BOLSONARO') pointColor = 'rgba(59, 130, 246, 0.6)';
            else pointColor = 'rgba(148, 163, 184, 0.6)';

            const ctx = document.getElementById('crossScatterChart').getContext('2d');
            if (crossChart) crossChart.destroy();

            crossChart = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [
                        {
                            label: 'Seções Eleitorais (Zona 7)',
                            data: points,
                            backgroundColor: pointColor,
                            borderColor: 'transparent',
                            pointRadius: 4,
                            pointHoverRadius: 6
                        },
                        {
                            type: 'line',
                            label: 'Linha de Tendência (Regressão)',
                            data: trendLine,
                            borderColor: '#38bdf8',
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: false,
                            tension: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: '#cbd5e1', font: { family: 'Outfit', size: 11 } } },
                        tooltip: {
                            callbacks: {
                                label: ctx => {
                                    const p = ctx.raw;
                                    if (p.secao) {
                                        return `Seção ${p.secao} (${p.local}): ${demogName} = ${p.x}% | ${candName} = ${p.y}% (${p.votos} votos)`;
                                    }
                                    return `Tendência: ${p.x.toFixed(1)}% -> ${p.y.toFixed(1)}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: { display: true, text: `${demogName} (%)`, color: '#94a3b8', font: { weight: 'bold' } },
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#94a3b8' }
                        },
                        y: {
                            title: { display: true, text: `${candName} (% Votos)`, color: '#94a3b8', font: { weight: 'bold' } },
                            grid: { color: 'rgba(255,255,255,0.05)' },
                            ticks: { color: '#94a3b8' }
                        }
                    }
                }
            });
        }

        function filterByHighDemog() {
            const demog = $('#crossDemog').val();
            const demogVals = secoesData.map(s => parseFloat(s[demog]) || 0).sort((a, b) => a - b);
            const q67 = demogVals[Math.floor(demogVals.length * 0.67)];

            currentFilter = 'custom_demog_high';
            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                if (currentFilter !== 'custom_demog_high') return true;
                const isLocais = settings.nTable.id === 'tableLocais';
                const row = isLocais ? locaisData[dataIndex] : secoesData[dataIndex];
                if (!row) return true;
                return (parseFloat(row[demog]) || 0) >= q67;
            });

            if (dtLocais) dtLocais.draw();
            if (dtSecoes) dtSecoes.draw();

            const countSec = dtSecoes ? dtSecoes.rows({ filter: 'applied' }).count() : 0;
            $('#filterStatusText').text(`⚡ Filtrando seções com Alta Concentração de ${DEMOG_LABELS[demog]} (≥ ${q67.toFixed(1)}%). Visíveis: ${countSec}/247 seções.`);
        }

        // Custom DataTables Filter Function
        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
            if (currentFilter === 'all') return true;
            if (currentFilter === 'custom_demog_high') return true; // Handled dynamically

            const isLocais = settings.nTable.id === 'tableLocais';
            const row = isLocais ? locaisData[dataIndex] : secoesData[dataIndex];
            if (!row) return true;

            const lula = parseFloat(row.PCT_LULA) || 0;
            const bols = parseFloat(row.PCT_BOLSONARO) || 0;
            const outros = parseFloat(row.PCT_OUTROS) || 0;
            const div = parseFloat(row.PCT_DIVORCIADOS) || 0;
            const cas = parseFloat(row.PCT_CASADOS) || 0;
            const sup = parseFloat(row.PCT_SUPERIOR) || 0;

            if (currentFilter === 'lula_55') return lula >= 55.0;
            if (currentFilter === 'lula_60') return lula >= 60.0;
            if (currentFilter === 'lula_65') return lula >= 65.0;

            if (currentFilter === 'bols_20') return bols >= 20.0;
            if (currentFilter === 'bols_25') return bols >= 25.0;
            if (currentFilter === 'bols_30') return bols >= 30.0;

            if (currentFilter === 'outros_12') return outros >= 12.0;
            if (currentFilter === 'outros_13') return outros >= 13.0;
            if (currentFilter === 'outros_15') return outros >= 15.0;
            if (currentFilter === 'outros_18') return outros >= 18.0;

            if (currentFilter === 'div_5') return div >= 5.0;
            if (currentFilter === 'cas_30') return cas >= 30.0;
            if (currentFilter === 'sup_40') return sup >= 40.0;

            return true;
        });

        function setCandidateFilter(filterType) {
            currentFilter = filterType;
            
            // Reset chip active classes
            $('.filter-chip').removeClass('active-all active-lula active-bols active-outros');
            $('#selectCandidateFilter').val(filterType);

            let statusMsg = 'Exibindo todos os registros.';
            if (filterType === 'all') {
                $('#btn-all').addClass('active-all');
            } else if (filterType === 'lula_60') {
                $('#btn-lula-60').addClass('active-lula');
                statusMsg = '🔴 Filtrando por: Lula &ge; 60% dos votos.';
            } else if (filterType === 'lula_65') {
                $('#btn-lula-65').addClass('active-lula');
                statusMsg = '🔴 Filtrando por: Lula &ge; 65% dos votos (Votação Alta).';
            } else if (filterType === 'bols_25') {
                $('#btn-bols-25').addClass('active-bols');
                statusMsg = '🔵 Filtrando por: Flávio Bolsonaro &ge; 25% dos votos.';
            } else if (filterType === 'bols_30') {
                $('#btn-bols-30').addClass('active-bols');
                statusMsg = '🔵 Filtrando por: Flávio Bolsonaro &ge; 30% dos votos (Destaque).';
            } else if (filterType === 'outros_13') {
                $('#btn-outros-13').addClass('active-outros');
                statusMsg = '⚪ Filtrando por: Outros (3ª Via, Brancos, Nulos) &ge; 13%.';
            } else if (filterType === 'outros_15') {
                $('#btn-outros-15').addClass('active-outros');
                statusMsg = '⚪ Filtrando por: Outros (3ª Via, Brancos, Nulos) &ge; 15% (3ª Via Forte).';
            } else if (filterType === 'lula_max') {
                currentFilter = 'all';
                dtLocais.order([[4, 'desc']]).draw();
                dtSecoes.order([[5, 'desc']]).draw();
                statusMsg = '🔴 Ordenado por maior % de votos em Lula.';
                $('#filterStatusText').text(statusMsg);
                return;
            } else if (filterType === 'bols_max') {
                currentFilter = 'all';
                dtLocais.order([[5, 'desc']]).draw();
                dtSecoes.order([[6, 'desc']]).draw();
                statusMsg = '🔵 Ordenado por maior % de votos em Flávio Bolsonaro.';
                $('#filterStatusText').text(statusMsg);
                return;
            } else if (filterType === 'outros_max') {
                currentFilter = 'all';
                dtLocais.order([[6, 'desc']]).draw();
                dtSecoes.order([[7, 'desc']]).draw();
                statusMsg = '⚪ Ordenado por maior % de votos em Outros (3ª Via, Brancos e Nulos).';
                $('#filterStatusText').text(statusMsg);
                return;
            } else {
                statusMsg = `🎯 Filtro customizado ativo: ${filterType}`;
            }

            if (dtLocais) dtLocais.draw();
            if (dtSecoes) dtSecoes.draw();

            const countLoc = dtLocais ? dtLocais.rows({ filter: 'applied' }).count() : 20;
            const countSec = dtSecoes ? dtSecoes.rows({ filter: 'applied' }).count() : 247;
            $('#filterStatusText').text(`${statusMsg} (Visíveis: ${countLoc}/20 locais e ${countSec}/247 seções)`);
        }

        function onCustomSelectChange(val) {
            setCandidateFilter(val);
        }

        $(document).ready(function() {
            dtLocais = $('#tableLocais').DataTable({
                data: locaisData,
                pageLength: 25,
                order: [[2, 'desc']],
                columns: [
                    { data: 'NM_LOCAL_VOTACAO' },
                    { data: 'QTD_SECOES' },
                    { data: 'TOTAL_ELEITORES', render: v => Number(v).toLocaleString('pt-BR') },
                    { data: 'TOTAL_VOTOS', render: v => Number(v).toLocaleString('pt-BR') },
                    { data: 'PCT_LULA', render: v => `<span class="pct-pill" style="background:#450a0a;color:#f87171;">${v}%</span>` },
                    { data: 'PCT_BOLSONARO', render: v => `<span class="pct-pill" style="background:#172554;color:#60a5fa;">${v}%</span>` },
                    { data: 'PCT_OUTROS', render: v => `<span class="pct-pill" style="background:#334155;color:#cbd5e1;">${v}%</span>` },
                    { data: 'PCT_FEM', render: v => v + '%' },
                    { data: 'PCT_SOLTEIROS', render: v => v + '%' },
                    { data: 'PCT_CASADOS', render: v => v + '%' },
                    { data: 'PCT_DIVORCIADOS', render: v => `<span style="color:#f472b6;font-weight:bold;">${v}%</span>` },
                    { data: 'PCT_VIUVOS', render: v => v + '%' },
                    { data: 'PCT_SUPERIOR', render: v => `<b style="color:#c084fc;">${v}%</b>` },
                    { data: 'PCT_JOVENS_16_24', render: v => v + '%' },
                    { data: 'PCT_IDOSOS_60_MAIS', render: v => `<b style="color:#fb923c;">${v}%</b>` }
                ],
                language: {
                    url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/pt-BR.json'
                }
            });

            dtSecoes = $('#tableSecoes').DataTable({
                data: secoesData,
                pageLength: 25,
                order: [[0, 'asc']],
                columns: [
                    { data: 'NR_SECAO' },
                    { data: 'NM_LOCAL_VOTACAO' },
                    { data: 'MODELO_URNA', render: v => v === 'UE2015' ? '<span style="color:#f59e0b;font-weight:bold;">UE2015</span>' : '<span style="color:#38bdf8;">UE2020</span>' },
                    { data: 'TOTAL_ELEITORES', render: v => Number(v).toLocaleString('pt-BR') },
                    { data: 'TOTAL_VOTOS', render: v => Number(v).toLocaleString('pt-BR') },
                    { data: 'PCT_LULA', render: v => `<span class="pct-pill" style="background:#450a0a;color:#f87171;">${v}%</span>` },
                    { data: 'PCT_BOLSONARO', render: v => `<span class="pct-pill" style="background:#172554;color:#60a5fa;">${v}%</span>` },
                    { data: 'PCT_OUTROS', render: v => `<span class="pct-pill" style="background:#334155;color:#cbd5e1;">${v}%</span>` },
                    { data: 'PCT_FEM', render: v => v + '%' },
                    { data: 'PCT_SOLTEIROS', render: v => v + '%' },
                    { data: 'PCT_CASADOS', render: v => v + '%' },
                    { data: 'PCT_DIVORCIADOS', render: v => `<span style="color:#f472b6;font-weight:bold;">${v}%</span>` },
                    { data: 'PCT_VIUVOS', render: v => v + '%' },
                    { data: 'PCT_SUPERIOR', render: v => `<b style="color:#c084fc;">${v}%</b>` },
                    { data: 'PCT_JOVENS_16_24', render: v => v + '%' },
                    { data: 'PCT_IDOSOS_60_MAIS', render: v => `<b style="color:#fb923c;">${v}%</b>` }
                ],
                language: {
                    url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/pt-BR.json'
                }
            });

            // Inicializar Análise de Cruzamento Demográfico
            updateCrossAnalysis();
        });

        function showTab(tab) {
            if (tab === 'locais') {
                $('#tabLocais').show();
                $('#tabSecoes').hide();
                $('.tab-btn:first').addClass('active');
                $('.tab-btn:last').removeClass('active');
            } else {
                $('#tabLocais').hide();
                $('#tabSecoes').show();
                $('.tab-btn:first').removeClass('active');
                $('.tab-btn:last').addClass('active');
            }
        }
    </script>
</body>
</html>"""

    html = (template
        .replace("__LOCAIS_JSON__", locais_json)
        .replace("__SECOES_JSON__", secoes_json)
        .replace("__TOT_ELEITORES__", f"{tot_eleitores:,}")
        .replace("__PCT_LULA__", str(pct_lula))
        .replace("__TOT_LULA__", f"{tot_lula:,}")
        .replace("__PCT_BOLS__", str(pct_bols))
        .replace("__TOT_BOLS__", f"{tot_bols:,}")
        .replace("__PCT_OUTROS__", str(pct_outros))
        .replace("__TOT_OUTROS__", f"{tot_outros:,}")
        .replace("__PCT_SOLT__", str(pct_solt))
        .replace("__PCT_CAS__", str(pct_cas))
        .replace("__PCT_DIV__", str(pct_div))
        .replace("__PCT_VIU__", str(pct_viu))
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Relatório Interativo HTML da Zona 7 gerado: {output_path}")

if __name__ == "__main__":
    export_salvador_zona_7()
