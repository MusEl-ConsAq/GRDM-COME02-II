#!/usr/bin/env python3
"""Verifica le cifre del capitolo 10 sul brano *mare-nostrum*.

Uso:  python esempi/mare-nostrum/verifica_brano.py [../mare-nostrum/configs/mare-nostrum.yml]

Il brano non e' in questo repo (e' incompiuto): lo script legge il master dal
repository del brano, accanto a questo (o dal percorso passato come argomento),
e controlla con `assert` che cosa del capitolo un programma puo' verificare. Le
cifre sono quelle del master al commit 1979ce1 (22 ottobre 2026), col motore
alla versione che il repository del brano fissa (1188dbc). Se il brano e'
andato avanti le verifiche falliscono: e' il segnale che il capitolo va
riletto, non che lo script sia sbagliato.

Il motore e' quello del submodule `engine/` del repository del brano, se c'e';
altrimenti `PGE_DIR` (default ../PythonGranularEngine). Il numero di grani
dipende da durata, densita' e seme, non dal contenuto audio: il corpus non e'
versionato, e i campioni sono rumore sintetico dai nomi giusti (come fanno i
test del brano). Ogni sezione controlla una parte del capitolo:
  1. la testa del master e gli stream: due forme, nessuno silenziato;
  2. il profilo nel tempo: tre gruppi, due vuoti, la sovrapposizione massima;
  3. i campioni: quattordici, due tipi di nome, uno per forma di stream;
  4. le copie (`stream25`, `stream26`, `stream27`) e la famiglia dei primi stream;
  5. i due vocabolari: durate dei grani, densita', gate, voci, finestre;
  6. gli otto stream a valori predefiniti, che sono lo stream minimo del capitolo 4;
  7. i grani di ogni stream, sul motore vero, e le densita' che ne vengono;
  8. le copie hanno un'altra realizzazione, e con `rng_group` gli stessi grani;
  9. la tabella del capitolo coincide con i dati;
 10. il modello di costo del capitolo 7 applicato al brano;
 11. le intestazioni di PGE-ui e la regola «un file per stream» del repository del brano.
"""
import contextlib
import copy
import io
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parents[1]
MASTER = Path(sys.argv[1] if len(sys.argv) > 1
              else REPO.parent / "mare-nostrum" / "configs" / "mare-nostrum.yml").resolve()
BRANO = MASTER.parent.parent  # la radice del repository del brano
if "PGE_DIR" in os.environ:
    PGE = Path(os.environ["PGE_DIR"])
elif (BRANO / "engine" / "src").is_dir():
    PGE = BRANO / "engine"
else:
    PGE = REPO.parent / "PythonGranularEngine"
sys.path.insert(0, str(PGE / "src"))
sys.path.insert(0, str(AQUI))

from disposizione import codice, e_predefinito, leggi, stream_del_master, tratti_vuoti, valori  # noqa: E402

CAPITOLO = REPO / "docs" / "sezioni" / "10-USO-COMPOSITIVO.md"

# I grani che il motore produce con il seme dichiarato, uno stream alla volta
# (la colonna «Grani» della tabella del capitolo).
GRANI = {
    "stream2": 304042, "stream3": 934191, "stream9": 1524526, "stream5": 112093,
    "stream6": 302588, "stream10": 633345, "stream7": 34053, "stream8": 190663,
    "stream24": 2727140, "stream21": 22201, "stream22": 2296, "stream25": 302955,
    "stream27": 1523628, "stream26": 665552, "stream23": 5706, "stream18": 5598,
    "stream16": 4798, "stream20": 5219, "stream17": 4158, "stream19": 4853,
    "stream13": 3381, "stream14": 3998, "stream12": 100329, "stream15": 1999,
}
TOTALE = 9419312
GRUPPI = (  # (primo, ultimo) stream per ingresso, e i grani del gruppo
    ("stream2", "stream8", 4035501), ("stream24", "stream23", 5249478),
    ("stream18", "stream15", 134333))
RIVERRUN = 2375  # grani al secondo, il massimo di Riverrun (Truax 1988, p. 25)

