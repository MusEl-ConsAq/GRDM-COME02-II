# Architettura di Python Granular Engine

Questo capitolo descrive come Python Granular Engine (d'ora in avanti PGE) è costruito e perché è costruito così. Il linguaggio YAML (capitolo 4), il grano e lo stream (capitolo 5), le voci (capitolo 6) e i renderer (capitolo 7) hanno capitoli propri; qui interessano le parti del programma, la responsabilità di ciascuna e i contratti che le tengono insieme. Il disegno ruota attorno a una sola scelta: il motore non produce suono, produce una *lista di grani*, e tutto il resto è lavoro che precede o che segue quella lista. Le altre scelte ne sono conseguenze. Chi produce la lista non sa come la si trasforma in audio, e chi la consuma non sa come è stata prodotta. Aggiungere un consumatore, una strategia o una finestra non richiede di toccare chi produce. E poiché ogni scelta casuale viene presa in produzione e soltanto lì, la stessa specifica dà la stessa lista.

La versione descritta è la 9.1.0 [@DeMattia2026Pge], con le modifiche non ancora rilasciate fino al commit `1188dbc` del 13 ottobre 2026, fra cui la chiave `file:` del capitolo 4. I brani di codice citati sono identici nella 9.1.0 e in quel commit. Il pacchetto `pge` si divide in nove sotto-pacchetti e conta circa 26 400 righe di Python in `src/`, con 164 file di test. Dipende da NumPy, `soundfile`, matplotlib (importato soltanto quando serve) e PyYAML; Csound o SuperCollider servono ai rispettivi renderer. L'integrazione continua lo prova dalla versione 3.9 alla 3.14 di Python.

## La pipeline: dal file YAML al suono

Un brano attraversa tre fasi, che la figura mette in fila. La prima costruisce gli oggetti: legge lo YAML e crea uno `Stream` per ogni stream dichiarato. La seconda genera i grani di ciascuno stream. La terza consuma la lista dei grani e la trasforma in audio, in un'immagine o in un file di scambio. I dati scorrono in un solo verso, dall'alto in basso. La richiesta di lavoro che mette in moto la seconda fase corre invece in verso opposto, ed è ciò che permette di tenere distinte le prime due fasi.

![La pipeline di PGE. Le frecce piene portano i dati dal file YAML ai file di uscita; quella tratteggiata porta in senso contrario la richiesta che innesca la generazione dei grani. Reaper e Sonic Visualiser leggono i parametri dello stream, non la lista dei grani.](docs/images/pipeline.pdf){width=100%}

L'intera pipeline si legge in poche righe dell'interfaccia programmatica, `pge.api`. La costruzione è la funzione `load_generator`:

```python
generator = Generator(yaml_path, samples_dir=samples_dir)
generator.load_yaml()
generator.create_elements()
```

Il consumo, nella funzione `render`, mette un renderer, un criterio per i nomi dei file e una modalità davanti alla lista degli stream:

```python
engine = RenderingEngine(
    renderer_obj,
    naming_strategy=DefaultNamingStrategy(ext=audio_format.extension),
)
mode = StemsRenderMode() if per_stream else MixRenderMode()
generated = engine.render(
    streams=generator.streams,
    output_path=output_path,
    mode=mode,
)
```

Fra le due non c'è nessuna chiamata che generi i grani: la generazione non è un passo che il programma ordina, è l'effetto della prima lettura della lista (sottosezione 3.1.1).

**Costruzione.** Il `Generator` (`engine/generator.py`) è l'orchestratore. Il metodo `load_yaml()` legge il file, valuta le espressioni scritte nei valori (per esempio `(pi)` o `(10/3)`) e ne ricava il seme. Il metodo `create_elements()` applica la regola solo/mute e costruisce uno `Stream` per ogni stream rimasto. Lo `Stream` (`core/stream.py`) è l'unità compositiva: alla costruzione legge i propri parametri dallo YAML, li convalida e li affida a collaboratori specializzati (sezione 3.3). Alla fine della fase ogni stream è configurato e convalidato, e non ha ancora un solo grano. Intanto il `Generator` registra i campioni e le finestre degli stream in una tabella dei simboli, `FtableManager`, di cui si dice nella sezione 3.2.

**Generazione.** Alla prima lettura di `stream.voices`, `generate_grains()` produce la lista: un cursore del tempo per voce, un grano per voce attiva a ogni passo, infine la strategia di *clip* per i grani che sporgerebbero oltre la fine dello stream (capitoli 5 e 6).

**Consumo.** La lista è letta da tre tipi di consumatore. I renderer (NumPy, Csound, SuperCollider) la trasformano in audio; li coordina il `RenderingEngine`, che non sa quale dei tre ha davanti (sezione 3.6). La MAP (`ScoreVisualizer`) disegna ogni grano nel piano tempo-posizione di lettura e, sotto, le curve dei parametri. L'esportazione JSON scrive i grani di ogni stream. Altri due esportatori non leggono la lista: il progetto Reaper dispone gli stem sulla timeline e gli bastano onset, durata e nome dello stream; la sessione Sonic Visualiser disegna le curve dei parametri. Il confine fra produzione e consumo passa dalla lista, ed è per questo che un consumatore si aggiunge senza toccare il resto.

In termini di Seeger [@Seeger1958] il file YAML è una notazione *prescrittiva*, un'istruzione data al motore prima del rendering. La MAP è *descrittiva*: documenta ciò che è stato effettivamente generato e non viene riletta come input. Il verso unico della pipeline è lo stesso: la specifica sta a monte, i documenti derivati a valle, e nessuno risale.

### La generazione lazy

*Lazy evaluation* è un termine tecnico che si lascia in inglese. Indica una strategia di calcolo in cui un valore non viene calcolato nel punto in cui è definito, ma soltanto quando qualcuno ne ha bisogno. Al primo bisogno il calcolo si esegue e il risultato si conserva (si dice che è *memoizzato*); i bisogni successivi ricevono il risultato conservato senza ricalcolare. La strategia opposta si dice *eager*: il valore si calcola subito, alla definizione. Dalla differenza discendono tre proprietà della lazy evaluation: il calcolo si esegue al più una volta, può non eseguirsi mai, e il momento in cui si esegue lo stabilisce la richiesta di chi consuma il risultato, non l'ordine in cui il programma è scritto. Hughes [@Hughes1989] vede in quest'ultima proprietà ciò che permette di scomporre un programma in un produttore e un consumatore indipendenti: chi consuma decide quanto lavoro deve fare chi produce.

Il prezzo è di due tipi. Il costo si sposta: il primo accesso è più lento dei successivi, e un errore nato dentro il calcolo compare lì e non alla definizione. E il calcolo è sicuro soltanto se il suo risultato non dipende dal momento in cui si esegue: se leggesse uno stato condiviso, come un generatore casuale globale, cambiare l'ordine delle richieste cambierebbe il risultato.

In PGE la lista dei grani di uno stream è lazy. Il costruttore di `Stream` lascia vuoto il campo `_voices` e il segnale `generated` a `False`. Il calcolo sta dietro una proprietà (`@property`), il meccanismo con cui Python fa passare per un attributo ciò che in realtà è una chiamata:

```python
@property
def voices(self) -> List[List[Grain]]:
    """Grani organizzati per voce. Lazy: genera al primo accesso."""
    if not self.generated:
        self.generate_grains()
    return self._voices
```

Chiunque legga `stream.voices`, sia un renderer, la MAP o un esportatore, innesca la generazione la prima volta e riceve la lista conservata le volte successive. Il metodo `generate_grains()` chiude con due assegnazioni, e assegna al campo e non alla proprietà, perché il getter di `.voices` richiamerebbe `generate_grains()` all'infinito:

```python
self._voices = clip_strategy.apply(all_voice_grains, self)
self.generated = True
```

Il vantaggio non è dove si penserebbe. Quando il sistema lavora per stem con la cache attiva, il renderer chiede alla cache se lo stream è cambiato *prima* di leggere le voci (`NumpyAudioRenderer._cache_skip`; gli altri due renderer fanno lo stesso):

```python
if not self.cache_manager:
    return False
stream_dict = self.stream_data_map.get(stream.stream_id)
if not stream_dict:
    return False
dirty = self.cache_manager.is_dirty(stream_dict, output_path)
status = "DIRTY" if dirty else "clean"
print(f"[CACHE] {stream.stream_id}: {status}", flush=True)
return not dirty
```

Uno stream pulito non genera mai i propri grani, perché nessuno ne ha letto la lista. Lo si verifica rendendo due volte lo stesso brano di tre stream con lo script `lazy_e_riproducibilita.py`, nella cartella `esempi/architettura` del repository della tesina: dopo il secondo rendering, a cache a regime, `generated` è `False` per tutti e tre. Anche `Stream.__repr__` è scritto in modo da non innescare la generazione: finché i grani non esistono dichiara `grains=lazy`.

Non è però un'ottimizzazione del totale, e il capitolo 7 lo dice con le misure. La costruzione degli oggetti `Grain` pesa da un ottavo a un terzo del tempo di un rendering; il resto è la somma dei grani nel buffer. Se tutti gli stream sono da rifare, il lavoro è quello di una generazione eager, solo spostato in avanti. La lazy evaluation serve a non pagare il lavoro che la cache ha reso inutile e a tenere economica la costruzione degli stream.

Le due condizioni del prezzo sono rispettate. Ogni componente stocastico pesca da un generatore proprio, derivato dal seme (sezione 3.7), e quindi il risultato non dipende dal momento in cui si genera: lo script verifica che generare gli stream in ordine inverso, o metterne uno in mute, lascia identici i grani degli altri. La validazione dello YAML è eager, e i suoi difetti (una strategia inesistente, un parametro fuori dominio) si segnalano alla costruzione e non al primo accesso. Resta un caso non chiuso: uno `Stream` costruito fuori dal `Generator` si costruisce senza errori e fallisce soltanto al primo accesso a `.voices`, con un `AttributeError` su `window_table_map` (sezione 3.8).

## Il grano e la tabella dei simboli

La lista dei grani è il punto stretto del disegno: è l'unico oggetto che attraversa il confine fra produzione e consumo, e contiene un tipo solo (`core/grain.py`):

```python
@dataclass(frozen=True)
class Grain:
    __slots__ = (
        'onset', 'duration', 'pointer_pos', 'pitch_ratio',
        'volume', 'pan', 'sample_table', 'envelope_table',
    )
    onset: float
    duration: float
    pointer_pos: float
    pitch_ratio: float
    volume: float
    pan: float
    sample_table: int
    envelope_table: int
```

Ogni scelta della dichiarazione ha una ragione. Il grano è *congelato* (`frozen=True`): una volta creato nessuno può modificarlo, e quindi la generazione e i consumatori non possono interferire. L'immutabilità rende possibile anche il passaggio dei grani ai processi del renderer NumPy parallelo, che avviene per *pickle*: una classe congelata e con `__slots__` non sopravvive al pickle predefinito, e per questo il grano definisce `__reduce__`, che lo ricostruisce dal costruttore conservando validazione e immutabilità. Il grano ha poi `__slots__`, cioè nessun dizionario per istanza: un brano come *mare-nostrum* ne contiene più di tre milioni (capitolo 10), e il capitolo 7 misura circa 225 byte per grano.

Il grano contiene soltanto numeri: l'istante, la durata, la posizione di lettura, il rapporto di altezza, il volume, il pan e due interi. Il verso di lettura non ha un campo proprio, è il segno di `pitch_ratio`: `PitchController.calculate` nega il rapporto quando il grano si legge all'indietro. I due interi, `sample_table` e `envelope_table`, sono numeri di tabella (il secondo identifica la finestra del grano, e il suo nome viene dal vocabolario di Csound, dove l'inviluppo d'ampiezza è una tabella di funzione). Un grano non porta il nome del suo campione né della sua finestra, ma un indice. Il significato dell'indice sta in una tabella dei simboli, `FtableManager`, che il `Generator` riempie alla costruzione:

```python
def register_sample(self, sample_path: str) -> int:
    if sample_path in self._sample_cache:
        return self._sample_cache[sample_path]
    num = self.next_num
    self.next_num += 1
    self.tables[num] = ('sample', sample_path)
    self._sample_cache[sample_path] = num
    return num
```

La registrazione deduplica: due stream che leggono lo stesso file hanno lo stesso numero. Ogni renderer riceve la stessa tabella, `{numero: ('sample', percorso) | ('window', nome)}`, e la materializza a modo proprio: Csound come tabelle di funzione nello score, NumPy come array, SuperCollider come buffer. È la stessa idea della tabella dei simboli di un compilatore: i nomi si risolvono una volta, fuori dal dato, e il dato resta leggero e neutro rispetto a chi lo consuma.

La lista è una `List[List[Grain]]`, una lista per voce, e l'ordine voce per voce è quello su cui i renderer sommano: l'ordine delle somme in virgola mobile è ciò che rende un rendering riproducibile bit a bit. `stream.voices` è l'unica fonte di verità sui grani esistenti. Una vista piatta, `stream.grains`, era un secondo campo allineato soltanto lungo un percorso, e fuori da quello le due viste divergevano senza avvisare; oggi è una vista derivata, in sola lettura e deprecata. Il criterio è un solo stato, e il resto derivato.

## Dallo YAML al valore: il parametro

Il grano si ottiene interrogando i parametri dello stream a un dato istante, e come un blocco di YAML diventi qualcosa che si può interrogare è la parte meno visibile e più sistematica dell'architettura. Alla costruzione lo `Stream` separa due cose che il file mescola. L'*identità* dello stream (nome, onset, durata, campione, gruppo del caso) va in uno `StreamContext`. Le *regole di processo* (l'interpretazione della probabilità di deviazione, la modalità del tempo, la strategia di clip, il seme) vanno in uno `StreamConfig`. Sono due `dataclass` congelate, costruite una volta (`core/stream_config.py`) e condivise da tutti i collaboratori dello stream, che non possono modificarle.

Per i parametri propri dello stream (volume, pan, durata del grano, finestra) la costruzione è guidata dai dati. Una lista di specifiche dichiarative, `STREAM_PARAMETER_SCHEMA`, dice dove ciascun parametro sta nello YAML:

```python
ParameterSpec(
    name='volume',
    yaml_path='volume',
    default=0.0,
    range_path='volume_range',
    deviation_probability_key='volume'
),
```

Un'altra tabella, `GRANULAR_PARAMETERS`, dice quali sono i limiti (`ParameterBounds`: minimo, massimo, banda ammessa, tipo di variazione). Il `GranularParser` sa come si costruisce un `Parameter`; il `ParameterOrchestrator` è il solo punto in cui lo schema, che sa *dove* sono i dati, incontra il parser, che sa *come* si costruisce l'oggetto, e vi inietta il gate di probabilità. Aggiungere un parametro allo stream è perciò una riga di limiti e una `ParameterSpec`, senza modificare il codice che costruisce. Lo stesso meccanismo serve i controller: puntatore e densità hanno ciascuno il proprio schema nello stesso modulo e un proprio `ParameterOrchestrator`.

Il `Parameter` (`parameters/parameter.py`) è l'oggetto in cui il linguaggio del capitolo 4 diventa comportamento. Il suo metodo `get_value(time)` è, come dice la docstring, l'unico che il resto del programma deve chiamare:

```python
def get_value(self, time: float) -> float:
    base_val = self._evaluate_input(self._value, time)
    current_range = self._calculate_range(time, base_val)
    if not self._probability_gate.should_apply(time):
        return self._clamp(base_val, time)
    final_val = self._variation_strategy.apply(
        base_val,
        current_range,
        self._distribution
    )
    return self._clamp(final_val, time)
```

I passi sono cinque. Il valore centrale si ricava da un numero o da un inviluppo; la banda di variazione si calcola nello stesso istante; il gate di probabilità decide se *questo* grano devia; se devia, una strategia di variazione estrae un valore dentro la banda con la forma di distribuzione scelta; un limite di sicurezza riporta il risultato nel dominio del parametro. È la maschera di tendenza di Truax [@Truax1988] resa come oggetto: un valore centrale che varia nel tempo e una banda intorno ad esso. Il caso entra in due punti per parametro, il gate e la distribuzione, e ciascuno riceve alla costruzione un generatore proprio (sezione 3.7).

Puntatore, altezza, densità e finestra non sono parametri semplici ma comportamenti, e hanno un controller ciascuno (`controllers/`). I quattro si costruiscono con la stessa firma, `(params, config)`, a partire dal proprio blocco YAML (`pointer`, `pitch`, `grain`) o, per la densità, dall'intero stream. Le voci hanno un `VoiceManager`, descritto nel capitolo 6. Il parametro e il controller sono i due modi in cui un blocco YAML diventa un oggetto che sa rispondere alla domanda «quanto vale al tempo *t*?».

Tutti i collaboratori convergono in `Stream._create_grain`, che compone il grano. Ogni campo viene da un collaboratore diverso: l'altezza dal controller dell'altezza, la posizione dal puntatore, il volume e il pan dai rispettivi `Parameter`, la finestra dal controller della finestra, e a ciascuno si sommano gli scarti della voce. Il metodo si conclude così:

```python
return Grain(
    onset=absolute_onset,
    duration=grain_dur,
    pointer_pos=pointer_pos,
    pitch_ratio=pitch_ratio,
    volume=volume,
    pan=pan,
    sample_table=self.sample_table_num,
    envelope_table=window_table_num
)
```

## Organizzazione dei moduli

Il codice si divide in nove sotto-pacchetti, più `api.py` e `cli.py` alla radice. La tabella riassume il ruolo dei sotto-pacchetti.

| Pacchetto | Ruolo |
|-----------|-------|
| `engine` | Il `Generator`: lettura dello YAML, importazione degli stream, regola solo/mute |
| `core` | I tre oggetti centrali: `Stream`, `Grain`, `StreamConfig` |
| `parameters` | Schema, limiti e costruzione dei parametri; la classe `Parameter` |
| `envelopes` | Gli inviluppi che fanno variare un parametro nel tempo: interpolazioni, segmenti, distribuzione dei punti |
| `controllers` | Densità, altezza, puntatore, finestra e gestione delle voci |
| `strategies` | Le strategie intercambiabili: distribuzione di altezza, onset, puntatore e pan sulle voci, variazione stocastica, clip del grano |
| `rendering` | I renderer, i traduttori verso i linguaggi dei sintetizzatori, la cache, la MAP |
| `export` | Esportazione verso Reaper, Sonic Visualiser e file JSON dei grani |
| `shared` | Ciò che serve a tutti: errori, logger, gestione del seme, utilità |

Il pacchetto `rendering` è di gran lunga il più ampio, con 32 moduli e circa un terzo delle righe, perché ospita i tre renderer e tutto ciò che sta intorno: la tabella dei campioni, la scrittura degli score, la cache incrementale e il visualizzatore.

I pacchetti non sono strati, e non lo si afferma per comodità: lo script `dipendenze.py`, nella stessa cartella, costruisce il grafo degli import leggendo i sorgenti come alberi sintattici. Tra i 97 file Python del commit descritto non c'è nessun ciclo di import, contando 276 archi anche quando l'import sta dentro una funzione. Tra i pacchetti, invece, cinque coppie si importano a vicenda: `core` con `controllers`, con `parameters` e con `strategies`, `parameters` con `strategies`, `envelopes` con `shared`. Il motivo è che un pacchetto raccoglie cose dello stesso genere e non dello stesso livello. `core` contiene sia il dato più basso (`Grain` e `StreamConfig`, importati dai controller) sia l'orchestratore più alto (`Stream`, che importa i controller). Al livello dei moduli un ordine esiste; al livello dei pacchetti no.

![Il verso delle dipendenze tra i sotto-pacchetti, come le calcola `dipendenze.py`. Si omettono gli archi che saltano uno strato. Nel riquadro centrale i pacchetti dipendono l'uno dall'altro senza un ordine fra pacchetti; né essi né la base importano i pacchetti sopra.](docs/images/dipendenze.pdf){width=70%}

Ciò che regge a ogni livello è un confine solo. Nessuno dei sei pacchetti in basso nella figura (`core`, `controllers`, `parameters`, `strategies`, `envelopes`, `shared`) importa `rendering`, `engine`, `export`, `api` o `cli`. I renderer conoscono il grano; il grano non conosce i renderer. Lo script lo verifica elencando chi importa ciascun pacchetto di quelli in alto.

Nella forma più stretta il confine è imposto da un test. La sintassi di Csound non deve comparire sotto il livello dei renderer, e `tests/rendering/test_csound_emitter.py` legge otto moduli come alberi sintattici, fra cui `Grain`, `FtableManager`, il catalogo delle finestre e `ScoreWriter`. Ne estrae i letterali stringa, escluse le docstring, e fallisce se uno apre una riga di score:

```python
_SCORE_STATEMENT = re.compile(r'^([if][ "{]|e\n$|; )')
```

Un secondo test controlla che la guardia non sia cieca: applicata a `CsoundEmitter`, che quelle righe le scrive per mestiere, deve trovarle.

La regola ha una storia concreta. All'origine un `Grain` sapeva scrivere la propria riga di score Csound, e la precisione a otto decimali dell'onset, necessaria perché a 96 kHz un grano può durare un solo campione, era una decisione sul formato di Csound presa dentro il dato. Un secondo renderer testuale non avrebbe avuto altro posto in cui mettere il proprio metodo che accanto al primo. Oggi la decisione sta in un modulo solo, `CsoundEmitter`:

```python
def grain_statement(self, grain, onset_offset: float = 0.0) -> str:
    return (f'i "{self.instrument_name}" '
            f'{grain.onset - onset_offset:.8f} {grain.duration:.8f} '
            f'{grain.pointer_pos:.6f} {grain.pitch_ratio:.6f} '
            f'{grain.volume:.2f} {grain.pan:.3f} '
            f'{grain.sample_table} {grain.envelope_table}\n')
```

È il criterio che Parnas [@Parnas1972] propone per scomporre un sistema: non secondo i passi dell'elaborazione, ma secondo le decisioni di progetto che è probabile cambino, ciascuna nascosta in un modulo. Il formato di uno score è una di queste decisioni.

## Libreria e riga di comando

PGE nasce come programma da lanciare dalla radice del repository e con il tempo è diventato anche una libreria che altri progetti importano. Le due esigenze sono diverse: una riga di comando stampa messaggi, restituisce codici di uscita e può fare scelte di comodo; una libreria non deve stampare, né terminare il processo, né decidere al posto di chi la usa.

Il sistema ha perciò due strati. `pge.api` è l'interfaccia programmatica: `load_generator`, `build_renderer`, `render`, `render_file` e le funzioni `export_*`. Non legge `sys.argv`, non chiama `sys.exit` e segnala gli errori con eccezioni; ogni percorso sul disco è un parametro esplicito. `pge.cli` è un guscio sottile che interpreta gli argomenti, stampa e fissa i codici di uscita, e delega tutto il lavoro all'API. Il file `src/main.py` e il comando `pge` sono due ingressi alla stessa CLI. Da Python, una composizione si rende in due righe:

```python
from pge import api
risultato = api.render_file("brano.yml", "brano.aif", renderer="numpy", per_stream=True)
```

La funzione restituisce un `RenderResult`, che elenca i file prodotti, il tipo di renderer, la durata e il numero di grani per stream. La differenza fra i due strati sta nelle *politiche*, cioè nei valori predefiniti.

| Decisione | API (valore predefinito) | CLI |
|-----------|--------------------------|-----|
| Processi paralleli | 1, risultato deterministico | automatico (core disponibili meno uno) |
| Renderer | NumPy, nessun programma esterno | Csound, la scelta storica |
| Percorso del file di cache | esplicito | derivato dal nome del file YAML |
| Messaggi a schermo | nessun `print` nel proprio modulo | sempre |

Il punto più delicato è che anche la libreria, nei fatti, scrive a schermo: alcuni componenti che orchestra hanno ereditato dei `print()` che fanno parte del protocollo con l'editor grafico del progetto (per esempio la riga `[CACHE]` della sezione 3.1, che PGE-ui legge per costruire l'avanzamento). L'API lo dichiara in un censimento, nell'intestazione del modulo, e un test lo verifica sull'output reale. Quando un'interfaccia non può essere del tutto silenziosa, è meglio che il contratto dica esattamente quanto non lo è.

## Estensibilità

L'architettura è pensata perché le estensioni siano *additive* rispetto al nucleo: si scrive un file e lo si registra, senza modificare `core`, `controllers` e `parameters`. Il principio è quello detto *aperto/chiuso*: un modulo deve essere aperto all'estensione e chiuso alla modifica [@Meyer1988]. I nomi dei meccanismi sono quelli dei pattern classici [@Gamma1994], e il codice li usa nelle docstring: *facade* per il `RenderingEngine`, *strategy* per le modalità e le strategie, *factory* per la scelta del renderer. L'estensione si realizza in quattro luoghi, e va detto subito che in uno di essi, i renderer, la modifica sfiora il perimetro.

### Un renderer nuovo

Il sistema deve produrre audio con più renderer, e deve poterlo fare in due modi: un file per ogni stream (*stems*) oppure un unico file con tutto il brano (*mix*). Le due scelte sono indipendenti. L'interfaccia astratta del renderer ha due metodi obbligatori e uno concreto (`rendering/audio_renderer.py`):

```python
class AudioRenderer(ABC):
    renderer_type: str = 'unknown'

    @abstractmethod
    def render_single_stream(self, stream, output_path: str) -> str:
        ...

    @abstractmethod
    def render_merged_streams(self, streams: List, output_path: str) -> str:
        ...

    def render_streams(self, pairs: List[Tuple[object, str]]) -> List[str]:
        return [self.render_single_stream(stream, path) for stream, path in pairs]
```

Il primo metodo rende *uno* stream in *un* file, con onset relativi allo stream e il file che inizia a zero. Il secondo rende più stream in un file, con onset assoluti. Il terzo è concreto e il suo comportamento predefinito è un ciclo sul primo; il renderer NumPy lo ridefinisce per affidare ogni stem a un processo di lavoro, quando conviene. Il renderer non decide se produrre stems o mix. Lo decide la modalità, un oggetto a parte, e lo decide in due righe:

```python
paths_map = naming.generate_paths(output_path, streams, mode='stems')
return renderer.render_streams(paths_map)
```

La modalità decide *che cosa* rendere (un file per stream) e il renderer decide *come*. Le due scelte si combinano di conseguenza liberamente: ogni renderer funziona con ogni modalità, e un renderer nuovo le eredita entrambe.

La scelta del renderer sta in una fabbrica, `RendererFactory`, e il suo elenco dei tipi validi è il solo che esista:

```python
_VALID_TYPES = {'numpy', 'csound', 'supercollider'}
```

I messaggi d'errore e la CLI interrogano `available_types()` e non ne tengono una copia. L'elenco non si aggiorna però da solo. Per aggiungere un renderer la documentazione di PGE (`docs/how-to/add-renderer.md`) prescrive un file nuovo e tre modifiche: l'elenco e un ramo di costruzione nella fabbrica, un ramo in `api.build_renderer` e i flag in `cli._build_renderer`. Il disegno è additivo per il nucleo e non per il perimetro.

### Parametri e finestre

Aggiungere un parametro dello stream si è visto nella sezione 3.3: una riga di limiti e una specifica. Per le finestre del grano vale lo stesso criterio della sintassi di Csound (sezione 3.4). Il catalogo descrive una finestra *nei suoi termini* (forma, coefficienti, parametri, simmetria) senza nominare routine Csound né funzioni NumPy, e due traduttori ne ricavano la materializzazione: uno per Csound, che produce una tabella con una routine GEN, e uno per NumPy, che produce un array. SuperCollider riceve gli array del traduttore NumPy e li carica come buffer. Le forme sono meno delle finestre: Hamming, Hann, Blackman e Blackman-Harris sono quattro insiemi di coefficienti della stessa forma parametrica, la somma di coseni, e aggiungerne una quinta è una riga nel catalogo e nessuna nei traduttori.

La ragione è un difetto reale delle versioni precedenti. Il catalogo diceva *come Csound produce* una finestra e il renderer NumPy la reimplementava da zero, con i nomi in comune e le forme no: `triangle` passava la validazione dello YAML ed esplodeva a metà rendering solo con NumPy. Oggi una finestra entra nel catalogo soltanto se ogni traduttore sa produrla, un test lo richiede, e la copertura è dichiarata e non scoperta durante il rendering.

### Le strategie e il registro

Molti comportamenti sono scelte intercambiabili, selezionate per nome nello YAML: come le voci distribuiscono le altezze (`step`, `chord`, `spectral`), come si spostano nel tempo (`linear`, `geometric`, `stochastic`), come si dispongono nel pan, come si seleziona la finestra, come si applica la variazione stocastica. Ciascuna è una *strategia*, una classe che implementa un'interfaccia comune, e per ciascuna famiglia c'è un registro dal nome alla classe:

```python
VOICE_ONSET_STRATEGIES = StrategyRegistry('voice_onset', VoiceOnsetStrategy, {
    'linear':      LinearOnsetStrategy,
    'geometric':   GeometricOnsetStrategy,
    'stochastic':  StochasticOnsetStrategy,
})
```

Il meccanismo era ripetuto in nove moduli e le copie divergevano nei nomi dei parametri e nelle etichette. Oggi è una classe sola, `StrategyRegistry`, che eredita da `dict` ed è la mappa stessa: le fixture dei test ne fanno uno snapshot, e il language server ne legge le chiavi importandola per nome. La sua operazione essenziale è la costruzione per nome:

```python
def create(self, name: str, *args, **kwargs) -> S:
    if name not in self:
        raise StrategyNotFoundError(
            strategy_kind=self.kind,
            name=name,
            available=list(self.keys()),
        )
    return self[name](*args, **kwargs)
```

Otto famiglie la usano: altezza, onset, puntatore e pan delle voci, selezione della finestra, clip del grano, densità e variazione. Per aggiungere una strategia basta scrivere la classe e registrarla con un nome; lo YAML la riconosce subito, e un nome inesistente produce un errore che elenca i nomi disponibili.

### Gli errori

Gli errori seguono la stessa logica. Derivano tutti da una radice, `EngineError`, e portano il contesto utile a chi compone (lo stream in cui sono avvenuti, il campo, un suggerimento), così un errore del compositore, come un campo mancante o un file di campioni assente, si distingue da un difetto del programma. Gli errori di configurazione ereditano anche il tipo che sostituiscono: `ConfigFileNotFoundError` è anche un `FileNotFoundError`, e chi catturava l'eccezione di Python continua a catturarla.

## Riproducibilità e verifica

Una composizione generata con elementi casuali ha senso solo se può essere riprodotta. PGE tratta la riproducibilità come un requisito di progetto: la specifica con il seme dichiarato è il documento che si versiona e si invia a chi deve leggerla, e l'audio si rigenera da essa. Per questo il `Generator` non lascia che nessun componente peschi da un generatore casuale globale. Ogni sito stocastico (la variazione di un parametro, il gate di probabilità, l'intervallo asincrono fra i grani, la selezione della finestra) ottiene un proprio generatore, derivato dal seme, dall'identità dello stream e dal nome del componente (`shared/seeding.py`):

