# Il rendering audio

Finora i capitoli hanno seguito la costruzione dei grani. Al termine della fase algoritmica il motore possiede una lista di oggetti `Grain`, ciascuno con otto campi, e nessun campione audio. Il rendering trasforma quella lista in un file. Il sistema offre tre modi di farlo, e questo capitolo li descrive uno per uno: due traducono la lista in un linguaggio di sintesi esterno (Csound e SuperCollider), uno la rende direttamente in Python (NumPy). Segue la parte pratica, cioè il modo in cui il lavoro già fatto non si ripete (la cache) e quanto costa il lavoro che resta (il modello di costo).

## Tre motori, un solo grano

I tre renderer non sono tre varianti dello stesso programma. Condividono la lista di grani e la definizione di che cosa un grano sia, e questo è quanto basta a renderli intercambiabili. Il DSP di un grano è lo stesso in ogni motore, ed è breve:

1. Si legge il campione sorgente a partire dalla posizione `pointer_pos`, avanzando di `pitch_ratio` campioni sorgente per campione di uscita.
2. Si moltiplica la lettura per la finestra, stirata sulla durata del grano.
3. Si moltiplica per l'ampiezza, ricavata dal volume in decibel: $A = 10^{v/20}$.
4. Si distribuisce il risultato sui due canali con la matrice Mid-Side del capitolo 5, a potenza costante:

$$ L = \frac{s\cos\theta + s\sin\theta}{\sqrt{2}}, \qquad R = \frac{s\cos\theta - s\sin\theta}{\sqrt{2}} $$

dove $s$ è il grano finestrato e $\theta$ l'angolo `pan` in radianti. La somma $L^2 + R^2 = s^2$ non dipende da $\theta$, e per questo la potenza del grano resta la stessa in qualunque posizione.

Il risultato è la somma, in un buffer stereo, di tutti i grani posti al loro onset: un *overlap-add*. Quello che cambia da un motore all'altro è chi esegue questi quattro passi e dove vive la descrizione dell'operazione.

Un motore solo avrebbe bastato a produrre un suono. I tre motori servono a un altro scopo: rendere il rendering falsificabile. Con due motori, quando divergono non c'è un terzo parere, e quando concordano non si sa se hanno ragione o se condividono lo stesso assunto. Un terzo motore, scritto con strumenti diversi, toglie entrambe le incertezze. Nel capitolo 3 l'indipendenza del nucleo dal renderer appariva come un principio di ordine. Qui è la condizione che rende possibile questo controllo.

## Csound: generazione della partitura

Csound è il renderer storico del sistema. Generare la partitura Csound con un programma, invece di scriverla a mano, ha un precedente diretto in CMask, che produce partiture per la sintesi granulare [@Bartetzki1997]. In PGE il file `.sco` è un artefatto di compilazione e non il documento che il compositore scrive: il documento è lo YAML.

Il `.sco` prodotto per l'esempio minimo del capitolo 4 (`esempi/identity/identity.yml`, poche righe di YAML) ha tre parti. La prima descrive le tabelle di funzione:

```
; Sample: voice.wav
f 1 0 0 1 "voice.wav" 0 0 1

; Window: hanning - Hanning/von Hann window
f 2 0 1024 20 2 1
```

La tabella 1 contiene il file audio sorgente (routine GEN01, che legge un file). La tabella 2 contiene la finestra di Hann, 1024 punti generati dalla routine GEN20. La seconda parte è un evento per ciascun grano:

```
i "Grain" 0.00000000 0.05000000 0.000000 1.000000 0.00 0.000 1 2
i "Grain" 0.02500000 0.05000000 0.025000 1.000000 0.00 0.000 1 2
i "Grain" 0.05000000 0.05000000 0.050000 1.000000 0.00 0.000 1 2
```

Le colonne sono, nell'ordine, onset e durata in secondi, posizione di lettura nel sample in secondi, rapporto di altezza, volume in decibel, pan in gradi, numero della tabella del sample e numero della tabella della finestra: gli otto campi del `Grain`, più il nome dello strumento. La terza parte è l'istruzione di fine, `e`. Il file dell'esempio conta 78 grani su 111 righe, intestazioni comprese.

La partitura non contiene alcun codice di sintesi. Il lavoro vero lo fa l'orchestra `csound/main.orc`, un file scritto una volta e a mano, che il sistema non genera. Lo strumento `Grain` è in sostanza i quattro passi della prima sezione:

