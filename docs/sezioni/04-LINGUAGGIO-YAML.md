# Il linguaggio di descrizione degli stream

Il capitolo precedente ha collocato il linguaggio nell'architettura: è l'ingresso della pipeline, e il motore lo traduce in una lista di grani. Questo ne descrive la grammatica. Dice che forma ha un documento, che forme può assumere un valore e quali due proprietà valgono per il documento intero, il seme e l'importazione di stream da altri file. Il vocabolario, cioè che cosa governa ciascuna chiave, è l'argomento dei capitoli 5 e 6. Il capitolo segue la costruzione: lo stream e i suoi valori predefiniti (sezione 4.1); le forme di un valore, in ordine di ricchezza, cioè l'espressione (4.2), l'envelope (4.3) e la banda di variazione (4.4); poi il seme (4.5) e lo stream come file (4.6). L'ultima sezione raccoglie ciò che il linguaggio lascia passare senza avvertire.

Non è un manuale: la sintassi completa è nel riferimento del progetto (`docs/reference/yaml.md`). Gli esempi vengono dal paper presentato al XXV CIM [@DeMattia2026Cim] e si rieseguono dalla cartella `esempi/`; le affermazioni sul comportamento del motore sono controllate, una per una, dallo script `esempi/linguaggio/verifica_linguaggio.py`.

La scelta di YAML ha tre ragioni e un costo. Le ragioni sono quelle del progetto. Un file di testo si versiona con *git* e può essere letto e discusso con un modello linguistico. Il motore, esposto come libreria, può essere pilotato da un livello compositivo più alto che generi YAML invece di scriverlo a mano, come fa il laboratorio del capitolo 10. E la specifica dichiara soltanto la generazione dei grani, separata dal rendering. Il costo è che la sintassi è permissiva: il motore ricava i tipi dal testo, e ciò che non riconosce lo lascia passare. Il capitolo lo dichiara dove si presenta.

## Lo stream come unità compositiva

Un brano è un file YAML. Al livello più alto il motore legge due chiavi: `streams`, l'elenco degli stream, e, facoltativamente, `seed`, il seme dei processi casuali. Ogni altra chiave di primo livello, come il `composition` degli esempi o un `bpm`, il motore la ignora. Ogni stream è un dizionario di coppie chiave-valore, annidabili. A livello dello stream stanno la densità (`density` o `fill_factor`), `distribution`, `volume` e `pan`; gli altri parametri sono raggruppati in blocchi che corrispondono ai concetti dei capitoli seguenti: `grain` per il grano, `pointer` per la posizione di lettura, `pitch` per la trasposizione, `voices` per la molteplicità delle voci.

### Le condizioni minime di esistenza

Uno stream esiste con due soli parametri.

```yaml
streams:
  - stream_id: esempio1
    sample: voice.wav
```

`stream_id` è il nome dello stream, e `sample` è il file audio da granulare. Se ne manca uno il motore si ferma con un `MissingFieldError` che lo nomina. Tutto il resto è facoltativo, perché ogni chiave ha un valore predefinito, e i predefiniti sono scelti perché questa configurazione sia la trasformazione identica della sorgente.

| Chiave | Predefinito | Effetto |
|--------------------------|----------------|------------------------------------------|
| `grain.duration` | 0,05 s | grani di 50 ms |
| `fill_factor` | 2 | densità di 40 grani al secondo: un grano ogni 25 ms |
| `grain.envelope` | `hanning` | finestra di Hann |
| `volume`, `pan` | 0 dB, 0 gradi | grano centrale a guadagno 1 |
| `pointer.speed_ratio` | 1 | la lettura avanza alla velocità del tempo dello stream |
| `pitch` | rapporto 1 | nessuna trasposizione |

Con questi valori l'identità è una questione di aritmetica. Due finestre di Hann sfalsate di metà della loro durata sommano a 1: sul file di esempio, a 44,1 kHz, la somma delle finestre dei 78 grani sta fra 0,9986 e 1, salvo ai due estremi, dove copre l'istante un grano solo. Ogni grano legge il file nel punto in cui è nato, perché la posizione di lettura coincide con l'istante. La somma dei grani ricostruisce dunque la sorgente. È l'identità della lista dei grani, e non del file di uscita: il rendering NumPy a 44,1 kHz restituisce la sorgente con un guadagno di 0,70, perché il pan a potenza costante del capitolo 7 porta un grano centrale a $1/\sqrt{2}$ in ciascun canale, e con un residuo di $-21$ dB, che deriva dall'interpolazione lineare delle posizioni di lettura a mezzo campione.

