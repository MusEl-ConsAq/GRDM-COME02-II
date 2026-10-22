# Uso compositivo

PGE è nato per comporre, e questo capitolo lo mostra in uso. Il caso è *mare-nostrum*, un brano elettroacustico dell'autore che al momento della scrittura è a metà. Il capitolo ha quindi un'ambizione più ridotta di un'analisi: non descrive un lavoro concluso, ma lo stato di uno in corso, ciò che è già fissato, ciò che è ancora aperto e come lo strumento ha accompagnato il processo. Lo stato descritto è quello del repository del brano al commit `1979ce1`, con il motore alla versione che il repository stesso fissa (`1188dbc`); i numeri si ricontrollano con lo script `esempi/mare-nostrum/verifica_brano.py`. Prima del caso reale, una sezione mostra a che cosa somiglia una configurazione ricca quando non è ancora un brano.

<!-- TODO(giulio): questo capitolo è una bozza ricostruita dai file dei repository (mare-nostrum, granulation-studies, PGE) e dalla tua frase di partenza. Le parti segnate TODO sono quelle che solo tu puoi scrivere: la poetica, il titolo, la scelta e la provenienza dei materiali, le decisioni di forma. -->

## Dalla configurazione al brano

Gli esempi dei capitoli precedenti isolano un meccanismo alla volta. Un brano li usa tutti insieme, e il rapporto fra i parametri diventa la materia del lavoro. Lo stream completo del paper [@DeMattia2026Cim] (`esempi/complete_example/complete_example.yml`) è una configurazione di questo tipo: un solo stream di circa 32 secondi in cui densità, distribuzione, durata del grano, finestra, altezza, pan, scarto di lettura e volume cambiano tutti nel tempo.

![Lo stream completo. Il glifo del grano è la silhouette della finestra, alta quanto la durata; la finestra attraversa tre stati (Hann, `rexpodec`, Bartlett) e la forma delle teste cambia lungo lo stream. Le due lenti ingrandiscono due istanti a densità e a durata diverse.](docs/images/complete_example_map.pdf){width=100%}

La figura mostra due cose che gli esempi singoli non mostravano. La prima è la testa del grano: il glifo non è una freccia ma la sagoma della finestra, e poiché la finestra è a sua volta un inviluppo a tre stati, la forma delle teste muta nel tempo, in modo leggibile nelle lenti. La seconda è la correlazione fra densità, scarto di lettura e durata sulla linea di lettura, qui ferma (`speed_ratio: 0`): dove la densità cade (da oltre 2 900 grani al secondo a poche centinaia) la nuvola si dirada, e dove lo scarto di lettura cresce i grani si staccano dalla linea e riempiono lo spazio sopra e sotto. Lo stream è una voce sola, e la sua unica sorgente è la voce registrata, la stessa di tutti gli esempi.

## Il brano

*mare-nostrum* è un brano costruito con i lamenti e i pianti di bambini, trasformati in suono di mare. Il materiale di partenza è un corpus di registrazioni numerate. Il brano usa nove campioni, e i loro nomi sono di due tipi. Cinque sono frammenti ritagliati, che portano nel nome il punto del taglio (`001-41_5-5_5.wav`, per esempio, che dai nomi e dalla configurazione degli studi sembra essere la registrazione 001, a partire da 41,5 secondi, per 5,5): i nomi cominciano tutti per 001. Gli altri quattro portano soltanto un numero (`004.wav`, `007.wav`, `011.wav`, `016.wav`). I due tipi coincidono con le due forme in cui uno stream sta nel brano, che la sezione sullo schizzo descrive: i frammenti sono negli stream che hanno un file, i numeri negli stream scritti dentro il master.

La trasformazione è la granulazione. Nel primo gruppo di stream, presentato nella sezione sullo schizzo, è la granulazione fine del capitolo 2: pochi millisecondi per grano, tanti grani sovrapposti, un puntatore che avanza lentamente nel frammento. A questa scala un grano da solo non porta un evento riconoscibile: il materiale tende a un suono continuo, di cui il frammento fornisce soprattutto il colore spettrale. Sotto i circa 40 ms i suoni campionati perdono le loro qualità identificabili [@Roads2001, p. 189]; Truax pone a 50 ms la soglia sotto cui domina la fusione dei frammenti a frequenza audio, mentre sopra dominano le qualità timbriche della sorgente [@Truax1988, pp. 18-19]. I grani di quegli stream, da meno di un millisecondo a diciotto, stanno al di sotto di entrambe le soglie. Roads osserva che certe granulazioni rendono la sorgente irriconoscibile distruggendone la morfologia [@Roads2001, p. 192], e Truax descrive la propria tessitura granulare come un suono in flusso costante, simile ai suoni ambientali e in particolare al suono dell'acqua [@Truax1988, pp. 24-25]. Il brano però non sta più tutto in questo regime: le durate dichiarate dei suoi grani vanno da 0,1 millisecondi a 3 secondi, più di quattro ordini di grandezza, e la sezione sui due vocabolari dice dove.

