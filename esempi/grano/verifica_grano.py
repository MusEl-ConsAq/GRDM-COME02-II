#!/usr/bin/env python3
"""Verifica le affermazioni del capitolo 5 sul grano e sullo stream di PGE.

Uso:  python esempi/grano/verifica_grano.py

PGE_DIR (default ../PythonGranularEngine) indica il repo del motore: se ne usano src/
e refs/ (il campione `voice.wav`). Ogni sezione controlla con `assert` una parte del
capitolo, sul motore vero:
  1. il puntatore: ingresso nel loop, finestra, banda di posizione, lettura oltre il bordo;
  2. la griglia: intervalli, fill factor, limiti, taglio dei grani a fine stream;
  3. la durata del grano: limiti e unita';
  4. le finestre: catalogo, lista, transizione e percorso a stati;
  5. l'altezza: unita', limiti, quantizzazione, detune implicito;
  6. il verso di lettura;
  7. volume e pan: guadagni del renderer NumPy;
  8. la variazione stocastica: gate, scritture della chiave, dizionario, jitter implicito.
"""
import contextlib
import io
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml

AQUI = Path(__file__).resolve().parent
PGE = Path(os.environ.get("PGE_DIR", AQUI.parents[1].parent / "PythonGranularEngine"))
REFS = str(PGE / "refs")
sys.path.insert(0, str(PGE / "src"))

from pge import api  # noqa: E402
from pge.core.grain import Grain  # noqa: E402
from pge.rendering.grain_renderer import GrainRenderer  # noqa: E402
from pge.rendering.numpy_window_registry import NumpyWindowRegistry  # noqa: E402
from pge.rendering.sample_registry import SampleRegistry  # noqa: E402
from pge.shared.exceptions import EngineError  # noqa: E402

TMP = tempfile.mkdtemp()
INFO = sf.info(os.path.join(REFS, "voice.wav"))
FILE = INFO.frames / INFO.samplerate          # durata di voice.wav, in secondi


def carica(documento, nome="t.yml"):
    """Il Generator di un documento (dizionario o testo), col rumore di stdout/stderr tolto."""
    percorso = os.path.join(TMP, nome)
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(documento if isinstance(documento, str) else yaml.safe_dump(documento))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return api.load_generator(percorso, samples_dir=REFS)


def stream(sid="a", **chiavi):
    return {"stream_id": sid, "sample": "voice.wav", **chiavi}


def brano(*stream_, seed=2026, **top):
    return {"seed": seed, **top, "streams": list(stream_)}


def grani(g, i=0):
    return g.streams[i].voices[0]


def rifiuta(documento):
    """Il tipo dell'errore con cui il motore rifiuta un documento (None se lo accetta)."""
    try:
        carica(documento)
    except EngineError as e:
        return type(e).__name__
    return None


def ok(msg):
    print("ok  ", msg)


def renderer():
    """Il GrainRenderer NumPy di un grano, col campione gia' caricato."""
    campioni = SampleRegistry(REFS + "/")
    campioni.load("voice.wav")
    return GrainRenderer(campioni, NumpyWindowRegistry(), output_sr=INFO.samplerate)


def finestre(g):
    inv = {v: k for k, v in g.streams[0].window_table_map.items()}
    return [inv[x.envelope_table] for x in grani(g)]


