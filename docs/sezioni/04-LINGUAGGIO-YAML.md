# Il linguaggio di descrizione degli stream

Fin dalle prime esperienze di sintesi granulare al calcolatore, la specifica grano per grano si è mostrata intrattabile oltre poche unità al secondo [@Roads1978]. Comporre con i grani richiede perciò un livello di controllo che descriva il comportamento collettivo della popolazione, spesso per via statistica. La *tendency mask* di Truax assegna a ogni parametro una traiettoria centrale e un margine di deviazione, entro cui il valore di ogni grano è estratto [@Truax1988]. Sistemi come CMask la realizzano con una specifica testuale che il motore traduce in una rappresentazione intermedia, una lista di eventi, resa poi in suono da un sintetizzatore separato [@Bartetzki1997].

PGE segue lo stesso schema e sceglie per la specifica il formato YAML. Le ragioni sono tre. La prima è il versionamento: un file di testo si versiona con *git*, che diventa la documentazione del processo compositivo, e lo stesso testo può essere letto e discusso con un modello linguistico, che può diventare un'interfaccia alternativa. La seconda è che il motore, esposto come libreria, può essere pilotato da un livello compositivo più alto che generi YAML invece di scriverlo a mano. La terza è che la specifica dichiara soltanto la generazione dei grani, separata dal rendering: lo YAML diventa una lista di grani, una rappresentazione intermedia indipendente dal renderer che la consuma. Nel senso di Seeger [@Seeger1958] lo YAML è una notazione *prescrittiva*: un'istruzione data al motore prima del rendering. La partitura grafica, trattata in un capitolo successivo, è invece una notazione *descrittiva*, che documenta ciò che è stato davvero generato e non viene riletta come input.

Questo capitolo descrive il linguaggio, seguendo l'ordine del paper presentato al XXV CIM [@DeMattia2026Cim], da cui sono tratti anche gli esempi: si parte dallo stream minimo e si aggiunge una chiave alla volta. Non è un manuale: la sintassi completa è nel riferimento del progetto (`docs/reference/yaml.md`) e qui si presentano i concetti e le scelte che la rendono coerente.

## Lo stream come unità compositiva

Un brano è un file YAML. Al livello più alto contiene l'elenco degli stream (`streams`) e, facoltativamente, il seme dei processi casuali (`seed`). Ogni stream è un dizionario di coppie chiave-valore, annidabili. Le chiavi dello stream raggruppano i parametri in blocchi che corrispondono ai concetti del capitolo seguente: `grain` per il grano, `pointer` per la posizione di lettura, `pitch` per la trasposizione, `voices` per la molteplicità delle voci.

### Le condizioni minime di esistenza

Uno stream esiste con due soli parametri.

```yaml
streams:
  - stream_id: esempio1
    sample: voice.wav
```

`stream_id` è il nome dello stream, e `sample` è il file audio da granulare. Tutto il resto è facoltativo. Questa configurazione è la trasformazione identica della sorgente: lo stream riproduce il campione con la stessa durata, a guadagno unitario, rigenerandolo grano per grano. La figura seguente mostra la partitura grafica di questo caso. Ogni grano è un poligono posizionato sul tempo dello stream (asse orizzontale) e sulla posizione di lettura nel file (asse verticale). A sinistra, sullo stesso asse verticale, è disegnata la forma d'onda della sorgente. La lente ingrandisce tre grani contigui, in cui si vedono il profilo della finestra e la sovrapposizione fra grani adiacenti.

![Partitura grafica dello stream minimo: il puntatore percorre il file una sola volta, alla velocità del tempo dello stream.](docs/images/identity_map.pdf){width=100%}

### Una notazione differenziale

Ciò che non è scritto è una dichiarazione implicita, data dal valore predefinito del parametro. Il caso più visibile è la coppia `onset` e `duration`.

| Chiave | Se assente | Se dichiarata |
|--------|------------|---------------|
| `onset` | lo stream parte a 0 s, l'origine della timeline | lo stream parte all'istante indicato, in secondi assoluti |
| `duration` | lo stream dura quanto il campione | lo stream dura il tempo indicato, anche più o meno del file |