<!-- TODO(giulio): qui va la poetica del brano, con le tue parole: perché pianti e lamenti di bambini, perché il mare, che cosa significa «mare nostrum» nel pezzo; la provenienza e le condizioni delle registrazioni (e come sono trattate); il rapporto fra testimonianza e trasformazione. Non l'ho scritta perché non è documentata in nessun file e non va ricostruita da me. -->

### Dal materiale al mare: uno studio sui parametri

Il bersaglio è un percetto, la *connotazione della marea*, come lo chiama il diario di ascolto dell'autore, e non una configurazione. Per raggiungerlo l'autore ha costruito sopra PGE un piccolo laboratorio di studi, che vive nello stesso repository del brano. Uno studio (`study.yml`) dichiara uno stream di base, preso dal brano, e uno o più assi che si muovono mentre il resto sta fermo. Il motore rende un unico file audio in cui, nello studio principale, ogni valore dura venti secondi, così che si possa ascoltare un parametro alla volta.

Gli studi sono cinque, tutti sul frammento *001-41*, quello di `stream2`, il primo stream del master. Quattro incrociano due parametri: la durata del grano con il rapporto di altezza (lo studio principale), con il fattore di riempimento e con la velocità del puntatore, e la velocità del puntatore con il rapporto di altezza. Il quinto tiene come griglia la sola coppia durata e fattore di riempimento e mette gli altri parametri su selettori: si tiene ferma una cella e si gira una manopola sola. Nello studio principale la durata va da un campione (circa 21 microsecondi a 48 kHz) a mezzo secondo, in ventiquattro valori. I passi raddoppiano, tranne per le durate la cui inversa cade fra 500 e 5 000 Hz (da 0,2 a 2 millisecondi): lì si infittiscono, perché l'orecchio discrimina meglio le altezze e un salto d'ottava si sente come un buco. Il rapporto di altezza va da 0,2 a 1 in sette valori, per lo più a passi geometrici, perché l'altezza è una grandezza esponenziale e passi uguali all'orecchio sono passi uguali di rapporto.

Il lessico dello studio traduce in termini percettivi grandezze già incontrate. La densità è l'unica altezza del sistema: sotto circa 20 Hz si sente un ritmo, sopra un'altezza, e nel mezzo c'è un *flutter* in cui le due percezioni si confondono. Il prodotto di densità e durata è il fattore di riempimento del capitolo 5, e la sua isolinea a 1, dove i grani passano da radi a continui, è chiamata *cresta*. Una *zona d'ombra* è un tratto dello spazio dei parametri in cui si può muovere molto un valore senza che l'orecchio senta una differenza. Il diario di ascolto ha, finora, soltanto la prima sessione (4 settembre 2026), che apre la scala sul frammento 001-41: la tabella delle regioni e delle soglie è ancora vuota.

Il laboratorio prevede anche fasi successive (stati, una matrice di parentela fra stati, una composizione come percorso fra stati) che esistono come prototipi e non sono ancora state usate. Il ciclo di lavoro del laboratorio è più semplice: si modifica lo studio, si rende l'audio, si ascolta, si corregge.

### Lo schizzo

Il brano è un file YAML principale, il *master*. Il master tiene la testa del brano (il seme, la durata, il tempo) e dispone gli stream nel tempo. Ogni stream vi compare in una delle due forme del capitolo 4: come voce `file:`, che importa uno stream da un file a sé e ne decide il piazzamento, oppure scritto per intero dentro il master. Le due forme sono in uso tutte e due. Questo è un estratto del master, con la testa, due importazioni e uno stream scritto dentro; le altre voci sono omesse:

