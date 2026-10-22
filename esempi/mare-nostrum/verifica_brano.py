#!/usr/bin/env python3
"""Verifica le cifre del capitolo 10 sul brano *mare-nostrum*.

Uso:  python esempi/mare-nostrum/verifica_brano.py [../mare-nostrum/configs/mare-nostrum.yml]

Il brano non e' in questo repo (e' incompiuto): lo script legge il master dal
repository del brano, accanto a questo (o dal percorso passato come argomento),
e controlla con `assert` che cosa del capitolo un programma puo' verificare. Le
cifre sono quelle del master al commit 1979ce1, col motore alla versione che il
repository del brano fissa (1188dbc). Se il brano e' andato avanti le verifiche
falliscono: e' il segnale che il capitolo va riletto, non che lo script sia
sbagliato.

Il master contiene il brano (quindici stream) e, in fondo, nove stream messi da
parte per un uso futuro, che per ora non ne fanno parte (`DA_PARTE`, in
disposizione.py). I numeri del capitolo sono quelli del brano, salvo dove il
capitolo dice altrimenti.

Il motore e' quello del submodule `engine/` del repository del brano, se c'e';
altrimenti `PGE_DIR` (default ../PythonGranularEngine). Il numero di grani
dipende da durata, densita' e seme, non dal contenuto audio: il corpus non e'
versionato, e i campioni sono rumore sintetico dai nomi giusti (come fanno i
test del brano). Ogni sezione controlla una parte del capitolo:
  1. la testa del master e gli stream: due forme, il brano e il materiale messo da parte;
  2. il profilo del brano nel tempo: due gruppi, un respiro, la sovrapposizione massima;
  3. i campioni: nove nel brano, quattordici nel master;
  4. le copie (`stream25`, `stream26`, `stream27`) e la famiglia dei primi stream;
  5. i due vocabolari: durate dei grani, densita', gate, voci, finestre;
  6. il materiale messo da parte: otto stream a valori predefiniti, e `stream12`;
  7. i grani di ogni stream, sul motore vero, e le densita' che ne vengono;
  8. le copie hanno un'altra realizzazione, e con `rng_group` gli stessi grani;
  9. la tabella del capitolo coincide con i dati;
 10. il modello di costo del capitolo 7 applicato al brano;
 11. la regola «un file per stream» del repository del brano.
"""
import contextlib
import copy
import io
import os
import re
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

from disposizione import (DA_PARTE, codice, e_predefinito, leggi, stream_del_master,  # noqa: E402
                          tratti_vuoti, valori)

CAPITOLO = REPO / "docs" / "sezioni" / "10-USO-COMPOSITIVO.md"

# I grani che il motore produce con il seme dichiarato, uno stream alla volta
# (la colonna «Grani» della tabella del capitolo, e quelli del materiale messo da parte).
GRANI = {
    "stream2": 304042, "stream3": 934191, "stream9": 1524526, "stream5": 112093,
    "stream6": 302588, "stream10": 633345, "stream7": 34053, "stream8": 190663,
    "stream24": 2727140, "stream21": 22201, "stream22": 2296, "stream25": 302955,
    "stream27": 1523628, "stream26": 665552, "stream23": 5706, "stream18": 5598,
    "stream16": 4798, "stream20": 5219, "stream17": 4158, "stream19": 4853,
    "stream13": 3381, "stream14": 3998, "stream12": 100329, "stream15": 1999,
}
TOTALE_BRANO = 9284979          # i quindici stream del brano
GRANI_DA_PARTE = 134333         # i nove stream messi da parte
TOTALE_MASTER = TOTALE_BRANO + GRANI_DA_PARTE
GRUPPI = (  # primo e ultimo stream per ingresso, e i grani del gruppo
    ("stream2", "stream8", 4035501), ("stream24", "stream23", 5249478))
RIVERRUN = 2375  # grani al secondo, il massimo di Riverrun (Truax 1988, p. 25)
RESPIRO = (277.852, 278.634)  # l'unico tratto in cui il brano non ha stream, fra i due gruppi


def ok(testo):
    print("ok:", testo)


def vicino(a, b, tol=2e-3):
    return abs(a - b) <= tol


# --- il master, letto per stream -------------------------------------------------

def master_e_stream():
    master = leggi(MASTER)
    return master, stream_del_master(master, str(MASTER.parent))