SECONDI = (  # i vuoti del master, come intervalli [a, b]
    (277.852, 278.634), (674.954, 827.803))


def ok(testo):
    print("ok:", testo)


def vicino(a, b, tol=2e-3):
    return abs(a - b) <= tol


# --- il brano, letto dal master -------------------------------------------------

def master_e_stream():
    master = leggi(MASTER)
    return master, stream_del_master(master, str(MASTER.parent))


def fine(s):
    return float(s["onset"]) + float(s["duration"])


# --- 1. la testa e gli stream -------------------------------------------------------

def testa_e_stream():
    master, ss = master_e_stream()
    assert master["duration"] == 998.833 and master["bpm"] == 120 and master["seed"] == 1441
    ok("testa del master: seed 1441, 998,833 s (16 minuti e 39), 120 bpm")
    voci = master["streams"]
    con_file = [v["file"] for v in voci if "file" in v]
    dentro = [v["stream_id"] for v in voci if "file" not in v]
    assert len(voci) == 24 and len(con_file) == 11 and len(dentro) == 13
    assert [s["stream_id"] for s in ss].count("stream2") == 1
    assert len({s["stream_id"] for s in ss}) == 24
    assert sorted(os.path.basename(f)[:-4] for f in con_file) == sorted(
        ["stream2", "stream3", "stream5", "stream6", "stream7", "stream8", "stream9",
         "stream10", "stream25", "stream26", "stream27"])
    assert sorted(dentro) == sorted(f"stream{n}" for n in range(12, 25))
    assert not any(s.get("mute") or s.get("solo") for s in ss)
    ok("24 stream, 11 importati da file e 13 scritti dentro il master, nessuno silenziato")


# --- 2. il profilo nel tempo ---------------------------------------------------------

def sovrapposizioni(intervalli):
    """(a, b, n): i tratti in cui n intervalli sono insieme."""
    eventi = sorted([(a, 1) for a, b in intervalli] + [(b, -1) for a, b in intervalli])
    n, prima, tratti = 0, None, []
    for t, d in eventi:
        if prima is not None and t > prima:
            tratti.append((prima, t, n))
        n += d
        prima = t
    return tratti


def profilo():
    master, ss = master_e_stream()
    righe = [dict(onset=float(s["onset"]), durata=float(s["duration"]), muto=False) for s in ss]
    ultimo = max(fine(s) for s in ss)
    assert vicino(ultimo, 988.833) and vicino(master["duration"], ultimo + 10)
    vuoti = tratti_vuoti(righe, master["duration"])
    attesi = list(SECONDI) + [(988.833, 998.833)]
    assert len(vuoti) == 3 and all(vicino(a, x) and vicino(b, y) for (a, b), (x, y) in zip(vuoti, attesi)), vuoti
    assert 0.78 < vuoti[0][1] - vuoti[0][0] < 0.79 and round(vuoti[1][1] - vuoti[1][0]) == 153
    ok("tre tratti senza stream: 0,8 s a 278 s, 153 s da 675 a 828 s, la coda di 10 s dopo l'ultimo stream")
    tratti = sovrapposizioni([(float(s["onset"]), fine(s)) for s in ss])
    massimo = max(n for a, b, n in tratti)
    assert massimo == 9
    cima = [(a, b) for a, b, n in tratti if n == 9]
    assert len(cima) == 1 and vicino(cima[0][0], 889.152) and vicino(cima[0][1], 939.152)
    ok("la sovrapposizione massima e' di nove stream, per cinquanta secondi, da 889 a 939 s")
    # i tre gruppi: gli stream fra un vuoto e l'altro
    taglio = [b for a, b in SECONDI]
    gruppi = [[], [], []]
    for s in ss:
        gruppi[sum(float(s["onset"]) >= t - 1e-6 for t in taglio)].append(s)
    assert [len(g) for g in gruppi] == [8, 7, 9]
    for g, (primo, ultimo_stream, _) in zip(gruppi, GRUPPI):
        ordine = [s["stream_id"] for s in sorted(g, key=lambda s: (float(s["onset"]), s["stream_id"]))]
        assert ordine[0] == primo and ordine[-1] == ultimo_stream, (ordine, primo, ultimo_stream)
    picchi = [max(n for a, b, n in sovrapposizioni([(float(s["onset"]), fine(s)) for s in g])) for g in gruppi]
    assert picchi == [7, 5, 9]
    primo = sovrapposizioni([(float(s["onset"]), fine(s)) for s in gruppi[0]])
    sette = [(a, b) for a, b, n in primo if n == 7]
    assert len(sette) == 1 and vicino(sette[0][0], 112.003) and vicino(sette[0][1], 125.309)
    ok("tre gruppi di 8, 7 e 9 stream, con al massimo 7 (intorno al secondo 112), 5 e 9 stream insieme")
    d = {s["stream_id"]: s for s in ss}
    solo = [(a, b) for a, b, n in tratti if n == 1 and 278 < a < 342]
    assert len(solo) == 1 and solo[0][1] - solo[0][0] > 60
    assert vicino(solo[0][0], float(d["stream24"]["onset"])) and vicino(solo[0][1], float(d["stream21"]["onset"]))
    ok("`stream24` suona da solo per oltre un minuto (62,8 s) all'inizio del secondo gruppo")
    uno = [(a, b) for a, b, n in tratti if n == 1 and a < 278]
    assert len(uno) == 1 and uno[0][0] > 260 and vicino(uno[0][1], fine(d["stream8"]))
    ok("alla fine del primo gruppo resta il solo `stream8`, che finisce a 277,9 s")


