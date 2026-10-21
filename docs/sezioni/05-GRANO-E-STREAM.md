# Il grano e lo stream

Il capitolo precedente ha descritto la grammatica con cui si dichiara uno stream. Questo ne descrive il vocabolario: che cosa governa ciascuna parte della dichiarazione e come il motore la traduce in un campo del grano. Il metodo è quello del paper presentato al XXV CIM [@DeMattia2026Cim], che espone PGE per scostamenti: si parte dallo stream minimo del capitolo 4, la trasformazione identica della sorgente, e ci si scosta da esso un parametro alla volta. Per ciascuno si mostra un esempio che lo isola e la MAP che il motore ne ricava. Gli esempi, per non disturbare ciò che isolano, spesso fermano la lettura (`speed_ratio: 0`), così che la MAP mostri una sola variabile. I listati stanno nella cartella `esempi/` del repository della tesina, uno per cartella (`esempi/<nome>/<nome>.yml`), e le MAP si rigenerano da quei file. Le affermazioni sul comportamento del motore sono controllate, una per una, dallo script `esempi/grano/verifica_grano.py`.

L'ordine è quello del paper: dove il grano legge, cioè il puntatore; quando è emesso, cioè la griglia; che cosa è, cioè la sua durata, la finestra, l'altezza, il verso, il volume e la posizione nel campo; e quanto ne decide il caso. La tabella associa a ciascun campo del grano, il tipo descritto nel capitolo 3, la parte del linguaggio che lo determina.

| Campo del grano | Da che cosa dipende |
|-----------------|---------------------------------------------------|
| `pointer_pos` | il blocco `pointer` |
| `onset` | `density` o `fill_factor`, e `distribution` |
| `duration` | `grain.duration` |
| `envelope_table` | `grain.envelope` |
| `pitch_ratio` | il blocco `pitch`; il suo segno porta il verso di lettura, che dipende da `grain.read_direction` e `grain.reverse` |
| `volume`, `pan` | `volume`, in decibel, e `pan`, in gradi |
| `sample_table` | `sample` |

## Il puntatore

Il blocco `pointer` risponde a una domanda: da dove legge questo grano? La risposta è una posizione in secondi nel file, il campo `pointer_pos`, e il motore la compone in quattro passi (`controllers/pointer_controller.py`):

```python
linear_pos = self._calculate_linear_position(elapsed_time)
...
if grain_reverse:
    final_pos += grain_duration
rel = (final_pos - window_start) % window_length
return (window_start + rel) % self._sample_dur_sec
```

Il primo è la posizione lineare: `start` più l'integrale di `speed_ratio`, come ha mostrato il capitolo 4. `start` è un valore fisso, e un inviluppo è un errore che il motore nomina; se manca vale 0, oppure `loop_start`, quando c'è un loop. `speed_ratio` vale 1 per la velocità naturale, 0 per fermare la testina, un numero negativo per percorrere il file all'indietro, e sta fra $-100$ e 100. Il secondo passo applica il loop, se c'è. Il terzo somma alla posizione la deviazione di ciascun grano, scalata sulla lunghezza della finestra attiva (`dev_normalized * window_length`), lo scarto della voce (capitolo 6) e, per un grano letto all'indietro, la sua durata, di cui si dirà nella sezione sul verso. Il quarto è l'operazione modulare: riporta la posizione dentro la finestra e poi dentro il file, perciò la testina che arriva in fondo ricomincia dall'inizio.

### Il loop

Il puntatore può essere confinato in una finestra del file, il *loop*. Lo accende la presenza di `loop_start`; la fine si dichiara in due modi alternativi, con `loop_end`, un istante, o con `loop_dur`, una durata, e se compaiono entrambi vince `loop_end`. Senza `loop_start` il loop non esiste e le altre due chiavi sono ignorate, senza avviso. Se `loop_start` e `loop_end` sono numeri, un `loop_end` minore o uguale a `loop_start` è un errore, perché un loop a cavallo della fine del file si esprime soltanto con `loop_dur`: la finestra riprende dall'inizio. L'inizio e la fine accettano inviluppi, e la finestra può dunque muoversi nel file.

La chiave `loop_unit` fissa l'unità di tutte le posizioni nel file: secondi (il caso predefinito) oppure valori normalizzati fra 0 e 1, scalati sulla durata del campione. Le chiavi che interpreta sono quattro, `start`, `loop_start`, `loop_end` e `loop_dur`, e `start` ne fa parte benché non sia del loop: è una posizione nel file come le altre. L'unità è indipendente dal modo in cui si misura il tempo degli inviluppi: sono due assi diversi, quello del tempo dello stream e quello della posizione nel file.

