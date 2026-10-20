# La MAP e l'esportazione

La lista di grani, che nel capitolo 3 è stata presentata come rappresentazione intermedia, ha altri consumatori oltre ai renderer audio. Questo capitolo tratta i quattro che non producono suono. Il primo è la MAP (*Multiparametric Audio Plot*), un'immagine sinottica del rendering. Gli altri tre sono esportazioni verso strumenti esterni: una sessione di Sonic Visualiser, un progetto Reaper, un file JSON. La MAP e il JSON leggono la stessa lista di grani che il renderer legge per fare i campioni; Reaper e Sonic Visualiser leggono gli stream già costruiti, cioè onset, durata e curve dei parametri. Nessuno rilegge lo YAML.

Questa è la differenza che conta tra la specifica e la MAP. Lo YAML è una notazione prescrittiva nel senso di Seeger [@Seeger1958]: dice al motore che cosa fare. La MAP è descrittiva: documenta ciò che il motore ha fatto davvero, con i valori che le variabili casuali hanno assunto in quella realizzazione, e non viene mai riletta come input. Una MAP di uno stream con deviazione probabilistica mostra i grani che sono usciti, non le probabilità dichiarate. Per questo, in tutti i capitoli precedenti, ogni esempio ha accanto il listato YAML e la MAP del suo rendering: il primo è la causa, la seconda è l'effetto.

## Il grano come freccia nello spazio del materiale

### Precedenti

L'idea di vedere il controllo granulare invece di leggerlo non è nuova. La figura 4 di Truax [@Truax1988, p. 24] sovrappone maschere di tendenza e inviluppi su un terminale a 24 righe, con il tempo in ascissa e il valore del parametro in ordinata. Truax definisce questo modo di lavorare «*inherently a visual control method*» [@Truax1988, p. 23]. Sono le curve *dichiarate*, e nelle MAP di questa tesina occupano il pannello inferiore. I poligoni sul piano frequenza e tempo di Roads [@Roads1978, p. 62; @Roads1985cim, p. 200] descrivono invece la forma della nuvola, e la timeline di IRIN [@Caires2004] disegna i singoli eventi, con il numero di traccia in ordinata. Nella MAP l'ordinata è un'altra grandezza: il punto del materiale da cui ciascun grano proviene. Per un campionatore granulare è il parametro di prima classe, ed è quello che nessuno dei precedenti disegna.

### Che cosa si legge su un grano

La MAP è un piano. In ascissa c'è il tempo dello stream, in ordinata la posizione di lettura nel file sorgente, e a sinistra, sullo stesso asse verticale, la forma d'onda del file. Ogni grano è un poligono, e ciascuna proprietà del grano ha una sua variabile grafica:

| Proprietà del grano | Variabile grafica |
|---|---|
| onset | posizione orizzontale |
| posizione di lettura | posizione verticale |
| durata | larghezza |
| porzione di materiale percorsa | altezza |
| verso di lettura | orientamento della testa |
| finestra | profilo del bordo superiore, a richiesta |
| altezza (trasposizione) | colore |
| volume | opacità |

Il pan non ha una variabile sul grano: si legge nelle curve del pannello inferiore, quando è dichiarato come inviluppo.

Il colore appartiene a una scala divergente, centrata sulla trasposizione nulla. La scala è lineare, e l'unità (i cent) è stampata sulla legenda a destra. Il suo intervallo non è fisso. Si adatta all'escursione di altezza dei grani visibili, con un minimo di mezzo tono, perché pochi cent di detune non producano l'intero gradiente per una differenza musicalmente trascurabile. La legenda compare soltanto dove i grani hanno altezze diverse. L'opacità dei grani va da 0,3 a 1 sul volume tra -60 e 0 dB, così che i grani deboli restano visibili.

La freccia è la forma di default, e il suo orientamento dice il verso di lettura del buffer. Con `grain_shape: window` il bordo superiore del grano traccia invece la finestra che il grano usa, e due grani con inviluppi diversi smettono di avere la stessa forma. Sono le due modalità che si sono viste nei capitoli 4 e 5, dove la lente ingrandisce un gruppo di grani e ne mostra la forma. Sotto una soglia di larghezza sulla pagina, espressa in millimetri, la finestra non sarebbe leggibile e il grano ripiega sulla freccia.

