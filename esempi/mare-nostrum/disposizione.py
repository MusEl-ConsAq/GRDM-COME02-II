#!/usr/bin/env python3
"""Disegna la disposizione degli stream di mare-nostrum (capitolo 10).

Uso:  python esempi/mare-nostrum/disposizione.py [../mare-nostrum/configs/mare-nostrum.yml]

Legge il master del brano e, per ogni voce di `streams:`, lo stream: quello
importato dal file se la voce ha `file:`, altrimenti la voce stessa, che e' uno
stream scritto dentro il master (cosi' li salva PGE-ui). Scrive
docs/images/mare-nostrum_disposizione.pdf. Il brano non e' in questo repo: lo
script serve a rifare la figura dal suo stato corrente.

Una riga per stream, in ordine di ingresso. Il colore e' il campione sorgente;
a sinistra, accanto al nome, il campione; a destra della barra, il numero di
voci quando e' maggiore di uno. Gli stream che hanno soltanto i valori
predefiniti (capitolo 4: la risintesi identica della sorgente) sono tratteggiati;
gli stream silenziati (`mute`) sono tratteggiati e pallidi. I tratti in cui non
suona nessuno stream sono in grigio, e quelli piu' lunghi di dieci secondi
portano la durata.
"""
import math
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml
from matplotlib.patches import Patch

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(AQUI))

# Chiavi di piazzamento: stanno nel master accanto a `file:` e, in uno stream
# scritto dentro, accanto al resto.
PIAZZAMENTO = ("onset", "mute", "solo")

# Lo stream minimo del capitolo 4: con questi valori la lista dei grani
# ricostruisce la sorgente. Le chiavi che non cambiano il risultato (identita',
# durata, campione, modi temporali, unita' del puntatore) non contano.
PREDEFINITI = {"fill_factor": 2, "distribution": 0, "grain.duration": 0.05,
               "grain.envelope": "hanning", "pointer.speed_ratio": 1,
               "pointer.start": 0, "pitch.ratio": 1, "pan": 0, "volume": 0}
NEUTRE = {"stream_id", "duration", "sample", "time_mode", "distribution_mode",
          "pointer.loop_unit", *PIAZZAMENTO}

SOGLIA_VUOTO = 10.0  # secondi: sotto, il tratto vuoto non si annota


def appiattisci(d, pre=""):
    for k, v in d.items():
        if isinstance(v, dict) and "points" not in v:
            yield from appiattisci(v, pre + k + ".")
        else:
            yield pre + k, v


def e_predefinito(st):
    """Vero se lo stream ha solo valori predefiniti (o neutri)."""
    return all(k in NEUTRE or PREDEFINITI.get(k, object()) == v
               for k, v in appiattisci(st))


def valori(v):
    """I valori di un parametro: scalare, lista di punti o dizionario {type, points}."""
    if isinstance(v, dict):
        v = v.get("points", [])
    if isinstance(v, (int, float)):
        return [float(v)]
    return [float(p[1]) for p in v if isinstance(p, (list, tuple)) and len(p) > 1]


def codice(stem):
    """Il nome breve di un campione: `001-41_5-5_5` -> `001-41`, `016` -> `016`."""
    m = re.match(r"\d{3}(?:-\d+)?", stem)
    return m.group(0) if m else stem


