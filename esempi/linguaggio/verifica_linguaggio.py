#!/usr/bin/env python3
"""Verifica le affermazioni del capitolo 4 sul linguaggio YAML di PGE.

Uso:  python esempi/linguaggio/verifica_linguaggio.py

PGE_DIR (default ../PythonGranularEngine) indica il repo del motore: se ne usano src/
e refs/ (il campione `voice.wav`). Ogni sezione controlla con `assert` una parte del
capitolo, sul motore vero:
  1. lo stream minimo: valori predefiniti, grani che ricostruiscono la sorgente, guadagno
     del rendering;
  2. `null` e `0` per `onset` e `duration`;
  3. `solo` e `mute` contano la presenza della chiave, non il suo valore;
  4. le espressioni matematiche e i loro limiti;
  5. la banda dei `_range`: forma, ancora, unità relativa, banda che varia nel tempo;
  6. l'inviluppo: forme, interpolazioni, bordi, tempo normalizzato, integrale;
  7. l'esempio del puntatore (capitolo 4, figura sul `speed_ratio`);
  8. ciò che il linguaggio lascia passare: chiavi sconosciute e valori che non si controllano;
  9. il seme e `rng_group`;
 10. lo stream come file (`file:`), che esiste in `main` e non nella 9.1.0.
"""
import contextlib
import hashlib
import io
import os
import sys
import tempfile
import textwrap
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml

AQUI = Path(__file__).resolve().parent
PGE = Path(os.environ.get("PGE_DIR", AQUI.parents[1].parent / "PythonGranularEngine"))
REFS = str(PGE / "refs")
sys.path.insert(0, str(PGE / "src"))

from pge import api  # noqa: E402
from pge.engine.generator import Generator  # noqa: E402
from pge.envelopes.envelope import Envelope  # noqa: E402
from pge.shared.exceptions import EngineError  # noqa: E402

TMP = tempfile.mkdtemp()


def carica(documento, nome="t.yml"):
    """Il Generator di un documento (dizionario o testo), col rumore di stdout/stderr tolto."""
    percorso = os.path.join(TMP, nome)
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(documento if isinstance(documento, str) else yaml.safe_dump(documento))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return api.load_generator(percorso, samples_dir=REFS)


def stream(sid="a", **chiavi):
    return {"stream_id": sid, "sample": "voice.wav", **chiavi}


def brano(*stream_, **top):
    return {**top, "streams": list(stream_)}


def grani(g, i=0):
    return g.streams[i].voices[0]


def impronta(s):
    """Impronta dei grani di uno stream, con gli onset relativi all'onset dello stream."""
    h = hashlib.sha256()
    for voce in s.voices:
        for gr in voce:
            h.update(repr((round(gr.onset - s.onset, 9), gr.duration, gr.pointer_pos,
                           gr.pitch_ratio, gr.volume, gr.pan)).encode())
    return h.hexdigest()[:12]


def ok(msg):
    print("ok  ", msg)