# 1. Il puntatore ---------------------------------------------------------------------------
def puntatore():
    base = dict(duration=3.0, density=20, grain={"duration": 0.04})
    # loop statico: la testina corre libera finche' la posizione lineare non incontra la finestra
    g = carica(brano(stream(**base, pointer={"speed_ratio": 0.6, "start": 0.0, "loop_start": 0.9,
                                             "loop_dur": 0.4})))
    p = np.array([x.pointer_pos for x in grani(g)])
    t = np.array([x.onset for x in grani(g)])
    assert np.allclose(p[t < 1.45], 0.6 * t[t < 1.45])            # prima: lineare, fuori dalla finestra
    assert p[t > 1.5].min() >= 0.9 - 1e-9 and p[t > 1.5].max() < 1.3 + 1e-9   # poi: dentro [0.9, 1.3)
    ok("loop statico [0.9, 1.3): la testina corre libera fino a 0.9, poi resta nella finestra")

    # loop dinamico: loop_start e' un envelope, la testina entra subito
    g = carica(brano(stream(**base, time_mode="normalized", pointer={
        "speed_ratio": 0.3, "loop_start": [[0, 0.9], [1, 0.9001]], "loop_dur": 0.4})))
    p = np.array([x.pointer_pos for x in grani(g)])
    assert p[0] == 0.9 and p.min() >= 0.9 - 1e-9 and p.max() < 1.3002
    ok("loop dinamico: la testina nasce dentro la finestra, a loop_start(0), senza `start`")

    # start predefinito con un loop: loop_start(0)
    g = carica(brano(stream(**base, pointer={"speed_ratio": 0.0, "loop_start": 0.9, "loop_dur": 0.4})))
    assert {x.pointer_pos for x in grani(g)} == {0.9}
    # senza loop_start il loop non c'e': loop_end e loop_dur da soli sono ignorati, in silenzio
    for chiavi in ({"loop_end": 1.3}, {"loop_dur": 0.4}):
        g = carica(brano(stream(**base, pointer={"speed_ratio": 1.0, **chiavi})))
        t = np.array([x.onset for x in grani(g)])
        assert np.allclose([x.pointer_pos for x in grani(g)], t % FILE)
    # loop_end e loop_dur insieme: vince loop_end
    g = carica(brano(stream(**base, pointer={"speed_ratio": 0.0, "loop_start": 0.5, "loop_end": 0.7,
                                             "loop_dur": 0.9, "offset_range": 1.0})))
    assert max(x.pointer_pos for x in grani(g)) < 0.7
    assert rifiuta(brano(stream(**base, pointer={"loop_start": 1.0, "loop_end": 0.5}))) == "InvalidFieldValueError"
    ok("`start` predefinito = loop_start(0); `loop_start` accende il loop; loop_end batte loop_dur; "
       "loop_end <= loop_start e' un errore")

    # loop a cavallo della fine del file
    g = carica(brano(stream(**base, pointer={"speed_ratio": 0.0, "loop_start": 1.8, "loop_dur": 0.6,
                                             "offset_range": 1.0})))
    p = np.array([x.pointer_pos for x in grani(g)])
    assert np.all((p >= 1.8 - 1e-9) | (p < 1.8 + 0.6 - FILE + 1e-9))
    ok("loop_dur a cavallo della fine: le posizioni stanno in [1.8, fine) e [0, 0.415)")

    # offset_range e' una frazione della finestra attiva (il file, senza loop)
    def larghezza(**ptr):
        g = carica(brano(stream(duration=20.0, density=100, grain={"duration": 0.04},
                                pointer={"speed_ratio": 0.0, "offset_range": 0.2, **ptr})))
        p = np.array([x.pointer_pos for x in grani(g)])
        return p.max() - p.min()
    assert abs(larghezza(start=1.0) - 0.2 * FILE) < 0.01
    assert abs(larghezza(start=0.7, loop_start=0.5, loop_dur=0.4) - 0.2 * 0.4) < 0.005
    ok("offset_range 0.2 = 0.2 volte la finestra: 0.397 s sul file intero, 0.08 s in un loop di 0.4 s")

    # un grano non porta il loop: la lettura continua oltre il bordo della finestra
    g = carica(brano(stream(duration=1.0, density=20, grain={"duration": 0.2},
                            pointer={"speed_ratio": 0.0, "start": 0.55, "loop_start": 0.5, "loop_dur": 0.1})))
    primo = grani(g)[0]
    assert abs(primo.pointer_pos - 0.55) < 1e-9 and primo.duration == 0.2
    assert primo.pointer_pos + primo.duration > 0.6 + 0.1           # finisce ben oltre il bordo
    assert [c for c in Grain.__slots__ if "loop" in c] == []        # il grano non ha un campo per il loop
    ok("un grano che nasce a 0.55 in un loop [0.5, 0.6) dura fino a 0.75: il loop confina la partenza, non la lettura")

    sr = INFO.samplerate
    x = sf.read(os.path.join(REFS, "voice.wav"))[0]
    x = x if x.ndim == 1 else x.mean(axis=1)
    rend = renderer()
    n = round(0.2 * sr)
    out = rend.render(Grain(0.0, 0.2, 0.55, 1.0, 0.0, 45.0, 1, 1), "voice.wav", "rectangle")
    i0 = round(0.55 * sr)
    assert np.allclose(out[:, 0], x[i0:i0 + n], atol=1e-9) and np.allclose(out[:, 1], 0, atol=1e-12)
    ok("il renderer NumPy legge x[0.55 s : 0.75 s] senza conoscere il loop")

    # la lettura e' ciclica sul file intero
    out = rend.render(Grain(0.0, 0.2, FILE - 0.05, 1.0, 0.0, 45.0, 1, 1), "voice.wav", "rectangle")
    i0 = round((FILE - 0.05) * sr)
    atteso = np.concatenate([x[i0:], x[:n - (len(x) - i0)]])
    assert np.allclose(out[:, 0], atteso, atol=1e-2)
    ok("a fine file la lettura ricomincia dall'inizio (modulo sulla lunghezza del campione)")

    # `start` e' un valore, non un envelope
    assert rifiuta(brano(stream(**base, pointer={"start": [[0, 0], [1, 1]]}))) == "InvalidFieldValueError"
    assert rifiuta(brano(stream(**base, pointer={"speed_ratio": 150}))) == "ParameterBoundError"
    ok("pointer.start envelope e speed_ratio oltre 100 sono errori")


