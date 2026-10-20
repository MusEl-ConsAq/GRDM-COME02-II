# Uso compositivo

PGE è nato per comporre, e questo capitolo lo mostra in uso. Il caso è *mare-nostrum*, un brano elettroacustico dell'autore che al momento della scrittura è a metà. Il capitolo ha quindi un'ambizione più ridotta di un'analisi: non descrive un lavoro concluso, ma lo stato di uno in corso, ciò che è già fissato, ciò che è ancora aperto e come lo strumento ha accompagnato il processo. Prima del caso reale, una sezione mostra a che cosa somiglia una configurazione ricca quando non è ancora un brano.

<!-- TODO(giulio): questo capitolo è una bozza ricostruita dai file dei repository (mare-nostrum, granulation-studies, PGE) e dalla tua frase di partenza. Le parti segnate TODO sono quelle che solo tu puoi scrivere: la poetica, il titolo, la scelta e la provenienza dei materiali, le decisioni di forma. -->

## Dalla configurazione al brano

Gli esempi dei capitoli precedenti isolano un meccanismo alla volta. Un brano li usa tutti insieme, e il rapporto fra i parametri diventa la materia del lavoro. Lo stream completo del paper [@DeMattia2026Cim] (`esempi/complete_example/complete_example.yml`) è una configurazione di questo tipo: un solo stream di circa 32 secondi in cui densità, distribuzione, durata del grano, finestra, altezza, pan, scarto di lettura e volume cambiano tutti nel tempo.

![Lo stream completo. Il glifo del grano è la silhouette della finestra, alta quanto la durata; la finestra attraversa tre stati (Hann, `rexpodec`, Bartlett) e la forma delle teste cambia lungo lo stream. Le due lenti ingrandiscono due istanti a densità e a durata diverse.](docs/images/complete_example_map.pdf){width=100%}

La figura mostra due cose che gli esempi singoli non mostravano. La prima è la testa del grano: il glifo non è una freccia ma la sagoma della finestra, e poiché la finestra è a sua volta un inviluppo a tre stati, la forma delle teste muta nel tempo, in modo leggibile nelle lenti. La seconda è la correlazione fra densità, scarto di lettura e durata sulla linea di lettura, qui ferma (`speed_ratio: 0`): dove la densità cade (da oltre 2 900 grani al secondo a poche centinaia) la nuvola si dirada, e dove lo scarto di lettura cresce i grani si staccano dalla linea e riempiono lo spazio sopra e sotto. Lo stream è una voce sola, e la sua unica sorgente è la voce registrata, la stessa di tutti gli esempi.

## Il brano

*mare-nostrum* è un brano costruito con i lamenti e i pianti di bambini, trasformati in suono di mare. Il materiale di partenza è un corpus di registrazioni, ritagliate in frammenti di qualche secondo e numerate (`001-41_5-5_5.wav`, per esempio, che dai nomi e dalla configurazione degli studi sembra essere la registrazione 001, a partire da 41,5 secondi, per 5,5). La trasformazione è la granulazione: pochi millisecondi per grano, tanti grani sovrapposti, un puntatore che avanza lentamente nel frammento. A questa scala un grano da solo non porta un evento riconoscibile: il materiale tende a un suono continuo, di cui il frammento fornisce soprattutto il colore spettrale. La letteratura del capitolo 2 descrive il meccanismo. Sotto i circa 40 ms i suoni campionati perdono le loro qualità identificabili [@Roads2001, p. 189]; Truax pone a 50 ms la soglia sotto cui domina la fusione dei frammenti a frequenza audio, mentre sopra dominano le qualità timbriche della sorgente [@Truax1988, pp. 18-19]. I grani del brano, da 1 a 10 ms, stanno largamente al di sotto di entrambe. Roads osserva che certe granulazioni rendono la sorgente irriconoscibile distruggendone la morfologia [@Roads2001, p. 192], e Truax descrive la propria tessitura granulare come un suono in flusso costante, simile ai suoni ambientali e in particolare al suono dell'acqua [@Truax1988, pp. 24-25].

<!-- TODO(giulio): qui va la poetica del brano, con le tue parole: perché pianti e lamenti di bambini, perché il mare, che cosa significa «mare nostrum» nel pezzo; la provenienza e le condizioni delle registrazioni (e come sono trattate); il rapporto fra testimonianza e trasformazione. Non l'ho scritta perché non è documentata in nessun file e non va ricostruita da me. -->

### Dal materiale al mare: uno studio sui parametri

Il bersaglio è un percetto, la *connotazione della marea*, come lo chiama il diario di ascolto dell'autore, e non una configurazione. Per raggiungerlo l'autore ha costruito sopra PGE un piccolo laboratorio di studi, che vive nello stesso repository del brano. Uno studio (`study.yml`) dichiara uno stream di base, preso dal brano, e uno o più assi che si muovono mentre il resto sta fermo. Il motore rende un unico file audio in cui, in questo studio, ogni valore dura venti secondi, così che si possa ascoltare un parametro alla volta.