```
iSampleLen = ftlen(iSampleTable) / ftsr(iSampleTable)
iStartNorm = iStart / iSampleLen
iFreq      = iSpeed / iSampleLen
iAmp       = ampdb(iVolume)

aEnv   = poscil:a(iAmp, 1/p3, iEnvTable)
aSound = poscil:a(aEnv, iFreq, iSampleTable, iStartNorm)

aMid   = aSound*cos(irad)
aSide  = aSound*sin(irad)
aLeft  = (aMid + aSide) / sqrt(2)
aRight = (aMid - aSide) / sqrt(2)
```

Un oscillatore legge la finestra a frequenza $1/d$, dove $d$ è la durata del grano (`p3`): un ciclo della tabella dura quanto il grano. Un secondo oscillatore legge il sample, con fase iniziale pari alla posizione di lettura normalizzata e frequenza pari al rapporto di altezza diviso la durata del sample, quindi la velocità di lettura è `pitch_ratio` volte quella originale. La tabella si legge ciclicamente. Il tasso di controllo dell'orchestra coincide col tasso di campionamento (`ksmps = 1`), per cui un onset può cadere su qualunque campione.

Un dettaglio mostra perché la sintassi di Csound è confinata in un modulo solo. Nel `.sco` onset e durata sono scritti con otto decimali, e non per estetica: a 96 kHz un grano può durare un solo campione, cioè poco più di dieci microsecondi, e un formato più avaro lo troncherebbe. Questa decisione riguarda Csound e nient'altro. Per questo la scrive `CsoundEmitter`, l'unico modulo del motore che conosca la sintassi dello score, e non il `Grain`, come avveniva nelle prime versioni (capitolo 3).

PGE lancia Csound come processo esterno: scrive il `.sco`, invoca `csound` con l'orchestra e riceve il file audio. Nella modalità a stem (un file per stream) produce una partitura per stream, nella modalità mix una sola. Con l'opzione `--keep-sco` la partitura si conserva, ed è il modo più semplice di vedere con precisione quali grani sono stati prodotti.

## NumPy: sintesi diretta per overlap-add

Il renderer NumPy è il motore interno. Non richiede alcun programma esterno, si installa con le dipendenze del pacchetto ed è il renderer predefinito della funzione `render_file` dell'API. `GrainRenderer` è la traduzione in Python dello strumento `Grain`, e il suo codice conserva la tabella delle corrispondenze.

| Csound | NumPy |
|--------|-------|
| `iSampleLen = ftlen/ftsr` | `sample_len_sec = len(samples)/file_sr` |
| `iStartNorm = iStart/iSampleLen` | `start_norm = pointer_pos/sample_len_sec` |
| `iFreq = iSpeed/iSampleLen` | `increment = pitch_ratio·file_sr/output_sr` |
| `ampdb(iVolume)` | `10**(volume/20)` |
| lettura ciclica con `poscil` | indici modulo la lunghezza, interpolazione lineare |
| matrice Mid-Side con `cos`, `sin` | identica |

Un grano diventa un array stereo, lungo quanto la durata moltiplicata per la frequenza di campionamento. Il calcolo è una funzione pura: non legge né scrive stato e non estrae numeri casuali. Questa purezza rende il rendering parallelizzabile.

Il rendering di uno stream procede così. Si alloca un buffer stereo in doppia precisione, lungo quanto serve per contenere l'ultimo grano. Per ogni grano si calcola il campione di partenza a partire dall'onset (relativo allo stream nella modalità stem, assoluto nella modalità mix) e si somma il grano nel buffer. Poi il buffer attraversa due passi prima di essere scritto con `soundfile`: la rimozione dell'offset in continua e un clip tra $-1$ e $1$.

La somma di molti grani finestrati prende dal materiale sorgente anche la sua componente a frequenza zero. Ogni frammento ha in generale media non nulla, e la somma accumula un offset lentamente variabile, che decentra la forma d'onda e riduce il margine dinamico. Il rimedio è sottrarre al segnale la sua media mobile centrata, cioè applicare un filtro FIR a fase lineare con kernel $h = \delta - \frac{1}{N}\mathbf{1}$, la cui risposta in frequenza è nulla a 0 Hz. La media mobile si calcola con una somma cumulativa, in tempo lineare nella lunghezza del segnale, e la lunghezza $N$ della finestra fissa il taglio: il valore predefinito è 20 Hz, che tocca la continua e il subsonico e lascia intatta la banda udibile. La scelta è un compromesso dichiarato, perché un taglio più alto toglierebbe anche le modulazioni d'ampiezza più lente, per esempio gli inviluppi di grani molto lunghi. L'orchestra Csound non contiene un passo equivalente: è una fase propria del renderer NumPy.