# 2. La griglia -----------------------------------------------------------------------------
def griglia():
    def iot(**k):
        g = carica(brano(stream(duration=20.0, **k)))
        o = np.array([x.onset for x in grani(g)])
        return np.diff(o), o

    d, o = iot(density=40)
    assert o[0] == 0.0 and np.allclose(d, 0.025)
    for dist, lo, hi in ((0.5, 0.0125, 0.0375), (1.0, 0.0, 0.05)):
        d, _ = iot(density=40, distribution=dist)
        assert d.min() >= lo - 1e-12 and d.max() <= hi + 1e-12
        assert abs(d.mean() - 0.025) < 0.0015 and abs(d.std() - dist * 0.05 / np.sqrt(12)) < 0.0015
    assert d.min() < 0.002 and d.max() > 0.048                      # d = 1 riempie tutto [0, 50 ms]
    ok("distribution 0: 25 ms esatti; 0.5: intervalli in [12.5, 37.5] ms; 1: in [0, 50] ms, media 25 ms")

    g = carica(brano(stream(duration=2.0, density=10, fill_factor=1)))
    assert abs(grani(g)[1].onset - grani(g)[0].onset - 0.05) < 1e-12   # fill_factor 1 / 0.05 s = 20 al secondo
    g = carica(brano(stream(duration=2.0)))
    assert abs(grani(g)[1].onset - grani(g)[0].onset - 0.025) < 1e-12  # predefinito: fill_factor 2
    ok("density e fill_factor insieme: vince fill_factor; senza nessuno dei due, fill_factor 2")

    g = carica(brano(stream(duration=3.0, fill_factor=2, grain={"duration": 0.05, "duration_range": 0.04})))
    gr = grani(g)
    d = np.array([x.duration for x in gr])
    o = np.array([x.onset for x in gr])
    assert d.max() - d.min() > 0.03
    assert np.abs(np.diff(o) - d[:-1] / 2).max() < 1e-12
    ok("con fill_factor 2 l'intervallo dopo un grano e' esattamente la meta' della sua durata, anche se la durata varia")

    for doc in (stream(duration=3.0, density=0.001), stream(duration=3.0, fill_factor=60),
                stream(duration=3.0, fill_factor=0.0005), stream(duration=3.0, distribution=1.5),
                stream(duration=3.0, time_mode="normalized", density=[[0, 0.001], [1, 0.001]])):
        assert rifiuta(brano(doc)) == "ParameterBoundError"
    g = carica(brano(stream(duration=300.0, density=0.01)))
    assert len(grani(g)) == 3
    ok("density sotto 0.01, fill_factor fuori da [0.001, 50], distribution fuori da [0, 1]: errori alla lettura")

    # la densita' vale all'onset di ogni grano: il numero di grani segue l'integrale
    for T, a, b in ((4.0, 10, 200), (4.0, 200, 10)):
        g = carica(brano(stream(duration=T, time_mode="normalized", density=[[0, a], [1, b]],
                                grain={"duration": 0.01})))
        assert abs(len(grani(g)) - T * (a + b) / 2) < 0.02 * T * (a + b) / 2
    ok("una rampa di densita' da 10 a 200 (e il suo inverso) produce i grani che ne dice l'integrale, entro il 2%")

    # un grano la cui coda sfora la fine dello stream e' scartato, non troncato
    def n_e_fine(**extra):
        g = carica(brano(stream(duration=1.0, density=7, grain={"duration": 0.3}, **extra)))
        gr = grani(g)
        return len(gr), gr[-1].onset + gr[-1].duration
    n, fine = n_e_fine()
    assert n == 5 and fine <= 1.0
    try:
        n2, fine2 = n_e_fine(clip_strategy="passthrough")
        assert n2 == 8 and fine2 > 1.0
    except TypeError:       # nella 9.1.0 `passthrough` fa fallire il costruttore: corretto in main
        n2 = None
    assert len(grani(carica(brano(stream(duration=2.0))))) == 79
    assert len(grani(carica(brano(stream())))) == 78
    ok("a fine stream i grani con la coda oltre la durata sono scartati: 79 grani su 2 s, 78 su voice.wav"
       + ("; con clip_strategy: passthrough restano tutti" if n2 else ""))


