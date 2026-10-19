# Il grano e lo stream

Il capitolo precedente ha descritto il linguaggio con cui si dichiara uno stream. Questo descrive che cosa quel linguaggio governa: il grano, la sua durata e la sua forma, la regola con cui i grani si susseguono nel tempo, il punto del materiale da cui sono letti, la loro altezza e la parte che il caso ha nella loro distribuzione. L'ordine è quello dell'esposizione per scostamenti del paper presentato al XXV CIM [@DeMattia2026Cim]: i parametri vengono introdotti uno alla volta, e per ciascuno si mostra la MAP di un esempio che lo isola. I listati degli esempi stanno nella cartella `esempi/` del repository della tesina, e le MAP si rigenerano da quei file.

## Il grano come dato immutabile

Il grano è l'oggetto che il motore produce e che i renderer consumano. Come si è visto, è un dato immutabile con otto campi. La tabella associa ciascun campo alla parte del linguaggio che lo determina.

| Campo del grano | Da che cosa dipende |
|-----------------|---------------------|
| istante di inizio (*onset*) | densità e distribuzione, nelle sezioni seguenti |
| durata | `grain.duration` |
| posizione di lettura | blocco `pointer` |
| rapporto di altezza (il suo segno porta il verso di lettura) | blocco `pitch` e `grain.read_direction` |
| volume | `volume`, in decibel |
| pan | `pan`, in gradi |
| tabella del campione | `sample` |
| tabella della finestra | `grain.envelope` |

La durata del grano è in secondi per impostazione predefinita (0,05 s). Con `grain.duration_unit` si può dichiararla in millisecondi o in campioni, alla frequenza di uscita del motore; la conversione avviene alla lettura del file e vale per i valori fissi e per gli inviluppi. Il millisecondo è la scala comoda per la granulazione udibile, dove in secondi si scriverebbero soltanto numeri molto piccoli. La banda di variazione della durata può essere assoluta, oppure relativa: in questo caso `duration_range` è una frazione della durata corrente, istante per istante, e quindi non dipende dall'unità in cui la durata è scritta.

Il pan merita una nota. L'angolo `pan` muove il grano lungo una circonferenza unitaria in codifica Mid-Side, la matrice di Blumlein [@Blumlein1931]. Mid e side sono due microfoni a figura otto ortogonali, le proiezioni coseno e seno del grano lungo la circonferenza [@Gerzon1975]; sinistra e destra sono la stessa coppia ruotata di 45 gradi, e non l'unico esito possibile. Con un'altra matrice si ottengono microfoni virtuali verso un numero qualsiasi di altoparlanti, perché il motore non vincola il numero di canali di uscita: la coppia stereo è il valore predefinito. La posizione nel campo sonoro è dunque un attributo del singolo grano, parte della costruzione dello strumento, e non un effetto di spazializzazione aggiunto in fondo alla catena.

La figura seguente mostra una texture in cui più dimensioni del grano variano insieme (`esempi/duration/duration.yml`): la durata scende da 50 a circa 1 millisecondo a metà dello stream e risale a 150, mentre densità, distribuzione, pan e banda del pan si muovono con andamenti propri. La lente ingrandisce l'istante di durata minima, illeggibile a piena scala.

![Una texture in cui durata del grano, densità, distribuzione e pan variano insieme. Il colore dei grani indica lo scarto di altezza; in basso gli inviluppi dei parametri.](docs/images/duration_map.pdf){width=100%}

## Densità e distribuzione temporale

L'intervallo fra due onset successivi si chiama *inter-onset time* (IOT). Due parametri lo governano: la densità (`density`), in grani al secondo, che ne fissa il valore medio, $\mathrm{IOT}_{\mathrm{avg}} = 1/\mathit{density}$, e la distribuzione (`distribution`), che stabilisce quanto gli intervalli siano regolari.

In alternativa alla densità si può dichiarare il *fill factor* (`fill_factor`), che ha la priorità se presente. Il fill factor di Roads è il prodotto della densità per la durata del grano: a valore 1 i grani sono adiacenti, sotto 1 sono radi, sopra 1 si sovrappongono [@Roads2001, pp. 105-106]. Dichiararlo al posto della densità rende la densità dipendente dalla durata del grano, e la sovrapposizione resta costante anche quando la durata varia. Non esiste un limite superiore alla densità; il limite inferiore, 0,01 grani al secondo, esiste perché l'intervallo medio è il suo inverso, e una densità nulla sarebbe una divisione per zero.

