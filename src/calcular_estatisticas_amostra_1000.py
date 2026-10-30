"""
Gera métricas estatísticas avançadas 100% OFICIAIS do TSE para a amostra de 1.000 URNAS (Bahia 2026):
1. Biometria vs Liberação Manual (Mesário) 1º vs 2º Turno (Testes Pareados com N = 1.000).
2. Diminuição da Abstenção vs Evolução de Votos nos Candidatos (Lula 13 vs Bolsonaro 22).
DADOS 100% OFICIAIS EXTRAÍDOS DOS BOLETINS DE URNA (.bu.dat) DO TSE.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.stats as stats

import sys
sys.stdout.reconfigure(encoding="utf-8")

def calcular_estatisticas_1000():
    json_path = Path("data/processed/amostra_1000_urnas_auditoria_oficial.json")
    if not json_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {json_path}")
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    df = pd.DataFrame(data)
    n = len(df)
    print(f"Carregadas {n} urnas oficiais para processamento estatístico.")
    
    # Padronização de colunas
    df["COMP_T1"] = df["1T_COMPARECIMENTO"]
    df["COMP_T2"] = df["2T_COMPARECIMENTO"]
    df["DIF_COMP"] = df["DELTA_COMPARECIMENTO"]
    
    df["ABST_T1"] = df["1T_ABSTENCAO"]
    df["ABST_T2"] = df["2T_ABSTENCAO"]
    df["PCT_ABST_T1"] = df["1T_PCT_ABSTENCAO"]
    df["PCT_ABST_T2"] = df["2T_PCT_ABSTENCAO"]
    df["DIF_PCT_ABST"] = (df["PCT_ABST_T2"] - df["PCT_ABST_T1"]).round(2)
    df["QUEDA_ABST_PCT"] = (-df["DIF_PCT_ABST"]).round(2)
    
    df["MAN_T1"] = df["1T_QTD_MANUAL"]
    df["MAN_T2"] = df["2T_QTD_MANUAL"]
    df["PCT_MAN_T1"] = df["1T_PCT_MANUAL"]
    df["PCT_MAN_T2"] = df["2T_PCT_MANUAL"]
    df["DIF_PCT_MANUAL"] = df["DELTA_PCT_MANUAL"]
    df["DIF_ABS_MANUAL"] = df["DELTA_MANUAL"]
    
    df["BIO_T1"] = df["1T_QTD_BIOMETRIA"]
    df["BIO_T2"] = df["2T_QTD_BIOMETRIA"]
    
    df["VOTOS_13_T1"] = df["1T_VOTOS_13"]
    df["VOTOS_13_T2"] = df["2T_VOTOS_13"]
    df["DIF_VOTOS_13"] = df["DELTA_VOTOS_13"]
    
    df["VOTOS_22_T1"] = df["1T_VOTOS_22"]
    df["VOTOS_22_T2"] = df["2T_VOTOS_22"]
    df["DIF_VOTOS_22"] = df["DELTA_VOTOS_22"]
    
    df["PCT_13_T1"] = df["1T_PCT_13"]
    df["PCT_13_T2"] = df["2T_PCT_13"]
    df["PCT_22_T1"] = df["1T_PCT_22"]
    df["PCT_22_T2"] = df["2T_PCT_22"]

    # =========================================================================
    # 1. TESTES ESTATÍSTICOS PAREADOS: HABILITAÇÃO MANUAL (MESÁRIO)
    # =========================================================================
    pct_man_t1 = df["PCT_MAN_T1"].values
    pct_man_t2 = df["PCT_MAN_T2"].values
    dif_pct_man = df["DIF_PCT_MANUAL"].values
    
    mean_man_t1 = float(np.mean(pct_man_t1))
    std_man_t1 = float(np.std(pct_man_t1, ddof=1))
    median_man_t1 = float(np.median(pct_man_t1))
    iqr_man_t1 = float(stats.iqr(pct_man_t1))
    
    mean_man_t2 = float(np.mean(pct_man_t2))
    std_man_t2 = float(np.std(pct_man_t2, ddof=1))
    median_man_t2 = float(np.median(pct_man_t2))
    iqr_man_t2 = float(stats.iqr(pct_man_t2))
    
    mean_dif_man = float(np.mean(dif_pct_man))
    std_dif_man = float(np.std(dif_pct_man, ddof=1))
    sem_dif_man = std_dif_man / np.sqrt(n)
    
    # Teste de Normalidade de D'Agostino-Pearson (ideal para N grande como 1.000)
    dag_stat, dag_pval = stats.normaltest(dif_pct_man)
    
    # Teste de Shapiro-Wilk
    sw_stat_man, sw_pval_man = stats.shapiro(dif_pct_man)
    
    # Teste t de Student pareado
    ttest_res_man = stats.ttest_rel(pct_man_t2, pct_man_t1)
    t_stat_man = float(ttest_res_man.statistic)
    t_pval_man = float(ttest_res_man.pvalue)
    
    # Teste não-paramétrico de Wilcoxon (Signed-Rank)
    wilc_res_man = stats.wilcoxon(pct_man_t2, pct_man_t1)
    w_stat_man = float(wilc_res_man.statistic)
    w_pval_man = float(wilc_res_man.pvalue)
    
    # Cohen's d pareado
    cohen_d_man = float(mean_dif_man / std_dif_man) if std_dif_man > 0 else 0.0
    
    # Bootstrap CI 95% (10.000 iterações)
    np.random.seed(42)
    boot_means = [np.mean(np.random.choice(dif_pct_man, size=n, replace=True)) for _ in range(10000)]
    ci_boot_lower = float(np.percentile(boot_means, 2.5))
    ci_boot_upper = float(np.percentile(boot_means, 97.5))

    # =========================================================================
    # 2. ANÁLISE DE CORRELAÇÃO E REGRESSÃO: COMPARECIMENTO vs VOTOS
    # =========================================================================
    dif_comp = df["DIF_COMP"].values
    dif_votos_13 = df["DIF_VOTOS_13"].values
    dif_votos_22 = df["DIF_VOTOS_22"].values
    
    # Lula (13)
    r_13, p_r_13 = stats.pearsonr(dif_comp, dif_votos_13)
    rho_13, p_rho_13 = stats.spearmanr(dif_comp, dif_votos_13)
    slope_13, intercept_13, r_val_13, p_val_ols_13, std_err_13 = stats.linregress(dif_comp, dif_votos_13)
    r2_13 = float(r_val_13**2)
    
    # Bolsonaro (22)
    r_22, p_r_22 = stats.pearsonr(dif_comp, dif_votos_22)
    rho_22, p_rho_22 = stats.spearmanr(dif_comp, dif_votos_22)
    slope_22, intercept_22, r_val_22, p_val_ols_22, std_err_22 = stats.linregress(dif_comp, dif_votos_22)
    r2_22 = float(r_val_22**2)
    
    # Totais consolidados
    tot_aptos = int(np.sum(df["1T_APTOS"]))
    tot_comp_t1 = int(np.sum(df["COMP_T1"]))
    tot_comp_t2 = int(np.sum(df["COMP_T2"]))
    tot_dif_comp = tot_comp_t2 - tot_comp_t1
    tot_abst_t1 = int(np.sum(df["ABST_T1"]))
    tot_abst_t2 = int(np.sum(df["ABST_T2"]))
    tot_queda_abst = tot_abst_t1 - tot_abst_t2
    
    tot_man_t1 = int(np.sum(df["MAN_T1"]))
    tot_man_t2 = int(np.sum(df["MAN_T2"]))
    tot_bio_t1 = int(np.sum(df["BIO_T1"]))
    tot_bio_t2 = int(np.sum(df["BIO_T2"]))
    
    tot_votos_13_t1 = int(np.sum(df["VOTOS_13_T1"]))
    tot_votos_13_t2 = int(np.sum(df["VOTOS_13_T2"]))
    tot_delta_13 = tot_votos_13_t2 - tot_votos_13_t1
    
    tot_votos_22_t1 = int(np.sum(df["VOTOS_22_T1"]))
    tot_votos_22_t2 = int(np.sum(df["VOTOS_22_T2"]))
    tot_delta_22 = tot_votos_22_t2 - tot_votos_22_t1
    
    mean_abst_t1 = float(np.mean(df["PCT_ABST_T1"]))
    mean_abst_t2 = float(np.mean(df["PCT_ABST_T2"]))
    mean_queda_abst = float(np.mean(df["QUEDA_ABST_PCT"]))
    mean_dif_comp = float(np.mean(df["DIF_COMP"]))
    mean_comp_t1 = float(np.mean(df["COMP_T1"]))
    mean_comp_t2 = float(np.mean(df["COMP_T2"]))

    stats_report = {
        "status": "DADOS_100%_OFICIAIS_TSE",
        "amostra_tamanho": n,
        "totais": {
            "aptos": tot_aptos,
            "comp_t1": tot_comp_t1,
            "comp_t2": tot_comp_t2,
            "delta_comp": tot_dif_comp,
            "abst_t1": tot_abst_t1,
            "abst_t2": tot_abst_t2,
            "queda_abst": tot_queda_abst,
            "man_t1": tot_man_t1,
            "man_t2": tot_man_t2,
            "delta_man": tot_man_t2 - tot_man_t1,
            "bio_t1": tot_bio_t1,
            "bio_t2": tot_bio_t2,
            "votos_13_t1": tot_votos_13_t1,
            "votos_13_t2": tot_votos_13_t2,
            "delta_13": tot_delta_13,
            "votos_22_t1": tot_votos_22_t1,
            "votos_22_t2": tot_votos_22_t2,
            "delta_22": tot_delta_22
        },
        "t1": {
            "mean": round(mean_man_t1, 2),
            "std": round(std_man_t1, 2),
            "median": round(median_man_t1, 2),
            "iqr": round(iqr_man_t1, 2)
        },
        "t2": {
            "mean": round(mean_man_t2, 2),
            "std": round(std_man_t2, 2),
            "median": round(median_man_t2, 2),
            "iqr": round(iqr_man_t2, 2)
        },
        "diff": {
            "mean": round(mean_dif_man, 2),
            "std": round(std_dif_man, 2),
            "sem": round(sem_dif_man, 3),
            "ci_95": [round(ci_boot_lower, 2), round(ci_boot_upper, 2)]
        },
        "tests": {
            "paired_t": round(t_stat_man, 3),
            "paired_t_p": round(t_pval_man, 4),
            "wilcoxon_w": round(w_stat_man, 1),
            "wilcoxon_p": round(w_pval_man, 4),
            "cohens_d": round(cohen_d_man, 3),
            "cohen_label": "Desprezível" if abs(cohen_d_man) < 0.2 else ("Pequeno" if abs(cohen_d_man) < 0.5 else "Médio"),
            "shapiro_w": round(float(sw_stat_man), 4),
            "shapiro_p": round(float(sw_pval_man), 4),
            "dagostino_stat": round(float(dag_stat), 2),
            "dagostino_p": round(float(dag_pval), 4)
        },
        "abstencao": {
            "mean_abst_t1": round(mean_abst_t1, 2),
            "mean_abst_t2": round(mean_abst_t2, 2),
            "mean_queda_abst": round(mean_queda_abst, 2),
            "mean_dif_comp": round(mean_dif_comp, 1),
            "mean_comp_t1": round(mean_comp_t1, 1),
            "mean_comp_t2": round(mean_comp_t2, 1),
            "r_comp_13": round(float(r_13), 3),
            "p_comp_13": f"{float(p_r_13):.2e}" if p_r_13 < 0.001 else f"{float(p_r_13):.4f}",
            "rho_comp_13": round(float(rho_13), 3),
            "r_comp_22": round(float(r_22), 3),
            "p_comp_22": f"{float(p_r_22):.2e}" if p_r_22 < 0.001 else f"{float(p_r_22):.4f}",
            "rho_comp_22": round(float(rho_22), 3),
            "slope_13": round(float(slope_13), 4),
            "int_13": round(float(intercept_13), 2),
            "r2_13": round(r2_13, 3),
            "se_13": round(float(std_err_13), 3),
            "p_ols_13": f"{float(p_val_ols_13):.2e}" if p_val_ols_13 < 0.001 else f"{float(p_val_ols_13):.4f}",
            "slope_22": round(float(slope_22), 4),
            "int_22": round(float(intercept_22), 2),
            "r2_22": round(r2_22, 3),
            "se_22": round(float(std_err_22), 3),
            "p_ols_22": f"{float(p_val_ols_22):.2e}" if p_val_ols_22 < 0.001 else f"{float(p_val_ols_22):.4f}",
            "share_marginal_13": round(float(slope_13) / (float(slope_13) + max(0.001, float(slope_22))) * 100, 1),
            "share_marginal_22": round(float(slope_22) / (float(slope_13) + max(0.001, float(slope_22))) * 100, 1)
        }
    }
    
    out_file = Path("data/processed/estatisticas_amostra_1000_urnas.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(stats_report, f, indent=2, ensure_ascii=False)
        
    print("\n" + "="*70)
    print("RELATÓRIO ESTATÍSTICO COMPLETO COM N = 1.000 URNAS OFICIAIS:")
    print("="*70)
    print(f"Total Eleitores Aptos na Amostra: {tot_aptos:,}")
    print(f"Comparecimento 1T -> 2T: {tot_comp_t1:,} -> {tot_comp_t2:,} (+{tot_dif_comp:,} eleitores / queda de abstenção)")
    print(f"\n1. AUDITORIA BIOMETRIA / MESÁRIO:")
    print(f"   - Média 1ºT: {mean_man_t1:.2f}% (DP: {std_man_t1:.2f}%)")
    print(f"   - Média 2ºT: {mean_man_t2:.2f}% (DP: {std_man_t2:.2f}%)")
    print(f"   - Variação Média Pareada (Delta): {mean_dif_man:+.2f}% (IC 95%: [{ci_boot_lower:+.2f}%, {ci_boot_upper:+.2f}%])")
    print(f"   - Teste t pareado: t(999) = {t_stat_man:.3f}, p = {t_pval_man:.4f}")
    print(f"   - Teste Wilcoxon: W = {w_stat_man:.1f}, p = {w_pval_man:.4f}")
    print(f"   - Cohen's d: {cohen_d_man:.3f} ({stats_report['tests']['cohen_label']})")
    print(f"\n2. MOBILIZAÇÃO E EVOLUÇÃO DE VOTOS:")
    print(f"   - Total Votos Lula 13: {tot_votos_13_t1:,} -> {tot_votos_13_t2:,} (+{tot_delta_13:,} votos)")
    print(f"   - Total Votos Bolsonaro 22: {tot_votos_22_t1:,} -> {tot_votos_22_t2:,} (+{tot_delta_22:,} votos)")
    print(f"   - OLS Lula 13: slope = {slope_13:.4f}, R² = {r2_13:.4f}, r = {r_13:.4f} (p = {p_r_13:.2e})")
    print(f"   - OLS Bolsonaro 22: slope = {slope_22:.4f}, R² = {r2_22:.4f}, r = {r_22:.4f} (p = {p_r_22:.2e})")
    print("="*70)
    
    return df, stats_report

if __name__ == "__main__":
    calcular_estatisticas_1000()
