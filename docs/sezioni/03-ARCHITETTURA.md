# Architettura di Python Granular Engine

Questo capitolo descrive come PGE è costruito e perché è costruito così. Il disegno ruota attorno a una sola scelta: il motore non produce suono, produce una *lista di grani*, e tutto il resto è lavoro che precede o che segue quella lista. Chi produce la lista non sa come la si trasforma in audio, e chi la consuma non sa come è stata prodotta; aggiungere un consumatore, una strategia o una finestra non richiede di toccare chi produce. E poiché ogni scelta casuale viene presa in produzione e soltanto lì, la stessa specifica dà la stessa lista. La versione descritta è la 9.1.0 [@DeMattia2026Pge], con le modifiche non ancora rilasciate fino al commit `1188dbc` del 13 ottobre 2026, fra cui la chiave `file:` del capitolo 4. Il pacchetto `pge` conta circa 26 400 righe di Python in nove sotto-pacchetti, con 164 file di test.

## La pipeline: dal file YAML al suono

Un brano attraversa tre fasi, che la figura mette in fila. La prima costruisce gli oggetti: legge lo YAML e crea uno `Stream` per ogni stream dichiarato. La seconda genera i grani di ciascuno stream. La terza consuma la lista dei grani e la trasforma in audio, in un'immagine o in un file di scambio. I dati scorrono in un solo verso, dall'alto in basso; la richiesta di lavoro che mette in moto la seconda fase corre invece in verso opposto, ed è ciò che permette di tenere distinte le prime due fasi.

![La pipeline di PGE. Le frecce piene portano i dati dal file YAML ai file di uscita; quella tratteggiata porta in senso contrario la richiesta che innesca la generazione dei grani. Reaper e Sonic Visualiser leggono i parametri dello stream, non la lista dei grani.](docs/images/pipeline.pdf){width=70%}

Il `Generator` è l'orchestratore: legge il file, ne ricava il seme, applica la regola solo/mute e costruisce uno `Stream` per ogni stream rimasto. Lo `Stream` è l'unità compositiva: alla costruzione legge i propri parametri dallo YAML, li convalida e li affida a collaboratori specializzati (sezione 3.3), ma non ha ancora un solo grano. Alla prima lettura di `stream.voices` la generazione produce la lista: un cursore del tempo per voce, un grano per voce attiva a ogni passo (capitoli 5 e 6). La lista è poi letta da tre tipi di consumatore: i renderer (NumPy, Csound, SuperCollider), che la trasformano in audio e che il `RenderingEngine` coordina senza sapere quale dei tre ha davanti (sezione 3.6); la MAP, che disegna ogni grano nel piano tempo-posizione di lettura; l'esportazione JSON, che scrive i grani di ogni stream. Reaper e Sonic Visualiser non leggono la lista ma i parametri dello stream. Il confine fra produzione e consumo passa dalla lista, ed è per questo che un consumatore si aggiunge senza toccare il resto: la specifica sta a monte, i documenti derivati a valle, e nessuno risale (capitolo 8).

### La generazione lazy

*Lazy evaluation* indica una strategia di calcolo in cui un valore non viene calcolato nel punto in cui è definito, ma soltanto quando qualcuno ne ha bisogno, e il risultato si conserva per i bisogni successivi. Il calcolo si esegue dunque al più una volta, può non eseguirsi mai, e il momento in cui si esegue lo stabilisce chi consuma il risultato: Hughes [@Hughes1989] vi vede ciò che permette di scomporre un programma in un produttore e un consumatore indipendenti. Il prezzo è che il costo si sposta (il primo accesso è più lento, e un errore nato dentro il calcolo compare lì e non alla definizione) e che il calcolo è sicuro soltanto se il suo risultato non dipende dal momento in cui si esegue.

In PGE la lista dei grani di uno stream è lazy: il costruttore di `Stream` lascia vuoto il campo `_voices`, e il calcolo sta dietro una proprietà.

```python
@property
def voices(self) -> List[List[Grain]]:
    """Grani organizzati per voce. Lazy: genera al primo accesso."""
    if not self.generated:
        self.generate_grains()
    return self._voices
```

Chiunque legga `stream.voices` (un renderer, la MAP, un esportatore) innesca la generazione la prima volta e riceve la lista conservata le volte successive. Il vantaggio non è dove si penserebbe: quando il sistema lavora per stem con la cache attiva, il renderer chiede alla cache se lo stream è cambiato *prima* di leggere le voci, e uno stream pulito non genera mai i propri grani (lo verifica lo script `lazy_e_riproducibilita.py`, nella cartella `esempi/architettura` del repository della tesina). Non è però un'ottimizzazione del totale, come mostrano le misure del capitolo 7: se tutti gli stream sono da rifare, il lavoro è quello di una generazione eager, solo spostato in avanti. Le due condizioni del prezzo sono rispettate, perché ogni componente stocastico pesca da un generatore proprio (sezione 3.7) e la validazione dello YAML è eager; resta un caso non chiuso (sezione 3.8).

