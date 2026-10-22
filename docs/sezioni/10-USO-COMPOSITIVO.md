# Uso compositivo

PGE è nato per comporre, e questo capitolo lo mostra in uso. Il caso è *mare-nostrum*, un brano elettroacustico dell'autore che al momento della scrittura è a metà. Il capitolo ha quindi un'ambizione più ridotta di un'analisi: non descrive un lavoro concluso, ma lo stato di uno in corso, ciò che è già fissato, ciò che è ancora aperto e come lo strumento ha accompagnato il processo. Gli esempi dei capitoli precedenti isolano un meccanismo alla volta; un brano li usa tutti insieme, e il rapporto fra i parametri diventa la materia del lavoro.

<!-- TODO(giulio): questo capitolo è una bozza ricostruita dai file dei repository (mare-nostrum, granulation-studies, PGE) e dalla tua frase di partenza. Le parti segnate TODO sono quelle che solo tu puoi scrivere: la poetica, il titolo, la scelta e la provenienza dei materiali, le decisioni di forma. -->

## Il brano

*mare-nostrum* è un brano costruito con i lamenti e i pianti di bambini, trasformati in suono di mare. Il materiale di partenza è un corpus di registrazioni, ritagliate in frammenti di qualche secondo e numerate (`001-41_5-5_5.wav`, per esempio, che dai nomi e dalla configurazione degli studi sembra essere la registrazione 001, a partire da 41,5 secondi, per 5,5). La trasformazione è la granulazione: pochi millisecondi per grano, tanti grani sovrapposti, un puntatore che avanza lentamente nel frammento. A questa scala un grano da solo non porta un evento riconoscibile: il materiale tende a un suono continuo, di cui il frammento fornisce soprattutto il colore spettrale. La letteratura del capitolo 2 descrive il meccanismo. Sotto i circa 40 ms i suoni campionati perdono le loro qualità identificabili [@Roads2001, p. 189]; Truax pone a 50 ms la soglia sotto cui domina la fusione dei frammenti a frequenza audio, mentre sopra dominano le qualità timbriche della sorgente [@Truax1988, pp. 18-19]. I grani del brano, da 1 a 10 ms, stanno largamente al di sotto di entrambe.

<!-- TODO(giulio): qui va la poetica del brano, con le tue parole: perché pianti e lamenti di bambini, perché il mare, che cosa significa «mare nostrum» nel pezzo; la provenienza e le condizioni delle registrazioni (e come sono trattate); il rapporto fra testimonianza e trasformazione. Non l'ho scritta perché non è documentata in nessun file e non va ricostruita da me. -->

### Dal materiale al mare: uno studio sui parametri

Il bersaglio è un percetto, la *connotazione della marea*, come lo chiama il diario di ascolto dell'autore, e non una configurazione. Per raggiungerlo l'autore ha costruito sopra PGE un piccolo laboratorio di studi, che vive nello stesso repository del brano. Uno studio dichiara uno stream di base, preso dal brano, e uno o più assi che si muovono mentre il resto sta fermo; il motore rende un unico file audio in cui, in questo studio, ogni valore dura venti secondi, così che si possa ascoltare un parametro alla volta. Lo studio principale incrocia la durata del grano e il rapporto di altezza, su *001-41*, il frammento più ricorrente del brano: la durata va da un campione (circa 21 microsecondi a 48 kHz) a mezzo secondo, in ventiquattro valori. Il lessico dello studio traduce in termini percettivi grandezze già incontrate. La densità è l'unica altezza del sistema: sotto circa 20 Hz si sente un ritmo, sopra un'altezza, e nel mezzo c'è un *flutter* in cui le due percezioni si confondono. Il prodotto di densità e durata è il fattore di riempimento del capitolo 5, e la sua isolinea a 1, dove i grani passano da radi a continui, è chiamata *cresta*. Una *zona d'ombra* è un tratto dello spazio dei parametri in cui si può muovere molto un valore senza che l'orecchio senta una differenza. Il diario di ascolto ha, finora, soltanto la prima sessione (4 settembre 2026): la tabella delle regioni e delle soglie è ancora vuota.

### Lo schizzo

Il brano è un file YAML principale, il *master*, che importa uno stream per file (la voce `file:` del capitolo 4). Il master tiene la testa del brano (il seme 1441 e la durata, 322 secondi) e il piazzamento di ogni stream, e ciascun file tiene tutto lo stream. Gli stream sono dieci, ma due sono silenziati (`mute: true`): restano otto stream attivi, disposti come mostra la figura.

![La disposizione degli stream di *mare-nostrum* nello stato attuale. Il colore indica il campione sorgente; i rettangoli tratteggiati sono gli stream silenziati; a destra delle barre, il numero di voci quando è maggiore di uno.](docs/images/mare-nostrum_disposizione.pdf){width=100%}

Due stream lunghi partono insieme a zero: `stream2`, che dura 173,5 secondi su *001-41*, e `stream3`, che ne dura 249,2 su un altro frammento (*001-47*) e ha quattro voci. Dopo undici secondi entra `stream9`, che granula lo stesso frammento di `stream3` con un'altra durata del grano. Poi si succedono stream più brevi, ciascuno su un frammento diverso, e `stream4` conclude, da 241 a 312 secondi. La tabella riassume i dati che definiscono ciascuno stream; il numero di grani è quello che il motore, nello stato attuale del suo repository, produce con il seme dichiarato.