# 1. Lo stream minimo -----------------------------------------------------------------------
def stream_minimo():
    s = carica(brano(stream(), seed=1)).streams[0]
    durata_file = sf.info(os.path.join(REFS, "voice.wav")).duration
    assert s.onset == 0.0 and s.duration == durata_file
    assert s.fill_factor.get_value(0) == 2 and s.density is None
    assert s.grain_duration.get_value(0) == 0.05
    assert s.volume.get_value(0) == 0.0 and s.pan.get_value(0) == 0.0
    assert list(s.window_table_map) == ["hanning"]
    ok(f"valori predefiniti: durata del file ({durata_file:.3f} s), fill factor 2, grano 50 ms, "
       "0 dB, pan 0, finestra hanning")

    gr = s.voices[0]
    assert len(gr) == 78
    assert all(g.pitch_ratio == 1.0 and abs(g.pointer_pos - g.onset) < 1e-9 for g in gr)
    assert abs(gr[1].onset - gr[0].onset - 0.025) < 1e-9
    ok("78 grani a distanza di 25 ms, rapporto di altezza 1, posizione di lettura = istante")

    sr, n = 44100, round(0.05 * 44100)
    somma = np.zeros(round(durata_file * sr) + 2 * n)
    for g in gr:
        a = round(g.onset * sr)
        somma[a:a + n] += np.hanning(n)
    interno = somma[round(0.05 * sr):round(1.9 * sr)]
    assert interno.min() > 0.998 and interno.max() <= 1.0 + 1e-12
    ok(f"le finestre sommano a 1 con scarto di {1 - interno.min():.4f} (min {interno.min():.4f}, "
       f"max {interno.max():.4f})")

    yml = os.path.join(TMP, "min.yml")
    Path(yml).write_text("seed: 1\nstreams:\n  - stream_id: a\n    sample: voice.wav\n")
    out = os.path.join(TMP, "min.aif")
    with contextlib.redirect_stdout(io.StringIO()):
        api.render_file(yml, out, samples_dir=REFS, output_sr=44100)
    y = sf.read(out)[0][:, 0]
    x = sf.read(os.path.join(REFS, "voice.wav"))[0].mean(axis=1)
    i = slice(int(0.05 * sr), int(1.9 * sr))
    guadagno = (y[i] * x[i]).sum() / (x[i] * x[i]).sum()
    residuo = np.sqrt(((y[i] - guadagno * x[i]) ** 2).mean() / (y[i] ** 2).mean())
    assert 0.69 < guadagno < 0.71 and residuo < 0.10
    ok(f"rendering NumPy a 44,1 kHz: guadagno {guadagno:.4f} (1/sqrt(2) = 0.7071), "
       f"residuo {20 * np.log10(residuo):.1f} dB")


# 2. null e 0 -------------------------------------------------------------------------------
def null_e_zero():
    durata_file = sf.info(os.path.join(REFS, "voice.wav")).duration
    s = carica(brano(stream(duration=None, onset=None))).streams[0]
    assert s.duration == durata_file and s.onset == 0.0
    s = carica(brano(stream(duration=0))).streams[0]
    assert s.duration == 0 and sum(len(v) for v in s.voices) == 0
    assert carica(brano(stream(onset=0))).streams[0].onset == 0
    ok("`null` vale come chiave assente; `duration: 0` non attiva il valore predefinito e non dà grani")


# 3. solo e mute ----------------------------------------------------------------------------
def solo_mute():
    ids = lambda *s: [x.stream_id for x in carica(brano(*s)).streams]
    assert ids(stream("a"), stream("b", mute=True)) == ["a"]
    assert ids(stream("a"), stream("b", mute=False)) == ["a"]
    assert ids(stream("a"), stream("b", solo=False), stream("c")) == ["b"]
    assert ids(stream("a", mute=True), stream("b", solo=True), stream("c", solo=True),
               stream("d")) == ["b", "c"]
    assert ids(stream("a", mute=True, solo=True), stream("b")) == ["a"]
    ok("`mute: false` muta, `solo: false` attiva la modalità solo, più `solo` convivono, `solo` batte `mute`")


# 4. Espressioni ----------------------------------------------------------------------------
def espressioni():
    ev = Generator("x.yml")._eval_math_expressions
    with contextlib.redirect_stdout(io.StringIO()):
        assert ev("(1/20)") == 0.05 and ev("(10/2)") == 5.0 and ev("(pi)") == np.pi
        assert abs(ev("(2**(7/12))") - 1.4983070768766815) < 1e-12
        assert ev("(abs(-3))") == 3 and ev("(int(7.9))") == 7 and ev("(7//2)") == 3
        assert ev([0, "(1/2)"]) == [0, 0.5] and ev({"a": "(1/4)"}) == {"a": 0.25}
        for non_valutata in ("(max(3, 7))", "(min(3,7))", "(pow(2, 3))", "(7%2)", "(sin(1))", "(1/0)"):
            assert ev(non_valutata) == non_valutata
        assert ev("voice (1).wav") == "voice 1.wav" and ev("a(2+3)b") == "a5b"
    ok("espressioni: operatori, abs/int/float, costanti; `max`, `min`, `pow` con due argomenti non si "
       "valutano (la virgola non è nel pattern); `%` e `sin` neppure; vale per ogni stringa, nomi di file compresi")