Come la testina entra nel loop dipende dalla finestra (`_apply_loop`, nel puntatore):

```python
if self._loop_is_dynamic:
    entry_pos = current_loop_start
else:
    check_pos = linear_pos % self._sample_dur_sec
    if current_loop_start <= check_pos < current_loop_end:
        entry_pos = check_pos
```

Una finestra è dinamica quando `loop_start` è un inviluppo, e allora la testina nasce dentro, a `loop_start(0)`. Una finestra statica non cattura nessuno finché non la si incontra: la testina corre libera sul file intero, e solo quando la sua posizione lineare entra nella finestra vi resta. Se `start` è omesso la testina parte dall'inizio della finestra, e l'ingresso è immediato. Dentro il loop la posizione avanza della stessa quantità di quella lineare. Se la finestra non si muove e la posizione ne esce, rientra dal lato opposto. Se la finestra si muove e lascia indietro la testina, questa è riportata al bordo da cui sarebbe uscita: l'inizio, se avanzava, la fine, se tornava indietro.

La deviazione di posizione si dichiara con `offset_range`, la larghezza della banda attorno alla posizione calcolata. L'unità è una frazione della finestra attiva, il file intero se non c'è un loop, ed è per questo che il passo precedente la moltiplica per la lunghezza della finestra: con 0,2 la banda è larga un quinto della finestra. Il valore sta fra 0 e 1, e il modulo riporta dal lato opposto i grani che uscirebbero dalla finestra.

Il confine riguarda però soltanto la partenza del grano. Il grano non porta con sé il loop, perché nessuno dei suoi otto campi lo descrive, e il renderer legge a partire da `pointer_pos` per tutta la durata, avanzando del rapporto di altezza e tornando all'inizio del *file*, non della finestra (`rendering/grain_renderer.py`):

```python
increment = grain.pitch_ratio * file_sr / self.output_sr
...
read_indices = read_indices % n_source
```

Un grano di 0,2 s che parte a 0,55 s in un loop che finisce a 0,6 s legge fino a 0,75 s. Il loop decide da dove si parte, non fin dove si legge.

L'esempio `loop` muove una finestra larga 0,2 volte la durata del file, da 0,1 a 0,6 della durata del file, con la lettura a velocità naturale. Dopo metà dello stream la banda di posizione si apre fino a 0,5.

```yaml
pointer:
  loop_unit: normalized
  speed_ratio: 1.0
  loop_start: [[0, 0.1], [1, 0.6]]
  loop_dur: 0.2
  offset_range: [[0, 0], [0.5, 0], [1, 0.5]]
```

