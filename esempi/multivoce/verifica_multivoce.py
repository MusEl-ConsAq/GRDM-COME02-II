#!/usr/bin/env python3
"""Verifica le affermazioni del capitolo 6 sulle voci di PGE.

Uso:  python esempi/multivoce/verifica_multivoce.py

PGE_DIR (default ../PythonGranularEngine) indica il repo del motore: se ne usano src/
e refs/ (il campione `voice.wav`). Ogni sezione controlla con `assert` una parte del
capitolo, sul motore vero:
  1. che cos'e' una voce: liste, densita', invariante della voce 0, posizioni fisse;
  2. onset, pointer e pan: le strategie, il seme per voce, il loop, la strategia `range`;
  3. il pitch: geometria delle unita', accordi, estensione, rivolti, serie spettrale;
  4. la progressione d'accordi e il riabbinamento `nearest`;
  5. il numero di voci e la dissolvenza;
  6. lo scatter;
  7. l'esempio completo `voices`;
  8. cio' che il blocco `voices` lascia passare.
"""
import contextlib
import io
import itertools
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import yaml

AQUI = Path(__file__).resolve().parent
PGE = Path(os.environ.get("PGE_DIR", AQUI.parents[1].parent / "PythonGranularEngine"))
REFS = str(PGE / "refs")
sys.path.insert(0, str(PGE / "src"))

from pge import api  # noqa: E402
from pge.shared.exceptions import EngineError  # noqa: E402
from pge.strategies.voice_pitch_strategy import CHORD_INTERVALS  # noqa: E402
from pge.strategies.voice_pitch_strategy import ChordProgressionPitchStrategy  # noqa: E402

TMP = tempfile.mkdtemp()
FILE = 1.9853                                    # durata di voice.wav, in secondi


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


def voci(g, i=0):
    return g.streams[i].voices


def S(vox, **extra):
    """Uno stream di 4 secondi, 10 grani al secondo, lettura ferma a 1.0 s, con il blocco voices."""
    d = dict(duration=4.0, density=10, grain={"duration": 0.02},
             pointer={"speed_ratio": 0.0, "start": 1.0}, voices=vox)
    d.update(extra)
    return stream(**d)


def prova(documento):
    """Il tipo dell'eccezione con cui il motore rifiuta un documento (None se lo accetta)."""
    try:
        carica(documento)
    except Exception as e:
        return type(e).__name__, isinstance(e, EngineError)
    return None


def primi(g, f):
    return [f(v[0]) for v in voci(g)]


def semitoni(g):
    return [round(12 * np.log2(abs(x)), 2) for x in primi(g, lambda x: x.pitch_ratio)]


def ok(msg):
    print("ok  ", msg)