I formati di uscita sono tre: AIFF o WAV a 32 bit in virgola mobile, FLAC a 24 bit. Quello predefinito è l'AIFF in virgola mobile. Nella catena non c'è normalizzazione: il livello è quello che i volumi dei grani determinano, e il clip a $\pm 1$ è l'unica protezione.

### Parallelismo senza perdere la riproducibilità

Con migliaia di grani l'overlap-add diventa il costo dominante. Il renderer può distribuirlo su un pool di processi, e il numero di worker si sceglie con l'opzione `--jobs` (`auto` usa i core disponibili meno uno). La difficoltà non è il parallelismo in sé, ma il suo rapporto con la riproducibilità del capitolo 3. La *generazione* dei grani, che consuma numeri casuali, resta in un solo processo, e solo la *somma* dei grani, un'operazione senza stato, si distribuisce. La documentazione del codice motiva la scelta con l'ordine di consumo di un generatore casuale globale. Da quando ogni componente stocastico pesca da un generatore proprio, derivato dal seme, l'ordine in cui gli stream si generano non cambia i grani (capitolo 3), e la scelta non discende più da quella condizione.

La distribuzione ha due livelli. Con più stream da rendere in stem, ogni stream è un compito per il pool, e il lavoro (somma, rimozione della continua, scrittura) gira per intero nel worker. Con uno stream solo, molto denso, i grani si ordinano per onset e si dividono in blocchi contigui nel tempo: ogni worker somma il proprio blocco in un buffer locale, e il processo principale compone i buffer nell'ordine dei blocchi. Il pool si avvia soltanto sopra una soglia di 1024 grani per chiamata, perché sotto non conviene: l'avvio dei processi costa circa un secondo, contro i 40 millisecondi di un rendering sequenziale di mille grani.

Il contratto di determinismo è questo:

- con `--jobs 1` i campioni coincidono bit a bit con quelli del rendering sequenziale originario;
- a parità di `--jobs`, due esecuzioni producono gli stessi campioni;
- tra valori diversi di `--jobs` cambia soltanto l'ordine delle somme in doppia precisione, e la differenza massima sta sotto un bit meno significativo a 24 bit, quindi non è udibile;
- in modalità stem, anche con più processi, ogni stem coincide con quello ottenuto con un processo solo.

## SuperCollider in modalità non real-time

SuperCollider è il terzo motore. La scelta non nasce dal bisogno di un suono diverso: nasce dalla funzione di controllo descritta all'inizio del capitolo. SuperCollider rende già in non-realtime, senza meccanismi sperimentali: `scsynth -N` legge uno score da file e scrive il risultato in un file audio, senza passare per una scheda audio.

Il problema, perciò, non era far suonare SuperCollider. Era non introdurre un terzo comportamento. Un motore nuovo che reimplementa le finestre, la conversione dei decibel o la soglia dei grani cortissimi aggiunge un dialetto, e non un controllo. Il disegno risolve la questione spostando le decisioni dalla SynthDef allo score, e quindi su Python, dove esistono già.

La catena ricalca quella di Csound con un serializzatore diverso:

```
Stream -> SuperColliderScoreWriter -> .osc -> scsynth -N -> .aif
```

Uno score non-realtime di SuperCollider è una sequenza di bundle OSC ordinati nel tempo, ognuno preceduto dalla propria lunghezza. La struttura è quella del `.sco`, in forma binaria: prima le tabelle, poi un evento per grano.

| `.sco` Csound | `.osc` SuperCollider |
|---|---|
| `f 1 0 0 1 "voice.wav" 0 0 1` | `/b_allocReadChannel 1 "/percorso/voice.wav" 0 0 0` |
| `f 2 0 1024 20 2 1` | `/b_alloc 2 4096 1` seguito da `/b_setn 2 ...` |
| `i "Grain" 0.5 0.05 ...` | `/s_new "pgeGrain" 1000 0 0 ...` |
| `e` | `/c_set 0 0` al tempo finale |

Tre decisioni, prese nello score e non nella SynthDef, tengono il backend allineato a NumPy invece che parallelo ad esso:

