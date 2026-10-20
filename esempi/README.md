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

`mare-nostrum/disposizione.py` non e' un esempio ma uno script: disegna la disposizione degli stream del brano *mare-nostrum* (capitolo 10) leggendo il master dal repository del brano (`../mare-nostrum/configs/mare-nostrum.yml`, o un percorso passato come argomento). Il brano e' incompiuto e non e' copiato qui.

`figure_teoria.py` non rende MAP: disegna le due figure del capitolo 2 (il segnale elementare di Gabor e otto finestre del catalogo di PGE).

`architettura/` raccoglie ciò che serve al capitolo 3 e non è un esempio di YAML. `pipeline.tex` e `dipendenze.tex` sono le due figure in TikZ (la pipeline e il verso delle dipendenze tra i pacchetti): si compilano con XeLaTeX e il PDF va in `docs/images/` (`xelatex -output-directory=/tmp/fig pipeline.tex && cp /tmp/fig/pipeline.pdf ../../docs/images/`), cosi' la build della tesina non dipende da TikZ. `dipendenze.py` costruisce il grafo degli import di `pge` e verifica che tra i moduli non ci siano cicli e che nessun pacchetto della parte generativa importi `rendering`, `engine` ed `export`. `lazy_e_riproducibilita.py` verifica con `assert` le affermazioni del capitolo sulla generazione lazy e sul seme: nessun grano alla costruzione, grani indipendenti dall'ordine di generazione e dal mute degli altri stream, stessa impronta in processi con `PYTHONHASHSEED` diverso, nessun grano generato quando la cache e' a regime. Entrambi gli script usano `PGE_DIR` come `render.py`; il secondo vuole il venv del motore (`../PythonGranularEngine/.venv/bin/python`).

`linguaggio/verifica_linguaggio.py` verifica con `assert` le affermazioni del capitolo 4 sul linguaggio YAML, sul motore vero: i valori predefiniti dello stream minimo e il guadagno del suo rendering, `null` e `0`, `solo` e `mute`, le espressioni matematiche e i loro limiti, la banda dei `_range`, l'inviluppo (forme, interpolazioni, bordi, tempo normalizzato), i numeri dell'esempio del puntatore, ciò che il linguaggio lascia passare, il seme e `rng_group`, lo stream come file. Usa `PGE_DIR` come gli altri script e vuole il venv del motore; la parte su `file:` esiste in `main` e non nella 9.1.0, e si salta da sola se manca.