# 1. Che cos'e' una voce --------------------------------------------------------------------
def una_voce():
    from pge.controllers.voice_manager import VoiceConfig, VoiceManager
    assert [f for f in VoiceConfig.__dataclass_fields__] == ["pitch_factor", "pointer_offset", "pan_offset", "onset_offset"]
    assert VoiceManager(max_voices=3).get_voice_config(0, 1.0) == VoiceConfig(1.0, 0.0, 0.0, 0.0)
    ok("VoiceConfig ha quattro campi, e senza strategie la voce 0 e' (1, 0, 0, 0)")

    for n in (1, 2.5, 64, 70, 256):
        assert len(voci(carica(brano(S(dict(num_voices=n)))))) == int(np.ceil(n))
    for n in (257, 0.5, 0):
        assert prova(brano(S(dict(num_voices=n))))[0] == "ParameterBoundError"
    ok("num_voices da 1 a 256, una lista per ogni voce del picco (arrotondato per eccesso); fuori e' un errore")

    g1 = carica(brano(S(dict(num_voices=1))))
    g4 = carica(brano(S(dict(num_voices=4))))
    assert [len(v) for v in voci(g1)] == [40] and [len(v) for v in voci(g4)] == [40, 40, 40, 40]
    ok("la densita' dichiarata vale per ogni voce: 4 voci a 10 grani al secondo = 40 grani al secondo")

    def firma(v):
        return [(round(x.onset, 9), round(x.duration, 9), round(x.volume, 6), round(x.pan, 6),
                 round(x.pointer_pos, 6)) for x in v]
    rumore = dict(duration=6.0, density=40, distribution=0.5, grain={"duration": 0.03, "duration_range": 0.02},
                  volume_range=6, pan_range=40, pointer={"speed_ratio": 0.0, "start": 1.0, "offset_range": 0.1})
    senza = carica(brano(stream(**rumore)))
    uno = carica(brano(stream(**rumore, voices=dict(num_voices=1))))
    tre = carica(brano(stream(**rumore, voices=dict(num_voices=3))))
    assert firma(voci(senza)[0]) == firma(voci(uno)[0])
    a, b = voci(senza)[0], voci(tre)[0]
    assert [x.onset for x in a] == [x.onset for x in b]                      # la griglia e' la stessa
    assert [x.volume for x in a] != [x.volume for x in b]                    # i parametri per grano no
    assert [x.duration for x in a] != [x.duration for x in b]
    ok("num_voices: 1 = nessun blocco voices; con 3 voci la voce 0 ha gli stessi onset ma altri valori casuali per grano")

    # le strategie vedono il numero MASSIMO di voci: una voce che si accende non sposta le altre
    g = carica(brano(S(dict(num_voices=[[0, 2], [4, 4]], pitch={"strategy": "range", "pitch_range": 12}),
                       time_mode="absolute")))
    v = voci(g)
    for i, atteso in ((1, 4.0), (2, 8.0), (3, 12.0)):
        assert {round(12 * np.log2(x.pitch_ratio), 2) for x in v[i]} == {atteso}
    assert v[1][0].onset < 0.2 and v[3][0].onset > 2.0                        # la voce 3 entra dopo
    ok("range 12 con num_voices da 2 a 4: la voce 1 sta a +4 semitoni anche quando e' l'unica secondaria")

    # gli scarti seguono il cursore della voce
    st = S(dict(num_voices=3, scatter=1.0, pan={"strategy": "step", "step": [[0, 0], [4, 30]]}),
           distribution=1.0, density=20)
    g = carica(brano(st))
    for i in (1, 2):
        assert max(abs(x.pan - i * 30 * (x.onset / 4.0)) for x in voci(g)[i]) < 1e-9
    assert [x.onset for x in voci(g)[0][:5]] != [x.onset for x in voci(g)[1][:5]]
    ok("con scatter 1 gli scarti sono valutati all'istante della voce, non a quello della voce 0")