# 5. La banda -------------------------------------------------------------------------------
def banda():
    import random
    from pge.shared.distribution_strategy import DistributionFactory
    atteso = {("uniform", "center"): (200, 400, 300), ("uniform", "min"): (300, 500, 400),
              ("gaussian", "center"): (200, 400, 300), ("gaussian", "min"): (300, 500, 400)}
    for (forma, ancora), (lo, hi, media) in atteso.items():
        d = DistributionFactory.create(forma, rng=random.Random(1), anchor=ancora)
        v = np.array([d.sample(300, 200) for _ in range(300000)])
        assert v.min() >= lo and v.max() <= hi and abs(v.mean() - media) < 1.0, (forma, ancora)
        if forma == "gaussian":
            estremi = np.mean((v == lo) | (v == hi))
            assert 0.002 < estremi < 0.0035 and abs(v.std() - 200 / 6) < 1.0
    ok("banda: [200, 400] o [300, 500]; gaussiana con deviazione standard 200/6, "
       "circa lo 0,27% dei valori appiattito sugli estremi")

    durate = lambda g: np.array([x.duration for x in grani(g)])
    d = durate(carica(brano(stream(duration=2, grain={"duration": 0.05, "duration_range": 0.01}), seed=1)))
    assert 0.045 <= d.min() and d.max() <= 0.055 and d.std() > 0.001
    d = durate(carica(brano(stream(duration=2, grain={"duration": 0.05}), seed=1)))
    assert d.min() == d.max() == 0.05
    d = durate(carica(brano(stream(duration=2, grain={"duration": 0.05, "duration_range": 0.5,
                                                      "duration_range_unit": "relative"}), seed=1)))
    assert 0.0375 <= d.min() and d.max() <= 0.0625
    ok("un `_range` dichiarato si applica senza altre chiavi; `duration_range_unit: relative` è una frazione")

    g = carica(brano(stream(duration=10, grain={"duration": [[0, 0.02], [10, 0.2]],
                                                "duration_range": [[0, 0.0], [10, 0.1]]}), seed=1))
    gr = grani(g)
    scarto = [(x.onset, x.duration - (0.02 + 0.018 * x.onset)) for x in gr]
    assert all(abs(d) <= 0.5 * 0.01 * t + 1e-9 for t, d in scarto)
    assert max(abs(d) for t, d in scarto if t > 9) > 0.03
    ok("maschera di tendenza: centro e larghezza entrambi inviluppi, ogni grano sta dentro la semi-banda "
       "che si apre nel tempo (±0,005 s per secondo)")