# --- 3. i campioni ----------------------------------------------------------------

def campioni():
    master, ss = master_e_stream()
    nomi = {s["sample"] for s in ss}
    assert len(nomi) == 14
    frammenti = sorted(n for n in nomi if n.startswith("001-"))
    numerati = sorted(n for n in nomi if re.fullmatch(r"\d{3}\.wav", n))
    assert len(frammenti) == 5 and len(numerati) == 9 and len(frammenti) + len(numerati) == len(nomi)
    assert numerati[0] == "002.wav" and numerati[-1] == "016.wav"
    importati = {v["file"] for v in master["streams"] if "file" in v}
    for v in master["streams"]:
        if "file" in v:
            assert leggi(MASTER.parent / v["file"])["streams"][0]["sample"] in frammenti
        else:
            assert v["sample"] in numerati
    ok("quattordici campioni: cinque frammenti `001-*` negli stream importati, nove file numerati "
       f"da 002 a 016 negli stream scritti dentro (importati: {len(importati)})")


# --- 4. copie e famiglia -----------------------------------------------------------

def pulito(s):
    return {k: v for k, v in s.items() if k not in ("stream_id", "onset") and not k.startswith("_")}


def copie_e_famiglia():
    _, ss = master_e_stream()
    d = {s["stream_id"]: s for s in ss}
    assert pulito(d["stream25"]) == pulito(d["stream6"])
    assert pulito(d["stream27"]) == pulito(d["stream9"])
    a, b = pulito(d["stream26"]), pulito(d["stream3"])
    assert a["grain"]["duration"] == [[0, 0.006]] and b["grain"]["duration"] != a["grain"]["duration"]
    a["grain"] = {k: v for k, v in a["grain"].items() if k != "duration"}
    b["grain"] = {k: v for k, v in b["grain"].items() if k != "duration"}
    assert a == b
    for copia, origine in (("stream25", "stream6"), ("stream26", "stream3"), ("stream27", "stream9")):
        assert float(d[copia]["onset"]) > fine(d[origine])
    assert [round(float(d[x]["onset"])) for x in ("stream25", "stream27", "stream26")] == [414, 415, 426]
    ok("`stream25` e `stream27` hanno gli stessi valori di `stream6` e `stream9` a ogni chiave; "
       "`stream26` e' `stream3` con la durata del grano fissa a 6 ms; entrano a 414, 415 e 426 s")
    famiglia = [d[x] for x in ("stream2", "stream3", "stream5", "stream6", "stream7", "stream8",
                               "stream9", "stream10", "stream25", "stream26", "stream27")]
    assert sum(valori(s["fill_factor"]) == [4.0] for s in famiglia) == 10 and valori(d["stream10"]["fill_factor"]) == [2.0]
    assert sum("read_direction" in s["grain"] for s in famiglia) == 10 and "read_direction" not in d["stream10"]["grain"]
    assert all(s["pan_range"] == 360 for s in famiglia)
    rapporto = {}
    for s in famiglia:
        rapporto.setdefault(max(valori(s["pitch"]["ratio"])) if s["stream_id"] != "stream2" else 0.2,
                            []).append(s["stream_id"])
    assert {k: len(v) for k, v in rapporto.items()} == {0.2: 6, 0.5: 2, 1.0: 3}
    assert valori(d["stream2"]["pitch"]["ratio"]) == [0.2, 0.4, 0.2]
    assert all(s["pitch"].get("range", 0) == 0.05 for s in famiglia if max(valori(s["pitch"]["ratio"])) <= 0.4)
    velocita = [v for s in famiglia for v in valori(s["pointer"]["speed_ratio"])]
    assert max(velocita) == 0.35 and max(valori(d["stream8"]["pointer"]["speed_ratio"])) == 0.35
    assert max(v for s in famiglia if s["stream_id"] != "stream8" for v in valori(s["pointer"]["speed_ratio"])) == 0.1
    brevi = [v for s in famiglia for v in valori(s["grain"]["duration"])]
    assert min(brevi) == 0.0004 and max(brevi) < 0.019
    ok("famiglia di undici stream: fattore di riempimento 4 in dieci, verso di lettura in dieci, pan su 360 gradi, "
       "rapporto di altezza 0,2 / 0,5 / 1 in sei / due / tre, puntatore a 0,1 o meno (0,35 solo in `stream8`)")