Lo studio principale incrocia la durata del grano e il rapporto di altezza, su *001-41*, il frammento più ricorrente del brano. La durata va da un campione (circa 21 microsecondi a 48 kHz) a mezzo secondo, in ventiquattro valori. I passi raddoppiano, tranne per le durate la cui inversa cade fra 500 e 5 000 Hz (da 0,2 a 2 millisecondi): lì si infittiscono, perché l'orecchio discrimina meglio le altezze e un salto d'ottava si sente come un buco. Il rapporto di altezza va da 0,2 a 1 in sette valori, per lo più a passi geometrici, perché l'altezza è una grandezza esponenziale e passi uguali all'orecchio sono passi uguali di rapporto. Un secondo studio incrocia la durata con il fattore di riempimento.

Il lessico dello studio traduce in termini percettivi grandezze già incontrate. La densità è l'unica altezza del sistema: sotto circa 20 Hz si sente un ritmo, sopra un'altezza, e nel mezzo c'è un *flutter* in cui le due percezioni si confondono. Il prodotto di densità e durata è il fattore di riempimento del capitolo 5, e la sua isolinea a 1, dove i grani passano da radi a continui, è chiamata *cresta*. Una *zona d'ombra* è un tratto dello spazio dei parametri in cui si può muovere molto un valore senza che l'orecchio senta una differenza. Il diario di ascolto ha, finora, soltanto la prima sessione (4 settembre 2026), che apre la scala sul frammento 001-41: la tabella delle regioni e delle soglie è ancora vuota.

Il laboratorio prevede anche fasi successive (stati, una matrice di parentela fra stati, una composizione come percorso fra stati) che esistono come prototipi e non sono ancora state usate. Il ciclo di lavoro in questo momento è più semplice: si modifica lo studio, si rende l'audio, si ascolta, si corregge.

### Lo schizzo

Il brano è un file YAML principale, il *master*, che importa uno stream per file (la voce `file:` del capitolo 4). Il master tiene la testa del brano (seme, durata, tempo) e il piazzamento di ogni stream, e ciascun file tiene tutto lo stream. Il contenuto reale è questo:

```yaml
duration: 322.074
bpm: 120
seed: 1441
streams:
  - file: streams/stream2.yml
    onset: 0
  - file: streams/stream2-norm.yml
    onset: 0
    mute: true
  - file: streams/stream3.yml
    onset: 0
  - file: streams/stream9.yml
    onset: 11.061
  - file: streams/stream5.yml
    onset: 43.761
  - file: streams/stream6.yml
    onset: 56.679
  - file: streams/stream7.yml
    onset: 112.003
  - file: streams/stream8.yml
    onset: 159.003
  - file: streams/stream4.yml
    onset: 241.217
  - file: streams/stream10.yml
    onset: 120.03
    mute: true
```

Il brano dura 322 secondi (cinque minuti e ventidue). Gli stream sono dieci, ma due sono silenziati (`mute: true`): `stream2-norm` è lo stesso stream di `stream2` su una copia normalizzata del frammento (presumibilmente per confronto), e `stream10` è un'altra variante, anch'essa silenziata. Restano otto stream attivi, disposti come mostra la figura.

![La disposizione degli stream di *mare-nostrum* nello stato attuale. Il colore indica il campione sorgente; i rettangoli tratteggiati sono gli stream silenziati; a destra delle barre, il numero di voci quando è maggiore di uno.](docs/images/mare-nostrum_disposizione.pdf){width=100%}

Due stream lunghi partono insieme a zero: `stream2`, che dura 173,5 secondi su *001-41*, e `stream3`, che ne dura 249,2 su un altro frammento (*001-47*) e ha quattro voci. Dopo undici secondi entra `stream9`, che granula lo stesso frammento di `stream3` con un'altra durata del grano. Poi si succedono stream più brevi, ciascuno su un frammento diverso: `stream5` e `stream6` si sovrappongono fra i 44 e i 135 secondi, `stream7` (26 secondi) si inserisce intorno al secondo 112, `stream8` riprende il frammento di `stream6` con un'altezza diversa, e `stream4` conclude, da 241 a 312 secondi. Il brano si chiude dieci secondi dopo l'ultimo stream.

La tabella riassume i dati che definiscono ciascuno stream. Il numero di grani è quello che il motore, nello stato attuale del suo repository, produce con il seme dichiarato:

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

In totale il brano ha circa 3,3 milioni di grani. Il modello di costo del capitolo 7 (circa 34 microsecondi per grano, a un processo solo) ne prevede un rendering di circa due minuti: è una stima, non una misura.

