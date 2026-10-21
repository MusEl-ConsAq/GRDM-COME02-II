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
