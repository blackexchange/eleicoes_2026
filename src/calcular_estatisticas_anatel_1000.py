import json
import pandas as pd
import numpy as np
import scipy.stats as stats
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")

def calcular_estatisticas_anatel():
    data_path = Path("data/processed/amostra_1000_urnas_anatel_enriquecida.json")
    with open(data_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    
    df = pd.DataFrame(records)
    
    # 1. Correlações
    r_comp, p_comp = stats.pearsonr(df['delta_pct_comp'], df['densidade_smp'])
    r_v13, p_v13 = stats.pearsonr(df['delta_votos_13'], df['densidade_smp'])
    r_v22, p_v22 = stats.pearsonr(df['delta_votos_22'], df['densidade_smp'])
    r_pct13, p_pct13 = stats.pearsonr(df['delta_pct_13_val'], df['densidade_smp'])
    r_pos13, p_pos13 = stats.pearsonr(df['delta_votos_13'], df['pct_pos_pago'])
    
    # 2. Quartis de Conectividade
    df['quartil_cod'] = pd.qcut(df['densidade_smp'], 4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
    
    quartis = []
    labels = {
        'Q1': 'Q1: Baixa Conectividade (<58 acessos/100 hab)',
        'Q2': 'Q2: Média-Baixa (58 a 74 acessos/100 hab)',
        'Q3': 'Q3: Média-Alta (74 a 106 acessos/100 hab)',
        'Q4': 'Q4: Alta Conectividade / Capital (>106 acessos/100 hab)'
    }
    
    for q_code in ['Q1', 'Q2', 'Q3', 'Q4']:
        sub = df[df['quartil_cod'] == q_code]
        delta_comp_sum = int(sub['delta_comp_abs'].sum())
        d13 = int(sub['delta_votos_13'].sum())
        d22 = int(sub['delta_votos_22'].sum())
        tot_delta_valid = d13 + d22
        taxa_captura_13 = round((d13 / tot_delta_valid * 100), 2) if tot_delta_valid > 0 else 0
        
        quartis.append({
            'codigo': q_code,
            'label': labels[q_code],
            'n_urnas': len(sub),
            'densidade_media': round(float(sub['densidade_smp'].mean()), 2),
            'pct_4g5g_media': round(float(sub['pct_4g_5g'].mean()), 2),
            'pct_pos_media': round(float(sub['pct_pos_pago'].mean()), 2),
            'renda_media': round(float(sub['RENDIMENTO_DOMICILIAR_RS'].mean()), 2),
            'comp_1t': round(float(sub['pct_comp_1t'].mean()), 2),
            'comp_2t': round(float(sub['pct_comp_2t'].mean()), 2),
            'delta_comp_pct': round(float(sub['delta_pct_comp'].mean()), 2),
            'delta_comp_abs': delta_comp_sum,
            'delta_v13': d13,
            'delta_v22': d22,
            'pct_lula_1t': round(float(sub['pct_13_1t_val'].mean()), 2),
            'pct_lula_2t': round(float(sub['pct_13_2t_val'].mean()), 2),
            'delta_pct_lula': round(float(sub['delta_pct_13_val'].mean()), 2),
            'taxa_captura_lula': taxa_captura_13
        })
        
    # 3. Capital vs Interior
    cap = df[df['NM_MUNICIPIO'] == 'SALVADOR']
    inte = df[df['NM_MUNICIPIO'] != 'SALVADOR']
    
    cap_stats = {
        'n_urnas': len(cap),
        'densidade_media': round(float(cap['densidade_smp'].mean()), 2),
        'pct_pos_media': round(float(cap['pct_pos_pago'].mean()), 2),
        'delta_comp_pct': round(float(cap['delta_pct_comp'].mean()), 2),
        'delta_comp_abs': int(cap['delta_comp_abs'].sum()),
        'delta_v13': int(cap['delta_votos_13'].sum()),
        'delta_v22': int(cap['delta_votos_22'].sum()),
        'delta_pct_lula': round(float(cap['delta_pct_13_val'].mean()), 2),
        'taxa_captura_lula': round((cap['delta_votos_13'].sum() / (cap['delta_votos_13'].sum() + cap['delta_votos_22'].sum()) * 100), 2)
    }
    
    inte_stats = {
        'n_urnas': len(inte),
        'densidade_media': round(float(inte['densidade_smp'].mean()), 2),
        'pct_pos_media': round(float(inte['pct_pos_pago'].mean()), 2),
        'delta_comp_pct': round(float(inte['delta_pct_comp'].mean()), 2),
        'delta_comp_abs': int(inte['delta_comp_abs'].sum()),
        'delta_v13': int(inte['delta_votos_13'].sum()),
        'delta_v22': int(inte['delta_votos_22'].sum()),
        'delta_pct_lula': round(float(inte['delta_pct_13_val'].mean()), 2),
        'taxa_captura_lula': round((inte['delta_votos_13'].sum() / (inte['delta_votos_13'].sum() + inte['delta_votos_22'].sum()) * 100), 2)
    }

    # 4. Regressão OLS Múltipla
    # y = Delta Votos Lula, X = [Delta Comp, Densidade SMP]
    sub = df[['delta_votos_13', 'delta_comp_abs', 'densidade_smp']].dropna()
    y = sub['delta_votos_13'].values
    X = np.column_stack([np.ones(len(sub)), sub['delta_comp_abs'].values, sub['densidade_smp'].values])
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    y_pred = X @ beta
    ss_tot = np.sum((y - np.mean(y))**2)
    ss_res = np.sum((y - y_pred)**2)
    r2_multi = 1 - ss_res / ss_tot
    sigma2 = ss_res / (len(y) - 3)
    cov = sigma2 * np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diagonal(cov))
    t_stats = beta / se
    p_vals = [float(2 * (1 - stats.t.cdf(np.abs(t), df=len(y)-3))) for t in t_stats]

    results = {
        'correlacoes': {
            'r_comp_dens': round(float(r_comp), 4),
            'p_comp_dens': float(p_comp),
            'r_v13_dens': round(float(r_v13), 4),
            'p_v13_dens': float(p_v13),
            'r_v22_dens': round(float(r_v22), 4),
            'p_v22_dens': float(p_v22),
            'r_pct13_dens': round(float(r_pct13), 4),
            'p_pct13_dens': float(p_pct13),
            'r_pos13': round(float(r_pos13), 4),
            'p_pos13': float(p_pos13)
        },
        'quartis': quartis,
        'capital_vs_interior': {
            'capital': cap_stats,
            'interior': inte_stats
        },
        'ols_multiplo': {
            'r2': round(float(r2_multi), 4),
            'intercept': round(float(beta[0]), 4),
            'slope_comp': round(float(beta[1]), 4),
            'se_comp': round(float(se[1]), 4),
            't_comp': round(float(t_stats[1]), 2),
            'p_comp': float(p_vals[1]),
            'slope_dens': round(float(beta[2]), 4),
            'se_dens': round(float(se[2]), 4),
            't_dens': round(float(t_stats[2]), 2),
            'p_dens': float(p_vals[2])
        }
    }
    
    with open("data/processed/estatisticas_anatel_1000_urnas.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    return results

if __name__ == "__main__":
    res = calcular_estatisticas_anatel()
    print("Sucesso! Estatisticas salvas.")