### Che cosa hanno in comune gli stream

Gli stream attivi sono in gran parte parenti, scritti con lo stesso vocabolario. Il fattore di riempimento vale 4 in sette stream su otto, quindi in ogni istante circa quattro grani si sovrappongono. Le durate dei grani stanno per lo più fra uno e dieci millisecondi, e variano nel tempo con inviluppi. Il puntatore avanza a un decimo della velocità reale (`speed_ratio: 0.1`) o meno, in un anello normalizzato, con un piccolo scarto di lettura. Il verso di lettura si inverte più volte lungo lo stream, con un inviluppo sul parametro `read_direction` di cui si è visto il meccanismo nel capitolo 5. Il rapporto di altezza è 0,2 in quattro stream (circa due ottave e mezzo sotto), con una banda di variazione di 0,05, e 0,5 in altri due (un'ottava sotto). `stream9` e `stream4` fanno eccezione, con rapporto 1 e 0,3. Il pan occupa una banda di 360 gradi, l'intero cerchio del capitolo 5, e per questo il campo sonoro non ha una direzione privilegiata.

`stream4`, l'ultimo ad entrare, si distingue dal resto: ha durate dei grani più lunghe (fino a 20 millisecondi, con un gradino iniziale), un fattore di riempimento che oscilla fra 0,4 e 2,75, un puntatore molto più lento (`speed_ratio: 0.01`) e una banda del pan di 100 gradi. Con grani più lunghi e riempimento sotto 1 in alcuni tratti, i grani tornano a essere separabili.

<!-- TODO(giulio): descrivere la forma: perché questi ingressi (11, 44, 57, 112, 159, 241 s), che cosa succede fra i piani sovrapposti, quale direzione prende il brano. Il CONTEXT.md di mare-nostrum chiama «drammaturgia» il ritmo fra ridondanza e novità e la rimanda a una fase successiva: qui si può dire a che punto è. -->

### Il processo e la riproducibilità

Due aspetti del lavoro mostrano le scelte del sistema alla prova. Il primo è la riproducibilità. Il seme 1441 sta nel master e vale per tutto il brano, e la realizzazione di ciascuno stream dipende, come nel capitolo 3, dal seme, dall'identificativo dello stream e dal componente stocastico. Lo stream ha l'identificativo del nome del suo file, e di qui una conseguenza non ovvia: *rinominare il file cambia il suono*. Un file `risacca.yml` è lo stream `risacca` nel brano e nel laboratorio, e se si rinominasse `stream2.yml` la sua realizzazione sarebbe un'altra. L'autore ha scelto di legare l'identificativo al nome del file perché lo stream suoni uguale nel brano e quando lo si apre da solo nel laboratorio. Prima del seme dichiarato ogni rendering era una realizzazione diversa: con il seme il brano è riproducibile, ma è diverso da tutti i rendering ascoltati prima, e va riascoltato prima di considerarlo valido. La cache per stream (capitolo 7) vede il seme del master: dopo un cambio di seme si rifanno da soli tutti gli stem.

Il secondo è la divisione del lavoro fra i file, che il repository fa rispettare con un test. Il master tiene il piazzamento (onset, silenziamento, solo), e il file dello stream tiene il suono. Spostare uno stream nel tempo o zittirlo si fa nel master; cambiarne il suono si fa nel file. Un file nella cartella degli stream che il master non nomina è un errore del test, perché non suonerebbe da nessuna parte. Lo stesso editor grafico del motore, PGE-ui, rispetta la divisione: un onset toccato va nel master, un volume toccato nel file.

## Stato dei lavori

Il brano ha, oggi, un materiale scelto, una famiglia di stream parenti con parametri decisi a orecchio, una disposizione nel tempo e un seme. Non ha ancora la forma conclusa. Restano aperte, per quanto si ricava dal repository, almeno quattro cose.

- La consolidazione dello studio sui parametri: il diario di ascolto ha una sessione, e le regioni, le soglie e le zone d'ombra del frammento principale vanno ancora scritte a partire dall'ascolto.
- Il destino degli stream silenziati, `stream2-norm` e `stream10`.
- La forma complessiva: ingressi, sovrapposizioni, durata di ciascuna sezione.
- La resa nello spazio: il pan di 360 gradi è oggi scritto per una coppia stereo, e il motore non vincola il numero di canali.

<!-- TODO(giulio): aggiornare questo elenco con lo stato reale al momento della consegna (26/10/2026) e aggiungere, se vuoi, un ascolto guidato o una MAP di un passaggio del brano. Una MAP dell'intero brano non è praticabile: sono 3,3 milioni di grani su dieci stream. Una pagina breve di MAP, su un passaggio a scelta, lo è. -->
