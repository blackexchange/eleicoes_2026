"""
Gera o ranking dos bairros de Salvador por percentual de votos em Flávio Bolsonaro (2026),
cruzando com os indicadores de escolaridade (% de Ensino Superior) do eleitorado apto.

Fontes de dados (DuckDB local):
- votacao_presidente_secao_2026_BA
- locais_votacao_dedup
- perfil_eleitorado_2026_BA
"""

import os
import sys
import duckdb
import pandas as pd

def gerar_ranking_salvador(
    db_path: str = "data/processed/eleicoes.duckdb",
    output_processed_csv: str = "data/processed/ranking_bairros_salvador_flavio_bolsonaro_ensino_superior.csv",
    output_root_csv: str = "ranking_bairros_salvador_flavio_bolsonaro_ensino_superior.csv"
):
    print(f"[*] Conectando ao banco de dados: {db_path}...")
    con = duckdb.connect(db_path, read_only=True)

    query = """
    WITH votacao_bairro AS (
        SELECT 
            TRIM(UPPER(l.NM_BAIRRO)) as bairro,
            COUNT(DISTINCT v.NR_ZONA || '-' || v.NR_SECAO) as qtd_secoes_eleitorais,
            SUM(CASE WHEN v.NR_VOTAVEL = 22 THEN v.QT_VOTOS ELSE 0 END) as votos_flavio_bolsonaro,
            SUM(CASE WHEN v.NR_VOTAVEL NOT IN (95, 96) THEN v.QT_VOTOS ELSE 0 END) as votos_validos_totais,
            SUM(v.QT_VOTOS) as votos_totais_apurados,
            SUM(CASE WHEN v.NR_VOTAVEL = 13 THEN v.QT_VOTOS ELSE 0 END) as votos_lula
        FROM votacao_presidente_secao_2026_BA v
        JOIN locais_votacao_dedup l 
          ON TRY_CAST(l.NR_ZONA AS BIGINT) = v.NR_ZONA 
         AND TRY_CAST(l.NR_SECAO AS BIGINT) = v.NR_SECAO
         AND (l.CD_MUNICIPIO = '38490' OR l.NM_MUNICIPIO ILIKE '%SALVADOR%')
        WHERE v.CD_MUNICIPIO = 38490
        GROUP BY TRIM(UPPER(l.NM_BAIRRO))
    ),
    perfil_bairro AS (
        SELECT 
            TRIM(UPPER(l.NM_BAIRRO)) as bairro,
            SUM(p.QT_ELEITORES) as eleitores_aptos_bairro,
            SUM(CASE WHEN p.DS_GRAU_ESCOLARIDADE = 'SUPERIOR COMPLETO' THEN p.QT_ELEITORES ELSE 0 END) as eleitores_superior_completo,
            SUM(CASE WHEN p.DS_GRAU_ESCOLARIDADE = 'SUPERIOR INCOMPLETO' THEN p.QT_ELEITORES ELSE 0 END) as eleitores_superior_incompleto,
            SUM(CASE WHEN p.DS_GRAU_ESCOLARIDADE IN ('SUPERIOR COMPLETO', 'SUPERIOR INCOMPLETO') THEN p.QT_ELEITORES ELSE 0 END) as eleitores_ensino_superior_total
        FROM perfil_eleitorado_2026_BA p
        JOIN locais_votacao_dedup l 
          ON TRY_CAST(l.NR_ZONA AS BIGINT) = p.NR_ZONA 
         AND TRY_CAST(l.NR_SECAO AS BIGINT) = p.NR_SECAO
         AND (l.CD_MUNICIPIO = '38490' OR l.NM_MUNICIPIO ILIKE '%SALVADOR%')
        WHERE p.CD_MUNICIPIO = 38490
        GROUP BY TRIM(UPPER(l.NM_BAIRRO))
    )
    SELECT 
        v.bairro,
        v.qtd_secoes_eleitorais,
        v.votos_flavio_bolsonaro,
        v.votos_validos_totais,
        ROUND(100.0 * v.votos_flavio_bolsonaro / NULLIF(v.votos_validos_totais, 0), 2) as pct_votos_validos_flavio,
        v.votos_totais_apurados,
        ROUND(100.0 * v.votos_flavio_bolsonaro / NULLIF(v.votos_totais_apurados, 0), 2) as pct_votos_totais_flavio,
        v.votos_lula,
        ROUND(100.0 * v.votos_lula / NULLIF(v.votos_validos_totais, 0), 2) as pct_votos_validos_lula,
        p.eleitores_aptos_bairro,
        p.eleitores_superior_completo,
        ROUND(100.0 * p.eleitores_superior_completo / NULLIF(p.eleitores_aptos_bairro, 0), 2) as pct_superior_completo,
        p.eleitores_superior_incompleto,
        ROUND(100.0 * p.eleitores_superior_incompleto / NULLIF(p.eleitores_aptos_bairro, 0), 2) as pct_superior_incompleto,
        p.eleitores_ensino_superior_total,
        ROUND(100.0 * p.eleitores_ensino_superior_total / NULLIF(p.eleitores_aptos_bairro, 0), 2) as pct_ensino_superior_total
    FROM votacao_bairro v
    JOIN perfil_bairro p ON v.bairro = p.bairro
    ORDER BY pct_votos_validos_flavio DESC, votos_flavio_bolsonaro DESC
    """

    print("[*] Executando agregação analítica por bairro...")
    df = con.execute(query).df()
    con.close()

    # Mapeamento para restaurar caracteres acentuados corrompidos na fonte bruta
    fix_map = {
        'ARMA\ufffdO': 'ARMAÇÃO',
        'BOA VISTA DE S\ufffdO CAETANO': 'BOA VISTA DE SÃO CAETANO',
        'BOM JU\ufffd': 'BOM JUÁ',
        "CAIXA D'\ufffdGUA": "CAIXA D'ÁGUA",
        'CALABET\ufffdO': 'CALABETÃO',
        'CAMINHO DAS \ufffdRVORES': 'CAMINHO DAS ÁRVORES',
        'CAMPINAS DE PIRAJ\ufffd': 'CAMPINAS DE PIRAJÁ',
        'CAPELINHA DE S\ufffdO CAETANO': 'CAPELINHA DE SÃO CAETANO',
        'FEDERA\ufffdO': 'FEDERAÇÃO',
        'GRA\ufffdA': 'GRAÇA',
        'ILHA DE MAR\ufffd': 'ILHA DE MARÉ',
        'IMBU\ufffd': 'IMBUÍ',
        'ITAPU\ufffd': 'ITAPUÃ',
        'JARDIM ARMA\ufffdO': 'JARDIM ARMAÇÃO',
        'JARDIM NOVA ESPERAN\ufffdA': 'JARDIM NOVA ESPERANÇA',
        'JARDIM SANTO IN\ufffdCIO': 'JARDIM SANTO INÁCIO',
        'MERC\ufffdS': 'MERCÊS',
        'NAZAR\ufffd': 'NAZARÉ',
        'NOVA BRAS\ufffdLIA': 'NOVA BRASÍLIA',
        'NOVA ESPERAN\ufffdA': 'NOVA ESPERANÇA',
        'PARQUE S\ufffdO CRIST\ufffdV\ufffdO': 'PARQUE SÃO CRISTÓVÃO',
        'PAU MI\ufffdDO': 'PAU MIÚDO',
        'PERNAMBU\ufffdS': 'PERNAMBUÉS',
        'PIAT\ufffd': 'PIATÃ',
        'PIRAJ\ufffd': 'PIRAJÁ',
        'PITUA\ufffdU': 'PITUAÇU',
        'S\ufffdO CAETANO': 'SÃO CAETANO',
        'S\ufffdO CRIST\ufffdV\ufffdO': 'SÃO CRISTÓVÃO',
        'S\ufffdO GON\ufffdALO': 'SÃO GONÇALO',
        'S\ufffdO GON\ufffdALO DO RETIRO': 'SÃO GONÇALO DO RETIRO',
        'S\ufffdO JO\ufffdO DO CABRITO': 'SÃO JOÃO DO CABRITO',
        'S\ufffdO MARCOS': 'SÃO MARCOS',
        'S\ufffdO PEDRO': 'SÃO PEDRO',
        'S\ufffdO TOM\ufffd': 'SÃO TOMÉ',
        'TUBAR\ufffdO': 'TUBARÃO',
        'VAL\ufffdRIA': 'VALÉRIA',
        'VILA CAN\ufffdRIA': 'VILA CANÁRIA',
        '\ufffdGUAS CLARAS': 'ÁGUAS CLARAS'
    }
    df['bairro'] = df['bairro'].replace(fix_map)

    # Adicionar posição no ranking (1-indexed)
    df.insert(0, "posicao_ranking", range(1, len(df) + 1))

    # Formatar tipos inteiros
    int_cols = [
        "posicao_ranking", "qtd_secoes_eleitorais", "votos_flavio_bolsonaro",
        "votos_validos_totais", "votos_totais_apurados", "votos_lula",
        "eleitores_aptos_bairro", "eleitores_superior_completo",
        "eleitores_superior_incompleto", "eleitores_ensino_superior_total"
    ]
    for c in int_cols:
        df[c] = df[c].astype(int)

    # Salvar nos caminhos especificados com UTF-8-SIG (compatível com Excel e scripts)
    os.makedirs(os.path.dirname(output_processed_csv), exist_ok=True)
    df.to_csv(output_processed_csv, index=False, encoding="utf-8-sig")
    print(f"[+] Arquivo salvo com sucesso em: {output_processed_csv}")

    df.to_csv(output_root_csv, index=False, encoding="utf-8-sig")
    print(f"[+] Arquivo salvo com sucesso em: {output_root_csv}")

    # Estatísticas e correlações
    corr_sup_comp = df["pct_votos_validos_flavio"].corr(df["pct_superior_completo"])
    corr_sup_tot = df["pct_votos_validos_flavio"].corr(df["pct_ensino_superior_total"])

    print("\n" + "="*80)
    print(f"RESUMO EXECUTIVO - SALVADOR (151 BAIRROS)")
    print("="*80)
    print(f"Total de Votos em Flávio Bolsonaro: {df['votos_flavio_bolsonaro'].sum():,}".replace(",", "."))
    print(f"Total de Votos Válidos:            {df['votos_validos_totais'].sum():,}".replace(",", "."))
    print(f"Média % Flávio (Válidos):          {df['pct_votos_validos_flavio'].mean():.2f}%")
    print(f"Média % Ensino Superior Completo:  {df['pct_superior_completo'].mean():.2f}%")
    print(f"Média % Superior Total:            {df['pct_ensino_superior_total'].mean():.2f}%")
    print(f"Correlação de Pearson (% Flávio x % Superior Completo): {corr_sup_comp:.4f}")
    print(f"Correlação de Pearson (% Flávio x % Superior Total):    {corr_sup_tot:.4f}")
    print("="*80)

    print("\n--- TOP 10 BAIRROS COM MAIOR % FLÁVIO BOLSONARO ---")
    top10 = df.head(10)[[
        "posicao_ranking", "bairro", "pct_votos_validos_flavio", "votos_flavio_bolsonaro",
        "pct_superior_completo", "pct_ensino_superior_total", "eleitores_aptos_bairro"
    ]]
    print(top10.to_string(index=False))

    print("\n--- TOP 10 BAIRROS COM MENOR % FLÁVIO BOLSONARO ---")
    bottom10 = df.tail(10)[[
        "posicao_ranking", "bairro", "pct_votos_validos_flavio", "votos_flavio_bolsonaro",
        "pct_superior_completo", "pct_ensino_superior_total", "eleitores_aptos_bairro"
    ]]
    print(bottom10.to_string(index=False))

    return df

if __name__ == "__main__":
    gerar_ranking_salvador()