La scelta ha una ragione espressa nel progetto: a riposo lo stream risintetizza il campione, e l'unica durata non arbitraria è quella del file. Ogni altro valore è una decisione compositiva, e le decisioni compositive devono essere esplicite. Zero non è "niente", è l'origine: uno stream senza `onset` ha una posizione neutra, non indeterminata.

Il costo di questa comodità è dichiarato. Un `onset` cancellato per errore non produce un errore: lo stream si impila silenziosamente a zero. Per `duration` vale lo stesso. Inoltre `duration: 0` non attiva il valore predefinito, ma produce uno stream senza grani.

Due chiavi governano infine la presenza dello stream nel render. `mute` esclude lo stream, `solo` esclude tutti gli altri.

## Parametri, intervalli ed espressioni

Ogni parametro numerico di uno stream accetta indifferentemente un valore fisso o un inviluppo (si veda la sezione seguente). Gli altri modi di scrivere un valore sono due: la banda di variazione e l'espressione matematica.

### La banda di variazione

Molti parametri hanno un parametro compagno con suffisso `_range`, che definisce una banda attorno al valore base. Per ogni grano, il motore estrae il valore del parametro dentro quella banda.

```yaml
grain:
  duration: 0.05
  duration_range: 0.01
```

Il linguaggio distingue quattro concetti, ognuno con la propria chiave, perché tenerli distinti evita ambiguità. La *larghezza* della banda è il valore stesso di `_range`: è sempre la larghezza, mai una semi-ampiezza e mai una deviazione standard. L'*unità* in cui è misurata la larghezza è dichiarata da `<parametro>_range_unit`, per esempio in forma relativa al valore base. La *forma* (`distribution_mode`) dice come la banda viene riempita: uniforme oppure gaussiana. L'*ancora* (`range_anchor`) dice dove cade il valore base nella banda: al centro oppure al minimo.

Con valore base 300 e larghezza 200 le combinazioni danno questi risultati.

| Forma | Ancora | Banda | Dove si addensano i valori |
|-------|--------|-------|----------------------------|
| uniforme | centro | da 200 a 400 | in modo piatto |
| uniforme | minimo | da 300 a 500 | in modo piatto |
| gaussiana | centro | da 200 a 400 | attorno a 300 |
| gaussiana | minimo | da 300 a 500 | attorno a 400 |

La gaussiana è troncata: la deviazione standard è un sesto della larghezza, dunque i bordi della banda cadono a tre sigma dalla media, e la piccola coda che li supererebbe (circa lo 0,3%) è appiattita sull'estremo. Nessun valore esce dalla banda dichiarata.

Questo è il meccanismo della tendency mask, nella forma in cui lo descrive Truax [@Truax1988, p. 17]: un intervallo che varia nel tempo, da cui si estrae un valore per ogni grano. Come la larghezza della banda possa essere modulata, e come la probabilità che la deviazione si applichi sia un asse indipendente, è l'argomento del capitolo sul grano e sullo stream.

### Espressioni matematiche

Un valore racchiuso tra parentesi è un'espressione, valutata prima che il parser veda il dato.

```yaml
grain:
  duration: (1/20)
pitch:
  ratio: (2**(7/12))        # il rapporto di sette semitoni
```

Sono ammessi gli operatori aritmetici, le funzioni `abs`, `int`, `float`, `min`, `max`, `pow` e le costanti `pi` ed `e`. La valutazione avviene alla lettura del file e non durante il rendering: il risultato è un numero fisso, e l'espressione non è modulabile nel tempo. A questo serve l'inviluppo.

## Envelope: forme, interpolazioni e time mode

Un *envelope* è una funzione del tempo definita a tratti su punti di controllo (*breakpoint*), ciascuno una coppia `[tempo, valore]`. Può comparire al posto di qualunque valore numerico, ed è così che i parametri di uno stream variano nel tempo. Il motore riconosce un inviluppo dalla forma del dato: una lista di coppie, un dizionario con la chiave `points`, o uno dei formati compatti descritti sotto.

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