La figura seguente mostra la MAP di questo caso. Ogni grano è un poligono posizionato sul tempo dello stream (asse orizzontale) e sulla posizione di lettura nel file (asse verticale). A sinistra, sullo stesso asse verticale, è disegnata la forma d'onda della sorgente. La diagonale è l'identità. La lente ingrandisce tre grani contigui, in cui si vedono il profilo della finestra e la sovrapposizione fra grani adiacenti.

![MAP dello stream minimo: il puntatore percorre il file una sola volta, alla velocità del tempo dello stream.](docs/images/identity_map.pdf){width=100%}

### Una notazione differenziale

Ciò che non è scritto è una dichiarazione implicita, data dal valore predefinito del parametro. Il caso più visibile è la coppia `onset` e `duration`.

| Chiave | Se assente | Se dichiarata |
|--------|------------|---------------|
| `onset` | lo stream parte a 0 s, l'origine della timeline | lo stream parte all'istante indicato, in secondi assoluti |
| `duration` | lo stream dura quanto il campione | lo stream dura il tempo indicato, anche più o meno del file |

Il motore distingue «assente» da «dichiarata» con un predicato che guarda `None` e non la verità del valore (`core/stream_config.py`):

```python
def stream_duration_is_implicit(yaml_data: dict) -> bool:
    return yaml_data.get('duration') is None

def resolve_stream_duration(yaml_data: dict, sample_dur_sec: float) -> float:
    if stream_duration_is_implicit(yaml_data):
        return sample_dur_sec
    return yaml_data['duration']
```

`onset` ha il gemello `resolve_stream_onset`, con la costante 0.0 al posto della durata del file. Ne seguono due conseguenze. `duration: null` vale come chiave assente, e `duration: 0` no: è una dichiarazione, degenere, e produce uno stream senza grani.

La scelta ha una ragione espressa nel progetto: a riposo lo stream risintetizza il campione, e l'unica durata non arbitraria è quella del file. Ogni altro valore è una decisione compositiva, e le decisioni compositive devono essere esplicite. Zero non è «niente», è l'origine: uno stream senza `onset` ha una posizione neutra, non indeterminata. Il costo di questa comodità è dichiarato. Un `onset` cancellato per errore non produce un errore: lo stream si impila silenziosamente a zero. Per `duration` vale lo stesso.

Due chiavi governano la presenza dello stream nel render: `mute` lo esclude, `solo` esclude tutti gli altri. La regola è una funzione di poche righe (`filter_solo_mute`, in `engine/solo_mute.py`) e conta la presenza della chiave, non il suo valore:

```python
solo_mode = any('solo' in s for s in stream_data_list)

if solo_mode:
    filtered = [s for s in stream_data_list if 'solo' in s]
else:
    filtered = [s for s in stream_data_list if 'mute' not in s]
```

Perciò `mute: false` muta lo stream, e `solo: false` attiva la modalità solo: per togliere un flag si cancella la riga. Se più stream dichiarano `solo` suonano tutti, e `solo` prevale su `mute`.

## Espressioni matematiche

Un valore racchiuso tra parentesi è un'espressione.

```yaml
grain:
  duration: (1/20)
pitch:
  ratio: (2**(7/12))        # il rapporto di sette semitoni
```

Il motore la valuta alla lettura del file, prima che il resto del programma veda il dato, e il risultato è un numero fisso: l'espressione non è modulabile nel tempo, e a questo serve l'envelope. La valutazione è una sostituzione di testo applicata a ogni valore stringa del documento (`Generator._eval_math_expressions`):

```python
pattern = r'\(([a-zA-Z0-9+\-*/.() ]+)\)'
...
safe_dict = {
    'abs': abs,
    'int': int,
    'float': float,
    'min': min,
    'max': max,
    'pow': pow,
    'pi': math.pi,
    'e': math.e
}
...
result = eval(expr, {"__builtins__": {}}, safe_dict)
```

