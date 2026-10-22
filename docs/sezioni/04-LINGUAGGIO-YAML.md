# Il linguaggio di descrizione degli stream

Questo capitolo descrive la grammatica del linguaggio con cui si dichiara uno stream, l'ingresso della pipeline del capitolo 3: che forma ha un documento, che forme può assumere un valore, quali proprietà valgono per il documento intero (il seme e l'importazione di stream da altri file). Il vocabolario, cioè che cosa governa ciascuna chiave, è l'argomento dei capitoli 5 e 6. Non è un manuale: la sintassi completa è nel riferimento del progetto (`docs/reference/yaml.md`). Gli esempi vengono dal paper presentato al XXV CIM [@DeMattia2026Cim] e si rieseguono dalla cartella `esempi/`; le affermazioni sul comportamento del motore sono controllate, una per una, dallo script `esempi/linguaggio/verifica_linguaggio.py`.

La scelta di YAML ha tre ragioni e un costo. Un file di testo si versiona con *git* e può essere letto e discusso con un modello linguistico; il motore, esposto come libreria, può essere pilotato da un livello compositivo più alto che generi YAML, come fa il laboratorio del capitolo 10; e la specifica dichiara soltanto la generazione dei grani, separata dal rendering. Il costo è che la sintassi è permissiva: ciò che il motore non riconosce lo lascia passare.

## Lo stream come unità compositiva

Un brano è un file YAML. Al livello più alto il motore legge due chiavi: `streams`, l'elenco degli stream, e, facoltativamente, `seed`, il seme dei processi casuali. A livello dello stream stanno la densità (`density` o `fill_factor`), `distribution`, `volume` e `pan`; gli altri parametri sono raggruppati in blocchi che corrispondono ai concetti dei capitoli seguenti: `grain` per il grano, `pointer` per la posizione di lettura, `pitch` per la trasposizione, `voices` per la molteplicità delle voci. Uno stream esiste con due soli parametri.

```yaml
streams:
  - stream_id: esempio1
    sample: voice.wav
```

`stream_id` è il nome dello stream, e `sample` è il file audio da granulare. Tutto il resto è facoltativo, perché ogni chiave ha un valore predefinito, e i predefiniti sono scelti perché questa configurazione sia la trasformazione identica della sorgente: grani di 50 ms con finestra di Hann, un fattore di riempimento di 2 (un grano ogni 25 ms), volume 0 dB, pan centrale, lettura alla velocità del tempo dello stream, nessuna trasposizione. Con questi valori l'identità è una questione di aritmetica. Due finestre di Hann sfalsate di metà della loro durata sommano a 1, e ogni grano legge il file nel punto in cui è nato, perché la posizione di lettura coincide con l'istante: la somma dei grani ricostruisce dunque la sorgente. È l'identità della lista dei grani, e non del file di uscita: il rendering NumPy a 44,1 kHz restituisce la sorgente con un guadagno di 0,70, perché il pan a potenza costante del capitolo 7 porta un grano centrale a $1/\sqrt{2}$ in ciascun canale.

La figura seguente mostra la MAP di questo caso. Ogni grano è un poligono posizionato sul tempo dello stream (asse orizzontale) e sulla posizione di lettura nel file (asse verticale); a sinistra, sullo stesso asse verticale, è disegnata la forma d'onda della sorgente. La diagonale è l'identità. La lente ingrandisce tre grani contigui, in cui si vedono il profilo della finestra e la sovrapposizione fra grani adiacenti.

![MAP dello stream minimo: il puntatore percorre il file una sola volta, alla velocità del tempo dello stream.](docs/images/identity_map.pdf){width=100%}