Il primo elemento è il pattern di un ciclo, con le ascisse espresse da 0 a 100. Il secondo è il tempo assoluto finale del blocco, il terzo il numero di ripetizioni. In questo esempio la durata del grano sale da 0,01 a 0,2 secondi per quattro volte, fino al secondo 30. Il formato compatto accetta anche l'interpolazione, una distribuzione non uniforme delle durate dei cicli e l'opzione di chiudere il ciclo, e può essere mescolato con punti ordinari nella stessa lista.

### Le interpolazioni

Le interpolazioni sono tre.

- **Lineare** (predefinita): i valori fra due punti sono su una retta.
- **Cubica**: curva di Hermite con tangenti calcolate dall'algoritmo di Fritsch-Carlson, che garantisce la monotonia. Se tre punti crescono, la curva non esce dall'intervallo che li contiene. Con due soli punti, dove l'unica informazione è la pendenza, le tangenti agli estremi sono forzate a zero e la curva diventa una S simmetrica, perché altrimenti degenererebbe in una retta. La curva cubica è adatta ad attacchi e rilasci morbidi e a traiettorie dove una derivata seconda continua è udibile.
- **A gradini** (*step*): il valore di un segmento è quello del punto di sinistra fino al punto successivo. Serve ai cambi discontinui e ai parametri che assumono valori interi, come il numero di voci.

### Il tempo: assoluto e normalizzato

Il tempo di un inviluppo si misura in due modi. Con `time_mode: absolute` (il caso predefinito) i punti sono secondi: `[10, 40]` significa "al secondo 10 il valore è 40", qualunque sia la durata dello stream. Con `time_mode: normalized` l'ascissa va da 0 a 1 ed è moltiplicata per la durata dello stream. Un envelope scritto in forma normalizzata mantiene la propria forma se si cambia la durata del brano. La modalità si può impostare per tutto lo stream oppure localmente, dentro il dizionario di un singolo inviluppo.

La normalizzazione riguarda l'asse del tempo degli inviluppi. La posizione dello stream nella timeline, `onset`, è sempre in secondi assoluti.

### Il comportamento ai bordi

Fuori dall'intervallo coperto dai punti, l'inviluppo mantiene il valore del punto più vicino: prima del primo punto vale il primo valore, dopo l'ultimo vale l'ultimo. Uno stream più lungo del suo inviluppo non produce quindi errori. È una scelta voluta, e si legge nella figura seguente.

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

Con `duration: 7.0` e tempo normalizzato i punti cadono a 0,7, 1,05, 2,1 e 3,5 secondi. Il campione dura due secondi, ma lo stream ne dura sette.

![Partitura grafica dell'esempio. In basso l'inviluppo `speed_ratio`, con i valori annotati sui punti; in alto i grani.](docs/images/pointer_map.pdf){width=100%}

La figura mostra che i grani non ricalcano la curva di `speed_ratio`: ne seguono l'*accumulo*. La posizione di lettura è l'integrale della velocità istantanea. Per questo ogni segmento dell'inviluppo sa valutarsi in un punto e anche integrarsi su un intervallo (nel codice, `evaluate` e `integrate`): il puntatore usa la seconda operazione. Poiché lo stream eccede la durata del file, il puntatore esaurisce il buffer attorno a 1,35 secondi e rientra da zero. L'indice di lettura è preso modulo la durata del file, e il salto che si vede nella partitura è una discontinuità di posizione, non il ritorno a zero di una fase che continua ad accumularsi. Dove la velocità è negativa, fra circa 2 e 3,5 secondi, il puntatore percorre il file all'indietro e il verso di lettura interno ai grani si inverte con lui. Dopo l'ultimo punto, la velocità resta a zero (il comportamento ai bordi) e tutti i grani leggono lo stesso punto del file: la posizione si congela.

## Riproducibilità: seme e gruppi

Il seme è una chiave del livello più alto del file.

```yaml
seed: 2026
streams:
  - stream_id: s1
    sample: voice.wav
```