# 2. Onset, pointer e pan -------------------------------------------------------------------
def onset_pointer_pan():
    def on(vox):
        return [round(x, 3) for x in primi(carica(brano(S(vox))), lambda x: x.onset)]
    assert on(dict(num_voices=4, onset_offset={"strategy": "linear", "step": 0.05})) == [0.0, 0.05, 0.1, 0.15]
    assert on(dict(num_voices=4, onset_offset={"strategy": "geometric", "step": 0.05, "base": 2})) == [0.0, 0.05, 0.1, 0.2]
    s = on(dict(num_voices=6, onset_offset={"strategy": "stochastic", "max_offset": 0.2}))
    assert s[0] == 0.0 and all(0 < x <= 0.2 for x in s[1:]) and len(set(s)) == 6
    g = carica(brano(S(dict(num_voices=4, onset_offset={"strategy": "linear", "step": 0.05}))))
    assert [len(v) for v in voci(g)] == [40, 40, 39, 39]
    assert on(dict(num_voices=3, onset_offset={"strategy": "linear", "step": -0.05})) == [0.0, -0.05, -0.1]
    ok("onset: linear, geometric (step * base^(i-1)), stochastic in [0, max]; due voci ritardate perdono "
       "il grano di coda (39 su 40); un passo negativo e' accettato e da' onset negativi")

    def pt(vox, ptr=None):
        d = S(vox)
        if ptr:
            d["pointer"] = ptr
        return [round(x, 3) for x in primi(carica(brano(d)), lambda x: x.pointer_pos)]
    assert pt(dict(num_voices=4, pointer={"strategy": "linear", "step": 0.1})) == [1.0, 1.1, 1.2, 1.3]
    assert pt(dict(num_voices=4, pointer={"strategy": "linear", "step": -0.1})) == [1.0, 0.9, 0.8, 0.7]
    n = pt(dict(num_voices=4, pointer={"strategy": "linear", "step": 0.1, "normalized": True}))
    assert np.allclose(n, [1.0 + i * 0.1 * FILE for i in range(4)], atol=2e-3)
    assert prova(brano(S(dict(num_voices=2, pointer={"strategy": "linear", "step": 0.1, "normalized": 1}))))[0] \
        == "InvalidFieldValueError"
    loop = {"speed_ratio": 0.0, "start": 1.0, "loop_start": 0.9, "loop_dur": 0.4}
    assert pt(dict(num_voices=4, pointer={"strategy": "linear", "step": 0.3}), loop) == [1.0, 0.9, 1.2, 1.1]
    ok("pointer: linear in secondi, negativo verso l'inizio, normalized in frazione del file (solo un booleano); "
       "dentro un loop [0.9, 1.3) lo scarto e' ridotto modulo la finestra: 1.0, 0.9, 1.2, 1.1")

    def pn(vox, **extra):
        return [round(x, 3) for x in primi(carica(brano(S(vox, **extra))), lambda x: x.pan)]
    assert pn(dict(num_voices=4, pan={"strategy": "step", "step": 15})) == [0.0, 15.0, 30.0, 45.0]
    assert pn(dict(num_voices=4, pan={"strategy": "step", "step": 15}), pan=10) == [10.0, 25.0, 40.0, 55.0]
    assert pn(dict(num_voices=4, pan={"strategy": "range", "spread": 120})) == [0.0, -20.0, 20.0, 60.0]
    assert pn(dict(num_voices=3, pan={"strategy": "range", "spread": 120})) == [0.0, 0.0, 60.0]
    assert pn(dict(num_voices=2, pan={"strategy": "range", "spread": 120})) == [0.0, 60.0]
    st = pn(dict(num_voices=6, pan={"strategy": "stochastic", "spread": 120}))
    assert st[0] == 0.0 and all(abs(x) <= 60 for x in st) and len(set(st)) == 6
    ok("pan: step, stochastic in +-spread/2; range lascia la voce 0 a 0 e mette le altre fra -spread/2 + passo e "
       "+spread/2 (0, -20, 20, 60 con 4 voci; 0, 0, 60 con 3); il pan dello stream si somma")

    # le strategie stocastiche: seme per voce, direzione stabile, grandezza che segue l'inviluppo
    def spost(n, seed=2026, sid="x", **extra):
        g = carica(brano(S(dict(num_voices=n, pointer={"strategy": "stochastic", "pointer_range": 0.3}),
                           stream_id=sid, **extra), seed=seed))
        return [round(x, 5) for x in primi(g, lambda x: x.pointer_pos)]
    tre, cinque = spost(3), spost(5)
    assert tre == cinque[:3] and tre[0] == 1.0
    assert spost(4, seed=1) != spost(4, seed=2) and spost(4, seed=1) == spost(4, seed=1)
    assert all(abs(x - 1.0) <= 0.3 for x in cinque)
    ok("offset stocastici: fissati dal seme e dall'indice, indipendenti dal numero di voci, entro +-range")

    g = carica(brano(S(dict(num_voices=4, pointer={"strategy": "stochastic", "pointer_range": [[0, 0], [4, 0.4]]}),
                       time_mode="absolute")))
    for i in (1, 2, 3):
        d = np.array([x.pointer_pos - 1.0 for x in voci(g)[i]])
        t = np.array([x.onset for x in voci(g)[i]])
        r = d[t > 1] / (0.4 * t[t > 1] / 4.0)
        assert np.ptp(r) < 0.02 and abs(r[0]) > 0.01                      # segno e proporzione fissi
    ok("la direzione dello scarto di una voce non cambia, la grandezza segue l'inviluppo")

    def gemelli(gruppo):
        stocastico = dict(num_voices=4, pointer={"strategy": "stochastic", "pointer_range": 0.3})
        extra = {"rng_group": "g"} if gruppo else {}
        g = carica(brano(S(stocastico, stream_id="a", **extra), S(stocastico, stream_id="b", **extra)))
        return [v[0].pointer_pos for v in voci(g, 0)] == [v[0].pointer_pos for v in voci(g, 1)]
    assert not gemelli(False) and gemelli(True)
    ok("due stream con lo stesso rng_group hanno le voci negli stessi punti")