def leggi(percorso):
    with open(percorso, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def stream_del_master(master, base):
    """Per ogni voce del master: lo stream risolto, col suo piazzamento."""
    out = []
    for voce in master["streams"]:
        if "file" in voce:
            doc = leggi(os.path.join(base, voce["file"]))
            st = doc["streams"][0] if "streams" in doc else doc
            sid = voce.get("stream_id", os.path.splitext(os.path.basename(voce["file"]))[0])
            s = {k: v for k, v in st.items() if k not in PIAZZAMENTO and k != "stream_id"}
            s["stream_id"] = sid
            s.update({k: voce[k] for k in PIAZZAMENTO if k in voce})
        else:
            s = dict(voce)
        s.setdefault("onset", 0.0)
        out.append(s)
    return out


def righe_del_brano(master_path):
    master_path = os.path.abspath(master_path)
    master = leggi(master_path)
    righe = []
    for s in stream_del_master(master, os.path.dirname(master_path)):
        nv = valori((s.get("voices") or {}).get("num_voices", 1)) or [1.0]
        righe.append(dict(nome=s["stream_id"], onset=float(s["onset"]),
                          durata=float(s["duration"]),
                          sample=os.path.splitext(s["sample"])[0],
                          muto=bool(s.get("mute")), voci=math.ceil(max(nv)),
                          voci_min=min(nv), voci_max=max(nv),
                          minimo=e_predefinito(s)))
    righe.sort(key=lambda r: r["onset"])
    return master, righe


def tratti_vuoti(righe, fine):
    """Gli intervalli in cui non suona nessuno stream attivo, fino a `fine`."""
    attivi = sorted((r["onset"], r["onset"] + r["durata"]) for r in righe if not r["muto"])
    vuoti, fino = [], 0.0
    for a, b in attivi:
        if a > fino:
            vuoti.append((fino, a))
        fino = max(fino, b)
    if fino < fine:
        vuoti.append((fino, fine))
    return vuoti


def disegna(righe, out):
    """La figura: gli stream del brano, fino alla fine dell'ultimo."""
    fine = max(r["onset"] + r["durata"] for r in righe)
    # i campioni in ordine di ingresso: i primi prendono le tinte scure di tab20
    # (distinte fra loro), gli ultimi le chiare
    campioni = list(dict.fromkeys(r["sample"] for r in righe))
    tab = plt.get_cmap("tab20")
    ordine = [0, 2, 4, 6, 8, 10, 12, 16, 18, 14, 1, 3, 5, 7, 9, 11, 13, 17, 19, 15]
    colore = {c: tab(ordine[i % 20]) for i, c in enumerate(campioni)}
    breve = {c: codice(c) for c in campioni}
    if len(set(breve.values())) < len(breve):  # due campioni con lo stesso codice
        breve = {c: c for c in campioni}
    n = len(righe)

    plt.rcParams.update({"font.size": 6, "hatch.linewidth": 0.5})
    fig, ax = plt.subplots(figsize=(6.7, 0.135 * n + 0.75))
    for a, b in tratti_vuoti(righe, fine):
        ax.axvspan(a, b, color="0.93", zorder=0, linewidth=0)
        # l'ultimo tratto e' la coda che il master aggiunge dopo l'ultimo stream
        if b - a > SOGLIA_VUOTO and b < fine:
            ax.text((a + b) / 2, n - 0.05, f"nessuno stream\n{b - a:.0f} s".replace(".", ","),
                    ha="center", va="top", fontsize=6, color="0.35")
    for i, r in enumerate(righe):
        y = n - 1 - i
        ax.barh(y, r["durata"], left=r["onset"], height=0.72,
                color=colore[r["sample"]], alpha=0.35 if r["muto"] else 0.92,
                hatch="//////" if (r["muto"] or r["minimo"]) else None,
                edgecolor="black", linewidth=0.4, zorder=2)
        if r["voci"] > 1:
            if r["voci_min"] != r["voci_max"]:
                testo = f'{r["voci_min"]:g}–{r["voci_max"]:.1f}'.replace(".", ",").replace(",0", "") + " voci"
            else:
                testo = f'{r["voci"]} voci'
            if r["onset"] + r["durata"] + 0.075 * fine > fine:  # non c'e' posto a destra
                ax.text(r["onset"] - 4, y, testo, va="center", ha="right", fontsize=5.5, zorder=3)
            else:
                ax.text(r["onset"] + r["durata"] + 4, y, testo, va="center", fontsize=5.5, zorder=3)
    ax.set_yticks(range(n))
    ax.set_yticklabels([f'{r["nome"]}  ({breve[r["sample"]]})' + ("  muto" if r["muto"] else "")
                        for r in reversed(righe)], fontsize=5.5)
    ax.set_ylim(-0.7, n + 0.1)
    ax.set_xlim(0, fine)
    ax.set_xlabel("Tempo del brano (s)", fontsize=6.5)
    ax.tick_params(axis="x", labelsize=6)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", linestyle=":", linewidth=0.4, zorder=1)
    for lato in ("top", "right"):
        ax.spines[lato].set_visible(False)

    legenda = []
    if any(r["minimo"] for r in righe):
        legenda.append(Patch(facecolor="white", edgecolor="black", hatch="//////", linewidth=0.4,
                             label="valori predefiniti (risintesi identica)"))
    if any(r["muto"] for r in righe):
        legenda.append(Patch(facecolor="white", edgecolor="black", hatch="//////", alpha=0.35,
                             linewidth=0.4, label="silenziato (mute)"))
    if legenda:
        # l'angolo in basso a destra e' occupato dagli ultimi stream, quello in alto
        # dall'annotazione del vuoto: la legenda sta a meta' altezza, a destra
        ax.legend(handles=legenda, loc="center right", bbox_to_anchor=(0.995, 0.62),
                  fontsize=5.5, frameon=True, framealpha=0.95, edgecolor="0.7", borderpad=0.4)
    fig.tight_layout(pad=0.4)
    fig.savefig(out)
    plt.close(fig)


if __name__ == "__main__":
    master_path = (sys.argv[1] if len(sys.argv) > 1 else
                   os.path.join(REPO, "..", "mare-nostrum", "configs", "mare-nostrum.yml"))
    master, righe = righe_del_brano(master_path)
    out = os.path.join(REPO, "docs", "images", "mare-nostrum_disposizione.pdf")
    disegna(righe, out)
    print("figura:", out)
