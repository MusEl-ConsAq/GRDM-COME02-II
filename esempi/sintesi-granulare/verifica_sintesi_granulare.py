#!/usr/bin/env python3
"""Verifica le affermazioni del capitolo 2 (la sintesi granulare) che un programma puo' controllare.

Uso:  python esempi/sintesi-granulare/verifica_sintesi_granulare.py

Il capitolo 2 e' una rassegna: le sue date, i suoi virgolettati, le cifre e i numeri di pagina di
Gabor, Xenakis, Roads, Truax, Lippe e Dutilleux si controllano sulle fonti, e questo script non lo
fa. Controlla con `assert` il resto, con numpy dove basta la matematica e sul motore vero dove si
parla di PGE:
  1. il segnale elementare di Gabor: larghezze, area unitaria, convenzione della costante;
  2. l'aritmetica delle tabelle e degli esempi (frequenza di modulazione, fill factor, densita');
  3. il grano di PGE: otto campi;
  4. la tabella dei sette parametri della nuvola: ogni chiave YAML esiste e agisce sul grano;
  5. fill factor e densita': due modi di dire la stessa cosa;
  6. le finestre di PGE messe a confronto con quelle di Roads;
  7. la finestratura come modulazione: le bande laterali di un flusso regolare, a 1/IOT.

PGE_DIR (default ../PythonGranularEngine) indica il repo del motore: se ne usa src/. Il campione e'
un tono generato qui, quindi non serve refs/voice.wav. Passa sulla 9.1.0 e su main.
"""
import contextlib
import io
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml

AQUI = Path(__file__).resolve().parent
PGE = Path(os.environ.get("PGE_DIR", AQUI.parents[1].parent / "PythonGranularEngine"))
sys.path.insert(0, str(PGE / "src"))

from pge import api  # noqa: E402
from pge.controllers.window_registry import WindowRegistry  # noqa: E402
from pge.core.grain import Grain  # noqa: E402
from pge.rendering.numpy_window_registry import NumpyWindowRegistry  # noqa: E402

TMP = tempfile.mkdtemp()
SR = 48000
FILE = 3.0                                    # durata del tono di prova, in secondi
F0 = 1000.0                                   # la sua frequenza
sf.write(os.path.join(TMP, "tono.wav"), 0.5 * np.sin(2 * np.pi * F0 * np.arange(round(FILE * SR)) / SR),
         SR, subtype="FLOAT")


def stream(sid="a", **chiavi):
    return {"stream_id": sid, "sample": "tono.wav", **chiavi}


def brano(*stream_, seed=2026, **top):
    return {"seed": seed, **top, "streams": list(stream_)}


def scrivi(documento, nome):
    percorso = os.path.join(TMP, nome)
    with open(percorso, "w", encoding="utf-8") as f:
        f.write(yaml.safe_dump(documento))
    return percorso


def carica(documento, nome="t.yml"):
    """Il Generator di un documento, col rumore di stdout/stderr tolto."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return api.load_generator(scrivi(documento, nome), samples_dir=TMP)


def grani(documento, nome="t.yml"):
    return carica(documento, nome).streams[0].voices[0]


def ok(msg):
    print("ok  ", msg)


# 1. Il segnale elementare di Gabor ------------------------------------------------------------
def gabor():
    """s(t) = exp(-a^2 (t - t0)^2) exp(i 2 pi f0 t): Dt = sqrt(pi)/a, Df = a/sqrt(pi), Dt Df = 1."""
    n, T = 2 ** 18, 80.0
    t = (np.arange(n) - n // 2) * (T / n)
    f = np.fft.fftshift(np.fft.fftfreq(n, T / n))

    def scarti(s):
        """Scarto quadratico medio della distribuzione d'energia in tempo e in frequenza."""
        p = np.abs(s) ** 2
        p /= p.sum()
        q = np.abs(np.fft.fftshift(np.fft.fft(s))) ** 2
        q /= q.sum()
        mt, mf = (p * t).sum(), (q * f).sum()
        return np.sqrt((p * (t - mt) ** 2).sum()), np.sqrt((q * (f - mf) ** 2).sum()), mf

    for a in (0.7, 1.4, 2.8, 0.5, 4.0):                   # i primi tre sono quelli della figura
        st, sf_, mf = scarti(np.exp(-(a ** 2) * t ** 2) * np.exp(2j * np.pi * 6.0 * t))
        dt, df = 2 * np.sqrt(np.pi) * st, 2 * np.sqrt(np.pi) * sf_   # la convenzione di Gabor
        assert abs(mf - 6.0) < 1e-3                       # f0 sposta la cella, non ne cambia la forma
        assert abs(dt - np.sqrt(np.pi) / a) < 1e-3 * dt and abs(df - a / np.sqrt(np.pi)) < 1e-3 * df
        assert abs(dt * df - 1) < 1e-3                    # alfa cambia la forma della cella, non l'area
        assert abs(st * sf_ - 1 / (4 * np.pi)) < 1e-4     # con gli scarti quadratici medi, 1/(4 pi)
    ok("Dt = sqrt(pi)/alfa, Df = alfa/sqrt(pi), Dt*Df = 1 per ogni alfa; con gli scarti quadratici "
       "medi lo stesso segnale da' 1/(4 pi): la costante dipende da come si definiscono le larghezze")

    # il minimo si raggiunge solo con il segnale gaussiano: un impulso di Hann sta sopra
    s = np.where(np.abs(t) < 0.5, np.cos(np.pi * t) ** 2, 0.0) * np.exp(2j * np.pi * 6.0 * t)
    st, sf_, _ = scarti(s)
    assert 1.0 < (2 * np.sqrt(np.pi)) ** 2 * st * sf_ < 2.0
    ok(f"un impulso di Hann ha Dt*Df = {(2 * np.sqrt(np.pi)) ** 2 * st * sf_:.3f} > 1: l'uguaglianza e' "
       "dei segnali elementari gaussiani")