1. **Le finestre sono tabelle riempite dal registro delle finestre di NumPy**, lo stesso che usa il renderer NumPy. Non esiste un catalogo SuperCollider: due cataloghi possono divergere, uno solo no. Le finestre del catalogo sono campionate su $k/(n-1)$, e la SynthDef percorre la tabella da zero all'ultimo punto nell'arco del grano, dunque legge gli stessi valori a meno dell'interpolazione.
2. **Sotto i 10 campioni la finestra non si applica**, come nel renderer NumPy: un grano di pochi campioni non ha una forma che la finestra possa modellare. Qui è lo score a decidere, perché la lunghezza del grano la conosce solo lui: i grani troppo corti puntano a un buffer piatto. Csound conserva su questo punto una differenza nota: legge comunque la tabella da 1024 punti, anche a pochi campioni.
3. **Le conversioni di unità si fanno in Python.** I decibel diventano ampiezza lineare con $10^{v/20}$ e i gradi diventano radianti prima di entrare nello score. La SynthDef ha due UGen in meno e non c'è un posto in più dove sbagliare.

L'unico pezzo nuovo è la SynthDef del grano (`supercollider/pge_grain.scd`), l'omologo dell'orchestra Csound, versionata come sorgente leggibile. Il `.scsyndef` compilato è un artefatto di build, che si rigenera quando manca o quando il sorgente è più recente, con la regola di un Makefile; i suoi byte viaggiano dentro lo score (`/d_recv`), così il `.osc` è autosufficiente.

Due scelte di configurazione meritano una nota perché un valore sbagliato non dà errore. Il *block size* vale 1, per avere onset con precisione di campione, come `ksmps = 1` in Csound; con il valore normale di `scsynth`, 64, gli onset si quantizzerebbero a 1,33 millisecondi a 48 kHz. Il numero massimo di nodi vale 32 768, perché `scsynth` ne ammette 1024 per default, e una densità alta con grani lunghi li supera e interrompe il rendering a metà.

Resta la lezione operativa del backend. `scsynth` esce con codice zero anche quando non ha reso niente: con un sample mancante il buffer è vuoto e l'audio è puro silenzio, con i nodi esauriti i grani spariscono uno a uno. Il compilatore `sclang`, su macOS, fa l'opposto e non termina da solo dopo aver scritto il file. In entrambi i casi il codice d'uscita non dice la verità; la dice l'artefatto. Il renderer cerca perciò nell'output i marcatori dei guasti e verifica che il file audio esista e non sia vuoto, e per la SynthDef attende la comparsa del `.scsyndef` invece della fine del processo. Senza questi controlli SuperCollider sarebbe l'unico backend a restituire silenzio annunciandolo come suono: Csound in quei casi esce con errore e NumPy solleva un'eccezione.

## Cache degli stream e costo computazionale

Rendere una composizione intera costa. Modificare un solo stream e doverla rifare da capo rende lenta la composizione iterativa, che consiste proprio nel ritoccare. La cache incrementale risolve questo caso.

### Il fingerprint

La cache funziona per stream, in modalità stem, ed è disponibile con tutti e tre i renderer. Per ogni stream il sistema calcola un'impronta (*fingerprint*) SHA-256 del dizionario YAML dello stream e la confronta con quella salvata nel manifesto `cache/<nome>.json` dopo l'ultimo rendering riuscito. Uno stream è *sporco* (*dirty*) se l'impronta è cambiata, se manca dal manifesto o se il suo file audio non esiste più. Altrimenti il rendering lo salta. In modalità mix la cache non agisce, perché il mix è atomico: manca la granularità per stream.

L'impronta non è soltanto il testo dello stream. Entrano nel calcolo le cose da cui lo stem dipende e che lo YAML non dichiara:

