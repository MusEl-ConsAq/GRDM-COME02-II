# Architettura di Python Granular Engine

Python Granular Engine (d'ora in avanti PGE) è uno strumento per la composizione con la sintesi granulare del suono campionato. Il compositore non scrive codice: descrive in un file YAML uno o più *stream* granulari, e il sistema ne ricava un file audio e una partitura grafica. La versione descritta in questa tesina è la 9.1.0 [@DeMattia2026Pge]. Il sistema è stato presentato al XXV Colloquio di Informatica Musicale [@DeMattia2026Cim], e questa tesina ne riprende l'impostazione ampliandola.

Questo capitolo mostra come il sistema è costruito e perché è costruito così. Il linguaggio YAML, il grano, le voci e i renderer sono trattati nei capitoli successivi; qui interessa il disegno d'insieme e le scelte che lo tengono in piedi. Sono quattro. Chi decide *che cosa* suonare non sa *come* un programma di sintesi lo scrive. Il motore è usabile sia da riga di comando sia come libreria. Aggiungere un renderer, una finestra o una strategia non richiede di modificare il nucleo. Le composizioni sono riproducibili.

Il pacchetto `pge` conta circa 26 000 righe di Python, divise in nove sotto-pacchetti, ed è accompagnato da più di 160 file di test.

<!-- DA INSERIRE: schema della pipeline come figura (docs/images/pipeline.png) -->

## La pipeline: dal file YAML al suono

Il flusso dei dati ha un solo verso. Un file di configurazione attraversa quattro trasformazioni prima di diventare audio.

```text
configs/brano.yml
      |
      v
  Generator            legge e preprocessa lo YAML, crea gli Stream
      |
      v
  Stream (uno per ogni stream del brano)
      |  generate_grains()
      v
  Grain (liste di grani, una per voce)
      |
      v
  RenderingEngine --> AudioRenderer --> output/brano.aif
                           |
                           +--> Csound | NumPy | SuperCollider
```

**Il `Generator`** (`engine/generator.py`) è l'orchestratore. Legge il file YAML, risolve gli stream importati da altri file con la chiave `file:`, valuta le espressioni matematiche scritte nei valori (per esempio `(pi)` o `(10/3)`), applica la regola solo/mute e crea un oggetto `Stream` per ogni stream rimasto. Se il brano dichiara un seme casuale, o se ne viene fissato uno per la sessione, il `Generator` lo propaga a tutti i componenti stocastici.

**Lo `Stream`** (`core/stream.py`) è l'unità compositiva. Alla costruzione riceve i parametri letti dallo YAML e li distribuisce a collaboratori specializzati: la configurazione del processo, i controller di densità, altezza, puntatore e finestra, e il gestore delle voci. Lo `Stream` coordina e non contiene la logica di ciascun parametro; ne è l'orchestratore.

I grani non vengono generati alla costruzione. La generazione è *pigra*: avviene al primo accesso a `stream.voices` e si compone di un ciclo temporale. Per ogni voce il sistema tiene un cursore del tempo. A ogni passo calcola l'intervallo tra due onset successivi a partire dalla densità e dalla durata del grano, e crea un grano per ogni voce attiva. La densità è quindi un parametro che varia nel tempo, ed è così che lo stream può accelerare, rarefarsi o addensarsi. Il numero di voci può essere frazionario: la voce di confine non si accende di colpo ma sale e scende di volume. La lista dei grani passa infine per una strategia di *clip*, che decide che cosa fare dei grani che sporgerebbero oltre la fine dello stream.

La ragione della pigrizia è pratica. Quando il sistema lavora per stem con la cache attiva, uno stream non modificato non ha bisogno di essere rigenerato, e la generazione dei grani è la parte più costosa del lavoro. Il renderer controlla la cache *prima* di leggere `.voices` e, se lo stream è invariato, i grani non vengono mai creati.

**Il `Grain`** (`core/grain.py`) è il dato. È un oggetto immutabile con otto campi: istante di inizio, durata, posizione del puntatore nel campione, rapporto di altezza, volume, pan, numero della tabella del campione e numero della tabella della finestra. È dichiarato come `dataclass` congelata con `__slots__`, perché una composizione di durata considerevole produce un numero molto alto di grani e la memoria conta. L'immutabilità serve anche a un'altra cosa: un grano, una volta creato, può passare tra processi diversi senza che nessuno lo alteri.

**Il `RenderingEngine`** (`rendering/`) riceve la lista degli stream e un renderer e produce i file. Lo fa senza sapere se il renderer sia Csound, NumPy o SuperCollider: è il tema dell'ultima sezione di questo capitolo.

## Organizzazione dei moduli

I nove sotto-pacchetti di `pge` seguono la pipeline. La tabella riassume il ruolo di ciascuno.

| Pacchetto | Ruolo |
|-----------|-------|
| `engine` | Il `Generator`: lettura dello YAML, importazione degli stream, regola solo/mute |
| `core` | I tre oggetti centrali: `Stream`, `Grain`, `StreamConfig` |
| `parameters` | Definizione, validazione e lettura dei parametri e dei loro limiti |
| `envelopes` | Gli inviluppi che fanno variare un parametro nel tempo: interpolazioni, segmenti, distribuzione dei punti |
| `controllers` | Densità, altezza, puntatore, finestra e gestione delle voci |
| `strategies` | Le strategie intercambiabili: distribuzione di altezza, onset, puntatore e pan sulle voci, variazione stocastica, clip del grano |
| `rendering` | I renderer, i traduttori verso i linguaggi dei sintetizzatori, la cache, la partitura grafica |
| `export` | Esportazione verso Reaper, Sonic Visualiser e file JSON dei grani |
| `shared` | Ciò che serve a tutti: errori, logger, gestione del seme, utilità |

Il pacchetto `rendering` è di gran lunga il più ampio, con 32 moduli, perché ospita i tre renderer e tutto ciò che sta intorno: la tabella dei campioni, la scrittura delle partiture, la cache incrementale e il visualizzatore.

La dipendenza tra i pacchetti va in una sola direzione. `core` e `controllers` descrivono che cosa suonare e non conoscono alcun programma di sintesi. `rendering` conosce tutto ciò che sta sopra e traduce un grano nel linguaggio del renderer scelto. Questa regola non è soltanto una convenzione: un test legge il codice sorgente come albero sintattico e fallisce se in `Grain`, `FtableManager` o nel catalogo delle finestre compare un letterale che apre una riga di partitura Csound. La regola è quindi imposta dai test.

La storia di questa regola spiega perché esista. In origine un `Grain` sapeva scrivere la propria riga di partitura Csound, e la precisione a otto decimali dell'onset, necessaria perché a 96 kHz un grano può durare un solo campione, era una decisione sul formato di Csound presa dentro il dato. Un secondo renderer testuale non avrebbe avuto altro posto in cui mettere il proprio metodo che accanto al primo. Oggi tutta la sintassi di Csound sta in un unico modulo, `CsoundEmitter`, e `Grain` è soltanto il dato.

## Libreria e interfaccia a riga di comando

PGE nasce come programma da lanciare dalla radice del repository. Con il tempo è diventato anche una libreria che altri progetti importano, e le due esigenze sono diverse. Una riga di comando stampa messaggi, restituisce codici di uscita e può fare scelte di comodo. Una libreria non deve stampare, non deve terminare il processo e non deve decidere al posto di chi la usa.

Il sistema ha perciò due strati. `pge.api` è l'interfaccia programmatica (`load_generator`, `build_renderer`, `render`, `render_file`, le funzioni `export_*`). Non legge `sys.argv`, non chiama `sys.exit` e segnala gli errori con eccezioni; ogni percorso sul disco è un parametro esplicito. `pge.cli` è un guscio sottile che interpreta gli argomenti, stampa e fissa i codici di uscita, e delega tutto il lavoro all'API. Il file `src/main.py` e il comando `pge` sono due ingressi alla stessa CLI.

La differenza tra i due strati sta nelle *politiche*, cioè nei valori predefiniti.

| Decisione | API (valore predefinito) | CLI |
|-----------|--------------------------|-----|
| Processi paralleli | 1, risultato deterministico | automatico (core disponibili meno uno) |
| Renderer | NumPy, nessun programma esterno | Csound, la scelta storica |
| Percorso del file di cache | esplicito | derivato dal nome del file YAML |
| Messaggi a schermo | mai | sempre |

Il punto più delicato è che anche la libreria, nei fatti, scrive a schermo, perché alcuni componenti che orchestra hanno ereditato dei `print()` che fanno parte del protocollo con l'editor grafico del progetto. L'API lo dichiara in un censimento e un test lo verifica sull'output reale. Quando un'interfaccia non può essere del tutto silenziosa, è meglio che il contratto dica esattamente quanto non lo è.

## Estensibilità

L'architettura è pensata perché le estensioni siano *additive*: si aggiunge un file e si registra, senza modificare il nucleo. Il principio è quello detto aperto/chiuso. Si realizza in tre luoghi.

### Renderer e modalità di uscita

Il sistema deve produrre audio con più renderer, e deve poterlo fare in due modi: un file per ogni stream (*stems*) oppure un unico file con tutto il brano (*mix*). Le due scelte sono indipendenti, e il disegno le tiene separate.

```text
RenderingEngine
  |-- AudioRenderer (classe astratta)
  |     |-- CsoundRenderer
  |     |-- NumpyAudioRenderer
  |     `-- SuperColliderRenderer
  |-- NamingStrategy               nomi dei file di uscita
  `-- RenderMode
        |-- StemsRenderMode        un file per stream
        `-- MixRenderMode          un file unico
```

`AudioRenderer` ha due soli metodi: renderizzare un singolo stream in un file, e renderizzare più stream in un file. Il renderer non decide se produrre stems o mix; lo decide il `RenderMode`. Le due scelte si combinano di conseguenza liberamente: ogni renderer funziona con ogni modalità, e un renderer nuovo le eredita entrambe. Nelle modalità stems gli onset sono relativi allo stream, e il file inizia a zero; nel mix sono assoluti, e gli stream si collocano nel tempo del brano.

Il renderer da usare si sceglie in un unico punto, una fabbrica, e l'elenco dei tipi validi si ricava dalla fabbrica stessa. Un renderer nuovo non richiede di aggiornare alcuna lista scritta a mano.

### La sintassi di un renderer sta in un posto solo

Un renderer testuale ha bisogno di un secondo confine, più in basso: chi scrive la sintassi. Per Csound lo fa `CsoundEmitter`, l'unico modulo che scrive righe di partitura. Gli altri moduli decidono l'ordine delle sezioni del file, ma non scrivono una sola riga della sintassi del renderer.

Lo stesso criterio vale per le finestre del grano. Il catalogo descrive una finestra *nei suoi termini*: la forma, i coefficienti, i parametri, la simmetria. Non nomina nessuna routine Csound e nessuna funzione NumPy. Due traduttori ne ricavano la materializzazione, uno per Csound (che produce una tabella con una routine GEN) e uno per NumPy (che produce un array).

Le forme del catalogo sono meno delle finestre. Hamming, Hann, Blackman e Blackman-Harris sono quattro insiemi di coefficienti della stessa forma parametrica, la somma di coseni. Aggiungere una quinta finestra di questa famiglia significa scrivere una riga nel catalogo e nessuna riga nei traduttori.

La ragione di questo disegno è un difetto reale del sistema nelle versioni precedenti. Il catalogo descriveva le finestre dicendo *come Csound le produce*, e il renderer NumPy le reimplementava da zero: due definizioni della stessa finestra, che avevano in comune i nomi e non le forme. Una finestra, `triangle`, passava la validazione dello YAML ed esplodeva a metà del render solo con il renderer NumPy. Per questo oggi una finestra entra nel catalogo soltanto se ogni traduttore sa produrla, e un test lo verifica; la copertura di ciascun traduttore è dichiarata e non scoperta durante il render.

SuperCollider, che è il terzo renderer, non ha un traduttore proprio per le finestre: riceve gli array del traduttore NumPy e li carica come buffer.

### Le strategie e il registro

Molti comportamenti del sistema sono scelte intercambiabili, selezionate per nome nello YAML. Come le voci distribuiscono le altezze (`step`, `chord`, `spectral` e altre), come si spostano nel tempo (`linear`, `geometric`, `stochastic`), come si dispongono nel pan, come si seleziona la finestra, come si applica la variazione stocastica: ciascuna è una *strategia*, una classe che implementa un'interfaccia comune.

Per ognuna di queste famiglie esisteva un piccolo meccanismo di registrazione: un dizionario dal nome alla classe, una funzione per registrare, una fabbrica che cerca il nome e solleva un errore se manca. Il meccanismo era ripetuto in nove moduli, e le copie stavano divergendo nei nomi dei parametri, nelle etichette diagnostiche, nelle convenzioni. Oggi è una classe sola, `StrategyRegistry`, che *è* il dizionario e ne conosce il dominio.

```python
class StrategyRegistry(Dict[str, Type[S]]):
    """Mappa nome -> classe strategy che conosce il proprio dominio."""

    def register(self, name, strategy_class): ...
    def create(self, name, *args, **kwargs): ...
```

Otto famiglie la usano: altezza, onset, puntatore e pan delle voci, selezione della finestra, clip del grano, densità e variazione. Per aggiungere una strategia basta scrivere la classe e registrarla con un nome; lo YAML la riconosce subito, e un nome inesistente produce un errore che elenca i nomi disponibili.

### Gli errori

Gli errori seguono la stessa logica. Derivano tutti da una radice comune, `EngineError`, e portano con sé il contesto utile a chi compone: lo stream in cui è avvenuto, il campo, un suggerimento. Un errore del compositore (un campo mancante, un file di campioni assente) si distingue così da un difetto del programma. Un nome di strategia sbagliato, per esempio, non è un'eccezione generica ma un `StrategyNotFoundError` con l'elenco delle alternative.

## Riproducibilità e verifica

Una composizione generata con elementi casuali ha senso solo se può essere riprodotta. PGE tratta la riproducibilità come un requisito di progetto. Il seme è un parametro del brano; ogni componente stocastico riceve un proprio generatore, derivato dal seme, e uno stream può condividere la sequenza con un altro dichiarando un gruppo comune. A parità di seme e di configurazione, lo stesso YAML produce lo stesso comportamento musicale da ciascun renderer. Il risultato non è identico campione per campione tra Csound e NumPy, perché i due renderer estraggono sequenze casuali indipendenti per i grani stocastici, ma densità, dispersione, traiettoria e distribuzione delle voci coincidono.

Anche il parallelismo del renderer NumPy è subordinato a questo requisito. La *generazione* dei grani, che consuma il generatore casuale, resta in un unico processo, nell'ordine storico. Si parallelizza solo il rendering, cioè la somma dei grani nel buffer di uscita, che è un'operazione senza stato. Con un processo il risultato coincide bit a bit con quello storico; in modalità stems, anche con più processi, ogni stem è identico a quello ottenuto con un processo solo.

Il progetto è sviluppato con test in modo sistematico, con test unitari che si lanciano con `make tests` e test di integrazione sull'intera catena (`make e2e-tests`) per ciascuno dei tre renderer. Ne parla più diffusamente il capitolo sul metodo di sviluppo.