# 3. Il pitch -------------------------------------------------------------------------------
def pitch():
    def sem(vox, **extra):
        return semitoni(carica(brano(S(vox, **extra))))
    assert sem(dict(num_voices=4, pitch={"strategy": "step", "step": 3})) == [0, 3, 6, 9]
    assert sem(dict(num_voices=4, pitch={"strategy": "range", "pitch_range": 12})) == [0, 4, 8, 12]
    assert sem(dict(num_voices=4, pitch={"strategy": "step", "step": 12})) == [0, 12, 24, 36]
    st = sem(dict(num_voices=5, pitch={"strategy": "stochastic", "pitch_range": 12}))
    assert st[0] == 0 and all(abs(x) <= 12 for x in st) and len(set(st)) == 5
    assert sem(dict(num_voices=6, pitch={"strategy": "chord", "chord": "dom7"})) == [0, 4, 7, 10, 12, 16]
    assert sem(dict(num_voices=4, pitch={"strategy": "chord", "chord": "dom7", "inversion": 1})) == [0, 3, 6, 8]
    assert sem(dict(num_voices=8, pitch={"strategy": "spectral"})) == [0, 12, 19, 24, 28, 31, 34, 36]
    ok("step, range, stochastic, chord (estensione per ottave e rivolto), spectral")

    def rat(vox):
        return [round(abs(x), 4) for x in primi(carica(brano(S(vox))), lambda x: x.pitch_ratio)]
    assert rat(dict(num_voices=4, pitch={"strategy": "step", "step": 2, "unit": "ratio"})) == [1.0, 2.0, 4.0, 8.0]
    assert rat(dict(num_voices=4, pitch={"strategy": "range", "pitch_range": 2, "unit": "ratio"})) \
        == [1.0, 1.2599, 1.5874, 2.0]
    assert rat(dict(num_voices=4, pitch={"strategy": "step", "step": 100, "unit": "cents"})) \
        == [round(2 ** (i * 100 / 1200), 4) for i in range(4)]
    assert rat(dict(num_voices=4, pitch={"strategy": "step", "step": 1, "unit": {"edo": 31}})) \
        == [round(2 ** (i / 31), 4) for i in range(4)]
    ok("la geometria e' dell'unita': additiva nel logaritmo per le EDO (anche {edo: 31}), geometrica per ratio")

    for strategia, extra in (("chord", {"chord": "maj7"}), ("spectral", {})):
        for unita in ("cents", "ratio"):
            assert prova(brano(S(dict(num_voices=4, pitch={"strategy": strategia, "unit": unita, **extra}))))[0] \
                == "InvalidStrategyConfigError"
    assert prova(brano(S(dict(num_voices=4, pitch={"strategy": "chord", "chord": "maj7", "unit": "semitones"})))) is None
    assert prova(brano(S(dict(num_voices=4, pitch={"strategy": "range", "semitone_range": 12}))))[0] \
        == "InvalidStrategyConfigError"
    ok("chord, chord_progression e spectral rifiutano ogni unita' diversa dai semitoni; semitone_range e' rifiutato")

    assert CHORD_INTERVALS["dom7"] == [0, 4, 7, 10] and CHORD_INTERVALS["maj"] == [0, 4, 7]
    assert CHORD_INTERVALS["altered"] == [0, 4, 7, 10, 13, 15, 20]
    per_note = {}
    for nome, iv in CHORD_INTERVALS.items():
        per_note.setdefault(len(iv), []).append(nome)
    assert per_note == {3: ["maj", "min", "dim", "aug", "sus2", "sus4"],
                        4: ["dom7", "maj7", "min7", "dim7", "minmaj7"],
                        5: ["dom9", "maj9", "min9", "9sus4"],
                        6: ["dom9s11", "maj9s11", "min11"],
                        7: ["dom13", "min13", "maj13s11", "altered"]}
    ok("il catalogo degli accordi: 6 a tre note, 5 a quattro, 4 a cinque, 3 a sei, 4 a sette")

    # il pitch di voce si compone con quello dello stream e col verso
    g = carica(brano(S(dict(num_voices=3, pitch={"strategy": "step", "step": 12}), pitch={"semitones": 7},
                       pointer={"speed_ratio": -1, "start": 1.5})))
    r = primi(g, lambda x: x.pitch_ratio)
    assert np.allclose(r, [-2 ** (7 / 12) * 2 ** i for i in range(3)])
    ok("il fattore di voce si moltiplica sul rapporto dello stream e ne conserva il segno")