```yaml
duration: 998.833
bpm: 120
seed: 1441
streams:
  - file: streams/stream2.yml
    onset: 0
  - file: streams/stream3.yml
    onset: 0
  # ...
  - stream_id: stream24
    onset: 278.634
    duration: 87.416
    sample: 016.wav
    time_mode: normalized
    distribution_mode: uniform
    fill_factor: [[0, 0.8], [0.1844, 0.61], [0.2874, 0.72], [0.3602, 0.7], [0.5158, 0.9], [0.625, 0.78], [0.7965, 0.88], [1, 0.8]]
    distribution: 0.5
    grain:
      duration: 0.0001
      duration_range: 0.0001
      envelope: all
    pointer:
      start: 0.11
      speed_ratio: 0.1
      loop_unit: normalized
      offset_range: 0.005
    pitch:
      ratio: 8
      range: 1.7818
    pan: 0
    volume: -12
    voices:
      num_voices: 4
      scatter: 1
      pointer:
        pointer_range: 0.1
        strategy: stochastic
      pan:
        spread: 90
        strategy: stochastic
    deviation_probability: 40
  # ...
```

Il brano ha quindici stream e dura 675 secondi, undici minuti e un quarto: finisce con `stream26`. Undici stream sono file e quattro, da `stream21` a `stream24`, sono scritti dentro il master. La `duration` del master, 998,833 secondi, è più lunga del brano, perché il master contiene anche altro: dal secondo 828 ci sono nove stream, tutti sovrapposti, che sono materiale messo da parte e non fanno parte del brano (se ne parla più avanti). La figura mostra la disposizione degli stream del brano.

![La disposizione degli stream del brano *mare-nostrum*. Una riga per stream, in ordine di ingresso; il colore indica il campione sorgente, che il nome fra parentesi ripete; a destra delle barre, il numero di voci quando è maggiore di uno. Il materiale messo da parte, in fondo al master, non è disegnato.](docs/images/mare-nostrum_disposizione.pdf){width=100%}

Il brano ha due gruppi. Nel primo, da 0 a 278 secondi, entrano uno dopo l'altro otto stream, tutti importati da file, fino a sette sovrapposti intorno al secondo 112, e poi escono, finché resta il solo `stream8`. Un respiro di 0,8 secondi lo separa dal secondo gruppo, da 279 a 675 secondi, più rado, da uno a cinque stream alla volta. Comincia con il solo `stream24`, per oltre un minuto, e fra 414 e 426 secondi riprende tre stream del primo gruppo: `stream25` e `stream27` sono uguali a `stream6` e a `stream9` a ogni chiave, e `stream26` è `stream3` con la durata del grano fissa a 6 millisecondi invece che in rampa. Il brano finisce con `stream26`, al secondo 675.

La tabella riassume i dati che definiscono ciascuno stream del brano. Il numero di grani è quello che il motore, alla versione che il repository del brano fissa, produce con il seme dichiarato.

| Stream | Campione | Onset (s) | Durata (s) | Grano | Voci | Grani |
|---|---|---:|---:|---:|---:|---:|
| `stream2` | 001-41 | 0,0 | 178,5 | 1–9 ms | 1 | 304 042 |
| `stream3` | 001-47 | 0,0 | 249,2 | 2–6 ms | 4 | 934 191 |
| `stream9` | 001-47 | 11,1 | 249,2 | 0,4–11 ms | 2 | 1 524 526 |
| `stream5` | 001-18 | 43,8 | 81,5 | 1,1–4,1 ms | 1 | 112 093 |
| `stream6` | 001-3 | 56,7 | 88,3 | 1–5 ms | 1 | 302 588 |
| `stream10` | 001-41 | 107,0 | 146,2 | 1–8 ms | 4 | 633 345 |
| `stream7` | 001-65 | 112,0 | 26,4 | 1–18 ms | 1 | 34 053 |
| `stream8` | 001-3 | 146,0 | 131,8 | 1–11 ms | 1 | 190 663 |
| `stream24` | 016 | 278,6 | 87,4 | 0,1 ms | 4 | 2 727 140 |
| `stream21` | 004 | 341,5 | 94,1 | 1–19 ms | 1 | 22 201 |
| `stream22` | 011 | 342,2 | 129,2 | 1–3 s | 1 | 2 296 |
| `stream25` | 001-3 | 414,1 | 88,3 | 1–5 ms | 1 | 302 955 |
| `stream27` | 001-47 | 415,0 | 249,2 | 0,4–11 ms | 2 | 1 523 628 |
| `stream26` | 001-47 | 425,7 | 249,2 | 6 ms | 4 | 665 552 |
| `stream23` | 007 | 501,3 | 78,7 | 3 s | 4 | 5 706 |

In totale il brano ha 9 284 979 grani, circa 9,3 milioni, e più del 60% sta in tre soli stream: `stream24`, `stream9` e `stream27`. Il modello di costo del capitolo 7 (circa 34 microsecondi per grano e 1,4 millisecondi per secondo di uscita, a un processo solo) prevede per il rendering poco più di cinque minuti: è una stima, non una misura.

