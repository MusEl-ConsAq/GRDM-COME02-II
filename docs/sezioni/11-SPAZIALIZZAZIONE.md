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

Il motore ha già tutto ciò che la codifica richiede. Il renderer calcola, per ogni grano, il grano finestrato $s$ (che è $W$) e le sue due proiezioni, `mid = s cos(θ)` e `side = s sin(θ)`, e solo dopo le ruota in sinistra e destra. Tutta la differenza fra due altoparlanti e $n$ sta nell'ultimo passo, che nei tre renderer è la stessa matrice (capitolo 7). Le strade sono due. La prima è far scrivere ai renderer direttamente gli $n$ canali, decodificando con il layout dichiarato nello YAML. La seconda è scrivere il formato di trasmissione, i tre canali $W$, $M$ e $S$, e lasciare la decodifica al momento dell'esecuzione. La seconda segue il principio di Gerzon: il file non dipende dalla sala, il decoder sì, e se la disposizione degli altoparlanti cambia da un concerto all'altro non si ri-renderizza il brano. Il costo è un file a tre canali al posto di due. Nessuna delle due strade cambia il grano, la lista dei grani o il seme, e quindi la riproducibilità del capitolo 3.

L'autore ha esplorato questi algoritmi in una libreria Faust a parte (MidSide), con un panner mid-side a profilo polare regolabile e decoder a quattro altoparlanti, a rombo e a coppie anteriori e posteriori. La libreria non è integrata in PGE e non coincide punto per punto con la formula di questo capitolo (ricava la parte omnidirezionale dal mid), e il capitolo non la descrive.

Per *mare-nostrum* ciò che conta è che i pan del brano coprono già 360 gradi (capitolo 10). A due altoparlanti il dietro si piega sul davanti: un grano a $180^\circ - \theta$ suona come lo speculare davanti, con $L$ e $R$ scambiati e la polarità invertita, e a $\pm 90$ gradi le due uscite sono in controfase. Con $n$ altoparlanti attorno al pubblico gli stessi valori diventano posizioni vere.

<!-- TODO(giulio): decidere e scrivere le condizioni di esecuzione: numero e disposizione degli altoparlanti (anello regolare? quanti? a che distanza dal pubblico e a che altezza?), la sala, se la decodifica si fa al concerto (formato W, M, S) o in studio (n canali già decodificati), e con quale software. Verificare anche che il pan di ogni stream abbia senso come azimut fisico (0 davanti, positivo a sinistra): oggi è scritto per due altoparlanti e non è stato mai ascoltato su un anello. -->
