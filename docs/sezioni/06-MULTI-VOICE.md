# L'architettura multi-voce

Finora lo stream è stato una voce sola. PGE ne prevede $N$, e il modello è quello delle voci parallele del DMX-1000 di Truax [@Truax1988]: uno stream si sdoppia in più voci, ciascuna con scarti propri rispetto a una voce di riferimento. Questo capitolo descrive come le voci si costruiscono, quali scarti si possono assegnare e in che modo il loro numero e il loro grado di indipendenza varia nel tempo. È l'ultimo scostamento dell'esposizione del paper [@DeMattia2026Cim]: dopo la risintesi, la posizione di lettura, la griglia, il grano e la deviazione, si moltiplica lo stream di partenza.

## Voci come moltiplicazione dello stream

Aggiungere voci vuol dire inserire scostamenti ulteriori in alcuni parametri dello stream. La scala degli scarti decide che cosa si ascolta. Scarti di pochi millesimi di secondo restano un attributo spaziale: la massa si ispessisce e acquista direzione [@Vaggione2002]. Oltre i cinquanta millisecondi i grani si separano in eventi distinti [@Truax1988, p. 18], e lo stesso meccanismo produce polifonia. Il sistema non distingue i due regimi: sono lo stesso strumento a scale diverse.

Gli assi su cui una voce può scostarsi sono quattro, ciascuno governato da una strategia intercambiabile dichiarata per nome nel blocco `voices`.