<!-- TODO(giulio): descrivere la forma. Il master mostra due gruppi di stream (ingressi a 0, 11, 44, 57, 107, 112 e 146 s; poi da 279 a 675 s), ma non dice perché: perché il secondo gruppo comincia con il solo stream24 e riprende `stream6`, `stream3` e `stream9` fra 414 e 426 s; quale direzione prende il brano. Il CONTEXT.md di mare-nostrum chiama «drammaturgia» il ritmo fra ridondanza e novità e la rimanda a una fase successiva: qui si può dire a che punto è. -->

### Due vocabolari

Gli otto stream del primo gruppo e le tre copie del secondo, undici in tutto, sono parenti, scritti con lo stesso vocabolario. Il fattore di riempimento vale 4 in dieci di essi, quindi in ogni istante circa quattro grani per voce si sovrappongono. Le durate dei grani stanno per lo più fra uno e dieci millisecondi, e variano nel tempo con inviluppi. Il puntatore avanza a un decimo della velocità reale (`speed_ratio: 0.1`) o meno, con un'unica salita a 0,35 in `stream8`, in un anello normalizzato, con un piccolo scarto di lettura. Il verso di lettura si inverte più volte lungo lo stream in dieci stream su undici, con un inviluppo sul parametro `read_direction` di cui si è visto il meccanismo nel capitolo 5. Il rapporto di altezza è 0,2 in sei stream (circa due ottave e mezzo sotto), con una banda di variazione di 0,05, 0,5 in due e 1 in tre. Il pan occupa in tutti una banda di 360 gradi, l'intero cerchio del capitolo 5, e per questo il campo sonoro non ha una direzione privilegiata.

Quattro stream escono da questo vocabolario, ciascuno in una direzione. `stream24` scende sotto: grani di 0,1 millisecondi, circa cinque campioni a 48 kHz, con un fattore di riempimento fra 0,6 e 0,9 (quindi in media senza sovrapposizione), un rapporto di altezza di 8 e quattro voci. La finestra è `all`, cioè tutte le sedici del catalogo, e il gate di probabilità al 40% (capitolo 5) decide per ogni grano se le bande di variazione e il sorteggio della finestra valgono. Da solo emette 2,7 milioni di grani e arriva a oltre 35 000 al secondo, la densità più alta del brano. `stream22` e `stream23` salgono sopra: grani da 1 a 3 secondi, cioè da dieci a trenta volte il limite di 100 ms con cui Roads definisce il grano [@Roads2001, p. 86]. A quella scala un grano è un frammento della registrazione e non una particella, e i grani sono pochi (2 296 e 5 706), anche se si sovrappongono fino a 102 e a 460. La densità non è più fissata dal fattore di riempimento ma dichiarata, da 3 a 33 grani al secondo in `stream22` e da 2,5 a 39 in `stream23`, e la finestra è una lista di quattro, sorteggiata per ogni grano; `stream23` ha anche quattro voci, una banda di volume di 20 dB e il gate al 70%. `stream21` resta alla scala dei millisecondi e cambia l'uso della finestra, che passa da Hann a `rexpodec` dal 65% dello stream in poi (una transizione, capitolo 5). Dichiara anche un accordo, `sus4`, ma ha una voce sola, e con una voce il blocco `voices` non cambia nulla: per ora l'accordo non suona.

### Il materiale messo da parte

Dal secondo 828 il master contiene altri nove stream, da `stream12` a `stream20`, tutti sovrapposti, fino a nove insieme. Sono materiale messo da parte per un uso futuro, e per ora non fanno parte del brano: per questo la figura e la tabella non li mostrano e i numeri del capitolo non li contano, salvo dove detto. Otto hanno i valori predefiniti del capitolo 4 (`stream13` ha in più un pan a −110 gradi con una banda di 80), e quindi sono lo stream minimo, la cui lista di grani ricostruisce la sorgente: ciascuno su un campione diverso (`004.wav`, `006.wav`, `007.wav`, `008.wav`, `009.wav`, `011.wav`, `013.wav`, `016.wav`) e da 50 a 140 secondi. Il nono, `stream12`, è già lavorato: un numero di voci che sale da 1 a 12,7 (le voci frazionarie del capitolo 6), un accordo (`maj13s11`, in terzo rivolto), uno scarto di onset stocastico fra le voci fino a 10 secondi, un puntatore stocastico su tutto il file e un gate di probabilità che resta a 0 per la prima metà dello stream e sale a 100% alla fine. Il materiale pesa poco, 134 333 grani: 100 329 sono di `stream12`, e il resto degli otto stream minimi, che emettono quaranta grani al secondo ciascuno. Cinque dei campioni citati nel master (`002.wav`, `006.wav`, `008.wav`, `009.wav` e `013.wav`) stanno soltanto qui.