# 2. L'aritmetica delle tabelle e degli esempi --------------------------------------------------
def aritmetica():
    # tabella della durata del grano: la frequenza di modulazione e' l'inverso della durata
    for d, f in ((200e-6, 5000), (500e-6, 2000), (1e-3, 1000), (10e-3, 100), (50e-3, 20), (100e-3, 10),
                 (200e-3, 5)):
        assert abs(1 / d - f) < 1e-9 * f
    # Truax: grani da 8 ms senza ritardo, 125 Hz; grano da 15 ms con 5 ms di ritardo, 50 Hz
    assert abs(1 / 0.008 - 125) < 1e-9 and abs(1 / (0.015 + 0.005) - 50) < 1e-9
    # sotto i 2 ms la fondamentale supera i 500 Hz; con grani da 20 ms le bande distano 50 Hz
    assert abs(1 / 0.002 - 500) < 1e-9 and abs(1 / 0.020 - 50) < 1e-9
    ok("tabella della durata del grano: la frequenza di modulazione e' 1/durata (anche 8 ms = 125 Hz, "
       "15 + 5 ms = 50 Hz, 2 ms = 500 Hz, 20 ms = 50 Hz)")

    ff = lambda densita, durata: densita * durata
    assert abs(ff(20, 0.1) - 2) < 1e-12 and abs(ff(20, 0.01) - 0.2) < 1e-12
    assert abs(ff(20, 0.001) - 0.02) < 1e-12          # con 1 ms il prodotto e' 0,02, non 0,2
    assert abs(ff(50, 0.02) - 1) < 1e-12              # cinquanta grani da 20 ms riempiono un secondo
    for D in (0.001, 0.02, 0.05):
        assert abs(ff(2 / D, D) - 2) < 1e-12          # la regola 2/D e' fill factor 2
    ok("fill factor: venti grani da 100 ms = 2; da 10 ms = 0,2; da 1 ms = 0,02 (non 0,2); "
       "cinquanta da 20 ms = 1; densita' 2/D = fill factor 2")

    assert abs(20 / 0.008 - 2500) < 1e-9 and 2375 < 2500
    ok("DMX-1000: venti voci e grano minimo di 8 ms danno 2 500 grani/s; i 2 375 di Riverrun stanno sotto")


# 3. Il grano -------------------------------------------------------------------------------------
def il_grano():
    assert Grain.__slots__ == ("onset", "duration", "pointer_pos", "pitch_ratio", "volume", "pan",
                               "sample_table", "envelope_table")
    ok("il grano ha otto campi: istante, durata, posizione di lettura, rapporto di altezza, volume, pan, "
       "tabella del campione e della finestra")