# --- 5. i due vocabolari --------------------------------------------------------------

def vocabolari():
    _, ss = master_e_stream()
    d = {s["stream_id"]: s for s in ss}
    durate = {s["stream_id"]: valori(s["grain"]["duration"]) for s in ss}
    assert min(min(v) for v in durate.values()) == 0.0001 and durate["stream24"] == [0.0001]
    assert max(max(v) for v in durate.values()) == 3 and max(durate["stream22"]) == 3 and durate["stream23"] == [3.0]
    assert round(3 / 0.0001) == 30000  # piu' di quattro ordini di grandezza
    ok("le durate dichiarate dei grani vanno da 0,1 ms (`stream24`) a 3 s (`stream22`, `stream23`)")
    s24 = d["stream24"]
    assert s24["pitch"]["ratio"] == 8 and s24["voices"]["num_voices"] == 4 and s24["grain"]["envelope"] == "all"
    assert min(valori(s24["fill_factor"])) == 0.61 and max(valori(s24["fill_factor"])) == 0.9
    assert 0.0001 * 48000 < 5
    ok("`stream24`: grani di 0,1 ms (meno di cinque campioni a 48 kHz), fattore di riempimento 0,61-0,9, "
       "rapporto di altezza 8, quattro voci, finestra `all`")
    for sid, lo, hi in (("stream22", 3.09, 32.9), ("stream23", 2.53, 38.78)):
        assert "fill_factor" not in d[sid] and min(valori(d[sid]["density"])) == lo and max(valori(d[sid]["density"])) == hi
        assert isinstance(d[sid]["grain"]["envelope"], list) and len(d[sid]["grain"]["envelope"]) == 4
    assert d["stream23"]["voices"]["num_voices"] == 4 and d["stream23"]["volume_range"] == 20
    assert 1 / 0.1 == 10 and 3 / 0.1 == 30
    ok("`stream22` e `stream23`: densita' dichiarata (3-33 e 2,5-39 grani/s), lista di quattro finestre, "
       "grani da 10 a 30 volte il limite di 100 ms; `stream23` ha quattro voci e 20 dB di banda di volume")
    gate = {s["stream_id"]: s["deviation_probability"] for s in ss if "deviation_probability" in s}
    assert gate == {"stream24": 40, "stream23": 70, "stream12": [[0.4967, 0], [0.99663, 100]]}
    ok("il gate `deviation_probability` e' in tre stream: 40 in `stream24`, 70 in `stream23`, "
       "in rampa da 0 a 100 nella seconda meta' di `stream12`")
    s12 = d["stream12"]
    assert valori(s12["voices"]["num_voices"]) == [1.0, 12.74] and s12["voices"]["pitch"]["chord"] == "maj13s11"
    assert s12["voices"]["pitch"]["inversion"] == 3 and s12["voices"]["onset_offset"]["max_offset"] == 10
    assert s12["voices"]["pointer"]["pointer_range"] == 1 and valori(s12["voices"]["pan"]["spread"]) == [60.0, 60.0, 180.0]
    assert valori(s12["grain"]["duration"]) == [0.001, 0.0031, 0.05]
    ok("`stream12`: da 1 a 12,74 voci, accordo `maj13s11` in terzo rivolto, scarto di onset fino a 10 s, "
       "puntatore stocastico su tutto il file, pan da 60 a 180 gradi, grani da 1 a 50 ms")
    s21 = d["stream21"]
    assert s21["grain"]["envelope"] == {"from": "hanning", "to": "rexpodec", "curve": [[0.65, 0], [1, 1]]}
    assert s21["voices"]["num_voices"] == 1 and s21["voices"]["pitch"]["chord"] == "sus4"
    ok("`stream21`: finestra da Hann a `rexpodec` dal 65% dello stream, accordo `sus4` con una voce sola")


