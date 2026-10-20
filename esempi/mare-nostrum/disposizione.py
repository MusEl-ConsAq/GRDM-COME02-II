#!/usr/bin/env python3
"""Disegna la disposizione degli stream di mare-nostrum (capitolo 10).

Uso:  python esempi/mare-nostrum/disposizione.py [../mare-nostrum/configs/mare-nostrum.yml]

Legge il master del brano e, per ogni `file:`, lo stream importato; scrive
docs/images/mare-nostrum_disposizione.pdf. Il brano non e' in questo repo (e'
incompiuto): lo script serve a rifare la figura dal suo stato corrente.
"""
import os, sys
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(AQUI))
master = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else
                         os.path.join(REPO, "..", "mare-nostrum", "configs", "mare-nostrum.yml"))
base = os.path.dirname(master)

m = yaml.safe_load(open(master))
righe = []
for e in m["streams"]:
    s = yaml.safe_load(open(os.path.join(base, e["file"])))
    st = s["streams"][0] if "streams" in s else s
    righe.append(dict(nome=os.path.splitext(os.path.basename(e["file"]))[0],
                      onset=e.get("onset", 0.0), durata=st["duration"],
                      sample=os.path.splitext(st["sample"])[0],
                      muto=bool(e.get("mute")),
                      voci=(st.get("voices") or {}).get("num_voices", 1)))

campioni = sorted({r["sample"] for r in righe})
tab = plt.get_cmap("tab10")
colore = {c: tab(i) for i, c in enumerate(campioni)}

fig, ax = plt.subplots(figsize=(10, 3.8))
for i, r in enumerate(righe):
    y = len(righe) - 1 - i
    ax.barh(y, r["durata"], left=r["onset"], height=0.62,
            color=colore[r["sample"]], alpha=0.35 if r["muto"] else 0.9,
            hatch="////" if r["muto"] else None, edgecolor="black", linewidth=0.5)
    if r["voci"] > 1:
        ax.text(r["onset"] + r["durata"] + 3, y, f'{r["voci"]} voci', va="center", fontsize=7)
ax.set_yticks(range(len(righe)))
ax.set_yticklabels([r["nome"] + ("  (muto)" if r["muto"] else "") for r in reversed(righe)], fontsize=8)
ax.set_xlim(0, m["duration"])
ax.set_xlabel("Tempo del brano (s)")
ax.grid(axis="x", linestyle=":", linewidth=0.5)
ax.legend(handles=[Patch(color=colore[c], label=c) for c in campioni],
          title="Campione sorgente", fontsize=7, title_fontsize=7,
          loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False)
fig.tight_layout()
out = os.path.join(REPO, "docs", "images", "mare-nostrum_disposizione.pdf")
fig.savefig(out)
print("figura:", out)