# 6. L'inviluppo ----------------------------------------------------------------------------
def inviluppo():
    e = Envelope([[10, 40], [0, 5], [30, 5]])
    assert e.breakpoints == [[0, 5], [10, 40], [30, 5]]
    e = Envelope({"type": "cubic", "points": [[0, 5], [10, 40], [30, 5]]})
    assert max(e.evaluate(t) for t in np.linspace(0, 30, 3001)) <= 40.0 + 1e-9
    e = Envelope({"type": "cubic", "points": [[0, 0], [1, 10]]})
    assert abs(e.evaluate(0.25) - 10 * (3 * 0.25 ** 2 - 2 * 0.25 ** 3)) < 1e-12
    e = Envelope({"type": "step", "points": [[0, 5], [10, 40], [20, 10]]})
    assert [e.evaluate(t) for t in (-1, 9.99, 10, 15, 25)] == [5, 5, 40, 40, 10]
    ok("punti ordinati; cubica monotona senza sovraelongazione; con due punti è lo smoothstep; "
       "gradini col valore del punto di sinistra")

    e = Envelope([[0, 5, "cubic"], [0.3, 30, "linear"], [0.7, 10, "step"], [1, 5]])
    assert [type(s.strategy).__name__ for s in e.segments] == [
        "CubicInterpolation", "LinearInterpolation", "StepInterpolation"]
    ok("il tipo di un punto vale per il segmento fino al successivo")

    e = Envelope([[[0, 0.01], [100, 0.2]], 30, 4])
    punti = e.breakpoints
    assert len(punti) == 8 and [round(p[0], 3) for p in punti[::2]] == [0.0, 7.5, 15.0, 22.5]
    assert abs(e.evaluate(7.4999) - 0.2) < 1e-4 and e.evaluate(7.51) < 0.011 and e.evaluate(40) == 0.2
    ok("formato compatto: quattro cicli di 7,5 s da 0,01 a 0,2, salto di 1 microsecondo fra un ciclo e l'altro")

    e = Envelope([[2, 1], [4, 3]])
    assert [e.evaluate(t) for t in (0, 2, 3, 4, 10)] == [1, 1, 2, 3, 3]
    assert e.integrate(0, 10) == 2 * 1 + 4 + 6 * 3
    ok("fuori dai punti vale il valore del punto più vicino, anche nell'integrale")

    durata = lambda doc: carica(doc).streams[0].density.value.breakpoints
    assert durata(brano(stream(duration=10, time_mode="normalized", density=[[0, 5], [1, 50]]))) \
        == [[0, 5], [10, 50]]
    assert durata(brano(stream(duration=10, density={"points": [[0, 5], [1, 50]], "time_unit": "normalized"}))) \
        == [[0, 5], [10, 50]]
    assert durata(brano(stream(duration=10, density={"points": [[0, 5], [1, 50]], "time_mode": "normalized"}))) \
        == [[0, 5], [1, 50]]
    assert durata(brano(stream(duration=10, time_mode="normalized",
                               density={"points": [[0, 5], [10, 50]], "time_mode": "absolute"}))) \
        == [[0, 5], [100, 50]]
    assert durata(brano(stream(duration=10, time_mode="normalized",
                               density={"points": [[0, 5], [10, 50]], "time_unit": "absolute"}))) \
        == [[0, 5], [10, 50]]
    ok("tempo normalizzato per lo stream; nel dizionario di un parametro la chiave locale è `time_unit`, "
       "e un `time_mode` locale non ha effetto")


# 7. L'esempio del puntatore ----------------------------------------------------------------
def puntatore():
    punti = [[0.1, 1.0], [0.15, 2.6], [0.3, -0.3], [0.5, 0.0]]
    g = carica(brano(stream("pointer_freeze", duration=7.0, time_mode="normalized",
                            pointer={"speed_ratio": punti}), seed=2026))
    s = g.streams[0]
    env = s._pointer.speed_ratio.value
    assert [[round(t, 6), v] for t, v in env.breakpoints] == [[0.7, 1.0], [1.05, 2.6], [2.1, -0.3], [3.5, 0.0]]
    file_ = s.sample_dur_sec
    t = np.linspace(0, 7, 70001)
    pos = np.array([env.integrate(0, x) for x in t])
    esaurimento = t[np.argmax(pos >= file_)]
    assert abs(esaurimento - 1.35) < 0.01
    negativa = t[[env.evaluate(x) < 0 for x in t]]
    assert abs(negativa.min() - 2.0) < 0.02 and abs(negativa.max() - 3.5) < 0.01
    gr = grani(g)
    segno = lambda a, b: {np.sign(x.pitch_ratio) for x in gr if a <= x.onset < b}
    assert segno(0, 1.99) == {1.0} and segno(1.99, 3.5) == {-1.0} and segno(3.5, 7) == {1.0}
    fermo = {round(x.pointer_pos, 3) for x in gr if x.onset >= 3.5}
    assert fermo == {0.342}
    ok(f"puntatore: esaurisce il file ({file_:.3f} s) a {esaurimento:.2f} s; velocità negativa fra "
       f"{negativa.min():.2f} e {negativa.max():.2f} s, con i grani invertiti; da 3,5 s legge sempre a 0,342 s")


