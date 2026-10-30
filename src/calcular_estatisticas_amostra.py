"""
Gera métricas estatísticas avançadas 100% OFICIAIS do TSE para a amostra de 20 urnas:
1. Biometria vs Liberação Manual (Mesário) 1º vs 2º Turno (Testes Pareados).
2. Diminuição da Abstenção vs Evolução de Votos nos Candidatos (Lula 13 vs Bolsonaro 22).
DADOS 100% OFICIAIS EXTRAÍDOS DOS BOLETINS DE URNA (.bu.dat) E LOGS (.logjez) DO TSE.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import scipy.stats as stats

def calcular_estatisticas_avancadas():
    json_path = Path("data/processed/amostra_20_urnas_auditoria_oficial.json")
    if not json_path.exists():
        raise FileNotFoundError(f"Arquivo oficial não encontrado: {json_path}")
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Carrega também os locais de votação da amostra original de 20 urnas
    locais_map = {}
    orig_path = Path("data/processed/amostra_20_urnas_auditoria.json")
    if orig_path.exists():
        with open(orig_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                key = (item["ZONA"], item["SECAO"])
                locais_map[key] = item.get("LOCAL_VOTACAO", "ESCOLA MUNICIPAL")

    df = pd.DataFrame(data)
    n = len(df)
    
    # Padroniza nomes de colunas esperadas pelo dashboard
    df["LOCAL_VOTACAO"] = [locais_map.get((row["ZONA"], row["SECAO"]), "LOCAL ELEITORAL") for _, row in df.iterrows()]
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
    
    # Shapiro-Wilk
    sw_stat_man, sw_pval_man = stats.shapiro(dif_pct_man)
    
    # Teste t pareado
    ttest_res_man = stats.ttest_rel(pct_man_t2, pct_man_t1)
    t_stat_man = float(ttest_res_man.statistic)
    t_pval_man = float(ttest_res_man.pvalue)
    
    # Wilcoxon
    wilc_res_man = stats.wilcoxon(pct_man_t2, pct_man_t1)
    w_stat_man = float(wilc_res_man.statistic)
    w_pval_man = float(wilc_res_man.pvalue)
    
    # Cohen's d
    cohen_d_man = float(mean_dif_man / std_dif_man) if std_dif_man > 0 else 0.0
    
    # Bootstrap CI 95%
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
    slope_13, intercept_13, r_val_13, p_val_ols_13, std_err_13 = stats.linregress(dif_comp, dif_votos_13)
    r2_13 = float(r_val_13**2)
    
    # Bolsonaro (22)
    r_22, p_r_22 = stats.pearsonr(dif_comp, dif_votos_22)
    slope_22, intercept_22, r_val_22, p_val_ols_22, std_err_22 = stats.linregress(dif_comp, dif_votos_22)
    r2_22 = float(r_val_22**2)
    
    # Médias de abstenção
    mean_abst_t1 = float(np.mean(df["PCT_ABST_T1"]))
    mean_abst_t2 = float(np.mean(df["PCT_ABST_T2"]))
    mean_queda_abst = float(np.mean(df["QUEDA_ABST_PCT"]))
    mean_dif_comp = float(np.mean(df["DIF_COMP"]))
    mean_comp_t1 = float(np.mean(df["COMP_T1"]))
    mean_comp_t2 = float(np.mean(df["COMP_T2"]))
    
    # Estrutura completa de estatísticas esperada pelo dashboard
    stats_formatted = {
        "n": n,
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
            "sem": round(sem_dif_man, 2),
            "ci_95": [round(ci_boot_lower, 2), round(ci_boot_upper, 2)]
        },
        "tests": {
            "paired_t": round(t_stat_man, 3),
            "paired_t_p": round(t_pval_man, 4),
            "wilcoxon_w": round(w_stat_man, 1),
            "wilcoxon_p": round(w_pval_man, 4),
            "cohens_d": round(cohen_d_man, 3),
            "cohen_label": "Desprezível" if abs(cohen_d_man) < 0.2 else "Pequeno",
            "shapiro_w": round(float(sw_stat_man), 4),
            "shapiro_p": round(float(sw_pval_man), 4),
            "normal": bool(sw_pval_man > 0.05)
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
            "r_comp_22": round(float(r_22), 3),
            "p_comp_22": f"{float(p_r_22):.2e}" if p_r_22 < 0.001 else f"{float(p_r_22):.4f}",
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
    
    return df, stats_formatted

if __name__ == "__main__":
    df, stats = calcular_estatisticas_avancadas()
    print("Sucesso! DF shape:", df.shape)
    print("Stats T1 Mesário:", stats["t1"])
    print("Stats T2 Mesário:", stats["t2"])
    print("Regressão OLS Lula:", stats["abstencao"]["slope_13"], "R²:", stats["abstencao"]["r2_13"])
    print("Regressão OLS Bolsonaro:", stats["abstencao"]["slope_22"], "R²:", stats["abstencao"]["r2_22"])
