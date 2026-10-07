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
                
                -- Estado Civil
                SUM(CASE WHEN DS_ESTADO_CIVIL = 'SOLTEIRO' THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_SOLTEIROS,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL = 'SOLTEIRO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_SOLTEIROS,
                SUM(CASE WHEN DS_ESTADO_CIVIL = 'CASADO' THEN QT_ELEITORES ELSE 0 END) AS ELEITORES_CASADOS,
                ROUND(SUM(CASE WHEN DS_ESTADO_CIVIL = 'CASADO' THEN QT_ELEITORES ELSE 0 END) * 100.0 / SUM(QT_ELEITORES), 2) AS PCT_CASADOS,
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

    # Preparar JSON para a tabela interativa
    locais_json = df_locais.to_json(orient="records", force_ascii=False)
    secoes_json = df_secoes.to_json(orient="records", force_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Salvador - Zona Eleitoral 007: Votos Presidente e Demografia 2026</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }}
        body {{ background: #0b0f19; color: #f8fafc; padding: 24px; }}
        .header {{ margin-bottom: 20px; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; background: #38bdf8; color: #000; }}
        h1 {{ font-size: 1.6rem; font-weight: 700; margin: 8px 0 4px 0; }}
        p {{ color: #94a3b8; font-size: 0.88rem; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 16px 0 24px 0; }}
        .kpi-card {{ background: #0f172a; padding: 14px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); }}
        .kpi-val {{ font-size: 1.35rem; font-weight: 700; }}
        .kpi-lbl {{ font-size: 0.72rem; color: #94a3b8; }}
        .tabs {{ display: flex; gap: 10px; margin-bottom: 16px; }}
        .tab-btn {{ background: #1e293b; border: 1px solid #334155; color: #f8fafc; padding: 10px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: 0.2s; }}
        .tab-btn.active {{ background: #38bdf8; color: #000; border-color: #38bdf8; }}
        .table-container {{ background: #0f172a; border-radius: 14px; padding: 18px; border: 1px solid rgba(255,255,255,0.08); overflow-x: auto; }}
        table.dataTable {{ width: 100% !important; background: transparent; color: #f8fafc; font-size: 0.82rem; }}
        table.dataTable thead th {{ background: #1e293b; color: #38bdf8; font-weight: 700; border-bottom: 1px solid #334155 !important; padding: 10px 8px; text-align: left; }}
        table.dataTable tbody td {{ border-bottom: 1px solid rgba(255,255,255,0.05); padding: 8px; }}
        table.dataTable tbody tr:hover {{ background: rgba(56, 189, 248, 0.08); }}
        .dataTables_wrapper .dataTables_length, .dataTables_wrapper .dataTables_filter, .dataTables_wrapper .dataTables_info, .dataTables_wrapper .dataTables_paginate {{ color: #94a3b8 !important; font-size: 0.8rem; margin: 10px 0; }}
        .dataTables_wrapper .dataTables_filter input {{ background: #1e293b; border: 1px solid #334155; border-radius: 6px; color: #fff; padding: 6px 10px; outline: none; }}
        .pct-pill {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }}
    </style>
</head>
<body>
    <div class="header">
        <span class="badge">ZONA ELEITORAL 007 &bull; SALVADOR / BA</span>
        <h1>Votação para Presidente & Estratificação Demográfica Completa</h1>
        <p>Eleições Gerais 2026 (1º Turno) &bull; Cruzamento Seção a Seção com o Perfil do Eleitorado TSE</p>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-val" style="color: #38bdf8;">{tot_eleitores:,}</div>
            <div class="kpi-lbl">👥 Eleitores Aptos (Zona 7)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #22c55e;">{tot_votos:,}</div>
            <div class="kpi-lbl">🗳️ Votos Apurados (247 Seções)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #ef4444;">{pct_lula}%</div>
            <div class="kpi-lbl">🔴 Lula ({tot_lula:,} votos)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #3b82f6;">{pct_bols}%</div>
            <div class="kpi-lbl">🔵 Flávio Bolsonaro ({tot_bols:,} votos)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #cbd5e1;">{pct_outros}%</div>
            <div class="kpi-lbl">⚪ Outros / 3ª Via + Nulos ({tot_outros:,} votos)</div>
        </div>
    </div>

    <div class="tabs">
        <button class="tab-btn active" onclick="showTab('locais')">🏫 Visão por Local de Votação (20 Colégios)</button>
        <button class="tab-btn" onclick="showTab('secoes')">🗳️ Visão por Seção Eleitoral (247 Seções)</button>
    </div>

    <div id="tabLocais" class="table-container">
        <table id="tableLocais" class="display" style="width:100%">
            <thead>
                <tr>
                    <th>Local / Colégio</th>
                    <th>Seções</th>
                    <th>Eleitores</th>
                    <th>Total Votos</th>
                    <th>Lula (%)</th>
                    <th>Flávio (%)</th>
                    <th>Outros (%)</th>
                    <th>Mulheres (%)</th>
                    <th>Solteiros (%)</th>
                    <th>Casados (%)</th>
                    <th>Superior (%)</th>
                    <th>Jovens 16-24 (%)</th>
                    <th>Idosos 60+ (%)</th>
                </tr>
            </thead>
            <tbody></tbody>
        </table>
    </div>

    <div id="tabSecoes" class="table-container" style="display:none;">
        <table id="tableSecoes" class="display" style="width:100%">
            <thead>
                <tr>
                    <th>Seção</th>
                    <th>Local de Votação</th>
                    <th>Urna</th>
                    <th>Eleitores</th>
                    <th>Total Votos</th>
                    <th>Lula (%)</th>
                    <th>Flávio (%)</th>
                    <th>Outros (%)</th>
                    <th>Mulheres (%)</th>
                    <th>Solteiros (%)</th>
                    <th>Casados (%)</th>
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
    <script>
        const locaisData = {locais_json};
        const secoesData = {secoes_json};

        $(document).ready(function() {{
            $('#tableLocais').DataTable({{
                data: locaisData,
                pageLength: 25,
                order: [[2, 'desc']],
                columns: [
                    {{ data: 'NM_LOCAL_VOTACAO' }},
                    {{ data: 'QTD_SECOES' }},
                    {{ data: 'TOTAL_ELEITORES', render: v => Number(v).toLocaleString('pt-BR') }},
                    {{ data: 'TOTAL_VOTOS', render: v => Number(v).toLocaleString('pt-BR') }},
                    {{ data: 'PCT_LULA', render: v => `<span class="pct-pill" style="background:#450a0a;color:#f87171;">${{v}}%</span>` }},
                    {{ data: 'PCT_BOLSONARO', render: v => `<span class="pct-pill" style="background:#172554;color:#60a5fa;">${{v}}%</span>` }},
                    {{ data: 'PCT_OUTROS', render: v => `<span class="pct-pill" style="background:#334155;color:#cbd5e1;">${{v}}%</span>` }},
                    {{ data: 'PCT_FEM', render: v => v + '%' }},
                    {{ data: 'PCT_SOLTEIROS', render: v => v + '%' }},
                    {{ data: 'PCT_CASADOS', render: v => v + '%' }},
                    {{ data: 'PCT_SUPERIOR', render: v => `<b style="color:#c084fc;">${{v}}%</b>` }},
                    {{ data: 'PCT_JOVENS_16_24', render: v => v + '%' }},
                    {{ data: 'PCT_IDOSOS_60_MAIS', render: v => `<b style="color:#fb923c;">${{v}}%</b>` }}
                ],
                language: {{
                    url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/pt-BR.json'
                }}
            }});

            $('#tableSecoes').DataTable({{
                data: secoesData,
                pageLength: 25,
                order: [[0, 'asc']],
                columns: [
                    {{ data: 'NR_SECAO' }},
                    {{ data: 'NM_LOCAL_VOTACAO' }},
                    {{ data: 'MODELO_URNA', render: v => v === 'UE2015' ? '<span style="color:#f59e0b;font-weight:bold;">UE2015</span>' : '<span style="color:#38bdf8;">UE2020</span>' }},
                    {{ data: 'TOTAL_ELEITORES', render: v => Number(v).toLocaleString('pt-BR') }},
                    {{ data: 'TOTAL_VOTOS', render: v => Number(v).toLocaleString('pt-BR') }},
                    {{ data: 'PCT_LULA', render: v => `<span class="pct-pill" style="background:#450a0a;color:#f87171;">${{v}}%</span>` }},
                    {{ data: 'PCT_BOLSONARO', render: v => `<span class="pct-pill" style="background:#172554;color:#60a5fa;">${{v}}%</span>` }},
                    {{ data: 'PCT_OUTROS', render: v => `<span class="pct-pill" style="background:#334155;color:#cbd5e1;">${{v}}%</span>` }},
                    {{ data: 'PCT_FEM', render: v => v + '%' }},
                    {{ data: 'PCT_SOLTEIROS', render: v => v + '%' }},
                    {{ data: 'PCT_CASADOS', render: v => v + '%' }},
                    {{ data: 'PCT_SUPERIOR', render: v => `<b style="color:#c084fc;">${{v}}%</b>` }},
                    {{ data: 'PCT_JOVENS_16_24', render: v => v + '%' }},
                    {{ data: 'PCT_IDOSOS_60_MAIS', render: v => `<b style="color:#fb923c;">${{v}}%</b>` }}
                ],
                language: {{
                    url: 'https://cdn.datatables.net/plug-ins/1.13.7/i18n/pt-BR.json'
                }}
            }});
        }});

        function showTab(tab) {{
            if (tab === 'locais') {{
                $('#tabLocais').show();
                $('#tabSecoes').hide();
                $('.tab-btn:first').addClass('active');
                $('.tab-btn:last').removeClass('active');
            }} else {{
                $('#tabLocais').hide();
                $('#tabSecoes').show();
                $('.tab-btn:first').removeClass('active');
                $('.tab-btn:last').addClass('active');
            }}
        }}
    </script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Relatório Interativo HTML da Zona 7 gerado: {output_path}")

if __name__ == "__main__":
    export_salvador_zona_7()