# 8. Ciò che il linguaggio lascia passare ---------------------------------------------------
def lascia_passare():
    base = len(grani(carica(brano(stream(), seed=1))))
    for doc in (brano(stream(desnity=40), seed=1), brano(stream(grain={"duraton": 0.2}), seed=1),
                brano(stream(), seed=1, bpm=60), brano(stream(time_mode="normalised"), seed=1)):
        assert len(grani(carica(doc))) == base
    for doc in (brano(stream(distribution_mode="gausian")), brano(stream(range_anchor="max")),
                brano(stream(density=-5))):
        try:
            carica(doc)
        except EngineError:
            continue
        raise AssertionError(doc)
    ok("chiavi sconosciute e `time_mode: normalised` ignorati senza avviso; "
       "`distribution_mode`, `range_anchor` e i limiti dei parametri sbagliati sono errori")


# 9. Seme e rng_group -----------------------------------------------------------------------
def seme():
    g = carica(brano(stream(), seed=0))
    assert g.seed == 0 and not g.seed_is_session
    g = carica(brano(stream()))
    assert g.seed_is_session and isinstance(g.seed, int)
    comuni = dict(duration=2, density=40, distribution=1, grain={"duration": 0.05, "duration_range": 0.02})
    g = carica(brano(stream("a", **comuni), stream("b", **comuni), seed=7))
    assert impronta(g.streams[0]) != impronta(g.streams[1])
    g = carica(brano(stream("a", rng_group="g", **comuni), stream("b", rng_group="g", **comuni), seed=7))
    assert impronta(g.streams[0]) == impronta(g.streams[1])
    ok("`seed: 0` è dichiarato; senza seme il motore ne sceglie uno di sessione; due stream uguali con "
       "`stream_id` diversi hanno grani diversi, con lo stesso `rng_group` grani identici")