Un frammento fra parentesi fatto soltanto di cifre, lettere, operatori, punto e spazi si calcola con `eval` in un ambiente senza i `builtins` di Python e con i soli nomi di `safe_dict`; il risultato prende il posto del frammento, e se l'intera stringa diventa un numero il valore è un numero. Il meccanismo ha tre limiti. Il pattern non contiene la virgola, quindi `min`, `max` e `pow`, che vogliono due argomenti, sono nella lista ma non si possono chiamare: restano `abs`, `int`, `float`, le costanti `pi` ed `e` e gli operatori `+ - * / // **`, non il resto della divisione. Un'espressione che non si calcola, poi, non è un errore: il motore stampa un avviso e lascia la stringa com'è. Infine la sostituzione non distingue un valore numerico da un nome, e un file chiamato `voice (1).wav` diventa `voice 1.wav`.

## Envelope: forme, interpolazioni e time mode

Un *envelope* è una funzione del tempo definita a tratti su punti di controllo (*breakpoint*), ciascuno una coppia `[tempo, valore]`. Può comparire al posto di qualunque valore numerico, ed è così che i parametri di uno stream variano nel tempo. Il motore riconosce un inviluppo dalla forma del dato (`Envelope.is_envelope_like`): una lista che contiene almeno una coppia, un dizionario con la chiave `points`, o uno dei formati compatti descritti sotto.

### Le forme di scrittura

La forma più comune è la lista di coppie `[tempo, valore]`.

```yaml
density: [[0, 5], [10, 40], [30, 5]]
```

I punti vengono ordinati automaticamente per tempo crescente. Quando serve scegliere il tipo di interpolazione, o il modo in cui si misura il tempo, si usa la forma a dizionario.

```yaml
density:
  type: cubic
  points: [[0, 5], [10, 40], [30, 5]]
```

Il tipo di interpolazione si può anche assegnare a un singolo punto, e vale per il segmento che va da quel punto al successivo.

```yaml
density: [[0, 5, 'cubic'], [0.3, 30, 'linear'], [0.7, 10, 'step'], [1, 5]]
```

Per i pattern che si ripetono esiste un formato compatto, che genera più cicli di una forma definita in percentuale.

```yaml
grain:
  duration: [[[0, 0.01], [100, 0.2]], 30, 4]
```

Il primo elemento è il pattern di un ciclo, con le ascisse espresse da 0 a 100. Il secondo è il tempo assoluto finale del blocco, il terzo il numero di ripetizioni. In questo esempio la durata del grano sale da 0,01 a 0,2 secondi quattro volte, in cicli di 7,5 secondi, fino al secondo 30; fra un ciclo e il successivo il motore inserisce un salto di un microsecondo, perché due punti non cadano sullo stesso istante. Il formato compatto accetta anche l'interpolazione, una distribuzione non uniforme delle durate dei cicli e l'opzione di chiudere il ciclo, e può essere mescolato con punti ordinari nella stessa lista.

### Le interpolazioni

Le interpolazioni sono tre.

- **Lineare** (predefinita): i valori fra due punti sono su una retta. L'integrale è l'area di un trapezio.
- **Cubica**: curva di Hermite con tangenti scelte perché la curva sia monotona, secondo il metodo che il codice attribuisce a Fritsch e Carlson. In un punto interno la tangente è la media armonica delle pendenze dei due segmenti adiacenti, e vale zero se le pendenze cambiano segno o una è nulla; per questo, fra due punti, la curva non esce dall'intervallo dei loro valori, e nel profilo `[0, 5], [10, 40], [30, 5]` il massimo resta 40. Con due soli punti l'unica informazione è la pendenza, e assegnarla a entrambe le tangenti darebbe una retta: le tangenti sono forzate a zero e la curva diventa una S simmetrica, $v_0 + (v_1 - v_0)(3s^2 - 2s^3)$. La cubica è adatta ad attacchi e rilasci morbidi e a traiettorie dove una derivata seconda continua è udibile. L'integrale è calcolato con la regola di Simpson su dieci sotto-intervalli per segmento.
- **A gradini** (*step*): il valore di un segmento è quello del punto di sinistra fino al punto successivo. Serve ai cambi discontinui e ai parametri che assumono valori interi, come il numero di voci.