Ciò che non è scritto è una dichiarazione implicita, data dal valore predefinito del parametro: è una *notazione differenziale*. Il caso più visibile è la coppia `onset` e `duration`. Se `onset` è assente lo stream parte a 0 s, l'origine della timeline; se è dichiarato, parte all'istante indicato, in secondi assoluti. Se `duration` è assente lo stream dura quanto il campione; se è dichiarata, dura il tempo indicato, anche più o meno del file. La scelta ha una ragione espressa nel progetto: a riposo lo stream risintetizza il campione, e l'unica durata non arbitraria è quella del file; ogni altro valore è una decisione compositiva, e le decisioni compositive devono essere esplicite. Il costo di questa comodità è dichiarato: un `onset` cancellato per errore non produce un errore, lo stream si impila silenziosamente a zero. Un'altra forma che il motore risolve da sé è l'espressione, un valore racchiuso tra parentesi, come `(1/20)` per la durata del grano o `(2**(7/12))` per il rapporto di sette semitoni: il motore la valuta alla lettura del file, e il risultato è un numero fisso, non modulabile nel tempo (a questo serve l'envelope).

## Envelope: forme, interpolazioni e time mode

Un *envelope* è una funzione del tempo definita a tratti su punti di controllo (*breakpoint*), ciascuno una coppia `[tempo, valore]`. Può comparire al posto di qualunque valore numerico, ed è così che i parametri di uno stream variano nel tempo. La forma più comune è la lista di coppie (`density: [[0, 5], [10, 40], [30, 5]]`); quando serve scegliere il tipo di interpolazione, o il modo in cui si misura il tempo, si usa la forma a dizionario.

```yaml
density:
  type: cubic
  points: [[0, 5], [10, 40], [30, 5]]
```

Le interpolazioni sono tre. La **lineare** (predefinita) congiunge i punti con rette. La **cubica** è una curva di Hermite monotona, che fra due punti non esce dall'intervallo dei loro valori (nel profilo dell'esempio il massimo resta 40), adatta ad attacchi e rilasci morbidi. La **a gradini** (*step*) tiene il valore del punto di sinistra fino al successivo, e serve ai cambi discontinui e ai parametri che assumono valori interi, come il numero di voci. Il tempo si misura in due modi: con `time_mode: absolute` (il caso predefinito) i punti sono secondi, con `time_mode: normalized` l'ascissa va da 0 a 1 ed è moltiplicata per la durata dello stream, così che un envelope mantenga la propria forma se si cambia la durata del brano. Fuori dall'intervallo coperto dai punti l'envelope mantiene il valore del punto più vicino, e uno stream più lungo del suo envelope non produce quindi errori: è una scelta voluta.

Un esempio è il parametro `pointer.speed_ratio`, il rapporto tra la velocità con cui il puntatore percorre il file e la velocità del tempo dello stream: i grani non ne ricalcano la curva ma ne seguono l'*accumulo*, perché la posizione di lettura è l'integrale della velocità istantanea, e il puntatore chiede all'envelope `integrate` invece di `evaluate`. Quando la velocità diventa negativa il puntatore percorre il file all'indietro; se resta a zero dopo l'ultimo punto, tutti i grani leggono lo stesso punto del file e la posizione si congela.

## La banda di variazione