| Stream | Frammento | Onset (s) | Durata (s) | Grano (ms) | Voci | Grani |
|---|---|---|---|---|---|---|
| `stream2` | 001-41 | 0 | 173,5 | 1–9 | 1 | 301 850 |
| `stream3` | 001-47 | 0 | 249,2 | 2–6 | 4 | 934 191 |
| `stream9` | 001-47 | 11,1 | 249,2 | 0,4–11 | 2 | 1 524 526 |
| `stream5` | 001-18 | 43,8 | 81,5 | 1,1–4,1 | 1 | 112 093 |
| `stream6` | 001-3 | 56,7 | 78,4 | 1–5 | 1 | 262 627 |
| `stream7` | 001-65 | 112,0 | 26,4 | 1–18 | 1 | 34 053 |
| `stream8` | 001-3 | 159,0 | 78,4 | 1–10 | 1 | 121 704 |
| `stream4` | 002-20 | 241,2 | 70,9 | 3,2–20 | 4 | 52 486 |

In totale il brano ha circa 3,3 milioni di grani. Il modello di costo del capitolo 7 (circa 34 microsecondi per grano, a un processo solo) ne prevede un rendering di circa due minuti: è una stima, non una misura. Gli stream attivi sono in gran parte parenti, scritti con lo stesso vocabolario. Il fattore di riempimento vale 4 in sette stream su otto, quindi in ogni istante circa quattro grani si sovrappongono. Le durate dei grani stanno per lo più fra uno e dieci millisecondi, e variano nel tempo con inviluppi. Il puntatore avanza a un decimo della velocità reale (`speed_ratio: 0.1`) o meno, in un anello normalizzato, con un piccolo scarto di lettura, e il verso di lettura si inverte più volte lungo lo stream. Il rapporto di altezza è 0,2 in quattro stream (circa due ottave e mezzo sotto), con una banda di variazione di 0,05, e 0,5 in altri due (un'ottava sotto). Il pan occupa una banda di 360 gradi, l'intero cerchio del capitolo 5, e per questo il campo sonoro non ha una direzione privilegiata. `stream4`, l'ultimo ad entrare, si distingue dal resto: ha durate dei grani più lunghe (fino a 20 millisecondi), un fattore di riempimento che oscilla fra 0,4 e 2,75, un puntatore molto più lento e una banda del pan di 100 gradi, e con riempimento sotto 1 in alcuni tratti i grani tornano a essere separabili.

<!-- TODO(giulio): descrivere la forma: perché questi ingressi (11, 44, 57, 112, 159, 241 s), che cosa succede fra i piani sovrapposti, quale direzione prende il brano. Il CONTEXT.md di mare-nostrum chiama «drammaturgia» il ritmo fra ridondanza e novità e la rimanda a una fase successiva: qui si può dire a che punto è. -->

### Il processo e la riproducibilità

Due aspetti del lavoro mostrano le scelte del sistema alla prova. Il primo è la riproducibilità. Il seme 1441 sta nel master e vale per tutto il brano, e la realizzazione di ciascuno stream dipende, come nel capitolo 3, dal seme, dall'identificativo dello stream e dal componente stocastico. Lo stream ha l'identificativo del nome del suo file, e di qui una conseguenza non ovvia: *rinominare il file cambia il suono*. L'autore ha scelto di legare l'identificativo al nome del file perché lo stream suoni uguale nel brano e quando lo si apre da solo nel laboratorio. Prima del seme dichiarato ogni rendering era una realizzazione diversa: con il seme il brano è riproducibile, ma è diverso da tutti i rendering ascoltati prima, e va riascoltato prima di considerarlo valido. Il secondo è la divisione del lavoro fra i file, che il repository fa rispettare con un test: il master tiene il piazzamento (onset, silenziamento, solo), e il file dello stream tiene il suono. Lo stesso editor grafico del motore, PGE-ui, rispetta la divisione: un onset toccato va nel master, un volume toccato nel file.

## Stato dei lavori

Il brano ha, oggi, un materiale scelto, una famiglia di stream parenti con parametri decisi a orecchio, una disposizione nel tempo e un seme. Non ha ancora la forma conclusa. Restano aperte, per quanto si ricava dal repository, almeno quattro cose: la consolidazione dello studio sui parametri, perché il diario di ascolto ha una sessione e le regioni, le soglie e le zone d'ombra del frammento principale vanno ancora scritte a partire dall'ascolto; il destino degli stream silenziati, `stream2-norm` e `stream10`; la forma complessiva, cioè ingressi, sovrapposizioni e durata di ciascuna sezione; la resa nello spazio, perché il pan di 360 gradi è oggi scritto per una coppia stereo, dato che i tre renderer sono stereofonici.

<!-- TODO(giulio): aggiornare questo elenco con lo stato reale al momento della consegna (26/10/2026) e aggiungere, se vuoi, un ascolto guidato o una MAP di un passaggio del brano. Una MAP dell'intero brano non è praticabile: sono 3,3 milioni di grani su dieci stream. Una pagina breve di MAP, su un passaggio a scelta, lo è. -->