# 10. Stream come file ----------------------------------------------------------------------
def stream_come_file():
    try:
        from pge.engine import stream_files  # noqa: F401
    except ImportError:
        print("salta: `file:` non è in questa versione del motore (è in main, dopo la 9.1.0)")
        return
    from pge.rendering.stream_cache_manager import StreamCacheManager
    os.makedirs(os.path.join(TMP, "streams"), exist_ok=True)

    def scrivi(percorso, testo):
        Path(TMP, percorso).write_text(textwrap.dedent(testo))

    lab = """
        seed: 1441
        streams:
          - stream_id: lab_nome
            onset: 0
            duration: 3
            sample: voice.wav
            density: 40
            grain: {duration: 0.05, duration_range: 0.02}
            pan_range: 40
        """
    scrivi("streams/risacca.yml", lab)
    scrivi("lab.yml", lab)
    scrivi("m1.yml", "seed: 1441\nstreams:\n  - file: streams/risacca.yml\n    onset: 12.5\n")
    scrivi("m2.yml", "seed: 1441\nstreams:\n  - file: streams/risacca.yml\n    stream_id: lab_nome\n"
                     "    onset: 12.5\n")
    g1, g2, g0 = carica(open(Path(TMP, "m1.yml")).read(), "m1.yml"), None, None
    g2 = carica(open(Path(TMP, "m2.yml")).read(), "m2.yml")
    g0 = carica(open(Path(TMP, "lab.yml")).read(), "lab.yml")
    s1, s2, s0 = g1.streams[0], g2.streams[0], g0.streams[0]
    assert s1.stream_id == "risacca" and s1.onset == 12.5 and s1.duration == 3
    assert impronta(s1) != impronta(s0) and impronta(s2) == impronta(s0)
    ok("senza `stream_id` accanto a `file:` l'id è il nome del file e la realizzazione cambia; "
       "con lo stesso id del laboratorio è identica")

    scrivi("streams/rg.yml", lab.replace("pan_range: 40", "pan_range: 40\n            rng_group: g1"))
    scrivi("m3.yml", "seed: 1441\nstreams:\n  - file: streams/rg.yml\n    stream_id: altro\n")
    scrivi("rg.yml", Path(TMP, "streams/rg.yml").read_text())
    assert impronta(carica(Path(TMP, "m3.yml").read_text(), "m3.yml").streams[0]) \
        == impronta(carica(Path(TMP, "rg.yml").read_text(), "rg.yml").streams[0])
    ok("con `rng_group` nel file la realizzazione non dipende dal nome dato dal master")

    errori = {
        "m4.yml": ("StreamFileKeyError", "seed: 1\nstreams:\n  - file: streams/risacca.yml\n    density: 3\n"),
        "m5.yml": ("StreamFileDuplicateIdError", "seed: 1\nstreams:\n  - file: streams/risacca.yml\n"
                                                 "  - file: streams/risacca.yml\n    onset: 5\n"),
    }
    scrivi("streams/catena.yml", "streams:\n  - file: risacca.yml\n")
    errori["m6.yml"] = ("StreamFileChainError", "seed: 1\nstreams:\n  - file: streams/catena.yml\n")
    for nome, (tipo, testo) in errori.items():
        try:
            carica(testo, nome)
        except EngineError as err:
            assert type(err).__name__ == tipo, (nome, type(err).__name__)
        else:
            raise AssertionError(nome)
    scrivi("m7.yml", "seed: 1441\nstreams:\n  - file: streams/risacca.yml\n    stream_id: a\n"
                     "  - file: streams/risacca.yml\n    stream_id: b\n    onset: 5\n")
    g7 = carica(Path(TMP, "m7.yml").read_text(), "m7.yml")
    assert impronta(g7.streams[0]) != impronta(g7.streams[1])
    ok("chiave estranea, stesso id importato due volte e catena sono errori; due id diversi, due realizzazioni")

    def fingerprint(testo, nome):
        g = carica(testo, nome)
        m = StreamCacheManager(cache_path=os.path.join(TMP, "m.json"), samples_dir=REFS,
                               renderer_type="csound", seed=g.declared_seed)
        return {k: m.compute_fingerprint(d) for k, d in g.stream_data_map.items()}

    scrivi("streams/ris.yml", "seed: 1\nstreams:\n  - stream_id: ris\n    duration: 3\n    sample: voice.wav\n"
                              "    density: 40\n")
    dentro = "seed: 1\nstreams:\n  - stream_id: ris\n    onset: 12.5\n    duration: 3\n    sample: voice.wav\n" \
             "    density: 40\n"
    fuori = "seed: 1\nstreams:\n  - file: streams/ris.yml\n    onset: 12.5\n"
    prima = fingerprint(fuori, "f1.yml")
    assert prima == fingerprint(dentro, "f2.yml")
    scrivi("streams/ris.yml", Path(TMP, "streams/ris.yml").read_text().replace("density: 40", "density: 41"))
    assert fingerprint(fuori, "f1.yml") != prima
    ok("la cache vede lo stream risolto: stesso fingerprint dentro il master o in un file, cambia se il file cambia")


if __name__ == "__main__":
    for prova in (stream_minimo, null_e_zero, solo_mute, espressioni, banda, inviluppo, puntatore,
                  lascia_passare, seme, stream_come_file):
        prova()
    print("\ntutte le verifiche passano")