# 3. La durata del grano --------------------------------------------------------------------
def durata():
    def d(**gr):
        g = carica(brano(stream(duration=20.0, density=0.5, grain=gr)))
        return [x.duration for x in grani(g)]

    assert d(duration=0.000021)[0] == 0.000021 and d(duration=10)[0] == 10
    assert rifiuta(brano(stream(duration=20.0, grain={"duration": 0.00002}))) == "ParameterBoundError"
    assert rifiuta(brano(stream(duration=20.0, grain={"duration": 20}))) == "ParameterBoundError"
    assert 1 / 48000 > 0.00002
    ok("grain.duration: da 1 campione a 48 kHz (20.8 us) a 10 s; fuori e' un errore")

    assert abs(d(duration_unit="samples", duration=480)[0] - 0.01) < 1e-12
    assert abs(d(duration_unit="milliseconds", duration=20)[0] - 0.02) < 1e-12
    assert rifiuta(brano(stream(grain={"duration_unit": "samples"}))) == "MissingFieldError"
    def fitto(**gr):
        g = carica(brano(stream(duration=5.0, density=200, grain=gr)))
        return [x.duration for x in grani(g)]
    v = fitto(duration_unit="milliseconds", duration=20, duration_range=5)
    assert abs(min(v) - 0.0175) < 2e-4 and abs(max(v) - 0.0225) < 2e-4
    v = fitto(duration_unit="milliseconds", duration=20, duration_range=0.5, duration_range_unit="relative")
    assert abs(min(v) - 0.015) < 2e-4 and abs(max(v) - 0.025) < 2e-4
    ok("duration_unit: campioni e millisecondi; la durata va scritta; il range e' convertito, tranne se relativo")


