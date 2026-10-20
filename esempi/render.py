#!/usr/bin/env python3
"""Rende le MAP (e, con --audio, i file audio) degli esempi con PythonGranularEngine.

Uso:  python esempi/render.py [--audio] esempi/pitch/pitch.yml [...]
      (senza argomenti: tutti gli esempi)

PGE_DIR (default ../PythonGranularEngine) indica il repo del motore: se ne usano
src/ e refs/ (i campioni). Le MAP vanno in docs/images/<token>_map.pdf, cosi' la
build della tesina non ha bisogno di PGE; l'audio in esempi/<token>/<token>.aif.
"""
import os, sys, glob

AQUI = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(AQUI)
PGE = os.path.abspath(os.environ.get("PGE_DIR", os.path.join(REPO, "..", "PythonGranularEngine")))
sys.path.insert(0, os.path.join(PGE, "src"))

# Lente d'ingrandimento (POC) per esempio: stessi target del paper.
LENTI = {
    "identity": [{"t": 1.0, "zoom": 5.0, "corner": "top-left"}],
    "distribution": [{"t": 2.5, "y": 1.035, "zoom": 30.0, "corner": "bottom-left"},
                     {"t": 17.5, "y": 1.035, "zoom": 30.0, "corner": "bottom-right"}],
    "duration": [{"t": 5.0, "zoom": 13.0, "corner": "top-right"}],
    "window": [{"t": 0.6, "zoom": 5.0, "corner": "top-left"},
               {"t": 3.0, "zoom": 5.0, "corner": "top-right"},
               {"t": 5.4, "zoom": 5.0, "corner": "bottom-right"}],
    "read_direction": [{"t": 2.0, "zoom": 6.0, "corner": "top-left"},
                       {"t": 5.0, "zoom": 6.0, "corner": "bottom-right"}],
    "complete_example": [{"t": 13, "y": .6, "zoom": 40.0, "corner": "top-left"},
                         {"t": 27.5, "y": .6, "zoom": 40.0, "corner": "top-right"}],
}

# Varianti di lettura della stessa MAP (capitolo 8): file docs/images/<token>_<tag>_map.pdf.
VARIANTI = {
    "grain_height": {
        "duration": {"grain_shape": "arrow"},
        "readspan": {"grain_shape": "arrow", "grain_height": "read_span"},
        "bw": {"grain_shape": "arrow", "bw": True},
    },
}

def main():
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42   # testo estraibile dal PDF
    from pge import api

    args = sys.argv[1:]
    audio = "--audio" in args
    ymls = [a for a in args if a != "--audio"] or sorted(glob.glob(os.path.join(AQUI, "*", "*.yml")))
    refs = os.path.join(PGE, "refs")
    for yml in ymls:
        yml = os.path.abspath(yml)
        nome = os.path.splitext(os.path.basename(yml))[0]
        gen = api.load_generator(yml, samples_dir=refs)
        durata = max(s.onset + s.duration for s in gen.streams)
        config = {"page_duration": durata, "font_scale": 2.3, "grain_shape": "window"}
        if nome in LENTI:
            config["magnify_targets"] = LENTI[nome]
        pdf = os.path.join(REPO, "docs", "images", nome + "_map.pdf")
        api.export_score_pdf(gen, pdf, config=config, samples_dir=refs)
        print("MAP:", pdf)
        for tag, extra in VARIANTI.get(nome, {}).items():
            var = os.path.join(REPO, "docs", "images", f"{nome}_{tag}_map.pdf")
            api.export_score_pdf(gen, var, config={**config, **extra}, samples_dir=refs)
            print("MAP:", var)
        if audio:
            aif = os.path.join(os.path.dirname(yml), nome + ".aif")
            api.render_file(yml, aif, per_stream=(nome == "deviation"), samples_dir=refs)
            print("audio:", aif)

if __name__ == "__main__":
    main()