![La finestra di loop, in colore, scorre nel file. Il puntatore la percorre e, raggiunta la fine, ricomincia dall'inizio della finestra; dopo metà dello stream i grani si disperdono dentro la finestra.](docs/images/loop_map.pdf){width=100%}

## La griglia di emissione

Il campo `onset` dipende da una successione di intervalli. L'intervallo fra due onset successivi si chiama *inter-onset time* (IOT), e due parametri lo governano: la densità (`density`), in grani al secondo, che ne fissa il valore medio, $\mathrm{IOT}_{\mathrm{avg}} = 1/\mathit{density}$, e la distribuzione (`distribution`), che stabilisce quanto gli intervalli siano regolari. «Sincrono» e «asincrono» hanno il senso di Roads descritto nel capitolo 2: la regolarità degli intervalli.

In alternativa alla densità si può dichiarare il *fill factor* (`fill_factor`), il prodotto della densità per la durata del grano. Ha la priorità se compare insieme alla densità, perché nello schema dei parametri è il primo del gruppo esclusivo `density_mode`; e se non compare nessuno dei due vale 2. Con il fill factor la densità diventa un quoziente, e il motore lo calcola con la durata del grano che sta per emettere (`strategies/strategie.py`):

```python
fill_factor = self._fill_factor.get_value(elapsed_time)
grain_duration = context['grain_duration']
raw_density = fill_factor / grain_duration
return self._clamp(raw_density)
```

Dopo un grano di durata $d$, il successivo arriva dunque dopo $d/F$, con $F$ il fill factor, qualunque sia $d$: la sovrapposizione resta quella dichiarata anche quando la durata varia da un grano all'altro. È la differenza pratica fra le due chiavi, perché con la densità la sovrapposizione cambia con la durata.

I limiti sono pochi. `density` non ha un tetto e ha un pavimento di 0,01 grani al secondo: l'intervallo medio è il suo inverso, e una densità nulla sarebbe una divisione per zero. Sopra `DENSITY_NOTICE_THRESHOLD`, 4 000 grani al secondo, il motore non taglia ma scrive un avviso nel log, perché a quella densità una durata del grano sbagliata di un ordine di grandezza è un rendering che non finisce. Il `fill_factor` sta fra 0,001 e 50. Un valore dichiarato fuori dai limiti, che sia un numero o il punto di un inviluppo, è un errore alla lettura dello YAML: il motore non lo corregge in silenzio.

La distribuzione è un numero fra 0 e 1, e fuori da questo intervallo è un errore. Con $d$ uguale a `distribution`, l'intervallo è

$$\mathrm{IOT}(d) = (1-d)\,\mathrm{IOT}_{\mathrm{avg}} + d\,\mathcal{U}\!\left(0,\, 2\,\mathrm{IOT}_{\mathrm{avg}}\right), \qquad d \in [0,1]$$

dove $\mathcal{U}$ è il campionamento uniforme. Il codice è la formula (`density_controller.py`):

```python
dist_val = self.distribution_param.get_value(elapsed_time)
if dist_val <= 0.0:
    return avg_iot
else:
    async_iot = self._rng.uniform(0.0, 2.0 * avg_iot)
    return (1.0 - dist_val) * avg_iot + dist_val * async_iot
```

L'espressione è una combinazione convessa. A $d = 0$ ogni intervallo vale $\mathrm{IOT}_{\mathrm{avg}}$: la griglia è metronomica, l'emissione sincrona, e il ramo non consuma numeri casuali. A $d = 1$ l'intervallo è estratto da una distribuzione uniforme fra 0 e il doppio del valore medio: l'emissione è asincrona, ma non è un processo di Poisson, i cui intervalli sarebbero esponenziali: qui sono limitati fra 0 e il doppio della media. I valori intermedi sono il regime quasi-sincrono. Il parametro accetta un inviluppo, quindi lo stream può passare dall'uno all'altro regime nel tempo.

La griglia è un cursore che avanza lungo lo stream (`Stream.generate_grains`). A ogni passo il motore emette un grano al tempo del cursore e lo sposta dell'intervallo calcolato in quell'istante, con la durata di quel grano:

```python
grain_dur_0 = self.grain_duration.get_value(t0)
sync_iot = self._density.calculate_inter_onset(t0, grain_dur_0)
...
voice_cursors[voice_index] += iot
```

Il cursore è uno per voce, e le voci sono il tema del capitolo 6. Il primo grano è sempre a 0, e il cursore si ferma quando supera la durata dello stream. Un grano la cui coda sfora la fine è però scartato, non troncato (`strategies/grain_clip_strategy.py`):

```python
stream_end = stream.onset + stream.duration
limit = stream_end + self.margin
```

La strategia tiene i grani con `g.onset < stream_end` e `g.onset + g.duration <= limit`, e il margine è nullo per impostazione predefinita. Per questo lo stream minimo del capitolo 4 ha 78 grani e non 79: quello nato a 1,95 s finirebbe a 2,0 s, dopo la fine del file, che dura 1,985 s.

L'esempio `distribution` lascia ferma la lettura su un punto del file, per vedere soltanto la griglia di emissione. Lo stream dura 20 secondi. La densità sale da 10 a 200 grani al secondo e ridiscende; la distribuzione resta a zero fino a circa 6 secondi e poi sale a 1, per ritornare a zero.

```yaml
duration: 20
time_mode: normalized
density: {type: cubic, points: [[0, 10], [0.5, 200], [1, 10]]}
pointer:
  speed_ratio: 0.0
  start: 0.5
  loop_unit: normalized
distribution: {type: cubic, points: [[0.3, 0], [.75, 1], [1, 0]]}
```

![Passaggio da emissione sincrona ad asincrona su lettura ferma. Nella prima lente gli onset sono equispaziati, nella seconda irregolari.](docs/images/distribution_map.pdf){width=100%}

La differenza si sente oltre che vedersi. Quando la griglia è sincrona e la densità è alta, l'emissione periodica di grani identici produce uno spettro a righe, spaziate a multipli della densità [@Roads2001Pulsars]. Quando la distribuzione sale verso 1 gli istanti di emissione si irregolarizzano e le righe si smerigliano in una banda.

## Il grano

I campi che restano descrivono il grano in sé: quanto dura, con quale finestra, a quale altezza, in che verso legge, con quale livello e in quale posizione del campo sonoro.

### La durata

La durata è in secondi per impostazione predefinita (0,05 s) e sta fra un campione, circa 21 microsecondi a 48 kHz, e 10 secondi: fuori da quei limiti il motore si ferma con un errore. Con `grain.duration_unit` si può dichiararla in millisecondi o in campioni, alla frequenza di uscita del motore. Il millisecondo è la scala comoda per la granulazione udibile, dove in secondi si scriverebbero soltanto numeri molto piccoli. Le unità sono tre, e la conversione avviene alla lettura del file, per i valori fissi e per gli inviluppi (`core/stream.py`):

```python
GRAIN_DURATION_UNITS = ('seconds', 'samples', 'milliseconds')
```

I millisecondi si moltiplicano per $10^{-3}$, i campioni si dividono per la frequenza di uscita. Con un'unità diversa dai secondi la durata va scritta, perché il valore predefinito resterebbe in secondi e non verrebbe convertito: senza di essa il motore si ferma con un errore che lo dice. Anche `duration_range` si converte, a meno che sia relativa: allora è una frazione della durata corrente, istante per istante, e non ha unità (capitolo 4).

L'esempio `duration`, tratto dal paper, non isola la durata: la fa variare insieme a densità, distribuzione, pan e banda del pan. Serve a vedere che cosa succede quando la durata scende. A metà dello stream passa da 50 a circa 1 millisecondo e risale a 150, e a 1 millisecondo i grani sono clic (capitolo 2). La lente ingrandisce l'istante di durata minima, illeggibile a piena scala.

![Una texture in cui durata del grano, densità, distribuzione e pan variano insieme. Il colore dei grani indica lo scarto di altezza; in basso gli inviluppi dei parametri.](docs/images/duration_map.pdf){width=100%}

### La finestra

La finestra è l'inviluppo di ampiezza che dà forma al grano. Finestrare un grano ne modula l'ampiezza e aggiunge allo spettro bande laterali [@Roads2001]; la scelta della forma è quindi anche una scelta timbrica. Nel linguaggio la finestra si dichiara con la chiave `grain.envelope`, che non va confusa con gli inviluppi dei parametri, trattati nel capitolo 4. Il catalogo ha sedici finestre, e la parola `all` le comprende tutte.

| Nome nello YAML | Forma |
|----------------------------------------------------|------------------------------------------|
| `hanning` (predefinita), `hamming`, `blackman`, `blackman_harris` | somme di coseni |
| `bartlett`, alias `triangle` | triangolare |
| `gaussian`, `kaiser` | gaussiana, Kaiser-Bessel |
| `rectangle` | costante |
| `sinc`, `half_sine` | lobo centrale della sinc, semi-sinusoide |
| `expodec`, `expodec_strong`, `exporise`, `exporise_strong`, `rexpodec`, `rexporise` | tratti esponenziali asimmetrici |

Il catalogo (`controllers/window_registry.py`) è dato e non codice: ogni voce descrive una forma matematica e i suoi coefficienti. Hann e Hamming sono la stessa funzione, una somma di coseni, con coefficienti diversi, e per questo aggiungere una finestra di quella famiglia è una riga di catalogo. Le sei curve asimmetriche sono un solo segmento esponenziale, con valore iniziale, curvatura e valore finale:

```python
'hanning': WindowSpec(
    name='hanning',
    shape=WindowShape.COSINE_SUM,
    coefficients=(0.5, 0.5),
...
'rexpodec': _asymmetric_curve(
    'rexpodec', 1.0, -4.0, 0.0,
```

`rexpodec` parte a 1 e cade subito, con un attacco brusco e un decadimento esponenziale; `expodec` tiene il valore e cade alla fine. `exporise` e `rexporise` sono le loro omologhe lette all'indietro, e le versioni `_strong` hanno una curvatura di 10 invece di 4. I nomi non coincidono con quelli di Roads, come ha detto il capitolo 2.

Le modalità di dichiarazione sono quattro, e il motore sceglie la classe di selezione dalla forma di `grain.envelope` (`controllers/window_selection_strategy.py`).

- **Una finestra sola**, per nome.
- **Una lista di finestre**, fra cui il motore sceglie a caso per ogni grano.
- **Una transizione** da una finestra a un'altra, governata da una curva da 0 a 1: a 0 tutti i grani hanno la prima finestra, a 1 tutti la seconda, e nei valori intermedi la scelta è probabilistica.
- **Un percorso a più stati**, che generalizza la transizione a una sequenza di finestre collocate sull'asse della curva.

La transizione è un sorteggio per grano, e non una dissolvenza fra due finestre:

```python
return self._to if self._rng.random() < blend else self._from
```

Il valore `blend` è la curva valutata al tempo del grano e limitata a $[0, 1]$: a 0,5 metà dei grani ha la prima finestra e metà la seconda. Se la curva manca vale `[[0, 0], [1, 1]]` nel tempo dello stream, quindi in tempo assoluto arriva a 1 dopo un secondo, e di solito si usa con `time_mode: normalized`. La lista, invece, passa dal gate di probabilità della sezione sulla variazione stocastica: a gate chiuso il grano riceve la prima finestra della lista, a gate aperto una a caso, e senza `deviation_probability` il gate è sempre aperto. La transizione e il percorso a stati non lo consultano.

```yaml
grain:
  envelope:
    states: [[0, hanning], [0.5, rexpodec], [1, bartlett]]
    curve: [[0, 0], [1, 1]]
```

Nell'esempio `window` la finestra attraversa tre stati, a densità bassa perché le forme siano distinguibili: Hann, poi `rexpodec`, poi Bartlett.

![Il glifo del grano è la sagoma della sua finestra. Le tre lenti ingrandiscono tre istanti: all'inizio i grani sono finestrati per lo più con Hann, e qualcuno con la finestra esponenziale, perché la scelta è probabilistica; a metà con la finestra esponenziale, con l'attacco brusco e la coda che decade; in chiusura con Bartlett.](docs/images/window_map.pdf){width=100%}

### L'altezza

Il blocco `pitch` governa la trasposizione del grano. Funziona per unità: ogni unità di misura è una chiave del linguaggio, e in un blocco se ne dichiara una sola. Più unità insieme sono un errore, perché non c'è una priorità implicita; lo stesso vale per una chiave sconosciuta, come `semitone` al posto di `semitones`, che qui non viene ignorata, come accade altrove (capitolo 4), ma rifiutata. Senza alcuna unità il valore predefinito è zero semitoni, cioè il rapporto 1; per nessuna trasposizione si omette il blocco o si scrive `pitch: {}`, mentre `pitch:` lasciato vuoto è un errore.

| Chiave | Unità | Divisioni dell'ottava | Limiti |
|--------------------|----------------------------|--------------------|--------------------|
| `semitones` | semitoni | 12 | da $-36$ a 36 |
| `quarter_tone` | quarti di tono | 24 | da $-72$ a 72 |
| `eighth_tone` | ottavi di tono | 48 | da $-144$ a 144 |
| `cents` | cent | 1200 | da $-3600$ a 3600 |
| `edo` con `value` | divisione arbitraria dell'ottava | $N$ | da $-3N$ a $3N$ |
| `ratio` | rapporto diretto | non applicabile | da 0,001 a 8 |

Le unità della famiglia EDO (*equal division of the octave*) sono la stessa classe con un numero di divisioni diverso (`parameters/pitch_unit.py`):

```python
'semitones':    lambda: EdoUnit(12, name='semitones', symbol='st'),
'cents':        lambda: EdoUnit(1200, name='cents', symbol='c'),
'ratio':        lambda: RatioUnit(),
```

e la conversione nel rapporto di trasposizione è una riga, $2^{v/N}$ con $v$ il valore e $N$ il numero di divisioni:

```python
return 2 ** (value / self.divisions)
```

`ratio` è invece un moltiplicatore diretto. L'unità `edo` apre a scale arbitrarie: `edo: 31` con `value: 18` dichiara diciotto gradi di una scala a trentuno divisioni. I limiti delle unità EDO sono tre ottave, cioè $\pm 3N$ (`bound = 3.0 * self.divisions`).

Come per ogni parametro, il valore può essere un inviluppo, e la banda di variazione `range` è espressa nella stessa unità, con una larghezza massima di tre ottave per le unità EDO e di 2 per `ratio`. Nelle unità EDO la variazione è quantizzata: si estrae un grado intero della griglia, e con `range: 5` in semitoni i valori possibili sono $-2$, $-1$, 0, 1 e 2. Con `ratio` la variazione è continua.

L'esempio `pitch` lascia ferma la lettura e porta la trasposizione a gradini: 0, 7, $-5$ e 12 semitoni.

```yaml
pitch:
  semitones: {type: step, points: [[0, 0], [0.25, 7], [0.5, -5], [0.75, 12]]}
```

![La trasposizione a gradini su lettura ferma. Il colore dei grani codifica l'altezza, in cent rispetto al suono originale; in basso l'inviluppo dei semitoni.](docs/images/pitch_map.pdf){width=100%}

### Il verso di lettura

Il segno del rapporto di altezza è il verso con cui il grano legge il materiale. Tre grandezze diverse lo riguardano e vanno tenute distinte.

| Grandezza | Che cosa governa | Valori |
|------------------------------|-------------------------------------|--------------------------|
| `pointer.speed_ratio` | velocità e verso con cui la testina percorre il file | negativo: all'indietro |
| `grain.read_direction` | verso con cui il singolo grano legge il materiale | $-1$ indietro, $+1$ avanti |
| blocco `pitch` | altezza percepita | sempre positivo, per costruzione |

Il motore le compone in `Stream._calculate_grain_reverse`:

```python
if self.read_direction is not None:
    return self.read_direction.get_value(elapsed_time) < 0
if self.grain_reverse_mode == 'auto':
    is_reverse_base = (self._pointer.get_speed(elapsed_time) < 0)
else:
    is_reverse_base = True
```

Se `read_direction` è dichiarata vince il suo segno. Altrimenti il verso del grano segue quello della testina, a meno che sia presente `grain.reverse`: la chiave si scrive vuota, e forza l'inversione per tutti i grani. Un valore, come `reverse: true`, è un errore. Lo è anche dichiarare `read_direction` insieme a `reverse`, perché le due chiavi governano la stessa grandezza con semantiche opposte, e sceglierne una in silenzio nasconderebbe l'errore invece di segnalarlo. `read_direction` accetta soltanto $-1$ e $+1$, e un inviluppo ha l'interpolazione a gradini, imposta, perché il verso non ha valori intermedi.

Un grano letto all'indietro ha il rapporto negato (`pitch_ratio *= -1`, nel controller dell'altezza), e la sua posizione di lettura è spostata in avanti della sua durata (`final_pos += grain_duration`, nel puntatore). A rapporto 1 legge così lo stesso segmento del file che avrebbe letto in avanti, ma dalla fine verso l'inizio. Con la testina all'indietro e `read_direction: 1` i grani leggono in avanti, e viceversa.

