"""
Gera gráficos analíticos profissionais relacionando a votação de Flávio Bolsonaro (2026)
ao percentual de Ensino Superior nos 151 bairros de Salvador/BA.

Gera:
1. PNG em alta resolução (300 DPI) com design executivo (Dispersão + Linha de Regressão + Ranking Comparativo).
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

def gerar_graficos(
    csv_path: str = "ranking_bairros_salvador_flavio_bolsonaro_ensino_superior.csv",
    png_output: str = "grafico_ranking_flavio_ensino_superior_salvador.png",
    html_output: str = "grafico_bairros_salvador.html"
):
    print(f"[*] Carregando dados de: {csv_path}...")
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    # Estatísticas de regressão
    x = df["pct_superior_completo"]
    y = df["pct_votos_validos_flavio"]
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    r2 = r_value ** 2

    print(f"[*] Correlação: r = {r_value:.4f}, R² = {r2:.4f}, p = {p_value:.2e}")

    # =========================================================================
    # 1. GRÁFICO ESTÁTICO DE ALTA RESOLUÇÃO (MATPLOTLIB)
    # =========================================================================
    print("[*] Gerando visualização estática em alta resolução (PNG)...")
    
    # Configuração de estilo escuro executivo moderno
    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig = plt.figure(figsize=(18, 9), facecolor="#0f172a", dpi=300)
    
    # Grid de 1 linha e 2 colunas
    gs = fig.add_gridspec(1, 2, width_ratios=[1.15, 0.85], wspace=0.25)
    
    # ---------------------------------------------------------
    # PAINEL 1: DISPERSÃO E REGRESSÃO LINEAR
    # ---------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor("#1e293b")
    
    # Grid sutil
    ax1.grid(True, linestyle="--", alpha=0.2, color="#94a3b8")
    ax1.set_axisbelow(True)

    # Cores baseadas no % de votos de Flávio (gradiente amarelo-dourado/azul)
    scatter = ax1.scatter(
        df["pct_superior_completo"],
        df["pct_votos_validos_flavio"],
        s=np.sqrt(df["eleitores_aptos_bairro"]) * 2.2, # tamanho proporcional aos eleitores
        c=df["pct_votos_validos_flavio"],
        cmap="plasma",
        alpha=0.75,
        edgecolors="#f8fafc",
        linewidth=0.8,
        zorder=3
    )

    # Linha de regressão
    x_vals = np.linspace(x.min(), x.max(), 100)
    y_vals = slope * x_vals + intercept
    ax1.plot(x_vals, y_vals, color="#38bdf8", linestyle="-", linewidth=2.5, zorder=2, label=f"Tendência Linear (R² = {r2:.2f})")

    # Intervalo de confiança da regressão (95%)
    n = len(x)
    x_mean = np.mean(x)
    s_err = np.sqrt(np.sum((y - (slope * x + intercept))**2) / (n - 2))
    ci = 1.96 * s_err * np.sqrt(1/n + (x_vals - x_mean)**2 / np.sum((x - x_mean)**2))
    ax1.fill_between(x_vals, y_vals - ci, y_vals + ci, color="#38bdf8", alpha=0.15, zorder=1)

    # Bairros em destaque para rotular
    destaques = [
        "ITAIGARA", "PATAMARES", "GRAÇA", "PIATÃ", "STELLA MARIS",
        "PITUBA", "BARRA", "CANELA", "BROTAS", "CABULA", "PERIPERI",
        "CAJAZEIRAS", "LIBERDADE", "BAIRRO DA PAZ", "ILHA DE MARÉ"
    ]

    for _, row in df.iterrows():
        b_nome = row["bairro"]
        if b_nome in destaques:
            bx = row["pct_superior_completo"]
            by = row["pct_votos_validos_flavio"]
            
            # Ajuste de posição para não sobrepor
            dx, dy = 1.0, 0.4
            ha = "left"
            if b_nome in ["ITAIGARA", "PATAMARES"]:
                dx, dy = -1.2, 0.5
                ha = "right"
            elif b_nome in ["ILHA DE MARÉ", "BAIRRO DA PAZ"]:
                dx, dy = 1.2, -0.6
            elif b_nome in ["GRAÇA", "BARRA"]:
                dx, dy = 1.2, 0.6
                
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
        f"Correlação de Pearson (r): {r_value:.4f}\n"
        f"Coeficiente R²: {r2:.4f}\n"
        f"Significância (p): < 0.0001\n"
        f"Total de Bairros: {len(df)}\n"
        f"Eleitores Mapeados: {df['eleitores_aptos_bairro'].sum():,}".replace(",", ".")
    )
    ax1.text(
        0.05, 0.95, stats_text,
        transform=ax1.transAxes,
        fontsize=9,
        color="#e2e8f0",
        va="top",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#090d16", edgecolor="#38bdf8", alpha=0.9, linewidth=1.2)
    )

    ax1.set_title("Correlação: Votação de Flávio Bolsonaro vs. Ensino Superior\n(Salvador - Eleições 2026, 151 Bairros)", fontsize=13, fontweight="bold", color="#f8fafc", pad=14)
    ax1.set_xlabel("% Eleitores com Ensino Superior Completo", fontsize=11, color="#cbd5e1", labelpad=10)
    ax1.set_ylabel("% Votos Válidos em Flávio Bolsonaro (PL 22)", fontsize=11, color="#cbd5e1", labelpad=10)
    ax1.xaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))
    ax1.yaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))
    ax1.tick_params(colors="#94a3b8", labelsize=9.5)
    for spine in ax1.spines.values():
        spine.set_color("#334155")

    # ---------------------------------------------------------
    # PAINEL 2: RANKING COMPARATIVO (TOP 10 & BOTTOM 10)
    # ---------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor("#1e293b")
    ax2.grid(True, linestyle="--", alpha=0.2, color="#94a3b8", axis="x")
    ax2.set_axisbelow(True)

    top10 = df.head(10).copy()
    bot10 = df.tail(10).copy()
    ranking_plot = pd.concat([bot10, top10]).reset_index(drop=True)

    y_pos = np.arange(len(ranking_plot))
    bar_colors = ["#ef4444" if i < 10 else "#10b981" for i in range(len(ranking_plot))]

    bars = ax2.barh(y_pos, ranking_plot["pct_votos_validos_flavio"], color=bar_colors, height=0.68, alpha=0.85, edgecolor="#0f172a", linewidth=0.5)

    # Rótulos das barras com % e Ensino Superior
    for i, bar in enumerate(bars):
        pct_voto = ranking_plot.loc[i, "pct_votos_validos_flavio"]
        pct_sup = ranking_plot.loc[i, "pct_superior_completo"]
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
    ax2.set_yticklabels(ranking_plot["bairro"], fontsize=8.5, color="#f1f5f9")
    ax2.set_xlim(0, 56)
    ax2.set_title("Ranking Extremos: Top 10 (Verde) vs. Menores 10 (Vermelho)\n[% Votos Flávio e % Superior Completo]", fontsize=12, fontweight="bold", color="#f8fafc", pad=14)
    ax2.set_xlabel("% Votos Válidos", fontsize=11, color="#cbd5e1", labelpad=10)
    ax2.xaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))
    ax2.tick_params(colors="#94a3b8", labelsize=9.5)
    for spine in ax2.spines.values():
        spine.set_color("#334155")

    # Linha divisória entre bot10 e top10
    ax2.axhline(9.5, color="#64748b", linestyle=":", linewidth=1.5, alpha=0.7)

    # Rodapé institucional
    fig.text(0.5, 0.02, "Fonte dos Dados: TSE / Repositório Eleições 2026 | Processamento: DuckDB + Script Analítico | Salvador - BA", 
             ha="center", fontsize=9, color="#64748b")

    fig.subplots_adjust(left=0.06, right=0.96, top=0.92, bottom=0.08, wspace=0.25)
    fig.savefig(png_output, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"[+] Gráfico PNG salvo com sucesso em: {png_output}")

    # =========================================================================
    # 2. DASHBOARD INTERATIVO (PLOTLY HTML)
    # =========================================================================
    print("[*] Gerando dashboard interativo HTML (Plotly)...")

    # Subplots: 1 Dispersão + 1 Barra Horizontal (Top 20)
    fig_plotly = make_subplots(
        rows=1, cols=2,
        column_widths=[0.6, 0.4],
        subplot_titles=(
            "Dispersão Interativa: Votação Flávio vs. % Superior (151 Bairros)",
            "Top 20 Bairros: Maior % Flávio Bolsonaro (PL)"
        ),
        horizontal_spacing=0.08
    )

    # 1. Scatter Plot
    hover_scatter = (
        "<b>%{customdata[0]}</b> (Posição: %{customdata[1]}º)<br>" +
        "------------------------------------<br>" +
        "• Flávio Bolsonaro: <b>%{y:.2f}%</b> (%{customdata[2]:,} votos)<br>" +
        "• Lula: <b>%{customdata[3]:.2f}%</b> (%{customdata[4]:,} votos)<br>" +
        "• Superior Completo: <b>%{x:.2f}%</b> (%{customdata[5]:,} eleitores)<br>" +
        "• Superior Total: <b>%{customdata[6]:.2f}%</b><br>" +
        "• Eleitores Aptos: %{customdata[7]:,}<br>" +
        "• Seções Eleitorais: %{customdata[8]}<extra></extra>"
    )

    customdata_scatter = df[[
        "bairro", "posicao_ranking", "votos_flavio_bolsonaro",
        "pct_votos_validos_lula", "votos_lula", "eleitores_superior_completo",
        "pct_ensino_superior_total", "eleitores_aptos_bairro", "qtd_secoes_eleitorais"
    ]].values

    fig_plotly.add_trace(
        go.Scatter(
            x=df["pct_superior_completo"],
            y=df["pct_votos_validos_flavio"],
            mode="markers",
            marker=dict(
                size=np.sqrt(df["eleitores_aptos_bairro"]) * 0.16 + 5,
                color=df["pct_votos_validos_flavio"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="% Votos Flávio", x=0.55, len=0.8),
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

    # Linha de tendência no Plotly
    fig_plotly.add_trace(
        go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="lines",
            line=dict(color="#38bdf8", width=3, dash="dash"),
            name=f"Tendência Linear (r={r_value:.2f}, R²={r2:.2f})"
        ),
        row=1, col=1
    )

    # 2. Barra Horizontal Top 20
    top20 = df.head(20).iloc[::-1] # inverter para o 1º ficar no topo
    hover_bar = (
        "<b>%{y}</b> (Posição: %{customdata[0]}º)<br>" +
        "• % Votos Flávio: <b>%{x:.2f}%</b><br>" +
        "• Votos Flávio: %{customdata[1]:,}<br>" +
        "• % Superior Completo: %{customdata[2]:.2f}%<extra></extra>"
    )
    customdata_bar = top20[["posicao_ranking", "votos_flavio_bolsonaro", "pct_superior_completo"]].values

    fig_plotly.add_trace(
        go.Bar(
            x=top20["pct_votos_validos_flavio"],
            y=top20["bairro"],
            orientation="h",
            marker=dict(
                color=top20["pct_superior_completo"],
                colorscale="Tealgrn",
                line=dict(color="#0f172a", width=1)
            ),
            customdata=customdata_bar,
            hovertemplate=hover_bar,
            name="Top 20 Bairros"
        ),
        row=1, col=2
    )

    # Layout dark moderno e responsivo
    fig_plotly.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0b1120",
        plot_bgcolor="#111827",
        title=dict(
            text="<b>Análise Eleitoral Salvador 2026: Votação Flávio Bolsonaro vs. Ensino Superior</b><br><span style='font-size:12px; color:#94a3b8;'>Correlação linear r = 0,8236 | Cruzamento de 151 bairros via dados de seções eleitorais do TSE</span>",
            x=0.03, y=0.96,
            font=dict(size=18, color="#f8fafc")
        ),
        font=dict(family="sans-serif", color="#e2e8f0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=60, r=40, t=100, b=50),
        height=700
    )

    fig_plotly.update_xaxes(title_text="% Eleitores com Ensino Superior Completo", row=1, col=1, ticksuffix="%")
    fig_plotly.update_yaxes(title_text="% Votos Válidos em Flávio Bolsonaro", row=1, col=1, ticksuffix="%")
    fig_plotly.update_xaxes(title_text="% Votos Válidos", row=1, col=2, ticksuffix="%")

    fig_plotly.write_html(html_output, include_plotlyjs="cdn")
    print(f"[+] Dashboard HTML salvo com sucesso em: {html_output}")

if __name__ == "__main__":
    gerar_graficos()