# 4. La tabella dei sette parametri della nuvola --------------------------------------------------
def sette_parametri():
    # istante d'inizio e durata della nuvola: onset e duration dello stream
    gr = grani(brano(stream(onset=1.5, duration=2.0, density=20)))
    assert gr[0].onset == 1.5 and all(1.5 <= g.onset and g.onset + g.duration <= 3.5 + 1e-9 for g in gr)

    # durata del grano: costante, variabile (inviluppo), casuale fra due limiti (duration_range)
    assert {g.duration for g in grani(brano(stream(duration=2.0, density=20, grain={"duration": 0.05})))} == {0.05}
    d = [g.duration for g in grani(brano(stream(duration=2.0, density=20,
                                                grain={"duration": [[0, 0.01], [2, 0.1]]})))]
    assert all(b >= a for a, b in zip(d, d[1:])) and d[-1] > 5 * d[0]
    d = [g.duration for g in grani(brano(stream(duration=2.0, density=200,
                                                grain={"duration": 0.05, "duration_range": 0.02})))]
    assert 0.04 - 1e-9 <= min(d) and max(d) <= 0.06 + 1e-9 and max(d) - min(d) > 0.015

    # densita' variabile nel tempo: density (o fill_factor) e distribution
    gr = grani(brano(stream(duration=2.0, density=[[0, 10], [2, 50]], grain={"duration": 0.01})))
    assert abs(len(gr) - 60) <= 3                                 # l'integrale della rampa
    iot = np.diff([g.onset for g in grani(brano(stream(duration=2.0, density=20, distribution=0)))])
    assert np.allclose(iot, 0.05)
    iot = np.diff([g.onset for g in grani(brano(stream(duration=20.0, density=20, distribution=1)))])
    assert iot.std() > 0.02                                       # d = 1: intervalli casuali in [0, 2/density]

    # banda di frequenze: nel campionamento e' la trasposizione, pitch (rapporto e banda)
    p = [g.pitch_ratio for g in grani(brano(stream(duration=2.0, density=200,
                                                   pitch={"ratio": 1.0, "range": 0.1})))]
    assert 0.95 - 1e-9 <= min(p) and max(p) <= 1.05 + 1e-9 and max(p) - min(p) > 0.05
    assert {g.pitch_ratio for g in grani(brano(stream(duration=2.0, density=20, pitch={"ratio": 2.0})))} == {2.0}

    # inviluppo d'ampiezza della nuvola: volume
    assert {g.volume for g in grani(brano(stream(duration=2.0, density=20, volume=-6)))} == {-6.0}

    # forma d'onda nei grani: sample e pointer. A velocita' 1 la lettura segue lo stream, a 0 resta ferma
    gr = grani(brano(stream(duration=2.0, density=20)))
    assert all(abs(g.pointer_pos - (g.onset - gr[0].onset)) < 1e-9 for g in gr)
    gr = grani(brano(stream(duration=2.0, density=20, pointer={"speed_ratio": 0})))
    assert len({round(g.pointer_pos, 9) for g in gr}) == 1

    # dispersione spaziale: pan e pan_range
    pan = [g.pan for g in grani(brano(stream(duration=2.0, density=200, pan=20, pan_range=10)))]
    assert 15 - 1e-9 <= min(pan) and max(pan) <= 25 + 1e-9 and max(pan) - min(pan) > 5
    ok("sette parametri: onset/duration, grain.duration (valore, inviluppo, duration_range), density e "
       "distribution, pitch (ratio e range), volume, sample e pointer, pan e pan_range")


# 5. Fill factor e densita' -----------------------------------------------------------------------
def fill_factor():
    def onset(**k):
        return [g.onset for g in grani(brano(stream(duration=2.0, **k)))]
    a = onset(fill_factor=2.0, grain={"duration": 0.1})          # densita' = fill_factor / durata = 20
    b = onset(density=20, grain={"duration": 0.1})               # fill factor = 20 * 0.1 = 2
    assert len(a) == len(b) and np.allclose(a, b)
    c = onset(density=10, fill_factor=1.0, grain={"duration": 0.1})
    assert np.allclose(np.diff(c), 0.1)                          # insieme, vince fill_factor
    ok("fill_factor 2 con grani da 100 ms e density 20 danno gli stessi istanti; insieme vince fill_factor")