# 4. Le finestre ----------------------------------------------------------------------------
def finestre_():
    from pge.controllers.window_registry import WindowRegistry
    nomi = sorted(WindowRegistry.WINDOWS)
    assert nomi == sorted("""bartlett blackman blackman_harris expodec expodec_strong exporise exporise_strong
                             gaussian half_sine hamming hanning kaiser rectangle rexpodec rexporise sinc""".split())
    assert WindowRegistry.ALIASES == {"triangle": "bartlett"}
    ok("il catalogo ha 16 finestre e l'alias triangle -> bartlett")

    assert rifiuta(brano(stream(grain={"envelope": "rectangular"}))) == "InvalidWindowError"
    assert rifiuta(brano(stream(grain={"envelope": "hann"}))) == "InvalidWindowError"
    base = dict(duration=20.0, density=100)

    def conta(**extra):
        g = carica(brano(stream(**base, **extra)))
        c = Counter(finestre(g))
        return {k: v / sum(c.values()) for k, v in c.items()}

    tre = ["hanning", "expodec", "gaussian"]
    c = conta(grain={"duration": 0.04, "envelope": tre})
    assert set(c) == set(tre) and all(abs(v - 1 / 3) < 0.05 for v in c.values())
    c = conta(grain={"duration": 0.04, "envelope": tre}, deviation_probability=30)
    assert abs(c["hanning"] - 0.8) < 0.05                              # 70% prima + 30% / 3
    c = conta(grain={"duration": 0.04, "envelope": tre}, deviation_probability=0)
    assert c == {"hanning": 1.0}
    c = conta(grain={"duration": 0.04, "envelope": tre}, deviation_probability={"pc_rand_envelope": 30})
    assert abs(c["hanning"] - 0.8) < 0.05
    c = conta(grain={"duration": 0.04, "envelope": tre}, deviation_probability={"envelope": 30})
    assert all(abs(v - 1 / 3) < 0.05 for v in c.values())              # la chiave `envelope` non agisce
    assert len(conta(grain={"duration": 0.04, "envelope": "all"})) == 16
    ok("lista di finestre: scelta uniforme; il gate chiuso da' sempre la prima; "
       "la chiave del dizionario e' pc_rand_envelope, `envelope` non agisce; `all` le usa tutte e 16")

    def quota_seconda(**env):
        g = carica(brano(stream(**base, time_mode="normalized", grain={"duration": 0.04, "envelope": env})))
        f = finestre(g)
        t = np.array([x.onset for x in grani(g)])
        return [np.mean([n == env.get("to", "bartlett") for n, tt in zip(f, t) if a * 20 <= tt < b * 20])
                for a, b in ((0, .25), (.25, .5), (.5, .75), (.75, 1))]
    q = quota_seconda(**{"from": "hanning", "to": "bartlett", "curve": [[0, 0], [1, 1]]})
    assert all(abs(a - b) < 0.06 for a, b in zip(q, (0.125, 0.375, 0.625, 0.875)))
    g = carica(brano(stream(**base, time_mode="normalized", deviation_probability=0, grain={
        "duration": 0.04, "envelope": {"from": "hanning", "to": "bartlett", "curve": [[0, 0], [1, 1]]}})))
    assert 0.7 < np.mean([n == "bartlett" for n in finestre(g)][len(grani(g)) // 2:]) < 0.8   # il gate non c'entra
    ok("transizione: la quota della seconda finestra segue la curva (13, 38, 63, 88%); il gate non agisce")

    g = carica(brano(stream(**base, time_mode="normalized", grain={"duration": 0.04, "envelope": {
        "states": [[0, "hanning"], [0.5, "rexpodec"], [1, "bartlett"]], "curve": [[0, 0], [1, 1]]}})))
    f, t = finestre(g), np.array([x.onset for x in grani(g)])
    meta = Counter(n for n, tt in zip(f, t) if 9 <= tt < 11)
    assert meta["rexpodec"] / sum(meta.values()) > 0.9
    inizio = Counter(n for n, tt in zip(f, t) if tt < 2)
    assert inizio["hanning"] > inizio["rexpodec"] > 0 and "bartlett" not in inizio
    assert rifiuta(brano(stream(**base, time_mode="normalized",
                                grain={"envelope": {"states": [[0.5, "hanning"], [0, "bartlett"]]}}))) \
        == "InvalidStrategyConfigError"
    ok("percorso a stati: attorno a 0.5 quasi solo rexpodec, in apertura hanning con qualche rexpodec")

    r = NumpyWindowRegistry()
    w = {n: r.get(n, 801)[::100] for n in ("rexpodec", "expodec", "exporise", "rexporise")}
    assert w["rexpodec"][0] == 1 and w["rexpodec"][1] < 0.65 and w["rexpodec"][-1] == 0      # attacco pieno, caduta
    assert w["expodec"][1] > 0.95 and w["expodec"][-2] < 0.5                                  # tenuta, poi caduta
    assert np.allclose(w["exporise"], w["expodec"][::-1]) and np.allclose(w["rexporise"], w["rexpodec"][::-1])
    assert WindowRegistry.WINDOWS["expodec"].param("curve") == 4.0
    assert WindowRegistry.WINDOWS["expodec_strong"].param("curve") == 10.0                   # curvatura 10, non 4
    ok("rexpodec parte a 1 e cade subito; expodec tiene e cade alla fine; exporise e rexporise sono "
       "le loro omologhe lette all'indietro; _strong ha curvatura 10 invece di 4")


# 5. L'altezza ------------------------------------------------------------------------------
def altezza():
    B = dict(duration=10.0, density=200, grain={"duration": 0.02})

    def r(**pitch):
        return np.array([x.pitch_ratio for x in grani(carica(brano(stream(**B, pitch=pitch))))])

    assert abs(r(semitones=7)[0] - 2 ** (7 / 12)) < 1e-12
    assert abs(r(cents=700)[0] - 2 ** (7 / 12)) < 1e-12 and abs(r(quarter_tone=14)[0] - 2 ** (7 / 12)) < 1e-12
    assert abs(r(eighth_tone=28)[0] - 2 ** (7 / 12)) < 1e-12 and r(ratio=1.5)[0] == 1.5
    assert abs(r(edo=31, value=18)[0] - 2 ** (18 / 31)) < 1e-12
    ok("semitoni, cent, quarti e ottavi di tono, edo e ratio: 2^(v/N) oppure il rapporto diretto")

    for pitch, errore in (({"semitones": 36}, None), ({"semitones": 37}, "ParameterBoundError"),
                          ({"cents": 3600}, None), ({"cents": 3601}, "ParameterBoundError"),
                          ({"ratio": 8}, None), ({"ratio": 8.1}, "ParameterBoundError"),
                          ({"ratio": 0.001}, None), ({"ratio": 0.0005}, "ParameterBoundError"),
                          ({"edo": 31, "value": 93}, None), ({"edo": 31, "value": 94}, "ParameterBoundError"),
                          ({"semitone": 7}, "InvalidFieldValueError"),
                          ({"semitones": 7, "cents": 3}, "InvalidFieldValueError"),
                          (None, "InvalidFieldValueError"), ({"edo": 31}, "InvalidFieldValueError")):
        assert rifiuta(brano(stream(**B, pitch=pitch))) == errore, pitch
    assert set(r()) == {1.0}
    assert r(range=4).min() < 0.9 and r(range=4).max() > 1.1
    ok("limiti (+-3 ottave; ratio da 0.001 a 8), una sola unita', chiavi sconosciute rifiutate, "
       "blocco {} neutro, `range` da solo agisce sui semitoni")

    s = 12 * np.log2(r(semitones=0, range=5))
    assert set(np.round(s, 6)) == {-2.0, -1.0, 0.0, 1.0, 2.0}
    c = 1200 * np.log2(r(cents=0, range=250))
    assert np.allclose(c, np.round(c), atol=1e-6) and abs(c.min() + 125) < 1 and abs(c.max() - 125) < 1
    e = 31 * np.log2(r(edo=31, value=0, range=6))
    assert set(np.round(e, 6)) == {-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0}
    v = r(ratio=1.0, range=0.2)
    assert len(set(np.round(v, 6))) > 1000 and abs(v.min() - 0.9) < 0.005 and abs(v.max() - 1.1) < 0.005
    ok("con `range` le unita' EDO variano a passi interi (+-int(range/2)); ratio varia in modo continuo")

    def con_gate(**pitch):
        g = carica(brano(stream(**B, pitch=pitch, deviation_probability={"pitch": 100})))
        return np.array([x.pitch_ratio for x in grani(g)])
    c = 1200 * np.log2(con_gate(semitones=0))
    assert abs(c.max() - 12) < 0.1 and abs(c.min() + 12) < 0.1
    c = 1200 * np.log2(con_gate(edo=31, value=0))
    assert abs(c.max() - 12) < 0.1 and abs(c.min() + 12) < 0.1
    q = con_gate(ratio=1.0)
    assert abs(q.max() - 1.0025) < 2e-4 and abs(q.min() - 0.9975) < 2e-4
    assert len(set(np.round(con_gate(semitones=0, range=0), 9))) == 1
    ok("detune implicito: +-12 cent sulle unita' EDO, +-0.0025 sul ratio; con range (anche 0) non si applica")

    for pitch, errore in (({"semitones": 0, "range": 36}, None), ({"semitones": 0, "range": 37}, "ParameterBoundError"),
                          ({"cents": 0, "range": 3600}, None), ({"cents": 0, "range": 3601}, "ParameterBoundError"),
                          ({"ratio": 1.0, "range": 2}, None), ({"ratio": 1.0, "range": 2.1}, "ParameterBoundError")):
        assert rifiuta(brano(stream(**B, pitch=pitch))) == errore, pitch
    ok("larghezza massima di `range`: tre ottave per le unita' EDO (36 semitoni, 3600 cent), 2 per ratio")


# 6. Il verso di lettura --------------------------------------------------------------------
def verso():
    d = 0.05
    g = carica(brano(stream(duration=2.0, density=20, grain={"duration": d},
                            pointer={"speed_ratio": -0.5, "start": 1.5})))
    gr, t = grani(g), np.array([x.onset for x in grani(g)])
    assert all(x.pitch_ratio == -1.0 for x in gr)
    assert np.allclose([x.pointer_pos for x in gr], 1.5 - 0.5 * t + d)
    ok("testina all'indietro: grani con rapporto -1 e posizione spostata in avanti della loro durata")

    g = carica(brano(stream(duration=2.0, density=20, grain={"duration": d, "reverse": None},
                            pointer={"speed_ratio": 0.5, "start": 0.5})))
    assert {x.pitch_ratio for x in grani(g)} == {-1.0} and abs(grani(g)[0].pointer_pos - 0.55) < 1e-12
    B = dict(duration=2.0, density=20)
    assert rifiuta(brano(stream(**B, grain={"reverse": True}))) == "InvalidFieldValueError"
    assert rifiuta(brano(stream(**B, grain={"reverse": None, "read_direction": 1}))) == "InvalidFieldValueError"
    assert rifiuta(brano(stream(**B, grain={"read_direction": 0.5}))) == "InvalidFieldValueError"
    ok("grain.reverse vuoto ribalta tutti i grani; `reverse: true`, reverse + read_direction e "
       "read_direction fuori da -1 e +1 sono errori")

    g = carica(brano(stream(duration=2.0, density=20, grain={"duration": d, "read_direction": 1},
                            pointer={"speed_ratio": -0.5, "start": 1.5})))
    assert {x.pitch_ratio for x in grani(g)} == {1.0}
    g = carica(brano(stream(duration=8.0, density=6, time_mode="normalized", grain={
        "duration": 0.12, "read_direction": [[0, 1], [0.5, -1], [0.75, 1]]}, pointer={"speed_ratio": 0.25})))
    segno = {round(x.onset, 1): x.pitch_ratio < 0 for x in grani(g)}
    assert not segno[3.8] and segno[4.2] and segno[5.8] and not segno[6.2]
    ok("read_direction e' indipendente dalla testina; a gradini: all'indietro fra 4 e 6 s")

    def ribaltati(gr, dp):
        g = carica(brano(stream(duration=20.0, density=100, grain=gr, deviation_probability=dp)))
        return np.mean([x.pitch_ratio < 0 for x in grani(g)])
    assert abs(ribaltati({"duration": 0.02}, {"reverse": 50}) - 0.5) < 0.05
    assert abs(ribaltati({"duration": 0.02, "read_direction": 1}, {"read_direction": 50}) - 0.5) < 0.05
    assert ribaltati({"duration": 0.02, "read_direction": 1}, {"reverse": 50}) == 0.0
    assert ribaltati({"duration": 0.02}, 100) == 1.0
    ok("il ribaltamento stocastico ha chiavi proprie (reverse, read_direction); un gate globale al 100% "
       "ribalta tutti i grani in modo automatico")


# 7. Volume e pan ---------------------------------------------------------------------------
def volume_e_pan():
    sr = INFO.samplerate
    x = sf.read(os.path.join(REFS, "voice.wav"))[0]
    x = x if x.ndim == 1 else x.mean(axis=1)
    rend = renderer()
    n = round(0.05 * sr)
    i0 = round(0.5 * sr)
    sorgente = x[i0:i0 + n]

    def gain(pan, volume=0.0):
        out = rend.render(Grain(0.0, 0.05, 0.5, 1.0, volume, pan, 1, 1), "voice.wav", "rectangle")
        gl = (out[:, 0] * sorgente).sum() / (sorgente * sorgente).sum()
        gr = (out[:, 1] * sorgente).sum() / (sorgente * sorgente).sum()
        return gl, gr

    att = {0: (0.7071, 0.7071), 45: (1.0, 0.0), -45: (0.0, 1.0), 90: (0.7071, -0.7071),
           180: (-0.7071, -0.7071), 135: (0.0, -1.0)}
    for pan, (l, r) in att.items():
        gl, gr = gain(pan)
        assert abs(gl - l) < 1e-3 and abs(gr - r) < 1e-3, (pan, gl, gr)
        assert abs(gl ** 2 + gr ** 2 - 1) < 1e-3
    gl, _ = gain(45, -6.0206)
    assert abs(gl - 0.5) < 1e-3
    ok("pan: 0 gradi = centro (0.707, 0.707), +45 tutto a sinistra, -45 tutto a destra, +90 in controfase; "
       "potenza costante; -6.02 dB = meta' ampiezza")

    B = dict(duration=2.0, density=20)
    for doc, errore in ((stream(**B, volume=12), None), (stream(**B, volume=13), "ParameterBoundError"),
                        (stream(**B, volume=-121), "ParameterBoundError"), (stream(**B, pan=3600), None),
                        (stream(**B, pan=3601), "ParameterBoundError"),
                        (stream(**B, volume_range=24), None), (stream(**B, volume_range=25), "ParameterBoundError"),
                        (stream(**B, pan_range=360), None), (stream(**B, pan_range=361), "ParameterBoundError")):
        assert rifiuta(brano(doc)) == errore
    ok("volume da -120 a +12 dB, volume_range fino a 24 dB; pan fino a +-3600 gradi, pan_range fino a 360")


# 8. La variazione stocastica ---------------------------------------------------------------
def variazione():
    B = dict(duration=15.0, density=200, grain={"duration": 0.02}, pointer={"speed_ratio": 0.0, "start": 1.0})

    def deviati(g):
        gr = grani(g)
        return np.array([x.volume != 0 or x.pan != 0 or abs(x.duration - 0.02) > 1e-12
                         or abs(x.pointer_pos - 1.0) > 1e-9 or x.pitch_ratio != 1.0 for x in gr])

    # senza _range le quattro scritture non deviano; con un _range lo applicano a tutti i grani
    scritture = {"omessa": {}, "false": {"deviation_probability": False}, "{}": {"deviation_probability": {}},
                 "{volume: null}": {"deviation_probability": {"volume": None}}}
    for nome, extra in scritture.items():
        assert deviati(carica(brano(stream(**B, **extra)))).sum() == 0, nome
        assert deviati(carica(brano(stream(**B, volume_range=6, **extra)))).all(), nome
    ok("deviation_probability omessa, false, {} o {chiave: null}: senza _range nessuna deviazione, "
       "con un _range il range vale per tutti i grani")

    # la chiave scritta e lasciata vuota apre il gate implicito: 1% per parametro
    v = deviati(carica(brano(stream(**B, deviation_probability=None))))
    attesa = 1 - 0.99 ** 6                                            # sei gate: volume, pan, durata, lettura, altezza, verso
    assert abs(v.mean() - attesa) < 0.015, (v.mean(), attesa)
    v2 = deviati(carica(brano(stream(**B, volume_range=6, deviation_probability=None))))
    assert abs(v2.mean() - attesa) < 0.015                              # il range e' soggetto al gate
    ok(f"deviation_probability: vuota = 1% per parametro: devia il {100 * v.mean():.1f}% dei grani "
       f"(1 - 0.99^6 = {100 * attesa:.1f}%), anche con un _range dichiarato")

    # la misura della documentazione di PGE: 79 grani, read_direction dichiarata, nessun _range
    def ribaltati(scrittura, semi=range(200)):
        """Grani ribaltati ogni 79, sommando su piu' semi (la chiave vuota apre anche il gate della durata)."""
        flip = tot = 0
        for s in semi:
            g = carica(brano(stream(duration=2.0, grain={"read_direction": 1}, **scrittura), seed=s))
            flip += sum(x.pitch_ratio < 0 for x in grani(g))
            tot += len(grani(g))
        return 79 * flip / tot
    for nome in ("omessa", "false", "{}", "{volume: null}"):
        assert ribaltati(scritture[nome], range(40)) == 0.0
    media = ribaltati({"deviation_probability": None})
    assert 0.5 < media < 1.1, media
    ok(f"su 79 grani con read_direction e nessun _range: la chiave vuota ne ribalta in media {media:.2f} "
       "(1% di 79 = 0.79), le altre quattro scritture mai")

    # il dizionario: la chiave assente lascia il range sempre attivo
    g = carica(brano(stream(**B, volume_range=6, pan_range=40, deviation_probability={"volume": 30})))
    gr = grani(g)
    assert abs(np.mean([x.volume != 0 for x in gr]) - 0.3) < 0.03
    assert np.mean([x.pan != 0 for x in gr]) == 1.0
    g = carica(brano(stream(**B, volume_range=6, pan_range=40, deviation_probability=30)))
    gr = grani(g)
    assert abs(np.mean([x.volume != 0 for x in gr]) - 0.3) < 0.03 and abs(np.mean([x.pan != 0 for x in gr]) - 0.3) < 0.03
    assert abs(np.mean([abs(x.duration - 0.02) > 1e-12 for x in gr]) - 0.3) < 0.03     # jitter implicito, senza range
    ok("dizionario {volume: 30}: il volume devia nel 30% dei grani, il pan (assente) nel 100%; "
       "una probabilita' globale del 30% vale per tutti i parametri, anche per quelli senza _range")

    # ogni chiave del dizionario ferma il proprio parametro
    R = dict(volume_range=12, pan_range=60, grain={"duration": 0.02, "duration_range": 0.01},
             pointer={"speed_ratio": 0.0, "start": 1.0, "offset_range": 0.1}, pitch={"semitones": 0, "range": 4})
    base = dict(duration=10.0, density=100)

    def varia(dp):
        gr = grani(carica(brano(stream(**base, **R, deviation_probability=dp))))
        return {"volume": np.ptp([x.volume for x in gr]) > 1e-9, "pan": np.ptp([x.pan for x in gr]) > 1e-9,
                "duration": np.ptp([x.duration for x in gr]) > 1e-9,
                "pointer": np.ptp([x.pointer_pos for x in gr]) > 1e-9,
                "pitch": np.ptp([x.pitch_ratio for x in gr]) > 1e-9}
    assert all(varia({"grain_duration": 0}).values()) and all(varia(False).values())
    for chiave in ("volume", "pan", "duration", "pointer", "pitch"):
        m = varia({chiave: 0})
        assert not m[chiave] and all(v for k, v in m.items() if k != chiave), chiave
    ok("le chiavi del dizionario sono volume, pan, duration, pointer, pitch (e reverse, read_direction, "
       "pc_rand_envelope): ciascuna ferma solo il proprio parametro; `grain_duration` non esiste")

    # la banda: +-range/2 attorno al centro
    g = carica(brano(stream(**B, volume_range=6)))
    assert abs(max(abs(x.volume) for x in grani(g)) - 3.0) < 0.01
    ok("volume_range 6: i grani stanno entro +-3 dB")

    # il jitter implicito (gate al 100%, nessun _range): meta' della larghezza di default
    def estremi(chiave, **extra):
        g = carica(brano(stream(**B, deviation_probability={chiave: 100}, **extra)))
        return grani(g)
    gr = estremi("volume")
    assert abs(max(abs(x.volume) for x in gr) - 1.5) < 0.01
    gr = estremi("pan")
    assert abs(max(abs(x.pan) for x in gr) - 15.0) < 0.05
    gr = estremi("duration")
    assert abs(max(abs(x.duration - 0.02) for x in gr) - 0.005) < 5e-5
    gr = estremi("pointer")
    assert abs(max(abs(x.pointer_pos - 1.0) for x in gr) - 0.025 * FILE) < 5e-4
    c = 1200 * np.log2([x.pitch_ratio for x in estremi("pitch")])
    assert abs(c.max() - 12) < 0.1 and abs(c.min() + 12) < 0.1
    ok("jitter implicito: volume +-1.5 dB, pan +-15 gradi, durata +-5 ms, lettura +-2.5% del file, altezza +-12 cent")

    # i limiti sono dichiarati, e i valori prodotti dalla banda sono richiusi nei limiti
    S = dict(duration=2.0, density=20)
    assert rifiuta(brano(stream(**S, grain={"duration": 0.02, "duration_range": 1.5}))) == "ParameterBoundError"
    assert rifiuta(brano(stream(**S, pointer={"offset_range": 1.5}))) == "ParameterBoundError"
    ok("duration_range e offset_range fuori da [0, 1]: errori")


def main():
    for f in (puntatore, griglia, durata, finestre_, altezza, verso, volume_e_pan, variazione):
        print(f"--- {f.__doc__ or f.__name__}")
        f()
    print("\ntutte le verifiche passano")


if __name__ == "__main__":
    main()