Per la cubica il calcolo delle tangenti, nel modulo `envelope.py`, è questo:

```python
if n == 2:
    return [0.0, 0.0]
...
if d_left * d_right <= 0:
    tangents[i] = 0.0
else:
    tangents[i] = 2.0 / (1.0 / d_left + 1.0 / d_right)
```

### Il tempo: assoluto e normalizzato

Il tempo di un inviluppo si misura in due modi. Con `time_mode: absolute` (il caso predefinito) i punti sono secondi: `[10, 40]` significa «al secondo 10 il valore è 40», qualunque sia la durata dello stream. Con `time_mode: normalized` l'ascissa va da 0 a 1 ed è moltiplicata per la durata dello stream, alla costruzione dell'inviluppo (`create_scaled_envelope`). Un envelope scritto in forma normalizzata mantiene la propria forma se si cambia la durata del brano. `time_mode` si dichiara per tutto lo stream; per un solo inviluppo si scrive, nel suo dizionario, la chiave `time_unit`. Un `time_mode` scritto nel dizionario di un parametro come `density` non ha effetto, e il motore non avverte.

La normalizzazione riguarda l'asse del tempo degli inviluppi. La posizione dello stream nella timeline, `onset`, è sempre in secondi assoluti.

### Il comportamento ai bordi

Fuori dall'intervallo coperto dai punti, l'inviluppo mantiene il valore del punto più vicino: prima del primo punto vale il primo valore, dopo l'ultimo vale l'ultimo. Lo dice il codice del segmento (`NormalSegment.evaluate`), e vale anche per l'integrale:

```python
if t < self.start_time:
    return self.breakpoints[0][1]

if t > self.end_time:
    return self.breakpoints[-1][1]

return self.strategy.evaluate(t, self.breakpoints, **self.context)
```

Uno stream più lungo del suo inviluppo non produce quindi errori. È una scelta voluta, e si legge nella figura seguente.

### Un esempio: la posizione di lettura

L'esempio mostra un inviluppo che governa `pointer.speed_ratio`, il rapporto tra la velocità con cui il puntatore percorre il file e la velocità del tempo dello stream.

```yaml
streams:
  - stream_id: pointer_freeze
    sample: voice.wav
    duration: 7.0
    time_mode: normalized
    pointer:
      speed_ratio:
        - [0.1, 1.0]
        - [0.15, 2.6]
        - [0.3, -0.3]
        - [0.5, 0.0]
```

Con `duration: 7.0` e tempo normalizzato i punti cadono a 0,7, 1,05, 2,1 e 3,5 secondi. Il campione dura 1,985 secondi, circa due, ma lo stream ne dura sette.

![MAP dell'esempio. In basso l'inviluppo `speed_ratio`, con i valori annotati sui punti; in alto i grani.](docs/images/pointer_map.pdf){width=100%}

La figura mostra che i grani non ricalcano la curva di `speed_ratio`: ne seguono l'*accumulo*. La posizione di lettura è l'integrale della velocità istantanea, e il puntatore chiede all'envelope la seconda delle sue due operazioni, `integrate` invece di `evaluate` (`PointerController._calculate_linear_position`):

```python
internal_val = self.speed_ratio.value
if isinstance(internal_val, Envelope):
    sample_position = internal_val.integrate(0, elapsed_time)
else:
    sample_position = elapsed_time * float(internal_val)
return self.start + sample_position
```

L'indice di lettura è poi preso modulo la durata del file. Con la velocità che sale a 2,6 il puntatore esaurisce il buffer a 1,35 secondi e rientra da zero: il salto che si vede nella MAP è una discontinuità di posizione, non il ritorno a zero di una fase che continua ad accumularsi. Fra circa 2 e 3,5 secondi la velocità è negativa e il puntatore percorre il file all'indietro. Il verso di lettura interno ai grani si inverte con lui, perché per impostazione predefinita un grano è invertito quando la testina va indietro (`Stream._calculate_grain_reverse`, nel ramo `auto` di `grain.reverse`):

```python
if self.grain_reverse_mode == 'auto':
    is_reverse_base = (self._pointer.get_speed(elapsed_time) < 0)
```