```python
def component_rng(seed, stream_id: str, component: str):
    if seed is None:
        return random
    digest = hashlib.sha256(
        f"{seed}:{stream_id}:{component}".encode()
    ).hexdigest()
    return random.Random(int(digest, 16))
```

La derivazione usa SHA-256 e non la funzione `hash()` di Python, perché `hash()` su una stringa cambia da un processo all'altro, e la riproducibilità fra una sessione e la successiva andrebbe perduta. Uno stream può condividere la sequenza di un altro dichiarando un gruppo comune (`rng_group`, capitolo 4). Se lo YAML non dichiara un seme, il `Generator` ne ricava uno dall'orologio, lo stampa (`[SEED] … aggiungi 'seed: N' allo YAML`) e il brano resta ricostruibile a posteriori.

Il risultato si verifica con lo script `lazy_e_riproducibilita.py`. Per un brano di tre stream con il seme dichiarato, i grani sono gli stessi in tre processi con `PYTHONHASHSEED` diverso (la stessa impronta SHA-256 su 662 grani), non cambiano se gli stream si generano in ordine inverso né se un altro stream è in mute, e cambiano con un altro seme. Sono le condizioni da cui dipendono la generazione lazy (sezione 3.1) e la cache per stream: lo stem di uno stream non dipende da quali altri stream sono puliti in quel rendering.