# 4. La progressione ------------------------------------------------------------------------
def progressione():
    def prog(p, n=4, interp="step", vl="nearest", tm="normalized", dur=9.0, **extra):
        d = dict(duration=dur, density=20, time_mode=tm, grain={"duration": 0.06},
                 pointer={"speed_ratio": 0.0, "start": 1.0},
                 voices=dict(num_voices=n, pitch={"strategy": "chord_progression", "progression": p,
                                                  "interp": interp, "voice_leading": vl}))
        d.update(extra)
        return stream(**d)

    def sem(g, t):
        out = []
        for v in voci(g):
            c = [x for x in v if abs(x.onset - t) < 0.06]
            out.append(round(12 * np.log2(abs(c[0].pitch_ratio)), 2))
        return out
    P = [[0, "maj7"], [0.34, "min7"], [0.67, "dom7"]]
    g = carica(brano(prog(P)))
    assert sem(g, 1.0) == [0, 4, 7, 11] and sem(g, 4.0) == [0, 3, 7, 10] and sem(g, 7.0) == [0, 4, 7, 10]
    ok("maj7 -> min7 -> dom7: la terza e la settima scendono di un semitono, poi la terza risale")

    g = carica(brano(prog(P, pitch={"semitones": {"type": "step", "points": [[0, 0], [0.34, 5], [0.67, -2]]}})))
    assert sem(g, 1.0) == [0, 4, 7, 11] and sem(g, 4.0) == [5, 8, 12, 15] and sem(g, 7.0) == [-2, 2, 5, 8]
    g = carica(brano(prog(P, interp="linear")))
    assert sem(g, 4.0)[1] == 3.3 and sem(g, 5.0)[1] == 3.64                    # glissando fra due accordi
    g = carica(brano(prog([[0, "maj7"], [3, "min7"], [6, "dom7"]], tm="absolute")))
    assert sem(g, 1.0) == [0, 4, 7, 11] and sem(g, 7.0) == [0, 4, 7, 10]
    ok("il moto della radice si somma al voicing; interp lineare da' il glissando; i tempi seguono il time_mode")

    for p, atteso in (([[0, {"chord": "min7", "inversion": 2}]], [0, 3, 5]), ([[0, "min7", 2]], [0, 3, 5])):
        assert sem(carica(brano(prog(p, n=3))), 1.0) == atteso
    for p, tipo in (([[0.5, "maj"], [0.1, "min"]], "InvalidStrategyConfigError"), ([], "InvalidStrategyConfigError"),
                    ([[0, "foo"]], "InvalidStrategyConfigError")):
        assert prova(brano(prog(p, n=3)))[0] == tipo
    assert prova(brano(prog(P, interp="spline")))[0] == "InvalidStrategyConfigError"
    assert prova(brano(prog(P, vl="random")))[0] == "InvalidStrategyConfigError"
    ok("rivolto come terzo elemento o come dizionario; tempi decrescenti, lista vuota, accordo, interp e "
       "voice_leading sconosciuti sono errori")

    def moto(a, b):
        return sum(abs(x - y) for x, y in zip(a, b))

    def offs(p, n, vl):
        return ChordProgressionPitchStrategy(p, voice_leading=vl)._build_offsets(n)
    diversi = set()
    for a, b in itertools.product([k for k, v in CHORD_INTERVALS.items() if len(v) == 4], repeat=2):
        for inv in range(4):
            p = [[0, a], [1, b, inv]]
            pos, near = offs(p, 4, "positional"), offs(p, 4, "nearest")
            assert moto(*near) <= moto(*pos)
            if near != pos:
                diversi.add(inv)
    assert diversi == {3}
    p = [[0, "maj7"], [1, "minmaj7", 3]]
    assert moto(*offs(p, 4, "positional")) == 9 and moto(*offs(p, 4, "nearest")) == 3
    assert offs(p, 9, "nearest") != offs(p, 9, "positional")
    assert offs(p, 10, "nearest") == offs(p, 10, "positional")
    ok("nearest non fa mai peggio di positional; fra accordi di quattro note differisce solo col terzo rivolto "
       "(9 contro 3 semitoni); da 10 voci in su ripiega su positional")