## Il grano e la tabella dei simboli

La lista dei grani è il punto stretto del disegno: è l'unico oggetto che attraversa il confine fra produzione e consumo, e contiene un tipo solo (`core/grain.py`, qui senza `__slots__`).

```python
@dataclass(frozen=True)
class Grain:
    onset: float
    duration: float
    pointer_pos: float
    pitch_ratio: float
    volume: float
    pan: float
    sample_table: int
    envelope_table: int
```

Il grano è *congelato*: una volta creato nessuno può modificarlo, e quindi la generazione e i consumatori non possono interferire. Contiene soltanto numeri, e un brano come *mare-nostrum* ne ha più di tre milioni (capitolo 10). Il verso di lettura non ha un campo proprio, è il segno di `pitch_ratio`. Un grano non porta il nome del suo campione né della sua finestra, ma un indice, il cui significato sta in una tabella dei simboli, `FtableManager`, che il `Generator` riempie alla costruzione: Csound la materializza come tabelle di funzione nello score, NumPy come array, SuperCollider come buffer. È la stessa idea della tabella dei simboli di un compilatore: i nomi si risolvono una volta, fuori dal dato, e il dato resta leggero e neutro rispetto a chi lo consuma. La lista è una `List[List[Grain]]`, una lista per voce, e `stream.voices` è l'unica fonte di verità sui grani esistenti.

## Dallo YAML al valore: il parametro

Il grano si ottiene interrogando i parametri dello stream a un dato istante. La costruzione dei parametri è guidata dai dati: una lista di specifiche dichiarative dice dove ciascuno sta nello YAML e una tabella ne dice i limiti, per cui aggiungere un parametro allo stream è una riga di limiti e una specifica. Il `Parameter` è l'oggetto in cui il linguaggio del capitolo 4 diventa comportamento, e il suo metodo `get_value(time)` è l'unico che il resto del programma deve chiamare. I passi sono cinque: il valore centrale si ricava da un numero o da un inviluppo; la banda di variazione si calcola nello stesso istante; il gate di probabilità decide se *questo* grano devia; se devia, una strategia di variazione estrae un valore dentro la banda con la forma di distribuzione scelta; un limite di sicurezza riporta il risultato nel dominio del parametro. È la maschera di tendenza di Truax [@Truax1988] resa come oggetto. Il caso entra in due punti per parametro, il gate e la distribuzione, e ciascuno riceve alla costruzione un generatore proprio (sezione 3.7). Puntatore, altezza, densità e finestra sono comportamenti più che parametri, e hanno un controller ciascuno; le voci hanno un `VoiceManager` (capitolo 6). Tutti convergono in `Stream._create_grain`, che compone il grano campo per campo.

## Organizzazione dei moduli

Il codice si divide in nove sotto-pacchetti (`engine`, `core`, `parameters`, `envelopes`, `controllers`, `strategies`, `rendering`, `export`, `shared`), più `api.py` e `cli.py`. I pacchetti non sono strati, e non lo si afferma per comodità: lo script `dipendenze.py`, nella cartella `esempi/architettura`, costruisce il grafo degli import leggendo i sorgenti come alberi sintattici. Tra i 97 file Python del commit descritto non c'è nessun ciclo di import, mentre tra i pacchetti cinque coppie si importano a vicenda, perché un pacchetto raccoglie cose dello stesso genere e non dello stesso livello. Ciò che regge a ogni livello è un confine solo: nessuno dei sei pacchetti in basso (`core`, `controllers`, `parameters`, `strategies`, `envelopes`, `shared`) importa `rendering`, `engine`, `export`, `api` o `cli`. I renderer conoscono il grano; il grano non conosce i renderer. Nella forma più stretta il confine è imposto da un test: la sintassi di Csound non deve comparire sotto il livello dei renderer, e il test legge otto moduli come alberi sintattici e fallisce se uno apre una riga di score. All'origine un `Grain` sapeva scrivere la propria riga di score, compresa la precisione a otto decimali dell'onset, necessaria perché a 96 kHz un grano può durare un solo campione; oggi la decisione sta in un modulo solo, `CsoundEmitter`. È il criterio che Parnas [@Parnas1972] propone per scomporre un sistema: non secondo i passi dell'elaborazione, ma secondo le decisioni di progetto che è probabile cambino, ciascuna nascosta in un modulo.

## Libreria e riga di comando