### Due letture dello stesso asse

L'altezza di un grano è «una porzione di buffer». Quale porzione, però, non è ovvio, e il disegno ne ha usata una per un certo tempo senza dirlo. Un grano ha una durata nel tempo dello stream e una velocità di lettura al suo interno, il rapporto di altezza. La porzione di materiale che attraversa è il prodotto delle due: durata per rapporto di altezza. Il disegno storico usava soltanto la durata, cioè la porzione che il grano percorrerebbe leggendo a velocità normale. Le due misure coincidono solo quando il rapporto vale uno, che è il caso più comune, e per questo l'errore non si vedeva.

L'esempio `grain_height` (`esempi/grain_height/grain_height.yml`) isola la differenza con grani radi e lunghi. A lettura ferma, il pitch scende di un'ottava e poi sale di un'ottava sopra l'altezza di partenza; i grani durano 0,4 secondi.

![La stessa realizzazione di `grain_height`, con altezza del grano uguale alla durata (lettura storica). L'altezza del grano non cambia: cambia soltanto il colore.](docs/images/grain_height_duration_map.pdf){width=100%}

![La stessa realizzazione, con altezza del grano uguale alla porzione letta. A un'ottava sotto i grani leggono metà del materiale, a un'ottava sopra il doppio.](docs/images/grain_height_readspan_map.pdf){width=100%}

Nella prima figura la trasposizione si legge soltanto dal colore, e la pendenza apparente della freccia non cambia. Nella seconda la pendenza è un'informazione: ciò che il grano percorre sul buffer, che è esattamente ciò che il renderer legge. A un'ottava sopra la freccia dichiara il doppio di materiale. La lettura fedele ha un prezzo: un grano veloce vicino alla fine del file può uscirne, e il bordo del grafico lo taglia, mentre il renderer legge il buffer in modo ciclico e rientra dall'inizio.

Il default resta la lettura storica, e la ragione non è prudenza. La geometria nuova cambia l'aspetto di ogni MAP già generata, e una figura che cambia forma sotto i piedi di chi l'ha stampata è un'altra figura, non la stessa più corretta. Per questo il modo attivo è dichiarato nell'etichetta dell'asse, che nella seconda figura riporta *grain height = read span*: due MAP della stessa composizione, una per modo, sarebbero altrimenti indistinguibili fuori contesto.

### Il pannello degli inviluppi e la lente

Sotto il piano dei grani compaiono le curve dei parametri dichiarati come inviluppi, con i breakpoint annotati ciascuno col proprio valore. Per default si disegnano soltanto le curve dinamiche, e un parametro costante appare solo se lo si chiede (`--show-static`). Un filtro sceglie le curve da mostrare (`--plot-envelopes`). C'è anche una curva derivata che nello YAML non si può scrivere, la densità effettiva in grani al secondo, che in modalità a fattore di riempimento mostra quanto davvero la popolazione si addensa. Con più voci (capitolo 6) gli scarti di ciascuna si possono disegnare come curve separate (`--show-voice-offsets`).

La lente risolve un problema di scala. Una MAP che descrive decine di secondi non può mostrare i singoli grani di pochi millisecondi: a piena pagina sono segmenti sub-pixel. La lente è un cerchio di ingrandimento puntato su un istante e una posizione di lettura, con un fattore di zoom e due cerchi che ne dichiarano la provenienza. Il fattore e la posizione si scelgono (`--magnify-at`), oppure il sistema punta da solo sul cluster più denso (`--magnify`). Ogni lente proietta inoltre il proprio istante sul pannello degli inviluppi, con una verticale tratteggiata e un marker sul valore reale che ciascuna curva ha in quel punto. In questo modo ciò che si vede ingrandito è collegato ai valori dei parametri che lo hanno prodotto.

Con più stream sulla stessa pagina, il sistema assegna a ciascuno una corsia verticale, e una composizione lunga si impagina su più pagine, per default da 30 secondi su un foglio A3 orizzontale. Le misure della pagina sono dichiarate in millimetri, e non in pixel, perché la stessa figura esce in PDF vettoriale e in PNG a risoluzioni diverse.

### Stampare in bianco e nero

La MAP è pensata per lo schermo. Su carta in bianco e nero, dentro un testo come questo, perde informazione in due punti. Il primo è il segno della trasposizione. La scala divergente ha il braccio freddo e il braccio caldo alla stessa chiarezza, e in grigio non si somigliano soltanto: la luminanza non è nemmeno monotona. A ±150 cent su un intervallo di ±300 i due grani cadono a 0,510 e 0,595 di luminanza, a ±50 cent a 0,481 e 0,509. Un grano calante e uno crescente diventano lo stesso grigio. Il secondo punto è l'identità delle curve: gli inviluppi si distinguono per la tinta, e in grigio volume, pan e durata diventano tre linee uguali.

Un'opzione (`--bw`) seleziona un insieme di valori predefiniti che ricostruisce entrambe le informazioni. La scala del colore diventa una scala di grigi monotona, e le curve si distinguono per il tratto.

![La stessa realizzazione di `grain_height` con l'opzione `--bw`: il segno della trasposizione si legge dalla luminanza (scuro sotto, chiaro sopra), e la curva dell'inviluppo è tratteggiata.](docs/images/grain_height_bw_map.pdf){width=100%}

Il preset non è un modo di lettura a parte: è un insieme di default, ciascuno sovrascrivibile chiave per chiave. Ha però un costo dichiarato. L'opacità dei grani viene fissata, perché sul fondo bianco opacità e luminanza del grigio sono lo stesso canale. In bianco e nero il volume non si legge più nel riempimento del grano, e lasciare l'opacità libera cancellerebbe il segno del detune, che è proprio ciò che il preset serve a salvare.

### Come è costruito il visualizzatore

Il visualizzatore è il modulo più lungo del pacchetto di rendering, con circa 1 750 righe, ed è anche un'illustrazione del criterio del capitolo 3. Ospita due cose diverse: *quali numeri disegnare* (la paginazione, le corsie, i vertici dei grani, le scale dei colori, la posizione delle lenti) e *come disegnarli*. Solo la seconda richiede matplotlib. I numeri sono stati estratti in cinque moduli che non importano matplotlib e che si fermano al valore: il modulo dei grani restituisce la frazione della scala di colore e l'elenco dei vertici, e disegnare il poligono e interrogare la mappa dei colori è compito del visualizzatore. Il guadagno si vede nei test, che per verificare un calcolo di normalizzazione non richiedono più un generatore finto e la pila di plotting: richiedono un array.

Una correzione di questo lavoro mostra che cosa significhi dichiarare la regola. La forma d'onda a sinistra veniva ridotta con un campione ogni duecento. I transienti più stretti del passo non erano mai presi, le frequenze alte aliasavano su quelle basse (una nota a 220 Hz letta a 220,5 Hz si disegnava come un'onda a 0,4 Hz), e la scala verticale dipendeva dalla manopola della risoluzione. Oggi si legge ogni campione e si tiene la coppia (minimo, massimo) di ogni colonna, come fa qualunque editor audio, e il costo del disegno non dipende dalla durata del file.

