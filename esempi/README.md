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

`mare-nostrum/disposizione.py` non e' un esempio ma uno script: disegna la disposizione degli stream del brano *mare-nostrum* (capitolo 10) leggendo il master dal repository del brano (`../mare-nostrum/configs/mare-nostrum.yml`, o un percorso passato come argomento). Gli stream del master possono essere importati con `file:` o scritti dentro, e lo script li legge in tutti e due i modi. Il brano e' incompiuto e non e' copiato qui.

`mare-nostrum/verifica_brano.py` verifica con `assert` le cifre del capitolo 10 sul master del brano (lo stesso di `disposizione.py`) e sul motore vero: la testa del master e le due forme degli stream, il profilo del brano nel tempo (i due gruppi, la sovrapposizione massima), i campioni, le copie (`stream25`, e `stream26` e `stream27` accorciati, con gli inviluppi uguali in secondi fino al taglio), le durate dei grani, il gate e le voci dei due vocabolari, il numero di grani di ogni stream e le densita' che ne vengono, la realizzazione diversa di una copia e il caso di `rng_group`, la tabella del capitolo, il modello di costo del capitolo 7 e la regola «un file per stream» del repository del brano. Le cifre sono quelle del master al commit `399de71` del repository del brano, col motore `1188dbc` che quel repository fissa: se il brano va avanti le verifiche falliscono, ed e' il segnale che il capitolo va riletto. Il motore e' quello del submodule `engine/` del repository del brano, se c'e', altrimenti `PGE_DIR`. Non servono i campioni audio, che il brano non versiona: si usa rumore sintetico dai nomi giusti, perche' il numero di grani non dipende dal contenuto. Impiega circa due minuti su quattro processi.

`figure_teoria.py` non rende MAP: disegna le due figure del capitolo 2 (il segnale elementare di Gabor e otto finestre del catalogo di PGE).

`sintesi-granulare/verifica_sintesi_granulare.py` verifica con `assert` ciò che del capitolo 2 un programma può controllare: la matematica del segnale elementare di Gabor (larghezze, area unitaria, la costante che dipende dalla convenzione), l'aritmetica delle tabelle e degli esempi, il grano di otto campi, le chiavi YAML della tabella dei sette parametri della nuvola, l'equivalenza di fill factor e densità, il confronto fra le finestre di PGE e quelle di Roads e le bande laterali di un flusso regolare, misurate sul rendering. Le date, i virgolettati, le cifre e le pagine di Gabor, Xenakis, Roads, Truax, Lippe e Dutilleux si controllano sulle fonti e non si verificano qui. Usa `PGE_DIR` come gli altri script e vuole il venv del motore, ma non `voice.wav` (genera un tono); passa sia sulla 9.1.0 sia su `main`.

`architettura/` raccoglie ciò che serve al capitolo 3 e non è un esempio di YAML. `pipeline.tex` e `dipendenze.tex` sono le due figure in TikZ (la pipeline e il verso delle dipendenze tra i pacchetti): si compilano con XeLaTeX e il PDF va in `docs/images/` (`xelatex -output-directory=/tmp/fig pipeline.tex && cp /tmp/fig/pipeline.pdf ../../docs/images/`), cosi' la build della tesina non dipende da TikZ. `dipendenze.py` costruisce il grafo degli import di `pge` e verifica che tra i moduli non ci siano cicli e che nessun pacchetto della parte generativa importi `rendering`, `engine` ed `export`. `lazy_e_riproducibilita.py` verifica con `assert` le affermazioni del capitolo sulla generazione lazy e sul seme: nessun grano alla costruzione, grani indipendenti dall'ordine di generazione e dal mute degli altri stream, stessa impronta in processi con `PYTHONHASHSEED` diverso, nessun grano generato quando la cache e' a regime. Entrambi gli script usano `PGE_DIR` come `render.py`; il secondo vuole il venv del motore (`../PythonGranularEngine/.venv/bin/python`).

`multivoce/verifica_multivoce.py` verifica con `assert` le affermazioni del capitolo 6 sulle voci, sul motore vero: le liste e la densita' per voce, l'invariante della voce 0, le posizioni indipendenti dal numero di voci attive, le strategie di onset, pointer, pan e pitch con le loro chiavi, il seme per voce, la strategia `range` del pan, gli accordi, la progressione e il riabbinamento `nearest`, la dissolvenza della voce di confine, lo `scatter` e l'esempio `voices`. Usa `PGE_DIR` come gli altri script e vuole il venv del motore; passa sia sulla 9.1.0 sia su `main`.

`grano/verifica_grano.py` verifica con `assert` le affermazioni del capitolo 5 sul grano e sullo stream, sul motore vero: l'ingresso nel loop, la finestra e la banda di posizione, la lettura oltre il bordo del loop, gli intervalli della griglia e il fill factor, i limiti dei parametri, il taglio dei grani a fine stream, le unità della durata, il catalogo delle finestre e le quattro modalità di scelta, le unità di altezza e il detune implicito, il verso di lettura, i guadagni del pan, il gate, le scritture di `deviation_probability` e il jitter implicito. Usa `PGE_DIR` come gli altri script e vuole il venv del motore; passa sia sulla 9.1.0 sia su `main`.

`linguaggio/verifica_linguaggio.py` verifica con `assert` le affermazioni del capitolo 4 sul linguaggio YAML, sul motore vero: i valori predefiniti dello stream minimo e il guadagno del suo rendering, `null` e `0`, `solo` e `mute`, le espressioni matematiche e i loro limiti, la banda dei `_range`, l'inviluppo (forme, interpolazioni, bordi, tempo normalizzato), i numeri dell'esempio del puntatore, ciò che il linguaggio lascia passare, il seme e `rng_group`, lo stream come file. Usa `PGE_DIR` come gli altri script e vuole il venv del motore; la parte su `file:` esiste in `main` e non nella 9.1.0, e si salta da sola se manca.