# --- 6. gli stream a valori predefiniti ------------------------------------------------

def predefiniti():
    _, ss = master_e_stream()
    d = {s["stream_id"]: s for s in ss}
    minimi = sorted(s["stream_id"] for s in ss if e_predefinito(s))
    assert minimi == [f"stream{n}" for n in range(14, 21)], minimi
    s13 = pulito(d["stream13"])
    assert (s13.pop("pan"), s13.pop("pan_range")) == (-110, 80)
    assert e_predefinito({**s13, "stream_id": "x", "onset": 0})
    assert all(valori(d[f"stream{n}"]["fill_factor"]) == [2.0] for n in range(13, 21))
    assert 2 / 0.05 == 40
    assert sorted(round(float(d[f"stream{n}"]["duration"]), 3) for n in range(13, 21)) == \
        [50, 84.552, 100, 104, 120, 121.356, 130.506, 140]
    ok("da `stream13` a `stream20`: valori predefiniti (`stream13` ha in piu' un pan a -110 con banda 80), "
       "quaranta grani al secondo, durate da 50 a 140 s")


# --- il motore ---------------------------------------------------------------------

_CAMPIONI = {}


def campioni_sintetici():
    """Una cartella di rumore dai nomi dei campioni del brano (8 s, 48 kHz, stereo)."""
    if "dir" not in _CAMPIONI:
        _, ss = master_e_stream()
        d = tempfile.mkdtemp(prefix="campioni_")
        rng = np.random.default_rng(0)
        for n in sorted({s["sample"] for s in ss}):
            sf.write(os.path.join(d, n), 0.3 * rng.standard_normal((48000 * 8, 2)), 48000)
        _CAMPIONI["dir"] = d
    return _CAMPIONI["dir"]


def carica(percorso):
    from pge import api, configure_clip_logger, configure_engine_logger
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        configure_clip_logger(enabled=False, console_enabled=False, file_enabled=False)
        configure_engine_logger(yaml_name="verifica_brano", log_dir=tempfile.mkdtemp(prefix="log_"))
        return api.load_generator(str(percorso), samples_dir=campioni_sintetici())


def carica_documento(streams, seed=1441):
    percorso = os.path.join(tempfile.mkdtemp(prefix="doc_"), "t.yml")
    with open(percorso, "w", encoding="utf-8") as f:
        yaml.safe_dump({"seed": seed, "streams": [
            {k: v for k, v in s.items() if not k.startswith("_")} for s in streams]}, f, sort_keys=False)
    return carica(percorso)