La distribuzione è un numero fra 0 e 1. Il termine *sincrono* va inteso nel senso di Roads [@Roads2001, p. 93]: il grado di regolarità degli intervalli. Nella sintesi granulare sincrona i grani si susseguono a intervalli regolari. In quella quasi-sincrona un fattore di deviazione casuale ne determina l'irregolarità, e quando l'irregolarità è grande il risultato si avvicina alla sintesi asincrona. Non è il senso, pure corrente nella letteratura, di sintesi *pitch-synchronous*, in cui la sincronia è con il periodo della forma d'onda e serve a fissare l'altezza [@DePoliPiccialli1988].

Con $d$ uguale a `distribution`, l'intervallo è

$$\mathrm{IOT}(d) = (1-d)\,\mathrm{IOT}_{\mathrm{avg}} + d\,\mathcal{U}\!\left(0,\, 2\,\mathrm{IOT}_{\mathrm{avg}}\right), \qquad d \in [0,1]$$

dove $\mathcal{U}$ è il campionamento uniforme. L'espressione è una combinazione convessa. A $d = 0$ ogni intervallo vale $\mathrm{IOT}_{\mathrm{avg}}$: la griglia è metronomica e l'emissione sincrona. A $d = 1$ l'intervallo è estratto da una distribuzione uniforme fra 0 e il doppio del valore medio: l'emissione è asincrona. I valori intermedi sono il regime quasi-sincrono. Il parametro accetta un inviluppo, quindi lo stream può passare dall'uno all'altro regime nel tempo.

L'esempio che segue (`esempi/distribution/distribution.yml`) lascia ferma la lettura su un punto del file, per vedere soltanto la griglia di emissione. La densità sale da 10 a 200 grani al secondo e ridiscende; la distribuzione resta a zero fino a circa 6 secondi e poi sale a 1, per ritornare a zero.

```yaml
density: {type: cubic, points: [[0, 10], [0.5, 200], [1, 10]]}
pointer:
  speed_ratio: 0.0
  start: 0.5
  loop_unit: normalized
distribution: {type: cubic, points: [[0.3, 0], [.75, 1], [1, 0]]}
```

![Passaggio da emissione sincrona ad asincrona su lettura ferma. Nella prima lente gli onset sono equispaziati, nella seconda irregolari.](docs/images/distribution_map.pdf){width=100%}

La differenza si sente oltre che vedersi. Quando la griglia è sincrona e la densità è alta, l'emissione periodica di grani identici produce uno spettro a righe, spaziate a multipli della densità [@Roads2001Pulsars]. Quando la distribuzione sale verso 1 gli istanti di emissione si irregolarizzano e le righe si smerigliano in una banda.

## Il puntatore: lettura del campione, loop e verso di lettura

Il blocco `pointer` governa il punto del materiale da cui ciascun grano legge. Il capitolo precedente ha mostrato che la posizione di lettura è l'integrale di `speed_ratio`, il rapporto tra la velocità del puntatore e quella del tempo dello stream: a 1 il puntatore percorre il file alla velocità naturale, a 0 si ferma, a valori negativi va all'indietro. La posizione iniziale è `start`, in secondi, ed è un valore fisso, non un inviluppo, perché viene sommata alla posizione calcolata e non valutata nel tempo.

### Il loop

Il puntatore può essere confinato in una finestra del file, il *loop*. Si dichiara con `loop_start`, l'inizio, e con la fine scelta in due modi alternativi: `loop_end`, un istante, oppure `loop_dur`, una durata. L'inizio e la durata o la fine accettano inviluppi, e la finestra può dunque muoversi nel file. La chiave `loop_unit` fissa l'unità di tutte le posizioni nel campione, `start` compreso: secondi (il caso predefinito) oppure valori normalizzati fra 0 e 1, scalati sulla durata del file. Questa unità è indipendente dal modo in cui si misura il tempo degli inviluppi: sono due assi diversi, quello del tempo dello stream e quello della posizione nel file.

Un loop può anche attraversare la fine del file, e lo si esprime soltanto con `loop_dur`: se inizio e durata superano la lunghezza del campione, la finestra riprende dall'inizio.

Ai grani può essere assegnata una deviazione di posizione con `offset_range`, la larghezza della banda attorno alla posizione calcolata. La posizione finale di ciascun grano, quella base più la deviazione, è confinata nella finestra del loop con un'operazione modulare: i grani leggono soltanto da dentro la finestra. Senza loop la finestra coincide con l'intero file.