# 5. Il numero di voci ----------------------------------------------------------------------
def numero_di_voci():
    def base(vox):
        return stream(duration=10.0, density=10, time_mode="normalized", grain={"duration": 0.02},
                      pointer={"speed_ratio": 0.0, "start": 1.0}, voices=vox)
    g = carica(brano(base(dict(num_voices=[[0, 1], [0.5, 4], [1, 2.5]]))))
    assert len(voci(g)) == 4

    def volume_a(g, i, t):
        c = [x for x in voci(g)[i] if abs(x.onset - t) < 0.06]
        return round(c[0].volume, 2) if c else None
    for t, i, atteso in ((1.0, 1, -4.44), (3.0, 2, -1.94), (7.5, 3, -12.04), (9.5, 2, -3.74)):
        v = float(np.interp(t / 10, [0, 0.5, 1], [1, 4, 2.5]))
        assert abs(volume_a(g, i, t) - 20 * np.log10(v - np.floor(v))) < 0.15, (t, i)
        assert abs(volume_a(g, i, t) - atteso) < 0.15
    assert volume_a(g, 0, 1.0) == 0.0 and volume_a(g, 3, 1.0) is None
    ok("voce di confine: volume di 20 log10(f) dB (f = parte frazionaria); le voci intere a 0 dB, le spente senza grani")

    g = carica(brano(base(dict(num_voices={"type": "step", "points": [[0, 1], [0.5, 3]]}))))
    assert [len(v) for v in voci(g)] == [100, 49, 49] and min(x.onset for x in voci(g)[1]) > 5.0
    assert all(x.volume == 0.0 for v in voci(g) for x in v)
    ok("con interpolazione a gradini e punti interi le voci si accendono di colpo, senza fade")