def lista(stream):
    """I grani di uno stream, con gli onset relativi a quello dello stream."""
    return np.array([(g.onset - stream.onset, g.duration, g.pointer_pos, g.pitch_ratio, g.volume, g.pan)
                     for v in stream.voices for g in v]).reshape(-1, 6)


def _grani_dello_stream(i):
    gen = _GEN.setdefault("g", carica(MASTER))
    s = gen.streams[i]
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        voci = s.voices
    onset = np.concatenate([[g.onset for g in v] for v in voci if v]) if any(voci) else np.array([])
    durata = np.concatenate([[g.duration for g in v] for v in voci if v]) if any(voci) else np.array([])
    eventi = np.concatenate([onset, onset + durata])
    segno = np.concatenate([np.ones_like(onset), -np.ones_like(onset)])
    concorrenti = int(np.cumsum(segno[np.argsort(eventi, kind="stable")]).max()) if len(onset) else 0
    return dict(stream=s.stream_id, voci=len(voci), grani=int(len(onset)),
                picco=int(np.bincount(np.floor(onset - s.onset).astype(int)).max()) if len(onset) else 0,
                concorrenti=concorrenti)


_GEN = {}


# --- 7. i grani ---------------------------------------------------------------------

def grani():
    campioni_sintetici()
    n = len(GRANI)
    with ProcessPoolExecutor(max_workers=max(1, min(4, os.cpu_count() or 1))) as pool:
        risultati = list(pool.map(_grani_dello_stream, range(n)))
    per_stream = {r["stream"]: r for r in risultati}
    assert {k: v["grani"] for k, v in per_stream.items()} == GRANI, \
        {k: (GRANI[k], per_stream[k]["grani"]) for k in GRANI if GRANI[k] != per_stream[k]["grani"]}
    assert sum(GRANI.values()) == TOTALE
    ok(f"grani del brano: {TOTALE:,} ({TOTALE / 1e6:.1f} milioni), uno stream alla volta come nella tabella".replace(",", " "))
    for (primo, ultimo, atteso), nomi in zip(GRUPPI, gruppi_per_nome()):
        assert sum(GRANI[x] for x in nomi) == atteso, (primo, atteso)
    ok("grani per gruppo: 4 035 501, 5 249 478 e 134 333")
    tre = sum(GRANI[x] for x in ("stream24", "stream9", "stream27"))
    assert tre / TOTALE > 0.60 and GRANI["stream24"] == max(GRANI.values())
    ok(f"`stream24`, `stream9` e `stream27` hanno il {100 * tre / TOTALE:.0f}% dei grani")
    otto = sum(GRANI[f"stream{n}"] for n in range(13, 21))
    assert 33500 < otto < 34500
    ok(f"da `stream13` a `stream20`: {otto} grani in tutto")
    assert per_stream["stream24"]["picco"] > 35000 and per_stream["stream24"]["picco"] / RIVERRUN > 15
    assert per_stream["stream24"]["picco"] == max(r["picco"] for r in risultati)
    ok(f"`stream24` arriva a {per_stream['stream24']['picco']} grani al secondo, "
       f"{per_stream['stream24']['picco'] / RIVERRUN:.1f} volte il massimo di Riverrun")
    assert per_stream["stream22"]["concorrenti"] == 102 and per_stream["stream23"]["concorrenti"] == 460
    ok("grani sovrapposti: fino a 102 in `stream22` e a 460 in `stream23`")
    assert per_stream["stream12"]["voci"] == 13 and per_stream["stream23"]["voci"] == 4
    assert per_stream["stream3"]["voci"] == 4 and per_stream["stream9"]["voci"] == 2
    ok("il motore prepara 13 liste di voci per `stream12` (da 1 a 12,74 voci)")


def gruppi_per_nome():
    _, ss = master_e_stream()
    taglio = [b for a, b in SECONDI]
    gruppi = [[], [], []]
    for s in ss:
        gruppi[sum(float(s["onset"]) >= t - 1e-6 for t in taglio)].append(s["stream_id"])
    return gruppi


# --- 8. realizzazioni ----------------------------------------------------------------