La casualità sta tutta nella generazione: i renderer sono funzioni pure della lista dei grani e non estraggono numeri casuali. Ne seguono due conseguenze. Il parallelismo del renderer NumPy distribuisce soltanto la somma dei grani nel buffer, un'operazione senza stato (le sue garanzie sono nel capitolo 7). E il confronto fra renderer è un controllo: due renderer che ricevono lo stesso YAML con lo stesso seme ricevono la stessa lista, e se i loro file differiscono la differenza sta nel DSP (interpolazione, quantizzazione, precisione delle tabelle) e mai in una scelta casuale (capitolo 7).

Il progetto è sviluppato con test in modo sistematico: test unitari (`make tests`) e test di integrazione sull'intera catena, `make e2e-tests`, per ciascuno dei tre renderer. Ne parla il capitolo 9.

## Che cosa il disegno lascia aperto

Quattro punti dell'architettura non sono risolti, e conviene dirlo perché ciascuno è il rovescio di una scelta descritta sopra. I primi due sono registrati nella documentazione di PGE; gli altri due emergono dalla lettura del codice fatta per questa tesina.

Il primo è la taglia di `Stream`. Con oltre 1 100 righe è il secondo modulo del pacchetto per lunghezza, e coordina una ventina di moduli. La documentazione di PGE (`docs/explanation/stream-decomposition.md`) registra la decisione di *non* scomporlo nei cinque mestieri che vi si riconoscono (validazione, normalizzazione delle unità, collegamento dei collaboratori, generazione, vista di lettura). La ragione è il criterio con cui si decide un confine di modulo: vale la pena quando è stretto, con pochi ingressi e uscite restituite invece che scritte. Quattro mestieri su cinque hanno un solo chiamante e, per la generazione e per il collegamento dei collaboratori, un modulo separato avrebbe avuto in ingresso lo `Stream` intero: il codice si sarebbe spostato senza che cambiasse l'accoppiamento. La sola cucitura decisa, il blocco `voices:` che passerà al suo controller, non è ancora eseguita. Il costo del resto è accettato: ogni chiave nuova del blocco `grain:` continuerà ad atterrare in quel file.

Il secondo è un accoppiamento nel tempo. Il `Generator` assegna a ogni stream `sample_table_num` e `window_table_map` *dopo* la costruzione, e il costruttore non dichiara il secondo. Uno `Stream` costruito da solo è perciò un oggetto a metà: si costruisce senza errori e fallisce al primo accesso a `.voices`, per la ragione detta nella sezione 3.1. La generazione lazy sposta l'errore dal costruttore al primo accesso.

Il terzo è un residuo storico. Il `Generator` importa `FtableManager` e `ScoreWriter` dal pacchetto `rendering` e custodisce uno `ScoreWriter` Csound, con il metodo `generate_score_file`. Il confine della sezione 3.4 è dunque completo per `Grain` e per `Stream` e non per il `Generator`, che conserva la memoria di quando il motore produceva soltanto uno score.

Il quarto è il numero di canali. Il grano ha un pan in gradi, che non impone il numero di canali di uscita, ma i tre renderer producono oggi file stereofonici: la generalità sta nel dato e non ancora nei consumatori.