PGE nasce come programma da lanciare dalla radice del repository e con il tempo è diventato anche una libreria che altri progetti importano, e le due esigenze sono diverse: una riga di comando stampa e restituisce codici di uscita, una libreria non deve stampare né terminare il processo. Il sistema ha perciò due strati: `pge.api`, l'interfaccia programmatica, che segnala gli errori con eccezioni e non legge `sys.argv`, e `pge.cli`, un guscio sottile che interpreta gli argomenti e delega tutto il lavoro all'API.

## Estensibilità

L'architettura è pensata perché le estensioni siano *additive* rispetto al nucleo: si scrive un file e lo si registra, senza modificare `core`, `controllers` e `parameters`. È il principio *aperto/chiuso* [@Meyer1988], e i meccanismi sono quelli dei pattern classici [@Gamma1994]: *facade* per il `RenderingEngine`, *strategy* per le modalità e le strategie, *factory* per la scelta del renderer. Un renderer nuovo implementa un'interfaccia con due metodi, uno che rende uno stream in un file e uno che rende più stream in un file, e la modalità (un file per ogni stream, gli *stem*, oppure un unico file con tutto il brano, il *mix*) è un oggetto a parte: ogni renderer funziona con ogni modalità. Qui, però, la modifica sfiora il perimetro, perché l'elenco dei renderer validi sta in una fabbrica e la documentazione prescrive, oltre al file nuovo, tre modifiche ai bordi: il disegno è additivo per il nucleo e non per il perimetro. Il catalogo delle finestre descrive una finestra *nei suoi termini* (forma, coefficienti, simmetria) senza nominare routine Csound né funzioni NumPy, e due traduttori ne ricavano la materializzazione; la ragione è un difetto reale delle versioni precedenti, in cui `triangle` passava la validazione dello YAML ed esplodeva a metà rendering solo con NumPy. Le scelte intercambiabili selezionate per nome nello YAML sono *strategie*, raccolte per famiglia in un registro dal nome alla classe: per aggiungerne una basta scrivere la classe e registrarla.

## Riproducibilità e verifica

Una composizione generata con elementi casuali ha senso solo se può essere riprodotta, e PGE ne fa un requisito di progetto: la specifica con il seme dichiarato è il documento che si versiona, e l'audio si rigenera da essa. Per questo nessun componente pesca da un generatore casuale globale. Ogni sito stocastico (la variazione di un parametro, il gate di probabilità, l'intervallo asincrono fra i grani, la selezione della finestra) ottiene un proprio generatore, derivato dal seme, dall'identità dello stream e dal nome del componente con SHA-256 e non con la funzione `hash()` di Python, che su una stringa cambia da un processo all'altro. Se lo YAML non dichiara un seme, il `Generator` ne ricava uno dall'orologio e lo stampa, e il brano resta ricostruibile a posteriori. Lo script `lazy_e_riproducibilita.py` verifica che, per un brano di tre stream con il seme dichiarato, i grani siano gli stessi in tre processi con `PYTHONHASHSEED` diverso (la stessa impronta su 662 grani), che non cambino se gli stream si generano in ordine inverso né se un altro stream è in mute, e che cambino con un altro seme. La casualità sta tutta nella generazione: i renderer sono funzioni pure della lista dei grani. Ne segue che il parallelismo del renderer NumPy può distribuire soltanto la somma dei grani, e che il confronto fra renderer è un controllo: due renderer che ricevono lo stesso YAML con lo stesso seme ricevono la stessa lista, e se i loro file differiscono la differenza sta nel DSP e mai in una scelta casuale (capitolo 7).

## Che cosa il disegno lascia aperto

Quattro punti non sono risolti, e ciascuno è il rovescio di una scelta descritta sopra. Il primo è la taglia di `Stream`: con oltre 1 100 righe è il secondo modulo del pacchetto per lunghezza, e la documentazione di PGE registra la decisione di *non* scomporlo, perché per la generazione e per il collegamento dei collaboratori un modulo separato avrebbe avuto in ingresso lo `Stream` intero, e il codice si sarebbe spostato senza che cambiasse l'accoppiamento. Il secondo è un accoppiamento nel tempo: il `Generator` assegna a ogni stream la tabella dei campioni e quella delle finestre *dopo* la costruzione, e uno `Stream` costruito da solo si costruisce senza errori e fallisce soltanto al primo accesso a `.voices`, perché la generazione lazy sposta l'errore dal costruttore al primo accesso. Il terzo è un residuo storico: il `Generator` importa `FtableManager` e `ScoreWriter` dal pacchetto `rendering`, e il confine della sezione 3.4 è completo per `Grain` e per `Stream` e non per il `Generator`. Il quarto è il numero di canali: il grano ha un pan in gradi, che non impone il numero di canali di uscita, ma i tre renderer producono oggi file stereofonici.
