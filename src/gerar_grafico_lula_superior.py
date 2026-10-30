"""
Gera gráficos analíticos profissionais relacionando a votação de Luiz Inácio Lula da Silva (2026)
ao percentual de Ensino Superior nos 151 bairros de Salvador/BA (Ótica Invertida).

Gera:
1. PNG em alta resolução (300 DPI) com design executivo escuro (Dispersão + Linha de Regressão Invertida + Ranking Extremos).
2. Dashboard HTML interativo via Plotly (Hover interativo, Zoom, Tooltips completas).
"""

import os
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def gerar_graficos_lula(
    csv_path: str = "ranking_bairros_salvador_flavio_bolsonaro_ensino_superior.csv",
    png_output: str = "grafico_ranking_lula_ensino_superior_salvador.png",
    html_output: str = "grafico_bairros_salvador_lula.html"
):
    print(f"[*] Carregando dados de: {csv_path}...")
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # Estatísticas de regressão
    x = df["pct_superior_completo"]
    y = df["pct_votos_validos_lula"]
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    r2 = r_value ** 2

    print(f"[*] Correlação (Lula x Superior Completo): r = {r_value:.4f}, R² = {r2:.4f}, p = {p_value:.2e}")

    # =========================================================================
    # 1. GRÁFICO ESTÁTICO DE ALTA RESOLUÇÃO (MATPLOTLIB)
    # =========================================================================
    print("[*] Gerando visualização estática em alta resolução (PNG)...")
    
    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig = plt.figure(figsize=(18, 9), facecolor="#0f172a", dpi=300)
    
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 0.85], wspace=0.25)
    
    # ---------------------------------------------------------
    # PAINEL 1: DISPERSÃO E REGRESSÃO LINEAR INVERTIDA
    # ---------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor("#1e293b")
    ax1.grid(True, linestyle="--", alpha=0.2, color="#94a3b8")
    ax1.set_axisbelow(True)

    # Dispersão com gradiente temático avermelhado/coral (PT 13)
    scatter = ax1.scatter(
        df["pct_superior_completo"],
        df["pct_votos_validos_lula"],
        s=np.sqrt(df["eleitores_aptos_bairro"]) * 2.2,
        c=df["pct_votos_validos_lula"],
        cmap="magma",
        alpha=0.8,
        edgecolors="#f8fafc",
        linewidth=0.8,
        zorder=3
    )

    # Linha de regressão (declive negativo)
    x_vals = np.linspace(x.min(), x.max(), 100)
    y_vals = slope * x_vals + intercept
    ax1.plot(x_vals, y_vals, color="#ef4444", linestyle="-", linewidth=2.5, zorder=2, label=f"Tendência Linear (R² = {r2:.2f})")

    # Intervalo de confiança da regressão (95%)
    n = len(x)
    x_mean = np.mean(x)
    s_err = np.sqrt(np.sum((y - (slope * x + intercept))**2) / (n - 2))
    ci = 1.96 * s_err * np.sqrt(1/n + (x_vals - x_mean)**2 / np.sum((x - x_mean)**2))
    ax1.fill_between(x_vals, y_vals - ci, y_vals + ci, color="#ef4444", alpha=0.15, zorder=1)

    # Bairros em destaque para rotular
    destaques = [
        "ILHA DE MARÉ", "ILHA DOS FRADES", "CASSANGE", "BAIRRO DA PAZ", "BOM JUÁ",
        "PERO VAZ", "PERIPERI", "LIBERDADE", "CAJAZEIRAS", "BROTAS", "CABULA",
        "BARRA", "PITUBA", "GRAÇA", "PATAMARES", "ITAIGARA"
    ]

    for _, row in df.iterrows():
        b_nome = row["bairro"]
        if b_nome in destaques:
            bx = row["pct_superior_completo"]
            by = row["pct_votos_validos_lula"]
            
            dx, dy = 1.0, 0.4
            ha = "left"
            if b_nome in ["ILHA DE MARÉ", "ILHA DOS FRADES", "CASSANGE"]:
                dx, dy = 1.0, 0.5
            elif b_nome in ["ITAIGARA", "PATAMARES", "GRAÇA"]:
                dx, dy = -1.2, -0.6
                ha = "right"
            elif b_nome in ["PITUBA", "BARRA"]:
                dx, dy = 1.2, -0.5
                
            ax1.annotate(
                b_nome,
                xy=(bx, by),
                xytext=(bx + dx, by + dy),
                fontsize=8.5,
                fontweight='bold',
                color="#f1f5f9",
                ha=ha,
                va='center',
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#0f172a", edgecolor="#475569", alpha=0.85, linewidth=0.6),
                arrowprops=dict(arrowstyle="->", color="#94a3b8", lw=0.7, shrinkA=3, shrinkB=3)
            )

    # Box de estatísticas
    stats_text = (
        f"Correlação de Pearson (r): {r_value:.4f} (Inversa)\n"
        f"Coeficiente R²: {r2:.4f}\n"
        f"Significância (p): < 0.0001\n"
        f"Total de Bairros: {len(df)}\n"
        f"Votos Totais em Lula: {df['votos_lula'].sum():,}".replace(",", ".")
    )
    ax1.text(
        0.58, 0.95, stats_text,
        transform=ax1.transAxes,
        fontsize=9,
        color="#e2e8f0",
        va="top",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#090d16", edgecolor="#ef4444", alpha=0.9, linewidth=1.2)
    )

    ax1.set_title("Ótica Invertida: Votação de Lula vs. Ensino Superior\n(Salvador - Eleições 2026, 151 Bairros)", fontsize=13, fontweight="bold", color="#f8fafc", pad=14)
    ax1.set_xlabel("% Eleitores com Ensino Superior Completo", fontsize=11, color="#cbd5e1", labelpad=10)
    ax1.set_ylabel("% Votos Válidos em Lula (PT 13)", fontsize=11, color="#cbd5e1", labelpad=10)
    ax1.xaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))
    ax1.yaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))
    ax1.tick_params(colors="#94a3b8", labelsize=9.5)
    for spine in ax1.spines.values():
        spine.set_color("#334155")

    # ---------------------------------------------------------
    # PAINEL 2: RANKING COMPARATIVO LULA (TOP 10 & MENORES 10)
    # ---------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor("#1e293b")
    ax2.grid(True, linestyle="--", alpha=0.2, color="#94a3b8", axis="x")
    ax2.set_axisbelow(True)

    df_lula_sorted = df.sort_values("pct_votos_validos_lula", ascending=True).reset_index(drop=True)
    bot10_lula = df_lula_sorted.head(10).copy() # menores % lula (itaigara, patamares, etc.)
    top10_lula = df_lula_sorted.tail(10).copy() # maiores % lula (ilha de mare, cassange, etc.)
    ranking_lula = pd.concat([bot10_lula, top10_lula]).reset_index(drop=True)

    y_pos = np.arange(len(ranking_lula))
    bar_colors = ["#f59e0b" if i < 10 else "#dc2626" for i in range(len(ranking_lula))]

    bars = ax2.barh(y_pos, ranking_lula["pct_votos_validos_lula"], color=bar_colors, height=0.68, alpha=0.88, edgecolor="#0f172a", linewidth=0.5)

    for i, bar in enumerate(bars):
        pct_voto = ranking_lula.loc[i, "pct_votos_validos_lula"]
        pct_sup = ranking_lula.loc[i, "pct_superior_completo"]
        ax2.text(
            pct_voto + 0.6,
            bar.get_y() + bar.get_height() / 2,
            f"{pct_voto:.1f}%  [Sup: {pct_sup:.1f}%]",
            va="center",
            ha="left",
            fontsize=8,
            fontweight="bold",
            color="#f1f5f9"
        )

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(ranking_lula["bairro"], fontsize=8.5, color="#f1f5f9")
    ax2.set_xlim(0, 95)
    ax2.set_title("Ranking Extremos: Top 10 Lula (Vermelho) vs. Menores 10 (Laranja)\n[% Votos Lula e % Superior Completo]", fontsize=12, fontweight="bold", color="#f8fafc", pad=14)
    ax2.set_xlabel("% Votos Válidos", fontsize=11, color="#cbd5e1", labelpad=10)
    ax2.xaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))
    ax2.tick_params(colors="#94a3b8", labelsize=9.5)
    for spine in ax2.spines.values():
        spine.set_color("#334155")

    # Linha divisória entre menores10 e top10
    ax2.axhline(9.5, color="#64748b", linestyle=":", linewidth=1.5, alpha=0.7)

    # Rodapé institucional
    fig.text(0.5, 0.02, "Fonte dos Dados: TSE / Repositório Eleições 2026 | Processamento: DuckDB + Script Analítico | Salvador - BA", 
             ha="center", fontsize=9, color="#64748b")

    fig.subplots_adjust(left=0.06, right=0.96, top=0.92, bottom=0.08, wspace=0.25)
    fig.savefig(png_output, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"[+] Gráfico PNG Lula salvo com sucesso em: {png_output}")

    # =========================================================================
    # 2. DASHBOARD INTERATIVO (PLOTLY HTML) - LULA
    # =========================================================================
    print("[*] Gerando dashboard interativo HTML para Lula (Plotly)...")

    fig_plotly = make_subplots(
        rows=1, cols=2,
        column_widths=[0.6, 0.4],
        subplot_titles=(
            "Dispersão Interativa: Votação Lula vs. % Superior (151 Bairros)",
            "Top 20 Bairros: Maior % Lula (PT)"
        ),
        horizontal_spacing=0.08
    )

    hover_scatter = (
        "<b>%{customdata[0]}</b><br>" +
        "------------------------------------<br>" +
        "• Lula: <b>%{y:.2f}%</b> (%{customdata[1]:,} votos)<br>" +
        "• Flávio Bolsonaro: <b>%{customdata[2]:.2f}%</b> (%{customdata[3]:,} votos)<br>" +
        "• Superior Completo: <b>%{x:.2f}%</b> (%{customdata[4]:,} eleitores)<br>" +
        "• Superior Total: <b>%{customdata[5]:.2f}%</b><br>" +
        "• Eleitores Aptos: %{customdata[6]:,}<br>" +
        "• Seções Eleitorais: %{customdata[7]}<extra></extra>"
    )

    customdata_scatter = df[[
        "bairro", "votos_lula", "pct_votos_validos_flavio",
        "votos_flavio_bolsonaro", "eleitores_superior_completo",
        "pct_ensino_superior_total", "eleitores_aptos_bairro", "qtd_secoes_eleitorais"
    ]].values

    fig_plotly.add_trace(
        go.Scatter(
            x=df["pct_superior_completo"],
            y=df["pct_votos_validos_lula"],
            mode="markers",
            marker=dict(
                size=np.sqrt(df["eleitores_aptos_bairro"]) * 0.16 + 5,
                color=df["pct_votos_validos_lula"],
                colorscale="Reds",
                showscale=True,
                colorbar=dict(title="% Votos Lula", x=0.55, len=0.8),
                line=dict(color="#ffffff", width=1),
                opacity=0.85
            ),
            text=df["bairro"],
            customdata=customdata_scatter,
            hovertemplate=hover_scatter,
            name="Bairros de Salvador"
        ),
        row=1, col=1
    )

    # Linha de tendência decrescente
    fig_plotly.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines",
            line=dict(color="#ef4444", width=3, dash="dash"),
            name=f"Tendência Linear (r={r_value:.2f}, R²={r2:.2f})"
        ),
        row=1, col=1
    )

    # 2. Barra Horizontal Top 20 Lula
    top20_lula = df.sort_values("pct_votos_validos_lula", ascending=True).tail(20)
    hover_bar = (
        "<b>%{y}</b><br>" +
        "• % Votos Lula: <b>%{x:.2f}%</b><br>" +
        "• Votos Lula: %{customdata[0]:,}<br>" +
        "• % Superior Completo: %{customdata[1]:.2f}%<extra></extra>"
    )
    customdata_bar = top20_lula[["votos_lula", "pct_superior_completo"]].values

    fig_plotly.add_trace(
        go.Bar(
            x=top20_lula["pct_votos_validos_lula"],
            y=top20_lula["bairro"],
            orientation="h",
            marker=dict(
                color=top20_lula["pct_votos_validos_lula"],
                colorscale="Reds",
                line=dict(color="#0f172a", width=1)
            ),
            customdata=customdata_bar,
            hovertemplate=hover_bar,
            name="Top 20 Lula"
        ),
        row=1, col=2
    )

    fig_plotly.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0b1120",
        plot_bgcolor="#111827",
        title=dict(
            text="<b>Análise Eleitoral Salvador 2026: Votação Lula vs. Ensino Superior (Ótica Invertida)</b><br><span style='font-size:12px; color:#94a3b8;'>Correlação linear inversa r = -0,8001 | Cruzamento de 151 bairros via dados de seções eleitorais do TSE</span>",
            x=0.03, y=0.96,
            font=dict(size=18, color="#f8fafc")
        ),
        font=dict(family="sans-serif", color="#e2e8f0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=60, r=40, t=100, b=50),
        height=700
    )

    fig_plotly.update_xaxes(title_text="% Eleitores com Ensino Superior Completo", row=1, col=1, ticksuffix="%")
    fig_plotly.update_yaxes(title_text="% Votos Válidos em Lula", row=1, col=1, ticksuffix="%")
    fig_plotly.update_xaxes(title_text="% Votos Válidos", row=1, col=2, ticksuffix="%")

    fig_plotly.write_html(html_output, include_plotlyjs="cdn")
    print(f"[+] Dashboard HTML Lula salvo com sucesso em: {html_output}")

if __name__ == "__main__":
    gerar_graficos_lula()