<!-- TODO(giulio): i nove stream messi da parte non sono silenziati nel master (nessuno ha `mute: true`): un rendering del master li suonerebbe insieme al brano, e la `duration` del master li conta. Se non devono suonare, aggiungere `mute: true` o spostarli in un master a parte; il capitolo dice soltanto che non fanno parte del brano. -->

### Il processo e la riproducibilità

Due aspetti del lavoro mostrano le scelte del sistema alla prova. Il primo è la riproducibilità. Il seme 1441 sta nel master e vale per tutto il brano, e la realizzazione di ciascuno stream dipende, come nel capitolo 3, dal seme, dall'identificativo dello stream e dal componente stocastico. Lo stream importato ha l'identificativo del nome del suo file, e di qui una conseguenza non ovvia: *rinominare il file cambia il suono*. Un file `risacca.yml` è lo stream `risacca` nel brano e nel laboratorio, e se si rinominasse `stream2.yml` la sua realizzazione sarebbe un'altra. L'autore ha scelto di legare l'identificativo al nome del file perché lo stream suoni uguale nel brano e quando lo si apre da solo nel laboratorio. Lo mostra il brano stesso: `stream25` e `stream27` hanno gli stessi valori di `stream6` e di `stream9` e un'altra realizzazione, perché hanno un altro identificativo: 302 955 grani invece di 302 588, 1 523 628 invece di 1 524 526. È lo stesso materiale con un altro sorteggio. Per avere gli stessi grani, spostati nel tempo, i due stream dovrebbero dichiarare lo stesso gruppo (`rng_group`, capitolo 4). Prima del seme dichiarato ogni rendering era una realizzazione diversa: con il seme il brano è riproducibile, ma è diverso da tutti i rendering ascoltati prima, e va riascoltato prima di considerarlo valido. La cache per stream (capitolo 7) vede il seme del master: dopo un cambio di seme si rifanno da soli tutti gli stem.

Il secondo è la divisione del lavoro fra i file, che il repository fa rispettare con un test. Il master tiene il piazzamento (onset, silenziamento, solo), e il file dello stream tiene il suono: spostare uno stream nel tempo o zittirlo si fa nel master, cambiarne il suono si fa nel file. Un file nella cartella degli stream che il master non nomina è un errore del test, perché non suonerebbe da nessuna parte, e lo è anche uno stream scritto dentro il master. Lo stato attuale non rispetta più questa seconda regola: tredici stream, quattro del brano e nove del materiale messo da parte, sono scritti dentro il master, nella forma in cui li salva PGE-ui, e il test che chiede un file per ogni stream non passa. Per gli stream importati, lo stesso editor grafico del motore rispetta la divisione: un onset toccato va nel master, un volume toccato nel file.

<!-- TODO(giulio): decidere se estrarre i tredici stream scritti dentro il master (quattro del brano, nove del materiale messo da parte) in file (PGE-ui sa dividere e duplicare gli stream) o allentare la regola e il test del repository del brano; fino ad allora questo capitolo dice che il test non passa. -->

## Stato dei lavori

Il brano ha, oggi, un materiale scelto di nove campioni, due vocabolari di stream, una disposizione nel tempo in due gruppi e un seme. Non ha ancora la forma conclusa. Accanto al brano, nel master, c'è materiale messo da parte per un uso futuro. Restano aperte, per quanto si ricava dal repository, almeno quattro cose.

- La forma complessiva: ingressi, sovrapposizioni e durata di ciascun gruppo.
- La consolidazione dello studio sui parametri: il diario di ascolto ha una sessione, e le regioni, le soglie e le zone d'ombra del frammento principale vanno ancora scritte a partire dall'ascolto.
- L'allineamento fra il master e la divisione del lavoro: tredici stream sono scritti dentro il master, mentre la regola del repository vuole un file per stream.
- La resa nello spazio: il pan di 360 gradi è oggi scritto per una coppia stereo, perché i tre renderer sono stereofonici: il grano porta soltanto un angolo, e non vincola il numero di canali.

<!-- TODO(giulio): aggiornare questo elenco con lo stato reale al momento della consegna (26/10/2026) e aggiungere, se vuoi, un ascolto guidato o una MAP di un passaggio del brano. Una MAP dell'intero brano non è praticabile: sono 9,3 milioni di grani su quindici stream. Una pagina breve di MAP, su un passaggio a scelta, lo è, ma serve il corpus audio, che non sta nel repository. -->
