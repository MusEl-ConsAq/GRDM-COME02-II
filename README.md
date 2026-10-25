---
abstract: |
  Python Granular Engine (PGE) è uno strumento per la sintesi granulare del suono campionato, scritto in Python e usato dall'autore per comporre. Lo stream si dichiara in un file YAML che il motore traduce in una lista di grani, da cui tre renderer producono l'audio e la MAP ne disegna un'immagine; con il seme dichiarato la specifica è il documento che si versiona e l'audio si rigenera da essa. PGE lavora in tempo differito, per disporre di molto più calcolo della granulazione in tempo reale, e prende a modello il sistema di Barry Truax sul DMX-1000, di cui conserva il lessico e le maschere di tendenza.
  
  La tesina ricostruisce l'origine teorica della tecnica, da Gabor a Truax, descrive il motore e il suo metodo di sviluppo, e lo mostra in uso in *mare-nostrum*, un brano elettroacustico per otto altoparlanti disposti attorno al pubblico. Il brano è costruito con pianti di bambini granulati fino a diventare suono di mare, da cui il pianto emerge a poco a poco fino a un coro di persone morte: è una critica dell'indifferenza di chi riposa al mare mentre, dall'altra parte dello stesso mare, muoiono dei bambini, e vuole romperla. La spazializzazione si fonda sulla codifica Mid-Side di Blumlein e sui metodi di Gerzon per decodificarla su n altoparlanti. Le conclusioni indicano i limiti, tra cui un solo file sorgente per stream e una granulazione a un solo livello, e gli sviluppi, fra cui la granulazione annidata e PGE-ui, l'interfaccia grafica con timeline dell'autore.
---

# Introduzione