# 6. Lo scatter -----------------------------------------------------------------------------
def scatter():
    def prova_scatter(dist, sc, **extra):
        g = carica(brano(stream(duration=20.0, density=20, grain={"duration": 0.02},
                                pointer={"speed_ratio": 0.0, "start": 1.0}, distribution=dist,
                                voices=dict(num_voices=2, scatter=sc), **extra)))
        return [np.diff([x.onset for x in v]) for v in voci(g)]
    for sc in (0.0, 0.5, 1.0):
        a, b = prova_scatter(0.0, sc)
        assert np.allclose(a[:min(len(a), len(b))], b[:min(len(a), len(b))])
    a, b = prova_scatter(1.0, 0.0)
    assert np.allclose(a[:len(b)], b[:len(a)])
    for sc in (0.5, 1.0):
        a, b = prova_scatter(1.0, sc)
        n = min(len(a), len(b))
        rho = np.corrcoef(a[:n], b[:n])[0, 1]
        teoria = (1 - sc) / np.sqrt((1 - sc) ** 2 + sc ** 2)
        assert abs(rho - teoria) < 0.08, (sc, rho, teoria)
    ok("griglia sincrona: onset identici per qualunque scatter; griglia stocastica: la correlazione degli "
       "intervalli e' (1-s)/sqrt((1-s)^2+s^2), cioe' 1, 0.71 e 0")

    assert prova(brano(S(dict(num_voices=2, scatter=1.5))))[0] == "ParameterBoundError"
    assert prova(brano(S(dict(num_voices=2, scatter=[[0, 0], [4, 1]], ), time_mode="absolute"))) is None
    ok("scatter da 0 a 1, anche come inviluppo")


# 7. L'esempio completo ---------------------------------------------------------------------
def esempio_completo():
    doc = yaml.safe_load(open(AQUI.parent / "voices" / "voices.yml"))
    g = carica(doc)
    tutti = [x for v in voci(g) for x in v]
    assert len(voci(g)) == 70 and all(voci(g))
    assert 30000 < len(tutti) < 31500, len(tutti)
    r = np.array([abs(x.pitch_ratio) for x in tutti])
    assert abs(12 * np.log2(r.max()) - 792) < 0.01 and abs(r.min() - 0.125) < 1e-9
    assert r.max() > 1e19
    voce13 = [abs(x.pitch_ratio) for x in voci(g)[13]]
    voce12 = [abs(x.pitch_ratio) for x in voci(g)[12]]
    assert min(voce13) > 1000 and max(voce12) < 1000
    ok(f"voices: 70 liste, {len(tutti)} grani; rapporto massimo 2^66 ({r.max():.3g}); "
       "dalla voce 13 in poi il rapporto supera 1000")

    v5 = voci(g)[5]                                  # voce 5: scarto di pan = 5 * passo, piu' pan_range (+-15)
    assert max(abs(x.pan) for x in v5 if x.onset < 23.9) <= 15.01
    assert max(abs(x.pan - 300.0) for x in v5 if x.onset > 36.1) <= 15.01
    ok("il passo del pan e' chiuso fino a 24 s e si apre fino a 36 s")


# 8. Che cosa il blocco lascia passare ------------------------------------------------------
def lascia_passare():
    assert prova(brano(S(dict(num_voices=4, pitch={"step": 3})))) == ("KeyError", False)
    assert prova(brano(S(dict(num_voices=4, pitch={"strategy": "arpeggio"})))) == ("StrategyNotFoundError", True)
    ok("un sotto-blocco senza strategy e' un KeyError nudo; un nome sconosciuto e' un errore del motore")

    from pge.strategies.voice_onset_strategy import VOICE_ONSET_STRATEGIES
    from pge.strategies.voice_pan_strategy import VOICE_PAN_STRATEGIES
    from pge.strategies.voice_pitch_strategy import VOICE_PITCH_STRATEGIES
    from pge.strategies.voice_pointer_strategy import VOICE_POINTER_STRATEGIES
    assert sorted(VOICE_ONSET_STRATEGIES) == ["geometric", "linear", "stochastic"]
    assert sorted(VOICE_POINTER_STRATEGIES) == ["linear", "stochastic"]
    assert sorted(VOICE_PAN_STRATEGIES) == ["range", "step", "stochastic"]
    assert sorted(VOICE_PITCH_STRATEGIES) == ["chord", "chord_progression", "range", "spectral", "step", "stochastic"]
    ok("le strategie dei quattro assi: 3 di onset, 2 di pointer, 3 di pan, 6 di pitch")


def main():
    for f in (una_voce, onset_pointer_pan, pitch, progressione, numero_di_voci, scatter, esempio_completo,
              lascia_passare):
        print(f"--- {f.__name__}")
        f()
    print("\ntutte le verifiche passano")


if __name__ == "__main__":
    main()
