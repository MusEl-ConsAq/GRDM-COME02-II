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