| Asse | Unità dello scarto | Effetto |
|------|--------------------|---------|
| `pitch` | semitoni (o un'altra unità) | trasposizione della voce |
| `onset_offset` | secondi | ritardo di ingresso della voce |
| `pointer` | secondi nel file, o frazione del file | posizione di lettura della voce |
| `pan` | gradi | posizione della voce nel campo sonoro |

```yaml
voices:
  num_voices: 4
  scatter: 0.0
  pitch:        {strategy: ..., ...}
  onset_offset: {strategy: ..., ...}
  pointer:      {strategy: ..., ...}
  pan:          {strategy: ..., ...}
```

I quattro assi sono ortogonali: ciascuno ha la propria strategia, e qualunque combinazione è valida. Il parametro di ogni strategia è un valore fisso o un inviluppo, quindi uno scarto può variare nel tempo: un cluster può aprirsi in un ventaglio.

La voce 0 è sempre il riferimento. Non riceve scarti da nessuna strategia, ed è l'invariante che ogni strategia nuova deve rispettare. Anche le altre regole sono vincoli di costruzione: gli scarti di onset non sono mai negativi, quindi le voci secondarie non precedono mai la voce 0, e il pitch di una voce si compone moltiplicando il rapporto di lettura, in modo compatibile con i rapporti audio ordinari.

Ogni voce ha il proprio cursore del tempo e produce una propria lista di grani; la lista finale dello stream è l'insieme di queste liste, indicizzato per voce. La densità dichiarata vale per ogni voce, quindi la densità complessiva è la densità per il numero di voci. Per ciascun grano il motore calcola gli scarti della voce al tempo reale della voce stessa, non a quello della voce di riferimento. Gli scarti si applicano poi al grano: il rapporto di altezza si moltiplica, la posizione di lettura e il pan si sommano, l'onset si ritarda.

Le strategie stocastiche rispettano la riproducibilità del capitolo sul linguaggio. Ogni voce ha un generatore proprio, derivato dal seme, dall'identità dello stream e dall'indice della voce. La direzione dello scarto di ciascuna voce è calcolata una volta sola e resta stabile; ciò che varia nel tempo, seguendo l'inviluppo, è soltanto la sua grandezza. Una voce che si è collocata a sinistra di quella di riferimento non cambia lato.

## Strategie di pitch

Le strategie di pitch sono sei. In tutte, la voce 0 resta all'identità.

- **`step`**: la voce $i$ è trasposta di $i$ volte il passo. Con passo di un'ottava le voci si dispongono in ottave pulite.
- **`range`**: le voci sono distribuite in modo equidistante entro un'ampiezza totale.
- **`stochastic`**: ogni voce ha uno scarto fisso, estratto con il seme, e l'inviluppo ne varia la grandezza massima.
- **`chord`**: gli scarti sono quelli di un accordo nominale, con un eventuale rivolto.
- **`chord_progression`**: l'accordo diventa una funzione del tempo.
- **`spectral`**: la voce $i$ sta sul parziale $i+1$ della serie armonica, cioè a $\mathrm{round}(12\log_2(i+1))$ semitoni: 0, 12, 19, 24, 28, 31 per le prime sei voci.

Gli scarti di `step`, `range` e `stochastic` sono posizioni adimensionali, e la loro geometria dipende dalla chiave `unit`, che accetta le stesse unità del blocco `pitch`. Nelle unità della famiglia EDO la distribuzione è additiva nel logaritmo: equidistante in semitoni, cent o gradi. Con l'unità `ratio` è invece geometrica: un passo di 2 dà rapporti 1, 2, 4, 8, e le frequenze si compongono moltiplicandosi. Le strategie `chord`, `chord_progression` e `spectral` sono definite per costruzione in semitoni, e rifiutano ogni altra unità.

Gli accordi disponibili sono nominati e raggruppati per numero di voci.

| Voci | Accordi |
|------|---------|
| 3 | `maj`, `min`, `dim`, `aug`, `sus2`, `sus4` |
| 4 | `dom7`, `maj7`, `min7`, `dim7`, `minmaj7` |
| 5 | `dom9`, `maj9`, `min9`, `9sus4` |
| 6 | `dom9s11`, `maj9s11`, `min11` |
| 7 | `dom13`, `min13`, `maj13s11`, `altered` |

La progressione è una lista di coppie `[tempo, accordo]`, con un rivolto facoltativo. Tra un accordo e il successivo l'interpolazione può essere lineare o cubica, e allora le voci scivolano in glissando, oppure a gradini, e allora l'armonia cambia a blocchi. La chiave `voice_leading` decide come le note del nuovo accordo si abbinano alle voci: `positional` assegna la nota $i$ alla voce $i$, `nearest` (il caso predefinito) riabbina le note perché ogni voce si muova il meno possibile, ripiegando le ottave e tenendo ferme le note comuni. Il moto della radice non appartiene alla progressione: si dichiara sull'inviluppo `pitch` dello stream, e si somma al voicing. I tempi della progressione seguono il modo temporale dello stream, come ogni inviluppo.

L'esempio (`esempi/voices_chords/voices_chords.yml`) lascia ferma la lettura e usa quattro voci, separate nella posizione di lettura perché le bande siano distinguibili. La progressione va da `maj7` a `min7` a `dom7`, e la radice sale di cinque semitoni a un terzo dello stream e scende di due ai due terzi.

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

![Quattro voci su una progressione d'accordi. Ogni voce traccia una banda orizzontale nella posizione di lettura, e il colore ne codifica l'altezza. A un terzo e a due terzi del tempo cambiano insieme il voicing, con scarti di 100 cent su due voci, e la radice, che muove tutte le bande.](docs/images/voices_chords_map.pdf){width=100%}

## Strategie di onset, pointer e pan

Le altre tre famiglie hanno meno strategie e seguono la stessa logica.

L'**onset** ritarda l'ingresso della voce. `linear` dà alla voce $i$ un ritardo di $i$ volte il passo, in secondi. `geometric` le dà il passo moltiplicato per una potenza della base, $\mathrm{passo}\cdot\mathrm{base}^{\,i-1}$, e i ritardi crescono in progressione. `stochastic` estrae per ogni voce un ritardo fra 0 e un massimo.

Il **pointer** sposta la voce nella posizione di lettura. `linear` dà alla voce $i$ uno scarto di $i$ volte il passo, e un passo negativo fa leggere le voci all'indietro rispetto alla voce di riferimento. `stochastic` estrae per ogni voce uno scarto fra meno e più un'ampiezza. Per impostazione predefinita lo scarto è in secondi nel file; con `normalized: true` lo stesso valore è una frazione della durata del file.

Il **pan** distribuisce le voci nel campo sonoro. `range` le dispone a distanze uguali entro un ventaglio centrato sullo zero. `stochastic` assegna a ciascuna un angolo stabile entro lo stesso ventaglio. `step` dà alla voce $i$ un angolo di $i$ volte il passo. Un offset uniforme per tutte le voci non è una strategia: lo dà il parametro `pan` dello stream.

La spazializzazione agisce quindi a due livelli annidati. La strategia assegna a ciascuna voce il proprio angolo, e il parametro `pan_range` dello stream aggiunge a ogni grano di quella voce una deviazione attorno a quell'angolo.

## Numero di voci e dissolvenze

Il numero di voci, `num_voices`, è un valore fisso o un inviluppo, e assume valori da 1 a 64. Il valore interpolato può essere frazionario. In quel caso le voci intere suonano a volume pieno, e la parte decimale diventa un fattore di volume sulla voce di confine, quella che si sta accendendo o spegnendo: con $f$ la parte frazionaria, il volume di quella voce si riduce di $-20\log_{10} f$ decibel. Invece di un'accensione di colpo, la voce di confine sale o scende gradualmente. Con interpolazione a gradini e punti interi non c'è parte frazionaria, e le voci si accendono e si spengono di colpo; con interpolazione lineare o cubica la transizione fra due conteggi interi diventa una dissolvenza. La dissolvenza è guidata dall'inviluppo e non usa numeri casuali. Nella MAP la voce in dissolvenza appare più trasparente, perché l'opacità del grano segue il suo volume.

L'esempio (`esempi/voices_fade/voices_fade.yml`) porta il numero di voci da 1 a 4 a metà dello stream, e poi a 2,5.

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

Un secondo inviluppo governa l'accoppiamento fra le voci, ed è un livello che si aggiunge alla griglia della singola voce. Il ritardo fra i grani di un flusso e il grado di sincronicità fra flussi diversi sono due controlli distinti, e la stessa coppia struttura per intero il trattamento canonico della granulazione [@Dutilleux2016]. Il primo lo governa la griglia, descritta nel capitolo precedente. Il secondo è `scatter`, un numero da 0 a 1. A 0 tutte le voci condividono la sequenza di intervalli della voce 0. A 1 ciascuna calcola la propria. I valori intermedi interpolano: l'intervallo di una voce è la combinazione lineare dell'intervallo condiviso e di quello indipendente, pesata da `scatter`.

`scatter` si distingue dallo scarto di onset, che è uno sfasamento fisso. Non ritarda le voci: decide se la loro scansione temporale sia la stessa. Agisce quindi in modo evidente quando la griglia è stocastica. Con una griglia pienamente sincrona le voci che calcolano la propria sequenza producono essenzialmente la stessa, e i due regimi coincidono. Con `distribution` a 1 le sequenze indipendenti divergono, e l'inviluppo di `scatter` diventa il passaggio da un'unica nuvola coerente a più nuvole indipendenti. Anche questo calcolo è stocastico: quali voci si sganciano e in quali istanti cambia da una realizzazione all'altra, ma l'andamento dell'inviluppo resta lo stesso, e con il seme dichiarato la realizzazione si ripete.

## Un esempio completo

L'esempio del paper (`esempi/voices/voices.yml`) mette insieme le quattro strategie e i due inviluppi di insieme, su uno stream di quaranta secondi.

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

Il passo di pitch è di un'ottava per voce: uno scarto molto largo, lontano dal regime della decorrelazione, che distende le voci su un registro vastissimo. La scala cromatica della figura misura l'escursione risultante. Restano fuori dalla figura i parametri spaziali: il passo del pan è un inviluppo, quindi il ventaglio resta chiuso per la prima metà dello stream e si apre nell'ultimo terzo.

## Come si estende

Le quattro famiglie di strategie sono punti di estensione. Per aggiungere un modo diverso di distribuire le voci lungo uno degli assi basta scrivere una classe che ne calcoli lo scarto e registrarla sotto un nome, come descritto nel capitolo sull'architettura; il nome diventa subito utilizzabile nel listato. Un intervento di struttura, invece, è l'aggiunta di un asse nuovo: non si esaurisce in una classe, perché tocca la configurazione della voce, il calcolo degli scarti e la loro applicazione al grano.