def il_brano():
    """Il master, gli stream del brano e quelli messi da parte."""
    master, ss = master_e_stream()
    return master, [s for s in ss if s["stream_id"] not in DA_PARTE], [s for s in ss if s["stream_id"] in DA_PARTE]


def fine(s):
    return float(s["onset"]) + float(s["duration"])


# --- 1. la testa e gli stream -------------------------------------------------------

def testa_e_stream():
    master, brano, parte = il_brano()
    ss = brano + parte
    assert master["duration"] == 998.833 and master["bpm"] == 120 and master["seed"] == 1441
    ok("testa del master: seed 1441, 998,833 s, 120 bpm")
    voci = master["streams"]
    con_file = [v["file"] for v in voci if "file" in v]
    dentro = [v["stream_id"] for v in voci if "file" not in v]
    assert len(voci) == 24 and len(con_file) == 11 and len(dentro) == 13
    assert len({s["stream_id"] for s in ss}) == 24
    assert sorted(os.path.basename(f)[:-4] for f in con_file) == sorted(
        ["stream2", "stream3", "stream5", "stream6", "stream7", "stream8", "stream9",
         "stream10", "stream25", "stream26", "stream27"])
    assert sorted(dentro) == sorted(f"stream{n}" for n in range(12, 25))
    assert not any(s.get("mute") or s.get("solo") for s in ss)
    ok("24 stream, 11 importati da file e 13 scritti dentro il master, nessuno silenziato")
    assert sorted(DA_PARTE) == sorted(f"stream{n}" for n in range(12, 21)) and set(DA_PARTE) <= set(dentro)
    assert len(brano) == 15 and len(parte) == 9
    assert sorted(s["stream_id"] for s in brano if s["stream_id"] in dentro) == \
        ["stream21", "stream22", "stream23", "stream24"]
    ok("il brano ha 15 stream: 11 importati e 4 scritti dentro (da `stream21` a `stream24`); "
       "gli altri 9 (da `stream12` a `stream20`) sono messi da parte")


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
    master, brano, parte = il_brano()
    fine_brano = max(fine(s) for s in brano)
    assert vicino(fine_brano, 674.954) and round(fine_brano) == 675
    assert int(fine_brano // 60) == 11 and 14.9 < fine_brano % 60 <= 15
    assert vicino(fine_brano, fine(next(s for s in brano if s["stream_id"] == "stream26")))
    ok("il brano finisce con `stream26` a 674,954 s: 675 secondi, undici minuti e un quarto")
    ultimo = max(fine(s) for s in brano + parte)
    assert vicino(ultimo, 988.833) and vicino(master["duration"], ultimo + 10) and master["duration"] > fine_brano
    ok("la `duration` del master (998,833 s) e' dieci secondi dopo l'ultimo stream, che e' del materiale messo da parte")
    righe = [dict(onset=float(s["onset"]), durata=float(s["duration"]), muto=False) for s in brano]
    vuoti = tratti_vuoti(righe, fine_brano)
    assert len(vuoti) == 1 and vicino(vuoti[0][0], RESPIRO[0]) and vicino(vuoti[0][1], RESPIRO[1])
    assert 0.78 < vuoti[0][1] - vuoti[0][0] < 0.79
    ok("nel brano c'e' un solo tratto senza stream: 0,8 s fra la fine di `stream8` (278 s) e l'ingresso di `stream24`")
    gruppi = [[], []]
    for s in brano:
        gruppi[float(s["onset"]) >= RESPIRO[1] - 1e-6].append(s)
    assert [len(g) for g in gruppi] == [8, 7]
    for g, (primo, ultimo_stream, _) in zip(gruppi, GRUPPI):
        ordine = [s["stream_id"] for s in sorted(g, key=lambda s: (float(s["onset"]), s["stream_id"]))]
        assert ordine[0] == primo and ordine[-1] == ultimo_stream, (ordine, primo, ultimo_stream)
    importati = {v["stream_id"] if "stream_id" in v else os.path.basename(v["file"])[:-4]
                 for v in master["streams"] if "file" in v}
    assert all(s["stream_id"] in importati for s in gruppi[0])
    picchi = [max(n for a, b, n in sovrapposizioni([(float(s["onset"]), fine(s)) for s in g])) for g in gruppi]
    assert picchi == [7, 5]
    primo = sovrapposizioni([(float(s["onset"]), fine(s)) for s in gruppi[0]])
    sette = [(a, b) for a, b, n in primo if n == 7]
    assert len(sette) == 1 and vicino(sette[0][0], 112.003) and vicino(sette[0][1], 125.309)
    ok("due gruppi di 8 (tutti importati) e 7 stream, con al massimo 7 (intorno al secondo 112) e 5 stream insieme")
    d = {s["stream_id"]: s for s in brano}
    tratti = sovrapposizioni([(float(s["onset"]), fine(s)) for s in brano])
    solo = [(a, b) for a, b, n in tratti if n == 1 and 278 < a < 342]
    assert len(solo) == 1 and solo[0][1] - solo[0][0] > 60
    assert vicino(solo[0][0], float(d["stream24"]["onset"])) and vicino(solo[0][1], float(d["stream21"]["onset"]))
    ok("`stream24` suona da solo per oltre un minuto (62,8 s) all'inizio del secondo gruppo")
    uno = [(a, b) for a, b, n in tratti if n == 1 and a < 278]
    assert len(uno) == 1 and uno[0][0] > 260 and vicino(uno[0][1], fine(d["stream8"]))
    ok("alla fine del primo gruppo resta il solo `stream8`, che finisce a 277,9 s")
    primo_da_parte = min(float(s["onset"]) for s in parte)
    assert round(primo_da_parte) == 828 and primo_da_parte > fine_brano
    tratti_parte = sovrapposizioni([(float(s["onset"]), fine(s)) for s in parte])
    cima = [(a, b) for a, b, n in tratti_parte if n == 9]
    assert max(n for a, b, n in tratti_parte) == 9 and len(cima) == 1
    assert vicino(cima[0][0], 889.152) and vicino(cima[0][1], 939.152)
    ok("il materiale messo da parte comincia al secondo 828, dopo la fine del brano, e arriva a nove stream insieme")


# --- 3. i campioni ----------------------------------------------------------------

def campioni():
    master, brano, parte = il_brano()
    nomi = {s["sample"] for s in brano + parte}
    assert len(nomi) == 14
    nomi_brano = {s["sample"] for s in brano}
    frammenti = sorted(n for n in nomi_brano if n.startswith("001-"))
    numerati = sorted(n for n in nomi_brano if re.fullmatch(r"\d{3}\.wav", n))
    assert len(nomi_brano) == 9 and len(frammenti) == 5 and numerati == ["004.wav", "007.wav", "011.wav", "016.wav"]
    for v in master["streams"]:
        if "file" in v:
            assert leggi(MASTER.parent / v["file"])["streams"][0]["sample"] in frammenti
        elif v["stream_id"] not in DA_PARTE:
            assert v["sample"] in numerati
    ok("il brano usa nove campioni: cinque frammenti `001-*`, tutti negli stream importati, "
       "e quattro file numerati (004, 007, 011, 016), negli stream scritti dentro")
    nomi_parte = [s["sample"] for s in parte]
    assert len(set(nomi_parte)) == 9
    soli = sorted(set(nomi_parte) - nomi_brano)
    assert soli == ["002.wav", "006.wav", "008.wav", "009.wav", "013.wav"]
    ok("il master cita quattordici campioni; cinque (002, 006, 008, 009, 013) stanno soltanto nel materiale messo da parte")


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
    _, brano, parte = il_brano()
    d = {s["stream_id"]: s for s in brano + parte}
    durate = {s["stream_id"]: valori(s["grain"]["duration"]) for s in brano}
    assert min(min(v) for v in durate.values()) == 0.0001 and durate["stream24"] == [0.0001]
    assert max(max(v) for v in durate.values()) == 3 and max(durate["stream22"]) == 3 and durate["stream23"] == [3.0]
    assert round(3 / 0.0001) == 30000  # piu' di quattro ordini di grandezza
    ok("le durate dichiarate dei grani del brano vanno da 0,1 ms (`stream24`) a 3 s (`stream22`, `stream23`)")
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
    gate = {s["stream_id"]: s["deviation_probability"] for s in brano + parte if "deviation_probability" in s}
    assert gate == {"stream24": 40, "stream23": 70, "stream12": [[0.4967, 0], [0.99663, 100]]}
    ok("il gate `deviation_probability` e' in tre stream: 40 in `stream24`, 70 in `stream23`, "
       "in rampa da 0 a 100 nella seconda meta' di `stream12`, che e' messo da parte")
    s21 = d["stream21"]
    assert s21["grain"]["envelope"] == {"from": "hanning", "to": "rexpodec", "curve": [[0.65, 0], [1, 1]]}
    assert s21["voices"]["num_voices"] == 1 and s21["voices"]["pitch"]["chord"] == "sus4"
    ok("`stream21`: finestra da Hann a `rexpodec` dal 65% dello stream, accordo `sus4` con una voce sola")


# --- 6. il materiale messo da parte -----------------------------------------------------

def materiale_da_parte():
    _, brano, parte = il_brano()
    d = {s["stream_id"]: s for s in parte}
    minimi = sorted(s["stream_id"] for s in parte if e_predefinito(s))
    assert minimi == [f"stream{n}" for n in range(14, 21)], minimi
    s13 = pulito(d["stream13"])
    assert (s13.pop("pan"), s13.pop("pan_range")) == (-110, 80)
    assert e_predefinito({**s13, "stream_id": "x", "onset": 0})
    assert all(valori(d[f"stream{n}"]["fill_factor"]) == [2.0] for n in range(13, 21))
    assert 2 / 0.05 == 40
    assert sorted(round(float(d[f"stream{n}"]["duration"]), 3) for n in range(13, 21)) == \
        [50, 84.552, 100, 104, 120, 121.356, 130.506, 140]
    assert sorted(d[f"stream{n}"]["sample"] for n in range(13, 21)) == \
        ["004.wav", "006.wav", "007.wav", "008.wav", "009.wav", "011.wav", "013.wav", "016.wav"]
    ok("da `stream13` a `stream20`: valori predefiniti (`stream13` ha in piu' un pan a -110 con banda 80), "
       "quaranta grani al secondo, otto campioni diversi, durate da 50 a 140 s")
    s12 = d["stream12"]
    assert valori(s12["voices"]["num_voices"]) == [1.0, 12.74] and s12["voices"]["pitch"]["chord"] == "maj13s11"
    assert s12["voices"]["pitch"]["inversion"] == 3 and s12["voices"]["onset_offset"]["max_offset"] == 10
    assert s12["voices"]["pointer"]["pointer_range"] == 1 and s12["deviation_probability"] == [[0.4967, 0], [0.99663, 100]]
    assert s12["sample"] == "002.wav"
    ok("`stream12`: da 1 a 12,74 voci, accordo `maj13s11` in terzo rivolto, scarto di onset fino a 10 s, "
       "puntatore stocastico su tutto il file, gate da 0 a 100 nella seconda meta'")


# --- il motore ---------------------------------------------------------------------

_CAMPIONI = {}
_GEN = {}


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


# --- 7. i grani ---------------------------------------------------------------------

def grani():
    campioni_sintetici()
    n = len(GRANI)
    with ProcessPoolExecutor(max_workers=max(1, min(4, os.cpu_count() or 1))) as pool:
        risultati = list(pool.map(_grani_dello_stream, range(n)))
    per_stream = {r["stream"]: r for r in risultati}
    assert {k: v["grani"] for k, v in per_stream.items()} == GRANI, \
        {k: (GRANI[k], per_stream[k]["grani"]) for k in GRANI if GRANI[k] != per_stream[k]["grani"]}
    brano = [k for k in GRANI if k not in DA_PARTE]
    assert sum(GRANI[k] for k in brano) == TOTALE_BRANO
    assert sum(GRANI[k] for k in DA_PARTE) == GRANI_DA_PARTE and sum(GRANI.values()) == TOTALE_MASTER
    ok(f"grani del brano: {TOTALE_BRANO:,} (circa {TOTALE_BRANO / 1e6:.1f} milioni), uno stream alla volta come "
       f"nella tabella; il materiale messo da parte ne ha {GRANI_DA_PARTE:,}".replace(",", " "))
    _, brano_s, _ = il_brano()
    gruppi = [[], []]
    for s in brano_s:
        gruppi[float(s["onset"]) >= RESPIRO[1] - 1e-6].append(s["stream_id"])
    for nomi, (primo, ultimo, atteso) in zip(gruppi, GRUPPI):
        assert sum(GRANI[x] for x in nomi) == atteso, (primo, atteso)
    ok("grani per gruppo: 4 035 501 e 5 249 478")
    tre = sum(GRANI[x] for x in ("stream24", "stream9", "stream27"))
    assert tre / TOTALE_BRANO > 0.60 and GRANI["stream24"] == max(GRANI.values())
    ok(f"`stream24`, `stream9` e `stream27` hanno il {100 * tre / TOTALE_BRANO:.0f}% dei grani del brano")
    otto = sum(GRANI[f"stream{n}"] for n in range(13, 21))
    assert 33500 < otto < 34500 and GRANI["stream12"] == 100329 and otto + GRANI["stream12"] == GRANI_DA_PARTE
    ok(f"materiale messo da parte: {GRANI['stream12']} grani sono di `stream12`, {otto} degli otto stream a valori predefiniti")
    assert per_stream["stream24"]["picco"] > 35000 and per_stream["stream24"]["picco"] / RIVERRUN > 15
    assert per_stream["stream24"]["picco"] == max(r["picco"] for r in risultati)
    ok(f"`stream24` arriva a {per_stream['stream24']['picco']} grani al secondo, "
       f"{per_stream['stream24']['picco'] / RIVERRUN:.1f} volte il massimo di Riverrun")
    assert per_stream["stream22"]["concorrenti"] == 102 and per_stream["stream23"]["concorrenti"] == 460
    ok("grani sovrapposti: fino a 102 in `stream22` e a 460 in `stream23`")
    assert per_stream["stream12"]["voci"] == 13 and per_stream["stream23"]["voci"] == 4
    assert per_stream["stream3"]["voci"] == 4 and per_stream["stream9"]["voci"] == 2
    ok("il motore prepara 13 liste di voci per `stream12` (da 1 a 12,74 voci)")


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
    _, brano, parte = il_brano()
    testo = CAPITOLO.read_text(encoding="utf-8")
    righe = {m.group(1): [c.strip() for c in m.group(2).split("|")]
             for m in re.finditer(r"^\|\s*`(stream\d+)`\s*\|(.*)\|\s*$", testo, re.M)}
    assert righe, "il capitolo non ha la tabella degli stream"
    assert set(righe) == {s["stream_id"] for s in brano}, set(righe) ^ {s["stream_id"] for s in brano}
    assert not set(righe) & set(DA_PARTE)
    for s in brano:
        atteso = [codice(os.path.splitext(s["sample"])[0]), dec(float(s["onset"])), dec(float(s["duration"])),
                  testo_grano(s["grain"]), testo_voci(s), mig(GRANI[s["stream_id"]])]
        assert righe[s["stream_id"]] == atteso, (s["stream_id"], righe[s["stream_id"]], atteso)
    ordine = [m.group(1) for m in re.finditer(r"^\|\s*`(stream\d+)`", testo, re.M)]
    assert ordine == [s["stream_id"] for s in sorted(brano, key=lambda s: (float(s["onset"]), brano.index(s)))]
    ok("la tabella del capitolo (15 righe, in ordine di ingresso, senza il materiale messo da parte) "
       "coincide con i dati e con i grani")


# --- 10. il modello di costo --------------------------------------------------------------

def costo():
    master, brano, _ = il_brano()
    fine_brano = max(fine(s) for s in brano)
    secondi = 34e-6 * TOTALE_BRANO + 1.4e-3 * fine_brano
    assert 300 < secondi < 360  # «poco piu' di cinque minuti»
    assert 300 < 34e-6 * TOTALE_MASTER + 1.4e-3 * master["duration"] < 360
    ok(f"modello di costo del capitolo 7 (34 us per grano, 1,4 ms per secondo di uscita): "
       f"{secondi / 60:.1f} minuti a un processo solo")


# --- 11. la regola del repository del brano ---------------------------------------------------

def regola_un_file_per_stream():
    master, brano, parte = il_brano()
    testa = MASTER.read_text(encoding="utf-8").splitlines()[:5]
    assert any(r.startswith("# editor:") and "PGE-ui" in r for r in testa)
    # la regola (tests/test_brano.py): ogni voce del master e' un `file:`
    dentro = [v["stream_id"] for v in master["streams"] if "file" not in v]
    assert len(dentro) == 13
    assert sorted(set(dentro) - set(DA_PARTE)) == ["stream21", "stream22", "stream23", "stream24"]
    assert len(set(dentro) & set(DA_PARTE)) == 9
    ok("il master, salvato da PGE-ui, ha tredici stream scritti dentro (quattro del brano, nove messi da parte): "
       "la regola «un file per stream» del repository del brano non e' rispettata")


if __name__ == "__main__":
    for prova in (testa_e_stream, profilo, campioni, copie_e_famiglia, vocabolari, materiale_da_parte, grani,
                  realizzazioni, stream21_e_voce_sola, stream_minimo, tabella, costo, regola_un_file_per_stream):
        prova()
    print("\ntutte le verifiche passano")