Se è dichiarato, lo stesso YAML produce la stessa realizzazione ad ogni esecuzione, anche su macchine diverse. Se è assente, il motore genera un seme di sessione dall'istante di avvio e lo riporta a schermo: il render non è riproducibile in anticipo, ma resta ricostruibile a posteriori, perché aggiungendo `seed: N` al file si riottiene lo stesso risultato. Anche `seed: 0` è un valore valido, distinto dall'assenza della chiave.

Il seme non alimenta un generatore globale. Ogni sito stocastico ha il proprio generatore, derivato da un hash del seme, dell'identità dello stream e del nome del componente: la variazione della durata del grano, il gate di probabilità di ciascun parametro, la distribuzione degli intervalli fra onset, la scelta della finestra, il detune implicito. Il risultato più utile per chi compone è l'isolamento. Mettere uno stream in `solo` fa ascoltare esattamente ciò che suona nel mix, perché i grani degli altri stream non vengono toccati. Modificare uno stream lascia intatti i grani di tutti gli altri. Anche le voci stocastiche hanno un generatore proprio, derivato dal seme, dallo stream e dall'indice della voce.

L'identità del generatore è per impostazione predefinita lo `stream_id`, quindi due stream non pescano mai la stessa sequenza, nemmeno con lo stesso seme. La chiave `rng_group` sostituisce lo `stream_id` in questa derivazione: gli stream che dichiarano lo stesso gruppo condividono le sequenze casuali di tutti i componenti.

```yaml
seed: 1988
streams:
  - stream_id: cugini_1
    rng_group: cugini
  - stream_id: cugini_2
    rng_group: cugini
```

Questo serve quando più stream vanno letti come un unico oggetto, per esempio più stream distribuiti su posizione e pan con la stessa griglia stocastica. Condividere la sequenza non significa condividere la griglia temporale: gli intervalli fra onset dipendono anche dalla densità, e con densità diverse i due stream si sfasano subito pur pescando dalla stessa sequenza.

Resta un limite dichiarato. Il seme governa il generatore di Python, quindi il renderer NumPy. Csound ha un generatore proprio: con il renderer Csound i due non sono identici bit per bit nemmeno a parità di seme. L'obiettivo è riprodurre la stessa realizzazione, non l'identità tra renderer.

## Stream come file

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

La divisione dei compiti segue una regola: ogni chiave ha una sola casa. Accanto a `file:` il master può tenere soltanto il piazzamento, cioè `stream_id`, `onset`, `mute` e `solo`; qualsiasi altra chiave è un errore che nomina il master, la voce e la chiave. Del file importato si legge lo stream. Il laboratorio può scrivere `onset: 0` e un proprio `stream_id` perché il file si renda da solo, ma nel brano le decisioni di piazzamento sono del master. Il percorso è relativo alla cartella del master. Un file importato contiene un solo stream e non può a sua volta importarne altri, quindi non esistono catene né cicli.

L'importazione è risolta prima di ogni altra elaborazione, e da lì in poi il motore vede una lista di stream come se fossero stati scritti nel master. La cache degli stem lo tratta di conseguenza: spostare uno stream dal master a un file non lo rende da rifare, e modificare il file importato rifà quello stream e nessun altro.

Resta da chiarire cosa succede al suono. Il seme è uno solo, quello del master: se il file importato ne dichiara uno diverso, il render procede con quello del master e il motore avvisa. Dal momento che il generatore di ogni componente deriva da seme e identità, uno stream importato suona come nel laboratorio solo con lo stesso seme e lo stesso `stream_id`. Uno `stream_id` diverso dà un'altra realizzazione dello stesso stream, ed è accettato: importare due volte lo stesso file con due nomi diversi dà due realizzazioni distinte. Chi vuole la realizzazione del laboratorio scrive quell'identificatore accanto a `file:`, oppure dichiara nel file un `rng_group`, che non dipende dal nome con cui il master chiama lo stream.

Il meccanismo permette di lavorare per parti. Ogni stream è sviluppato e ascoltato nel proprio file, e il brano si assembla in un master che li dispone nel tempo e decide quali far suonare.