Cinque parametri dello stream hanno una banda di variazione, dichiarata da una chiave con `range` nel nome: `volume_range`, `pan_range`, `grain.duration_range`, `pointer.offset_range` e `pitch.range`. La banda sta attorno al valore base, e per ogni grano il motore estrae il valore del parametro dentro di essa. Il linguaggio distingue quattro concetti, ognuno con la propria chiave. La *larghezza* della banda è il valore stesso di `_range`: è sempre la larghezza, mai una semi-ampiezza e mai una deviazione standard. L'*unità* in cui è misurata è assoluta, nell'unità del parametro, oppure relativa al valore base (`grain.duration_range_unit`, solo per la durata del grano, l'unico parametro la cui base spazia per costruzione su più ordini di grandezza). La *forma* (`distribution_mode`) dice come la banda viene riempita, in modo uniforme o gaussiano; la gaussiana è troncata, con la deviazione standard pari a un sesto della larghezza, e nessun valore esce dalla banda dichiarata. L'*ancora* (`range_anchor`) dice dove cade il valore base nella banda: al centro oppure al minimo.

Centro e larghezza sono due valori come tutti gli altri, e ciascuno può essere un numero o un envelope. Quando lo sono entrambi la banda è un'area che si apre e si chiude nel tempo: è la maschera di tendenza, nella forma in cui la descrive Truax [@Truax1988, p. 17], scritta in testo.

```yaml
grain:
  duration: [[0, 0.02], [10, 0.2]]
  duration_range: [[0, 0.0], [10, 0.1]]
```

Qui la durata del grano sale da 20 a 200 millisecondi in dieci secondi e la banda si apre da zero a 100 millisecondi. Il capitolo 5 dice come la probabilità che la deviazione si applichi sia un asse indipendente dall'ampiezza.

## Riproducibilità: seme e gruppi

Il seme è una chiave del livello più alto del file (`seed: 2026`). Se è dichiarato, lo stesso YAML produce la stessa lista di grani a ogni esecuzione, anche in processi diversi, e quindi la stessa realizzazione. Se è assente, il motore genera un seme di sessione e lo riporta a schermo: il render non è riproducibile in anticipo, ma resta ricostruibile a posteriori, aggiungendo `seed: N` al file. Poiché ogni sito stocastico ha il proprio generatore, derivato dal seme, dall'identità dello stream e dal nome del componente (sezione 3.7), il risultato più utile per chi compone è l'isolamento: mettere uno stream in `solo` fa ascoltare esattamente ciò che suona nel mix, e modificare uno stream lascia intatti i grani di tutti gli altri. L'identità del generatore è per impostazione predefinita lo `stream_id`, quindi due stream non pescano mai la stessa sequenza, nemmeno con lo stesso seme; la chiave `rng_group` la sostituisce, e gli stream che dichiarano lo stesso gruppo condividono le sequenze casuali di tutti i componenti.

## Stream come file

Questa sezione descrive il ramo principale del motore: `file:` è successivo alla versione 9.1.0 descritta nel capitolo 3, e non è ancora in una versione rilasciata. Una voce della lista `streams` può essere un riferimento a un altro documento YAML, invece di uno stream scritto per intero. Il documento importato è un file a sé, tipicamente quello di un laboratorio, che si apre e si rende anche da solo; il documento del brano, il *master*, ne decide soltanto il piazzamento.

```yaml
# brano.yml, il master
seed: 1441
streams:
  - file: streams/risacca.yml
    onset: 12.5
    mute: true
```

La divisione dei compiti segue una regola: ogni chiave ha una sola casa. Accanto a `file:` il master può tenere soltanto il piazzamento, cioè `stream_id`, `onset`, `mute` e `solo`; qualsiasi altra chiave è un errore che nomina il master, la voce e la chiave. Se il master non scrive uno `stream_id`, vale il nome del file senza estensione. Il seme è uno solo, quello del master, e poiché il generatore di ogni componente deriva da seme e identità, uno stream importato suona come nel laboratorio solo con lo stesso seme e lo stesso `stream_id`: chi vuole la realizzazione del laboratorio scrive quell'identificatore accanto a `file:`. Il meccanismo permette di lavorare per parti: ogni stream è sviluppato e ascoltato nel proprio file, e il brano si assembla in un master che li dispone nel tempo e decide quali far suonare.

## Che cosa il linguaggio lascia passare

Il linguaggio è permissivo: la notazione differenziale rende comoda la scrittura e paga il prezzo di non protestare davanti a ciò che non riconosce. Un `onset` o una `duration` cancellati diventano l'origine della timeline e la durata del file; `mute: false` muta lo stream, perché la regola conta la presenza della chiave e non il suo valore; una chiave che il motore non conosce (`desnity`, un `bpm` in testa al file) viene ignorata senza avviso, e `time_mode: normalised` è letto come `absolute`. Un valore sbagliato di `distribution_mode` o `range_anchor`, invece, o un numero fuori dai limiti del parametro, fermano il motore con un errore alla costruzione dello stream, prima di ogni grano. Il motore non conosce, quando legge, l'insieme delle chiavi valide, e chi scrive a mano ha due guardie fuori da lui: il completamento delle chiavi del language server (capitolo 9) e la MAP, che a rendering fatto mostra ciò che è uscito davvero (capitolo 8). Una chiave scritta male si riconosce nella MAP perché l'effetto atteso non c'è.