Dopo l'ultimo punto la velocità resta a zero, per il comportamento ai bordi, e da 3,5 secondi tutti i grani leggono lo stesso punto del file, a 0,342 secondi: la posizione si congela.

## La banda di variazione

Cinque parametri dello stream hanno una banda di variazione, dichiarata da una chiave con `range` nel nome: `volume_range`, `pan_range`, `grain.duration_range`, `pointer.offset_range` e `pitch.range`. La banda sta attorno al valore base, e per ogni grano il motore estrae il valore del parametro dentro di essa.

```yaml
grain:
  duration: 0.05
  duration_range: 0.01
```

Il linguaggio distingue quattro concetti, ognuno con la propria chiave, perché tenerli distinti evita ambiguità. La *larghezza* della banda è il valore stesso di `_range`: è sempre la larghezza, mai una semi-ampiezza e mai una deviazione standard. L'*unità* in cui è misurata la larghezza è assoluta, nell'unità del parametro, oppure relativa al valore base. Si sceglie con `grain.duration_range_unit`, e solo per la durata del grano, l'unico parametro la cui base spazia per costruzione su più ordini di grandezza, da un campione a dieci secondi, e per cui una banda assoluta cambierebbe carattere da sola lungo un envelope. La *forma* (`distribution_mode`) dice come la banda viene riempita: uniforme oppure gaussiana. L'*ancora* (`range_anchor`) dice dove cade il valore base nella banda: al centro oppure al minimo. Forma e ancora sono chiavi dello stream e valgono per tutte le sue bande.

Con valore base 300 e larghezza 200 le combinazioni danno questi risultati.

| Forma | Ancora | Banda | Dove si addensano i valori |
|-------|--------|-------|----------------------------|
| uniforme | centro | da 200 a 400 | in modo piatto |
| uniforme | minimo | da 300 a 500 | in modo piatto |
| gaussiana | centro | da 200 a 400 | attorno a 300 |
| gaussiana | minimo | da 300 a 500 | attorno a 400 |

Le due forme stanno in due classi (`shared/distribution_strategy.py`). L'ancora sceglie la banda, e la forma ne estrae il valore. Per la distribuzione uniforme con ancora al centro l'estrazione è la riga che il capitolo 5 scrive come formula, $v = c + \xi\rho$ con $\xi$ fra $-1/2$ e $1/2$:

```python
def _band(self, center: float, spread: float) -> Tuple[float, float]:
    if self._anchor == ANCHOR_MIN:
        return (center, center + spread)
    half_spread = spread / 2
    return (center - half_spread, center + half_spread)
```

```python
return center + self._rng.uniform(-0.5, 0.5) * spread
```

La gaussiana è troncata:

```python
lo, hi = self._band(center, spread)
mu = (lo + hi) / 2.0
sigma = spread / self.SIGMA_DIVISOR

return min(max(self._rng.gauss(mu, sigma), lo), hi)
```

`SIGMA_DIVISOR` vale 6, dunque la deviazione standard è un sesto della larghezza e i bordi della banda cadono a tre sigma dalla media. La piccola coda che li supererebbe, circa lo 0,27% dei valori, è appiattita sull'estremo. Nessun valore esce dalla banda dichiarata.

Centro e larghezza sono due valori come tutti gli altri, e ciascuno può essere un numero o un envelope. Quando lo sono entrambi la banda è un'area che si apre e si chiude nel tempo: è la maschera di tendenza, nella forma in cui la descrive Truax [@Truax1988, p. 17], scritta in testo.

```yaml
grain:
  duration: [[0, 0.02], [10, 0.2]]
  duration_range: [[0, 0.0], [10, 0.1]]
```

Qui la durata del grano sale da 20 a 200 millisecondi in dieci secondi e la banda si apre da zero a 100 millisecondi: ogni grano cade dentro una semi-banda che cresce di 5 millisecondi per secondo. La sezione 3.3 descrive come `Parameter.get_value` compone centro, banda, gate di probabilità e limite; il capitolo 5 dice come la probabilità che la deviazione si applichi sia un asse indipendente dall'ampiezza.

## Riproducibilità: seme e gruppi