## Integrazione con Sonic Visualiser e Reaper

La MAP è un'immagine statica. Per ascoltare il materiale, ispezionarlo nel tempo o montarlo, il sistema esporta la lista dei grani, o le sue derivate, verso strumenti che sanno farlo. Le tre esportazioni condividono con la MAP la stessa sorgente e la stessa regola: il motore scrive il file, e il file non torna indietro come input.

### Reaper

`ReaperProjectWriter` scrive un progetto Reaper (`.rpp`) accanto ai file audio. Ha senso solo in modalità a stem, un file per stream, perché il progetto dispone gli stem sulla timeline. Ogni stream diventa una traccia, nominata con il suo `stream_id`, con un solo elemento posto all'onset dello stream e lungo quanto la sua durata. Il file audio è referenziato per percorso e non incorporato. Il progetto prodotto per l'esempio `deviation` è questo:

```
<REAPER_PROJECT 0.1 "6.0"
  <TRACK
    NAME "mask_range"
    <ITEM
      POSITION 0.0
      LENGTH 12.0
      <SOURCE WAVE
        FILE "output/deviation__mask_range.aif"
      >
    >
  >
  <TRACK
    NAME "mask_probability"
    <ITEM
      POSITION 0.0
      LENGTH 12.0
      <SOURCE WAVE
        FILE "output/deviation__mask_probability.aif"
      >
    >
  >
>
```

