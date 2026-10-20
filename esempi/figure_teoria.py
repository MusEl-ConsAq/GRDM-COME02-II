#!/usr/bin/env python3
"""Figure del capitolo 2 (la sintesi granulare): non sono MAP, sono grafici di teoria.

Uso:  python esempi/figure_teoria.py

Scrive in docs/images/:
  gabor_quanto.pdf     il segnale elementare di Gabor e la sua cella nel piano
                       tempo-frequenza, per tre valori della costante alfa;
  finestre_catalogo.pdf otto finestre del catalogo di PGE, con i nomi del catalogo (non
                       tutti coincidono con le forme che Roads chiama allo stesso modo).

PGE_DIR (default ../PythonGranularEngine) indica il repo del motore.
"""
import os, sys
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(AQUI)
PGE = os.path.abspath(os.environ.get("PGE_DIR", os.path.join(REPO, "..", "PythonGranularEngine")))
sys.path.insert(0, os.path.join(PGE, "src"))

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["pdf.fonttype"] = 42
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

IMG = os.path.join(REPO, "docs", "images")


def gabor():
    """s(t) = exp(-a^2 (t-t0)^2) cos(2 pi f0 t), con dt = sqrt(pi)/a e df = a/sqrt(pi): dt*df = 1."""
    f0, t0 = 6.0, 0.0
    t = np.linspace(-3.2, 3.2, 4000)
    fig, assi = plt.subplots(2, 3, figsize=(9, 4.6), gridspec_kw={"height_ratios": [1, 1.25]})
    for col, a in enumerate((0.7, 1.4, 2.8)):
        s = np.exp(-(a ** 2) * (t - t0) ** 2) * np.cos(2 * np.pi * f0 * t)
        dt, df = np.sqrt(np.pi) / a, a / np.sqrt(np.pi)
        ax = assi[0, col]
        ax.plot(t, s, lw=0.8, color="black")
        ax.plot(t, np.exp(-(a ** 2) * (t - t0) ** 2), lw=0.6, color="steelblue", ls="--")
        ax.set_xlim(-3.2, 3.2); ax.set_ylim(-1.15, 1.15)
        ax.set_title(rf"$\alpha = {a}$", fontsize=9)
        ax.set_xlabel("tempo (unità arbitrarie)", fontsize=8)
        ax.tick_params(labelsize=7)
        ax = assi[1, col]
        ax.add_patch(Rectangle((t0 - dt / 2, f0 - df / 2), dt, df, fc="steelblue", alpha=0.35, ec="black", lw=0.8))
        ax.set_xlim(-3.2, 3.2); ax.set_ylim(f0 - 3.2, f0 + 3.2)
        ax.set_xlabel("tempo", fontsize=8)
        ax.set_aspect("auto")
        ax.text(0.03, 0.93, rf"$\Delta t = {dt:.2f}$  $\Delta f = {df:.2f}$" "\n" rf"$\Delta t\,\Delta f = {dt * df:.1f}$",
                transform=ax.transAxes, va="top", fontsize=8)
        ax.tick_params(labelsize=7)
        if col == 0:
            assi[0, col].set_ylabel("ampiezza", fontsize=8)
            ax.set_ylabel("frequenza", fontsize=8)
    fig.tight_layout()
    out = os.path.join(IMG, "gabor_quanto.pdf")
    fig.savefig(out); plt.close(fig)
    print("figura:", out)


def finestre():
    from pge.rendering.numpy_window_registry import NumpyWindowRegistry
    reg = NumpyWindowRegistry()
    nomi = ["gaussian", "hanning", "bartlett", "sinc", "expodec", "rexpodec", "exporise", "rexporise"]
    fig, assi = plt.subplots(2, 4, figsize=(9.5, 3.8), sharey=True)
    for ax, nome in zip(assi.flat, nomi):
        w = reg.get(nome, 512)
        x = np.linspace(0, 1, len(w))
        ax.plot(x, w, color="black", lw=0.9)
        ax.fill_between(x, w, alpha=0.2, color="steelblue")
        ax.set_title(nome, fontsize=8, family="monospace")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1.05); ax.tick_params(labelsize=7)
    for ax in assi[1]:
        ax.set_xlabel("tempo nel grano (normalizzato)", fontsize=7)
    for ax in assi[:, 0]:
        ax.set_ylabel("ampiezza", fontsize=8)
    fig.tight_layout()
    out = os.path.join(IMG, "finestre_catalogo.pdf")
    fig.savefig(out); plt.close(fig)
    print("figura:", out)


if __name__ == "__main__":
    gabor()
    finestre()
