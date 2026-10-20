# Esempi

Sorgenti YAML degli esempi della tesina, uno per cartella (`<nome>/<nome>.yml`).
Ogni esempio isola un meccanismo di PythonGranularEngine; le MAP (partiture
grafiche) in `docs/images/<nome>_map.pdf` sono generate da questi file.

`identity`, `pointer`, `distribution`, `probability`, `deviation`, `duration` e
`complete_example` vengono dal paper CIM 2026; `loop`, `pitch`, `window`,
`read_direction`, `voices_chords`, `voices_fade` e `grain_height` sono nuovi
(`grain_height` serve al capitolo 8 e `render.py` ne scrive tre varianti della MAP). Tutti dichiarano `seed`, quindi la realizzazione è
quella che si riottiene rieseguendoli. I commenti iniziali dei file del paper
sono quelli originali e in parte datati (p. es. quelli sul seme).

```bash
# serve il repo del motore accanto a questo (o PGE_DIR=...) col suo venv
../PythonGranularEngine/.venv/bin/python esempi/render.py            # tutte le MAP
../PythonGranularEngine/.venv/bin/python esempi/render.py --audio esempi/pitch/pitch.yml
```

`render.py` scrive le MAP in `docs/images/` e, con `--audio`, il file audio accanto
allo YAML (`.aif`, ignorato da git). I campioni sono quelli di `PGE_DIR/refs`
(`voice.wav`).
