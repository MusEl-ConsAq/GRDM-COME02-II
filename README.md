---
abstract: |
  Python Granular Engine (PGE) è uno strumento per la sintesi granulare del suono campionato, scritto in Python e usato dall'autore per comporre. La tesina ne descrive il disegno, il linguaggio e il metodo di sviluppo, e lo mostra in uso in un brano ancora incompiuto, *mare-nostrum*.
  
  Il problema è quello classico della granulazione: migliaia di grani al secondo non si scrivono uno per uno, e chi compone ha bisogno di descrivere il comportamento collettivo della popolazione senza perdere la possibilità di risalire dall'esito ai parametri. PGE lo affronta in tempo differito, per disporre di molto più calcolo di quello che la granulazione in tempo reale consente, e prende a modello il sistema che Barry Truax ha costruito sul DMX-1000, di cui conserva il lessico e le maschere di tendenza. Lo stream si dichiara in un file YAML che il motore traduce in una lista di grani, una rappresentazione intermedia indipendente da chi la consuma. Tre renderer (NumPy, Csound, SuperCollider) la trasformano in audio; la MAP (*Multiparametric Audio Plot*), che disegna ogni grano nel piano tempo-posizione di lettura, e tre esportazioni (Reaper, Sonic Visualiser, JSON) la leggono a loro volta. Con il seme dichiarato la specifica è il documento che si versiona e l'audio si rigenera da essa.
  
  La tesina ricostruisce l'origine teorica della tecnica da Gabor a Xenakis, a Roads e a Truax, e descrive il motore capitolo per capitolo: l'architettura, il linguaggio, il grano e lo stream, le voci, il rendering, la MAP. Racconta poi il metodo di sviluppo (test, documentazione verificata da controlli automatici, versionamento, un language server per l'editor) e presenta lo stato di *mare-nostrum*. Le conclusioni indicano i limiti, tra cui il governo del materiale per posizione e non per contenuto, e gli sviluppi, fra cui PGE-ui, l'interfaccia grafica con timeline che l'autore sta sviluppando.
---

# Introduzione

Questa tesina descrive Python Granular Engine (d'ora in avanti PGE), uno strumento per la sintesi granulare del suono campionato che ho scritto in Python e che uso per comporre. Non è una teoria della granulazione e non è un manuale. È la descrizione di un ambiente, di come è costruito e di perché è costruito così, e del lavoro compositivo in cui lo sto usando.

## Motivazioni

La sintesi granulare costruisce il suono con migliaia di eventi brevi al secondo, e nessuno li scrive uno per uno. Fin dai primi esperimenti al calcolatore la specifica grano per grano si è rivelata intrattabile: nel dicembre del 1974 Roads batteva ogni grano su una scheda perforata, e per trenta secondi di suono servivano circa ottocento schede [@Roads2001, p. 110]. Comporre con i grani richiede perciò un livello di controllo che descriva il comportamento collettivo della popolazione, spesso per via statistica. La storia della tecnica è, in buona parte, la storia degli strumenti inventati per descrivere popolazioni di grani: gli *eventi* di Roads, le *maschere di tendenza* di Truax, le specifiche testuali come CMask [@Roads1978; @Truax1988; @Bartetzki1997]. PGE appartiene a questa linea. Il compositore scrive un testo in YAML che dichiara come si comporta lo *stream*, il motore lo traduce in una lista di grani e un renderer la trasforma in suono.

Le ragioni per cui l'ho fatto così sono tre.

La prima è il tempo differito. Volevo comporre e indagare gli aspetti della granulazione potendo contare su molto più calcolo di quello che la granulazione in tempo reale offre. In tempo reale la densità dei grani, il numero delle voci e la complessità del suono sono limitati dal budget di calcolo di ogni istante; in tempo differito il solo limite è il tempo che si è disposti ad attendere. È una posizione poco consueta, e Risset l'ha argomentata con chiarezza. Per lui il livello di complessità sonora che un sistema digitale raggiunge in tempo reale è sempre limitato, e il compositore non ha la libertà di sceglierlo [@Risset1999, p. 33]; la sintesi per software offre una scelta più libera dei pochi menù di controllo dei sistemi in tempo reale [@Risset1999, p. 33]; il tempo reale non è la soluzione al problema difficile di padroneggiare la sintesi del suono, perché la combinazione desiderata non si raggiunge per tentativi, come non si risolve un cubo di Rubik girandone a caso le facce [@Risset1999, p. 34]. Anzi, il concetto di tempo reale riguarda in primo luogo l'esecuzione e può avere poca rilevanza per la composizione [@Risset1999, p. 31]. La scala che il tempo differito consente si misura. Nel 1986 Truax raggiungeva in *Riverrun* una densità massima di 2 375 grani al secondo [@Truax1988, p. 25]. Lo schizzo di *mare-nostrum*, descritto nel capitolo 10, ha circa 3,3 milioni di grani, e due dei suoi stream partono oltre i 4 000 grani al secondo.

La seconda è la riproducibilità e il versionamento. Una composizione scritta come testo si versiona con *git*, che diventa la documentazione del processo compositivo: ogni modifica è confrontabile con la precedente, e si può tornare a un qualsiasi stato. Il seme dei processi casuali è una chiave della specifica, e dichiararlo rende la realizzazione identica a ogni esecuzione, a parità di renderer. La specifica, non l'audio, è dunque il documento che si conserva: il rendering si rigenera da essa. Risset, fra le ragioni contro i sistemi in tempo reale, indicava la loro fragilità nel tempo, perché la tecnologia cambia in fretta e i brani legati a un dispositivo non si possono più ascoltare, e chiedeva che la struttura compositiva sia esplicitata in termini di operazioni di base, che i dispositivi futuri possano riprodurre [@Risset1999, pp. 34-35]. Un testo dichiarativo e un motore deterministico rispondono, in parte, a quella richiesta.

La terza è la finalità pedagogica. Il dominio di PGE è il *granular sampling* [@Lippe1993cim], e i nomi e i parametri sono quelli della letteratura classica di Roads e di Truax: la densità, la durata del grano, il fattore di riempimento, la maschera di tendenza, la posizione di lettura nel materiale. Usare lo strumento è anche un modo di studiare la tecnica. Per questo la tabella del capitolo 2 mette in corrispondenza i sette parametri della nuvola di Roads con le chiavi dello YAML.

C'è poi un percorso personale, che il paper presentato al XXV Colloquio di Informatica Musicale [@DeMattia2026Cim] racconta in nota. L'impostazione dichiarativa è l'esito di circa due anni di ricerca, e nasce da un confronto con Francesco Vitucci nel laboratorio *Le Domeniche alla Periferia dell'Impero*. Ne è venuto GAMMA, brano acusmatico la cui prima esecuzione assoluta è stata il 10 luglio 2025 al Museo degli Strumenti Musicali di Roma, nel concerto *INCONTRI* del Festival ArteScienza 2025, realizzato con un altro ambiente di composizione assistita, per sintesi additiva. PGE porta quell'impostazione sulla granulazione.

Il paper aggiunge una quarta ragione, da cui è nata la MAP (*Multiparametric Audio Plot*). Pochi secondi di granulazione producono decine di migliaia di eventi, e a quella scala ricondurre l'esito agli attributi che lo hanno prodotto richiede un controllo che la specifica da sola non offre. Una lista di eventi è, come documento, meno accessibile del file audio, e il file audio non permette di risalire ai parametri. Senza un passaggio di analisi, verificare l'effetto di un parametro significa procedere per tentativi. La MAP rappresenta la popolazione di grani in un'immagine, prima ancora di riascoltare.

## Il modello di riferimento: il DMX-1000 di Barry Truax

PGE prende a modello il sistema di sintesi granulare che Barry Truax ha realizzato a metà degli anni Ottanta, descritto nell'articolo del 1988 [@Truax1988]. Il modello è il punto di partenza, e il confronto mostra che cosa PGE conserva e che cosa cambia.

Il sistema di Truax è costruito sul DMX-1000, uno dei primi processori di segnale, controllato da un microcalcolatore PDP Micro 11 [@Truax1988, p. 14]. Offre tre modelli di strumento: sintesi additiva, modulazione di frequenza e un modello che granula un suono campionato, con venti, otto e venti voci rispettivamente, metà sul canale sinistro e metà sul destro [@Truax1988, p. 15]. Ogni voce è un generatore d'inviluppo, e il numero delle voci fissa la densità massima in verticale. Un programma sul calcolatore pilota lo strumento: avvia ogni grano impostando la rampa d'attacco, lo termina impostando quella di decadimento, con interruzioni di clock ogni millisecondo e un ritardo variabile fino al grano successivo. Il grano più breve controllabile in tempo reale è di 8 millisecondi, e le densità arrivano a 2 500 grani al secondo con le venti voci [@Truax1988, pp. 15-16]. Nel modello a campioni il suono sorgente è un segmento fisso di 4 032 campioni, circa 150-170 millisecondi, perché la memoria del processore è di quattro kiloparole [@Truax1988, p. 15].

I controlli sono quattro: frequenza centrale e banda di frequenza (o, nel modello a campioni, lo scostamento dall'inizio del campione e la sua banda), durata media e banda della durata, ritardo fra i grani [@Truax1988, p. 17]. A ciascuno corrisponde un correlato psicoacustico, e Truax li propone come base più suggestiva per l'organizzazione compositiva dei valori numerici: l'altezza media, la larghezza di banda (il continuo fra altezza e rumore), la densità, la modulazione [@Truax1988, pp. 18-19]. Sopra i controlli sta una gerarchia: gruppi di parametri salvati come *preset*, *rampe* che cambiano un parametro a una velocità data, e le maschere di tendenza, che il compositore specifica come aree entro cui i valori sono scelti [@Truax1988, pp. 19, 23]. Il programma mostra su un terminale a 24 righe la sovrapposizione grafica delle maschere e degli inviluppi, per verificarne la sincronizzazione [@Truax1988, p. 24]. Truax inquadra il lavoro come composizione in tempo reale, capace di unire la complessità della composizione in studio e la spontaneità dell'esecuzione dal vivo [@Truax1988, p. 14].

PGE conserva il lessico e la struttura di controllo. Ogni parametro è un valore centrale, che può variare nel tempo, più una banda entro cui il valore di ogni grano è estratto: è la maschera di tendenza, in forma testuale (capitolo 4). Il modello a campioni di Truax, con lo scostamento dall'inizio del campione e la sua banda, è il blocco `pointer` (capitolo 5). Le voci parallele del DMX-1000 sono la molteplicità delle voci di uno stream (capitolo 6). Il rapporto fra un programma che calcola gli eventi e un motore che li suona è quello fra il generatore di grani e i renderer (capitolo 3). La lettura psicoacustica dei parametri guida ancora il lavoro, come si vede nello studio dei parametri di *mare-nostrum* (capitolo 10).

Cambia il tempo, e con il tempo tutto ciò che nel DMX-1000 era un limite dell'hardware. La tabella confronta le due configurazioni.

| | DMX-1000 [@Truax1988] | PGE |
|---|---|---|
| tempo | reale | differito |
| grano più breve | 8 ms | un campione |
| densità massima | 2 500 grani/s con venti voci | nessun tetto dichiarato (nello schizzo, oltre 4 000 grani/s per stream) |
| voci | 20, 8 o 20, per modello | da 1 a 256 per stream, anche frazionarie, e un numero qualsiasi di stream |
| materiale campionato | 4 032 campioni, circa 150-170 ms | file di qualsiasi durata |
| controllo | comandi da tastiera, preset, rampe, maschere | un documento di testo |
| visualizzazione | sovrapposizione delle maschere su un terminale | la MAP dei grani generati |

I due ultimi righi richiedono una precisazione. La figura 4 di Truax disegna le curve di controllo, le maschere e gli inviluppi, e non i grani: corrisponde al pannello inferiore della MAP, quello degli inviluppi. Il pannello dei grani, con la posizione di lettura in ordinata, è una rappresentazione dell'esito, non del controllo (capitolo 8). L'altra differenza è il controllo. Truax osserva che i file di partitura prodotti da editor e programmi algoritmici sono di solito troppo grandi da maneggiare [@Truax1988, p. 14], e risponde generando i grani in tempo reale. PGE risponde in un altro modo: la lista dei grani, che può avere milioni di elementi, esiste ma non si scrive e non si legge. Ciò che il compositore scrive e versiona è la specifica, di poche righe, e la MAP dà accesso alla lista.

## Obiettivi e struttura della tesina

Mi propongo quattro cose. La prima è documentare PGE per intero: il suo disegno, il linguaggio, il grano e lo stream, le voci, il rendering. La seconda è collocarlo nella letteratura della sintesi granulare, da cui prende il lessico. La terza è mostrarlo in uso, nel brano che sto scrivendo. La quarta è registrare il metodo con cui è sviluppato, perché in un progetto di questa durata il metodo è parte del risultato. Non mi propongo di valutare lo strumento con ascoltatori o con altri compositori, né di confrontarlo con altri sistemi, né di sostituire la documentazione del progetto, che resta nel repository (`docs/`) e a cui la tesina rimanda.

La tesina riprende l'impostazione del paper presentato al CIM [@DeMattia2026Cim], di cui espande la materia, e ne conserva il metodo espositivo e il vocabolario. Gli esempi sono quelli del paper, con alcuni aggiunti, e sono rieseguibili: ogni listato YAML è nella cartella `esempi/` del repository della tesina e dichiara il proprio seme, per cui la realizzazione è quella che si riottiene rieseguendolo. La MAP è sempre quella generata dal motore, mai ridisegnata. La versione descritta è la 9.1.0 [@DeMattia2026Pge].

L'esposizione procede dal generale al particolare. Il capitolo 2 ricostruisce l'origine della sintesi granulare, definisce il grano, i suoi parametri e i modi di organizzarlo nel tempo, e arriva alla granulazione del suono campionato. Il capitolo 3 mostra come PGE è costruito: la lista dei grani come rappresentazione intermedia fra generazione e rendering, la generazione lazy, la regola di dipendenza fra i moduli, l'uso come libreria e i punti in cui il disegno resta aperto. Il capitolo 4 descrive la grammatica del linguaggio, partendo da uno stream di due righe: i valori predefiniti, le forme che un valore può assumere (espressione, envelope, banda di variazione), il seme e l'importazione di stream da altri file. Il capitolo 5 è dedicato al grano e allo stream, con il puntatore, la griglia di emissione, le proprietà del grano (durata, finestra, altezza, verso, volume e pan) e la variazione stocastica; il capitolo 6 alla molteplicità delle voci. Il capitolo 7 descrive i tre renderer, Csound, NumPy e SuperCollider, la cache e il costo del rendering. Il capitolo 8 tratta la MAP e le esportazioni verso Reaper, Sonic Visualiser e JSON. Il capitolo 9 racconta il metodo di sviluppo, dai test alla documentazione, e il language server PGE-ls. Il capitolo 10 presenta *mare-nostrum*, il brano per cui lo strumento è usato, che al momento è incompiuto, e lo dice. Le conclusioni raccolgono i limiti e gli sviluppi.

Una nota sul lessico. Chiamo MAP l'immagine sinottica dei grani generati, come nel paper, e non la chiamo «partitura», parola che uso soltanto per il file di eventi che Csound legge. Chiamo *stream* il flusso di grani descritto da un blocco dello YAML, e *voce* ciascuna delle copie parallele con cui uno stream si moltiplica.


# La sintesi granulare

La sintesi granulare costruisce un suono come somma di molti eventi molto brevi, i *grani*. Questo capitolo ne ricostruisce l'origine teorica, definisce il grano e i suoi parametri, distingue i modi di organizzare i grani nel tempo e arriva al caso che interessa PGE, la granulazione di un suono già registrato. Il riferimento principale è *Microsound* di Roads [@Roads2001], che raccoglie e ordina la letteratura; le fonti primarie sono state riprese ogni volta che era possibile. La trattazione è la base dei capitoli seguenti, che ne usano il vocabolario senza ridefinirlo.

## Origini teoriche: Gabor, Xenakis, Roads

### Gabor e il quanto acustico

L'idea di scomporre il suono in unità elementari nasce come teoria dell'udito. Nel 1947 il fisico Dennis Gabor osserva che l'analisi di Fourier, su cui riposa la teoria classica di Ohm e Helmholtz, è «una descrizione senza tempo», in termini di onde di durata infinita, mentre l'esperienza più elementare è che il suono ha insieme una forma temporale e una forma frequenziale. Serve una descrizione matematica che tenga conto fin dall'inizio di questa dualità [@Gabor1947, p. 591]. La sua soluzione è un piano con il tempo e la frequenza come coordinate ortogonali, il *diagramma dell'informazione*, in cui a ogni segnale si associa una cella rettangolare. L'area della cella ha un minimo:

$$ \Delta t \,\Delta f \ge 1 $$

È la formulazione esatta della relazione di indeterminazione fra tempo e frequenza [@Gabor1947, p. 591]. La costante dipende da come si definiscono le due larghezze, e Gabor stesso lo avverte [@Gabor1947, pp. 591, 593], ma il contenuto è indipendente dalla convenzione: per determinare con precisione le frequenze occorre una finestra lunga, per determinare con precisione l'istante occorre rinunciare alla frequenza. I segnali per cui la disuguaglianza diventa uguaglianza, e che occupano quindi una cella di area minima, sono i *segnali elementari*: oscillazioni armoniche modulate da un impulso gaussiano,

$$ s(t) = e^{-\alpha^2 (t - t_0)^2} \, e^{\,i 2\pi f_0 t} $$

con $\alpha$ costante reale [@Gabor1947, pp. 591-592]. Un segnale qualsiasi si può espandere su un reticolo di tali segnali, ciascuno con un'ampiezza complessa propria, e Gabor rappresenta l'espansione come una matrice di celle [@Gabor1947, p. 592]. La costante $\alpha$ decide la forma della cella e non la sua area.

![Il segnale elementare di Gabor (in alto, con l'inviluppo gaussiano tratteggiato) e la sua cella nel piano tempo-frequenza (in basso), per tre valori di $\alpha$. Con $\Delta t = \sqrt{\pi}/\alpha$ e $\Delta f = \alpha/\sqrt{\pi}$ [@Roads2001, p. 59] l'area è sempre unitaria: aumentare la risoluzione nel tempo diminuisce quella in frequenza.](docs/images/gabor_quanto.pdf){width=100%}

Il secondo passo è quello che interessa la musica. Gabor osserva che le soglie di discriminazione dell'orecchio, misurate in esperimenti precedenti, si lasciano riassumere dicendo che l'orecchio ha una *soglia d'area* dell'ordine dell'unità: nelle misure considerate il prodotto vale da 1,05 a 1,5 [@Gabor1947, pp. 592-593]. L'esperienza del suono breve va nella stessa direzione. Una sinusoide eseguita per pochi periodi è udita come un rumore, e dopo circa dieci millisecondi è udita come una breve nota con altezza determinabile [@Gabor1947, p. 592]. Il comportamento non si spiega con i soli risuonatori meccanici dell'orecchio interno, il cui smorzamento è di circa dieci millisecondi. Gabor postula un secondo meccanismo, non meccanico, che affina l'altezza percepita finché il suono dura, fino a circa 250 millisecondi, e nota che l'impressione di un suono «musicale» comincia proprio dove subentra il secondo meccanismo [@Gabor1947, p. 593].

Gabor ha una teoria analitica e un'invenzione. La teoria serve ad analizzare i segnali, e Roads sottolinea che il suo orientamento è questo [@Roads2001, p. 57]. L'invenzione, nella metà degli anni Quaranta, è un granulatore: il *Kinematical Frequency Convertor*, costruito adattando un sistema di registrazione ottica di un proiettore a 16 mm, che cambiava l'altezza di un suono senza cambiarne la durata e viceversa [@Roads2001, p. 61]. Il principio è la granulazione del suono registrato. Una testina rotante campiona a intervalli regolari la registrazione, ogni segmento prelevato è un grano, e i grani si riassemblano in un flusso continuo su un altro supporto. Per allungare il suono la testina gira più veloce e preleva più copie dello stesso passaggio. Il contenuto frequenziale locale, e quindi l'altezza, si conserva. Con lo stesso principio Schaeffer e Poullin costruirono il Phonogène all'inizio degli anni Cinquanta, e la ditta Springer lo Zeitregler, o Tempophon, a testine multiple su nastro magnetico [@Roads2001, pp. 61-62]. La granulazione di un suono registrato è dunque più antica del calcolatore.

### Dal quanto alla composizione

Dalla teoria dell'udito alla composizione il passaggio è breve. Nel 1950 Meyer-Eppler, fra i fondatori dello studio di Colonia, descrive a Darmstadt la matrice di Gabor come mezzo per analizzare i suoni in quanti acustici, e nel 1955 la presenta come una sorta di partitura che si potrebbe comporre con una *Mosaiktechnik*; stima inoltre in circa 15 millisecondi il limite inferiore di percezione delle differenze fra i parametri [@Roads2001, p. 62]. Moles segmenta lo spazio dei suoni udibili in quanti di frequenza, intensità e tempo, per misurare il contenuto d'informazione di un messaggio sonoro [@Roads2001, p. 63]. Wiener, ugualmente scettico verso Fourier, adotta una visione quantistica del suono [@Roads2001, pp. 63-64].

Chi ne fa una teoria compositiva è Xenakis: Roads lo indica come il primo a formulare una teoria compositiva dei grani di suono [@Roads1978, p. 61; @Roads1988, p. 11]. In *Formalized Music* la teoria si apre con una «ipotesi temporanea di base», un lemma:

> «All sound is an integration of grains, of elementary sonic particles, of sonic quanta. Each of these elementary grains has a threefold nature: duration, frequency, and intensity. All sound, even all continuous sonic variation, is conceived as an assemblage of a large number of elementary grains adequately disposed in time.» [@Xenakis1992, p. 43]

Il suono complesso è paragonato a «un fuoco d'artificio multicolore» in cui ogni punto di luce appare e sparisce all'istante, e in cui una moltitudine di punti organizzati ad arte produce forme e spirali, o linee di luce [@Xenakis1992, pp. 43-44]. Nel passo che precede il lemma Xenakis elenca, fra le opere con cui ha mostrato il valore della stocastica anche nella musica elettroacustica, *Diamorphoses* (1957-58), *Concret PH* (nel Padiglione Philips all'Esposizione di Bruxelles, 1958) e *Orient-Occident* (1960) [@Xenakis1992, p. 43].

Le due opere in cui Xenakis lavora davvero con i grani hanno metodi opposti [@Roads2001, pp. 64-67]. In *Concret PH* (1958) mescola registrazioni di braci di legno ardente, tagliate in frammenti di un secondo, con tecniche di taglio e giunzione del nastro, cambio di velocità e missaggio, in modo intuitivo e non matematico. In *Analogique B* (1959, che secondo Roads dura 2 minuti e 25 secondi) lavora in modo sistematico: toni sinusoidali di generatori analogici, registrati su nastro e tagliati in frammenti, sono disposti su *schermi* (*screens*), istantanee del suono suddivise in celle di frequenza e ampiezza come la matrice di Gabor; una successione di schermi forma un *libro* (*book*), che può costituire un intero suono complesso. Per distribuire i grani su uno schermo Xenakis ricorre alla teoria delle probabilità, con una distribuzione esponenziale per le durate e una regola lineare per frequenza, ampiezza e densità, e regola il grado di ordine e disordine fra schermi successivi, che chiama *ataxy* (atassia), con una catena di Markov. Roads ne ricava una critica che anticipa il resto del capitolo: l'ipotesi che tutti i grani abbiano la stessa durata e che gli schermi si susseguano a passo costante è esteticamente limitante, e produce artefatti udibili di modulazione costante o di filtraggio a pettine, mentre la durata del grano si rivela uno dei parametri più importanti da far variare nel tempo [@Roads2001, p. 67].

### I primi calcolatori

Xenakis non ha mai realizzato la sintesi granulare al calcolatore [@Roads2001, pp. 108-109]. Roads, che nel 1972 segue il suo seminario a Indiana University, la realizza a San Diego nel dicembre del 1974: l'esperimento, *Klang-1*, è la prima implementazione della sintesi granulare asincrona, e le specifiche di ogni grano (frequenza, ampiezza, durata) sono battute su una scheda perforata ciascuna, per una pila di circa ottocento schede, fra strumento e partitura, per trenta secondi di suono [@Roads2001, p. 110]. I grani di quei trenta secondi sono 766, uno per scheda [@Roads2001, p. 302]. L'esperienza impone l'automazione: Roads scrive un programma che genera le specifiche dei grani da descrizioni sintetiche di *nuvole*, e con quel programma realizza lo studio *Prototype*, di otto minuti [@Roads2001, p. 110]. Il sistema, descritto nel 1978, è un processore di ingresso per Music V: il compositore specifica *eventi*, ciascuno con un istante e una durata, valori iniziali e pendenze di forma d'onda, frequenza centrale, larghezza di banda, densità e ampiezza (Roads 1988 li conta in dodici parametri), e il programma calcola da ciascun evento migliaia di grani [@Roads1978, p. 61; @Roads1988, p. 12]. Il grano è di 20 millisecondi, con attacco e decadimento gaussiani e un picco sostenuto, e al più 32 grani suonano insieme [@Roads1978, p. 61]. Gli eventi si possono disegnare come poligoni sul piano frequenza-tempo, in una notazione grafica più libera di quella di Stockhausen nello *Studie II* [@Roads1978, p. 62].

Questo schema, una descrizione compatta che un programma traduce in una lista di eventi per un sintetizzatore separato, è quello che torna nei sistemi successivi. Nel 1981, al MIT, Roads granula suoni campionati con un programma in C che legge un copione con i parametri di una nuvola e produce una partitura di centinaia di note per Music 11, con uno strumento che estrae i grani dal file [@Roads2001, pp. 189-190]. CMask, di Bartetzki, fa lo stesso per Csound [@Bartetzki1997]. Il quadro di PGE (capitoli 3 e 7) ne è una ripresa.

Il secondo filone è il tempo reale. Truax realizza nel 1986 un sistema sul processore di segnali DMX-1000, controllato da un microcalcolatore, e nel 1987 lo estende alla granulazione di un breve suono campionato [@Roads2001, p. 112]. Il suo articolo del 1988 apre ponendo due problemi. Il primo è generare la gran quantità di dati necessaria a specificare il suono, perché si possono avere da mille a duemila grani al secondo. Il secondo è disegnare le variabili di controllo che colleghino i dati di basso livello alle strategie e ai gesti compositivi di alto livello. Gli editor di partitura e i programmi algoritmici soddisfano il secondo bisogno, ma i file prodotti sono di norma troppo grandi per essere maneggiati [@Truax1988, p. 14]. *Riverrun* (1986) è, nelle parole di Truax, probabilmente il primo brano realizzato interamente con sintesi granulare in tempo reale, con una densità massima di 2 375 grani al secondo [@Truax1988, pp. 14, 25].

Dallo stesso bisogno nasce l'uso di scelte statistiche: con migliaia di eventi al secondo servono, nelle parole di Truax, «strategie di controllo potenti» [@Truax1988, p. 19], ed è un'economia di mezzi, più che un cambio di postura compositiva. Non è la rinuncia al disegno: Truax descrive la propria composizione come un'organizzazione gerarchica di livelli, in cui la sovrapposizione di molti sotto-eventi simili e spettralmente imparentati produce una tessitura di livello macroscopico definita e controllabile, mentre la presenza di una singola componente frequenziale al livello micro può essere determinata soltanto in modo statistico [@Truax1988, p. 25].

| Anno | Chi | Che cosa |
|------|-----|----------|
| 1946-47 | Gabor | quanto acustico; granulatore elettro-ottico di suono registrato [@Gabor1947; @Roads2001, p. 61] |
| 1950-55 | Meyer-Eppler | la matrice di Gabor come partitura (*Mosaiktechnik*) |
| 1958-59 | Xenakis | *Concret PH*, *Analogique B*: grani di nastro, schermi, atassia |
| 1974-75 | Roads | *Klang-1*, *Prototype*; il sistema a eventi, per Music V |
| 1981 | Roads | granulazione di suoni campionati al calcolatore (MIT) [@Roads2001, p. 110] |
| 1986-87 | Truax | sintesi e granulazione in tempo reale (DMX-1000) |
| 1990 | Truax | granulazione in tempo reale di un suono in ingresso [@Roads2001, p. 112] |
| 1993 | Lippe | *granular sampling* con maschere di tendenza (ISPW, IRCAM) [@Lippe1993cim] |
| 1995 | Roads, Alexander | *Cloud Generator* [@Roads2001, p. 111] |

## Il grano e i suoi parametri

### Anatomia

Un grano è, per Roads, un breve evento microacustico, con una durata prossima alla soglia della percezione uditiva, tipicamente fra un millesimo e un decimo di secondo (da 1 a 100 ms), che contiene una forma d'onda modellata da un inviluppo d'ampiezza [@Roads2001, p. 86]. Gli estremi sono convenzionali: nel 1988 Roads dà da 1 a 50 ms, Truax parla di 10-50 ms [@Roads1988, p. 11; @Truax1994, p. 38], e le prime stime della durata ottimale andavano da 10 ms (Gabor) a 60 ms (Moles) [@Roads2001, p. 101]. Per Roads il grano è una rappresentazione adatta del suono musicale perché porta due dimensioni percettive: l'informazione nel tempo (istante d'inizio, durata, forma dell'inviluppo) e l'informazione in frequenza (l'altezza della forma d'onda e lo spettro). Le rappresentazioni a campioni non registrano la seconda, i metodi di Fourier non registrano la prima [@Roads2001, p. 87].

Il grano ha molti parametri e ne occorrono migliaia al secondo. Se $n$ è il numero di parametri per grano e $d$ la densità in grani al secondo, per specificare un secondo di suono servono $n \times d$ valori, con $n$ di solito maggiore di dieci e $d$ che può superare mille. Serve perciò un'unità di organizzazione globale: il compositore descrive il suono in termini globali, e l'algoritmo riempie i dettagli [@Roads2001, p. 87]. Le diverse forme di sintesi granulare si distinguono proprio per questa organizzazione globale, tema delle sezioni seguenti. Dal rapporto fra la semplicità dello strumento e la complessità del controllo Roads ricava un principio di sintesi: si può scambiare complessità dello strumento con complessità della partitura. Uno strumento semplice basta, perché la complessità del suono deriva dalla combinazione mutevole di molti grani, a patto di fornire un flusso massiccio di dati di controllo per ogni parametro [@Roads2001, p. 90]. L'ambiente descritto in questa tesina accetta lo scambio: il grano è un dato di otto campi (capitolo 3), e la complessità sta nella descrizione di come quei campi variano.

### L'inviluppo

L'inviluppo che modella il grano non è un dettaglio. L'inviluppo classico di Gabor è la campana gaussiana, la più liscia dal punto di vista matematico. Roads usa nei primi esperimenti una variante, la quasi-gaussiana (coseno raccordato a un rettangolo, nota anche come finestra di Tukey), che mantiene i raccordi lisci e aumenta l'ampiezza efficace. Nei primi sistemi in tempo reale si usano segmenti di retta, per risparmiare memoria e calcolo: il grano di Truax ha un inviluppo a tre tratti, con attacco e decadimento di un quarto della durata, la cui simmetria rende palindrome le tessiture dei modelli sintetici, cioè riproducibili all'indietro senza cambio timbrico [@Roads2001, p. 88; @Truax1988, p. 15]. Roads descrive anche il grano triangolare, la funzione *sinc* (che impone una forte modulazione) e due inviluppi asimmetrici: l'*expodec*, con attacco brusco (in genere sotto i 10 ms) e decadimento esponenziale, e la sua inversa, la *rexpodec*, con attacco lungo e caduta improvvisa [@Roads2001, pp. 88-90, 100].

L'inviluppo è inoltre una scelta spettrale. Quando i grani si susseguono a intervalli regolari, l'inviluppo complessivo è una funzione periodica e il segnale è una modulazione d'ampiezza: ogni componente del portante genera bande laterali, distanti dal portante quanto l'inverso del periodo dell'inviluppo, e la forma dell'inviluppo decide il numero e il peso delle bande. Roads scrive che con grani da 20 millisecondi le bande distano 50 Hz, e che per un inviluppo gaussiano anche lo spettro è una campana [@Roads2001, p. 98]. La cifra dei 50 Hz vale però solo se ogni grano è seguito subito da un altro della stessa durata, perché solo allora la durata del grano è il periodo dell'inviluppo [@Truax1988, p. 17]. La quasi-gaussiana ha un primo lobo laterale a -18 dB contro i -42 dB della gaussiana [@Roads2001, pp. 99-100]. Finestrare un grano è quindi modulare il suo segnale, e non un prelievo neutro. È la ragione per cui in PGE la forma della finestra è un parametro dello stream (capitolo 5) e non una convenzione fissa.

![Otto finestre del catalogo di PGE, con i nomi del catalogo. I nomi non coincidono tutti con quelli di Roads: la forma più vicina a quella che Roads chiama *expodec* (attacco brusco, decadimento esponenziale) è `rexpodec` nel catalogo, e quella più vicina alla *rexpodec* di Roads (attacco lungo, caduta improvvisa) è `rexporise`.](docs/images/finestre_catalogo.pdf){width=100%}

Il catalogo di PGE comprende le finestre a somma di coseni (Hann, che è il valore predefinito, Hamming, Blackman e Blackman-Harris), la gaussiana, la triangolare, la rettangolare, la Kaiser-Bessel, una semisinusoide, una `sinc` ridotta al solo lobo centrale e un gruppo di curve esponenziali, ma non la quasi-gaussiana né il segmento a tre tratti. Le sue finestre asimmetriche cominciano o finiscono a un valore pieno, senza il tratto di attacco di Roads. Chi legge Roads deve tenerlo presente: i nomi `expodec` e `rexpodec` del catalogo non designano le forme omonime del libro, e per quelle occorre cercare la forma più vicina.

C'è infine un'osservazione sul verso. Truax ha ipotizzato che, come nella fisica delle particelle il tempo è reversibile a livello quantistico, un grano invertito nel tempo suoni allo stesso modo. Roads mostra che vale solo in condizioni speciali: l'inviluppo deve essere simmetrico, la forma d'onda non deve cambiare nel tempo, e una tessitura è reversibile solo se stazionaria in senso statistico, cioè con inviluppi d'ampiezza e spettro simmetrici, densità interna costante e forme d'onda simili [@Roads2001, pp. 100-101]. Per un suono campionato, che in generale non è stazionario, il verso di lettura conta: in PGE è un parametro del grano, con un proprio inviluppo (capitolo 5).

### La durata

La durata del grano è il parametro con l'effetto più forte, e lo ha in più modi. Roads distingue quattro classi: durata costante, variabile nel tempo, casuale fra due limiti, dipendente da un altro parametro (come nei wavelet o nei *grainlet*) [@Roads2001, p. 101]. Gli effetti percettivi sono riassunti da Roads in una tabella, per le nuvole asincrone [@Roads2001, p. 101]:

| Durata del grano | Frequenza della modulazione | Effetto percepito |
|---|---|---|
| 200 µs | 5 kHz | disgregazione rumorosa e particellare |
| 500 µs | 2 kHz | |
| 1 ms | 1 kHz | perdita dell'altezza |
| 10 ms | 100 Hz | tremolio, gorgoglio |
| 50 ms | 20 Hz | formazione di un'altezza stabile |
| 100 ms | 10 Hz | |
| 200 ms | 5 Hz | tremolo aperiodico, *jittering* |

La relazione è quella di Gabor: più il segnale è breve, più la sua banda è larga, e l'ampiezza della banda occupata dalle bande laterali è inversamente proporzionale alla durata del grano [@Roads2001, p. 102]. Sotto i 2 ms circa (frequenze fondamentali oltre 500 Hz) i grani suonano come *click*, ma il timbro del click si può ancora modificare cambiando forma d'onda e frequenza del grano. A 5 ms l'impressione d'altezza è vaga e diventa chiara intorno ai 25 ms [@Roads2001, p. 88]. Anche per Truax il discrimine è a circa 50 millisecondi: con grani molto più brevi si ha la fusione in una tessitura continua, con grani molto più lunghi si percepiscono eventi separati, e intorno ai 50 ms sta un continuo fra la fusione a frequenza audio e gli eventi discreti [@Truax1988, p. 18].

### Densità e fattore di riempimento

La densità è il numero di grani al secondo, ma da sola dice poco sulla tessitura, perché con la durata del grano produce la tessitura. Venti grani da 100 ms in un secondo formano una nuvola continua e opaca, mentre venti grani molto più brevi formano una nuvola rada e trasparente. La differenza è il *fattore di riempimento* (*fill factor*): il prodotto della densità per la durata del grano in secondi, che nel primo caso vale 2. Per il secondo caso Roads scrive 1 ms e 0,2, ma i due numeri non coincidono (0,2 è il valore per grani da 10 ms; per grani da 1 ms il prodotto è 0,02). Roads distingue nuvole *rade* (FF < 0,5, più della metà della nuvola è silenzio), *coperte* (FF circa 1) e *compatte* (FF > 1, grani sovrapposti) [@Roads2001, p. 105]. In una nuvola asincrona l'istante d'inizio è casuale, e non si garantisce che cinquanta grani da 20 ms riempiano un secondo. Una regola pratica per una nuvola piena è porre la densità ad almeno 2/D, con D durata del grano in secondi [@Roads2001, p. 106].

Le soglie percettive della densità, per grani di 25 ms, sono quelle di Roads [@Roads2001, p. 106]:

| Densità (grani al secondo) | Percezione |
|---|---|
| meno di 15 | sequenze ritmiche |
| da 15 a 25 | *flutter*: la sensazione di ritmo scompare, nelle nuvole asincrone si sentono intermittenze |
| da 25 a 50 | l'ordine dei grani scompare, si inferiscono i limiti di frequenza |
| da 50 a 100 | banda di tessitura |
| oltre 100 | massa sonora continua; in certi casi somiglia a un riverbero |

Il fattore di riempimento è, nel linguaggio di PGE, una chiave alternativa alla densità (capitolo 5): chi la usa pensa alla copertura e non alla frequenza di emissione.

### Forma d'onda, banda e spazio

Gli altri parametri della nuvola si possono riassumere in poche righe. La forma d'onda dentro il grano può variare grano per grano: fissa e sintetica (seno, dente di sega, quadra, *sinc*), tratta da un suono campionato, oppure variabile nel tempo. Una nuvola può essere *monocroma* (una forma d'onda), *policroma* (due o più) o *transcroma* (la forma d'onda evolve da una all'altra) [@Roads2001, pp. 103-104]. La banda di frequenze limita le frequenze fondamentali dei grani, che si disperdono in modo uniforme in una banda (*cumulus*) o si allineano a un insieme di altezze (*stratus*) [@Roads2001, p. 104]. Con bande strette e densità alte si ottengono flussi con spettro a formanti, con bande medie un rumore colorato, con bande larghe masse di suono [@Roads2001, pp. 106-107]. Il suono granulare chiede infine un'uscita multicanale, con una posizione propria per ogni grano: se ogni grano cade in un punto diverso, la nuvola ha una morfologia spaziale tridimensionale anche in stereofonia, e la dispersione casuale è efficace per articolare grani lunghi a bassa densità [@Roads2001, p. 107].

Roads elenca sette parametri con cui il compositore specifica una nuvola [@Roads2001, p. 96]. Ciascuno ha un corrispondente nel linguaggio di PGE, con la differenza che l'oggetto dei grani non è una forma d'onda sintetica ma un suono campionato.

| Parametro della nuvola [@Roads2001, p. 96] | In PGE |
|---|---|
| istante d'inizio e durata della nuvola | `onset` e `duration` dello stream |
| durata del grano (costante, variabile, casuale) | `grain.duration`, come valore, inviluppo, o con `duration_range` |
| densità, variabile nel tempo | `density` o `fill_factor`, e `distribution` |
| banda di frequenze | `pitch` (rapporto e banda di variazione): nel campionamento la frequenza del grano diventa trasposizione |
| inviluppo d'ampiezza della nuvola | `volume` |
| forma d'onda nei grani | `sample` e il blocco `pointer` |
| dispersione spaziale | `pan` e `pan_range` |

## Flussi sincroni e asincroni

Il modo in cui i grani si dispongono nel tempo distingue, secondo Roads, le forme principali di sintesi granulare. Roads ne elenca sei: matrici e schermi sul piano tempo-frequenza, flussi sovrapposti sincroni con l'altezza, flussi sincroni e quasi sincroni, nuvole asincrone, modelli fisici o astratti, granulazione di suono campionato [@Roads2001, p. 91]. Le prime due partono dall'analisi di un suono esistente: la matrice di Gabor, le trasformate di Fourier e wavelet, la sintesi granulare con sincronia d'altezza di De Poli e Piccialli [@Roads2001, p. 92; @DePoliPiccialli1991]. Gli schermi di Xenakis appartengono alla prima famiglia, ma invece di partire da un suono analizzato lo riempiono di grani con algoritmi stocastici [@Roads2001, p. 92]. Qui interessano le forme sincrone, quasi sincrone e asincrone, e la granulazione.

Nella sintesi granulare **sincrona** il suono risulta da uno o più flussi di grani, in cui ogni grano segue il precedente a intervalli regolari. La densità, cioè la frequenza di emissione, si può leggere come una frequenza in hertz. Con densità fra 0,1 e 20 grani al secondo si ottengono ritmi metrici, e quando la densità cambia nel tempo si sentono accelerando e rallentando. Con densità maggiori i grani si fondono in toni continui con una forte frequenza fondamentale, e secondo l'inviluppo e la durata del grano compaiono bande laterali che possono suonare come altezze separate o fondersi in una formante, talvolta con una qualità simile alla voce [@Roads2001, p. 93]. L'altezza percepita di un flusso sincrono è un'illusione fragile e dipende dall'interazione di tre periodicità: il periodo della forma d'onda nel grano, quello dell'inviluppo del grano e quello della densità, cioè della frequenza di emissione. Una o l'altra può prevalere nel decidere l'altezza, e l'interazione può rendere ambigua l'altezza, e in particolare l'ottava [@Roads2001, pp. 93-94].

Nella sintesi **quasi sincrona** i grani si susseguono a intervalli disuguali, e una deviazione casuale ne decide l'irregolarità. Se l'irregolarità è grande, il risultato si avvicina a quello della sintesi asincrona [@Roads2001, p. 93]. Il caso estremo, in cui l'istante di ogni grano è casuale, è quello della sintesi **asincrona**, che abbandona i flussi lineari e disperde i grani su una durata data, entro regioni del piano tempo-frequenza chiamate *nuvole*, che sono le unità con cui lavora il compositore. La dispersione è irregolare nel tempo e governata da un algoritmo stocastico o caotico [@Roads2001, p. 96]. La casualità degli istanti produce un ispessimento controllabile dello spettro, uno sfocamento della struttura formantica [@Roads2001, p. 99; @Truax1988].

In termini di segnale l'effetto della regolarità si vede nella modulazione. Quando la durata del grano non varia e il ritardo è nullo, ogni grano è seguito subito da un altro della stessa durata, e la durata diventa il periodo dell'onda modulante: Truax ottiene così un'onda modulata in ampiezza, e per una durata di 8 ms una modulante a 125 Hz. Anche una piccola variazione di durata produce invece una tessitura stocastica [@Truax1988, p. 17]. Quanto alla frequenza di modulazione, vale l'inverso della durata del grano più il ritardo fino al successivo: un grano da 15 ms con 5 ms di ritardo produce una modulazione a 50 Hz [@Truax1988, p. 18]. Il manuale di elaborazione dei segmenti temporali di Dutilleux e colleghi riassume la distinzione in due categorie semplificate: strategie sincrone, basate soprattutto su funzioni deterministiche, e strategie asincrone, basate su funzioni stocastiche. Le due variabili di controllo principali sono il ritardo fra i grani di un flusso e il grado di sincronicità fra i grani di flussi diversi [@Dutilleux2016, pp. 110-111]. In PGE il primo è la distribuzione degli intervalli fra i grani del capitolo 5, e il secondo lo `scatter` fra le voci del capitolo 6.

C'è un'avvertenza terminologica. «Sincrono» ha più di un senso: nel lavoro di De Poli e Piccialli la sintesi sincrona aggancia i grani al periodo del suono quasi periodico analizzato, per conservare la continuità di fase [@DePoliPiccialli1991; @Roads2001, p. 92], mentre nella tradizione di Roads e Truax, che è anche quella di PGE, indica soltanto la regolarità degli intervalli.

### La maschera di tendenza

Come specificare la dispersione, in pratica? Il metodo che Truax mette al centro del suo sistema è la *maschera di tendenza*. La maggior parte delle variabili di controllo del suo sistema è descritta da un valore medio e da un intervallo intorno ad esso, da cui si estrae a caso: due grandezze che sono esattamente quelle che descrivono una maschera. La maschera è però espressa come un'area entro cui i valori possono essere scelti. È uno dei modi più semplici per specificare una selezione variabile nel tempo, e la sua larghezza in ogni punto determina l'intervallo di scelta, fornendo un continuo fra scelte deterministiche e scelte stocastiche. Truax osserva anche che, essendo per sua natura un metodo di controllo visivo, la maschera presenta un'immagine della forma del controllo: suggerisce gesti, mentre una coppia di parametri numerici variabili suggerisce processi in corso [@Truax1988, p. 23]. Lippe la applica nel 1993 al granular sampling: i grani sono scelti in modo statistico entro maschere di tendenza, finestre in continuo movimento di ampiezza variabile. Una finestra grande quanto un solo grano, che avanza in un suono e si allarga fino a coprire l'intero campione di dieci secondi, produce un suono che comincia intatto e diventa via via una massa statistica [@Lippe1993cim, p. 181]. Gli stessi due ingredienti, un valore centrale che varia nel tempo e una banda di variazione, sono la struttura dei parametri del linguaggio di PGE, descritta nel capitolo 4.

## La granulazione del suono campionato

### Sintesi e granulazione

Finora il grano conteneva una forma d'onda. Se il contenuto è un frammento di suono già registrato, si parla di granulazione. Roads la distingue dalla sintesi granulare con forme d'onda sintetiche: la sintesi *costruisce* un suono, la granulazione ne *trasforma* uno esistente [@Roads2001, p. 86]. Granulare significa segmentare, o finestrare, un segnale in grani, eventualmente modificarli, e riassemblarli secondo un nuovo ordine temporale e un nuovo microritmo; è un'operazione puramente nel dominio del tempo [@Roads2001, pp. 98, 188]. Con la formalizzazione di Dutilleux e colleghi, un grano è il segmento estratto da un segnale di ingresso $x$ con una finestra $w_k$ di lunghezza $L_k$ a partire dall'istante $i_k$, e l'uscita è la somma dei grani collocati agli istanti $n_k$, con ampiezze $a_k$:

$$ g_k(i) = x(i + i_k)\, w_k(i), \qquad y(n) = \sum_k a_k \, g_k(n - n_k) $$

[@Dutilleux2016, pp. 109-110]. Sono i parametri del grano di PGE (capitolo 5): $i_k$ è la posizione di lettura, $n_k$ l'istante di emissione, $w_k$ la finestra, $a_k$ il volume. Il risultato dipende fortemente dal criterio con cui si scelgono gli istanti $n_k$: se sono regolari e la forma del grano non cambia troppo, si ottiene un treno di impulsi filtrati, un suono periodico il cui inviluppo spettrale è quello del grano; se la distanza fra due grani è molto maggiore della loro durata, grani separati da silenzi; se molti grani brevi si sovrappongono, una tessitura [@Dutilleux2016, p. 110].

Lippe, nel 1993, dà a questa distinzione il suo nome. Granular synthesis e *granular sampling* sono varianti della stessa tecnica, ma le loro essenze musicali stanno a poli opposti: la prima appartiene all'*elektronische Musik* e a suoni puramente sintetici, la seconda alla musique concrète, in cui suoni registrati sono manipolati e trasformati [@Lippe1993cim, p. 179]. Il granular sampling è, come suggerisce Jean Piché, una tecnica «dipendente dall'ingresso» (*input dependent*), e opera su un oggetto sonoro già esistente, il che apre un livello di implicazione musicale che nella sintesi non c'è. Con il campionamento compare anche un parametro in più, l'istante da cui si preleva nel suono memorizzato, che può avere un'importanza primaria. L'ordine dei grani non è più un parametro «commutativo» o arbitrario, e crea una gerarchia implicita fra i parametri. Se si granula il parlato e gli istanti di prelievo scendono in ordine dall'alto al basso, mentre tutti gli altri parametri sono calcolati a caso, il risultato è sempre riconosciuto come parlato suonato all'indietro, anche se le varianti possono suonare molto diverse. Una delle caratteristiche musicalmente più interessanti del granular sampling è per Lippe la capacità di *decostruire* i suoni con la manipolazione degli istanti di prelievo, muovendosi sul continuo che separa il riconoscibile dal non riconoscibile [@Lippe1993cim, pp. 179-180]. È la nozione su cui si regge il dominio di PGE (capitolo 3): la posizione di lettura nel materiale è un parametro di prima classe.

### Un'operazione antica, in tempo reale e in tempo differito

La granulazione digitale ha una storia breve. Roads la sperimenta al MIT nel 1981, su suoni di percussioni e di sassofono, e Truax è il primo a realizzarla in tempo reale, nel 1986-87, con il programma GSAMX sul DMX-1000 [@Roads2001, pp. 110, 190]. Il sistema opera su un campione fisso di 4 032 campioni, circa 150-170 ms di suono, per via della piccola memoria del processore [@Truax1988, p. 15]. Le sue variabili di controllo sono, ancora oggi, il lessico della granulazione: lo scostamento dall'inizio del campione e la sua banda di variazione, la durata media e la banda della durata, il ritardo fra i grani e la velocità di lettura, che agisce come trasposizione di altezza e di tempo [@Truax1988, pp. 15-18]. Il grano ha un attacco e un decadimento, e per questo non ci sono scatti o transitori quando si estrae un segmento da un punto arbitrario [@Truax1988, p. 16]. Nel 1990 Truax estende il sistema alla granulazione di un suono in ingresso e alla registrazione su disco di campioni lunghi, con dilatazione temporale: con grani di suono campionato di durata in genere inferiore a 50 ms, la tecnica allunga il suono senza cambiarne l'altezza [@Roads2001, pp. 112, 190; @Truax1994, p. 38].

La granulazione in tempo reale ha due forme: quella di un suono in ingresso, per esempio da un microfono, e quella di un file con controllo in tempo reale. Il granulatore di un suono in ingresso funziona come una linea di ritardo con puntatori di lettura [@Roads2001, p. 191], e il suo limite è nella freccia del tempo: «granulation may be many things, but it is not omniscient» (Truax, citato in [@Roads2001, p. 192]). Un puntatore non può guardare nel futuro, e quindi nemmeno accorciare il suono. La lettura da file non ha questo limite. Roads osserva che la riproduzione asincrona da un file dà molta più libertà della granulazione in tempo reale di un suono che viene da un microfono: poiché il suono sta in un file, i grani si possono estrarre in qualunque ordine, in sequenza, all'indietro, a caso, con un'evoluzione statistica o in una successione arbitraria [@Roads2001, pp. 188-189]. I parametri della granulazione sono, nel suo elenco: l'ordine di selezione dei grani (sequenziale, quasi sequenziale, casuale), la trasposizione, l'ampiezza, la posizione e la traiettoria spaziale, la durata, la densità, la forma dell'inviluppo, il disegno temporale (sincrono o asincrono) e gli effetti applicati grano per grano [@Roads2001, p. 188]. Il lessico di PGE ne ricalca la maggior parte, e la lettura da file di un campione, con puntatore, anello e verso, è il caso che Roads descrive come il più libero. Roads distingue infine la granulazione dal micromontaggio: la prima è inevitabilmente un processo automatico, mentre l'artista può realizzare il secondo lavorando direttamente, punto per punto, e il compito richiede una pazienza fuori dal comune [@Roads2001, p. 187].

### Durata del grano e riconoscibilità

Che cosa resta del suono d'origine dipende soprattutto dalla durata del grano. Per Roads, quando i grani sono molto brevi (meno di 40 ms), i file campionati perdono le loro qualità intrinseche identificabili, mentre per materiali che si vogliono conservare, come il testo parlato, funzionano meglio grani più lunghi, oltre i 40 ms [@Roads2001, p. 189]. Truax assegna a 50 ms una funzione analoga con un suono campionato: intorno a quella soglia, e sopra di essa, dominano le qualità timbriche del suono di partenza, e sotto domina la fusione dei frammenti a frequenza audio. Aggiunge che la durata di grani molto brevi può essere inferiore a un periodo del suono campionato e produrre un risultato a banda larga [@Truax1988, pp. 18-19]. Dutilleux e colleghi lo dicono con gli stessi termini: i grani lunghi tendono a mantenere l'identità timbrica della porzione di segnale d'ingresso, quelli corti assumono una qualità impulsiva [@Dutilleux2016, p. 109]. Nelle conclusioni aggiungono che, quando l'organizzazione dei grani cambia su larga scala, il suono d'ingresso può essere molto meno riconoscibile nell'uscita [@Dutilleux2016, p. 112]. Ricordano anche che lo spettro locale incide sulla struttura globale del suono, e che per questo si può analizzare un suono in grani senza alterarne le caratteristiche complessive, «come gocce d'acqua per suoni tipo corso d'acqua» [@Dutilleux2016, p. 111].

La granulazione può anche distruggere ciò che granula. Roads cita Lavoisier: granulare e polverizzare sono, a rigore, operazioni meccaniche, che non raggiungono la struttura interna della materia, e ogni molecola, dopo la granulazione, somiglia ancora al materiale d'origine. E tuttavia, osserva Roads, una pietra multicolore può essere ridotta a una polvere grigia indistinta, e certe granulazioni rendono la sorgente irriconoscibile distruggendone la morfologia [@Roads2001, p. 192]. Truax osserva che in certi casi il risultato acustico della sintesi granulare somiglia ai suoni ambientali per complessità interna e tessitura statistica, e che in *Riverrun* ogni suono è in uno stato di flusso costante, come i suoni ambientali in generale e il suono dell'acqua in particolare [@Truax1988, pp. 24-25]. Nel 1994 parla di un'esperienza compositiva che lega la complessità interna del suono alla complessità del mondo esterno [@Truax1994, p. 38].

### Il quadro di PGE

Il capitolo ha fissato il vocabolario. PGE granula un file con un puntatore che si muove nel campione, emette i grani su una griglia che va dal sincrono all'asincrono, descrive i parametri con valori centrali e bande di variazione e legge il file in un ordine scelto: è la granulazione da file di Roads e il granular sampling di Lippe, con il tempo differito che la lettura da un file rende possibile, e con la stessa catena che Roads usava nel 1981, dalla descrizione di una nuvola alla lista di eventi per un sintetizzatore separato. I capitoli seguenti descrivono come sono costruiti i singoli pezzi.


# Architettura di Python Granular Engine

Questo capitolo descrive come Python Granular Engine (d'ora in avanti PGE) è costruito e perché è costruito così. Il linguaggio YAML (capitolo 4), il grano e lo stream (capitolo 5), le voci (capitolo 6) e i renderer (capitolo 7) hanno capitoli propri; qui interessano le parti del programma, la responsabilità di ciascuna e i contratti che le tengono insieme. Il disegno ruota attorno a una sola scelta: il motore non produce suono, produce una *lista di grani*, e tutto il resto è lavoro che precede o che segue quella lista. Le altre scelte ne sono conseguenze. Chi produce la lista non sa come la si trasforma in audio, e chi la consuma non sa come è stata prodotta. Aggiungere un consumatore, una strategia o una finestra non richiede di toccare chi produce. E poiché ogni scelta casuale viene presa in produzione e soltanto lì, la stessa specifica dà la stessa lista.

La versione descritta è la 9.1.0 [@DeMattia2026Pge], con le modifiche non ancora rilasciate fino al commit `1188dbc` del 13 ottobre 2026, fra cui la chiave `file:` del capitolo 4. I brani di codice citati sono identici nella 9.1.0 e in quel commit. Il pacchetto `pge` si divide in nove sotto-pacchetti e conta circa 26 400 righe di Python in `src/`, con 164 file di test. Dipende da NumPy, `soundfile`, matplotlib (importato soltanto quando serve) e PyYAML; Csound o SuperCollider servono ai rispettivi renderer. L'integrazione continua lo prova dalla versione 3.9 alla 3.14 di Python.

## La pipeline: dal file YAML al suono

Un brano attraversa tre fasi, che la figura mette in fila. La prima costruisce gli oggetti: legge lo YAML e crea uno `Stream` per ogni stream dichiarato. La seconda genera i grani di ciascuno stream. La terza consuma la lista dei grani e la trasforma in audio, in un'immagine o in un file di scambio. I dati scorrono in un solo verso, dall'alto in basso. La richiesta di lavoro che mette in moto la seconda fase corre invece in verso opposto, ed è ciò che permette di tenere distinte le prime due fasi.

![La pipeline di PGE. Le frecce piene portano i dati dal file YAML ai file di uscita; quella tratteggiata porta in senso contrario la richiesta che innesca la generazione dei grani. Reaper e Sonic Visualiser leggono i parametri dello stream, non la lista dei grani.](docs/images/pipeline.pdf){width=100%}

L'intera pipeline si legge in poche righe dell'interfaccia programmatica, `pge.api`. La costruzione è la funzione `load_generator`:

```python
generator = Generator(yaml_path, samples_dir=samples_dir)
generator.load_yaml()
generator.create_elements()
```

Il consumo, nella funzione `render`, mette un renderer, un criterio per i nomi dei file e una modalità davanti alla lista degli stream:

```python
engine = RenderingEngine(
    renderer_obj,
    naming_strategy=DefaultNamingStrategy(ext=audio_format.extension),
)
mode = StemsRenderMode() if per_stream else MixRenderMode()
generated = engine.render(
    streams=generator.streams,
    output_path=output_path,
    mode=mode,
)
```

Fra le due non c'è nessuna chiamata che generi i grani: la generazione non è un passo che il programma ordina, è l'effetto della prima lettura della lista (sottosezione 3.1.1).

**Costruzione.** Il `Generator` (`engine/generator.py`) è l'orchestratore. Il metodo `load_yaml()` legge il file, valuta le espressioni scritte nei valori (per esempio `(pi)` o `(10/3)`) e ne ricava il seme. Il metodo `create_elements()` applica la regola solo/mute e costruisce uno `Stream` per ogni stream rimasto. Lo `Stream` (`core/stream.py`) è l'unità compositiva: alla costruzione legge i propri parametri dallo YAML, li convalida e li affida a collaboratori specializzati (sezione 3.3). Alla fine della fase ogni stream è configurato e convalidato, e non ha ancora un solo grano. Intanto il `Generator` registra i campioni e le finestre degli stream in una tabella dei simboli, `FtableManager`, di cui si dice nella sezione 3.2.

**Generazione.** Alla prima lettura di `stream.voices`, `generate_grains()` produce la lista: un cursore del tempo per voce, un grano per voce attiva a ogni passo, infine la strategia di *clip* per i grani che sporgerebbero oltre la fine dello stream (capitoli 5 e 6).

**Consumo.** La lista è letta da tre tipi di consumatore. I renderer (NumPy, Csound, SuperCollider) la trasformano in audio; li coordina il `RenderingEngine`, che non sa quale dei tre ha davanti (sezione 3.6). La MAP (`ScoreVisualizer`) disegna ogni grano nel piano tempo-posizione di lettura e, sotto, le curve dei parametri. L'esportazione JSON scrive i grani di ogni stream. Altri due esportatori non leggono la lista: il progetto Reaper dispone gli stem sulla timeline e gli bastano onset, durata e nome dello stream; la sessione Sonic Visualiser disegna le curve dei parametri. Il confine fra produzione e consumo passa dalla lista, ed è per questo che un consumatore si aggiunge senza toccare il resto.

In termini di Seeger [@Seeger1958] il file YAML è una notazione *prescrittiva*, un'istruzione data al motore prima del rendering. La MAP è *descrittiva*: documenta ciò che è stato effettivamente generato e non viene riletta come input. Il verso unico della pipeline è lo stesso: la specifica sta a monte, i documenti derivati a valle, e nessuno risale.

### La generazione lazy

*Lazy evaluation* è un termine tecnico che si lascia in inglese. Indica una strategia di calcolo in cui un valore non viene calcolato nel punto in cui è definito, ma soltanto quando qualcuno ne ha bisogno. Al primo bisogno il calcolo si esegue e il risultato si conserva (si dice che è *memoizzato*); i bisogni successivi ricevono il risultato conservato senza ricalcolare. La strategia opposta si dice *eager*: il valore si calcola subito, alla definizione. Dalla differenza discendono tre proprietà della lazy evaluation: il calcolo si esegue al più una volta, può non eseguirsi mai, e il momento in cui si esegue lo stabilisce la richiesta di chi consuma il risultato, non l'ordine in cui il programma è scritto. Hughes [@Hughes1989] vede in quest'ultima proprietà ciò che permette di scomporre un programma in un produttore e un consumatore indipendenti: chi consuma decide quanto lavoro deve fare chi produce.

Il prezzo è di due tipi. Il costo si sposta: il primo accesso è più lento dei successivi, e un errore nato dentro il calcolo compare lì e non alla definizione. E il calcolo è sicuro soltanto se il suo risultato non dipende dal momento in cui si esegue: se leggesse uno stato condiviso, come un generatore casuale globale, cambiare l'ordine delle richieste cambierebbe il risultato.

In PGE la lista dei grani di uno stream è lazy. Il costruttore di `Stream` lascia vuoto il campo `_voices` e il segnale `generated` a `False`. Il calcolo sta dietro una proprietà (`@property`), il meccanismo con cui Python fa passare per un attributo ciò che in realtà è una chiamata:

```python
@property
def voices(self) -> List[List[Grain]]:
    """Grani organizzati per voce. Lazy: genera al primo accesso."""
    if not self.generated:
        self.generate_grains()
    return self._voices
```

Chiunque legga `stream.voices`, sia un renderer, la MAP o un esportatore, innesca la generazione la prima volta e riceve la lista conservata le volte successive. Il metodo `generate_grains()` chiude con due assegnazioni, e assegna al campo e non alla proprietà, perché il getter di `.voices` richiamerebbe `generate_grains()` all'infinito:

```python
self._voices = clip_strategy.apply(all_voice_grains, self)
self.generated = True
```

Il vantaggio non è dove si penserebbe. Quando il sistema lavora per stem con la cache attiva, il renderer chiede alla cache se lo stream è cambiato *prima* di leggere le voci (`NumpyAudioRenderer._cache_skip`; gli altri due renderer fanno lo stesso):

```python
if not self.cache_manager:
    return False
stream_dict = self.stream_data_map.get(stream.stream_id)
if not stream_dict:
    return False
dirty = self.cache_manager.is_dirty(stream_dict, output_path)
status = "DIRTY" if dirty else "clean"
print(f"[CACHE] {stream.stream_id}: {status}", flush=True)
return not dirty
```

Uno stream pulito non genera mai i propri grani, perché nessuno ne ha letto la lista. Lo si verifica rendendo due volte lo stesso brano di tre stream con lo script `lazy_e_riproducibilita.py`, nella cartella `esempi/architettura` del repository della tesina: dopo il secondo rendering, a cache a regime, `generated` è `False` per tutti e tre. Anche `Stream.__repr__` è scritto in modo da non innescare la generazione: finché i grani non esistono dichiara `grains=lazy`.

Non è però un'ottimizzazione del totale, e il capitolo 7 lo dice con le misure. La costruzione degli oggetti `Grain` pesa da un ottavo a un terzo del tempo di un rendering; il resto è la somma dei grani nel buffer. Se tutti gli stream sono da rifare, il lavoro è quello di una generazione eager, solo spostato in avanti. La lazy evaluation serve a non pagare il lavoro che la cache ha reso inutile e a tenere economica la costruzione degli stream.

Le due condizioni del prezzo sono rispettate. Ogni componente stocastico pesca da un generatore proprio, derivato dal seme (sezione 3.7), e quindi il risultato non dipende dal momento in cui si genera: lo script verifica che generare gli stream in ordine inverso, o metterne uno in mute, lascia identici i grani degli altri. La validazione dello YAML è eager, e i suoi difetti (una strategia inesistente, un parametro fuori dominio) si segnalano alla costruzione e non al primo accesso. Resta un caso non chiuso: uno `Stream` costruito fuori dal `Generator` si costruisce senza errori e fallisce soltanto al primo accesso a `.voices`, con un `AttributeError` su `window_table_map` (sezione 3.8).

## Il grano e la tabella dei simboli

La lista dei grani è il punto stretto del disegno: è l'unico oggetto che attraversa il confine fra produzione e consumo, e contiene un tipo solo (`core/grain.py`):

```python
@dataclass(frozen=True)
class Grain:
    __slots__ = (
        'onset', 'duration', 'pointer_pos', 'pitch_ratio',
        'volume', 'pan', 'sample_table', 'envelope_table',
    )
    onset: float
    duration: float
    pointer_pos: float
    pitch_ratio: float
    volume: float
    pan: float
    sample_table: int
    envelope_table: int
```

Ogni scelta della dichiarazione ha una ragione. Il grano è *congelato* (`frozen=True`): una volta creato nessuno può modificarlo, e quindi la generazione e i consumatori non possono interferire. L'immutabilità rende possibile anche il passaggio dei grani ai processi del renderer NumPy parallelo, che avviene per *pickle*: una classe congelata e con `__slots__` non sopravvive al pickle predefinito, e per questo il grano definisce `__reduce__`, che lo ricostruisce dal costruttore conservando validazione e immutabilità. Il grano ha poi `__slots__`, cioè nessun dizionario per istanza: un brano come *mare-nostrum* ne contiene più di tre milioni (capitolo 10), e il capitolo 7 misura circa 225 byte per grano.

Il grano contiene soltanto numeri: l'istante, la durata, la posizione di lettura, il rapporto di altezza, il volume, il pan e due interi. Il verso di lettura non ha un campo proprio, è il segno di `pitch_ratio`: `PitchController.calculate` nega il rapporto quando il grano si legge all'indietro. I due interi, `sample_table` e `envelope_table`, sono numeri di tabella (il secondo identifica la finestra del grano, e il suo nome viene dal vocabolario di Csound, dove l'inviluppo d'ampiezza è una tabella di funzione). Un grano non porta il nome del suo campione né della sua finestra, ma un indice. Il significato dell'indice sta in una tabella dei simboli, `FtableManager`, che il `Generator` riempie alla costruzione:

```python
def register_sample(self, sample_path: str) -> int:
    if sample_path in self._sample_cache:
        return self._sample_cache[sample_path]
    num = self.next_num
    self.next_num += 1
    self.tables[num] = ('sample', sample_path)
    self._sample_cache[sample_path] = num
    return num
```

La registrazione deduplica: due stream che leggono lo stesso file hanno lo stesso numero. Ogni renderer riceve la stessa tabella, `{numero: ('sample', percorso) | ('window', nome)}`, e la materializza a modo proprio: Csound come tabelle di funzione nello score, NumPy come array, SuperCollider come buffer. È la stessa idea della tabella dei simboli di un compilatore: i nomi si risolvono una volta, fuori dal dato, e il dato resta leggero e neutro rispetto a chi lo consuma.

La lista è una `List[List[Grain]]`, una lista per voce, e l'ordine voce per voce è quello su cui i renderer sommano: l'ordine delle somme in virgola mobile è ciò che rende un rendering riproducibile bit a bit. `stream.voices` è l'unica fonte di verità sui grani esistenti. Una vista piatta, `stream.grains`, era un secondo campo allineato soltanto lungo un percorso, e fuori da quello le due viste divergevano senza avvisare; oggi è una vista derivata, in sola lettura e deprecata. Il criterio è un solo stato, e il resto derivato.

## Dallo YAML al valore: il parametro

Il grano si ottiene interrogando i parametri dello stream a un dato istante, e come un blocco di YAML diventi qualcosa che si può interrogare è la parte meno visibile e più sistematica dell'architettura. Alla costruzione lo `Stream` separa due cose che il file mescola. L'*identità* dello stream (nome, onset, durata, campione, gruppo del caso) va in uno `StreamContext`. Le *regole di processo* (l'interpretazione della probabilità di deviazione, la modalità del tempo, la strategia di clip, il seme) vanno in uno `StreamConfig`. Sono due `dataclass` congelate, costruite una volta (`core/stream_config.py`) e condivise da tutti i collaboratori dello stream, che non possono modificarle.

Per i parametri propri dello stream (volume, pan, durata del grano, finestra) la costruzione è guidata dai dati. Una lista di specifiche dichiarative, `STREAM_PARAMETER_SCHEMA`, dice dove ciascun parametro sta nello YAML:

```python
ParameterSpec(
    name='volume',
    yaml_path='volume',
    default=0.0,
    range_path='volume_range',
    deviation_probability_key='volume'
),
```

Un'altra tabella, `GRANULAR_PARAMETERS`, dice quali sono i limiti (`ParameterBounds`: minimo, massimo, banda ammessa, tipo di variazione). Il `GranularParser` sa come si costruisce un `Parameter`; il `ParameterOrchestrator` è il solo punto in cui lo schema, che sa *dove* sono i dati, incontra il parser, che sa *come* si costruisce l'oggetto, e vi inietta il gate di probabilità. Aggiungere un parametro allo stream è perciò una riga di limiti e una `ParameterSpec`, senza modificare il codice che costruisce. Lo stesso meccanismo serve i controller: puntatore e densità hanno ciascuno il proprio schema nello stesso modulo e un proprio `ParameterOrchestrator`.

Il `Parameter` (`parameters/parameter.py`) è l'oggetto in cui il linguaggio del capitolo 4 diventa comportamento. Il suo metodo `get_value(time)` è, come dice la docstring, l'unico che il resto del programma deve chiamare:

```python
def get_value(self, time: float) -> float:
    base_val = self._evaluate_input(self._value, time)
    current_range = self._calculate_range(time, base_val)
    if not self._probability_gate.should_apply(time):
        return self._clamp(base_val, time)
    final_val = self._variation_strategy.apply(
        base_val,
        current_range,
        self._distribution
    )
    return self._clamp(final_val, time)
```

I passi sono cinque. Il valore centrale si ricava da un numero o da un inviluppo; la banda di variazione si calcola nello stesso istante; il gate di probabilità decide se *questo* grano devia; se devia, una strategia di variazione estrae un valore dentro la banda con la forma di distribuzione scelta; un limite di sicurezza riporta il risultato nel dominio del parametro. È la maschera di tendenza di Truax [@Truax1988] resa come oggetto: un valore centrale che varia nel tempo e una banda intorno ad esso. Il caso entra in due punti per parametro, il gate e la distribuzione, e ciascuno riceve alla costruzione un generatore proprio (sezione 3.7).

Puntatore, altezza, densità e finestra non sono parametri semplici ma comportamenti, e hanno un controller ciascuno (`controllers/`). I quattro si costruiscono con la stessa firma, `(params, config)`, a partire dal proprio blocco YAML (`pointer`, `pitch`, `grain`) o, per la densità, dall'intero stream. Le voci hanno un `VoiceManager`, descritto nel capitolo 6. Il parametro e il controller sono i due modi in cui un blocco YAML diventa un oggetto che sa rispondere alla domanda «quanto vale al tempo *t*?».

Tutti i collaboratori convergono in `Stream._create_grain`, che compone il grano. Ogni campo viene da un collaboratore diverso: l'altezza dal controller dell'altezza, la posizione dal puntatore, il volume e il pan dai rispettivi `Parameter`, la finestra dal controller della finestra, e a ciascuno si sommano gli scarti della voce. Il metodo si conclude così:

```python
return Grain(
    onset=absolute_onset,
    duration=grain_dur,
    pointer_pos=pointer_pos,
    pitch_ratio=pitch_ratio,
    volume=volume,
    pan=pan,
    sample_table=self.sample_table_num,
    envelope_table=window_table_num
)
```

## Organizzazione dei moduli

Il codice si divide in nove sotto-pacchetti, più `api.py` e `cli.py` alla radice. La tabella riassume il ruolo dei sotto-pacchetti.

| Pacchetto | Ruolo |
|-----------|-------|
| `engine` | Il `Generator`: lettura dello YAML, importazione degli stream, regola solo/mute |
| `core` | I tre oggetti centrali: `Stream`, `Grain`, `StreamConfig` |
| `parameters` | Schema, limiti e costruzione dei parametri; la classe `Parameter` |
| `envelopes` | Gli inviluppi che fanno variare un parametro nel tempo: interpolazioni, segmenti, distribuzione dei punti |
| `controllers` | Densità, altezza, puntatore, finestra e gestione delle voci |
| `strategies` | Le strategie intercambiabili: distribuzione di altezza, onset, puntatore e pan sulle voci, variazione stocastica, clip del grano |
| `rendering` | I renderer, i traduttori verso i linguaggi dei sintetizzatori, la cache, la MAP |
| `export` | Esportazione verso Reaper, Sonic Visualiser e file JSON dei grani |
| `shared` | Ciò che serve a tutti: errori, logger, gestione del seme, utilità |

Il pacchetto `rendering` è di gran lunga il più ampio, con 32 moduli e circa un terzo delle righe, perché ospita i tre renderer e tutto ciò che sta intorno: la tabella dei campioni, la scrittura degli score, la cache incrementale e il visualizzatore.

I pacchetti non sono strati, e non lo si afferma per comodità: lo script `dipendenze.py`, nella stessa cartella, costruisce il grafo degli import leggendo i sorgenti come alberi sintattici. Tra i 97 file Python del commit descritto non c'è nessun ciclo di import, contando 276 archi anche quando l'import sta dentro una funzione. Tra i pacchetti, invece, cinque coppie si importano a vicenda: `core` con `controllers`, con `parameters` e con `strategies`, `parameters` con `strategies`, `envelopes` con `shared`. Il motivo è che un pacchetto raccoglie cose dello stesso genere e non dello stesso livello. `core` contiene sia il dato più basso (`Grain` e `StreamConfig`, importati dai controller) sia l'orchestratore più alto (`Stream`, che importa i controller). Al livello dei moduli un ordine esiste; al livello dei pacchetti no.

![Il verso delle dipendenze tra i sotto-pacchetti, come le calcola `dipendenze.py`. Si omettono gli archi che saltano uno strato. Nel riquadro centrale i pacchetti dipendono l'uno dall'altro senza un ordine fra pacchetti; né essi né la base importano i pacchetti sopra.](docs/images/dipendenze.pdf){width=70%}

Ciò che regge a ogni livello è un confine solo. Nessuno dei sei pacchetti in basso nella figura (`core`, `controllers`, `parameters`, `strategies`, `envelopes`, `shared`) importa `rendering`, `engine`, `export`, `api` o `cli`. I renderer conoscono il grano; il grano non conosce i renderer. Lo script lo verifica elencando chi importa ciascun pacchetto di quelli in alto.

Nella forma più stretta il confine è imposto da un test. La sintassi di Csound non deve comparire sotto il livello dei renderer, e `tests/rendering/test_csound_emitter.py` legge otto moduli come alberi sintattici, fra cui `Grain`, `FtableManager`, il catalogo delle finestre e `ScoreWriter`. Ne estrae i letterali stringa, escluse le docstring, e fallisce se uno apre una riga di score:

```python
_SCORE_STATEMENT = re.compile(r'^([if][ "{]|e\n$|; )')
```

Un secondo test controlla che la guardia non sia cieca: applicata a `CsoundEmitter`, che quelle righe le scrive per mestiere, deve trovarle.

La regola ha una storia concreta. All'origine un `Grain` sapeva scrivere la propria riga di score Csound, e la precisione a otto decimali dell'onset, necessaria perché a 96 kHz un grano può durare un solo campione, era una decisione sul formato di Csound presa dentro il dato. Un secondo renderer testuale non avrebbe avuto altro posto in cui mettere il proprio metodo che accanto al primo. Oggi la decisione sta in un modulo solo, `CsoundEmitter`:

```python
def grain_statement(self, grain, onset_offset: float = 0.0) -> str:
    return (f'i "{self.instrument_name}" '
            f'{grain.onset - onset_offset:.8f} {grain.duration:.8f} '
            f'{grain.pointer_pos:.6f} {grain.pitch_ratio:.6f} '
            f'{grain.volume:.2f} {grain.pan:.3f} '
            f'{grain.sample_table} {grain.envelope_table}\n')
```

È il criterio che Parnas [@Parnas1972] propone per scomporre un sistema: non secondo i passi dell'elaborazione, ma secondo le decisioni di progetto che è probabile cambino, ciascuna nascosta in un modulo. Il formato di uno score è una di queste decisioni.

## Libreria e riga di comando

PGE nasce come programma da lanciare dalla radice del repository e con il tempo è diventato anche una libreria che altri progetti importano. Le due esigenze sono diverse: una riga di comando stampa messaggi, restituisce codici di uscita e può fare scelte di comodo; una libreria non deve stampare, né terminare il processo, né decidere al posto di chi la usa.

Il sistema ha perciò due strati. `pge.api` è l'interfaccia programmatica: `load_generator`, `build_renderer`, `render`, `render_file` e le funzioni `export_*`. Non legge `sys.argv`, non chiama `sys.exit` e segnala gli errori con eccezioni; ogni percorso sul disco è un parametro esplicito. `pge.cli` è un guscio sottile che interpreta gli argomenti, stampa e fissa i codici di uscita, e delega tutto il lavoro all'API. Il file `src/main.py` e il comando `pge` sono due ingressi alla stessa CLI. Da Python, una composizione si rende in due righe:

```python
from pge import api
risultato = api.render_file("brano.yml", "brano.aif", renderer="numpy", per_stream=True)
```

La funzione restituisce un `RenderResult`, che elenca i file prodotti, il tipo di renderer, la durata e il numero di grani per stream. La differenza fra i due strati sta nelle *politiche*, cioè nei valori predefiniti.

| Decisione | API (valore predefinito) | CLI |
|-----------|--------------------------|-----|
| Processi paralleli | 1, risultato deterministico | automatico (core disponibili meno uno) |
| Renderer | NumPy, nessun programma esterno | Csound, la scelta storica |
| Percorso del file di cache | esplicito | derivato dal nome del file YAML |
| Messaggi a schermo | nessun `print` nel proprio modulo | sempre |

Il punto più delicato è che anche la libreria, nei fatti, scrive a schermo: alcuni componenti che orchestra hanno ereditato dei `print()` che fanno parte del protocollo con l'editor grafico del progetto (per esempio la riga `[CACHE]` della sezione 3.1, che PGE-ui legge per costruire l'avanzamento). L'API lo dichiara in un censimento, nell'intestazione del modulo, e un test lo verifica sull'output reale. Quando un'interfaccia non può essere del tutto silenziosa, è meglio che il contratto dica esattamente quanto non lo è.

## Estensibilità

L'architettura è pensata perché le estensioni siano *additive* rispetto al nucleo: si scrive un file e lo si registra, senza modificare `core`, `controllers` e `parameters`. Il principio è quello detto *aperto/chiuso*: un modulo deve essere aperto all'estensione e chiuso alla modifica [@Meyer1988]. I nomi dei meccanismi sono quelli dei pattern classici [@Gamma1994], e il codice li usa nelle docstring: *facade* per il `RenderingEngine`, *strategy* per le modalità e le strategie, *factory* per la scelta del renderer. L'estensione si realizza in quattro luoghi, e va detto subito che in uno di essi, i renderer, la modifica sfiora il perimetro.

### Un renderer nuovo

Il sistema deve produrre audio con più renderer, e deve poterlo fare in due modi: un file per ogni stream (*stems*) oppure un unico file con tutto il brano (*mix*). Le due scelte sono indipendenti. L'interfaccia astratta del renderer ha due metodi obbligatori e uno concreto (`rendering/audio_renderer.py`):

```python
class AudioRenderer(ABC):
    renderer_type: str = 'unknown'

    @abstractmethod
    def render_single_stream(self, stream, output_path: str) -> str:
        ...

    @abstractmethod
    def render_merged_streams(self, streams: List, output_path: str) -> str:
        ...

    def render_streams(self, pairs: List[Tuple[object, str]]) -> List[str]:
        return [self.render_single_stream(stream, path) for stream, path in pairs]
```

Il primo metodo rende *uno* stream in *un* file, con onset relativi allo stream e il file che inizia a zero. Il secondo rende più stream in un file, con onset assoluti. Il terzo è concreto e il suo comportamento predefinito è un ciclo sul primo; il renderer NumPy lo ridefinisce per affidare ogni stem a un processo di lavoro, quando conviene. Il renderer non decide se produrre stems o mix. Lo decide la modalità, un oggetto a parte, e lo decide in due righe:

```python
paths_map = naming.generate_paths(output_path, streams, mode='stems')
return renderer.render_streams(paths_map)
```

La modalità decide *che cosa* rendere (un file per stream) e il renderer decide *come*. Le due scelte si combinano di conseguenza liberamente: ogni renderer funziona con ogni modalità, e un renderer nuovo le eredita entrambe.

La scelta del renderer sta in una fabbrica, `RendererFactory`, e il suo elenco dei tipi validi è il solo che esista:

```python
_VALID_TYPES = {'numpy', 'csound', 'supercollider'}
```

I messaggi d'errore e la CLI interrogano `available_types()` e non ne tengono una copia. L'elenco non si aggiorna però da solo. Per aggiungere un renderer la documentazione di PGE (`docs/how-to/add-renderer.md`) prescrive un file nuovo e tre modifiche: l'elenco e un ramo di costruzione nella fabbrica, un ramo in `api.build_renderer` e i flag in `cli._build_renderer`. Il disegno è additivo per il nucleo e non per il perimetro.

### Parametri e finestre

Aggiungere un parametro dello stream si è visto nella sezione 3.3: una riga di limiti e una specifica. Per le finestre del grano vale lo stesso criterio della sintassi di Csound (sezione 3.4). Il catalogo descrive una finestra *nei suoi termini* (forma, coefficienti, parametri, simmetria) senza nominare routine Csound né funzioni NumPy, e due traduttori ne ricavano la materializzazione: uno per Csound, che produce una tabella con una routine GEN, e uno per NumPy, che produce un array. SuperCollider riceve gli array del traduttore NumPy e li carica come buffer. Le forme sono meno delle finestre: Hamming, Hann, Blackman e Blackman-Harris sono quattro insiemi di coefficienti della stessa forma parametrica, la somma di coseni, e aggiungerne una quinta è una riga nel catalogo e nessuna nei traduttori.

La ragione è un difetto reale delle versioni precedenti. Il catalogo diceva *come Csound produce* una finestra e il renderer NumPy la reimplementava da zero, con i nomi in comune e le forme no: `triangle` passava la validazione dello YAML ed esplodeva a metà rendering solo con NumPy. Oggi una finestra entra nel catalogo soltanto se ogni traduttore sa produrla, un test lo richiede, e la copertura è dichiarata e non scoperta durante il rendering.

### Le strategie e il registro

Molti comportamenti sono scelte intercambiabili, selezionate per nome nello YAML: come le voci distribuiscono le altezze (`step`, `chord`, `spectral`), come si spostano nel tempo (`linear`, `geometric`, `stochastic`), come si dispongono nel pan, come si seleziona la finestra, come si applica la variazione stocastica. Ciascuna è una *strategia*, una classe che implementa un'interfaccia comune, e per ciascuna famiglia c'è un registro dal nome alla classe:

```python
VOICE_ONSET_STRATEGIES = StrategyRegistry('voice_onset', VoiceOnsetStrategy, {
    'linear':      LinearOnsetStrategy,
    'geometric':   GeometricOnsetStrategy,
    'stochastic':  StochasticOnsetStrategy,
})
```

Il meccanismo era ripetuto in nove moduli e le copie divergevano nei nomi dei parametri e nelle etichette. Oggi è una classe sola, `StrategyRegistry`, che eredita da `dict` ed è la mappa stessa: le fixture dei test ne fanno uno snapshot, e il language server ne legge le chiavi importandola per nome. La sua operazione essenziale è la costruzione per nome:

```python
def create(self, name: str, *args, **kwargs) -> S:
    if name not in self:
        raise StrategyNotFoundError(
            strategy_kind=self.kind,
            name=name,
            available=list(self.keys()),
        )
    return self[name](*args, **kwargs)
```

Otto famiglie la usano: altezza, onset, puntatore e pan delle voci, selezione della finestra, clip del grano, densità e variazione. Per aggiungere una strategia basta scrivere la classe e registrarla con un nome; lo YAML la riconosce subito, e un nome inesistente produce un errore che elenca i nomi disponibili.

### Gli errori

Gli errori seguono la stessa logica. Derivano tutti da una radice, `EngineError`, e portano il contesto utile a chi compone (lo stream in cui sono avvenuti, il campo, un suggerimento), così un errore del compositore, come un campo mancante o un file di campioni assente, si distingue da un difetto del programma. Gli errori di configurazione ereditano anche il tipo che sostituiscono: `ConfigFileNotFoundError` è anche un `FileNotFoundError`, e chi catturava l'eccezione di Python continua a catturarla.

## Riproducibilità e verifica

Una composizione generata con elementi casuali ha senso solo se può essere riprodotta. PGE tratta la riproducibilità come un requisito di progetto: la specifica con il seme dichiarato è il documento che si versiona e si invia a chi deve leggerla, e l'audio si rigenera da essa. Per questo il `Generator` non lascia che nessun componente peschi da un generatore casuale globale. Ogni sito stocastico (la variazione di un parametro, il gate di probabilità, l'intervallo asincrono fra i grani, la selezione della finestra) ottiene un proprio generatore, derivato dal seme, dall'identità dello stream e dal nome del componente (`shared/seeding.py`):

```python
def component_rng(seed, stream_id: str, component: str):
    if seed is None:
        return random
    digest = hashlib.sha256(
        f"{seed}:{stream_id}:{component}".encode()
    ).hexdigest()
    return random.Random(int(digest, 16))
```

La derivazione usa SHA-256 e non la funzione `hash()` di Python, perché `hash()` su una stringa cambia da un processo all'altro, e la riproducibilità fra una sessione e la successiva andrebbe perduta. Uno stream può condividere la sequenza di un altro dichiarando un gruppo comune (`rng_group`, capitolo 4). Se lo YAML non dichiara un seme, il `Generator` ne ricava uno dall'orologio, lo stampa (`[SEED] … aggiungi 'seed: N' allo YAML`) e il brano resta ricostruibile a posteriori.

Il risultato si verifica con lo script `lazy_e_riproducibilita.py`. Per un brano di tre stream con il seme dichiarato, i grani sono gli stessi in tre processi con `PYTHONHASHSEED` diverso (la stessa impronta SHA-256 su 662 grani), non cambiano se gli stream si generano in ordine inverso né se un altro stream è in mute, e cambiano con un altro seme. Sono le condizioni da cui dipendono la generazione lazy (sezione 3.1) e la cache per stream: lo stem di uno stream non dipende da quali altri stream sono puliti in quel rendering.

La casualità sta tutta nella generazione: i renderer sono funzioni pure della lista dei grani e non estraggono numeri casuali. Ne seguono due conseguenze. Il parallelismo del renderer NumPy distribuisce soltanto la somma dei grani nel buffer, un'operazione senza stato (le sue garanzie sono nel capitolo 7). E il confronto fra renderer è un controllo: due renderer che ricevono lo stesso YAML con lo stesso seme ricevono la stessa lista, e se i loro file differiscono la differenza sta nel DSP (interpolazione, quantizzazione, precisione delle tabelle) e mai in una scelta casuale (capitolo 7).

Il progetto è sviluppato con test in modo sistematico: test unitari (`make tests`) e test di integrazione sull'intera catena, `make e2e-tests`, per ciascuno dei tre renderer. Ne parla il capitolo 9.

## Che cosa il disegno lascia aperto

Quattro punti dell'architettura non sono risolti, e conviene dirlo perché ciascuno è il rovescio di una scelta descritta sopra. I primi due sono registrati nella documentazione di PGE; gli altri due emergono dalla lettura del codice fatta per questa tesina.

Il primo è la taglia di `Stream`. Con oltre 1 100 righe è il secondo modulo del pacchetto per lunghezza, e coordina una ventina di moduli. La documentazione di PGE (`docs/explanation/stream-decomposition.md`) registra la decisione di *non* scomporlo nei cinque mestieri che vi si riconoscono (validazione, normalizzazione delle unità, collegamento dei collaboratori, generazione, vista di lettura). La ragione è il criterio con cui si decide un confine di modulo: vale la pena quando è stretto, con pochi ingressi e uscite restituite invece che scritte. Quattro mestieri su cinque hanno un solo chiamante e, per la generazione e per il collegamento dei collaboratori, un modulo separato avrebbe avuto in ingresso lo `Stream` intero: il codice si sarebbe spostato senza che cambiasse l'accoppiamento. La sola cucitura decisa, il blocco `voices:` che passerà al suo controller, non è ancora eseguita. Il costo del resto è accettato: ogni chiave nuova del blocco `grain:` continuerà ad atterrare in quel file.

Il secondo è un accoppiamento nel tempo. Il `Generator` assegna a ogni stream `sample_table_num` e `window_table_map` *dopo* la costruzione, e il costruttore non dichiara il secondo. Uno `Stream` costruito da solo è perciò un oggetto a metà: si costruisce senza errori e fallisce al primo accesso a `.voices`, per la ragione detta nella sezione 3.1. La generazione lazy sposta l'errore dal costruttore al primo accesso.

Il terzo è un residuo storico. Il `Generator` importa `FtableManager` e `ScoreWriter` dal pacchetto `rendering` e custodisce uno `ScoreWriter` Csound, con il metodo `generate_score_file`. Il confine della sezione 3.4 è dunque completo per `Grain` e per `Stream` e non per il `Generator`, che conserva la memoria di quando il motore produceva soltanto uno score.

Il quarto è il numero di canali. Il grano ha un pan in gradi, che non impone il numero di canali di uscita, ma i tre renderer producono oggi file stereofonici: la generalità sta nel dato e non ancora nei consumatori.


# Il linguaggio di descrizione degli stream

Il capitolo precedente ha collocato il linguaggio nell'architettura: è l'ingresso della pipeline, e il motore lo traduce in una lista di grani. Questo ne descrive la grammatica. Dice che forma ha un documento, che forme può assumere un valore e quali due proprietà valgono per il documento intero, il seme e l'importazione di stream da altri file. Il vocabolario, cioè che cosa governa ciascuna chiave, è l'argomento dei capitoli 5 e 6. Il capitolo segue la costruzione: lo stream e i suoi valori predefiniti (sezione 4.1); le forme di un valore, in ordine di ricchezza, cioè l'espressione (4.2), l'envelope (4.3) e la banda di variazione (4.4); poi il seme (4.5) e lo stream come file (4.6). L'ultima sezione raccoglie ciò che il linguaggio lascia passare senza avvertire.

Non è un manuale: la sintassi completa è nel riferimento del progetto (`docs/reference/yaml.md`). Gli esempi vengono dal paper presentato al XXV CIM [@DeMattia2026Cim] e si rieseguono dalla cartella `esempi/`; le affermazioni sul comportamento del motore sono controllate, una per una, dallo script `esempi/linguaggio/verifica_linguaggio.py`.

La scelta di YAML ha tre ragioni e un costo. Le ragioni sono quelle del progetto. Un file di testo si versiona con *git* e può essere letto e discusso con un modello linguistico. Il motore, esposto come libreria, può essere pilotato da un livello compositivo più alto che generi YAML invece di scriverlo a mano, come fa il laboratorio del capitolo 10. E la specifica dichiara soltanto la generazione dei grani, separata dal rendering. Il costo è che la sintassi è permissiva: il motore ricava i tipi dal testo, e ciò che non riconosce lo lascia passare. Il capitolo lo dichiara dove si presenta.

## Lo stream come unità compositiva

Un brano è un file YAML. Al livello più alto il motore legge due chiavi: `streams`, l'elenco degli stream, e, facoltativamente, `seed`, il seme dei processi casuali. Ogni altra chiave di primo livello, come il `composition` degli esempi o un `bpm`, il motore la ignora. Ogni stream è un dizionario di coppie chiave-valore, annidabili. A livello dello stream stanno la densità (`density` o `fill_factor`), `distribution`, `volume` e `pan`; gli altri parametri sono raggruppati in blocchi che corrispondono ai concetti dei capitoli seguenti: `grain` per il grano, `pointer` per la posizione di lettura, `pitch` per la trasposizione, `voices` per la molteplicità delle voci.

### Le condizioni minime di esistenza

Uno stream esiste con due soli parametri.

```yaml
streams:
  - stream_id: esempio1
    sample: voice.wav
```

`stream_id` è il nome dello stream, e `sample` è il file audio da granulare. Se ne manca uno il motore si ferma con un `MissingFieldError` che lo nomina. Tutto il resto è facoltativo, perché ogni chiave ha un valore predefinito, e i predefiniti sono scelti perché questa configurazione sia la trasformazione identica della sorgente.

| Chiave | Predefinito | Effetto |
|--------------------------|----------------|------------------------------------------|
| `grain.duration` | 0,05 s | grani di 50 ms |
| `fill_factor` | 2 | densità di 40 grani al secondo: un grano ogni 25 ms |
| `grain.envelope` | `hanning` | finestra di Hann |
| `volume`, `pan` | 0 dB, 0 gradi | grano centrale a guadagno 1 |
| `pointer.speed_ratio` | 1 | la lettura avanza alla velocità del tempo dello stream |
| `pitch` | rapporto 1 | nessuna trasposizione |

Con questi valori l'identità è una questione di aritmetica. Due finestre di Hann sfalsate di metà della loro durata sommano a 1: sul file di esempio, a 44,1 kHz, la somma delle finestre dei 78 grani sta fra 0,9986 e 1, salvo ai due estremi, dove copre l'istante un grano solo. Ogni grano legge il file nel punto in cui è nato, perché la posizione di lettura coincide con l'istante. La somma dei grani ricostruisce dunque la sorgente. È l'identità della lista dei grani, e non del file di uscita: il rendering NumPy a 44,1 kHz restituisce la sorgente con un guadagno di 0,70, perché il pan a potenza costante del capitolo 7 porta un grano centrale a $1/\sqrt{2}$ in ciascun canale, e con un residuo di $-21$ dB, che deriva dall'interpolazione lineare delle posizioni di lettura a mezzo campione.

La figura seguente mostra la MAP di questo caso. Ogni grano è un poligono posizionato sul tempo dello stream (asse orizzontale) e sulla posizione di lettura nel file (asse verticale). A sinistra, sullo stesso asse verticale, è disegnata la forma d'onda della sorgente. La diagonale è l'identità. La lente ingrandisce tre grani contigui, in cui si vedono il profilo della finestra e la sovrapposizione fra grani adiacenti.

![MAP dello stream minimo: il puntatore percorre il file una sola volta, alla velocità del tempo dello stream.](docs/images/identity_map.pdf){width=100%}

### Una notazione differenziale

Ciò che non è scritto è una dichiarazione implicita, data dal valore predefinito del parametro. Il caso più visibile è la coppia `onset` e `duration`.

| Chiave | Se assente | Se dichiarata |
|--------|------------|---------------|
| `onset` | lo stream parte a 0 s, l'origine della timeline | lo stream parte all'istante indicato, in secondi assoluti |
| `duration` | lo stream dura quanto il campione | lo stream dura il tempo indicato, anche più o meno del file |

Il motore distingue «assente» da «dichiarata» con un predicato che guarda `None` e non la verità del valore (`core/stream_config.py`):

```python
def stream_duration_is_implicit(yaml_data: dict) -> bool:
    return yaml_data.get('duration') is None

def resolve_stream_duration(yaml_data: dict, sample_dur_sec: float) -> float:
    if stream_duration_is_implicit(yaml_data):
        return sample_dur_sec
    return yaml_data['duration']
```

`onset` ha il gemello `resolve_stream_onset`, con la costante 0.0 al posto della durata del file. Ne seguono due conseguenze. `duration: null` vale come chiave assente, e `duration: 0` no: è una dichiarazione, degenere, e produce uno stream senza grani.

La scelta ha una ragione espressa nel progetto: a riposo lo stream risintetizza il campione, e l'unica durata non arbitraria è quella del file. Ogni altro valore è una decisione compositiva, e le decisioni compositive devono essere esplicite. Zero non è «niente», è l'origine: uno stream senza `onset` ha una posizione neutra, non indeterminata. Il costo di questa comodità è dichiarato. Un `onset` cancellato per errore non produce un errore: lo stream si impila silenziosamente a zero. Per `duration` vale lo stesso.

Due chiavi governano la presenza dello stream nel render: `mute` lo esclude, `solo` esclude tutti gli altri. La regola è una funzione di poche righe (`filter_solo_mute`, in `engine/solo_mute.py`) e conta la presenza della chiave, non il suo valore:

```python
solo_mode = any('solo' in s for s in stream_data_list)

if solo_mode:
    filtered = [s for s in stream_data_list if 'solo' in s]
else:
    filtered = [s for s in stream_data_list if 'mute' not in s]
```

Perciò `mute: false` muta lo stream, e `solo: false` attiva la modalità solo: per togliere un flag si cancella la riga. Se più stream dichiarano `solo` suonano tutti, e `solo` prevale su `mute`.

## Espressioni matematiche

Un valore racchiuso tra parentesi è un'espressione.

```yaml
grain:
  duration: (1/20)
pitch:
  ratio: (2**(7/12))        # il rapporto di sette semitoni
```

Il motore la valuta alla lettura del file, prima che il resto del programma veda il dato, e il risultato è un numero fisso: l'espressione non è modulabile nel tempo, e a questo serve l'envelope. La valutazione è una sostituzione di testo applicata a ogni valore stringa del documento (`Generator._eval_math_expressions`):

```python
pattern = r'\(([a-zA-Z0-9+\-*/.() ]+)\)'
...
safe_dict = {
    'abs': abs,
    'int': int,
    'float': float,
    'min': min,
    'max': max,
    'pow': pow,
    'pi': math.pi,
    'e': math.e
}
...
result = eval(expr, {"__builtins__": {}}, safe_dict)
```

Un frammento fra parentesi fatto soltanto di cifre, lettere, operatori, punto e spazi si calcola con `eval` in un ambiente senza i `builtins` di Python e con i soli nomi di `safe_dict`; il risultato prende il posto del frammento, e se l'intera stringa diventa un numero il valore è un numero. Il meccanismo ha tre limiti. Il pattern non contiene la virgola, quindi `min`, `max` e `pow`, che vogliono due argomenti, sono nella lista ma non si possono chiamare: restano `abs`, `int`, `float`, le costanti `pi` ed `e` e gli operatori `+ - * / // **`, non il resto della divisione. Un'espressione che non si calcola, poi, non è un errore: il motore stampa un avviso e lascia la stringa com'è. Infine la sostituzione non distingue un valore numerico da un nome, e un file chiamato `voice (1).wav` diventa `voice 1.wav`.

## Envelope: forme, interpolazioni e time mode

Un *envelope* è una funzione del tempo definita a tratti su punti di controllo (*breakpoint*), ciascuno una coppia `[tempo, valore]`. Può comparire al posto di qualunque valore numerico, ed è così che i parametri di uno stream variano nel tempo. Il motore riconosce un inviluppo dalla forma del dato (`Envelope.is_envelope_like`): una lista che contiene almeno una coppia, un dizionario con la chiave `points`, o uno dei formati compatti descritti sotto.

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

Il primo elemento è il pattern di un ciclo, con le ascisse espresse da 0 a 100. Il secondo è il tempo assoluto finale del blocco, il terzo il numero di ripetizioni. In questo esempio la durata del grano sale da 0,01 a 0,2 secondi quattro volte, in cicli di 7,5 secondi, fino al secondo 30; fra un ciclo e il successivo il motore inserisce un salto di un microsecondo, perché due punti non cadano sullo stesso istante. Il formato compatto accetta anche l'interpolazione, una distribuzione non uniforme delle durate dei cicli e l'opzione di chiudere il ciclo, e può essere mescolato con punti ordinari nella stessa lista.

### Le interpolazioni

Le interpolazioni sono tre.

- **Lineare** (predefinita): i valori fra due punti sono su una retta. L'integrale è l'area di un trapezio.
- **Cubica**: curva di Hermite con tangenti scelte perché la curva sia monotona, secondo il metodo che il codice attribuisce a Fritsch e Carlson. In un punto interno la tangente è la media armonica delle pendenze dei due segmenti adiacenti, e vale zero se le pendenze cambiano segno o una è nulla; per questo, fra due punti, la curva non esce dall'intervallo dei loro valori, e nel profilo `[0, 5], [10, 40], [30, 5]` il massimo resta 40. Con due soli punti l'unica informazione è la pendenza, e assegnarla a entrambe le tangenti darebbe una retta: le tangenti sono forzate a zero e la curva diventa una S simmetrica, $v_0 + (v_1 - v_0)(3s^2 - 2s^3)$. La cubica è adatta ad attacchi e rilasci morbidi e a traiettorie dove una derivata seconda continua è udibile. L'integrale è calcolato con la regola di Simpson su dieci sotto-intervalli per segmento.
- **A gradini** (*step*): il valore di un segmento è quello del punto di sinistra fino al punto successivo. Serve ai cambi discontinui e ai parametri che assumono valori interi, come il numero di voci.

Per la cubica il calcolo delle tangenti, nel modulo `envelope.py`, è questo:

```python
if n == 2:
    return [0.0, 0.0]
...
if d_left * d_right <= 0:
    tangents[i] = 0.0
else:
    tangents[i] = 2.0 / (1.0 / d_left + 1.0 / d_right)
```

### Il tempo: assoluto e normalizzato

Il tempo di un inviluppo si misura in due modi. Con `time_mode: absolute` (il caso predefinito) i punti sono secondi: `[10, 40]` significa «al secondo 10 il valore è 40», qualunque sia la durata dello stream. Con `time_mode: normalized` l'ascissa va da 0 a 1 ed è moltiplicata per la durata dello stream, alla costruzione dell'inviluppo (`create_scaled_envelope`). Un envelope scritto in forma normalizzata mantiene la propria forma se si cambia la durata del brano. `time_mode` si dichiara per tutto lo stream; per un solo inviluppo si scrive, nel suo dizionario, la chiave `time_unit`. Un `time_mode` scritto nel dizionario di un parametro come `density` non ha effetto, e il motore non avverte.

La normalizzazione riguarda l'asse del tempo degli inviluppi. La posizione dello stream nella timeline, `onset`, è sempre in secondi assoluti.

### Il comportamento ai bordi

Fuori dall'intervallo coperto dai punti, l'inviluppo mantiene il valore del punto più vicino: prima del primo punto vale il primo valore, dopo l'ultimo vale l'ultimo. Lo dice il codice del segmento (`NormalSegment.evaluate`), e vale anche per l'integrale:

```python
if t < self.start_time:
    return self.breakpoints[0][1]

if t > self.end_time:
    return self.breakpoints[-1][1]

return self.strategy.evaluate(t, self.breakpoints, **self.context)
```

Uno stream più lungo del suo inviluppo non produce quindi errori. È una scelta voluta, e si legge nella figura seguente.

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

Con `duration: 7.0` e tempo normalizzato i punti cadono a 0,7, 1,05, 2,1 e 3,5 secondi. Il campione dura 1,985 secondi, circa due, ma lo stream ne dura sette.

![MAP dell'esempio. In basso l'inviluppo `speed_ratio`, con i valori annotati sui punti; in alto i grani.](docs/images/pointer_map.pdf){width=100%}

La figura mostra che i grani non ricalcano la curva di `speed_ratio`: ne seguono l'*accumulo*. La posizione di lettura è l'integrale della velocità istantanea, e il puntatore chiede all'envelope la seconda delle sue due operazioni, `integrate` invece di `evaluate` (`PointerController._calculate_linear_position`):

```python
internal_val = self.speed_ratio.value
if isinstance(internal_val, Envelope):
    sample_position = internal_val.integrate(0, elapsed_time)
else:
    sample_position = elapsed_time * float(internal_val)
return self.start + sample_position
```

L'indice di lettura è poi preso modulo la durata del file. Con la velocità che sale a 2,6 il puntatore esaurisce il buffer a 1,35 secondi e rientra da zero: il salto che si vede nella MAP è una discontinuità di posizione, non il ritorno a zero di una fase che continua ad accumularsi. Fra circa 2 e 3,5 secondi la velocità è negativa e il puntatore percorre il file all'indietro. Il verso di lettura interno ai grani si inverte con lui, perché per impostazione predefinita un grano è invertito quando la testina va indietro (`Stream._calculate_grain_reverse`, nel ramo `auto` di `grain.reverse`):

```python
if self.grain_reverse_mode == 'auto':
    is_reverse_base = (self._pointer.get_speed(elapsed_time) < 0)
```

Dopo l'ultimo punto la velocità resta a zero, per il comportamento ai bordi, e da 3,5 secondi tutti i grani leggono lo stesso punto del file, a 0,342 secondi: la posizione si congela.

## La banda di variazione

Cinque parametri dello stream hanno una banda di variazione, dichiarata da una chiave con `range` nel nome: `volume_range`, `pan_range`, `grain.duration_range`, `pointer.offset_range` e `pitch.range`. La banda sta attorno al valore base, e per ogni grano il motore estrae il valore del parametro dentro di essa.

```yaml
grain:
  duration: 0.05
  duration_range: 0.01
```

Il linguaggio distingue quattro concetti, ognuno con la propria chiave, perché tenerli distinti evita ambiguità. La *larghezza* della banda è il valore stesso di `_range`: è sempre la larghezza, mai una semi-ampiezza e mai una deviazione standard. L'*unità* in cui è misurata la larghezza è assoluta, nell'unità del parametro, oppure relativa al valore base. Si sceglie con `grain.duration_range_unit`, e solo per la durata del grano, l'unico parametro la cui base spazia per costruzione su più ordini di grandezza, da un campione a dieci secondi, e per cui una banda assoluta cambierebbe carattere da sola lungo un envelope. La *forma* (`distribution_mode`) dice come la banda viene riempita: uniforme oppure gaussiana. L'*ancora* (`range_anchor`) dice dove cade il valore base nella banda: al centro oppure al minimo. Forma e ancora sono chiavi dello stream e valgono per tutte le sue bande.

Con valore base 300 e larghezza 200 le combinazioni danno questi risultati.

| Forma | Ancora | Banda | Dove si addensano i valori |
|-------|--------|-------|----------------------------|
| uniforme | centro | da 200 a 400 | in modo piatto |
| uniforme | minimo | da 300 a 500 | in modo piatto |
| gaussiana | centro | da 200 a 400 | attorno a 300 |
| gaussiana | minimo | da 300 a 500 | attorno a 400 |

Le due forme stanno in due classi (`shared/distribution_strategy.py`). L'ancora sceglie la banda, e la forma ne estrae il valore. Per la distribuzione uniforme con ancora al centro l'estrazione è la riga che il capitolo 5 scrive come formula, $v = c + \xi\rho$ con $\xi$ fra $-1/2$ e $1/2$:

```python
def _band(self, center: float, spread: float) -> Tuple[float, float]:
    if self._anchor == ANCHOR_MIN:
        return (center, center + spread)
    half_spread = spread / 2
    return (center - half_spread, center + half_spread)
```

```python
return center + self._rng.uniform(-0.5, 0.5) * spread
```

La gaussiana è troncata:

```python
lo, hi = self._band(center, spread)
mu = (lo + hi) / 2.0
sigma = spread / self.SIGMA_DIVISOR

return min(max(self._rng.gauss(mu, sigma), lo), hi)
```

`SIGMA_DIVISOR` vale 6, dunque la deviazione standard è un sesto della larghezza e i bordi della banda cadono a tre sigma dalla media. La piccola coda che li supererebbe, circa lo 0,27% dei valori, è appiattita sull'estremo. Nessun valore esce dalla banda dichiarata.

Centro e larghezza sono due valori come tutti gli altri, e ciascuno può essere un numero o un envelope. Quando lo sono entrambi la banda è un'area che si apre e si chiude nel tempo: è la maschera di tendenza, nella forma in cui la descrive Truax [@Truax1988, p. 17], scritta in testo.

```yaml
grain:
  duration: [[0, 0.02], [10, 0.2]]
  duration_range: [[0, 0.0], [10, 0.1]]
```

Qui la durata del grano sale da 20 a 200 millisecondi in dieci secondi e la banda si apre da zero a 100 millisecondi: ogni grano cade dentro una semi-banda che cresce di 5 millisecondi per secondo. La sezione 3.3 descrive come `Parameter.get_value` compone centro, banda, gate di probabilità e limite; il capitolo 5 dice come la probabilità che la deviazione si applichi sia un asse indipendente dall'ampiezza.

## Riproducibilità: seme e gruppi

Il seme è una chiave del livello più alto del file.

```yaml
seed: 2026
streams:
  - stream_id: s1
    sample: voice.wav
```

Se è dichiarato, lo stesso YAML produce la stessa lista di grani a ogni esecuzione, anche in processi diversi, e quindi la stessa realizzazione. Se è assente, il motore genera un seme di sessione dall'istante di avvio e lo riporta a schermo: il render non è riproducibile in anticipo, ma resta ricostruibile a posteriori, perché aggiungendo `seed: N` al file si riottiene lo stesso risultato. Anche `seed: 0` è un valore valido, distinto dall'assenza della chiave.

Il seme non alimenta un generatore globale. Ogni sito stocastico ha il proprio generatore, derivato dal seme, dall'identità dello stream e dal nome del componente (sezione 3.7). Il risultato più utile per chi compone è l'isolamento. Mettere uno stream in `solo` fa ascoltare esattamente ciò che suona nel mix, perché i grani degli altri stream non vengono toccati. Modificare uno stream lascia intatti i grani di tutti gli altri. Anche le voci stocastiche hanno un generatore proprio, derivato dal seme, dallo stream e dall'indice della voce.

L'identità del generatore è per impostazione predefinita lo `stream_id`, quindi due stream non pescano mai la stessa sequenza, nemmeno con lo stesso seme. La chiave `rng_group` sostituisce lo `stream_id` in questa derivazione: gli stream che dichiarano lo stesso gruppo condividono le sequenze casuali di tutti i componenti.

```yaml
seed: 1988
streams:
  - stream_id: cugini_1
    sample: voice.wav
    rng_group: cugini
  - stream_id: cugini_2
    sample: voice.wav
    rng_group: cugini
```

Questo serve quando più stream vanno letti come un unico oggetto, per esempio più stream distribuiti su posizione e pan con la stessa griglia stocastica. Due stream identici con lo stesso gruppo hanno grani identici, e con `stream_id` diversi e senza gruppo hanno grani diversi. Condividere la sequenza non significa condividere la griglia temporale: gli intervalli fra onset dipendono anche dalla densità, e con densità diverse i due stream si sfasano subito pur pescando dalla stessa sequenza.

Il seme governa la generazione e non il rendering. I tre renderer ricevono la stessa lista di grani e nessuno estrae numeri casuali (sezione 3.7): se due file audio dello stesso brano non sono uguali bit per bit, la differenza sta nell'elaborazione del segnale e non in una scelta del caso.

## Stream come file

Questa sezione descrive il ramo principale del motore: `file:` è successivo alla versione 9.1.0 descritta nel capitolo 3, e non è ancora in una versione rilasciata.

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

La divisione dei compiti segue una regola: ogni chiave ha una sola casa. Accanto a `file:` il master può tenere soltanto il piazzamento, cioè `stream_id`, `onset`, `mute` e `solo`; qualsiasi altra chiave è un errore che nomina il master, la voce e la chiave. Del file importato si legge lo stream, senza le sue chiavi di piazzamento (`engine/stream_files.py`):

```python
CHIAVI_DI_PIAZZAMENTO = ('stream_id', 'onset', 'mute', 'solo')
estranee = [k for k in voce
            if k != 'file' and k not in CHIAVI_DI_PIAZZAMENTO]
if estranee:
    raise StreamFileKeyError(origine, estranee, CHIAVI_DI_PIAZZAMENTO)
risolto = {k: v for k, v in stream.items()
           if k not in CHIAVI_DI_PIAZZAMENTO}
piazzamento = {k: voce[k] for k in CHIAVI_DI_PIAZZAMENTO
               if k in voce}
if piazzamento.get('stream_id') is None:
    piazzamento['stream_id'] = os.path.splitext(
        os.path.basename(voce['file']))[0]
risolti.append({**piazzamento, **risolto})
```

Il laboratorio può scrivere `onset: 0` e un proprio `stream_id` perché il file si renda da solo, ma nel brano le decisioni di piazzamento sono del master. Se il master non scrive uno `stream_id`, vale il nome del file senza estensione: nell'esempio `risacca`, che coincide con quello del laboratorio. Il percorso è relativo alla cartella del master, mentre il `sample` si cerca come per ogni altro stream, nella cartella dei campioni. Un file importato contiene un solo stream e non può a sua volta importarne altri, quindi non esistono catene né cicli.

L'importazione è la prima cosa che il motore fa dopo aver letto il master, e le espressioni matematiche valgono sullo stream importato come su quello scritto nel master (`Generator.load_yaml`):

```python
raw_data = self._read_document(self.yaml_path)
raw_data, importati = resolve_stream_files(
    raw_data, self.yaml_path, self._read_document)
self.data = self._eval_math_expressions(raw_data)
```

Da lì in poi il motore vede una lista di stream come se fossero stati scritti nel master. La cache degli stem lo tratta di conseguenza: il suo fingerprint è quello dello stream risolto, quindi spostare uno stream dal master a un file non lo rende da rifare, e modificare il file importato rifà quello stream e nessun altro.

Resta da chiarire cosa succede al suono. Il seme è uno solo, quello del master: se il file importato ne dichiara uno diverso, il render procede con quello del master e il motore avvisa su stderr. Dal momento che il generatore di ogni componente deriva da seme e identità, uno stream importato suona come nel laboratorio solo con lo stesso seme e lo stesso `stream_id`. Uno `stream_id` diverso dà un'altra realizzazione dello stesso stream, ed è accettato: succede di default quando il laboratorio scrive un identificatore diverso dal nome del file. Chi vuole la realizzazione del laboratorio scrive quell'identificatore accanto a `file:`, oppure dichiara nel file un `rng_group`, che non dipende dal nome con cui il master chiama lo stream. Importare due volte lo stesso file richiede due `stream_id` diversi, e dà due realizzazioni distinte; senza, è un errore, perché i due stem avrebbero lo stesso nome.

Il meccanismo permette di lavorare per parti. Ogni stream è sviluppato e ascoltato nel proprio file, e il brano si assembla in un master che li dispone nel tempo e decide quali far suonare.

## Che cosa il linguaggio lascia passare

Il linguaggio è permissivo: la notazione differenziale rende comoda la scrittura e paga il prezzo di non protestare davanti a ciò che non riconosce. Le sezioni precedenti ne hanno incontrato i casi, che qui si raccolgono.

| Si scrive | Il motore |
|----------------------------------------------|----------------------------------------|
| un `onset` o una `duration` cancellati | usa l'origine della timeline e la durata del file |
| `mute: false` | muta lo stream |
| una chiave che non conosce (`desnity`, `grain: {duraton: 0.2}`, un `bpm` in testa al file) | la ignora, senza avviso |
| `time_mode: normalised` | lo legge come `absolute`, senza avviso |
| `time_mode` nel dizionario di `density` | lo ignora, senza avviso |
| un'espressione che non si calcola | stampa un avviso e lascia la stringa |
| `distribution_mode: gausian`, `range_anchor: max`, `density: -5` | si ferma con un errore |

Il confine fra i due comportamenti passa per ciascuna chiave: un valore sbagliato di `distribution_mode` o `range_anchor` è un errore, uno di `time_mode` no, e un numero fuori dai limiti del parametro è un errore alla costruzione dello stream, prima di ogni grano (sezione 3.1). Il motore non conosce, quando legge, l'insieme delle chiavi valide, e chi scrive a mano ha due guardie fuori da lui: il completamento delle chiavi del language server (capitolo 9) e la MAP, che a rendering fatto mostra ciò che è uscito davvero (capitolo 8). Una chiave scritta male si riconosce nella MAP perché l'effetto atteso non c'è.


# Il grano e lo stream

Il capitolo precedente ha descritto la grammatica con cui si dichiara uno stream. Questo ne descrive il vocabolario: che cosa governa ciascuna parte della dichiarazione e come il motore la traduce in un campo del grano. Il metodo è quello del paper presentato al XXV CIM [@DeMattia2026Cim], che espone PGE per scostamenti: si parte dallo stream minimo del capitolo 4, la trasformazione identica della sorgente, e ci si scosta da esso un parametro alla volta. Per ciascuno si mostra un esempio che lo isola e la MAP che il motore ne ricava. Gli esempi, per non disturbare ciò che isolano, spesso fermano la lettura (`speed_ratio: 0`), così che la MAP mostri una sola variabile. I listati stanno nella cartella `esempi/` del repository della tesina, uno per cartella (`esempi/<nome>/<nome>.yml`), e le MAP si rigenerano da quei file. Le affermazioni sul comportamento del motore sono controllate, una per una, dallo script `esempi/grano/verifica_grano.py`.

L'ordine è quello del paper: dove il grano legge, cioè il puntatore; quando è emesso, cioè la griglia; che cosa è, cioè la sua durata, la finestra, l'altezza, il verso, il volume e la posizione nel campo; e quanto ne decide il caso. La tabella associa a ciascun campo del grano, il tipo descritto nel capitolo 3, la parte del linguaggio che lo determina.

| Campo del grano | Da che cosa dipende |
|-----------------|---------------------------------------------------|
| `pointer_pos` | il blocco `pointer` |
| `onset` | `density` o `fill_factor`, e `distribution` |
| `duration` | `grain.duration` |
| `envelope_table` | `grain.envelope` |
| `pitch_ratio` | il blocco `pitch`; il suo segno porta il verso di lettura, che dipende da `grain.read_direction` e `grain.reverse` |
| `volume`, `pan` | `volume`, in decibel, e `pan`, in gradi |
| `sample_table` | `sample` |

## Il puntatore

Il blocco `pointer` risponde a una domanda: da dove legge questo grano? La risposta è una posizione in secondi nel file, il campo `pointer_pos`, e il motore la compone in quattro passi (`controllers/pointer_controller.py`):

```python
linear_pos = self._calculate_linear_position(elapsed_time)
...
if grain_reverse:
    final_pos += grain_duration
rel = (final_pos - window_start) % window_length
return (window_start + rel) % self._sample_dur_sec
```

Il primo è la posizione lineare: `start` più l'integrale di `speed_ratio`, come ha mostrato il capitolo 4. `start` è un valore fisso, e un inviluppo è un errore che il motore nomina; se manca vale 0, oppure `loop_start`, quando c'è un loop. `speed_ratio` vale 1 per la velocità naturale, 0 per fermare la testina, un numero negativo per percorrere il file all'indietro, e sta fra $-100$ e 100. Il secondo passo applica il loop, se c'è. Il terzo somma alla posizione la deviazione di ciascun grano, scalata sulla lunghezza della finestra attiva (`dev_normalized * window_length`), lo scarto della voce (capitolo 6) e, per un grano letto all'indietro, la sua durata, di cui si dirà nella sezione sul verso. Il quarto è l'operazione modulare: riporta la posizione dentro la finestra e poi dentro il file, perciò la testina che arriva in fondo ricomincia dall'inizio.

### Il loop

Il puntatore può essere confinato in una finestra del file, il *loop*. Lo accende la presenza di `loop_start`; la fine si dichiara in due modi alternativi, con `loop_end`, un istante, o con `loop_dur`, una durata, e se compaiono entrambi vince `loop_end`. Senza `loop_start` il loop non esiste e le altre due chiavi sono ignorate, senza avviso. Se `loop_start` e `loop_end` sono numeri, un `loop_end` minore o uguale a `loop_start` è un errore, perché un loop a cavallo della fine del file si esprime soltanto con `loop_dur`: la finestra riprende dall'inizio. L'inizio e la fine accettano inviluppi, e la finestra può dunque muoversi nel file.

La chiave `loop_unit` fissa l'unità di tutte le posizioni nel file: secondi (il caso predefinito) oppure valori normalizzati fra 0 e 1, scalati sulla durata del campione. Le chiavi che interpreta sono quattro, `start`, `loop_start`, `loop_end` e `loop_dur`, e `start` ne fa parte benché non sia del loop: è una posizione nel file come le altre. L'unità è indipendente dal modo in cui si misura il tempo degli inviluppi: sono due assi diversi, quello del tempo dello stream e quello della posizione nel file.

Come la testina entra nel loop dipende dalla finestra (`_apply_loop`, nel puntatore):

```python
if self._loop_is_dynamic:
    entry_pos = current_loop_start
else:
    check_pos = linear_pos % self._sample_dur_sec
    if current_loop_start <= check_pos < current_loop_end:
        entry_pos = check_pos
```

Una finestra è dinamica quando `loop_start` è un inviluppo, e allora la testina nasce dentro, a `loop_start(0)`. Una finestra statica non cattura nessuno finché non la si incontra: la testina corre libera sul file intero, e solo quando la sua posizione lineare entra nella finestra vi resta. Se `start` è omesso la testina parte dall'inizio della finestra, e l'ingresso è immediato. Dentro il loop la posizione avanza della stessa quantità di quella lineare. Se la finestra non si muove e la posizione ne esce, rientra dal lato opposto. Se la finestra si muove e lascia indietro la testina, questa è riportata al bordo da cui sarebbe uscita: l'inizio, se avanzava, la fine, se tornava indietro.

La deviazione di posizione si dichiara con `offset_range`, la larghezza della banda attorno alla posizione calcolata. L'unità è una frazione della finestra attiva, il file intero se non c'è un loop, ed è per questo che il passo precedente la moltiplica per la lunghezza della finestra: con 0,2 la banda è larga un quinto della finestra. Il valore sta fra 0 e 1, e il modulo riporta dal lato opposto i grani che uscirebbero dalla finestra.

Il confine riguarda però soltanto la partenza del grano. Il grano non porta con sé il loop, perché nessuno dei suoi otto campi lo descrive, e il renderer legge a partire da `pointer_pos` per tutta la durata, avanzando del rapporto di altezza e tornando all'inizio del *file*, non della finestra (`rendering/grain_renderer.py`):

```python
increment = grain.pitch_ratio * file_sr / self.output_sr
...
read_indices = read_indices % n_source
```

Un grano di 0,2 s che parte a 0,55 s in un loop che finisce a 0,6 s legge fino a 0,75 s. Il loop decide da dove si parte, non fin dove si legge.

L'esempio `loop` muove una finestra larga 0,2 volte la durata del file, da 0,1 a 0,6 della durata del file, con la lettura a velocità naturale. Dopo metà dello stream la banda di posizione si apre fino a 0,5.

```yaml
pointer:
  loop_unit: normalized
  speed_ratio: 1.0
  loop_start: [[0, 0.1], [1, 0.6]]
  loop_dur: 0.2
  offset_range: [[0, 0], [0.5, 0], [1, 0.5]]
```

![La finestra di loop, in colore, scorre nel file. Il puntatore la percorre e, raggiunta la fine, ricomincia dall'inizio della finestra; dopo metà dello stream i grani si disperdono dentro la finestra.](docs/images/loop_map.pdf){width=100%}

## La griglia di emissione

Il campo `onset` dipende da una successione di intervalli. L'intervallo fra due onset successivi si chiama *inter-onset time* (IOT), e due parametri lo governano: la densità (`density`), in grani al secondo, che ne fissa il valore medio, $\mathrm{IOT}_{\mathrm{avg}} = 1/\mathit{density}$, e la distribuzione (`distribution`), che stabilisce quanto gli intervalli siano regolari. «Sincrono» e «asincrono» hanno il senso di Roads descritto nel capitolo 2: la regolarità degli intervalli.

In alternativa alla densità si può dichiarare il *fill factor* (`fill_factor`), il prodotto della densità per la durata del grano. Ha la priorità se compare insieme alla densità, perché nello schema dei parametri è il primo del gruppo esclusivo `density_mode`; e se non compare nessuno dei due vale 2. Con il fill factor la densità diventa un quoziente, e il motore lo calcola con la durata del grano che sta per emettere (`strategies/strategie.py`):

```python
fill_factor = self._fill_factor.get_value(elapsed_time)
grain_duration = context['grain_duration']
raw_density = fill_factor / grain_duration
return self._clamp(raw_density)
```

Dopo un grano di durata $d$, il successivo arriva dunque dopo $d/F$, con $F$ il fill factor, qualunque sia $d$: la sovrapposizione resta quella dichiarata anche quando la durata varia da un grano all'altro. È la differenza pratica fra le due chiavi, perché con la densità la sovrapposizione cambia con la durata.

I limiti sono pochi. `density` non ha un tetto e ha un pavimento di 0,01 grani al secondo: l'intervallo medio è il suo inverso, e una densità nulla sarebbe una divisione per zero. Sopra `DENSITY_NOTICE_THRESHOLD`, 4 000 grani al secondo, il motore non taglia ma scrive un avviso nel log, perché a quella densità una durata del grano sbagliata di un ordine di grandezza è un rendering che non finisce. Il `fill_factor` sta fra 0,001 e 50. Un valore dichiarato fuori dai limiti, che sia un numero o il punto di un inviluppo, è un errore alla lettura dello YAML: il motore non lo corregge in silenzio.

La distribuzione è un numero fra 0 e 1, e fuori da questo intervallo è un errore. Con $d$ uguale a `distribution`, l'intervallo è

$$\mathrm{IOT}(d) = (1-d)\,\mathrm{IOT}_{\mathrm{avg}} + d\,\mathcal{U}\!\left(0,\, 2\,\mathrm{IOT}_{\mathrm{avg}}\right), \qquad d \in [0,1]$$

dove $\mathcal{U}$ è il campionamento uniforme. Il codice è la formula (`density_controller.py`):

```python
dist_val = self.distribution_param.get_value(elapsed_time)
if dist_val <= 0.0:
    return avg_iot
else:
    async_iot = self._rng.uniform(0.0, 2.0 * avg_iot)
    return (1.0 - dist_val) * avg_iot + dist_val * async_iot
```

L'espressione è una combinazione convessa. A $d = 0$ ogni intervallo vale $\mathrm{IOT}_{\mathrm{avg}}$: la griglia è metronomica, l'emissione sincrona, e il ramo non consuma numeri casuali. A $d = 1$ l'intervallo è estratto da una distribuzione uniforme fra 0 e il doppio del valore medio: l'emissione è asincrona, ma non è un processo di Poisson, i cui intervalli sarebbero esponenziali: qui sono limitati fra 0 e il doppio della media. I valori intermedi sono il regime quasi-sincrono. Il parametro accetta un inviluppo, quindi lo stream può passare dall'uno all'altro regime nel tempo.

La griglia è un cursore che avanza lungo lo stream (`Stream.generate_grains`). A ogni passo il motore emette un grano al tempo del cursore e lo sposta dell'intervallo calcolato in quell'istante, con la durata di quel grano:

```python
grain_dur_0 = self.grain_duration.get_value(t0)
sync_iot = self._density.calculate_inter_onset(t0, grain_dur_0)
...
voice_cursors[voice_index] += iot
```

Il cursore è uno per voce, e le voci sono il tema del capitolo 6. Il primo grano è sempre a 0, e il cursore si ferma quando supera la durata dello stream. Un grano la cui coda sfora la fine è però scartato, non troncato (`strategies/grain_clip_strategy.py`):

```python
stream_end = stream.onset + stream.duration
limit = stream_end + self.margin
```

La strategia tiene i grani con `g.onset < stream_end` e `g.onset + g.duration <= limit`, e il margine è nullo per impostazione predefinita. Per questo lo stream minimo del capitolo 4 ha 78 grani e non 79: quello nato a 1,95 s finirebbe a 2,0 s, dopo la fine del file, che dura 1,985 s.

L'esempio `distribution` lascia ferma la lettura su un punto del file, per vedere soltanto la griglia di emissione. Lo stream dura 20 secondi. La densità sale da 10 a 200 grani al secondo e ridiscende; la distribuzione resta a zero fino a circa 6 secondi e poi sale a 1, per ritornare a zero.

```yaml
duration: 20
time_mode: normalized
density: {type: cubic, points: [[0, 10], [0.5, 200], [1, 10]]}
pointer:
  speed_ratio: 0.0
  start: 0.5
  loop_unit: normalized
distribution: {type: cubic, points: [[0.3, 0], [.75, 1], [1, 0]]}
```

![Passaggio da emissione sincrona ad asincrona su lettura ferma. Nella prima lente gli onset sono equispaziati, nella seconda irregolari.](docs/images/distribution_map.pdf){width=100%}

La differenza si sente oltre che vedersi. Quando la griglia è sincrona e la densità è alta, l'emissione periodica di grani identici produce uno spettro a righe, spaziate a multipli della densità [@Roads2001Pulsars]. Quando la distribuzione sale verso 1 gli istanti di emissione si irregolarizzano e le righe si smerigliano in una banda.

## Il grano

I campi che restano descrivono il grano in sé: quanto dura, con quale finestra, a quale altezza, in che verso legge, con quale livello e in quale posizione del campo sonoro.

### La durata

La durata è in secondi per impostazione predefinita (0,05 s) e sta fra un campione, circa 21 microsecondi a 48 kHz, e 10 secondi: fuori da quei limiti il motore si ferma con un errore. Con `grain.duration_unit` si può dichiararla in millisecondi o in campioni, alla frequenza di uscita del motore. Il millisecondo è la scala comoda per la granulazione udibile, dove in secondi si scriverebbero soltanto numeri molto piccoli. Le unità sono tre, e la conversione avviene alla lettura del file, per i valori fissi e per gli inviluppi (`core/stream.py`):

```python
GRAIN_DURATION_UNITS = ('seconds', 'samples', 'milliseconds')
```

I millisecondi si moltiplicano per $10^{-3}$, i campioni si dividono per la frequenza di uscita. Con un'unità diversa dai secondi la durata va scritta, perché il valore predefinito resterebbe in secondi e non verrebbe convertito: senza di essa il motore si ferma con un errore che lo dice. Anche `duration_range` si converte, a meno che sia relativa: allora è una frazione della durata corrente, istante per istante, e non ha unità (capitolo 4).

L'esempio `duration`, tratto dal paper, non isola la durata: la fa variare insieme a densità, distribuzione, pan e banda del pan. Serve a vedere che cosa succede quando la durata scende. A metà dello stream passa da 50 a circa 1 millisecondo e risale a 150, e a 1 millisecondo i grani sono clic (capitolo 2). La lente ingrandisce l'istante di durata minima, illeggibile a piena scala.

![Una texture in cui durata del grano, densità, distribuzione e pan variano insieme. Il colore dei grani indica lo scarto di altezza; in basso gli inviluppi dei parametri.](docs/images/duration_map.pdf){width=100%}

### La finestra

La finestra è l'inviluppo di ampiezza che dà forma al grano. Finestrare un grano ne modula l'ampiezza e aggiunge allo spettro bande laterali [@Roads2001]; la scelta della forma è quindi anche una scelta timbrica. Nel linguaggio la finestra si dichiara con la chiave `grain.envelope`, che non va confusa con gli inviluppi dei parametri, trattati nel capitolo 4. Il catalogo ha sedici finestre, e la parola `all` le comprende tutte.

| Nome nello YAML | Forma |
|----------------------------------------------------|------------------------------------------|
| `hanning` (predefinita), `hamming`, `blackman`, `blackman_harris` | somme di coseni |
| `bartlett`, alias `triangle` | triangolare |
| `gaussian`, `kaiser` | gaussiana, Kaiser-Bessel |
| `rectangle` | costante |
| `sinc`, `half_sine` | lobo centrale della sinc, semi-sinusoide |
| `expodec`, `expodec_strong`, `exporise`, `exporise_strong`, `rexpodec`, `rexporise` | tratti esponenziali asimmetrici |

Il catalogo (`controllers/window_registry.py`) è dato e non codice: ogni voce descrive una forma matematica e i suoi coefficienti. Hann e Hamming sono la stessa funzione, una somma di coseni, con coefficienti diversi, e per questo aggiungere una finestra di quella famiglia è una riga di catalogo. Le sei curve asimmetriche sono un solo segmento esponenziale, con valore iniziale, curvatura e valore finale:

```python
'hanning': WindowSpec(
    name='hanning',
    shape=WindowShape.COSINE_SUM,
    coefficients=(0.5, 0.5),
...
'rexpodec': _asymmetric_curve(
    'rexpodec', 1.0, -4.0, 0.0,
```

`rexpodec` parte a 1 e cade subito, con un attacco brusco e un decadimento esponenziale; `expodec` tiene il valore e cade alla fine. `exporise` e `rexporise` sono le loro omologhe lette all'indietro, e le versioni `_strong` hanno una curvatura di 10 invece di 4. I nomi non coincidono con quelli di Roads, come ha detto il capitolo 2.

Le modalità di dichiarazione sono quattro, e il motore sceglie la classe di selezione dalla forma di `grain.envelope` (`controllers/window_selection_strategy.py`).

- **Una finestra sola**, per nome.
- **Una lista di finestre**, fra cui il motore sceglie a caso per ogni grano.
- **Una transizione** da una finestra a un'altra, governata da una curva da 0 a 1: a 0 tutti i grani hanno la prima finestra, a 1 tutti la seconda, e nei valori intermedi la scelta è probabilistica.
- **Un percorso a più stati**, che generalizza la transizione a una sequenza di finestre collocate sull'asse della curva.

La transizione è un sorteggio per grano, e non una dissolvenza fra due finestre:

```python
return self._to if self._rng.random() < blend else self._from
```

Il valore `blend` è la curva valutata al tempo del grano e limitata a $[0, 1]$: a 0,5 metà dei grani ha la prima finestra e metà la seconda. Se la curva manca vale `[[0, 0], [1, 1]]` nel tempo dello stream, quindi in tempo assoluto arriva a 1 dopo un secondo, e di solito si usa con `time_mode: normalized`. La lista, invece, passa dal gate di probabilità della sezione sulla variazione stocastica: a gate chiuso il grano riceve la prima finestra della lista, a gate aperto una a caso, e senza `deviation_probability` il gate è sempre aperto. La transizione e il percorso a stati non lo consultano.

```yaml
grain:
  envelope:
    states: [[0, hanning], [0.5, rexpodec], [1, bartlett]]
    curve: [[0, 0], [1, 1]]
```

Nell'esempio `window` la finestra attraversa tre stati, a densità bassa perché le forme siano distinguibili: Hann, poi `rexpodec`, poi Bartlett.

![Il glifo del grano è la sagoma della sua finestra. Le tre lenti ingrandiscono tre istanti: all'inizio i grani sono finestrati per lo più con Hann, e qualcuno con la finestra esponenziale, perché la scelta è probabilistica; a metà con la finestra esponenziale, con l'attacco brusco e la coda che decade; in chiusura con Bartlett.](docs/images/window_map.pdf){width=100%}

### L'altezza

Il blocco `pitch` governa la trasposizione del grano. Funziona per unità: ogni unità di misura è una chiave del linguaggio, e in un blocco se ne dichiara una sola. Più unità insieme sono un errore, perché non c'è una priorità implicita; lo stesso vale per una chiave sconosciuta, come `semitone` al posto di `semitones`, che qui non viene ignorata, come accade altrove (capitolo 4), ma rifiutata. Senza alcuna unità il valore predefinito è zero semitoni, cioè il rapporto 1; per nessuna trasposizione si omette il blocco o si scrive `pitch: {}`, mentre `pitch:` lasciato vuoto è un errore.

| Chiave | Unità | Divisioni dell'ottava | Limiti |
|--------------------|----------------------------|--------------------|--------------------|
| `semitones` | semitoni | 12 | da $-36$ a 36 |
| `quarter_tone` | quarti di tono | 24 | da $-72$ a 72 |
| `eighth_tone` | ottavi di tono | 48 | da $-144$ a 144 |
| `cents` | cent | 1200 | da $-3600$ a 3600 |
| `edo` con `value` | divisione arbitraria dell'ottava | $N$ | da $-3N$ a $3N$ |
| `ratio` | rapporto diretto | non applicabile | da 0,001 a 8 |

Le unità della famiglia EDO (*equal division of the octave*) sono la stessa classe con un numero di divisioni diverso (`parameters/pitch_unit.py`):

```python
'semitones':    lambda: EdoUnit(12, name='semitones', symbol='st'),
'cents':        lambda: EdoUnit(1200, name='cents', symbol='c'),
'ratio':        lambda: RatioUnit(),
```

e la conversione nel rapporto di trasposizione è una riga, $2^{v/N}$ con $v$ il valore e $N$ il numero di divisioni:

```python
return 2 ** (value / self.divisions)
```

`ratio` è invece un moltiplicatore diretto. L'unità `edo` apre a scale arbitrarie: `edo: 31` con `value: 18` dichiara diciotto gradi di una scala a trentuno divisioni. I limiti delle unità EDO sono tre ottave, cioè $\pm 3N$ (`bound = 3.0 * self.divisions`).

Come per ogni parametro, il valore può essere un inviluppo, e la banda di variazione `range` è espressa nella stessa unità, con una larghezza massima di tre ottave per le unità EDO e di 2 per `ratio`. Nelle unità EDO la variazione è quantizzata: si estrae un grado intero della griglia, e con `range: 5` in semitoni i valori possibili sono $-2$, $-1$, 0, 1 e 2. Con `ratio` la variazione è continua.

L'esempio `pitch` lascia ferma la lettura e porta la trasposizione a gradini: 0, 7, $-5$ e 12 semitoni.

```yaml
pitch:
  semitones: {type: step, points: [[0, 0], [0.25, 7], [0.5, -5], [0.75, 12]]}
```

![La trasposizione a gradini su lettura ferma. Il colore dei grani codifica l'altezza, in cent rispetto al suono originale; in basso l'inviluppo dei semitoni.](docs/images/pitch_map.pdf){width=100%}

### Il verso di lettura

Il segno del rapporto di altezza è il verso con cui il grano legge il materiale. Tre grandezze diverse lo riguardano e vanno tenute distinte.

| Grandezza | Che cosa governa | Valori |
|------------------------------|-------------------------------------|--------------------------|
| `pointer.speed_ratio` | velocità e verso con cui la testina percorre il file | negativo: all'indietro |
| `grain.read_direction` | verso con cui il singolo grano legge il materiale | $-1$ indietro, $+1$ avanti |
| blocco `pitch` | altezza percepita | sempre positivo, per costruzione |

Il motore le compone in `Stream._calculate_grain_reverse`:

```python
if self.read_direction is not None:
    return self.read_direction.get_value(elapsed_time) < 0
if self.grain_reverse_mode == 'auto':
    is_reverse_base = (self._pointer.get_speed(elapsed_time) < 0)
else:
    is_reverse_base = True
```

Se `read_direction` è dichiarata vince il suo segno. Altrimenti il verso del grano segue quello della testina, a meno che sia presente `grain.reverse`: la chiave si scrive vuota, e forza l'inversione per tutti i grani. Un valore, come `reverse: true`, è un errore. Lo è anche dichiarare `read_direction` insieme a `reverse`, perché le due chiavi governano la stessa grandezza con semantiche opposte, e sceglierne una in silenzio nasconderebbe l'errore invece di segnalarlo. `read_direction` accetta soltanto $-1$ e $+1$, e un inviluppo ha l'interpolazione a gradini, imposta, perché il verso non ha valori intermedi.

Un grano letto all'indietro ha il rapporto negato (`pitch_ratio *= -1`, nel controller dell'altezza), e la sua posizione di lettura è spostata in avanti della sua durata (`final_pos += grain_duration`, nel puntatore). A rapporto 1 legge così lo stesso segmento del file che avrebbe letto in avanti, ma dalla fine verso l'inizio. Con la testina all'indietro e `read_direction: 1` i grani leggono in avanti, e viceversa.

L'esempio `read_direction` tiene costante la velocità della testina, che avanza nel file per tutta la durata dello stream, e inverte il verso dei grani fra 4 e 6 secondi.

```yaml
grain:
  duration: 0.12
  read_direction: [[0, 1], [0.5, -1], [0.75, 1]]
pointer:
  speed_ratio: 0.25
```

![La testina avanza sempre, ma fra 4 e 6 secondi i grani leggono all'indietro: la testa del grano si capovolge. Le lenti mostrano un grano in lettura diretta e uno in lettura inversa.](docs/images/read_direction_map.pdf){width=100%}

### Volume e posizione nel campo

Il `volume` è in decibel: 0 dB è il livello del campione, e i limiti vanno da $-120$ a $+12$ dB. Il renderer lo converte in ampiezza, $A = 10^{v/20}$ (capitolo 7).

Il `pan` è un angolo in gradi, da $-3600$ a 3600, perché il pan può ruotare su più giri. L'angolo muove il grano lungo una circonferenza unitaria in codifica Mid-Side, la matrice di Blumlein [@Blumlein1931]. Mid e side sono due microfoni a figura otto ortogonali, le proiezioni coseno e seno del grano lungo la circonferenza [@Gerzon1975]; sinistra e destra sono la stessa coppia ruotata di 45 gradi, e non l'unico esito possibile. Gli angoli si leggono così, con i guadagni sui due canali:

| Pan (gradi) | Sinistra | Destra | Posizione |
|-------------|----------|---------|----------------------------------|
| 0 | 0,707 | 0,707 | al centro |
| 45 | 1 | 0 | tutto a sinistra |
| $-45$ | 0 | 1 | tutto a destra |
| 90 | 0,707 | $-0{,}707$ | in controfase |
| 180 | $-0{,}707$ | $-0{,}707$ | al centro, a polarità invertita |

La potenza resta costante a ogni angolo, $L^2 + R^2 = 1$, come dice il capitolo 7. Gli angoli positivi vanno a sinistra, e il grano si muove fra le due casse fra $-45$ e $+45$ gradi: oltre quei valori prevale la componente side, e a $\pm 90$ gradi le due uscite sono in controfase, e un ascolto in mono le cancella.

Il grano porta un angolo, non una coppia di guadagni, e la matrice appartiene al renderer. I tre renderer di PGE usano la stessa matrice stereo, e con un'altra matrice lo stesso angolo potrebbe pilotare un numero qualsiasi di altoparlanti: la generalità sta nel dato e non ancora nei consumatori, come dice il capitolo 3. La posizione nel campo sonoro è, in ogni caso, un attributo del singolo grano, parte della costruzione dello strumento, e non un effetto di spazializzazione aggiunto in fondo alla catena.

## La variazione stocastica

I parametri di un grano non sono tutti decisi dal compositore uno per uno: sarebbe la specifica grano per grano che l'introduzione ha indicato come intrattabile. La parte del caso è dichiarata a due livelli. Ogni parametro ha una traiettoria centrale, un inviluppo, e una banda di deviazione attorno a quella traiettoria, `_range`, da cui si estrae un valore diverso per ogni grano. È la maschera di tendenza del capitolo 2, che il capitolo 4 ha scritto come un valore centrale e una larghezza. Con $c(\tau)$ la traiettoria centrale, $\rho(\tau)$ la larghezza della banda e $\xi_n$ un valore uniforme fra $-1/2$ e $1/2$, il parametro del grano $n$ al tempo normalizzato $\tau_n$ è

$$v_n = c(\tau_n) + \xi_n\,\rho(\tau_n), \qquad \xi_n \sim \mathcal{U}\!\left(-\tfrac{1}{2}, \tfrac{1}{2}\right)$$

I parametri che hanno una banda sono cinque, e la tabella del jitter più avanti ne elenca le chiavi. Il sistema aggiunge un terzo livello: la probabilità, variabile nel tempo, che la deviazione si applichi. Un *gate* probabilistico, una porta che si apre o si chiude, decide grano per grano se il grano segue la traiettoria o subisce la deviazione:

$$v_n = c(\tau_n) + g_n\,\xi_n\,\rho(\tau_n), \qquad g_n \sim \mathrm{Bernoulli}\!\big(p(\tau_n)\big)$$

dove $p(\tau)$ è la probabilità, anch'essa un inviluppo: nella formula è un numero fra 0 e 1, nello YAML si scrive da 0 a 100. Il metodo `Parameter.get_value`, descritto nel capitolo 3, è questa espressione: se il gate è chiuso restituisce il valore centrale, se è aperto lo fa passare dalla banda. La differenza rispetto alla prima formula è il fattore $g_n$, che rende l'ampiezza della deviazione, $\rho$, e la sua probabilità, $p$, due dimensioni di controllo indipendenti. La chiave che le dichiara è `deviation_probability`.

Quando la chiave manca, il gate è sempre aperto per i parametri che hanno un `_range`: l'espressione si riduce alla prima, ed è la maschera di tendenza semplice. Un parametro senza `_range` non devia mai. Lo dice una riga del motore (`parameters/gate_factory.py`):

```python
return AlwaysGate() if has_explicit_range else NeverGate()
```

Il gate è una classe con un solo metodo, `should_apply(time)`, e ne esistono quattro: `NeverGate`, `AlwaysGate`, `RandomGate`, con una probabilità fissa, ed `EnvelopeGate`, con una probabilità che varia nel tempo (`shared/probability_gate.py`):

```python
return self._rng.uniform(0, 100) < self._probability
```

Nelle fonti consultate non si trova un precedente diretto del gate come asse dichiarabile e componibile nel tempo. Il più vicino è nell'ICMS, dove alcune trasformazioni del grano (lettura retrograda, inversione di fase, ripetizione) si applicano a circa metà dei grani per decisione di un generatore casuale [@DiScipioTisato1993cim]: la probabilità è però fissa e non dichiarata, e governa interruttori discreti, non l'applicazione di una maschera a un parametro continuo. Per forma è più vicina l'*intermittency* di EmissionControl2, un gate per grano dichiarabile e modulabile con continuità [@Roads2021]; ma decide se il grano viene emesso e agisce quindi sulla densità. Nel linguaggio qui descritto il grano resta, e il gate decide se applicargli la deviazione.

L'indipendenza dei due assi si vede in due stream che condividono la stessa traiettoria, una lettura ferma, e la stessa ampiezza massima di deviazione (esempio `deviation`). Nel primo cresce l'ampiezza della deviazione, nel secondo la probabilità; la differenza sta in due righe.

```yaml
# a: cresce l'ampiezza; deviation_probability è assente
pointer:
  offset_range: [[0, 0.0], [1, 0.35]]

# b: l'ampiezza è fissa e cresce la probabilità
deviation_probability:
  pointer: [[0, 0], [1, 100]]
pointer:
  offset_range: 0.35
```

![Due modi di aprire la deviazione, a parità di traiettoria e di ampiezza massima. Pannello superiore: l'ampiezza cresce da 0 a 0,35 con il gate sempre aperto, e i grani riempiono uniformemente uno spazio di lettura che si allarga a cuneo. Pannello inferiore: l'ampiezza è costante e cresce la probabilità da 0 a 100%; la linea si trasforma in nuvola, passando da grani fedeli a grani devianti.](docs/images/deviation_map.pdf){width=100%}

### Come si dichiara la probabilità

`deviation_probability` accetta più forme. Un numero da 0 a 100 vale per tutti i parametri; un inviluppo lo fa variare nel tempo; un dizionario assegna una probabilità per parametro, con le chiavi `volume`, `pan`, `duration`, `pitch`, `pointer`, `reverse`, `read_direction` e, per la lista di finestre, `pc_rand_envelope`, e ciascuna può essere a sua volta un inviluppo.

Vale una regola che conviene conoscere. In modalità per parametro, un parametro assente dal dizionario non riceve probabilità: se ha un `_range` dichiarato lo applica sempre, a tutti i grani, e se non ce l'ha resta fermo. Nel dizionario si dichiarano quindi soltanto i parametri di cui si vuole *ridurre* la probabilità. Nella modalità globale invece un'unica probabilità vale per tutti i parametri, anche per quelli senza `_range`.

```yaml
# solo il volume è ridotto al 30%; gli altri parametri con un _range lo applicano sempre
deviation_probability:
  volume: 30
```

Resta un caso che ha sorpreso più volte e che il progetto ha fissato con un test. Esistono cinque modi di scrivere la chiave senza assegnarle un valore, e quattro danno lo stesso risultato: nessun gate stocastico, cioè la regola di sopra. Lo danno l'omissione della chiave, `false`, `{}` e un parametro dichiarato `null`: i parametri senza `_range` non deviano, e quelli con un `_range` lo applicano a ogni grano. Fa eccezione la chiave scritta e lasciata vuota, `deviation_probability:`, che in YAML vale `null` e attiva la modalità implicita: una probabilità dell'1% per ogni parametro, con un'ampiezza predefinita, anche per i parametri con un `_range`, che da quel momento si applica soltanto all'1% dei grani. Su uno stream di 79 grani con `read_direction` dichiarata e nessun `_range`, la chiave vuota ne ribalta in media 0,8, cioè l'1%; le altre quattro scritture nessuno. Quella che più somiglia a «non voglio deviazione» fa dunque l'opposto: per disattivare si scrive `false` o si omette la chiave.

### Il jitter implicito

Se si dichiara una probabilità senza un `_range` esplicito, il motore applica una deviazione predefinita, il *jitter* implicito, parola inglese che indica un piccolo tremolio attorno al valore. L'ampiezza dipende dal parametro, e la tabella la dà come semi-ampiezza, con a fianco la chiave della banda e la larghezza massima che un `_range` dichiarato può avere.

| Parametro | Chiave della banda | Jitter implicito | Larghezza massima |
|------------|--------------------------------|------------------------|----------------------|
| volume | `volume_range` | ±1,5 dB | 24 dB |
| pan | `pan_range` | ±15 gradi | 360 gradi |
| durata | `grain.duration_range` | ±5 ms | 1 s, o 1 se relativa |
| lettura | `pointer.offset_range` | ±2,5% della finestra di lettura | 1, la finestra intera |
| altezza | `pitch.range` | ±12 cent, o ±0,0025 con `ratio` | tre ottave, o 2 con `ratio` |
| verso | | inversione discreta | |

Quella microvariazione è la decorrelazione di cui parla Vaggione, che rende una massa granulare più organica e meno meccanica [@Vaggione2002]. Per l'altezza il detune implicito è continuo e si applica dopo la quantizzazione sulla griglia dell'unità scelta; con un `range` dichiarato, anche nullo, non si applica e vale la variazione quantizzata dichiarata. Una probabilità globale apre il gate anche sul verso: con il 100% tutti i grani leggono nel verso opposto a quello di base, con il 50% la metà.

Nell'esempio `probability` la sola `deviation_probability` sale a gradini da 0 a 100%, senza alcun `_range` dichiarato.

```yaml
grain:
  duration: 0.02
deviation_probability: {points: [[0, 0], [.2, 25], [.4, 50], [.6, 75], [.8, 100]], type: step}
```

![La sola probabilità sale a gradini. Nel primo tratto i grani sono allineati sulla traiettoria; a ogni gradino una quota maggiore se ne discosta, per effetto del jitter implicito e dell'inversione del verso (il colore dei grani indica lo scarto di altezza). Nella legenda, la percentuale accanto al nome di un parametro è la probabilità che la deviazione sia applicata, non la sua ampiezza.](docs/images/probability_map.pdf){width=100%}


# L'architettura multi-voce

Finora lo stream è stato una voce sola. PGE ne prevede $N$, e il modello sono le voci parallele del DMX-1000 di Truax, la cui molteplicità fissa la densità in verticale (capitolo 1). Le voci di PGE non sono però generatori indipendenti: sono copie di una voce di riferimento, ciascuna con scarti propri. Questo capitolo descrive che cos'è una voce nel codice, quali scarti si possono assegnare e con quali strategie, in che modo il numero delle voci varia nel tempo e quanto la loro scansione temporale è indipendente. È l'ultimo scostamento dell'esposizione del paper [@DeMattia2026Cim]: dopo la risintesi, la posizione di lettura, la griglia, il grano e la deviazione, si moltiplica lo stream di partenza. Le affermazioni sul comportamento del motore sono controllate, una per una, dallo script `esempi/multivoce/verifica_multivoce.py`.

## Che cos'è una voce

Una voce è una lista di grani. Lo stream calcola, per ciascuna, la stessa produzione di grani della voce di riferimento, e a ogni grano applica quattro scarti. Gli scarti viaggiano in un oggetto minimo, un dato congelato come il grano (`controllers/voice_manager.py`):

```python
@dataclass(frozen=True)
class VoiceConfig:
    pitch_factor: float
    pointer_offset: float
    pan_offset: float
    onset_offset: float
```

Il `VoiceManager` lo costruisce a ogni grano interrogando quattro strategie indipendenti, una per asse, che ricevono l'indice della voce, il numero massimo di voci e il tempo, e non conoscono il resto dello stream:

```python
return VoiceConfig(
    pitch_factor=pitch,
    pointer_offset=pointer,
    pan_offset=pan,
    onset_offset=onset,
)
```

Gli assi sono quattro, ortogonali: ciascuno ha la propria strategia, e qualunque combinazione è valida. `Stream._create_grain` applica gli scarti al grano, ciascuno a modo suo: il fattore di altezza si moltiplica sul rapporto, il pan si somma, l'onset si ritarda, e lo scarto di lettura si somma alla posizione prima del confinamento nel loop (capitolo 5).

```python
pitch_ratio *= voice_config.pitch_factor
pan = self.pan.get_value(elapsed_time) + voice_config.pan_offset
absolute_onset = self.onset + elapsed_time + voice_config.onset_offset
```

La voce 0 è il riferimento, e non riceve scarti da nessuna strategia. È un invariante che ogni strategia garantisce, e che la più semplice scrive così:

```python
if voice_index == 0:
    return 0.0
return float(voice_index) * resolve_param(self.step, time)
```

Perciò uno stream con `num_voices: 1` è identico a uno senza il blocco `voices`. Non è identico, però, alla voce 0 di uno stream con più voci: i parametri per grano di tutte le voci (volume, durata, banda del pan) pescano dallo stesso generatore, uno per parametro e non per voce, e ogni voce aggiunta consuma estrazioni che spostano quelle della voce 0. Gli scarti stocastici delle strategie sono invece indipendenti dal numero delle voci, come si vedrà più avanti.

Ogni voce ha un proprio cursore del tempo, e produce una propria lista (`stream.voices`, capitolo 3). La densità dichiarata vale per ogni voce, perciò la densità complessiva è la densità per il numero di voci: con 4 voci e 10 grani al secondo per voce, 40 grani al secondo. Gli scarti si calcolano al tempo del cursore della voce, che con la griglia sincrona coincide con quello della voce 0 e con la griglia indipendente (`scatter`, più avanti) se ne separa.

Le strategie ricevono il numero *massimo* di voci, il picco di `num_voices`, e non quello attivo in quell'istante. La conseguenza è utile a chi compone: una voce che si accende non sposta le altre. Con `num_voices` da 2 a 4 e una strategia `range` di 12 semitoni, la voce 1 sta a +4 semitoni anche quando è l'unica voce secondaria.

Il blocco `voices` ha il numero di voci e le quattro strategie.

```yaml
voices:
  num_voices: 4
  scatter: 0.0
  pitch:        {strategy: ..., ...}
  onset_offset: {strategy: ..., ...}
  pointer:      {strategy: ..., ...}
  pan:          {strategy: ..., ...}
```

La scala degli scarti decide che cosa si ascolta. Con scarti di onset di pochi millesimi di secondo le voci sono versioni sfasate dello stesso evento. Nel DMX-1000 le voci avviate in istanti diversi, anche nello stesso interrupt di clock, hanno rapporti di fase diversi, e ne risulta un'ampiezza variabile per cancellazione e rinforzo [@Truax1988, p. 18]. Sul piano percettivo è la decorrelazione microtemporale di cui parla Vaggione: la massa si ispessisce e acquista direzione [@Vaggione2002]. Con scarti più lunghi della durata del grano le voci non si sovrappongono più nel tempo e diventano eventi distinti, e lo stesso meccanismo produce polifonia. Il sistema non distingue i due regimi: sono lo stesso strumento a scale diverse.

## Onset, pointer e pan

Tre assi su quattro hanno strategie della stessa famiglia: lo scarto cresce con l'indice della voce, oppure è estratto a caso. La tabella dà le chiavi di ciascuna strategia; ogni chiave accetta un numero o un inviluppo, quindi uno scarto può variare nel tempo e un cluster può aprirsi in un ventaglio.

| Asse | Strategia | Chiavi | Scarto della voce $i$ |
|----------------|-------------|-----------------|----------------------------------|
| `onset_offset` | `linear` | `step` | $i \cdot \mathit{step}$ secondi |
| | `geometric` | `step`, `base` | $\mathit{step} \cdot \mathit{base}^{\,i-1}$ secondi |
| | `stochastic` | `max_offset` | un valore fra 0 e `max_offset` secondi |
| `pointer` | `linear` | `step` | $i \cdot \mathit{step}$ |
| | `stochastic` | `pointer_range` | un valore fra $-$`pointer_range` e $+$`pointer_range` |
| `pan` | `step` | `step` | $i \cdot \mathit{step}$ gradi |
| | `range` | `spread` | $-\mathit{spread}/2 + i \cdot \mathit{spread}/(N-1)$ gradi |
| | `stochastic` | `spread` | un valore fra $-\mathit{spread}/2$ e $+\mathit{spread}/2$ gradi |

Le strategie stocastiche estraggono lo scarto di ogni voce una volta sola, e lo conservano (`strategies/voice_pointer_strategy.py`):

```python
if voice_index not in self._cache:
    rng = voice_rng(self.seed, self.stream_id, voice_index)
    self._cache[voice_index] = rng.uniform(-1.0, 1.0)
return self._cache[voice_index] * resolved
```

La direzione dello scarto resta stabile e ciò che varia nel tempo, seguendo l'inviluppo, è soltanto la sua grandezza: una voce collocata a sinistra di quella di riferimento non cambia lato. Il generatore è derivato dal seme, dall'identità dello stream e dall'indice della voce (`shared/seeding.py`):

```python
digest = hashlib.sha256(
    f"{seed}:{stream_id}:{voice_index}".encode()
).hexdigest()
```

e non dipende dal numero delle voci: aggiungerne una lascia dove sono gli scarti delle altre. L'identità è lo `stream_id`, o il `rng_group` quando più stream condividono la sequenza (capitolo 4), e due stream dello stesso gruppo hanno le voci negli stessi punti.

**Onset.** Lo scarto ritarda l'ingresso della voce. Le voci ritardate perdono i grani di coda: un grano la cui fine sfora quella dello stream è scartato (capitolo 5), e con un passo di 0,05 s, in uno stream di 4 secondi a 10 grani al secondo, la terza e la quarta voce hanno 39 grani, contro i 40 della voce 0. Gli scarti non sono vincolati a essere positivi, e un passo negativo anticipa le voci (si veda l'ultima sezione).

**Pointer.** Lo scarto è in secondi nel file; con `normalized: true`, che accetta soltanto un booleano vero, è una frazione della durata del file. Un passo negativo sposta le voci verso l'inizio del file rispetto alla voce di riferimento, e non ne cambia il verso di lettura. Lo scarto si somma alla posizione prima del modulo, perciò dentro un loop la voce resta nella finestra: con un loop da 0,9 a 1,3 s, la testina a 1,0 s e un passo di 0,3 s, le quattro voci leggono a 1,0, 0,9, 1,2 e 1,1 s, perché 1,3, 1,6 e 1,9 sono riportati nella finestra dal modulo.

**Pan.** Lo scarto è un angolo (capitolo 5), che si somma al `pan` dello stream: un offset uguale per tutte le voci non è una strategia, lo dà il parametro `pan`. La spazializzazione agisce quindi a due livelli annidati. La strategia assegna a ciascuna voce il proprio angolo, e `pan_range` aggiunge a ogni grano di quella voce una deviazione attorno a quell'angolo. La strategia `range` merita una nota, perché si comporta in modo diverso da come la descrive la sua documentazione (`strategies/voice_pan_strategy.py`):

```python
if voice_index == 0 or spread == 0.0 or num_voices <= 1:
    return 0.0

return -spread / 2.0 + voice_index * spread / (num_voices - 1)
```

La voce 0 resta al centro, per l'invariante, e le altre si dispongono a passo costante da $-\mathit{spread}/2 + \mathit{passo}$ fino a $+\mathit{spread}/2$. Con 4 voci e un ventaglio di 120 gradi gli scarti sono 0, $-20$, $+20$ e $+60$; con 3 voci le prime due coincidono. Il ventaglio non è centrato sullo zero: l'ultima voce sta a $+\mathit{spread}/2$, e la voce 0 non è a un bordo.

## Il pitch

Il pitch di una voce è un fattore moltiplicativo sul rapporto di lettura. A produrlo è un'unità di altezza, della stessa famiglia del blocco `pitch` dello stream (capitolo 5), che possiede la geometria: le strategie `step`, `range` e `stochastic` emettono una posizione adimensionale, e l'unità la materializza in un fattore. Nelle unità della famiglia EDO la distribuzione è additiva nel logaritmo, equidistante in semitoni, cent o gradi; con `ratio` è geometrica (`parameters/pitch_unit.py`):

```python
return 2 ** (position * amount / self.divisions)
```

```python
return amount ** position
```

Un passo di 2 in `ratio` dà dunque i rapporti 1, 2, 4 e 8, e le frequenze si compongono moltiplicandosi. L'unità si sceglie con la chiave `unit` del sotto-blocco, che accetta le stesse unità del blocco `pitch` (`unit: {edo: 31}` per una divisione arbitraria), indipendentemente da quella dello stream; senza `unit` valgono i semitoni.

| Strategia | Chiavi | Scarto della voce $i$ |
|---------------------------|------------------------|--------------------------------|
| `step` | `step` | $i \cdot \mathit{step}$ (EDO), $\mathit{step}^{\,i}$ (`ratio`) |
| `range` | `pitch_range` | da 0 a `pitch_range`, in parti uguali fra la voce 0 e l'ultima |
| `stochastic` | `pitch_range` | un valore fra $-$`pitch_range` e $+$`pitch_range`, fisso per voce |
| `chord` | `chord`, `inversion` | l'$i$-esima nota dell'accordo, estesa per ottave |
| `chord_progression` | `progression`, `interp`, `voice_leading` | l'accordo in funzione del tempo |
| `spectral` | | il parziale $i+1$ della serie armonica |

Con 4 voci, `step: 3` dà 0, 3, 6 e 9 semitoni, e `range` con `pitch_range: 12` dà 0, 4, 8 e 12. Un passo di un'ottava distende le voci in ottave pulite. Le strategie `chord`, `chord_progression` e `spectral` sono definite per costruzione in semitoni e rifiutano ogni altra unità, con un errore che lo dice.

Gli accordi sono nominati e raggruppati per numero di note.

| Note | Accordi |
|------|---------|
| 3 | `maj`, `min`, `dim`, `aug`, `sus2`, `sus4` |
| 4 | `dom7`, `maj7`, `min7`, `dim7`, `minmaj7` |
| 5 | `dom9`, `maj9`, `min9`, `9sus4` |
| 6 | `dom9s11`, `maj9s11`, `min11` |
| 7 | `dom13`, `min13`, `maj13s11`, `altered` |

Ogni accordo è una lista di intervalli in semitoni (`voice_pitch_strategy.py`):

```python
'maj':     [0, 4, 7],
'dom7':    [0, 4, 7, 10],
'altered': [0,  4,  7, 10, 13, 15, 20],
```

Se le voci sono più delle note, le eccedenti continuano il disegno all'ottava superiore: con $n$ note, la voce $i$ prende la nota $i \bmod n$ e vi somma $\lfloor i/n \rfloor$ ottave.

```python
n = len(self._intervals)
octave = voice_index // n
interval_idx = voice_index % n
```

Con `dom7` e sei voci i semitoni sono 0, 4, 7, 10, 12 e 16. `inversion` ruota gli intervalli perché la nota di grado $k$ diventi la più bassa: con `inversion: 1` `dom7` dà 0, 3, 6 e 8. `spectral` mette la voce $i$ sul parziale $i+1$, a $\mathrm{round}(12\log_2(i+1))$ semitoni: 0, 12, 19, 24, 28, 31, 34 e 36 per le prime otto voci.

**La progressione.** `chord_progression` fa dell'accordo una funzione del tempo. La progressione è una lista di coppie `[tempo, accordo]`, con un rivolto facoltativo, scritto come terzo elemento o in forma di dizionario (`{chord: min7, inversion: 1}`). I tempi non decrescono e seguono il modo temporale dello stream, come ogni inviluppo. Per ogni voce il motore costruisce un inviluppo dei semitoni, con un punto per accordo, e lo interpola con `interp`: lineare o cubica, e le voci scivolano in glissando, oppure a gradini, e l'armonia cambia a blocchi. Il moto della radice non appartiene alla progressione, perché la voce 0 resta ferma a 0: si dichiara sull'inviluppo `pitch` dello stream, e si somma al voicing.

La chiave `voice_leading` decide come le note del nuovo accordo si abbinano alle voci. Con `positional` la nota $i$ va alla voce $i$. Con `nearest`, il caso predefinito, le note si riabbinano alle voci superiori perché ogni voce si muova il meno possibile, scegliendo per ciascuna l'ottava più vicina e tenendo ferme le note comuni. Il riabbinamento è una ricerca su tutte le permutazioni, che il motore si risparmia oltre un limite (`strategies/voice_pitch_strategy.py`):

```python
if m > cls._NEAREST_BRUTE_MAX:
    return [float(t) for t in target_slots]
```

Il limite è 8 voci superiori: da 10 voci in su `nearest` ripiega in silenzio su `positional`. Con quattro voci le due strategie si distinguono poco: tra due accordi di quattro note, con il primo in posizione fondamentale, differiscono soltanto quando il secondo è in terzo rivolto, e da `maj7` a `minmaj7` in terzo rivolto `positional` sposta le voci di 9 semitoni in tutto, `nearest` di 3. `nearest` non fa mai peggio di `positional`.

L'esempio (`voices_chords`) lascia ferma la lettura e usa quattro voci, separate nella posizione di lettura di 0,08 volte la durata del file perché le bande siano distinguibili. La progressione va da `maj7` a `min7` a `dom7`, e la radice, sull'inviluppo `pitch` dello stream, passa a +5 semitoni a un terzo dello stream e a $-2$ ai due terzi.

```yaml
pitch:
  semitones: {type: step, points: [[0, 0], [0.34, 5], [0.67, -2]]}
voices:
  num_voices: 4
  pitch:
    strategy: chord_progression
    progression:
      - [0, maj7]
      - [0.34, min7]
      - [0.67, dom7]
    interp: step
    voice_leading: nearest
```

![Quattro voci su una progressione d'accordi. Ogni voce traccia una banda orizzontale nella posizione di lettura, e il colore ne codifica l'altezza. A un terzo dello stream il voicing passa da `maj7` a `min7` (la terza e la settima scendono di 100 cent) e a due terzi da `min7` a `dom7` (la terza risale di 100 cent). Negli stessi punti la radice sposta tutte le bande, a +5 semitoni e poi a $-2$.](docs/images/voices_chords_map.pdf){width=100%}

## Il numero di voci e le dissolvenze

Il numero di voci, `num_voices`, è un valore fisso o un inviluppo, e va da 1 a 256: fuori dai limiti è un errore alla lettura. Il motore prepara una lista per ogni voce possibile, cioè tante quante il picco dell'inviluppo, arrotondato per eccesso. Il valore interpolato può essere frazionario. In quel caso le voci intere suonano a volume pieno, e la parte decimale diventa un fattore di volume sulla voce di confine, quella che si sta accendendo o spegnendo (`Stream.generate_grains`):

```python
value = min(float(max_v), self.num_voices.get_value(t))
n_full = floor(value)
frac = value - n_full

if voice_index < n_full:
    voice_gain = 1.0
elif voice_index == n_full and frac > 0.0:
    voice_gain = frac           # voce di confine: fade graduale
else:
    voice_gain = 0.0            # voce spenta → nessun grano
```

Il guadagno è applicato in decibel al volume del grano, con un pavimento a $-120$ dB:

```python
if voice_gain != 1.0:
    volume = max(-120.0, volume + 20.0 * log10(voice_gain))
```

Con $f$ la parte frazionaria, la voce di confine suona dunque di $20\log_{10} f$ decibel, un numero negativo: $-6$ dB per $f = 0{,}5$ e $-12$ dB per $f = 0{,}25$. Invece di un'accensione di colpo, la voce sale o scende gradualmente. Con interpolazione a gradini e punti interi non c'è parte frazionaria, e le voci si accendono e si spengono di colpo; con interpolazione lineare o cubica la transizione fra due conteggi interi diventa una dissolvenza. La dissolvenza è guidata dall'inviluppo e non usa numeri casuali. Nella MAP la voce in dissolvenza appare più trasparente, perché l'opacità del grano segue il suo volume.

L'esempio (`voices_fade`) porta il numero di voci da 1 a 4 a metà dello stream, e poi a 2,5.

```yaml
voices:
  num_voices: [[0, 1], [0.5, 4], [1, 2.5]]
  pitch:
    strategy: step
    step: 5
  pointer:
    strategy: linear
    step: 0.08
    normalized: true
```

![Il numero di voci sale da 1 a 4 e scende a 2,5. Ogni voce entra con una dissolvenza (la banda è più trasparente all'inizio), e la quarta voce esce prima della fine, quando il valore scende sotto 3.](docs/images/voices_fade_map.pdf){width=100%}

### L'accoppiamento temporale fra le voci

Un secondo controllo governa quanto le voci siano indipendenti nel tempo, ed è un livello che si aggiunge alla griglia della singola voce. Il capitolo 2 ha ricordato che il trattamento canonico della granulazione ha due controlli distinti, il ritardo fra i grani di un flusso e il grado di sincronicità fra flussi diversi [@Dutilleux2016]. Il primo lo governa la griglia, descritta nel capitolo 5. Il secondo è `scatter`, un numero da 0 a 1, anche come inviluppo. L'intervallo di una voce è la combinazione lineare dell'intervallo condiviso, calcolato per la voce 0, e di uno indipendente, pesata da `scatter` (`Stream.generate_grains`):

```python
if voice_index == 0 or scatter_val == 0.0:
    iot = sync_iot
else:
    indep_iot = self._density.calculate_inter_onset(t, grain_dur)
    iot = (1.0 - scatter_val) * sync_iot + scatter_val * indep_iot
```

A 0 tutte le voci condividono la sequenza di intervalli della voce 0. A 1 ciascuna calcola la propria. Con $s$ uguale a `scatter` e griglia stocastica, la correlazione fra gli intervalli di una voce e quelli della voce 0 vale $(1-s)/\sqrt{(1-s)^2+s^2}$: 1 a $s=0$, circa 0,71 a $s=0{,}5$, 0 a $s=1$.

`scatter` si distingue dallo scarto di onset, che è uno sfasamento fisso: non ritarda le voci, decide se la loro scansione temporale sia la stessa. Agisce quindi in modo evidente quando la griglia è stocastica. Con una griglia pienamente sincrona le voci che calcolano la propria sequenza producono la stessa, e i due regimi coincidono: con `distribution` a 0 e densità e durata fisse gli onset delle voci sono identici per qualunque `scatter`. Con `distribution` a 1 le sequenze indipendenti divergono, e l'inviluppo di `scatter` diventa il passaggio da un'unica nuvola coerente a più nuvole indipendenti. Anche questo calcolo è stocastico: quali voci si sganciano e in quali istanti cambia da una realizzazione all'altra, ma l'andamento dell'inviluppo resta lo stesso, e con il seme dichiarato la realizzazione si ripete.

Gli scarti delle strategie seguono il cursore della voce. Con `scatter` a 1 una voce ha i propri onset, e un inviluppo del `step` del pan è valutato all'istante di quella voce, non a quello della voce 0.

## Un esempio completo

L'esempio del paper (`voices`) mette insieme le quattro strategie e i due inviluppi di insieme, su uno stream di quaranta secondi.

```yaml
voices:
  num_voices: [[0,50],[.3,7],[.8,7],[1,70]]
  scatter: {type: cubic, points: [[0.6, 0.0], [0.85, 1.0]]}
  pitch:
    strategy: step
    step: 12
  pan:
    strategy: step
    step:
      points: [[.6,0],[.9,60.0]]
      time_mode: normalized
  pointer:
    strategy: linear
    step: .2
```

![Lo stream completo con le voci. Ogni voce traccia una banda orizzontale sulla posizione di lettura; il colore ne codifica la trasposizione. Le bande sono fitte e dense di grani in apertura, si diradano verso il centro, dove il numero di voci è minimo e i singoli onset diventano leggibili, e si moltiplicano di nuovo in chiusura. Nella seconda metà le bande, all'inizio allineate sulla stessa griglia temporale, si sfasano fino a confondersi in una nuvola diffusa.](docs/images/voices_map.pdf){width=100%}

Il numero di voci passa da 50 a 7 e a 70, e ogni voce ha la densità dello stream: sono 70 liste e 30 648 grani. Il passo di pitch è di un'ottava per voce, e il motore non pone un limite al fattore di una voce, perché i limiti dell'altezza valgono per il blocco `pitch` dello stream, che qui è tre ottave sotto (`cents: -3600`). Con 70 voci la più alta sta 69 ottave sopra la voce 0, e il rapporto di lettura arriva a $2^{66}$, contro un massimo di 8 che l'altezza di uno stream può dichiarare. Dalla voce 13 in poi il rapporto supera 1000, e la lettura salta nel file di circa mille campioni per ogni campione di uscita: l'esempio usa le prime voci come registro e le altre come estremo. La scala cromatica della figura, che arriva a circa 80 000 cent, ne misura l'escursione. Restano fuori dalla figura i parametri spaziali: il passo del pan è un inviluppo con la stessa scala del tempo dello stream, quindi il ventaglio resta chiuso fino a 24 secondi e si apre fra 24 e 36 secondi, fino a 60 gradi per voce, cioè a molti giri con 70 voci. Il passo di pointer, 0,2 s per voce, è ridotto modulo la durata del file, 1,985 s, e le posizioni delle voci ricominciano da capo ogni dieci voci circa.

## Che cosa il blocco lascia passare

Come il linguaggio del capitolo 4, il blocco `voices` non protesta davanti a ciò che non vincola. La tabella raccoglie i casi, tutti verificati.

| Si scrive | Il motore |
|-----------------------------------------------|-----------------------------------------------|
| `onset_offset` con un passo negativo | anticipa le voci, con onset negativi: il renderer NumPy ne taglia l'inizio |
| un passo di pitch che porta una voce a molte ottave | non lo limita: i limiti valgono per l'altezza dello stream |
| `voice_leading: nearest` con 10 voci o più | usa `positional`, senza avviso |
| un sotto-blocco senza `strategy` | si ferma con un `KeyError` nudo, non con un errore del motore |
| `pan` con strategia `range` | lascia la voce 0 a 0 e dispone le altre fino a $+\mathit{spread}/2$ |
| più voci | cambia i valori casuali per grano della voce 0 |

Nell'elenco la chiave `strategy` mancante è l'unico caso che interrompe il motore, e lo fa con un'eccezione di Python e non con un errore del progetto, che nominerebbe il campo.

## Come si estende

Le quattro famiglie di strategie sono punti di estensione, e il meccanismo è quello del capitolo 3: una classe che ne calcoli lo scarto e un nome nel registro, che diventa subito utilizzabile nel listato. Una nota riguarda il caso: il motore inietta `stream_id` e `seed` nel costruttore soltanto per le strategie registrate con il nome `stochastic`, e una strategia stocastica con un altro nome riceve soltanto le chiavi scritte nel blocco. Un intervento di struttura, invece, è l'aggiunta di un asse nuovo: non si esaurisce in una classe. Servono una riga nella tabella degli assi di `Stream`, un campo in `VoiceConfig`, uno slot nel `VoiceManager` e la riga di `_create_grain` che applica lo scarto al grano.


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


# Metodo di sviluppo

PGE è uno strumento per comporre, ma è anche un progetto software che dura da dieci mesi, con una storia da ricostruire. Il primo commit risale al 17 dicembre 2025 e l'ultimo, al momento della scrittura, al 13 ottobre 2026: 1 321 commit, trenta versioni rilasciate dalla 1.0.0 del 23 marzo alla 9.1.0 del 27 settembre. Il pacchetto conta circa 26 400 righe di Python, e la suite di test circa 86 800, con 164 file di test e circa 8 450 test eseguiti per default. Un rapporto di oltre tre righe di test per ogni riga di codice non è un vanto: è la conseguenza di un metodo, e questo capitolo lo descrive.

Una nota sul modo di lavorare precede il resto. Lo sviluppo è avvenuto in dialogo con un modello linguistico, Claude Code, che opera nel repository sotto la direzione dell'autore. Lo dichiara la storia stessa: 682 dei 1 321 commit portano Claude come autore. Il dialogo è reso possibile da una scelta del capitolo 3, la specifica in testo versionato, ed è regolato da un file di istruzioni (`CLAUDE.md`) che fissa il processo: la lingua, i test da superare prima di ogni commit, le analisi d'impatto, la forma delle pull request. Molte delle regole descritte qui nascono perciò da un bisogno preciso. Un collaboratore che non ricorda la sessione precedente ha bisogno che il metodo stia scritto nel repository, e un metodo scritto è anche un metodo verificabile da una macchina.

## Sviluppo guidato dai test

La regola di fondo è lo sviluppo guidato dai test, nel ciclo rosso-verde-refactor. Per una funzionalità nuova o per un cambio di comportamento si scrive prima il test e se ne verifica il fallimento, poi si scrive il codice che lo fa passare. Il codice di produzione e i suoi test non si scrivono nello stesso passo, e prima di cominciare si analizza l'impatto della modifica (chi importa il modulo, quali test lo coprono, che cosa potrebbe rompersi) e si discute il disegno. Prima di ogni commit, di ogni pull request e di ogni etichetta di versione la suite deve essere verde, e prima di una versione devono esserlo anche i test di integrazione.

La suite ha due strati, divisi da un marcatore. I test unitari e quelli tra componenti girano di default e sono veloci. I test *end-to-end* (marcati `e2e`) invocano `make` come lo invocherebbe chi usa il sistema, e coprono la catena completa: la cache incrementale, gli errori del motore, l'esportazione Reaper, il renderer NumPy, il backend SuperCollider. Richiedono i programmi esterni, e per questo sono esclusi dall'esecuzione predefinita.

### Test che sorvegliano l'architettura

Un progetto di questa durata non teme soltanto i difetti di comportamento. Teme anche che il disegno si degradi in silenzio, perché un'architettura regge finché nessuno la scavalca e la regola che la tiene in piedi è di solito soltanto una convenzione. Una parte della suite è scritta per trasformare in errore alcune convenzioni. Sono i test più caratteristici del progetto, e quattro esempi li descrivono.

**La sintassi di Csound sta in un modulo solo.** Un test legge come albero sintattico i moduli che non devono conoscere Csound (il grano, l'allocatore delle tabelle, il catalogo delle finestre) e fallisce se compare un letterale che apre una riga di score. È la regola descritta nel capitolo 3, e senza il test sarebbe un'intenzione.

**Il nome di un file di test è una promessa.** `tests/<area>/test_<modulo>.py` dice di sorvegliare `src/pge/<area>/<modulo>.py`. Un test del contratto della suite pretende che il file importi il modulo che nomina e che non ne riscriva le classi pubbliche. Il caso che l'ha fatto nascere è istruttivo. Un file di 72 test, intitolato a `Parameter`, in 63 casi collaudava una copia di `Parameter` riscritta nel file stesso. La riscrittura non fallisce mai, perché resta coerente con sé stessa anche il giorno in cui il modulo vero cambia comportamento. Chi modificava il modulo apriva quel file, leggeva decine di test sul comportamento di una classe che si chiamava allo stesso modo e li vedeva restare verdi. Il test del contratto è il rumore che mancava. Dichiara anche ciò che non dice: che il modulo sia *testato*. Importarlo è il minimo osservabile da un albero sintattico, e la lista dei file che fanno eccezione ne dichiara il debito invece di nasconderlo.

**Il sorgente resta leggibile dal Python più vecchio supportato.** Il progetto dichiara di funzionare da Python 3.9, ma nessuno lo sviluppa su quella versione. In locale si usa l'interprete corrente, e il rosso arriva solo dal lavoro più vecchio della matrice di integrazione, un'ora dopo, su una modifica che in locale era verde. Il caso è accaduto davvero: una guardia, scritta per tenere in piedi una regola, usava una sintassi di annotazione non valida per 3.9, e su quella versione il file non si importava. La guardia non falliva, semplicemente non esisteva più. Un test dedicato verifica ora il sorgente rispetto alla grammatica più vecchia.

**La superficie che altri repository leggono.** L'interfaccia grafica del motore, PGE-ui, ne legge parti in due modi: importa alcuni simboli, e di altri legge il sorgente come albero sintattico, senza importarlo. Un registro elenca i moduli, i nomi e i letterali che ciascuno legge e verifica che si risolvano ancora dove li si cerca. Non è una promessa di interfaccia pubblica: un nome che comincia con il carattere di sottolineatura resta privato, e il motore non si impegna a mantenerlo. Si impegna a non rinominarlo per sbaglio. Una rinomina voluta passa da lì, e l'elenco è la lista di che cosa aggiornare anche altrove.

### L'integrazione continua

Tre lavori girano a ogni modifica. Il primo esegue la suite unitaria su sei versioni di Python (da 3.9 a 3.14), con `pytest` chiamato direttamente invece di `make`, perché la ricerca dell'interprete del Makefile sceglierebbe sempre la stessa versione e la matrice non misurerebbe niente. Il secondo esegue i test di integrazione, con Csound e SuperCollider installati su una macchina pulita; l'installazione di SuperCollider è esplicita perché senza il programma il test del terzo backend si salterebbe, e un test che si salta non verifica niente. Il terzo controlla la documentazione, come mostra la sezione che segue. I campioni audio dei test non sono nel repository: li genera uno script versionato, così che chi lavora in locale abbia esattamente ciò che ha la macchina di integrazione.

## Documentazione e versionamento

### Quattro quadranti

La documentazione del motore segue la tassonomia Diátaxis [@procida2017diataxis]: quattro tipi di testo con funzioni diverse, che non vanno mescolati. Il repository ne usa tre. I testi di *riferimento* (`reference/`, tre documenti: la sintassi YAML, la riga di comando, gli errori) descrivono ciò che è stabile e si consultano. I testi *esplicativi* (`explanation/`, undici documenti) spiegano un'idea e le sue ragioni. Quelli di *procedura* (`how-to/`, undici) accompagnano un compito, per esempio aggiungere una finestra, una strategia di voce o un renderer. Mancano i tutorial.

La struttura è imposta. Ogni documento ha un'intestazione con il proprio tipo, lo stato (`stable`, `draft`, `deprecated`), l'elenco dei file di codice di cui parla e l'identificativo dell'ultimo commit in cui è stato verificato. Ogni tipo ha sezioni obbligatorie, nell'ordine: un documento esplicativo ha *Problema, Modello, Trade-off, Implicazioni codice, Vedi anche*. Chi legge i capitoli di questa tesina sul rendering o sul multi-voce riconosce quella struttura, perché ne sono la fonte. Un controllo automatico (`make docs-lint`) verifica che l'intestazione sia completa, che i file citati esistano, che l'identificativo del commit sia risolvibile nella storia, che i rimandi tra documenti puntino a documenti reali e che nessun documento sia orfano. È il modo in cui la documentazione smette di essere un'affermazione e diventa un oggetto verificabile. Se un file di codice citato sparisce, il controllo fallisce, e il documento non può più restare silenziosamente fermo a una realtà passata. L'indice è generato, non scritto a mano; il controllo di integrazione verifica che sia aggiornato, e un gancio pre-commit lo rigenera.

### Piani, changelog, versioni

I lavori di una certa taglia cominciano con un piano in `docs/plans/`. Quando il lavoro finisce, il piano passa a `docs/plans/done/` e resta come archivio; se introduce una funzione stabile, la sua parte duratura si estrae nel documento di riferimento o esplicativo giusto. Ventidue piani chiusi documentano le decisioni dalle prime scelte sul formato audio al rendering parallelo, dalla riorganizzazione della documentazione alla direzione di lettura dichiarata. Un piano dice che cosa si è deciso *prima* di scrivere il codice, e un documento esplicativo dice che cosa è rimasto vero *dopo*.

Le modifiche si registrano in un changelog nel formato Keep a Changelog [@lacan2017changelog], con una sezione per versione e le voci raggruppate per categoria. Le versioni seguono il versionamento semantico [@prestonwerner2013semver]: il numero maggiore cambia per modifiche incompatibili, il minore per funzioni retrocompatibili, la patch per correzioni. Le versioni principali portano anche un nome: *Range Anchor* (6.0.0), *Deviation Probability* (7.0.0), *Declared Reverse* (7.3.0), *Timeline Origin* (8.0.0), *Third Backend* (9.0.0, l'arrivo di SuperCollider), *Quiet Stdout* (9.1.0). La procedura di rilascio è un comando che controlla di essere su `main`, esegue tutti i test compresi quelli di integrazione, chiede il numero e il nome, crea un'etichetta annotata e mostra le modifiche dall'ultima. Non pubblica l'etichetta senza conferma. La versione descritta in questa tesina è archiviata con un identificativo permanente [@DeMattia2026Pge].

### Le pull request

Il processo si conclude con un'unità di lavoro, la pull request, che il repository descrive con una regola di forma. Il corpo comincia con una riga in inglese che dichiara l'issue chiusa (`Closes #N`), perché è l'unica cosa che GitHub legge per chiudere l'issue quando il lavoro entra in `main`. La regola nasce da un errore reale: una pull request aveva scritto «Chiude #219», in italiano, che non chiude niente, ed è stata unita con l'issue ancora aperta. Seguono tre sezioni (che cosa cambia, come si è verificato, che impatto ha sugli altri repository). L'impatto è obbligatorio e va dichiarato repository per repository, anche quando è nullo, perché la copertura di uno non implica quella degli altri.

Un controllo automatico verifica la riga, e una regola del repository impone che quel controllo sia verde sul ramo principale. Le due metà sono separate per una ragione che vale la pena di notare: le regole dei rami non sanno leggere il corpo di una pull request, e quindi il lavoro di integrazione *misura* e la regola del ramo *pretende*. Il controllo è più rigido di GitHub, mai più largo: se passa, GitHub collega; il guasto che non si vede sarebbe il contrario.

Lo stesso spirito si estende oltre il repository. Il motore è incluso come sottomodulo di git nel repository del paper, a un commit fisso, e ne rigenera gli esempi. Quando il motore avanza, una regola chiede se aggiornare il puntatore, e la risposta non è automatica: alcune modifiche non toccano gli esempi.

## Il language server PGE-ls

Un linguaggio dichiarativo si scrive meglio con un editor che lo capisce. PGE-ls è un *language server* per lo YAML di PGE, secondo il Language Server Protocol [@microsoft2016lsp]: un processo che l'editor interroga e che risponde con completamenti, descrizioni e diagnosi. Si attiva sui file `PGE_*.yaml` e fornisce completamento delle chiavi e dei valori, descrizioni al passaggio del cursore, diagnosi degli errori, modelli per gli inviluppi e la navigazione verso i file audio citati. Ha client per VSCode (un'estensione) e per Neovim, ed è un repository a sé, con 77 commit e circa 11 000 righe di Python.

L'architettura è semplice. Un server (con la libreria `pygls`) riceve il testo del documento a ogni richiesta e lo passa a tre fornitori senza stato (completamento, descrizione, diagnosi). Tutti si appoggiano a un analizzatore YAML *tollerante*, che non solleva mai eccezioni su un documento incompleto, perché un testo in scrittura è quasi sempre incompleto. La conoscenza dello schema (che parametri esistono, in che intervallo, quali si escludono a vicenda) viene da un unico ponte verso il motore. Il ponte funziona in due modi: importa lo schema dal motore vivo, in sviluppo, oppure legge una copia congelata in un file JSON, in distribuzione, dove il pacchetto dell'estensione non può contare sul motore.

Un esempio di diagnosi mostra che cosa il server sa. Dato questo documento:

```yaml
streams:
  - stream_id: prova
    onset: 0
    sample: voice.wav
    density: 40
    fill_factor: 2
    grain:
      duration: 0.05
    pitch:
      semitones: 80
```

il server segnala tre problemi, qui riportati abbreviati e con a capo aggiunti:

```
6  Warning  Exclusive group 'density_mode': 'fill_factor' ha priorita'
            e sara' usato. Rimuovere gli altri: density.
5  Warning  Exclusive group 'density_mode': 'density' verra' ignorato
            perche' 'fill_factor' ha priorita' piu' alta.
10 Error    'pitch.semitones': valore 80.0 fuori range [-36, 36].
```

Le due segnalazioni di gruppo esclusivo dicono la stessa cosa, dai due lati: `density` e `fill_factor` sono due modi di specificare la stessa grandezza (capitolo 5), e quando ci sono entrambi il motore ne usa uno e ignora l'altro. Il server avverte della scelta, perché è sospetta ma non è un errore. Il valore fuori dall'intervallo del pitch è invece un errore: il motore lo rifiuterebbe.

### Il costo di avere due repository

Il language server è anche un caso di studio sul costo del disegno dichiarativo. Il server contiene alcune parti del motore *copiate a mano*: i nomi delle strategie di voce, gli accordi, i limiti delle unità di altezza, i nomi delle finestre. Sono copie statiche, perché non sempre si può importare lo schema dal motore, e una copia può divergere dall'originale senza che nessun altro test se ne accorga: la suite normale verifica i valori ricopiandoli nelle prove, non importandoli dal motore.

Il rimedio è un test di *parità*. Importa il sorgente vero del motore e lo confronta con le copie. Se il motore non c'è, il test si salta in locale; sulla macchina di integrazione il repository del motore viene clonato e il test gira davvero. Nel suo commento sono elencati tre scarti che avrebbe trovato: tre strategie di pan rinominate nel motore e non nel server, un limite minimo del rapporto di altezza passato da 0,125 a 0,001, un alias di finestra (`triangle`) assente dal server. Ciascuno era un errore silenzioso: il server avrebbe dichiarato errore su YAML validi, o taciuto su YAML sbagliati.

Anche il test di parità ha un limite, e conviene dichiararlo. Copre le superfici che si è deciso di elencare, e non le altre. Un esempio, rilevato scrivendo questo capitolo: il server segnala come mancante il campo `onset` di uno stream, mentre il motore lo tratta come facoltativo, e uno stream senza `onset` comincia a tempo zero. Nessun elenco di parità lo includeva. Il difetto è reale e minore: un avviso in più su un file valido. Mostra, però, il principio che regge il metodo di questa sezione. Una regola scritta ma non verificata invecchia, e il costo del disegno dichiarativo è mantenere allineati gli strumenti che lo leggono. Per questo il repository del motore ha una regola, già vista, che chiede a ogni modifica della superficie pubblica di dichiarare l'impatto su ciascuno dei tre repository che la leggono, e ne apre uno specifico per ciascuno.


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
- La resa nello spazio: il pan di 360 gradi è oggi scritto per una coppia stereo, perché i tre renderer sono stereofonici: il grano porta soltanto un angolo, e non vincola il numero di canali.

<!-- TODO(giulio): aggiornare questo elenco con lo stato reale al momento della consegna (26/10/2026) e aggiungere, se vuoi, un ascolto guidato o una MAP di un passaggio del brano. Una MAP dell'intero brano non è praticabile: sono 3,3 milioni di grani su dieci stream. Una pagina breve di MAP, su un passaggio a scelta, lo è. -->


# Conclusioni e sviluppi futuri

## Che cosa ho fatto

Ho descritto Python Granular Engine nella versione 9.1.0 [@DeMattia2026Pge]. Il problema è quello classico della sintesi granulare: una popolazione di migliaia di grani al secondo non si specifica grano per grano, e chi compone ha bisogno di descriverne il comportamento collettivo senza perdere la possibilità di risalire dall'esito ai parametri che lo hanno prodotto (capitolo 2). La risposta di PGE ha tre parti. La prima è un linguaggio dichiarativo in YAML, in cui ogni parametro è un valore centrale che varia nel tempo e una banda di variazione, la maschera di tendenza di Truax in forma testuale (capitolo 4). La seconda è la lista dei grani, una rappresentazione intermedia che fissa che cosa suonare senza dire come lo scrive un programma di sintesi (capitoli 3 e 5), e che il motore moltiplica in voci parallele (capitolo 6). La terza è l'insieme dei suoi consumatori: tre renderer, Csound, NumPy e SuperCollider, che la trasformano in audio (capitolo 7), la MAP, che la trasforma in un'immagine, e tre esportazioni, verso Reaper, Sonic Visualiser e JSON (capitolo 8). Lo strumento è sviluppato con test, documentazione verificata da controlli automatici e versionamento (capitolo 9).

Il disegno regge su due scelte che ritrovo in ogni capitolo. La prima è la separazione fra generazione e rendering, e quindi fra il compositore e il programma di sintesi: aggiungere un renderer, una finestra o una strategia non richiede di toccare il nucleo, e l'esistenza di tre renderer indipendenti rende il rendering falsificabile. La seconda è la riproducibilità: la specifica con il seme dichiarato è il documento che si conserva, e l'audio si rigenera da essa. Il tempo differito, che è la ragione per cui ho scritto lo strumento, ha consentito densità e numeri di voci che il tempo reale non offre.

## Che cosa ne è uscito

Dal punto di vista musicale posso dichiarare solo ciò che è verificabile. Il primo esito è una raccolta di esempi (cartella `esempi/`), ciascuno dei quali isola un meccanismo e ne mostra l'effetto con la MAP: sono il materiale su cui è costruita la tesina. Il secondo è *mare-nostrum*, il brano con i lamenti e i pianti di bambini trasformati in suono di mare, che è incompiuto. Ne esistono uno schizzo di 322 secondi, con otto stream attivi e circa 3,3 milioni di grani, e un laboratorio di studi sui parametri, costruito sopra PGE, che finora ha una sessione di ascolto documentata. Non ho ancora un brano concluso da presentare, e nessuno ha usato lo strumento oltre a me. Non posso dunque dire se le scelte di PGE, in particolare la lettura psicoacustica dei parametri e la MAP come strumento di verifica, reggano fuori dal mio lavoro.

## Limiti

Restano quattro limiti, che non ho colmato.

Il sistema governa il materiale per posizione di lettura e non per contenuto: non sa nulla del timbro di ciò che granula. Gli assi di controllo sono indipendenti per costruzione, dall'ampiezza e dalla probabilità della deviazione alle quattro strategie delle voci, e nessuno dichiara come covariano fra loro. La MAP affida l'altezza al colore. Il preset in bianco e nero (capitolo 8) restituisce il segno della trasposizione con la luminanza, e risponde al problema della stampa, ma l'altezza resta codificata in un solo canale. Infine i renderer producono oggi file stereofonici (il grano ha un pan in gradi, che non impone il numero di canali, ma non esiste un renderer multicanale).

## Sviluppi futuri

Ai primi due limiti corrispondono due direzioni di sviluppo: una libreria di descrittori del materiale, come il centroide spettrale e l'energia, per guidare i parametri sul timbro invece che sulla sola posizione, e la possibilità di dichiarare nella specifica come i parametri covariano, invece di lasciarli indipendenti. Truax prevedeva sistemi di controllo complessi, a più livelli di decisione, e modelli matematici che descrivono il comportamento di grandi masse di unità cellulari [@Truax1988, p. 25]. Un processo dichiarativo che generi intere popolazioni di stream, invece di scriverne uno alla volta, ne è la continuazione. Il laboratorio di *mare-nostrum*, con gli studi che variano due parametri su una griglia, è un primo passo in quella direzione. Resta poi da fare ciò che la tesina non fa: una valutazione condotta con altri compositori.

Il progetto che mi sta più a cuore è PGE-ui, un'interfaccia grafica per lo YAML di PGE che sviluppo in un repository a parte. È un editor nel browser, collegato al motore da un piccolo ponte locale, in cui ogni stream è una clip su una traccia di una timeline. Gli inviluppi si disegnano, le voci e gli altri parametri si regolano in un pannello, e il rendering lancia il motore, mostra l'avanzamento e permette di ascoltare gli stem sulla timeline, con annulla e ripristina. Per questo la chiamo, con una certa libertà, la DAW di PGE. Non è una DAW nel senso tradizionale: non registra né modifica l'audio, e quello che modifica è il documento YAML, da cui l'audio deriva. La specifica resta dunque l'unico documento, e l'interfaccia grafica e il testo si possono usare sullo stesso file. È il modo in cui voglio rendere più diretta la scrittura, mantenendo ciò che per me conta di più nel metodo: un documento testuale che si versiona e un rendering che si rigenera.


# BIBLIOGRAFIA

::: {#refs-bib}
:::

# DISCOGRAFIA

::: {#refs-dis}
:::

# SITOGRAFIA

::: {#refs-sit}
:::

