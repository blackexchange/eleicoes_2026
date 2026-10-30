"""
Gera o gráfico comparativo direto ('Efeito Tesoura') entre a votação de Flávio Bolsonaro (PL)
e Luiz Inácio Lula da Silva (PT) em função do nível de Ensino Superior nos 151 bairros de Salvador.
"""

import os
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import plotly.graph_objects as go

def gerar_grafico_comparativo(
    csv_path: str = "ranking_bairros_salvador_flavio_bolsonaro_ensino_superior.csv",
    png_output: str = "grafico_comparativo_tesoura_salvador.png",
    html_output: str = "grafico_comparativo_tesoura_salvador.html"
):
    print(f"[*] Carregando dados para análise comparativa...")
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    x = df["pct_superior_completo"]
    y_flavio = df["pct_votos_validos_flavio"]
    y_lula = df["pct_votos_validos_lula"]

    # Regressões
    s_f, i_f, r_f, p_f, _ = stats.linregress(x, y_flavio)
    s_l, i_l, r_l, p_l, _ = stats.linregress(x, y_lula)

    x_vals = np.linspace(x.min(), x.max(), 100)
    y_f_vals = s_f * x_vals + i_f
    y_l_vals = s_l * x_vals + i_l

    # Ponto de cruzamento da regressão
    # s_f * x + i_f = s_l * x + i_l  =>  x = (i_l - i_f) / (s_f - s_l)
    x_cross = (i_l - i_f) / (s_f - s_l)
    y_cross = s_f * x_cross + i_f

    # 1. FIGURA MATPLOTLIB (300 DPI)
    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig, ax = plt.subplots(figsize=(15, 8.5), facecolor="#0f172a", dpi=300)
    ax.set_facecolor("#1e293b")
    ax.grid(True, linestyle="--", alpha=0.2, color="#94a3b8")
    ax.set_axisbelow(True)

    # Dispersão Flávio (Azul Celeste)
    ax.scatter(
        x, y_flavio,
        s=np.sqrt(df["eleitores_aptos_bairro"]) * 2.0,
        color="#38bdf8",
        alpha=0.65,
        edgecolors="#ffffff",
        linewidth=0.7,
        label=f"Flávio Bolsonaro (r = +{r_f:.2f})"
    )

    # Dispersão Lula (Vermelho / Coral)
    ax.scatter(
        x, y_lula,
        s=np.sqrt(df["eleitores_aptos_bairro"]) * 2.0,
        color="#ef4444",
        alpha=0.65,
        edgecolors="#ffffff",
        linewidth=0.7,
        label=f"Lula (r = {r_l:.2f})"
    )

    # Retas de regressão
    ax.plot(x_vals, y_f_vals, color="#0284c7", linewidth=3.5, linestyle="-")
    ax.plot(x_vals, y_l_vals, color="#dc2626", linewidth=3.5, linestyle="-")

    # Linha vertical e marcador no ponto de inflexão/cruzamento
    if 0 <= x_cross <= 75:
        ax.axvline(x_cross, color="#fbbf24", linestyle=":", linewidth=1.8, alpha=0.8)
        ax.scatter([x_cross], [y_cross], color="#fbbf24", s=140, zorder=5, edgecolors="#000000", linewidth=1.5)
        ax.annotate(
            f"Ponto de Cruzamento Teórico\n({x_cross:.1f}% Sup. / {y_cross:.1f}% Votos)",
            xy=(x_cross, y_cross),
            xytext=(x_cross - 14, y_cross - 8),
            fontsize=9,
            fontweight="bold",
            color="#fbbf24",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#0f172a", edgecolor="#fbbf24", alpha=0.9),
            arrowprops=dict(arrowstyle="->", color="#fbbf24", lw=1.2)
        )

    # Destaques com setas
    destaques = [
        ("ITAIGARA", 63.33, 47.32, 42.70),
        ("PATAMARES", 60.85, 45.11, 44.04),
        ("PITUBA", 46.38, 38.05, 52.64),
        ("PERIPERI", 4.56, 27.57, 65.23),
        ("ILHA DE MARÉ", 1.71, 14.05, 81.99),
        ("BAIRRO DA PAZ", 4.98, 18.27, 75.34),
    ]

    for nome, bx, by_f, by_l in destaques:
        # Anotar o bairro conectando ambos os pontos
        ax.plot([bx, bx], [by_f, by_l], color="#64748b", linestyle="--", linewidth=0.9, alpha=0.6)
        y_mid = (by_f + by_l) / 2
        ax.text(
            bx + 0.8, y_mid, nome,
            fontsize=8, fontweight="bold", color="#f8fafc",
            va="center",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#090d16", edgecolor="#475569", alpha=0.85)
        )

    # Box de resumo analítico
    box_txt = (
        "EFEITO TESOURA ELEITORAL (SALVADOR 2026)\n"
        "-----------------------------------------\n"
        f"• Flávio (PL 22): r = +{r_f:.4f} (R² = {r_f**2:.2f})\n"
        f"• Lula (PT 13):   r = {r_l:.4f} (R² = {r_l**2:.2f})\n"
        "• Correlação quase perfeitamente antagônica\n"
        "• Flávio lidera no Itaigara e Patamares\n"
        "• Lula amplia vantagem em áreas populares (<10% Sup.)"
    )
    ax.text(
        0.03, 0.28, box_txt,
        transform=ax.transAxes,
        fontsize=9,
        color="#f1f5f9",
        va="top",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#090d16", edgecolor="#38bdf8", alpha=0.92, linewidth=1.2)
    )

    ax.set_title("O 'Efeito Tesoura': Votação de Flávio Bolsonaro vs. Lula por Ensino Superior\n(Salvador - Eleições 2026, 151 Bairros)", fontsize=14, fontweight="bold", color="#f8fafc", pad=15)
    ax.set_xlabel("% Eleitores com Ensino Superior Completo no Bairro", fontsize=11, color="#cbd5e1", labelpad=10)
    ax.set_ylabel("% de Votos Válidos", fontsize=11, color="#cbd5e1", labelpad=10)
    ax.xaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))
    ax.set_ylim(10, 90)
    ax.tick_params(colors="#94a3b8", labelsize=10)
    ax.legend(loc="upper right", facecolor="#0f172a", edgecolor="#475569", fontsize=10, labelcolor="#f1f5f9")
    for spine in ax.spines.values():
        spine.set_color("#334155")

    fig.text(0.5, 0.015, "Fonte: Dados Consolidados de Seções Eleitorais do TSE | Salvador - BA", ha="center", fontsize=9, color="#64748b")
    fig.subplots_adjust(left=0.07, right=0.96, top=0.92, bottom=0.08)
    fig.savefig(png_output, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"[+] Gráfico comparativo salvo em: {png_output}")

    # 2. PLOTLY HTML COMPARATIVO
    fig_plotly = go.Figure()

    hover_tpl = (
        "<b>%{customdata[0]}</b><br>" +
        "• Candidato: <b>%{customdata[1]}</b><br>" +
        "• Votação: <b>%{y:.2f}%</b> (%{customdata[2]:,} votos)<br>" +
        "• Superior Completo: <b>%{x:.2f}%</b><br>" +
        "• Eleitores Aptos: %{customdata[3]:,}<extra></extra>"
    )

    # Trace Flávio
    cd_f = np.column_stack([df["bairro"], ["Flávio Bolsonaro"]*len(df), df["votos_flavio_bolsonaro"], df["eleitores_aptos_bairro"]])
    fig_plotly.add_trace(go.Scatter(
        x=x, y=y_flavio,
        mode="markers",
        name="Flávio Bolsonaro (PL)",
        marker=dict(size=np.sqrt(df["eleitores_aptos_bairro"])*0.16 + 5, color="#38bdf8", opacity=0.75, line=dict(color="#ffffff", width=1)),
        customdata=cd_f,
        hovertemplate=hover_tpl
    ))

    # Trace Lula
    cd_l = np.column_stack([df["bairro"], ["Lula"]*len(df), df["votos_lula"], df["eleitores_aptos_bairro"]])
    fig_plotly.add_trace(go.Scatter(
        x=x, y=y_lula,
        mode="markers",
        name="Lula (PT)",
        marker=dict(size=np.sqrt(df["eleitores_aptos_bairro"])*0.16 + 5, color="#ef4444", opacity=0.75, line=dict(color="#ffffff", width=1)),
        customdata=cd_l,
        hovertemplate=hover_tpl
    ))

    # Linhas de tendência
    fig_plotly.add_trace(go.Scatter(x=x_vals, y=y_f_vals, mode="lines", name=f"Tendência Flávio (r = +{r_f:.2f})", line=dict(color="#0284c7", width=3)))
    fig_plotly.add_trace(go.Scatter(x=x_vals, y=y_l_vals, mode="lines", name=f"Tendência Lula (r = {r_l:.2f})", line=dict(color="#dc2626", width=3)))

    fig_plotly.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0b1120",
        plot_bgcolor="#111827",
        title=dict(
            text="<b>O 'Efeito Tesoura': Votação Flávio Bolsonaro vs. Lula por Ensino Superior</b><br><span style='font-size:12px; color:#94a3b8;'>Correlação com 151 bairros de Salvador (2026) | Confronto direto de tendências</span>",
            x=0.03, y=0.96,
            font=dict(size=18, color="#f8fafc")
        ),
        font=dict(family="sans-serif", color="#e2e8f0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=60, r=40, t=100, b=50),
        height=720
    )
    fig_plotly.update_xaxes(title_text="% Eleitores com Ensino Superior Completo", ticksuffix="%")
    fig_plotly.update_yaxes(title_text="% Votos Válidos", ticksuffix="%")

    fig_plotly.write_html(html_output, include_plotlyjs="cdn")
    print(f"[+] HTML comparativo salvo em: {html_output}")

if __name__ == "__main__":
    gerar_grafico_comparativo()