L'esempio `read_direction` tiene costante la velocità della testina, che avanza nel file per tutta la durata dello stream, e inverte il verso dei grani fra 4 e 6 secondi.

```yaml
grain:
  duration: 0.12
  read_direction: [[0, 1], [0.5, -1], [0.75, 1]]
pointer:
  speed_ratio: 0.25
```

![La testina avanza sempre, ma fra 4 e 6 secondi i grani leggono all'indietro: la testa del grano si capovolge. Le lenti mostrano un grano in lettura diretta e uno in lettura inversa.](docs/images/read_direction_map.pdf){width=100%}

### Volume e posizione nel campo

Il `volume` è in decibel: 0 dB è il livello del campione, e i limiti vanno da $-120$ a $+12$ dB. Il renderer lo converte in ampiezza, $A = 10^{v/20}$ (capitolo 7).

Il `pan` è un angolo in gradi, da $-3600$ a 3600, perché il pan può ruotare su più giri. L'angolo muove il grano lungo una circonferenza unitaria in codifica Mid-Side, la matrice di Blumlein [@Blumlein1931]. Mid e side sono due microfoni a figura otto ortogonali, le proiezioni coseno e seno del grano lungo la circonferenza [@Gerzon1975]; sinistra e destra sono la stessa coppia ruotata di 45 gradi, e non l'unico esito possibile. Gli angoli si leggono così, con i guadagni sui due canali:

| Pan (gradi) | Sinistra | Destra | Posizione |
|-------------|----------|---------|----------------------------------|
| 0 | 0,707 | 0,707 | al centro |
| 45 | 1 | 0 | tutto a sinistra |
| $-45$ | 0 | 1 | tutto a destra |
| 90 | 0,707 | $-0{,}707$ | in controfase |
| 180 | $-0{,}707$ | $-0{,}707$ | al centro, a polarità invertita |

La potenza resta costante a ogni angolo, $L^2 + R^2 = 1$, come dice il capitolo 7. Gli angoli positivi vanno a sinistra, e il grano si muove fra le due casse fra $-45$ e $+45$ gradi: oltre quei valori prevale la componente side, e a $\pm 90$ gradi le due uscite sono in controfase, e un ascolto in mono le cancella.

Il grano porta un angolo, non una coppia di guadagni, e la matrice appartiene al renderer. I tre renderer di PGE usano la stessa matrice stereo, e con un'altra matrice lo stesso angolo potrebbe pilotare un numero qualsiasi di altoparlanti: la generalità sta nel dato e non ancora nei consumatori, come dice il capitolo 3. La posizione nel campo sonoro è, in ogni caso, un attributo del singolo grano, parte della costruzione dello strumento, e non un effetto di spazializzazione aggiunto in fondo alla catena.

## La variazione stocastica

I parametri di un grano non sono tutti decisi dal compositore uno per uno: sarebbe la specifica grano per grano che l'introduzione ha indicato come intrattabile. La parte del caso è dichiarata a due livelli. Ogni parametro ha una traiettoria centrale, un inviluppo, e una banda di deviazione attorno a quella traiettoria, `_range`, da cui si estrae un valore diverso per ogni grano. È la maschera di tendenza del capitolo 2, che il capitolo 4 ha scritto come un valore centrale e una larghezza. Con $c(\tau)$ la traiettoria centrale, $\rho(\tau)$ la larghezza della banda e $\xi_n$ un valore uniforme fra $-1/2$ e $1/2$, il parametro del grano $n$ al tempo normalizzato $\tau_n$ è

$$v_n = c(\tau_n) + \xi_n\,\rho(\tau_n), \qquad \xi_n \sim \mathcal{U}\!\left(-\tfrac{1}{2}, \tfrac{1}{2}\right)$$

I parametri che hanno una banda sono cinque, e la tabella del jitter più avanti ne elenca le chiavi. Il sistema aggiunge un terzo livello: la probabilità, variabile nel tempo, che la deviazione si applichi. Un *gate* probabilistico, una porta che si apre o si chiude, decide grano per grano se il grano segue la traiettoria o subisce la deviazione:

$$v_n = c(\tau_n) + g_n\,\xi_n\,\rho(\tau_n), \qquad g_n \sim \mathrm{Bernoulli}\!\big(p(\tau_n)\big)$$

dove $p(\tau)$ è la probabilità, anch'essa un inviluppo: nella formula è un numero fra 0 e 1, nello YAML si scrive da 0 a 100. Il metodo `Parameter.get_value`, descritto nel capitolo 3, è questa espressione: se il gate è chiuso restituisce il valore centrale, se è aperto lo fa passare dalla banda. La differenza rispetto alla prima formula è il fattore $g_n$, che rende l'ampiezza della deviazione, $\rho$, e la sua probabilità, $p$, due dimensioni di controllo indipendenti. La chiave che le dichiara è `deviation_probability`.

Quando la chiave manca, il gate è sempre aperto per i parametri che hanno un `_range`: l'espressione si riduce alla prima, ed è la maschera di tendenza semplice. Un parametro senza `_range` non devia mai. Lo dice una riga del motore (`parameters/gate_factory.py`):

```python
return AlwaysGate() if has_explicit_range else NeverGate()
```

Il gate è una classe con un solo metodo, `should_apply(time)`, e ne esistono quattro: `NeverGate`, `AlwaysGate`, `RandomGate`, con una probabilità fissa, ed `EnvelopeGate`, con una probabilità che varia nel tempo (`shared/probability_gate.py`):

```python
return self._rng.uniform(0, 100) < self._probability
```

Nelle fonti consultate non si trova un precedente diretto del gate come asse dichiarabile e componibile nel tempo. Il più vicino è nell'ICMS, dove alcune trasformazioni del grano (lettura retrograda, inversione di fase, ripetizione) si applicano a circa metà dei grani per decisione di un generatore casuale [@DiScipioTisato1993cim]: la probabilità è però fissa e non dichiarata, e governa interruttori discreti, non l'applicazione di una maschera a un parametro continuo. Per forma è più vicina l'*intermittency* di EmissionControl2, un gate per grano dichiarabile e modulabile con continuità [@Roads2021]; ma decide se il grano viene emesso e agisce quindi sulla densità. Nel linguaggio qui descritto il grano resta, e il gate decide se applicargli la deviazione.

L'indipendenza dei due assi si vede in due stream che condividono la stessa traiettoria, una lettura ferma, e la stessa ampiezza massima di deviazione (esempio `deviation`). Nel primo cresce l'ampiezza della deviazione, nel secondo la probabilità; la differenza sta in due righe.

```yaml
# a: cresce l'ampiezza; deviation_probability è assente
pointer:
  offset_range: [[0, 0.0], [1, 0.35]]

# b: l'ampiezza è fissa e cresce la probabilità
deviation_probability:
  pointer: [[0, 0], [1, 100]]
pointer:
  offset_range: 0.35
```

![Due modi di aprire la deviazione, a parità di traiettoria e di ampiezza massima. Pannello superiore: l'ampiezza cresce da 0 a 0,35 con il gate sempre aperto, e i grani riempiono uniformemente uno spazio di lettura che si allarga a cuneo. Pannello inferiore: l'ampiezza è costante e cresce la probabilità da 0 a 100%; la linea si trasforma in nuvola, passando da grani fedeli a grani devianti.](docs/images/deviation_map.pdf){width=100%}

### Come si dichiara la probabilità

`deviation_probability` accetta più forme. Un numero da 0 a 100 vale per tutti i parametri; un inviluppo lo fa variare nel tempo; un dizionario assegna una probabilità per parametro, con le chiavi `volume`, `pan`, `duration`, `pitch`, `pointer`, `reverse`, `read_direction` e, per la lista di finestre, `pc_rand_envelope`, e ciascuna può essere a sua volta un inviluppo.

Vale una regola che conviene conoscere. In modalità per parametro, un parametro assente dal dizionario non riceve probabilità: se ha un `_range` dichiarato lo applica sempre, a tutti i grani, e se non ce l'ha resta fermo. Nel dizionario si dichiarano quindi soltanto i parametri di cui si vuole *ridurre* la probabilità. Nella modalità globale invece un'unica probabilità vale per tutti i parametri, anche per quelli senza `_range`.

```yaml
# solo il volume è ridotto al 30%; gli altri parametri con un _range lo applicano sempre
deviation_probability:
  volume: 30
```

Resta un caso che ha sorpreso più volte e che il progetto ha fissato con un test. Esistono cinque modi di scrivere la chiave senza assegnarle un valore, e quattro danno lo stesso risultato: nessun gate stocastico, cioè la regola di sopra. Lo danno l'omissione della chiave, `false`, `{}` e un parametro dichiarato `null`: i parametri senza `_range` non deviano, e quelli con un `_range` lo applicano a ogni grano. Fa eccezione la chiave scritta e lasciata vuota, `deviation_probability:`, che in YAML vale `null` e attiva la modalità implicita: una probabilità dell'1% per ogni parametro, con un'ampiezza predefinita, anche per i parametri con un `_range`, che da quel momento si applica soltanto all'1% dei grani. Su uno stream di 79 grani con `read_direction` dichiarata e nessun `_range`, la chiave vuota ne ribalta in media 0,8, cioè l'1%; le altre quattro scritture nessuno. Quella che più somiglia a «non voglio deviazione» fa dunque l'opposto: per disattivare si scrive `false` o si omette la chiave.

### Il jitter implicito

Se si dichiara una probabilità senza un `_range` esplicito, il motore applica una deviazione predefinita, il *jitter* implicito, parola inglese che indica un piccolo tremolio attorno al valore. L'ampiezza dipende dal parametro, e la tabella la dà come semi-ampiezza, con a fianco la chiave della banda e la larghezza massima che un `_range` dichiarato può avere.

| Parametro | Chiave della banda | Jitter implicito | Larghezza massima |
|------------|--------------------------------|------------------------|----------------------|
| volume | `volume_range` | ±1,5 dB | 24 dB |
| pan | `pan_range` | ±15 gradi | 360 gradi |
| durata | `grain.duration_range` | ±5 ms | 1 s, o 1 se relativa |
| lettura | `pointer.offset_range` | ±2,5% della finestra di lettura | 1, la finestra intera |
| altezza | `pitch.range` | ±12 cent, o ±0,0025 con `ratio` | tre ottave, o 2 con `ratio` |
| verso | | inversione discreta | |

Quella microvariazione è la decorrelazione di cui parla Vaggione, che rende una massa granulare più organica e meno meccanica [@Vaggione2002]. Per l'altezza il detune implicito è continuo e si applica dopo la quantizzazione sulla griglia dell'unità scelta; con un `range` dichiarato, anche nullo, non si applica e vale la variazione quantizzata dichiarata. Una probabilità globale apre il gate anche sul verso: con il 100% tutti i grani leggono nel verso opposto a quello di base, con il 50% la metà.

Nell'esempio `probability` la sola `deviation_probability` sale a gradini da 0 a 100%, senza alcun `_range` dichiarato.

```yaml
grain:
  duration: 0.02
deviation_probability: {points: [[0, 0], [.2, 25], [.4, 50], [.6, 75], [.8, 100]], type: step}
```

![La sola probabilità sale a gradini. Nel primo tratto i grani sono allineati sulla traiettoria; a ogni gradino una quota maggiore se ne discosta, per effetto del jitter implicito e dell'inversione del verso (il colore dei grani indica lo scarto di altezza). Nella legenda, la percentuale accanto al nome di un parametro è la probabilità che la deviazione sia applicata, non la sua ampiezza.](docs/images/probability_map.pdf){width=100%}