Il formato è testuale e scritto a mano dal sistema, senza librerie. La fase di ascolto e di montaggio avviene in Reaper, con effetti, automazioni e routing che PGE non conosce. Per questo la pulizia dell'output (`make clean`) conserva i progetti per default: il file `.rpp` rigenerato a ogni build dall'onset e dalla durata degli stream può contenere lavoro manuale che nessuno vuole perdere. La pulizia totale è opt-in.

Un aspetto pratico merita una nota: ricostruire un progetto con Reaper già aperto. Quando Reaper è già in esecuzione il Makefile non usa il comando di apertura del sistema, che non ha un comportamento deterministico se il file è già aperto. Genera invece al volo uno script Lua per Reaper (`ReaScript`) che apre il progetto in una nuova scheda, e una variante che prima chiude la scheda che punta allo stesso file. Esiste anche una modalità che chiude Reaper con `SIGKILL` prima della build e lo riapre dopo; è dichiarata distruttiva, perché senza dialogo di salvataggio perde le modifiche non salvate, ed è l'opzione per chi itera velocemente sullo stesso YAML.

### Sonic Visualiser

Sonic Visualiser è un programma di analisi e visualizzazione dell'audio. `SVExporter` scrive una sessione (`.sv`, un XML compresso con bzip2) che si apre con la forma d'onda dell'audio renderizzato e con un livello per ogni inviluppo del motore, già impaginati e sincronizzati sul tempo del file: non c'è nessuna importazione manuale. La MAP e Sonic Visualiser rispondono a due domande diverse. La prima dà un colpo d'occhio sulla struttura, e la seconda permette di ascoltare, ingrandire e confrontare una curva con ciò che si sente.

Il modello dell'esportazione ha tre punti da dichiarare.

1. **Il tempo è assoluto.** I breakpoint di un inviluppo sono relativi allo stream, mentre il frame di Sonic Visualiser è sulla timeline globale: `round((onset + t) · sr)`. L'onset dello stream allinea ciascuno all'audio del mix, e frequenza di campionamento e durata si leggono dall'intestazione del file reso, non da valori fissi.
2. **Il tipo di interpolazione diventa stile del livello.** Un inviluppo lineare è disegnato con segmenti, uno cubico con una curva di Hermite monotona, uno a gradini con la tenuta del valore e il salto verticale.
3. **I colori sono quelli della MAP.** La tavolozza degli inviluppi è la stessa, e con più stream il livello è nominato `stream_id/chiave`.

La resa dei gradini ha richiesto una modifica del programma: il disegno a scalini non esisteva fra gli stili dei livelli temporali di Sonic Visualiser ed è stato aggiunto in una versione compilata appositamente. Con un programma più vecchio lo stile sconosciuto viene ignorato. L'esportazione ha poi due limiti dichiarati: vale per il mix, non per gli stem (un file audio, una sessione), e non riporta le curve statiche, come la MAP per default.

### JSON

L'ultima esportazione è un file JSON per ogni stream, in forma compatta. Contiene la durata, il numero di voci e, per ogni grano, sei campi: onset relativo allo stream, durata, volume, posizione di lettura, rapporto di altezza e indice della voce. Il consumatore previsto è PGE-ui, l'interfaccia grafica del motore, che disegna i rettangoli dei grani nella clip di ogni stream e li colora per altezza (in cent: $1200 \log_2 r$, con $r$ il rapporto di altezza). L'onset relativo può essere negativo, quando uno scarto di onset per voce anticipa il grano rispetto allo stream: è un dato valido, non un errore. Come per Reaper, il file ha senso accanto a uno stem audio omonimo, e per questo richiede la modalità a stem.

### Un solo ingresso, quattro uscite

Le quattro uscite mostrano all'opera la scelta del capitolo 3: il motore costruisce i propri oggetti una volta (gli stream e la loro lista di grani), e chi li consuma li legge. Aggiungere un'uscita significa scrivere un lettore, non toccare il motore. È anche il motivo per cui l'esportazione non rifà il lavoro di sintesi. Il costo del rendering audio, descritto nel capitolo 7, non ricade su queste uscite, che leggono soltanto ciò che il motore ha già costruito, con un costo proprio che non è stato misurato qui.
