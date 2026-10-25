#!/usr/bin/env python3
"""Figura del capitolo 11: i profili polari dei decoder e un anello di otto altoparlanti.

Uso:  python esempi/spazializzazione/figura_spazializzazione.py

Scrive docs/images/spazializzazione_decoder.pdf: a sinistra i profili polari della
figura di otto, del cardioide e del nucleo 1 + 2cos(theta - phi) di Gerzon (i lobi
negativi, in controfase, sono tratteggiati); a destra gli otto altoparlanti di un anello
regolare, con un cerchio proporzionale al guadagno per una sorgente a 30 gradi.
"""
import os
import numpy as np

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(os.path.dirname(os.path.dirname(AQUI)), "docs", "images")


def polare(ax):
    ax.set_theta_zero_location("N")      # 0 davanti
    ax.set_theta_direction(1)            # positivo a sinistra, come il pan di PGE
    ax.set_xticks(np.radians(np.arange(0, 360, 45)))
    ax.tick_params(labelsize=7)


def main():
    t = np.radians(np.linspace(0, 360, 721))
    profili = [("figura di otto", np.cos(t), "0.55", "-"),
               ("cardioide", 0.5 + 0.5 * np.cos(t), "steelblue", "-"),
               (r"$(1 + 2\cos)/3$", (1 + 2 * np.cos(t)) / 3, "black", "-")]

    fig = plt.figure(figsize=(9, 4.4))
    ax = fig.add_subplot(1, 2, 1, projection="polar")
    polare(ax)
    for nome, f, col, _ in profili:
        pos, neg = np.where(f >= 0, f, np.nan), np.where(f < 0, -f, np.nan)
        ax.plot(t, pos, color=col, lw=1.1, label=nome)
        ax.plot(t, neg, color=col, lw=1.1, ls=(0, (3, 2)))
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0.5, 1.0]); ax.set_yticklabels(["0,5", "1"], fontsize=6)
    ax.set_title("profili di un altoparlante (tratteggio: controfase)", fontsize=8, pad=14)
    ax.legend(loc="lower left", bbox_to_anchor=(-0.18, -0.2), fontsize=7, frameon=False)

    N, src = 8, np.radians(30)
    phi = 2 * np.pi * np.arange(N) / N
    g = (1 + 2 * np.cos(src - phi)) / N
    ax = fig.add_subplot(1, 2, 2, projection="polar")
    polare(ax)
    for ph, gk in zip(phi, g):
        ax.scatter(ph, 1, s=900 * abs(gk), facecolor="black" if gk >= 0 else "white",
                   edgecolor="black", lw=1.0, zorder=3)
        etichetta = "0,00" if abs(gk) < 5e-3 else f"{gk:+.2f}".replace(".", ",")
        ax.text(ph, 1.32, etichetta, ha="center", va="center", fontsize=7)
    ax.annotate("", xy=(src, 0.78), xytext=(src, 0.0),
                arrowprops=dict(arrowstyle="-|>", color="steelblue", lw=1.4))
    ax.set_ylim(0, 1.5)
    ax.set_yticks([])
    ax.set_title("otto altoparlanti, sorgente a 30° (guadagni)", fontsize=8, pad=14)
    fig.tight_layout()
    out = os.path.join(IMG, "spazializzazione_decoder.pdf")
    fig.savefig(out, bbox_inches="tight"); plt.close(fig)
    print("figura:", out)


if __name__ == "__main__":
    main()