Questa tesina descrive Python Granular Engine (d'ora in avanti PGE), uno strumento per la sintesi granulare del suono campionato che ho scritto in Python e che uso per comporre. Non è una teoria della granulazione e non è un manuale. È la descrizione di un ambiente, di come è costruito e di perché è costruito così, e del lavoro compositivo in cui lo sto usando.

## Motivazioni

La sintesi granulare costruisce il suono con migliaia di eventi brevi al secondo, e nessuno li scrive uno per uno. Fin dai primi esperimenti al calcolatore la specifica grano per grano si è rivelata intrattabile: nel dicembre del 1974 Roads batteva ogni grano su una scheda perforata, e per trenta secondi di suono servivano circa ottocento schede [@Roads2001, p. 110]. Comporre con i grani richiede perciò un livello di controllo che descriva il comportamento collettivo della popolazione, spesso per via statistica. La storia della tecnica è, in buona parte, la storia degli strumenti inventati per descrivere popolazioni di grani: gli *eventi* di Roads, le *maschere di tendenza* di Truax, le specifiche testuali come CMask [@Roads1978; @Truax1988; @Bartetzki1997]. PGE appartiene a questa linea. Il compositore scrive un testo in YAML che dichiara come si comporta lo *stream*, il motore lo traduce in una lista di grani e un renderer la trasforma in suono.

Le ragioni per cui l'ho fatto così sono tre.

La prima è il tempo differito. Volevo comporre e indagare gli aspetti della granulazione potendo contare su molto più calcolo di quello che la granulazione in tempo reale offre: in tempo reale la densità dei grani, il numero delle voci e la complessità del suono sono limitati dal budget di calcolo di ogni istante, in tempo differito il solo limite è il tempo che si è disposti ad attendere. È una posizione poco consueta, e Risset l'ha argomentata con chiarezza: il livello di complessità sonora che un sistema digitale raggiunge in tempo reale è sempre limitato, e il compositore non ha la libertà di sceglierlo [@Risset1999, p. 33]. La scala che il tempo differito consente si misura. Nel 1986 Truax raggiungeva in *Riverrun* una densità massima di 2 375 grani al secondo [@Truax1988, p. 25]. *mare-nostrum*, descritto nel capitolo 10, ha circa 9,5 milioni di grani, e uno dei suoi stream, `stream24`, ne emette oltre 35 000 al secondo, più di quindici volte il massimo di *Riverrun*.

La seconda è la riproducibilità e il versionamento. Una composizione scritta come testo si versiona con *git*, che diventa la documentazione del processo compositivo: ogni modifica è confrontabile con la precedente, e si può tornare a un qualsiasi stato. Il seme dei processi casuali è una chiave della specifica, e dichiararlo rende la realizzazione identica a ogni esecuzione, a parità di renderer. La specifica, non l'audio, è dunque il documento che si conserva: il rendering si rigenera da essa.

La terza è la finalità pedagogica. Il dominio di PGE è il *granular sampling* [@Lippe1993cim], e i nomi e i parametri sono quelli della letteratura classica di Roads e di Truax: la densità, la durata del grano, il fattore di riempimento, la maschera di tendenza, la posizione di lettura nel materiale. Usare lo strumento è anche un modo di studiare la tecnica. Per questo la tabella del capitolo 2 mette in corrispondenza i sette parametri della nuvola di Roads con le chiavi dello YAML.

C'è poi un percorso personale, che il paper presentato al XXV Colloquio di Informatica Musicale [@DeMattia2026Cim] racconta in nota: l'impostazione dichiarativa è l'esito di circa due anni di ricerca, nata da un confronto con Francesco Vitucci nel laboratorio *Le Domeniche alla Periferia dell'Impero* e messa alla prova in GAMMA, brano acusmatico del 2025 realizzato con un altro ambiente di composizione assistita, per sintesi additiva. Il paper aggiunge una quarta ragione, da cui è nata la MAP (*Multiparametric Audio Plot*). Pochi secondi di granulazione producono decine di migliaia di eventi, e a quella scala ricondurre l'esito agli attributi che lo hanno prodotto richiede un controllo che la specifica da sola non offre: una lista di eventi è, come documento, meno accessibile del file audio, e il file audio non permette di risalire ai parametri. La MAP rappresenta la popolazione di grani in un'immagine, prima ancora di riascoltare.

## Il modello di riferimento: il DMX-1000 di Barry Truax

PGE prende a modello il sistema di sintesi granulare che Barry Truax ha realizzato a metà degli anni Ottanta, descritto nell'articolo del 1988 [@Truax1988]. Il sistema è costruito sul DMX-1000, uno dei primi processori di segnale, controllato da un microcalcolatore [@Truax1988, p. 14], e offre tre modelli di strumento, fra cui uno che granula un suono campionato, con venti voci [@Truax1988, p. 15]. Ogni voce è un generatore d'inviluppo, e il numero delle voci fissa la densità massima in verticale. Il grano più breve controllabile in tempo reale è di 8 millisecondi, e le densità arrivano a 2 500 grani al secondo [@Truax1988, pp. 15-16]. Nel modello a campioni il suono sorgente è un segmento fisso di 4 032 campioni, circa 150-170 millisecondi, perché la memoria del processore è di quattro kiloparole [@Truax1988, p. 15]. I controlli sono quattro: frequenza centrale e banda di frequenza (o, nel modello a campioni, lo scostamento dall'inizio del campione e la sua banda), durata media e banda della durata, ritardo fra i grani [@Truax1988, p. 17]. A ciascuno corrisponde un correlato psicoacustico (altezza, larghezza di banda, densità, modulazione) [@Truax1988, pp. 18-19], e sopra i controlli sta una gerarchia di *preset*, *rampe* e maschere di tendenza, che il compositore specifica come aree entro cui i valori sono scelti [@Truax1988, pp. 19, 23].

PGE conserva il lessico e la struttura di controllo. Ogni parametro è un valore centrale, che può variare nel tempo, più una banda entro cui il valore di ogni grano è estratto: è la maschera di tendenza, in forma testuale (capitolo 4). Il modello a campioni di Truax, con lo scostamento dall'inizio del campione e la sua banda, è il blocco `pointer` (capitolo 5). Le voci parallele del DMX-1000 sono la molteplicità delle voci di uno stream (capitolo 6). Il rapporto fra un programma che calcola gli eventi e un motore che li suona è quello fra il generatore di grani e i renderer (capitolo 3). La lettura psicoacustica dei parametri guida ancora il lavoro, come si vede nello studio dei parametri di *mare-nostrum* (capitolo 10). Cambia il tempo, e con il tempo tutto ciò che nel DMX-1000 era un limite dell'hardware.

| | DMX-1000 [@Truax1988] | PGE |
|---|---|---|
| tempo | reale | differito |
| grano più breve | 8 ms | un campione |
| densità massima | 2 500 grani/s con venti voci | nessun tetto dichiarato (in *mare-nostrum*, oltre 35 000 grani/s in un solo stream) |
| voci | 20, 8 o 20, per modello | da 1 a 256 per stream, anche frazionarie, e un numero qualsiasi di stream |
| materiale campionato | 4 032 campioni, circa 150-170 ms | file di qualsiasi durata |
| controllo | comandi da tastiera, preset, rampe, maschere | un documento di testo |
| visualizzazione | sovrapposizione delle maschere su un terminale | la MAP dei grani generati |

La differenza che più conta è il controllo. Truax osserva che i file di partitura prodotti da editor e programmi algoritmici sono di solito troppo grandi da maneggiare [@Truax1988, p. 14], e risponde generando i grani in tempo reale. PGE risponde in un altro modo: la lista dei grani, che può avere milioni di elementi, esiste ma non si scrive e non si legge. Ciò che il compositore scrive e versiona è la specifica, di poche righe, e la MAP dà accesso alla lista.

## Obiettivi e struttura della tesina

Mi propongo quattro cose: descrivere PGE, cioè il suo disegno, il linguaggio, il grano e lo stream, le voci, il rendering; collocarlo nella letteratura della sintesi granulare, da cui prende il lessico; mostrarlo in uso, nel brano che sto scrivendo; registrare il metodo con cui è sviluppato, perché in un progetto di questa durata il metodo è parte del risultato. Non mi propongo di valutare lo strumento con ascoltatori o con altri compositori, né di confrontarlo con altri sistemi, né di sostituire la documentazione del progetto, che resta nel repository (`docs/`) e a cui la tesina rimanda.

La tesina riprende l'impostazione del paper presentato al CIM [@DeMattia2026Cim], di cui espande la materia, e ne conserva il metodo espositivo e il vocabolario. Gli esempi sono quelli del paper, con alcuni aggiunti, e sono rieseguibili: ogni listato YAML è nella cartella `esempi/` del repository della tesina e dichiara il proprio seme, per cui la realizzazione è quella che si riottiene rieseguendolo. La MAP è sempre quella generata dal motore, mai ridisegnata. La versione descritta è la 9.1.0 [@DeMattia2026Pge].

L'esposizione procede dal generale al particolare: l'origine della sintesi granulare (capitolo 2), l'architettura (3), il linguaggio (4), il grano, lo stream e le voci (5 e 6), il rendering (7), la MAP e le esportazioni (8), il metodo di sviluppo (9), *mare-nostrum*, il brano per cui lo strumento è usato (10), e infine la spazializzazione per n altoparlanti con cui il brano deve essere eseguito (11). Una nota sul lessico: chiamo MAP l'immagine sinottica dei grani generati, come nel paper, e non la chiamo «partitura», parola che uso soltanto per il file di eventi che Csound legge; chiamo *stream* il flusso di grani descritto da un blocco dello YAML, e *voce* ciascuna delle copie parallele con cui uno stream si moltiplica.


# La sintesi granulare

La sintesi granulare costruisce un suono come somma di molti eventi molto brevi, i *grani*. Questo capitolo ne ricostruisce l'origine teorica, definisce il grano e i suoi parametri, distingue i modi di organizzare i grani nel tempo e arriva al caso che interessa PGE, la granulazione di un suono già registrato. Il riferimento principale è *Microsound* di Roads [@Roads2001], che raccoglie e ordina la letteratura. La trattazione è la base dei capitoli seguenti, che ne usano il vocabolario senza ridefinirlo.

## Origini teoriche: Gabor, Xenakis, Roads

L'idea di scomporre il suono in unità elementari nasce come teoria dell'udito. Nel 1947 il fisico Dennis Gabor osserva che l'analisi di Fourier è «una descrizione senza tempo», in termini di onde di durata infinita, mentre l'esperienza più elementare è che il suono ha insieme una forma temporale e una forma frequenziale [@Gabor1947, p. 591]. La sua soluzione è un piano con il tempo e la frequenza come coordinate ortogonali, in cui a ogni segnale si associa una cella rettangolare, la cui area ha un minimo:

$$ \Delta t \,\Delta f \ge 1 $$

È la formulazione esatta della relazione di indeterminazione fra tempo e frequenza [@Gabor1947, p. 591]: per determinare con precisione le frequenze occorre una finestra lunga, per determinare con precisione l'istante occorre rinunciare alla frequenza. I segnali che occupano una cella di area minima, i *segnali elementari*, sono oscillazioni armoniche modulate da un impulso gaussiano [@Gabor1947, pp. 591-592]. Gabor ha anche un'invenzione: nella metà degli anni Quaranta costruisce un granulatore, il *Kinematical Frequency Convertor*, che cambiava l'altezza di un suono senza cambiarne la durata e viceversa [@Roads2001, p. 61]. Una testina rotante campiona a intervalli regolari la registrazione, ogni segmento prelevato è un grano, e i grani si riassemblano in un flusso continuo su un altro supporto. La granulazione di un suono registrato è dunque più antica del calcolatore.

Chi ne fa una teoria compositiva è Xenakis: Roads lo indica come il primo a formulare una teoria compositiva dei grani di suono [@Roads1978, p. 61; @Roads1988, p. 11]. In *Formalized Music* la teoria si apre con una «ipotesi temporanea di base»:

> «All sound is an integration of grains, of elementary sonic particles, of sonic quanta. Each of these elementary grains has a threefold nature: duration, frequency, and intensity. All sound, even all continuous sonic variation, is conceived as an assemblage of a large number of elementary grains adequately disposed in time.» [@Xenakis1992, p. 43]

Le due opere in cui Xenakis lavora con i grani hanno metodi opposti [@Roads2001, pp. 64-67]. *Concret PH* (1958) è fatta di registrazioni di braci di legno ardente, tagliate in frammenti di un secondo, in modo intuitivo e non matematico. In *Analogique B* (1959) toni sinusoidali tagliati in frammenti di nastro sono disposti su *schermi*, istantanee del suono suddivise in celle di frequenza e ampiezza come la matrice di Gabor. Roads ne ricava una critica che anticipa il resto del capitolo: l'ipotesi che tutti i grani abbiano la stessa durata e che gli schermi si susseguano a passo costante è esteticamente limitante, e produce artefatti udibili, mentre la durata del grano si rivela uno dei parametri più importanti da far variare nel tempo [@Roads2001, p. 67].

Xenakis non ha mai realizzato la sintesi granulare al calcolatore [@Roads2001, pp. 108-109]. Roads la realizza a San Diego nel dicembre del 1974: l'esperimento, *Klang-1*, è la prima implementazione della sintesi granulare asincrona, e le specifiche di ogni grano sono battute su una scheda perforata ciascuna [@Roads2001, p. 110]. L'esperienza impone l'automazione: il sistema che Roads descrive nel 1978 è un processore di ingresso per Music V, in cui il compositore specifica *eventi*, ciascuno con un istante, una durata, una frequenza centrale, una larghezza di banda, una densità e un'ampiezza, e il programma calcola da ciascun evento migliaia di grani [@Roads1978, p. 61; @Roads1988, p. 12]. Questo schema, una descrizione compatta che un programma traduce in una lista di eventi per un sintetizzatore separato, è quello che torna nei sistemi successivi: nel 1981, al MIT, Roads lo applica a suoni campionati [@Roads2001, pp. 189-190], e CMask, di Bartetzki, lo fa per Csound [@Bartetzki1997]. Il quadro di PGE (capitoli 3 e 7) ne è una ripresa. Il secondo filone è il tempo reale: Truax realizza nel 1986 un sistema sul processore di segnali DMX-1000 e nel 1987 lo estende alla granulazione di un breve suono campionato [@Roads2001, p. 112]. Con migliaia di eventi al secondo servono, nelle sue parole, «strategie di controllo potenti» [@Truax1988, p. 19], e la scelta statistica è un'economia di mezzi, più che un cambio di postura compositiva.

## Il grano e i suoi parametri

Un grano è, per Roads, un breve evento microacustico, con una durata prossima alla soglia della percezione uditiva, tipicamente fra un millesimo e un decimo di secondo (da 1 a 100 ms), che contiene una forma d'onda modellata da un inviluppo d'ampiezza [@Roads2001, p. 86]. Gli estremi sono convenzionali: nel 1988 Roads dà da 1 a 50 ms, Truax parla di 10-50 ms [@Roads1988, p. 11; @Truax1994, p. 38]. Il grano ha molti parametri e ne occorrono migliaia al secondo: per specificare un secondo di suono servono $n \times d$ valori, con $n$ il numero di parametri per grano, di solito maggiore di dieci, e $d$ la densità in grani al secondo, che può superare mille. Serve perciò un'unità di organizzazione globale: il compositore descrive il suono in termini globali, e l'algoritmo riempie i dettagli [@Roads2001, p. 87]. Roads ne ricava un principio: si può scambiare complessità dello strumento con complessità della partitura, perché la complessità del suono deriva dalla combinazione mutevole di molti grani, a patto di fornire un flusso massiccio di dati di controllo [@Roads2001, p. 90]. L'ambiente descritto in questa tesina accetta lo scambio: il grano è un dato di otto campi (capitolo 3), e la complessità sta nella descrizione di come quei campi variano.

Anche l'inviluppo che modella il grano è una scelta spettrale. Quando i grani si susseguono a intervalli regolari, l'inviluppo complessivo è una funzione periodica e il segnale è una modulazione d'ampiezza: ogni componente del portante genera bande laterali, e la forma dell'inviluppo decide il numero e il peso delle bande [@Roads2001, p. 98]. Finestrare un grano è quindi modulare il suo segnale, e non un prelievo neutro; è la ragione per cui in PGE la forma della finestra è un parametro dello stream (capitolo 5) e non una convenzione fissa. La durata è il parametro con l'effetto più forte. Per le nuvole asincrone Roads riassume gli effetti percettivi così: a 200 µs una disgregazione rumorosa e particellare, a 1 ms la perdita dell'altezza, a 10 ms un tremolio, a 50 ms la formazione di un'altezza stabile, a 200 ms un tremolo aperiodico [@Roads2001, p. 101]. Anche per Truax il discrimine è a circa 50 millisecondi: con grani molto più brevi si ha la fusione in una tessitura continua, con grani molto più lunghi si percepiscono eventi separati [@Truax1988, p. 18].

La densità, da sola, dice poco sulla tessitura, perché con la durata del grano produce la tessitura. La differenza è il *fattore di riempimento* (*fill factor*): il prodotto della densità per la durata del grano in secondi. Roads distingue nuvole *rade* (FF < 0,5, più della metà della nuvola è silenzio), *coperte* (FF circa 1) e *compatte* (FF > 1, grani sovrapposti) [@Roads2001, p. 105]. Il fattore di riempimento è, nel linguaggio di PGE, una chiave alternativa alla densità (capitolo 5): chi la usa pensa alla copertura e non alla frequenza di emissione. Roads elenca sette parametri con cui il compositore specifica una nuvola [@Roads2001, p. 96]. Ciascuno ha un corrispondente nel linguaggio di PGE, con la differenza che l'oggetto dei grani non è una forma d'onda sintetica ma un suono campionato.

| Parametro della nuvola [@Roads2001, p. 96] | In PGE |
|---|---|
| istante d'inizio e durata della nuvola | `onset` e `duration` dello stream |
| durata del grano (costante, variabile, casuale) | `grain.duration` e `duration_range` |
| densità, variabile nel tempo | `density` o `fill_factor`, e `distribution` |
| banda di frequenze | `pitch`: nel campionamento la frequenza del grano diventa trasposizione |
| inviluppo d'ampiezza della nuvola | `volume` |
| forma d'onda nei grani | `sample` e il blocco `pointer` |
| dispersione spaziale | `pan` e `pan_range` |

## Flussi sincroni e asincroni

Il modo in cui i grani si dispongono nel tempo distingue, secondo Roads, le forme principali di sintesi granulare. Nella sintesi **sincrona** ogni grano segue il precedente a intervalli regolari, e la densità, cioè la frequenza di emissione, si può leggere come una frequenza in hertz: fra 0,1 e 20 grani al secondo si ottengono ritmi metrici, con densità maggiori i grani si fondono in toni continui con una forte frequenza fondamentale [@Roads2001, p. 93]. Nella sintesi **quasi sincrona** gli intervalli sono disuguali, e una deviazione casuale ne decide l'irregolarità. Il caso estremo, in cui l'istante di ogni grano è casuale, è quello della sintesi **asincrona**, che disperde i grani entro regioni del piano tempo-frequenza chiamate *nuvole*, le unità con cui lavora il compositore [@Roads2001, pp. 93, 96]. Dutilleux e colleghi riassumono la distinzione in strategie sincrone, basate soprattutto su funzioni deterministiche, e strategie asincrone, basate su funzioni stocastiche, e indicano due variabili di controllo: il ritardo fra i grani di un flusso e il grado di sincronicità fra i grani di flussi diversi [@Dutilleux2016, pp. 110-111]. In PGE il primo è la distribuzione degli intervalli fra i grani del capitolo 5, e il secondo lo `scatter` fra le voci del capitolo 6. C'è un'avvertenza terminologica: «sincrono» ha più di un senso. Nel lavoro di De Poli e Piccialli la sintesi sincrona aggancia i grani al periodo del suono quasi periodico analizzato, per conservare la continuità di fase [@DePoliPiccialli1991; @Roads2001, p. 92]; nella tradizione di Roads e Truax, che è anche quella di PGE, indica soltanto la regolarità degli intervalli.

Come specificare la dispersione, in pratica? Il metodo che Truax mette al centro del suo sistema è la *maschera di tendenza*. La maggior parte delle variabili di controllo del suo sistema è descritta da un valore medio e da un intervallo intorno ad esso, da cui si estrae a caso: due grandezze che sono esattamente quelle che descrivono una maschera, espressa come un'area entro cui i valori possono essere scelti. La sua larghezza in ogni punto determina l'intervallo di scelta, fornendo un continuo fra scelte deterministiche e scelte stocastiche [@Truax1988, p. 23]. Gli stessi due ingredienti, un valore centrale che varia nel tempo e una banda di variazione, sono la struttura dei parametri del linguaggio di PGE, descritta nel capitolo 4.

## La granulazione del suono campionato

Se il contenuto del grano è un frammento di suono già registrato, si parla di granulazione. Roads la distingue dalla sintesi granulare con forme d'onda sintetiche: la sintesi *costruisce* un suono, la granulazione ne *trasforma* uno esistente [@Roads2001, p. 86]. Con la formalizzazione di Dutilleux e colleghi, un grano è il segmento estratto da un segnale di ingresso $x$ con una finestra $w_k$ a partire dall'istante $i_k$, e l'uscita è la somma dei grani collocati agli istanti $n_k$, con ampiezze $a_k$:

$$ g_k(i) = x(i + i_k)\, w_k(i), \qquad y(n) = \sum_k a_k \, g_k(n - n_k) $$

[@Dutilleux2016, pp. 109-110]. Sono i parametri del grano di PGE (capitolo 5): $i_k$ è la posizione di lettura, $n_k$ l'istante di emissione, $w_k$ la finestra, $a_k$ il volume.

Lippe, nel 1993, dà a questa distinzione il suo nome. Granular synthesis e *granular sampling* sono varianti della stessa tecnica, ma le loro essenze musicali stanno a poli opposti: la prima appartiene all'*elektronische Musik* e a suoni puramente sintetici, la seconda alla musique concrète, in cui suoni registrati sono manipolati e trasformati [@Lippe1993cim, p. 179]. Con il campionamento compare un parametro in più, l'istante da cui si preleva nel suono memorizzato, che può avere un'importanza primaria: l'ordine dei grani non è più un parametro «commutativo» o arbitrario, e crea una gerarchia implicita fra i parametri. Una delle caratteristiche musicalmente più interessanti del granular sampling è per Lippe la capacità di *decostruire* i suoni con la manipolazione degli istanti di prelievo, muovendosi sul continuo che separa il riconoscibile dal non riconoscibile [@Lippe1993cim, pp. 179-180]. È la nozione su cui si regge il dominio di PGE (capitolo 3): la posizione di lettura nel materiale è un parametro di prima classe. Roads osserva che la lettura da un file dà molta più libertà della granulazione di un suono che viene da un microfono: poiché il suono sta in un file, i grani si possono estrarre in qualunque ordine, in sequenza, all'indietro, a caso, con un'evoluzione statistica o in una successione arbitraria [@Roads2001, pp. 188-189].

Che cosa resta del suono d'origine dipende soprattutto dalla durata del grano. Per Roads, quando i grani sono molto brevi (meno di 40 ms), i file campionati perdono le loro qualità intrinseche identificabili, mentre per materiali che si vogliono conservare, come il testo parlato, funzionano meglio grani più lunghi, oltre i 40 ms [@Roads2001, p. 189]. Truax assegna a 50 ms una funzione analoga: intorno a quella soglia, e sopra di essa, dominano le qualità timbriche del suono di partenza, e sotto domina la fusione dei frammenti a frequenza audio [@Truax1988, pp. 18-19]. La granulazione può anche distruggere ciò che granula: certe granulazioni rendono la sorgente irriconoscibile distruggendone la morfologia [@Roads2001, p. 192], e in *Riverrun* ogni suono è in uno stato di flusso costante, come i suoni ambientali in generale e il suono dell'acqua in particolare [@Truax1988, pp. 24-25].

PGE granula un file con un puntatore che si muove nel campione, emette i grani su una griglia che va dal sincrono all'asincrono e descrive i parametri con valori centrali e bande di variazione: è la granulazione da file di Roads e il granular sampling di Lippe, con il tempo differito che la lettura da un file rende possibile.


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

Il grano è *congelato*: una volta creato nessuno può modificarlo, e quindi la generazione e i consumatori non possono interferire. Contiene soltanto numeri, e un brano come *mare-nostrum* ne ha più di nove milioni (capitolo 10). Il verso di lettura non ha un campo proprio, è il segno di `pitch_ratio`. Un grano non porta il nome del suo campione né della sua finestra, ma un indice, il cui significato sta in una tabella dei simboli, `FtableManager`, che il `Generator` riempie alla costruzione: Csound la materializza come tabelle di funzione nello score, NumPy come array, SuperCollider come buffer. È la stessa idea della tabella dei simboli di un compilatore: i nomi si risolvono una volta, fuori dal dato, e il dato resta leggero e neutro rispetto a chi lo consuma. La lista è una `List[List[Grain]]`, una lista per voce, e `stream.voices` è l'unica fonte di verità sui grani esistenti.

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


# Il grano e lo stream

Alla grammatica del capitolo 4 segue il vocabolario: che cosa governa ciascuna parte della dichiarazione e come il motore la traduce in un campo del grano. Il metodo è quello del paper presentato al XXV CIM [@DeMattia2026Cim], che espone PGE per scostamenti: si parte dallo stream minimo del capitolo 4, la trasformazione identica della sorgente, e ci si scosta da esso un parametro alla volta. Per ciascuno esiste un esempio che lo isola, nella cartella `esempi/` del repository della tesina, con la MAP che il motore ne ricava; qui ne compaiono i due più significativi. Gli esempi, per non disturbare ciò che isolano, spesso fermano la lettura (`speed_ratio: 0`), così che la MAP mostri una sola variabile. Le affermazioni sul comportamento del motore sono controllate, una per una, dallo script `esempi/grano/verifica_grano.py`. L'ordine è quello del paper: dove il grano legge, cioè il puntatore; quando è emesso, cioè la griglia; che cosa è, cioè la sua durata, la finestra, l'altezza, il verso, il volume e la posizione nel campo; e quanto ne decide il caso.

## Il puntatore

Il blocco `pointer` risponde a una domanda: da dove legge questo grano? La risposta è una posizione in secondi nel file, il campo `pointer_pos`, e il motore la compone in quattro passi. Il primo è la posizione lineare: `start` più l'integrale di `speed_ratio`, come ha mostrato il capitolo 4; `speed_ratio` vale 1 per la velocità naturale, 0 per fermare la testina, un numero negativo per percorrere il file all'indietro. Il secondo passo applica il loop, se c'è. Il terzo somma alla posizione la deviazione di ciascun grano, scalata sulla lunghezza della finestra attiva, lo scarto della voce (capitolo 6) e, per un grano letto all'indietro, la sua durata. Il quarto è l'operazione modulare: riporta la posizione dentro la finestra e poi dentro il file, perciò la testina che arriva in fondo ricomincia dall'inizio.

Il puntatore può essere confinato in una finestra del file, il *loop*, che si accende con `loop_start`; la fine si dichiara con `loop_end`, un istante, o con `loop_dur`, una durata. Inizio e fine accettano inviluppi, e la finestra può dunque muoversi nel file. La deviazione di posizione si dichiara con `offset_range`, la larghezza della banda attorno alla posizione calcolata, come frazione della finestra attiva (il file intero se non c'è un loop). Il loop riguarda però soltanto la partenza del grano. Il grano non porta con sé il loop, perché nessuno dei suoi otto campi lo descrive, e il renderer legge a partire da `pointer_pos` per tutta la durata, tornando all'inizio del *file*, non della finestra: un grano di 0,2 s che parte a 0,55 s in un loop che finisce a 0,6 s legge fino a 0,75 s. Il loop decide da dove si parte, non fin dove si legge.

## La griglia di emissione

Il campo `onset` dipende da una successione di intervalli. L'intervallo fra due onset successivi si chiama *inter-onset time* (IOT), e due parametri lo governano: la densità (`density`), in grani al secondo, che ne fissa il valore medio, $\mathrm{IOT}_{\mathrm{avg}} = 1/\mathit{density}$, e la distribuzione (`distribution`), che stabilisce quanto gli intervalli siano regolari. «Sincrono» e «asincrono» hanno il senso di Roads descritto nel capitolo 2: la regolarità degli intervalli. In alternativa alla densità si può dichiarare il *fill factor* (`fill_factor`), il prodotto della densità per la durata del grano, che ha la priorità se compaiono entrambi; se non compare nessuno dei due vale 2. Con il fill factor la densità diventa un quoziente, calcolato con la durata del grano che sta per emettere: dopo un grano di durata $d$, il successivo arriva dopo $d/F$, con $F$ il fill factor, qualunque sia $d$, e la sovrapposizione resta quella dichiarata anche quando la durata varia da un grano all'altro. Un valore dichiarato fuori dai limiti del parametro è un errore alla lettura dello YAML; la densità non ha un tetto, ma sopra i 4 000 grani al secondo il motore scrive un avviso nel log.

La distribuzione è un numero fra 0 e 1. Con $d$ uguale a `distribution`, l'intervallo è

$$\mathrm{IOT}(d) = (1-d)\,\mathrm{IOT}_{\mathrm{avg}} + d\,\mathcal{U}\!\left(0,\, 2\,\mathrm{IOT}_{\mathrm{avg}}\right), \qquad d \in [0,1]$$

dove $\mathcal{U}$ è il campionamento uniforme. A $d = 0$ ogni intervallo vale $\mathrm{IOT}_{\mathrm{avg}}$: la griglia è metronomica, l'emissione sincrona. A $d = 1$ l'intervallo è estratto da una distribuzione uniforme fra 0 e il doppio del valore medio: l'emissione è asincrona, ma non è un processo di Poisson, i cui intervalli sarebbero esponenziali. I valori intermedi sono il regime quasi-sincrono, e poiché il parametro accetta un inviluppo lo stream può passare dall'uno all'altro regime nel tempo. Un grano la cui coda sfora la fine dello stream è scartato, non troncato.

L'esempio `distribution` lascia ferma la lettura su un punto del file, per vedere soltanto la griglia di emissione: lo stream dura 20 secondi, la densità sale da 10 a 200 grani al secondo e ridiscende, la distribuzione resta a zero fino a circa 6 secondi e poi sale a 1, per ritornare a zero.

![Passaggio da emissione sincrona ad asincrona su lettura ferma. Nella prima lente gli onset sono equispaziati, nella seconda irregolari.](docs/images/distribution_map.pdf){width=100%}

La differenza si sente oltre che vedersi. Quando la griglia è sincrona e la densità è alta, l'emissione periodica di grani identici produce uno spettro a righe, spaziate a multipli della densità [@Roads2001Pulsars]; quando la distribuzione sale verso 1 gli istanti di emissione si irregolarizzano e le righe si smerigliano in una banda.

## Il grano

La durata è in secondi per impostazione predefinita (0,05 s) e sta fra un campione, circa 21 microsecondi a 48 kHz, e 10 secondi; con `grain.duration_unit` si può dichiararla in millisecondi o in campioni.

La finestra è l'inviluppo di ampiezza che dà forma al grano, e la scelta della forma è anche una scelta timbrica [@Roads2001]. Il catalogo ha sedici finestre, tra cui Hann (la predefinita), Hamming, Blackman, la gaussiana, la triangolare, la `sinc` e curve esponenziali asimmetriche, ed è dato e non codice: ogni voce descrive una forma matematica e i suoi coefficienti. I nomi non coincidono tutti con quelli di Roads: `expodec` e `rexpodec` del catalogo non designano le forme omonime del libro, e per quelle occorre cercare la forma più vicina. La finestra si dichiara per nome, oppure come lista fra cui il motore sceglie a caso per ogni grano, oppure come transizione, anche a più stati, da una finestra a un'altra, governata da una curva da 0 a 1. La transizione è un sorteggio per grano, e non una dissolvenza fra due finestre: a 0,5 metà dei grani ha la prima finestra e metà la seconda.

Il blocco `pitch` governa la trasposizione del grano. Funziona per unità: semitoni, quarti di tono, ottavi di tono, cent, una divisione arbitraria dell'ottava (`edo`) o un rapporto diretto (`ratio`), e in un blocco se ne dichiara una sola, perché non c'è una priorità implicita. Nelle unità EDO (*equal division of the octave*) la conversione nel rapporto di trasposizione è $2^{v/N}$, con $v$ il valore e $N$ il numero di divisioni, e la variazione è quantizzata su un grado intero della griglia; `edo: 31` con `value: 18` dichiara diciotto gradi di una scala a trentuno divisioni.

Il segno del rapporto di altezza è il verso con cui il grano legge il materiale. Tre grandezze lo riguardano e vanno tenute distinte: `pointer.speed_ratio` governa la velocità e il verso con cui la testina percorre il file; `grain.read_direction` il verso con cui il singolo grano legge il materiale ($-1$ indietro, $+1$ avanti); il blocco `pitch` l'altezza percepita, sempre positiva per costruzione. Per impostazione predefinita il verso del grano segue quello della testina, e se `read_direction` è dichiarata vince il suo segno. Un grano letto all'indietro ha il rapporto negato e la sua posizione di lettura è spostata in avanti della sua durata, così che a rapporto 1 legga lo stesso segmento del file che avrebbe letto in avanti, ma dalla fine verso l'inizio.

Il `volume` è in decibel (0 dB è il livello del campione), e il renderer lo converte in ampiezza, $A = 10^{v/20}$. Il `pan` è un angolo in gradi che muove il grano lungo una circonferenza unitaria in codifica Mid-Side, la matrice di Blumlein [@Blumlein1931]: mid e side sono due microfoni a figura otto ortogonali, le proiezioni coseno e seno del grano lungo la circonferenza [@Gerzon1975]. La potenza resta costante a ogni angolo, $L^2 + R^2 = 1$ (capitolo 7); il grano si muove fra le due casse fra $-45$ e $+45$ gradi, e a $\pm 90$ gradi le due uscite sono in controfase e un ascolto in mono le cancella. Il grano porta un angolo, non una coppia di guadagni, e la matrice appartiene al renderer. La posizione nel campo sonoro è un attributo del singolo grano, parte della costruzione dello strumento, e non un effetto di spazializzazione aggiunto in fondo alla catena.

## La variazione stocastica

I parametri di un grano non sono tutti decisi dal compositore uno per uno: sarebbe la specifica grano per grano che l'introduzione ha indicato come intrattabile. La parte del caso è dichiarata a due livelli. Ogni parametro ha una traiettoria centrale, un inviluppo, e una banda di deviazione attorno a quella traiettoria, `_range`, da cui si estrae un valore diverso per ogni grano. È la maschera di tendenza del capitolo 2, che il capitolo 4 ha scritto come un valore centrale e una larghezza. Con $c(\tau)$ la traiettoria centrale, $\rho(\tau)$ la larghezza della banda e $\xi_n$ un valore uniforme fra $-1/2$ e $1/2$, il parametro del grano $n$ al tempo normalizzato $\tau_n$ è

$$v_n = c(\tau_n) + \xi_n\,\rho(\tau_n), \qquad \xi_n \sim \mathcal{U}\!\left(-\tfrac{1}{2}, \tfrac{1}{2}\right)$$

Il sistema aggiunge un terzo livello: la probabilità, variabile nel tempo, che la deviazione si applichi. Un *gate* probabilistico, una porta che si apre o si chiude, decide grano per grano se il grano segue la traiettoria o subisce la deviazione:

$$v_n = c(\tau_n) + g_n\,\xi_n\,\rho(\tau_n), \qquad g_n \sim \mathrm{Bernoulli}\!\big(p(\tau_n)\big)$$

dove $p(\tau)$ è la probabilità, anch'essa un inviluppo: nella formula è un numero fra 0 e 1, nello YAML (`deviation_probability`) si scrive da 0 a 100. Il metodo `Parameter.get_value`, descritto nel capitolo 3, è questa espressione. La differenza rispetto alla prima formula è il fattore $g_n$, che rende l'ampiezza della deviazione, $\rho$, e la sua probabilità, $p$, due dimensioni di controllo indipendenti. Quando la chiave manca, il gate è sempre aperto per i parametri che hanno un `_range`, ed è la maschera di tendenza semplice; un parametro senza `_range` non devia mai.

Nelle fonti consultate non si trova un precedente diretto del gate come asse dichiarabile e componibile nel tempo. Il più vicino è nell'ICMS, dove alcune trasformazioni del grano (lettura retrograda, inversione di fase, ripetizione) si applicano a circa metà dei grani per decisione di un generatore casuale [@DiScipioTisato1993cim]: la probabilità è però fissa e governa interruttori discreti, non l'applicazione di una maschera a un parametro continuo. Per forma è più vicina l'*intermittency* di EmissionControl2, un gate per grano modulabile con continuità [@Roads2021], ma decide se il grano viene emesso e agisce quindi sulla densità: nel linguaggio qui descritto il grano resta, e il gate decide se applicargli la deviazione.

L'indipendenza dei due assi si vede in due stream che condividono la stessa traiettoria, una lettura ferma, e la stessa ampiezza massima di deviazione (esempio `deviation`). Nel primo cresce l'ampiezza della deviazione, nel secondo la probabilità.

![Due modi di aprire la deviazione, a parità di traiettoria e di ampiezza massima. Pannello superiore: l'ampiezza cresce da 0 a 0,35 con il gate sempre aperto, e i grani riempiono uniformemente uno spazio di lettura che si allarga a cuneo. Pannello inferiore: l'ampiezza è costante e cresce la probabilità da 0 a 100%; la linea si trasforma in nuvola, passando da grani fedeli a grani devianti.](docs/images/deviation_map.pdf){width=100%}

Una trappola ha sorpreso più volte: scritta senza valore, `deviation_probability:` attiva la modalità implicita, una probabilità dell'1% per ogni parametro, e la scrittura che più somiglia a «non voglio deviazione» fa dunque l'opposto; per disattivare si scrive `false` o si omette la chiave. Se si dichiara una probabilità senza un `_range` esplicito, il motore applica una microvariazione predefinita, il *jitter* implicito (±1,5 dB sul volume, ±15 gradi sul pan, ±5 ms sulla durata, ±12 cent sull'altezza), che è la decorrelazione di cui parla Vaggione, e che rende una massa granulare più organica e meno meccanica [@Vaggione2002].


# L'architettura multi-voce

Finora lo stream è stato una voce sola. PGE ne prevede $N$, e il modello sono le voci parallele del DMX-1000 di Truax, la cui molteplicità fissa la densità in verticale (capitolo 1). Le voci di PGE non sono però generatori indipendenti: sono copie di una voce di riferimento, ciascuna con scarti propri. È l'ultimo scostamento dell'esposizione del paper [@DeMattia2026Cim]: dopo la risintesi, la posizione di lettura, la griglia, il grano e la deviazione, si moltiplica lo stream di partenza. Le affermazioni sul comportamento del motore sono controllate, una per una, dallo script `esempi/multivoce/verifica_multivoce.py`.

## Che cos'è una voce

Una voce è una lista di grani. Lo stream calcola, per ciascuna, la stessa produzione di grani della voce di riferimento, e a ogni grano applica quattro scarti: di altezza (un fattore sul rapporto), di posizione di lettura, di pan e di onset. Gli scarti viaggiano in un oggetto minimo, un dato congelato come il grano, che il `VoiceManager` costruisce a ogni grano interrogando quattro strategie indipendenti, una per asse, che ricevono l'indice della voce, il numero massimo di voci e il tempo, e non conoscono il resto dello stream. Gli assi sono ortogonali, e qualunque combinazione è valida. La voce 0 è il riferimento e non riceve scarti da nessuna strategia: perciò uno stream con `num_voices: 1` è identico a uno senza il blocco `voices`. Ogni voce ha un proprio cursore del tempo e produce una propria lista, e la densità dichiarata vale per ogni voce: con 4 voci e 10 grani al secondo per voce, la densità complessiva è di 40 grani al secondo. Le strategie ricevono il numero *massimo* di voci, il picco di `num_voices`, e non quello attivo in quell'istante, per cui una voce che si accende non sposta le altre.

La scala degli scarti decide che cosa si ascolta. Con scarti di onset di pochi millesimi di secondo le voci sono versioni sfasate dello stesso evento: nel DMX-1000 le voci avviate in istanti diversi hanno rapporti di fase diversi, e ne risulta un'ampiezza variabile per cancellazione e rinforzo [@Truax1988, p. 18]. Sul piano percettivo è la decorrelazione microtemporale di cui parla Vaggione: la massa si ispessisce e acquista direzione [@Vaggione2002]. Con scarti più lunghi della durata del grano le voci non si sovrappongono più nel tempo e diventano eventi distinti, e lo stesso meccanismo produce polifonia. Il sistema non distingue i due regimi: sono lo stesso strumento a scale diverse.

## Onset, pointer, pan e pitch

Tre assi su quattro hanno strategie della stessa famiglia: lo scarto cresce con l'indice della voce (`linear`, che per il pan si chiama `step`, e per l'onset anche `geometric`), oppure è estratto a caso (`stochastic`); per il pan c'è inoltre `range`, un ventaglio di ampiezza data. Ogni chiave accetta un numero o un inviluppo, quindi uno scarto può variare nel tempo e un cluster può aprirsi in un ventaglio. Le strategie stocastiche estraggono lo scarto di ogni voce una volta sola, e lo conservano: la direzione dello scarto resta stabile, e ciò che varia nel tempo, seguendo l'inviluppo, è soltanto la sua grandezza. Il generatore è derivato dal seme, dall'identità dello stream e dall'indice della voce, e non dipende dal numero delle voci: aggiungerne una lascia dove sono gli scarti delle altre. Lo scarto di pan è un angolo (capitolo 5) che si somma al `pan` dello stream, e la spazializzazione agisce quindi a due livelli annidati: la strategia assegna a ciascuna voce il proprio angolo, e `pan_range` aggiunge a ogni grano di quella voce una deviazione attorno a quell'angolo.

Il pitch di una voce è un fattore moltiplicativo sul rapporto di lettura, prodotto da un'unità di altezza della stessa famiglia del blocco `pitch` dello stream (capitolo 5); senza `unit` valgono i semitoni. Le strategie `step` (la voce $i$ sta a $i \cdot \mathit{step}$ semitoni), `range` (le voci si distribuiscono in parti uguali fra 0 e `pitch_range`) e `stochastic` (un valore fisso per voce fra $-$`pitch_range` e $+$`pitch_range`) emettono una posizione adimensionale, che l'unità materializza in un fattore: con 4 voci, `step: 3` dà 0, 3, 6 e 9 semitoni. Le strategie armoniche sono definite per costruzione in semitoni. `chord` assegna alla voce $i$ l'$i$-esima nota di un accordo nominato (`maj`, `min`, `dom7`, `maj7`, fino a `altered`, di sette note), esteso per ottave se le voci sono più delle note. `chord_progression` fa dell'accordo una funzione del tempo, e la chiave `voice_leading` decide come le note del nuovo accordo si abbinano alle voci: il caso predefinito, `nearest`, fa muovere ogni voce il meno possibile e tiene ferme le note comuni. `spectral` mette la voce $i$ sul parziale $i+1$ della serie armonica, a $\mathrm{round}(12\log_2(i+1))$ semitoni: 0, 12, 19, 24, 28, 31, 34 e 36 per le prime otto voci.

## Il numero di voci e le dissolvenze

Il numero di voci, `num_voices`, è un valore fisso o un inviluppo, e va da 1 a 256. Il valore interpolato può essere frazionario: le voci intere suonano a volume pieno, e la parte decimale diventa un fattore di volume sulla voce di confine, quella che si sta accendendo o spegnendo. Con $f$ la parte frazionaria, la voce di confine suona di $20\log_{10} f$ decibel, un numero negativo: $-6$ dB per $f = 0{,}5$ e $-12$ dB per $f = 0{,}25$. Con interpolazione a gradini e punti interi le voci si accendono e si spengono di colpo; con interpolazione lineare o cubica la transizione fra due conteggi interi diventa una dissolvenza, guidata dall'inviluppo e senza numeri casuali.

Un secondo controllo governa quanto le voci siano indipendenti nel tempo. Il capitolo 2 ha ricordato che il trattamento canonico della granulazione ha due controlli distinti, il ritardo fra i grani di un flusso e il grado di sincronicità fra flussi diversi [@Dutilleux2016]. Il primo lo governa la griglia, descritta nel capitolo 5; il secondo è `scatter`, un numero da 0 a 1, anche come inviluppo. L'intervallo di una voce è la combinazione lineare dell'intervallo condiviso, calcolato per la voce 0, e di uno indipendente, pesata da `scatter`: a 0 tutte le voci condividono la sequenza di intervalli della voce 0, a 1 ciascuna calcola la propria. Con $s$ uguale a `scatter` e griglia stocastica, la correlazione fra gli intervalli di una voce e quelli della voce 0 vale $(1-s)/\sqrt{(1-s)^2+s^2}$: 1 a $s=0$, circa 0,71 a $s=0{,}5$, 0 a $s=1$. `scatter` si distingue dallo scarto di onset, che è uno sfasamento fisso: non ritarda le voci, decide se la loro scansione temporale sia la stessa. L'inviluppo di `scatter` diventa così il passaggio da un'unica nuvola coerente a più nuvole indipendenti.

## Un esempio completo

L'esempio del paper (`voices`) mette insieme le quattro strategie e i due inviluppi di insieme, su uno stream di quaranta secondi. Il numero di voci passa da 50 a 7 e a 70, e ogni voce ha la densità dello stream: sono 70 liste e 30 648 grani. Il passo di pitch è di un'ottava per voce, e il motore non pone un limite al fattore di una voce, perché i limiti dell'altezza valgono per il blocco `pitch` dello stream: con 70 voci la più alta sta 69 ottave sopra la voce 0. Come il linguaggio del capitolo 4, anche il blocco `voices` non protesta davanti a ciò che non vincola (con 10 voci o più, `voice_leading: nearest` ripiega in silenzio su `positional`).

![Lo stream completo con le voci. Ogni voce traccia una banda orizzontale sulla posizione di lettura; il colore ne codifica la trasposizione. Le bande sono fitte e dense di grani in apertura, si diradano verso il centro, dove il numero di voci è minimo e i singoli onset diventano leggibili, e si moltiplicano di nuovo in chiusura. Nella seconda metà le bande, all'inizio allineate sulla stessa griglia temporale, si sfasano fino a confondersi in una nuvola diffusa.](docs/images/voices_map.pdf){width=100%}


# Il rendering audio

Finora i capitoli hanno seguito la costruzione dei grani. Al termine della fase algoritmica il motore possiede una lista di oggetti `Grain`, ciascuno con otto campi, e nessun campione audio. Il rendering trasforma quella lista in un file. Il sistema offre tre modi di farlo: due traducono la lista in un linguaggio di sintesi esterno (Csound e SuperCollider), uno la rende direttamente in Python (NumPy). Seguono la cache, che evita di ripetere il lavoro già fatto, e il modello di costo di quello che resta.

## Tre motori, un solo grano

I tre renderer condividono la lista di grani e la definizione di che cosa un grano sia, e questo è quanto basta a renderli intercambiabili. Il DSP di un grano è lo stesso in ogni motore, ed è breve: si legge il campione sorgente a partire dalla posizione `pointer_pos`, avanzando di `pitch_ratio` campioni sorgente per campione di uscita; si moltiplica la lettura per la finestra, stirata sulla durata del grano; si moltiplica per l'ampiezza, ricavata dal volume in decibel, $A = 10^{v/20}$; si distribuisce il risultato sui due canali con la matrice Mid-Side del capitolo 5, a potenza costante:

$$ L = \frac{s\cos\theta + s\sin\theta}{\sqrt{2}}, \qquad R = \frac{s\cos\theta - s\sin\theta}{\sqrt{2}} $$

dove $s$ è il grano finestrato e $\theta$ l'angolo `pan` in radianti. Il risultato è la somma, in un buffer stereo, di tutti i grani posti al loro onset: un *overlap-add*. Un motore solo avrebbe bastato a produrre un suono. I tre motori servono a un altro scopo: rendere il rendering falsificabile. Con due motori, quando divergono non c'è un terzo parere, e quando concordano non si sa se hanno ragione o se condividono lo stesso assunto. Un terzo motore, scritto con strumenti diversi, toglie entrambe le incertezze. Nel capitolo 3 l'indipendenza del nucleo dal renderer appariva come un principio di ordine; qui è la condizione che rende possibile questo controllo.

## Csound: generazione della partitura

Csound è il renderer storico del sistema. Generare la partitura Csound con un programma, invece di scriverla a mano, ha un precedente diretto in CMask [@Bartetzki1997]. In PGE il file `.sco` è un artefatto di compilazione e non il documento che il compositore scrive: il documento è lo YAML. Il `.sco` dello stream minimo del capitolo 4 ha una tabella di funzione per il campione, una per la finestra e un evento per ciascun grano:

```
i "Grain" 0.00000000 0.05000000 0.000000 1.000000 0.00 0.000 1 2
i "Grain" 0.02500000 0.05000000 0.025000 1.000000 0.00 0.000 1 2
```

Le colonne sono, nell'ordine, onset e durata in secondi, posizione di lettura nel sample in secondi, rapporto di altezza, volume in decibel, pan in gradi, numero della tabella del sample e numero della tabella della finestra: gli otto campi del `Grain`, più il nome dello strumento. La partitura non contiene alcun codice di sintesi: il lavoro lo fa l'orchestra `csound/main.orc`, scritta una volta e a mano, che è in sostanza i quattro passi della sezione precedente. Onset e durata sono scritti con otto decimali, e non per estetica: a 96 kHz un grano può durare un solo campione, cioè poco più di dieci microsecondi, e un formato più avaro lo troncherebbe.

## NumPy: sintesi diretta per overlap-add

Il renderer NumPy è il motore interno. Non richiede alcun programma esterno ed è il renderer predefinito della funzione `render_file` dell'API. `GrainRenderer` è la traduzione in Python dello strumento Csound, ed è una funzione pura: non legge né scrive stato e non estrae numeri casuali, e questa purezza rende il rendering parallelizzabile. Si alloca un buffer stereo in doppia precisione; per ogni grano si calcola il campione di partenza a partire dall'onset e si somma il grano nel buffer; poi il buffer attraversa due passi prima di essere scritto: la rimozione dell'offset in continua, con un filtro FIR a fase lineare che sottrae al segnale la sua media mobile (taglio predefinito 20 Hz, un compromesso dichiarato), e un clip tra $-1$ e $1$. Non c'è normalizzazione: il livello è quello che i volumi dei grani determinano.

La difficoltà del parallelismo non è il parallelismo in sé, ma il suo rapporto con la riproducibilità del capitolo 3. La *generazione* dei grani, che consuma numeri casuali, resta in un solo processo, e solo la *somma* dei grani, un'operazione senza stato, si distribuisce su un pool di processi (opzione `--jobs`). Il contratto di determinismo è questo: con `--jobs 1` i campioni coincidono bit a bit con quelli del rendering sequenziale originario; a parità di `--jobs`, due esecuzioni producono gli stessi campioni; tra valori diversi di `--jobs` cambia soltanto l'ordine delle somme in doppia precisione, e la differenza massima sta sotto un bit meno significativo a 24 bit, quindi non è udibile.

## SuperCollider in modalità non real-time

SuperCollider è il terzo motore. La scelta non nasce dal bisogno di un suono diverso: nasce dalla funzione di controllo descritta all'inizio del capitolo. SuperCollider rende già in non-realtime (`scsynth -N` legge uno score da file e scrive il risultato in un file audio, senza passare per una scheda audio), e il problema, perciò, non era far suonare SuperCollider, ma non introdurre un terzo comportamento. Un motore nuovo che reimplementa le finestre, la conversione dei decibel o la soglia dei grani cortissimi aggiunge un dialetto, e non un controllo. Il disegno risolve la questione spostando le decisioni dalla SynthDef allo score, e quindi su Python, dove esistono già: le finestre sono tabelle riempite dal registro delle finestre di NumPy, e le conversioni di unità si fanno in Python prima di entrare nello score. Resta la lezione operativa del backend: `scsynth` esce con codice zero anche quando non ha reso niente (con un sample mancante l'audio è puro silenzio), e il codice d'uscita non dice la verità; la dice l'artefatto, per cui il renderer verifica che il file audio esista e non sia vuoto.

## Cache degli stream e costo computazionale

Rendere una composizione intera costa, e modificare un solo stream e doverla rifare da capo rende lenta la composizione iterativa, che consiste proprio nel ritoccare. La cache incrementale funziona per stream, in modalità stem, con tutti e tre i renderer. Per ogni stream il sistema calcola un'impronta (*fingerprint*) SHA-256 del dizionario YAML dello stream e la confronta con quella salvata dopo l'ultimo rendering riuscito: uno stream è *sporco* (*dirty*) se l'impronta è cambiata, se manca dal manifesto o se il suo file audio non esiste più, altrimenti il rendering lo salta. Entrano nel calcolo anche le cose da cui lo stem dipende e che lo YAML non dichiara: la versione delle regole di variazione, il renderer (senza, passare da Csound a NumPy lascerebbe ogni stream *pulito*) e il seme, ma solo se il documento lo dichiara. Il controllo avviene *prima* di leggere le voci dello stream, ed è la ragione della generazione *lazy* descritta nel capitolo 3. L'impronta non copre il codice del DSP scritto a mano né il contenuto del file sorgente.

La domanda pratica di chi compone in tempo differito è quanto ci voglia, e la risposta ingenua sbaglia in entrambi i versi: non è «quanto dura il pezzo», perché il motore somma segmenti, ma nemmeno «il numero di grani», perché il buffer di uscita va comunque allocato, elaborato e scritto. Il costo ha due termini indipendenti,

$$ t = a\,N + b\,D $$

dove $N$ è il numero di grani e $D$ la durata dell'uscita in secondi. Una regressione ai minimi quadrati su 23 misure, da cento a trentamila grani e da cinque a 320 secondi, su un Apple M2 Max con Python 3.11 e rendering sequenziale, dà $a$ di circa 34 µs per grano e $b$ di circa 1,4 ms per secondo di uscita, con un errore relativo mediano sotto l'1%. I due termini pareggiano a circa 40 grani al secondo: nel regime granulare d'uso, ben sopra, il costo lo governa la popolazione dei grani e non la lunghezza del brano. Due rendering reali mostrano come si ripartisce il tempo: `PGE_ff2_rassegna.yml`, 221 082 grani in 1 698 s di uscita, richiede 14,95 s, di cui 1,72 s per costruire i grani; `PGE_cim.yml`, 994 555 grani in 92,5 s, richiede 30,22 s, di cui 9,73 s di costruzione. Nel regime denso, materializzare la popolazione dei grani costa quanto una parte consistente della sintesi. È il prezzo del disegno del capitolo 3: la lista di grani esiste come oggetto ispezionabile prima di diventare campioni, e questo rende possibili la MAP, le esportazioni e il debugging. In memoria ogni grano pesa circa 225 byte.


# La MAP e l'esportazione

La lista di grani, che nel capitolo 3 è stata presentata come rappresentazione intermedia, ha altri consumatori oltre ai renderer audio. Questo capitolo tratta i quattro che non producono suono. Il primo è la MAP (*Multiparametric Audio Plot*), un'immagine sinottica del rendering. Gli altri tre sono esportazioni verso strumenti esterni: una sessione di Sonic Visualiser, un progetto Reaper, un file JSON. La MAP e il JSON leggono la stessa lista di grani che il renderer legge per fare i campioni; Reaper e Sonic Visualiser leggono gli stream già costruiti, cioè onset, durata e curve dei parametri. Nessuno rilegge lo YAML.

Questa è la differenza che conta tra la specifica e la MAP. Lo YAML è una notazione prescrittiva nel senso di Seeger [@Seeger1958]: dice al motore che cosa fare. La MAP è descrittiva: documenta ciò che il motore ha fatto davvero, con i valori che le variabili casuali hanno assunto in quella realizzazione, e non viene mai riletta come input. Una MAP di uno stream con deviazione probabilistica mostra i grani che sono usciti, non le probabilità dichiarate. Per questo gli esempi dei capitoli precedenti si compongono di un listato YAML (nella cartella `esempi/`) e della MAP del suo rendering: il primo è la causa, la seconda è l'effetto.

## Il grano come freccia nello spazio del materiale

L'idea di vedere il controllo granulare invece di leggerlo non è nuova. La figura 4 di Truax [@Truax1988, p. 24] sovrappone maschere di tendenza e inviluppi su un terminale a 24 righe, con il tempo in ascissa e il valore del parametro in ordinata, e Truax definisce questo modo di lavorare «*inherently a visual control method*» [@Truax1988, p. 23]. Sono le curve *dichiarate*, e nelle MAP di questa tesina occupano il pannello inferiore. I poligoni sul piano frequenza e tempo di Roads [@Roads1978, p. 62; @Roads1985cim, p. 200] descrivono invece la forma della nuvola, e la timeline di IRIN [@Caires2004] disegna i singoli eventi, con il numero di traccia in ordinata. Nella MAP l'ordinata è un'altra grandezza: il punto del materiale da cui ciascun grano proviene. Per un campionatore granulare è il parametro di prima classe, ed è quello che nessuno dei precedenti disegna.

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

Il pan non ha una variabile sul grano: si legge nelle curve del pannello inferiore, quando è dichiarato come inviluppo. Il colore appartiene a una scala divergente, centrata sulla trasposizione nulla, e l'opacità dei grani va da 0,3 a 1 sul volume tra -60 e 0 dB, così che i grani deboli restano visibili. La freccia è la forma di default, e il suo orientamento dice il verso di lettura del buffer; con `grain_shape: window` il bordo superiore del grano traccia invece la finestra che il grano usa.

L'altezza di un grano è «una porzione di buffer». Quale porzione, però, non è ovvio, e il disegno ne ha usata una per un certo tempo senza dirlo. La porzione di materiale che un grano attraversa è il prodotto della durata per il rapporto di altezza; il disegno storico usava soltanto la durata, cioè la porzione che il grano percorrerebbe leggendo a velocità normale. Le due misure coincidono solo quando il rapporto vale uno, che è il caso più comune, e per questo l'errore non si vedeva. L'esempio `grain_height` lo isola con grani radi e lunghi (0,4 secondi): a lettura ferma, il pitch scende di un'ottava e poi sale di un'ottava sopra l'altezza di partenza. Nel disegno storico la trasposizione si legge soltanto dal colore; con l'altezza uguale alla porzione letta la pendenza è un'informazione, ed è esattamente ciò che il renderer legge.

![L'esempio `grain_height`, con altezza del grano uguale alla porzione letta. A un'ottava sotto i grani leggono metà del materiale, a un'ottava sopra il doppio.](docs/images/grain_height_readspan_map.pdf){width=100%}

Il default resta la lettura storica, e la ragione non è prudenza: la geometria nuova cambia l'aspetto di ogni MAP già generata, e una figura che cambia forma sotto i piedi di chi l'ha stampata è un'altra figura, non la stessa più corretta. Per questo il modo attivo è dichiarato nell'etichetta dell'asse. Sotto il piano dei grani compaiono le curve dei parametri dichiarati come inviluppi, con i breakpoint annotati ciascuno col proprio valore, e una curva derivata che nello YAML non si può scrivere, la densità effettiva in grani al secondo. La lente risolve un problema di scala: una MAP che descrive decine di secondi non può mostrare i singoli grani di pochi millisecondi, che a piena pagina sono segmenti sub-pixel. La lente è un cerchio di ingrandimento puntato su un istante e una posizione di lettura, e ogni lente proietta il proprio istante sul pannello degli inviluppi, con una verticale tratteggiata e un marker sul valore reale che ciascuna curva ha in quel punto: ciò che si vede ingrandito è collegato ai valori dei parametri che lo hanno prodotto.

La MAP è pensata per lo schermo: su carta in bianco e nero un grano calante e uno crescente diventano lo stesso grigio, e volume, pan e durata diventano tre linee uguali. L'opzione `--bw` seleziona perciò una scala di grigi monotona e curve che si distinguono per il tratto, al costo dichiarato di fissare l'opacità dei grani.

## Integrazione con Sonic Visualiser e Reaper

La MAP è un'immagine statica. Per ascoltare il materiale, ispezionarlo nel tempo o montarlo, il sistema esporta la lista dei grani, o le sue derivate, verso strumenti che sanno farlo, con la stessa regola della MAP: il motore scrive il file, e il file non torna indietro come input. `ReaperProjectWriter` scrive un progetto Reaper (`.rpp`) accanto ai file audio, in modalità a stem: ogni stream diventa una traccia, nominata con il suo `stream_id`, con un solo elemento posto all'onset dello stream e lungo quanto la sua durata. L'ascolto e il montaggio avvengono in Reaper, con effetti, automazioni e routing che PGE non conosce, e per questo la pulizia dell'output conserva i progetti per default: il file `.rpp` può contenere lavoro manuale che nessuno vuole perdere. `SVExporter` scrive una sessione di Sonic Visualiser (`.sv`) che si apre con la forma d'onda dell'audio renderizzato e con un livello per ogni inviluppo del motore, già impaginati e sincronizzati sul tempo del file; il tipo di interpolazione diventa stile del livello e i colori sono quelli della MAP. La MAP e Sonic Visualiser rispondono a due domande diverse: la prima dà un colpo d'occhio sulla struttura, la seconda permette di ascoltare, ingrandire e confrontare una curva con ciò che si sente. L'ultima esportazione è un file JSON per ogni stream, in forma compatta: la durata, il numero di voci e, per ogni grano, sei campi. Il consumatore previsto è PGE-ui, l'interfaccia grafica del motore, che disegna i rettangoli dei grani nella clip di ogni stream e li colora per altezza.

Le quattro uscite mostrano all'opera la scelta del capitolo 3: il motore costruisce i propri oggetti una volta, e chi li consuma li legge. Aggiungere un'uscita significa scrivere un lettore, non toccare il motore. È anche il motivo per cui l'esportazione non rifà il lavoro di sintesi: il costo del rendering audio, descritto nel capitolo 7, non ricade su queste uscite, che leggono soltanto ciò che il motore ha già costruito, con un costo proprio che non è stato misurato qui.


# Metodo di sviluppo

PGE è uno strumento per comporre, ma è anche un progetto software che dura da dieci mesi, con una storia da ricostruire. Il primo commit risale al 17 dicembre 2025 e l'ultimo, al momento della scrittura, al 13 ottobre 2026: 1 321 commit, trenta versioni rilasciate dalla 1.0.0 del 23 marzo alla 9.1.0 del 27 settembre. Il pacchetto conta circa 26 400 righe di Python, e la suite di test circa 86 800, con 164 file di test e circa 8 450 test eseguiti per default. Un rapporto di oltre tre righe di test per ogni riga di codice non è un vanto: è la conseguenza di un metodo, e questo capitolo lo descrive.

Una nota sul modo di lavorare precede il resto. Lo sviluppo è avvenuto in dialogo con un modello linguistico, Claude Code, che opera nel repository sotto la direzione dell'autore. Lo dichiara la storia stessa: 682 dei 1 321 commit portano Claude come autore. Il dialogo è reso possibile da una scelta del capitolo 3, la specifica in testo versionato, ed è regolato da un file di istruzioni (`CLAUDE.md`) che fissa il processo: la lingua, i test da superare prima di ogni commit, le analisi d'impatto, la forma delle pull request. Un collaboratore che non ricorda la sessione precedente ha bisogno che il metodo stia scritto nel repository, e un metodo scritto è anche un metodo verificabile da una macchina.

## Sviluppo guidato dai test

La regola di fondo è lo sviluppo guidato dai test, nel ciclo rosso-verde-refactor: per una funzionalità nuova o per un cambio di comportamento si scrive prima il test e se ne verifica il fallimento, poi si scrive il codice che lo fa passare. Prima di ogni commit, di ogni pull request e di ogni etichetta di versione la suite deve essere verde. La suite ha due strati: i test unitari e quelli tra componenti, veloci, girano di default; i test *end-to-end* invocano `make` come lo invocherebbe chi usa il sistema, e coprono la catena completa (la cache incrementale, gli errori del motore, l'esportazione Reaper, i renderer NumPy e SuperCollider). L'integrazione continua esegue la suite unitaria su sei versioni di Python, dalla 3.9 alla 3.14, e i test di integrazione con Csound e SuperCollider installati su una macchina pulita.

Una parte della suite è scritta per trasformare in errore alcune convenzioni, perché un'architettura regge finché nessuno la scavalca e la regola che la tiene in piedi è di solito soltanto una convenzione. Due esempi bastano. La sintassi di Csound sta in un modulo solo: è la regola del capitolo 3, e senza il test sarebbe un'intenzione. Il nome di un file di test è invece una promessa: `tests/<area>/test_<modulo>.py` dice di sorvegliare `src/pge/<area>/<modulo>.py`, e un test del contratto della suite pretende che il file importi il modulo che nomina e che non ne riscriva le classi pubbliche. Il caso che l'ha fatto nascere è istruttivo. Un file di 72 test, intitolato a `Parameter`, in 63 casi collaudava una copia di `Parameter` riscritta nel file stesso, e la riscrittura non fallisce mai, perché resta coerente con sé stessa anche il giorno in cui il modulo vero cambia comportamento.

## Documentazione e versionamento

La documentazione del motore segue la tassonomia Diátaxis [@procida2017diataxis]: quattro tipi di testo con funzioni diverse, che non vanno mescolati. Il repository ne usa tre: i testi di *riferimento* (la sintassi YAML, la riga di comando, gli errori), quelli *esplicativi* (undici documenti) e quelli di *procedura* (undici). La struttura è imposta: ogni documento ha un'intestazione con il proprio tipo, lo stato, l'elenco dei file di codice di cui parla e l'identificativo dell'ultimo commit in cui è stato verificato, e un controllo automatico (`make docs-lint`) verifica che l'intestazione sia completa, che i file citati esistano, che l'identificativo del commit sia risolvibile e che i rimandi tra documenti puntino a documenti reali. È il modo in cui la documentazione smette di essere un'affermazione e diventa un oggetto verificabile: se un file di codice citato sparisce, il controllo fallisce, e il documento non può più restare silenziosamente fermo a una realtà passata.

I lavori di una certa taglia cominciano con un piano in `docs/plans/`: un piano dice che cosa si è deciso *prima* di scrivere il codice, e un documento esplicativo dice che cosa è rimasto vero *dopo*. Le modifiche si registrano in un changelog nel formato Keep a Changelog [@lacan2017changelog], e le versioni seguono il versionamento semantico [@prestonwerner2013semver]; le versioni principali portano anche un nome, da *Range Anchor* (6.0.0) a *Quiet Stdout* (9.1.0). La versione descritta in questa tesina è archiviata con un identificativo permanente [@DeMattia2026Pge].

## Il language server PGE-ls

Un linguaggio dichiarativo si scrive meglio con un editor che lo capisce. PGE-ls è un *language server* per lo YAML di PGE, secondo il Language Server Protocol [@microsoft2016lsp]: un processo che l'editor interroga e che risponde con completamenti, descrizioni e diagnosi. Ha client per VSCode e per Neovim, ed è un repository a sé, con 77 commit e circa 11 000 righe di Python. Si appoggia a un analizzatore YAML *tollerante*, che non solleva mai eccezioni su un documento incompleto, perché un testo in scrittura è quasi sempre incompleto.

Il language server è anche un caso di studio sul costo del disegno dichiarativo. Contiene alcune parti del motore *copiate a mano* (i nomi delle strategie di voce, gli accordi, i limiti delle unità di altezza, i nomi delle finestre), e una copia può divergere dall'originale senza che nessun altro test se ne accorga: il rimedio è un test di *parità*, che importa il sorgente vero del motore e lo confronta con le copie. Ha un limite, perché copre le superfici che si è deciso di elencare e non le altre: il server segnala come mancante il campo `onset` di uno stream, mentre il motore lo tratta come facoltativo. È il principio che regge il metodo: una regola scritta ma non verificata invecchia, e il costo del disegno dichiarativo è mantenere allineati gli strumenti che lo leggono.


# Uso compositivo

PGE è nato per comporre, e questo capitolo lo mostra in uso. Il caso è *mare-nostrum*, un brano elettroacustico dell'autore. Il capitolo non è un'analisi: descrive come il brano è fatto e come lo strumento ne ha accompagnato il lavoro. Lo stato descritto è quello del repository del brano al commit `a26b0f8`; i numeri si ricontrollano con lo script `esempi/mare-nostrum/verifica_brano.py`. Gli esempi dei capitoli precedenti isolano un meccanismo alla volta; un brano li usa tutti insieme, e il rapporto fra i parametri diventa la materia del lavoro.

<!-- TODO(giulio): questo capitolo è una bozza ricostruita dai file dei repository (mare-nostrum, granulation-studies, PGE) e dalle tue risposte. Le parti segnate TODO sono quelle che solo tu puoi scrivere: le decisioni di forma. -->

## Il brano

*mare-nostrum* è un brano costruito con i lamenti e i pianti di bambini, trasformati in suono di mare. Il materiale di partenza è un corpus di registrazioni numerate di pianti di bambini, generiche e trovate in rete, da cui il brano usa nove campioni. Cinque sono frammenti ritagliati, che portano nel nome il punto del taglio (`001-41_5-5_5.wav`, per esempio, che dai nomi e dalla configurazione degli studi sembra essere la registrazione 001, a partire da 41,5 secondi, per 5,5); gli altri quattro portano soltanto un numero (`004.wav`, `007.wav`, `011.wav`, `016.wav`). La trasformazione è la granulazione. Nel primo gruppo di stream, presentato più avanti, è la granulazione fine del capitolo 2: pochi millisecondi per grano, tanti grani sovrapposti, un puntatore che avanza lentamente nel frammento. A questa scala un grano da solo non porta un evento riconoscibile: il materiale tende a un suono continuo, di cui il frammento fornisce soprattutto il colore spettrale. Sotto i circa 40 ms i suoni campionati perdono le loro qualità identificabili [@Roads2001, p. 189]; Truax pone a 50 ms la soglia sotto cui domina la fusione dei frammenti a frequenza audio, mentre sopra dominano le qualità timbriche della sorgente [@Truax1988, pp. 18-19]. I grani di quegli stream, da meno di un millisecondo a diciotto, stanno al di sotto di entrambe le soglie. Il brano però non sta più tutto in questo regime: le durate dichiarate dei suoi grani vanno da 0,1 millisecondi a 3 secondi.

### La poetica: il mare e l'indifferenza

*mare-nostrum* parla dell'indifferenza di chi riposa al mare mentre, dall'altra parte dello stesso mare, i bambini stanno morendo. È una critica del disinteresse verso i nostri fratelli, e più in generale di una vita borghese che pensa soltanto ai propri problemi e non si rende conto che le scelte del governo, di cui ci si disinteressa, portano alla morte di migliaia di persone. Il brano non vuole rappresentare questa indifferenza: vuole romperla.

La drammaturgia è costruita con la materia stessa del brano. Il suono è un mare, realizzato con pianti di bambini granulati; a poco a poco il pianto emerge dalle onde, finché a un certo punto emerge un coro di persone morte. Per un tratto chi ascolta può prendere quel suono per un mare qualunque, poi il pianto affiora e l'ascolto non può più essere indifferente.

La progressione si legge nei dati del brano, e non dipende dalla sola durata del grano. Gli stream del primo gruppo hanno grani di pochi millisecondi, sotto le soglie di riconoscibilità citate sopra, e il pianto vi si fonde in una texture continua. Con `stream22` (secondo 342) e `stream23` (secondo 424) i grani durano da uno a tre secondi. Il coro è `stream23`: lo stesso pianto (`007.wav`), con grani di 3 secondi e un `duration_range` di 1 secondo, e quindi non propriamente grani ma frammenti. Il rapporto di altezza è 0,3 con una banda di 0,4, e le quattro voci sono distribuite con la strategia `range` su un intervallo di 38 quarti di tono: quattro pianti trasposti verso il grave e a altezze diverse, che si ascoltano come un coro. Le curve di `density` (da 2,5 a 53 grani al secondo) e di `volume` (da -80 dB fino a -4,8 dB poco prima della fine) sono disegnate per ricreare le onde del mare. Il coro entra a 424 secondi e suona fino a 577, per due minuti e mezzo, mentre il brano arriva a 581.

Il coro mostra anche un limite dello strumento. PGE oggi ammette un solo file audio per stream e un solo livello di granulazione. A grani lunghi e non microgranulati il frammento si riconosce troppo come registrazione, la magia della granulazione fine si rompe e il suono connota in un altro modo: è un limite dello strumento, e le conclusioni lo indicano come direzione di lavoro, con una granulazione annidata in cui frammenti lunghi, scelti da più file, sono a loro volta granulati.

L'esecuzione è pensata per otto altoparlanti disposti in un cerchio attorno al pubblico, con la decodifica al concerto: il metodo è nel capitolo 11.

### Dal materiale al mare: uno studio sui parametri

Il bersaglio è un percetto, la *connotazione della marea*, come lo chiama il diario di ascolto dell'autore, e non una configurazione. Per raggiungerlo l'autore ha costruito sopra PGE un piccolo laboratorio di studi, che vive nello stesso repository del brano. Uno studio dichiara uno stream di base, preso dal brano, e uno o più assi che si muovono mentre il resto sta fermo.

### La struttura

Il brano è un file YAML principale, il *master*, che tiene la testa del brano (il seme 1441 e la durata) e dispone gli stream nel tempo. Ogni stream vi compare come voce `file:`, che importa uno stream da un file (capitolo 4), e il master ne tiene soltanto il piazzamento. Il brano ha sedici stream e dura 581 secondi, nove minuti e quarantun secondi. La `duration` del master, 591 secondi, è dieci secondi più lunga dell'ultimo stream. La figura mostra la disposizione degli stream.

![La disposizione degli stream del brano *mare-nostrum*. Una riga per stream, in ordine di ingresso; il colore indica il campione sorgente, che il nome fra parentesi ripete; a destra o a sinistra delle barre, il numero di voci quando è maggiore di uno.](docs/images/mare-nostrum_disposizione.pdf){width=100%}

Il brano ha due gruppi. Nel primo, da 0 a 278 secondi, entrano uno dopo l'altro nove stream, fino a sette sovrapposti fra i secondi 117 e 125, e poi escono, finché resta il solo `stream8`. Un respiro di 0,8 secondi lo separa dal secondo gruppo, da 279 a 581 secondi, più rado, da uno a cinque stream alla volta. Comincia con il solo `stream24`, per oltre un minuto. Fra 414 e 440 secondi il secondo gruppo riprende tre stream del primo: `stream25`, `stream27` e `stream26` riprendono `stream6`, `stream9` e `stream3`, con lo stesso campione e quasi tutti gli stessi valori. Cambiano la durata, la durata del grano e il verso di lettura; in `stream26` cambiano anche la finestra e lo scarto del puntatore, e la durata del grano è fissa a 6 millisecondi invece che in rampa. Anche il primo gruppo ha una ripresa, `stream6-2`, che entra a 117 secondi, subito dopo la fine di `stream6`: stesso campione, grani fissi di 1 millisecondo e lettura sempre all'indietro. Il brano finisce con `stream26`, che suona da solo gli ultimi 3,9 secondi. La tabella riassume i dati che definiscono ciascuno stream; il numero di grani è quello che il motore, alla versione che il repository del brano fissa, produce con il seme dichiarato.

| Stream | Campione | Onset (s) | Durata (s) | Grano | Voci | Grani |
|---|---|---:|---:|---:|---:|---:|
| `stream2` | 001-41 | 0,0 | 178,5 | 1–9 ms | 1 | 304 042 |
| `stream3` | 001-47 | 0,2 | 249,2 | 0,8–8,4 ms | 4 | 1 499 017 |
| `stream9` | 001-47 | 11,1 | 249,2 | 0,4–11 ms | 2 | 1 524 526 |
| `stream5` | 001-18 | 43,8 | 81,5 | 1,1–4,1 ms | 1 | 112 093 |
| `stream6` | 001-3 | 56,7 | 55,4 | 1–5 ms | 1 | 170 570 |
| `stream10` | 001-41 | 107,0 | 146,2 | 1–8 ms | 4 | 633 356 |
| `stream7` | 001-65 | 112,0 | 26,4 | 1–18 ms | 1 | 34 053 |
| `stream6-2` | 001-3 | 116,9 | 33,0 | 1 ms | 1 | 131 601 |
| `stream8` | 001-3 | 146,0 | 131,8 | 1–11 ms | 1 | 190 663 |
| `stream24` | 016 | 278,6 | 87,4 | 0,1 ms | 4 | 2 727 140 |
| `stream21` | 004 | 341,5 | 94,1 | 1–19 ms | 1 | 22 201 |
| `stream22` | 011 | 342,2 | 129,2 | 1–3 s | 1 | 2 296 |
| `stream25` | 001-3 | 414,1 | 88,3 | 1–5 ms | 1 | 302 955 |
| `stream27` | 001-47 | 415,0 | 151,9 | 0,4–9,2 ms | 2 | 1 452 100 |
| `stream23` | 007 | 424,1 | 152,9 | 3 s | 4 | 12 428 |
| `stream26` | 001-47 | 440,0 | 141,0 | 6 ms | 4 | 376 309 |

In totale il brano ha 9 495 350 grani, circa 9,5 milioni, e più del 60% sta in tre soli stream: `stream24`, `stream9` e `stream3`. Il modello di costo del capitolo 7 (circa 34 microsecondi per grano e 1,4 millisecondi per secondo di uscita, a un processo solo) prevede per il rendering poco più di cinque minuti: è una stima, non una misura.

<!-- TODO(giulio): descrivere la forma. Il master mostra due gruppi di stream (ingressi a 0, 0,2, 11, 44, 57, 107, 112, 117 e 146 s; poi da 279 a 440 s), ma non dice perché: perché il secondo gruppo comincia con il solo stream24 e riprende `stream6`, `stream3` e `stream9` fra 414 e 440 s; quale direzione prende il brano. Il CONTEXT.md di mare-nostrum chiama «drammaturgia» il ritmo fra ridondanza e novità e la rimanda a una fase successiva: qui si può dire a che punto è. -->

### Due vocabolari

I nove stream del primo gruppo e le tre riprese del secondo, dodici in tutto, sono parenti, scritti con lo stesso vocabolario: fattore di riempimento 4 (in undici su dodici), durate dei grani per lo più fra uno e dieci millisecondi, puntatore a un decimo della velocità reale o meno (la velocità sale a 0,35 soltanto in `stream8`) con un piccolo scarto di lettura, verso di lettura invertito più volte lungo lo stream (capitolo 5, in undici su dodici), rapporto di altezza 0,2 in sette stream, 0,5 in due e 1 in tre, pan su una banda di 360 gradi. Quattro stream escono da questo vocabolario. `stream24` scende a grani di 0,1 millisecondi, circa cinque campioni a 48 kHz, con quattro voci e il gate di probabilità al 40% (capitolo 5): è lo stream più pesante, con 2,7 milioni di grani e oltre 35 000 al secondo. `stream22` e `stream23` salgono a grani da 1 a 3 secondi, da dieci a trenta volte il limite di 100 ms con cui Roads definisce il grano [@Roads2001, p. 86]: a quella scala un grano è un frammento della registrazione e non una particella, e i grani sono pochi (2 296 e 12 428), anche se si sovrappongono fino a 102 e a 615. `stream21` resta ai millisecondi e cambia l'uso della finestra, che passa da Hann a `rexpodec` dal 65% dello stream in poi, e dichiara un accordo che non suona, perché lo stream ha una voce sola.

### Il processo e la riproducibilità

Due aspetti del lavoro mostrano le scelte del sistema alla prova. Il primo è la riproducibilità. Il seme 1441 sta nel master e vale per tutto il brano, e la realizzazione di ciascuno stream dipende, come nel capitolo 3, dal seme, dall'identificativo dello stream e dal componente stocastico. Lo stream importato ha l'identificativo del nome del suo file, e di qui una conseguenza non ovvia: *rinominare il file cambia il suono*. L'autore ha scelto di legare l'identificativo al nome del file perché lo stream suoni uguale nel brano e quando lo si apre da solo nel laboratorio. Lo si verifica su `stream6`: duplicato con un altro identificativo ha un'altra realizzazione, e con lo stesso gruppo (`rng_group`, capitolo 4) ha gli stessi grani, spostati nel tempo. Prima del seme dichiarato ogni rendering era una realizzazione diversa: con il seme il brano è riproducibile, ma è diverso da tutti i rendering ascoltati prima, e va riascoltato prima di considerarlo valido. Il secondo è la divisione del lavoro fra i file, che il repository fa rispettare con un test: il master tiene il piazzamento (onset, silenziamento, solo), e il file dello stream tiene il suono. La regola è rispettata: tutte e sedici le voci del master, salvato da PGE-ui, sono `file:`.

## Il brano e i limiti dello strumento

Il brano è fatto di nove campioni, due vocabolari di stream, una disposizione nel tempo in due gruppi e un seme, e va eseguito da otto altoparlanti con la decodifica al concerto. Mostra anche dove lo strumento arriva al suo limite, e sono tre punti. Il primo è lo spazio: il pan di 360 gradi è scritto per una coppia stereo, perché i tre renderer sono stereofonici, e il passaggio a otto altoparlanti (capitolo 11) richiede un formato a tre canali che i renderer non scrivono. Il secondo è il coro: uno stream attinge a un solo file sorgente e la granulazione ha un solo livello, e a grani lunghi il frammento si riconosce come registrazione. Il terzo è il materiale: lo strumento governa il suono per posizione di lettura e non per contenuto. Le conclusioni li riprendono e ne fanno la direzione del lavoro.

<!-- TODO(giulio): aggiungere, se vuoi, un ascolto guidato o una MAP di un passaggio del brano. Una MAP dell'intero brano non è praticabile: sono 9,5 milioni di grani su sedici stream. Una pagina breve di MAP, su un passaggio a scelta, lo è, ma serve il corpus audio, che non sta nel repository. -->


# La spazializzazione per n altoparlanti

*mare-nostrum* è pensato per essere eseguito da n altoparlanti disposti attorno al pubblico, e non da una coppia stereo. PGE oggi produce soltanto audio stereo: il capitolo 7 ne dà la formula, e il capitolo 10 registra la resa nello spazio fra le questioni aperte. Questo capitolo spiega il metodo con cui il pan di PGE si estende a un numero qualsiasi di altoparlanti e indica il punto del motore in cui l'estensione si innesta. Non descrive una funzione che PGE già possiede: descrive il fondamento teorico, che è il lavoro di Alan Blumlein e di Michael Gerzon sulla codifica Mid-Side, e ciò che di esso il motore contiene già. Le formule e le cifre del capitolo si ricontrollano con lo script `esempi/spazializzazione/verifica_spazializzazione.py`.

## La codifica: una direzione, non una coppia di guadagni

Si chiami $\theta$ l'azimut di una sorgente, misurato in gradi a partire da davanti, positivo verso sinistra: è la stessa convenzione del `pan` di PGE (capitolo 5) e quella di Gerzon, che pone l'asse $x$ davanti e l'asse $y$ a sinistra [@Gerzon1973, p. 3]. Blumlein, nel 1931, registrò una scena con due microfoni a figura di otto coincidenti, orientati a $\pm 45$ gradi [@Blumlein1931]. Una figura di otto ha guadagno $\cos\alpha$ nella direzione verso cui punta, dove $\alpha$ è l'angolo fra la direzione della sorgente e quella del microfono, ed è nullo a $90$ gradi da essa. Due figure di otto a $90$ gradi l'una dall'altra, una puntata davanti e una a sinistra, danno a un segnale $s$ proveniente da $\theta$ i due segnali

$$ M = s\cos\theta, \qquad S = s\sin\theta $$

che sono il *mid* e il *side*. Gerzon li chiama $x$ e $y$ e vi aggiunge un terzo canale, $1$, omnidirezionale, che raccoglie il suono da ogni direzione con guadagno unitario [@Gerzon1975]. Qui il terzo canale si chiama $W$, e per un grano coincide con il grano stesso: $W = s$. Un solo numero, $\theta$, determina i guadagni di tutti e tre i canali. È ciò che il capitolo 5 intendeva dicendo che il grano porta un angolo e non una coppia di guadagni: la posizione è una direzione, e la sua traduzione in segnali è un'operazione a parte.

La coppia $(M, S)$ ha due proprietà che il resto del capitolo usa. La prima è che la potenza non dipende dall'angolo, perché $M^2 + S^2 = s^2(\cos^2\theta + \sin^2\theta) = s^2$ per ogni $\theta$: è la potenza costante del capitolo 7. La seconda è che il mid-side e la coppia sinistra-destra sono la stessa informazione scritta in due modi. La matrice di somma e differenza

$$ L = \frac{M + S}{\sqrt{2}}, \qquad R = \frac{M - S}{\sqrt{2}} $$

dà $L = s\cos(\theta - 45^\circ)$ e $R = s\cos(\theta + 45^\circ)$: sono le due figure di otto di Blumlein, a $+45$ e a $-45$ gradi. Applicata due volte la stessa matrice restituisce il segnale di partenza, e l'energia totale non cambia, $L^2 + R^2 = M^2 + S^2$ [@Gerzon1992, p. 699]. Il passaggio da mid-side a sinistra-destra è quindi senza perdita e reversibile, e la scelta fra le due forme è una questione di comodità.

Il mid non è obbligato a essere una figura di otto. Se è un microfono con profilo $(1 - b) + b\cos\theta$ (con $b = 0$ è omnidirezionale, con $b = 1$ è una figura di otto) e la matrice di somma e differenza resta la stessa, le due uscite sono profili con il lobo orientato a $\pm\arctan(1/b)$ gradi dal fronte: $90$ gradi per un mid omnidirezionale, circa $63$ per un mid a metà fra i due, $45$ per la figura di otto. Il mid con $b = 1$ è il caso di PGE, ed è l'unico in cui la potenza $M^2 + S^2$ è costante a ogni angolo.

La codifica non dice nulla sugli altoparlanti, e Gerzon ne fa un principio. Codificare è assegnare a ogni direzione i guadagni con cui il suono entra negli $n$ canali di trasmissione; decodificare è ricavare dai canali i segnali per un dato insieme di altoparlanti [@Gerzon1977, p. 400]. Le due operazioni sono indipendenti, e il numero dei canali non è il numero degli altoparlanti: tre canali, $W$, $M$ e $S$, possono alimentarne quattro, otto, sedici. La direzione che si vuole far sentire non dipende da dove stanno gli altoparlanti, e perciò è il decoder a dover cambiare con la loro disposizione, non la codifica [@Gerzon1977, p. 400].

## La decodifica: un microfono virtuale per altoparlante

Per una disposizione regolare la decodifica ha una regola semplice: a ogni altoparlante basta dare l'uscita di un microfono direzionale puntato nella sua direzione [@Gerzon1973, p. 2]. Se l'altoparlante $k$ sta all'azimut $\varphi_k$, il suo segnale è la combinazione dei canali che realizza quel microfono:

$$ g_k = a\,W + b\,\big(M\cos\varphi_k + S\sin\varphi_k\big) = s\,\big(a + b\cos(\theta - \varphi_k)\big) $$

I numeri sono tre. $\varphi_k$ è l'azimut dell'altoparlante e dice dove punta il microfono virtuale. $a$ e $b$ ne scelgono il profilo: $a = 0$, $b = 1$ è la figura di otto, $a = b = 1/2$ è il cardioide. $W$ è il canale che porta la parte omnidirezionale; con $a = 0$ non serve.

Il caso stereo è il caso particolare più semplice. Due altoparlanti a $\varphi = \pm 45$ gradi, con $a = 0$ e $b = 1$, danno $g = s\cos(\theta \mp 45^\circ)$, cioè le formule per $L$ e $R$ del capitolo 7. Il renderer di PGE, che calcola mid e side e poi li ruota in sinistra e destra, esegue già una decodifica a due altoparlanti: aggiungere altoparlanti vuol dire cambiare i $\varphi_k$ e il loro numero, e non cambiare il metodo.

La figura di otto da sola, però, regge male oltre i due altoparlanti. Con $a = 0$ l'altoparlante opposto alla sorgente riceve lo stesso segnale di quello più vicino, con la polarità invertita, e con tre o più altoparlanti in disposizione regolare la somma dei guadagni è nulla: il suono arriva ai lati e dietro in controfase, e al centro la pressione è nulla. Con quattro altoparlanti a $0$, $90$, $180$ e $270$ gradi e una sorgente a zero, i guadagni sono $1$, $0$, $-1$ e $0$.

### Il 1970: somma e differenza su quattro altoparlanti

Un esempio storico di mid-side su più di due altoparlanti è dello stesso Gerzon, nel 1970 [@Gerzon1970]. L'esperimento è semplice: da una registrazione stereo si alimentano quattro altoparlanti a rombo con il canale sinistro a sinistra, il destro a destra, la somma dei due, $L + R$, davanti e la differenza, $L - R$, dietro. Davanti arriva il mid e dietro il side. Un suono registrato solo a sinistra esce soprattutto dall'altoparlante di sinistra; uno uguale sui due canali ma in controfase esce da dietro.

Gerzon riferisce che il sistema aumenta molto il realismo delle registrazioni con coppia Blumlein e che è meno efficace con le tecniche di registrazione artificiali. Ne elenca anche i difetti, che sono quelli della decodifica a sola figura di otto. Non tutti e quattro gli altoparlanti possono essere in fase, e per questo l'altoparlante posteriore non ha una polarità corretta. La direzione originale non è riprodotta: un musicista che cammina una volta attorno ai microfoni è riprodotto come se girasse due volte attorno ai quattro altoparlanti, e la larghezza delle immagini raddoppia. Con registrazioni a microfoni cardioidi, che non registrano nulla in controfase, non esce nulla da dietro; con registrazioni a pan-pot l'effetto stereo è scadente. Il raddoppio ha una causa geometrica: il segnale sinistro è un microfono a figura di otto puntato a $45$ gradi, ma l'altoparlante che lo riproduce sta a $90$, il doppio. Il microfono virtuale di ciascun altoparlante è puntato a metà dell'angolo a cui l'altoparlante sta. Lo stesso vale per la disposizione con gli altoparlanti agli angoli, per la quale Gerzon dà i coefficienti $0{,}924$ e $0{,}383$ [@Gerzon1970]: sono il coseno e il seno di $22{,}5$ gradi, e ogni altoparlante è un microfono virtuale puntato a $\pm 22{,}5$ o a $\pm 67{,}5$ gradi, la metà dei $\pm 45$ e dei $\pm 135$ a cui gli altoparlanti stanno.

La correzione è la regola della sezione precedente: puntare il microfono virtuale dove sta l'altoparlante, con $\varphi_k$ uguale al suo azimut vero.

### Il canale omnidirezionale

Anche con i microfoni puntati bene, il profilo a figura di otto ha i lobi in controfase che si sono visti. Il rimedio è aggiungere il canale $W$. Nel 1977 Gerzon scrive la decodifica come un integrale sul cerchio delle direzioni, $P_\varphi = \int k(\varphi, \theta)\, S_\theta\, d\theta$, dove il nucleo $k$ dice quanto una sorgente a $\theta$ entra nell'altoparlante a $\varphi$ [@Gerzon1977, p. 406]. Gerzon descrive con nuclei di questa forma i sistemi di Cooper e Shiga: $k = 1 + e^{-j(\varphi - \theta)}$ per il sistema a due canali (BMX) e $k = 1 + 2\cos(\varphi - \theta)$ per quello a tre (TMX). Il secondo è ciò che si ottiene dalla formula di sopra con $W$, $M$ e $S$ pesati $1$, $2$ e $2$. Per $N$ altoparlanti regolari, $\varphi_k = \varphi_0 + 360^\circ k/N$,

$$ g_k = \frac{1}{N}\Big(W + 2\big(M\cos\varphi_k + S\sin\varphi_k\big)\Big) = \frac{s}{N}\big(1 + 2\cos(\theta - \varphi_k)\big). $$

Il fattore $1/N$ fa sì che $\sum_k g_k = s$: la somma dei segnali degli altoparlanti è il segnale, cioè al centro la pressione è quella giusta. La potenza totale, $\sum_k g_k^2 = 3s^2/N$ per ogni disposizione regolare con $N \geq 3$, non dipende da $\theta$: una sorgente che gira attorno al pubblico non cambia di livello. Il profilo $(1 + 2\cos)/3$ è un ipercardioide con il nullo a $120$ gradi. Ha ancora un lobo posteriore in controfase, ma di un terzo del massimo e non pari a esso come nella figura di otto: a $180$ gradi vale $-1/3$.

La figura mette a confronto i tre profili e mostra, per otto altoparlanti, i guadagni di una sorgente a $30$ gradi: i due altoparlanti più vicini ricevono la parte maggiore, quelli opposti ricevono poco e in controfase.

![A sinistra, i profili polari di un altoparlante: figura di otto, cardioide e nucleo $(1 + 2\cos)/3$ di Gerzon; il tratteggio indica la controfase. A destra, i guadagni degli otto altoparlanti di un anello regolare per una sorgente a $30$ gradi; il cerchio pieno è in fase, quello vuoto in controfase.](docs/images/spazializzazione_decoder.pdf){width=100%}

La tabella dà i profili normalizzati al massimo, in funzione dell'angolo fra la sorgente e l'altoparlante. L'ultima riga è il fattore di direttività, il rapporto fra il massimo del quadrato del profilo e la sua media sul cerchio [@Gerzon1973, p. 5]: vale $1$ per un microfono omnidirezionale e cresce con la stretta del lobo.

| Angolo | Figura di otto | Cardioide | $(1 + 2\cos)/3$ |
|---|---:|---:|---:|
| 0° | 1 | 1 | 1 |
| 45° | 0,707 | 0,854 | 0,805 |
| 90° | 0 | 0,5 | 0,333 |
| 135° | -0,707 | 0,146 | -0,138 |
| 180° | -1 | 0 | -0,333 |
| Direttività | 2 | 2,67 | 3 |

Con quattro altoparlanti a $0$, $90$, $180$ e $270$ gradi e una sorgente a zero, i guadagni del decoder a tre canali sono $0{,}75$, $0{,}25$, $-0{,}25$ e $0{,}25$; a $45$ gradi, in mezzo a due altoparlanti, sono $0{,}60$, $0{,}60$, $-0{,}10$ e $-0{,}10$. Con otto altoparlanti e una sorgente a zero sono $0{,}375$, $0{,}302$, $0{,}125$, $-0{,}052$, $-0{,}125$, $-0{,}052$, $0{,}125$ e $0{,}302$. In tutti i casi la somma è $1$. Il lobo posteriore in controfase resta un terzo del massimo qualunque sia il numero degli altoparlanti: aumentarli non lo riduce.

## La gerarchia: più canali, più direttività

Il teorema della direttività, che Gerzon enuncia nel 1973, dice che con $N$ canali non ridondanti nessuna combinazione ha fattore di direttività maggiore di $N$, e che $N$ si raggiunge [@Gerzon1973, p. 5]. Per la scena orizzontale ne viene che con due canali, $M$ e $S$, il profilo più stretto è la figura di otto, con direttività $2$, e che con tre canali, aggiungendo $W$, il più stretto è l'ipercardioide, con $3$: sono le cifre della tabella. Per stringere il lobo servono più canali.

I canali in più hanno una struttura. I sistemi che trattano tutte le direzioni orizzontali in modo uguale formano una gerarchia, che Gerzon attribuisce a Cooper e Shiga: ciascun sistema si ottiene dal precedente aggiungendo canali, e la risoluzione direzionale è proporzionale al loro numero [@Gerzon1973, p. 3]. In forma reale, i canali sono le armoniche circolari: $1$ (l'ordine zero, $W$), poi $\cos\theta$ e $\sin\theta$ (l'ordine uno, $M$ e $S$), poi $\cos 2\theta$ e $\sin 2\theta$ (l'ordine due), e così via; un sistema di ordine $n$ ha $2n + 1$ canali [@Gerzon1973, p. 5]. Il mid-side con $W$ è il sistema di ordine uno. Il profilo più direzionale che $2n + 1$ canali permettono si ottiene sommando tutti i canali, ciascuno con il guadagno che ha nella direzione dell'altoparlante [@Gerzon1973, p. 8], e coincide con il nucleo

$$ g_k = \frac{s}{N}\Big(1 + 2\sum_{m=1}^{n}\cos m(\theta - \varphi_k)\Big), $$

che per $n = 1$ è il nucleo di prima e che ha direttività $2n + 1$ (la normalizzazione sul cerchio, con energia unitaria per canale, è quella usata in questo capitolo; Gerzon dà le armoniche sulla sfera). Gerzon mostra anche che questo profilo è quello a minima diafonia fra altoparlanti e che dà la migliore approssimazione ai minimi quadrati della riproduzione direzionale perfetta con i canali disponibili [@Gerzon1973, p. 8].

Una gerarchia è utile anche perché i livelli sono compatibili. Gerzon la studia per la scena frontale a più altoparlanti, per la televisione ad alta definizione: ogni canale aggiunto porta un dettaglio più fine sulla direzione, che chi riceve può usare o scartare, e quello che si trasmette per un certo numero di altoparlanti si riproduce in modo ottimale con un numero maggiore [@Gerzon1992, p. 692]. Per scrivere le matrici di quella gerarchia usa il mid-side di ogni coppia di altoparlanti simmetrici, $M_p = (L_p + R_p)/\sqrt{2}$ e $S_p = (L_p - R_p)/\sqrt{2}$, e osserva che in questa forma le equazioni di codifica e di decodifica sono le più semplici [@Gerzon1992, pp. 699-700].

## Quanti altoparlanti, e dove

Gerzon richiede che gli altoparlanti non siano meno dei canali [@Gerzon1973, p. 8]: tre canali richiedono almeno tre altoparlanti. In pratica, osserva che il minimo per una scena orizzontale accettabile, anche se non ideale, è quattro, e che, a parità di canali, più altoparlanti danno risultati migliori: tre canali riprodotti con cinque altoparlanti sono meglio che con quattro [@Gerzon1977, p. 401]. Il decoder di questo capitolo è pensato per una disposizione regolare. Gerzon riporta disegni per i poligoni regolari, per i poliedri regolari e per i rettangoli con rapporto qualunque fra fronte e lati, e ne prevede per disposizioni irregolari come un trapezio; un decoder ottimale è in generale una matrice che si adatta al layout e dipende dalla frequenza [@Gerzon1977, p. 405]. La formula di questo capitolo vale per l'anello regolare e va presa come punto di partenza, non come soluzione per qualunque sala.

Resta il pubblico, che non sta nel centro. Gerzon chiede a un decoder di dare un'illusione direzionale ragionevole anche a chi è fuori centro [@Gerzon1977, p. 405], e osserva che nel quadrato di quattro altoparlanti chi non è al centro sente le direzioni attratte verso l'altoparlante più vicino [@Gerzon1977, p. 402]. Il suo giudizio sul pan a coppie adiacenti, in cui si alimentano soltanto i due altoparlanti vicini alla direzione voluta, è severo: nelle prove di localizzazione che cita ha dato risultati quasi sempre scadenti, e non andrebbe preso come riferimento [@Gerzon1977, pp. 401-402]. È un giudizio del 1977, riferito ai sistemi quadrifonici del tempo, e qui va letto come tale; serve a spiegare perché si sceglie una decodifica a direzione continua.

## Che cosa cambia in PGE

Il motore ha già tutto ciò che la codifica richiede. Il renderer calcola, per ogni grano, il grano finestrato $s$ (che è $W$) e le sue due proiezioni, `mid = s cos(θ)` e `side = s sin(θ)`, e solo dopo le ruota in sinistra e destra. Tutta la differenza fra due altoparlanti e $n$ sta nell'ultimo passo, che nei tre renderer è la stessa matrice (capitolo 7). Le strade possibili sono due. La prima è far scrivere ai renderer direttamente gli $n$ canali, decodificando con il layout dichiarato nello YAML. La seconda è scrivere il formato di trasmissione, i tre canali $W$, $M$ e $S$, e lasciare la decodifica al momento dell'esecuzione. Per *mare-nostrum* è prevista la seconda, ed è quella che segue il principio di Gerzon: il file non dipende dalla sala, il decoder sì, e se la disposizione degli altoparlanti cambia da un concerto all'altro non si ri-renderizza il brano. Il costo è un file a tre canali al posto di due. La scelta non cambia il grano, la lista dei grani o il seme, e quindi lascia intatta la riproducibilità del capitolo 3. Oggi i renderer non scrivono ancora quel formato: è lavoro da fare, e il capitolo lo indica come tale.

## Le condizioni di esecuzione di *mare-nostrum*

Il brano è pensato per otto altoparlanti disposti in un anello circolare regolare attorno al pubblico, con la decodifica fatta al concerto a partire da un file a tre canali. Un altoparlante sta davanti, a $0$ gradi, e gli altri sette sono equidistanti sul cerchio, a $45$, $90$, $135$, $180$, $225$, $270$ e $315$ gradi: $\varphi_0 = 0^\circ$ nella formula del decoder. Otto altoparlanti a $45$ gradi l'uno dall'altro sono più dei tre canali che il decoder richiede, e quindi stanno nelle condizioni che Gerzon indica (altoparlanti non meno dei canali, e a parità di canali meglio di più di quattro). I loro guadagni sono quelli della tabella: per una sorgente a zero gradi, $0{,}375$, $0{,}302$, $0{,}125$, $-0{,}052$, $-0{,}125$, $-0{,}052$, $0{,}125$ e $0{,}302$, con somma $1$, e per una sorgente a $22{,}5$ gradi, in mezzo a due altoparlanti, il massimo spetta a quei due. Con otto altoparlanti l'anello ha anche spazio per un sistema di ordine due (cinque canali, $W$, $M$, $S$, $\cos 2\theta$ e $\sin 2\theta$), che il decoder di questo capitolo non usa ma che la gerarchia prevede. Nessun parametro del decoder dipende dal brano: quello che il decoder riceve è la direzione di ogni grano, e questa è già nell'angolo che PGE gli assegna.

L'autore ha esplorato questi algoritmi in una libreria Faust a parte (MidSide), con un panner mid-side a profilo polare regolabile e decoder a quattro altoparlanti, a rombo e a coppie anteriori e posteriori. La libreria non è integrata in PGE e non coincide punto per punto con la formula di questo capitolo (ricava la parte omnidirezionale dal mid), e il capitolo non la descrive.

Per *mare-nostrum* ciò che conta è che i pan del brano coprono già 360 gradi (capitolo 10). A due altoparlanti il dietro si piega sul davanti: un grano a $180^\circ - \theta$ suona come lo speculare davanti, con $L$ e $R$ scambiati e la polarità invertita, e a $\pm 90$ gradi le due uscite sono in controfase. Con $n$ altoparlanti attorno al pubblico gli stessi valori diventano posizioni vere.

<!-- TODO(giulio): resta da scrivere il software con cui si decodifica al concerto. Verificare anche che il pan di ogni stream abbia senso come azimut fisico (0 davanti, positivo a sinistra): oggi è scritto per due altoparlanti e non è stato mai ascoltato su un anello. -->


# Conclusioni e sviluppi futuri

## Che cosa ho fatto

Ho descritto Python Granular Engine nella versione 9.1.0 [@DeMattia2026Pge]. Il problema è quello classico della sintesi granulare: una popolazione di migliaia di grani al secondo non si specifica grano per grano, e chi compone ha bisogno di descriverne il comportamento collettivo senza perdere la possibilità di risalire dall'esito ai parametri che lo hanno prodotto (capitolo 2). La risposta di PGE ha tre parti. La prima è un linguaggio dichiarativo in YAML, in cui ogni parametro è un valore centrale che varia nel tempo e una banda di variazione, la maschera di tendenza di Truax in forma testuale (capitolo 4). La seconda è la lista dei grani, una rappresentazione intermedia che fissa che cosa suonare senza dire come lo scrive un programma di sintesi (capitoli 3 e 5), e che il motore moltiplica in voci parallele (capitolo 6). La terza è l'insieme dei suoi consumatori: tre renderer che la trasformano in audio (capitolo 7), la MAP, che la trasforma in un'immagine, e tre esportazioni (capitolo 8). Lo strumento è sviluppato con test, documentazione verificata da controlli automatici e versionamento (capitolo 9).

Il disegno regge su due scelte che ritrovo in ogni capitolo. La prima è la separazione fra generazione e rendering, e quindi fra il compositore e il programma di sintesi: aggiungere un renderer, una finestra o una strategia non richiede di toccare il nucleo, e l'esistenza di tre renderer indipendenti rende il rendering falsificabile. La seconda è la riproducibilità: la specifica con il seme dichiarato è il documento che si conserva, e l'audio si rigenera da essa. Il tempo differito, che è la ragione per cui ho scritto lo strumento, ha consentito densità e numeri di voci che il tempo reale non offre.

## Che cosa ne è uscito

Dal punto di vista musicale posso dichiarare solo ciò che è verificabile. Il primo esito è una raccolta di esempi (cartella `esempi/`), ciascuno dei quali isola un meccanismo e ne mostra l'effetto con la MAP: sono il materiale su cui è costruita la tesina. Il secondo è *mare-nostrum*, il brano con i lamenti e i pianti di bambini trasformati in suono di mare, di cui il capitolo 10 descrive la struttura: sedici stream, 581 secondi e circa 9,5 milioni di grani. Accanto al brano c'è un laboratorio di studi sui parametri, che finora ha una sessione di ascolto documentata. Nessuno ha usato lo strumento oltre a me. Non posso dunque dire se le scelte di PGE, in particolare la lettura psicoacustica dei parametri e la MAP come strumento di verifica, reggano fuori dal mio lavoro.

## Limiti

Restano sei limiti, che non ho colmato. Il sistema governa il materiale per posizione di lettura e non per contenuto: non sa nulla del timbro di ciò che granula. Gli assi di controllo sono indipendenti per costruzione, dall'ampiezza e dalla probabilità della deviazione alle quattro strategie delle voci, e nessuno dichiara come covariano fra loro. La MAP affida l'altezza al colore, e anche il preset in bianco e nero (capitolo 8) la codifica in un solo canale. I renderer producono oggi file stereofonici, anche se il grano non impone il numero di canali: il brano è pensato per otto altoparlanti, e il passaggio, descritto nel capitolo 11, richiede un formato a tre canali che non è ancora scritto.

Gli ultimi due limiti sono emersi lavorando a *mare-nostrum*. Il primo è che uno stream attinge a un solo file audio, mentre il brano avrebbe bisogno di scegliere fra più sorgenti. Il secondo è che la granulazione ha un solo livello. Il coro di persone morte, in cui i grani durano secondi (capitolo 10), usa frammenti di registrazione che non sono granulati al loro interno: a quella durata si riconoscono troppo come registrazioni, la magia della granulazione fine si rompe e il suono connota in un altro modo. Servirebbe poter granulare dentro il singolo grano lungo.

## Sviluppi futuri

Ai primi due limiti corrispondono due direzioni di sviluppo: una libreria di descrittori del materiale, come il centroide spettrale e l'energia, per guidare i parametri sul timbro invece che sulla sola posizione, e la possibilità di dichiarare nella specifica come i parametri covariano, invece di lasciarli indipendenti. Truax prevedeva sistemi di controllo complessi, a più livelli di decisione [@Truax1988, p. 25]: un processo dichiarativo che generi intere popolazioni di stream, invece di scriverne uno alla volta, ne è la continuazione, e il laboratorio di *mare-nostrum*, con gli studi che variano due parametri su una griglia, è un primo passo in quella direzione. Resta poi da fare ciò che la tesina non fa: una valutazione condotta con altri compositori.

Ai due limiti nati dal brano corrisponde la direzione in cui voglio portare il lavoro dopo questa tesina, per la tesi: uno stream che peschi da più file e una granulazione annidata. PGE diventerebbe un orchestratore di frammenti lunghi, scelti da più sorgenti, che a loro volta si granulano al loro interno, e non soltanto un granulatore di un frammento alla volta. Dietro questa direzione c'è una riflessione che non è solo tecnica. È uno studio sul linguaggio musicale attraverso la relazione fra più elementi: elementi messi in relazione e trattati in modi diversi connotano cose diverse. Vorrei che la connotazione non fosse soltanto culturale ma archetipica, legata alla realtà e al linguaggio umano: il mistero dell'ascolto, come nell'arte c'è il mistero della visione. Per ora è un'ipotesi di lavoro, e non un risultato di questa tesina: per sostenerla serviranno ascolti e riferimenti che qui non ci sono.

Il progetto che mi sta più a cuore è PGE-ui, un'interfaccia grafica per lo YAML di PGE che sviluppo in un repository a parte. È un editor nel browser, collegato al motore da un piccolo ponte locale, in cui ogni stream è una clip su una traccia di una timeline: gli inviluppi si disegnano, le voci e gli altri parametri si regolano in un pannello, e il rendering lancia il motore e permette di ascoltare gli stem sulla timeline. Per questo la chiamo, con una certa libertà, la DAW di PGE, ma non registra né modifica l'audio: quello che modifica è il documento YAML, da cui l'audio deriva. La specifica resta dunque l'unico documento, e l'interfaccia grafica e il testo si possono usare sullo stesso file. È il modo in cui voglio rendere più diretta la scrittura, mantenendo ciò che per me conta di più nel metodo: un documento testuale che si versiona e un rendering che si rigenera.


# BIBLIOGRAFIA

::: {#refs-bib}
:::

# SITOGRAFIA

::: {#refs-sit}
:::