- la versione delle regole con cui il motore interpreta la variazione dei parametri;
- il renderer, perché lo stesso stream reso con un altro motore è un altro stem (senza, passare da Csound a NumPy lascerebbe ogni stream *pulito* e l'audio del primo motore verrebbe dichiarato come del secondo);
- il seme, ma solo se il documento lo dichiara, perché ogni generatore del motore deriva da seme, gruppo e componente, e quindi cambiare seme cambia gli stem. Se il documento tace, il motore pesca un seme di sessione diverso a ogni esecuzione, e metterlo nell'impronta invaliderebbe ogni stem a ogni rendering.

Le chiavi `solo` e `mute` sono invece escluse: attivarle cambia *quali* stream si renderizzano, non il contenuto di quello dello stream. Uno stream importato con `file:` arriva all'impronta già risolto, cioè scritto per intero come se fosse nel master: modificare il file importato sporca soltanto quello stream, e spostare uno stream dal master a un file non lo sporca.

A ogni rendering il sistema esegue prima una raccolta dei rifiuti (*garbage collection*): toglie dal manifesto gli stream che non sono più nello YAML e cancella i loro file audio orfani. Poi, per ciascuno stream, controlla la cache e rende soltanto quelli sporchi. Il controllo avviene *prima* di leggere le voci dello stream, e per questo un stream pulito non genera mai i propri grani: è la ragione della generazione *lazy* descritta nel capitolo 3.

La cache ha due limiti che l'impronta non può coprire, perché dipendono da cose che lo YAML non nomina. La prima è il codice del DSP scritto a mano: l'impronta sa *quale* renderer ha reso lo stem, non *quale versione* della sua orchestra o della sua SynthDef. Modificarle lascia gli stem *puliti*, e occorre cancellarli. La seconda è il contenuto del file sorgente: se il file audio cambia e lo YAML no, lo stream resta pulito.

### Quanto costa un rendering

La domanda pratica di chi compone in tempo differito è quanto ci voglia, e la risposta ingenua sbaglia in entrambi i versi. Non è «quanto dura il pezzo», perché il motore non simula lo scorrere del tempo: somma segmenti. Ma non è nemmeno «il numero di grani», perché il buffer di uscita va comunque allocato, elaborato e scritto, e quel lavoro cresce con i campioni. Il costo ha due termini indipendenti:

$$ t = a\,N + b\,D $$

dove $N$ è il numero di grani e $D$ la durata dell'uscita in secondi. Una regressione ai minimi quadrati su 23 misure, da cento a trentamila grani e da cinque a 320 secondi, su un Apple M2 Max con Python 3.11 e rendering sequenziale, dà:

| Coefficiente | Valore | Che cosa paga |
|---|---|---|
| $a$ | circa 34 µs per grano | costruire il grano, finestrarlo, sommarlo nel buffer |
| $b$ | circa 1,4 ms per secondo di uscita | allocare, elaborare e scrivere il buffer |

L'errore relativo mediano sta sotto l'1%, il massimo intorno al 9% sul punto più piccolo, dove il costo fisso di avvio pesa. Due parametri bastano a coprire tre ordini di grandezza di grani e due di durata. I coefficienti dipendono dalla macchina: su un altro calcolatore cambiano i numeri e non la forma del modello.

I due termini pareggiano a circa 40 grani al secondo. Sotto quella densità comanda la durata, sopra comandano i grani. Il regime granulare d'uso sta ben sopra: a densità 100 il termine dei grani pesa 2,4 volte quello della durata, a densità 800 venti volte. Nella pratica, quindi, il costo lo governa la popolazione dei grani e non la lunghezza del brano. Non è un enunciato assoluto: a parità di grani, allungare l'uscita da 5 a 320 secondi quadruplica il tempo.

Due rendering reali mostrano come si ripartisce il tempo. La costruzione degli oggetti `Grain` è stata separata dall'overlap-add forzando la generazione prima del rendering:

| Materiale | Grani | Durata | Costruzione | Overlap-add e scrittura | Totale |
|---|---|---|---|---|---|
| `PGE_ff2_rassegna.yml` | 221 082 | 1 698 s | 1,72 s | 13,11 s | 14,95 s |
| `PGE_cim.yml` | 994 555 | 92,5 s | 9,73 s | 20,45 s | 30,22 s |

I due casi hanno il rapporto tra grani e durata rovesciato: 130 grani al secondo il primo, oltre diecimila il secondo. La quota di costruzione cambia di conseguenza: un ottavo del totale nel primo caso, quasi un terzo nel secondo. Nel regime denso, materializzare la popolazione dei grani costa quanto una parte consistente della sintesi. È il prezzo del disegno del capitolo 3. La lista di grani esiste come oggetto ispezionabile prima di diventare campioni, e questo rende possibili la MAP, le esportazioni e il debugging. In memoria ogni grano pesa circa 225 byte: 50 MB per il primo materiale, 224 MB per il secondo.

Le misure sono tutte a un processo solo (`--jobs 1`); il parallelismo descritto sopra agisce sull'overlap-add, cioè sulla parte di sintesi del termine $a$. Non sono incluse l'esportazione della MAP e delle altre rappresentazioni, che consumano la stessa lista con un costo proprio, né l'avvio del processo, circa 0,3 secondi per l'importazione di NumPy e matplotlib, che su un rendering breve non è trascurabile.

Le misure si riproducono con `make bench`, che stampa i tre sweep e i coefficienti, e con `make bench YAML=...` per un caso di riferimento. Lo script è anche il metodo con cui si controlla che una modifica non peggiori il rendering: un cambiamento alla costruzione del grano o all'overlap-add si vede sul coefficiente $a$, uno alla scrittura del file sul coefficiente $b$.