# 6. Le finestre di PGE e quelle di Roads --------------------------------------------------------
def finestre():
    nomi = set(WindowRegistry.all_names())
    assert {"gaussian", "bartlett", "triangle", "sinc", "expodec", "rexpodec", "exporise", "rexporise"} <= nomi
    # non ci sono ne' la quasi-gaussiana (finestra di Tukey) ne' il segmento a tre tratti (trapezio)
    assert not [n for n in nomi if any(s in n for s in ("tukey", "quasi", "trapez", "segment"))]
    assert "hanning" in nomi and WindowRegistry.canonical("triangle") == "bartlett"
    reg = NumpyWindowRegistry()
    x = np.linspace(0, 1, 1001)
    w = {n: reg.get(n, 1001) for n in ("gaussian", "sinc", "expodec", "rexpodec", "exporise", "rexporise")}

    assert np.allclose(w["gaussian"], w["gaussian"][::-1]) and w["gaussian"].argmax() == 500
    assert np.allclose(w["sinc"], np.sinc(2 * x - 1), atol=1e-12) and w["sinc"].min() > -1e-12
    ok("gaussiana simmetrica; sinc = np.sinc su [-1, 1], cioe' il solo lobo centrale (nulla ai bordi, mai negativa)")

    # nessuna ha il tratto di attacco di Roads: un estremo e' a 1, l'altro a 0
    for n in ("expodec", "rexpodec", "exporise", "rexporise"):
        assert {round(float(w[n][0]), 9), round(float(w[n][-1]), 9)} == {0.0, 1.0}
    # rexpodec di PGE: parte da 1 e decade come un esponenziale (e^(-4x), riportata a [0, 1])
    atteso = (np.exp(-4 * x) - np.exp(-4)) / (1 - np.exp(-4))
    assert np.allclose(w["rexpodec"], atteso)
    # expodec di PGE: tiene e cade alla fine, e' l'esponenziale rovesciata
    assert np.allclose(w["expodec"], 1 - (np.exp(4 * x) - 1) / (np.exp(4) - 1))
    # exporise e rexporise sono le due, lette all'indietro
    assert np.allclose(w["exporise"], w["expodec"][::-1]) and np.allclose(w["rexporise"], w["rexpodec"][::-1])
    ok("la rexpodec di PGE (attacco pieno, decadimento esponenziale) e' la expodec di Roads; la rexporise di PGE "
       "(salita esponenziale lenta, a fondo scala) e' la rexpodec di Roads; la expodec di PGE (tiene, poi cade) "
       "e la exporise non sono forme di Roads")


# 7. La finestratura come modulazione -------------------------------------------------------------
def bande_laterali():
    """Un flusso regolare di grani da 20 ms su un tono a 1000 Hz: l'inviluppo ha periodo 20 ms."""
    def spettro(**k):
        yml = scrivi(brano(stream(duration=FILE, distribution=0, **k)), "m.yml")
        out = os.path.join(TMP, "m.aif")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            api.render_file(yml, out, samples_dir=TMP, output_sr=SR)
        y = sf.read(out)[0]
        y = y if y.ndim == 1 else y[:, 0]
        seg = y[SR // 2: SR // 2 + 2 * SR]                       # 2 s = 100 periodi da 20 ms
        s = np.abs(np.fft.rfft(seg)) / len(seg) * 2
        return lambda hz: s[round(hz * len(seg) / SR)]

    # grani adiacenti (fill factor 1): inviluppo sin^2 periodico, bande a +-1/IOT = +-50 Hz, meta' del portante
    a = spettro(density=50, grain={"duration": 0.02})
    assert abs(20 * np.log10(a(F0 + 50) / a(F0)) - 20 * np.log10(0.5)) < 0.2
    assert abs(20 * np.log10(a(F0 - 50) / a(F0)) - 20 * np.log10(0.5)) < 0.2
    assert a(F0 + 100) / a(F0) < 1e-3 and a(F0 - 100) / a(F0) < 1e-3
    ok("grani da 20 ms adiacenti, finestra di Hann: bande laterali a +-50 Hz, 6 dB sotto il portante, nessuna a +-100 Hz")

    # a fattore 2 le finestre sommano a una costante: restano solo residui, a +-1/IOT = +-100 Hz
    b = spettro(density=100, grain={"duration": 0.02})
    assert b(F0 + 50) / b(F0) < 1e-6 and b(F0 + 100) / b(F0) < 1e-3
    ok(f"a fattore 2 le bande si elidono: a +-100 Hz restano {20 * np.log10(b(F0 + 100) / b(F0)):.0f} dB, "
       "a +-50 Hz nulla")


if __name__ == "__main__":
    for prova in (gabor, aritmetica, il_grano, sette_parametri, fill_factor, finestre, bande_laterali):
        prova()
    print("\ntutte le verifiche passano")