Il seme è una chiave del livello più alto del file.

```yaml
seed: 2026
streams:
  - stream_id: s1
    sample: voice.wav
```

Se è dichiarato, lo stesso YAML produce la stessa lista di grani a ogni esecuzione, anche in processi diversi, e quindi la stessa realizzazione. Se è assente, il motore genera un seme di sessione dall'istante di avvio e lo riporta a schermo: il render non è riproducibile in anticipo, ma resta ricostruibile a posteriori, perché aggiungendo `seed: N` al file si riottiene lo stesso risultato. Anche `seed: 0` è un valore valido, distinto dall'assenza della chiave.

Il seme non alimenta un generatore globale. Ogni sito stocastico ha il proprio generatore, derivato dal seme, dall'identità dello stream e dal nome del componente (sezione 3.7). Il risultato più utile per chi compone è l'isolamento. Mettere uno stream in `solo` fa ascoltare esattamente ciò che suona nel mix, perché i grani degli altri stream non vengono toccati. Modificare uno stream lascia intatti i grani di tutti gli altri. Anche le voci stocastiche hanno un generatore proprio, derivato dal seme, dallo stream e dall'indice della voce.

L'identità del generatore è per impostazione predefinita lo `stream_id`, quindi due stream non pescano mai la stessa sequenza, nemmeno con lo stesso seme. La chiave `rng_group` sostituisce lo `stream_id` in questa derivazione: gli stream che dichiarano lo stesso gruppo condividono le sequenze casuali di tutti i componenti.

```yaml
seed: 1988
streams:
  - stream_id: cugini_1
    sample: voice.wav
    rng_group: cugini
  - stream_id: cugini_2
    sample: voice.wav
    rng_group: cugini
```

Questo serve quando più stream vanno letti come un unico oggetto, per esempio più stream distribuiti su posizione e pan con la stessa griglia stocastica. Due stream identici con lo stesso gruppo hanno grani identici, e con `stream_id` diversi e senza gruppo hanno grani diversi. Condividere la sequenza non significa condividere la griglia temporale: gli intervalli fra onset dipendono anche dalla densità, e con densità diverse i due stream si sfasano subito pur pescando dalla stessa sequenza.

Il seme governa la generazione e non il rendering. I tre renderer ricevono la stessa lista di grani e nessuno estrae numeri casuali (sezione 3.7): se due file audio dello stesso brano non sono uguali bit per bit, la differenza sta nell'elaborazione del segnale e non in una scelta del caso.

## Stream come file

Questa sezione descrive il ramo principale del motore: `file:` è successivo alla versione 9.1.0 descritta nel capitolo 3, e non è ancora in una versione rilasciata.

Una voce della lista `streams` può essere un riferimento a un altro documento YAML, invece di uno stream scritto per intero. Il documento importato è un file a sé, tipicamente quello di un laboratorio, che si apre e si rende anche da solo. Il documento del brano, il *master*, ne decide soltanto il piazzamento.

```yaml
# brano.yml, il master
seed: 1441
streams:
  - file: streams/risacca.yml
    onset: 12.5
    mute: true
  - stream_id: stream2
    sample: pino.wav
```

```yaml
# streams/risacca.yml, che si rende anche da solo
seed: 1441
streams:
  - stream_id: risacca
    onset: 0
    duration: 30
    sample: mare.wav
    density: 40
```

La divisione dei compiti segue una regola: ogni chiave ha una sola casa. Accanto a `file:` il master può tenere soltanto il piazzamento, cioè `stream_id`, `onset`, `mute` e `solo`; qualsiasi altra chiave è un errore che nomina il master, la voce e la chiave. Del file importato si legge lo stream, senza le sue chiavi di piazzamento (`engine/stream_files.py`):

```python
CHIAVI_DI_PIAZZAMENTO = ('stream_id', 'onset', 'mute', 'solo')
estranee = [k for k in voce
            if k != 'file' and k not in CHIAVI_DI_PIAZZAMENTO]
if estranee:
    raise StreamFileKeyError(origine, estranee, CHIAVI_DI_PIAZZAMENTO)
risolto = {k: v for k, v in stream.items()
           if k not in CHIAVI_DI_PIAZZAMENTO}
piazzamento = {k: voce[k] for k in CHIAVI_DI_PIAZZAMENTO
               if k in voce}
if piazzamento.get('stream_id') is None:
    piazzamento['stream_id'] = os.path.splitext(
        os.path.basename(voce['file']))[0]
risolti.append({**piazzamento, **risolto})
```