def realizzazioni():
    _, ss = master_e_stream()
    d = {s["stream_id"]: s for s in ss}
    assert GRANI["stream25"] != GRANI["stream6"] and GRANI["stream27"] != GRANI["stream9"]
    ok("`stream25` e `stream27` hanno gli stessi valori di `stream6` e `stream9` e un'altra realizzazione: "
       "302 955 grani contro 302 588, 1 523 628 contro 1 524 526")
    a, b = copy.deepcopy(d["stream6"]), copy.deepcopy(d["stream25"])
    a["rng_group"] = b["rng_group"] = "gruppo"
    g = carica_documento([a, b])
    la, lb = lista(g.streams[0]), lista(g.streams[1])
    assert la.shape == lb.shape and np.allclose(la, lb, atol=1e-9, rtol=0)
    ok("con lo stesso `rng_group` le due copie hanno gli stessi grani, spostati nel tempo")


def stream21_e_voce_sola():
    _, ss = master_e_stream()
    s21 = next(s for s in ss if s["stream_id"] == "stream21")
    senza = {k: v for k, v in s21.items() if k != "voices"}
    con4 = copy.deepcopy(s21)
    con4["voices"]["num_voices"] = 4
    g1 = carica_documento([s21])
    g2 = carica_documento([senza])
    g3 = carica_documento([con4])
    l1, l2, l3 = lista(g1.streams[0]), lista(g2.streams[0]), lista(g3.streams[0])
    assert l1.shape == l2.shape and np.array_equal(l1, l2)
    assert l3.shape != l1.shape
    ok("`stream21`: con una voce sola il blocco `voices` (l'accordo `sus4`) non cambia i grani; con quattro voci li cambia")


def stream_minimo():
    _, ss = master_e_stream()
    s14 = next(s for s in ss if s["stream_id"] == "stream14")
    minimo = {"stream_id": "minimo", "sample": s14["sample"], "duration": s14["duration"],
              "onset": s14["onset"]}
    g = carica_documento([s14, minimo])
    assert np.array_equal(lista(g.streams[0]), lista(g.streams[1]))
    ok("`stream14` ha la stessa lista di grani dello stream minimo (identita' e campione, nient'altro)")


# --- 9. la tabella del capitolo ---------------------------------------------------------

def dec(x, n=1):
    return f"{x:.{n}f}".replace(".", ",")


def mig(n):
    return f"{n:,}".replace(",", " ")


def testo_grano(g):
    v = valori(g["duration"])
    lo, hi = min(v), max(v)
    if hi >= 1:
        a, b = f"{lo:g}".replace(".", ","), f"{hi:g}".replace(".", ",")
        return (a if lo == hi else f"{a}–{b}") + " s"
    lo, hi = lo * 1000, hi * 1000

    def f(x):
        if x < 10 and abs(x - round(x)) > 0.049:
            return f"{x:.1f}".rstrip("0").rstrip(".").replace(".", ",")
        return f"{round(x):d}"

    return (f(lo) if abs(lo - hi) < 1e-9 else f"{f(lo)}–{f(hi)}") + " ms"


def testo_voci(s):
    v = valori((s.get("voices") or {}).get("num_voices", 1)) or [1]
    lo, hi = min(v), max(v)
    return f"{int(lo)}" if lo == hi else f"{int(lo)}–{hi:.1f}".replace(".", ",")