L'esempio (`esempi/loop/loop.yml`) muove una finestra di 0,2 volte la durata del file dall'inizio del file verso la fine, con la lettura a velocità naturale. Dopo metà dello stream la deviazione cresce fino a 0,5.

```yaml
pointer:
  loop_unit: normalized
  speed_ratio: 1.0
  loop_start: [[0, 0.1], [1, 0.6]]
  loop_dur: 0.2
  offset_range: [[0, 0], [0.5, 0], [1, 0.5]]
```

![La finestra di loop, in colore, scorre nel file. Il puntatore la percorre e, raggiunta la fine, ricomincia dall'inizio della finestra; dopo metà dello stream i grani si disperdono dentro la finestra.](docs/images/loop_map.pdf){width=100%}

### Il verso di lettura

Tre grandezze diverse riguardano la direzione e vanno tenute distinte.

| Grandezza | Che cosa governa | Valori |
|-----------|------------------|--------|
| `pointer.speed_ratio` | velocità e verso con cui la testina percorre il file | negativo: all'indietro |
| `grain.read_direction` | verso con cui il singolo grano legge il materiale | $-1$ indietro, $+1$ avanti |
| blocco `pitch` | altezza percepita | sempre positivo, per costruzione |

Se non si dichiara nulla, il verso del grano segue il segno di `speed_ratio`: quando la testina va all'indietro, anche la lettura dentro ogni grano si inverte. Una chiave alternativa, `grain.reverse`, forza l'inversione per tutti i grani. `read_direction` è invece dichiarativa e indipendente dalla testina, e accetta un inviluppo (con interpolazione a gradini, imposta, perché il verso non ha valori intermedi). Dichiararla insieme a `reverse` è un errore, perché le due chiavi governano la stessa grandezza con semantiche opposte, e sceglierne una in silenzio nasconderebbe l'errore invece di segnalarlo.

L'esempio (`esempi/read_direction/read_direction.yml`) tiene costante la velocità della testina, che avanza nel file per tutta la durata dello stream, e inverte il verso dei grani fra 4 e 6 secondi.

```yaml
grain:
  duration: 0.12
  read_direction: [[0, 1], [0.5, -1], [0.75, 1]]
pointer:
  speed_ratio: 0.25
```

![La testina avanza sempre, ma fra 4 e 6 secondi i grani leggono all'indietro: la testa del grano si capovolge. Le lenti mostrano un grano in lettura diretta e uno in lettura inversa.](docs/images/read_direction_map.pdf){width=100%}

## Altezza e unità di pitch

Il blocco `pitch` governa la trasposizione del grano. Funziona per unità: ogni unità di misura è una voce del linguaggio, e in un blocco se ne dichiara una sola. Più unità insieme sono un errore, perché non c'è una priorità implicita; lo stesso vale per una chiave sconosciuta, come `semitone` al posto di `semitones`, che non viene ignorata ma segnalata. Senza alcuna unità il valore predefinito è zero semitoni, cioè il rapporto 1.

| Chiave | Unità | Divisioni dell'ottava | Limiti |
|--------|-------|-----------------------|--------|
| `semitones` | semitoni | 12 | da $-36$ a 36 |
| `quarter_tone` | quarti di tono | 24 | da $-72$ a 72 |
| `eighth_tone` | ottavi di tono | 48 | da $-144$ a 144 |
| `cents` | cent | 1200 | da $-3600$ a 3600 |
| `edo` con `value` | divisione arbitraria dell'ottava | $N$ | da $-3N$ a $3N$ |
| `ratio` | rapporto diretto | non applicabile | da 0,001 a 8 |

Le unità della famiglia EDO (*equal division of the octave*) si convertono nel rapporto di trasposizione con $2^{v/N}$, dove $v$ è il valore e $N$ il numero di divisioni dell'ottava. `ratio` è invece un moltiplicatore diretto. L'unità `edo` apre a scale arbitrarie: `edo: 31` con `value: 18` dichiara diciotto gradi di una scala a trentuno divisioni. Come per ogni parametro, il valore può essere un inviluppo, e la banda di variazione `range` è espressa nella stessa unità, con passi interi sulla griglia scelta.

L'esempio (`esempi/pitch/pitch.yml`) lascia ferma la lettura e porta la trasposizione a gradini: 0, 7, $-5$ e 12 semitoni.

```yaml
pitch:
  semitones: {type: step, points: [[0, 0], [0.25, 7], [0.5, -5], [0.75, 12]]}
```

![La trasposizione a gradini su lettura ferma. Il colore dei grani codifica l'altezza, in cent rispetto al suono originale; in basso l'inviluppo dei semitoni.](docs/images/pitch_map.pdf){width=100%}

## Le finestre del grano

La finestra è l'inviluppo di ampiezza che dà forma al grano. Finestrare un grano ne modula l'ampiezza e aggiunge allo spettro bande laterali [@Roads2001]; la scelta della forma è quindi anche una scelta timbrica. Nel linguaggio la finestra si dichiara con la chiave `grain.envelope`, che non va confusa con gli inviluppi dei parametri, trattati nel capitolo precedente.

Il catalogo comprende finestre simmetriche (Hann, che è la predefinita, Hamming, Bartlett, Blackman, Blackman-Harris, gaussiana, Kaiser-Bessel, rettangolare, sinc), una semi-sinusoide e un gruppo di finestre asimmetriche a decadimento o a salita esponenziale (`expodec`, `exporise`, e le versioni forte e inversa di ciascuna). La parola `all` le comprende tutte.

Le modalità di dichiarazione sono quattro.

- **Una finestra sola**, per nome.
- **Una lista di finestre**, fra cui il motore sceglie a caso per ogni grano.
- **Una transizione** da una finestra a un'altra, governata da una curva da 0 a 1: a 0 tutti i grani hanno la prima finestra, a 1 tutti la seconda, e nei valori intermedi la scelta è probabilistica.
- **Un percorso a più stati**, che generalizza la transizione a una sequenza di finestre collocate sull'asse della curva.

```yaml
grain:
  envelope:
    states: [[0, hanning], [0.5, rexpodec], [1, bartlett]]
    curve: [[0, 0], [1, 1]]
```

Nell'esempio (`esempi/window/window.yml`) la finestra attraversa tre stati, a densità bassa perché le forme siano distinguibili: Hann, poi la finestra esponenziale inversa, poi Bartlett.

![Il glifo del grano è la sagoma della sua finestra. Le tre lenti ingrandiscono tre istanti: all'inizio i grani sono finestrati con Hann, a metà con la finestra esponenziale, in chiusura con Bartlett.](docs/images/window_map.pdf){width=100%}

## La variazione stocastica

I parametri di un grano non sono tutti decisi dal compositore uno per uno: sarebbe la specifica grano per grano che il capitolo precedente dichiarava intrattabile. La parte del caso è dichiarata a due livelli. Ogni parametro ha una traiettoria centrale, un inviluppo, e una banda di deviazione attorno a quella traiettoria, `_range`, da cui si estrae un valore diverso per ogni grano. È la tendency mask di Truax [@Truax1988], realizzata in forma testuale anche da CMask [@Bartetzki1997]. Con $c(\tau)$ la traiettoria centrale, $\rho(\tau)$ la larghezza della banda e $\xi_n$ un valore uniforme fra $-1/2$ e $1/2$, il parametro del grano $n$ al tempo normalizzato $\tau_n$ è

$$v_n = c(\tau_n) + \xi_n\,\rho(\tau_n), \qquad \xi_n \sim \mathcal{U}\!\left(-\tfrac{1}{2}, \tfrac{1}{2}\right)$$

Il sistema aggiunge un terzo livello: la probabilità, variabile nel tempo, che la deviazione si applichi. Un *gate* probabilistico decide, grano per grano, se il grano segue la traiettoria o subisce la deviazione:

$$v_n = c(\tau_n) + g_n\,\xi_n\,\rho(\tau_n), \qquad g_n \sim \mathrm{Bernoulli}\!\big(p(\tau_n)\big)$$

dove $p(\tau)$ è la probabilità, anch'essa un inviluppo. Con $p$ sempre uguale a 1 il gate è sempre aperto e l'espressione si riduce alla precedente. La differenza è il fattore $g_n$, che rende l'ampiezza della deviazione, $\rho$, e la sua probabilità, $p$, due dimensioni di controllo indipendenti. La chiave che le dichiara è `deviation_probability`.

Nelle fonti consultate non si trova un precedente diretto del gate come asse dichiarabile e componibile nel tempo. Il più vicino è nell'ICMS, dove alcune trasformazioni del grano (lettura retrograda, inversione di fase, ripetizione) si applicano a circa metà dei grani per decisione di un generatore casuale [@DiScipioTisato1993cim]: la probabilità è però fissa e non dichiarata, e governa interruttori discreti, non l'applicazione di una maschera a un parametro continuo. Per forma è più vicina l'*intermittency* di EmissionControl2, un gate per grano dichiarabile e modulabile con continuità [@Roads2021]; ma decide se il grano viene emesso e agisce quindi sulla densità. Nel linguaggio qui descritto il grano resta, e il gate decide se applicargli la deviazione.

L'indipendenza dei due assi si vede in due stream che condividono la stessa traiettoria, una lettura ferma, e la stessa ampiezza massima di deviazione (`esempi/deviation/deviation.yml`). Nel primo cresce l'ampiezza della deviazione, nel secondo la probabilità.

![Due modi di aprire la deviazione, a parità di traiettoria e di ampiezza massima. Pannello superiore: l'ampiezza cresce da 0 a 0,35 con il gate sempre aperto, e i grani riempiono uniformemente uno spazio di lettura che si allarga a cuneo. Pannello inferiore: l'ampiezza è costante e cresce la probabilità da 0 a 100%; la linea si trasforma in nuvola, passando da grani fedeli a grani devianti.](docs/images/deviation_map.pdf){width=100%}

### Come si dichiara la probabilità

`deviation_probability` accetta più forme. Un numero da 0 a 100 vale per tutti i parametri; un inviluppo lo fa variare nel tempo; un dizionario assegna una probabilità per parametro (`volume`, `pan`, `duration`, `pitch`, `pointer`, `reverse`, `read_direction`, `envelope`), e ciascuna può essere a sua volta un inviluppo.

Vale una regola che conviene conoscere. In modalità per parametro, un parametro assente dal dizionario non riceve probabilità: se ha un `_range` dichiarato lo applica sempre, a tutti i grani, e se non ce l'ha resta fermo. Nel dizionario si dichiarano quindi soltanto i parametri di cui si vuole *ridurre* la probabilità. Nella modalità globale invece un'unica probabilità vale per tutti i parametri.

```yaml
# solo il volume è ridotto al 30%; gli altri parametri con un _range lo applicano sempre
deviation_probability:
  volume: 30
```

Resta un caso che ha sorpreso più volte e che il progetto ha fissato con un test. Esistono cinque modi di scrivere la chiave senza assegnarle un valore, e quattro danno lo stesso risultato: nessuna deviazione. Lo danno l'omissione della chiave, `false`, `{}` e un parametro dichiarato `null`. Fa eccezione la chiave scritta e lasciata vuota, `deviation_probability:`, che in YAML vale `null` e attiva la modalità implicita: una probabilità dell'1% di deviare, per ogni parametro, con un'ampiezza predefinita. Misurata su uno stream di 79 grani, la chiave vuota ne devia uno, le altre quattro scritture nessuno. Quella che più somiglia a "non voglio deviazione" fa dunque l'opposto; per disattivare si scrive `false` o si omette la chiave.

### Il jitter implicito

Se si dichiara una probabilità senza un `_range` esplicito, il motore applica una deviazione predefinita, la cui ampiezza dipende dal parametro.

| Parametro | Jitter implicito |
|-----------|------------------|
| volume | ±1,5 dB |
| pan | ±15 gradi |
| durata | ±5 ms |
| lettura | ±2,5% del file |
| altezza | ±12 cent |
| verso | inversione discreta |

Quella microvariazione è la decorrelazione di cui parla Vaggione, che rende una massa granulare più organica e meno meccanica [@Vaggione2002]. Per l'altezza il detune implicito è continuo e si applica dopo la quantizzazione sulla griglia dell'unità scelta; con un `range` dichiarato, anche nullo, non si applica e vale la variazione quantizzata dichiarata.

Nell'esempio (`esempi/probability/probability.yml`) la sola `deviation_probability` sale a gradini da 0 a 100%, senza alcun `_range` dichiarato.

```yaml
grain:
  duration: 0.02
deviation_probability: {points: [[0, 0], [.2, 25], [.4, 50], [.6, 75], [.8, 100]], type: step}
```

![La sola probabilità sale a gradini. Nel primo tratto i grani sono allineati sulla traiettoria; a ogni gradino una quota maggiore se ne discosta, per effetto del jitter implicito (il colore dei grani indica lo scarto di altezza). Nella legenda, la percentuale accanto al nome di un parametro è la probabilità che la deviazione sia applicata, non la sua ampiezza.](docs/images/probability_map.pdf){width=100%}