Il laboratorio può scrivere `onset: 0` e un proprio `stream_id` perché il file si renda da solo, ma nel brano le decisioni di piazzamento sono del master. Se il master non scrive uno `stream_id`, vale il nome del file senza estensione: nell'esempio `risacca`, che coincide con quello del laboratorio. Il percorso è relativo alla cartella del master, mentre il `sample` si cerca come per ogni altro stream, nella cartella dei campioni. Un file importato contiene un solo stream e non può a sua volta importarne altri, quindi non esistono catene né cicli.

L'importazione è la prima cosa che il motore fa dopo aver letto il master, e le espressioni matematiche valgono sullo stream importato come su quello scritto nel master (`Generator.load_yaml`):

```python
raw_data = self._read_document(self.yaml_path)
raw_data, importati = resolve_stream_files(
    raw_data, self.yaml_path, self._read_document)
self.data = self._eval_math_expressions(raw_data)
```

Da lì in poi il motore vede una lista di stream come se fossero stati scritti nel master. La cache degli stem lo tratta di conseguenza: il suo fingerprint è quello dello stream risolto, quindi spostare uno stream dal master a un file non lo rende da rifare, e modificare il file importato rifà quello stream e nessun altro.

Resta da chiarire cosa succede al suono. Il seme è uno solo, quello del master: se il file importato ne dichiara uno diverso, il render procede con quello del master e il motore avvisa su stderr. Dal momento che il generatore di ogni componente deriva da seme e identità, uno stream importato suona come nel laboratorio solo con lo stesso seme e lo stesso `stream_id`. Uno `stream_id` diverso dà un'altra realizzazione dello stesso stream, ed è accettato: succede di default quando il laboratorio scrive un identificatore diverso dal nome del file. Chi vuole la realizzazione del laboratorio scrive quell'identificatore accanto a `file:`, oppure dichiara nel file un `rng_group`, che non dipende dal nome con cui il master chiama lo stream. Importare due volte lo stesso file richiede due `stream_id` diversi, e dà due realizzazioni distinte; senza, è un errore, perché i due stem avrebbero lo stesso nome.

Il meccanismo permette di lavorare per parti. Ogni stream è sviluppato e ascoltato nel proprio file, e il brano si assembla in un master che li dispone nel tempo e decide quali far suonare.

## Che cosa il linguaggio lascia passare

Il linguaggio è permissivo: la notazione differenziale rende comoda la scrittura e paga il prezzo di non protestare davanti a ciò che non riconosce. Le sezioni precedenti ne hanno incontrato i casi, che qui si raccolgono.

| Si scrive | Il motore |
|----------------------------------------------|----------------------------------------|
| un `onset` o una `duration` cancellati | usa l'origine della timeline e la durata del file |
| `mute: false` | muta lo stream |
| una chiave che non conosce (`desnity`, `grain: {duraton: 0.2}`, un `bpm` in testa al file) | la ignora, senza avviso |
| `time_mode: normalised` | lo legge come `absolute`, senza avviso |
| `time_mode` nel dizionario di `density` | lo ignora, senza avviso |
| un'espressione che non si calcola | stampa un avviso e lascia la stringa |
| `distribution_mode: gausian`, `range_anchor: max`, `density: -5` | si ferma con un errore |

Il confine fra i due comportamenti passa per ciascuna chiave: un valore sbagliato di `distribution_mode` o `range_anchor` è un errore, uno di `time_mode` no, e un numero fuori dai limiti del parametro è un errore alla costruzione dello stream, prima di ogni grano (sezione 3.1). Il motore non conosce, quando legge, l'insieme delle chiavi valide, e chi scrive a mano ha due guardie fuori da lui: il completamento delle chiavi del language server (capitolo 9) e la MAP, che a rendering fatto mostra ciò che è uscito davvero (capitolo 8). Una chiave scritta male si riconosce nella MAP perché l'effetto atteso non c'è.