def tabella():
    _, ss = master_e_stream()
    testo = CAPITOLO.read_text(encoding="utf-8")
    righe = {m.group(1): [c.strip() for c in m.group(2).split("|")]
             for m in re.finditer(r"^\|\s*`(stream\d+)`\s*\|(.*)\|\s*$", testo, re.M)}
    if righe:
        assert set(righe) == set(GRANI), set(righe) ^ set(GRANI)
        for s in ss:
            atteso = [codice(os.path.splitext(s["sample"])[0]), dec(float(s["onset"])), dec(float(s["duration"])),
                      testo_grano(s["grain"]), testo_voci(s), mig(GRANI[s["stream_id"]])]
            assert righe[s["stream_id"]] == atteso, (s["stream_id"], righe[s["stream_id"]], atteso)
        ordine = [m.group(1) for m in re.finditer(r"^\|\s*`(stream\d+)`", testo, re.M)]
        assert ordine == [s["stream_id"] for s in sorted(ss, key=lambda s: (float(s["onset"]), ss.index(s)))]
        ok("la tabella del capitolo (24 righe, in ordine di ingresso) coincide con i dati e con i grani")
    gruppi = {m.group(1): [c.strip() for c in m.group(2).split("|")]
              for m in re.finditer(r"^\|\s*(primo|secondo|ultimo)\s*\|(.*)\|\s*$", testo, re.M)}
    if gruppi:
        _, ss = master_e_stream()
        assert list(gruppi) == ["primo", "secondo", "ultimo"]
        for nome, nomi, (primo, ultimo, grani_g) in zip(gruppi, gruppi_per_nome(), GRUPPI):
            membri = [s for s in ss if s["stream_id"] in nomi]
            a, b = min(float(s["onset"]) for s in membri), max(fine(s) for s in membri)
            assert gruppi[nome] == [f"{round(a)}–{round(b)}", str(len(membri)), mig(grani_g)], (nome, gruppi[nome])
        ok("la tabella dei gruppi del capitolo coincide con i dati")
    assert righe or gruppi, "il capitolo non ha una tabella degli stream ne' dei gruppi"


# --- 10. il modello di costo --------------------------------------------------------------

def costo():
    master, _ = master_e_stream()
    secondi = 34e-6 * TOTALE + 1.4e-3 * master["duration"]
    assert 300 < secondi < 360  # «poco piu' di cinque minuti»
    ok(f"modello di costo del capitolo 7 (34 us per grano, 1,4 ms per secondo di uscita): "
       f"{secondi / 60:.1f} minuti a un processo solo")


# --- 11. PGE-ui e la regola del repository ---------------------------------------------------

def intestazioni():
    master, _ = master_e_stream()
    def firma(percorso):
        testa = Path(percorso).read_text(encoding="utf-8").splitlines()[:5]
        editor = next((r for r in testa if r.startswith("# editor:")), "")
        salvato = next((r.split(":", 1)[1].strip() for r in testa if r.startswith("# saved:")), None)
        return "PGE-ui" in editor, salvato

    pge_ui, orari = [], []
    for percorso in [MASTER] + sorted((MASTER.parent / "streams").glob("*.yml")):
        e_pge, quando = firma(percorso)
        if e_pge:
            pge_ui.append(percorso.stem)
            orari.append(quando)
    assert len(pge_ui) == 10 and "mare-nostrum" in pge_ui and "stream3" not in pge_ui and "stream9" not in pge_ui
    assert min(orari) >= "2026-10-21T20:00" and max(orari) <= "2026-10-22T00:30", (min(orari), max(orari))
    ok("il master e nove file portano la firma di PGE-ui, salvati fra le 22:23 del 21 e le 2:08 del 22 ottobre (ora italiana)")
    # la regola del repository del brano (tests/test_brano.py): ogni voce del master e' un `file:`
    assert any("file" not in v for v in master["streams"])
    ok("il master ha stream scritti dentro: la regola «un file per stream» del repository del brano non e' rispettata")


def stato_precedente():
    try:
        vecchio = subprocess.run(["git", "-C", str(BRANO), "show", "1979ce1^:configs/mare-nostrum.yml"],
                                 capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        print("saltato: la storia del repository del brano non e' disponibile")
        return
    m = yaml.safe_load(vecchio)
    assert m["duration"] == 322.074 and len(m["streams"]) == 10
    assert sum(bool(v.get("mute")) for v in m["streams"]) == 2 and all("file" in v for v in m["streams"])
    ok("lo stato precedente del repository: dieci stream, due silenziati, 322,074 s")


if __name__ == "__main__":
    for prova in (testa_e_stream, profilo, campioni, copie_e_famiglia, vocabolari, predefiniti, grani,
                  realizzazioni, stream21_e_voce_sola, stream_minimo, tabella, costo, intestazioni,
                  stato_precedente):
        prova()
    print("\ntutte le verifiche passano")
