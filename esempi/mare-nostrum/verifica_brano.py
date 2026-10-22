#!/usr/bin/env python3
"""Verifica le cifre del capitolo 10 sul brano *mare-nostrum*.

Uso:  python esempi/mare-nostrum/verifica_brano.py [../mare-nostrum/configs/mare-nostrum.yml]

Il brano non e' in questo repo (e' incompiuto): lo script legge il master dal
repository del brano, accanto a questo (o dal percorso passato come argomento),
e controlla con `assert` che cosa del capitolo un programma puo' verificare. Le
cifre sono quelle del master al commit 399de71, col motore alla versione che il
repository del brano fissa (1188dbc). Se il brano e' andato avanti le verifiche
falliscono: e' il segnale che il capitolo va riletto, non che lo script sia
sbagliato.

Il motore e' quello del submodule `engine/` del repository del brano, se c'e';
altrimenti `PGE_DIR` (default ../PythonGranularEngine). Il numero di grani
dipende da durata, densita' e seme, non dal contenuto audio: il corpus non e'
versionato, e i campioni sono rumore sintetico dai nomi giusti (come fanno i
test del brano). Ogni sezione controlla una parte del capitolo:
  1. la testa del master e gli stream, nelle due forme;
  2. il profilo del brano nel tempo: due gruppi, un respiro, la sovrapposizione massima;
  3. i campioni: cinque frammenti e quattro file numerati;
  4. le copie (`stream25`, e `stream26`, `stream27` accorciati) e la famiglia dei primi stream;
  5. i due vocabolari: durate dei grani, densita', gate, voci, finestre;
  6. i grani di ogni stream, sul motore vero, e le densita' che ne vengono;
  7. una copia ha un'altra realizzazione, e con `rng_group` gli stessi grani;
  8. la tabella del capitolo coincide con i dati;
  9. il modello di costo del capitolo 7 applicato al brano;
 10. la regola «un file per stream» del repository del brano.
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

from disposizione import codice, leggi, stream_del_master, tratti_vuoti, valori  # noqa: E402

CAPITOLO = REPO / "docs" / "sezioni" / "10-USO-COMPOSITIVO.md"

# I grani che il motore produce con il seme dichiarato, uno stream alla volta
# (la colonna «Grani» della tabella del capitolo).
GRANI = {
    "stream2": 304042, "stream3": 934191, "stream26": 376309, "stream9": 1524526,
    "stream27": 1452100, "stream5": 112093, "stream6": 302588, "stream25": 302955,
    "stream7": 34053, "stream8": 190663, "stream24": 2727140, "stream10": 633345,
    "stream21": 22201, "stream22": 2296, "stream23": 5706,
}
TOTALE = 8924208
GRUPPI = (  # primo e ultimo stream per ingresso, e i grani del gruppo
    ("stream2", "stream8", 4035501), ("stream24", "stream23", 4888707))
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


def fine(s):
    return float(s["onset"]) + float(s["duration"])


# --- 1. la testa e gli stream -------------------------------------------------------

def testa_e_stream():
    master, ss = master_e_stream()
    assert master["duration"] == 655.136 and master["bpm"] == 120 and master["seed"] == 1441
    ok("testa del master: seed 1441, 655,136 s, 120 bpm")
    voci = master["streams"]
    con_file = [v["file"] for v in voci if "file" in v]
    dentro = [v["stream_id"] for v in voci if "file" not in v]
    assert len(voci) == 15 and len(con_file) == 11 and len(dentro) == 4
    assert len({s["stream_id"] for s in ss}) == 15
    assert sorted(os.path.basename(f)[:-4] for f in con_file) == sorted(
        ["stream2", "stream3", "stream5", "stream6", "stream7", "stream8", "stream9",
         "stream10", "stream25", "stream26", "stream27"])
    assert sorted(dentro) == ["stream21", "stream22", "stream23", "stream24"]
    assert not any(s.get("mute") or s.get("solo") for s in ss)
    ok("15 stream, 11 importati da file e 4 scritti dentro il master (da `stream21` a `stream24`), "
       "nessuno silenziato")


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
    d = {s["stream_id"]: s for s in ss}
    fine_brano = max(fine(s) for s in ss)
    assert vicino(fine_brano, 645.136) and vicino(fine_brano, fine(d["stream23"]))
    assert vicino(master["duration"], fine_brano + 10) and round(master["duration"]) == 655
    assert int(master["duration"] // 60) == 10 and master["duration"] % 60 > 50  # quasi undici minuti
    ok("l'ultimo stream, `stream23`, finisce a 645,136 s; la `duration` del master (655 s) "
       "aggiunge dieci secondi di coda")
    righe = [dict(onset=float(s["onset"]), durata=float(s["duration"]), muto=False) for s in ss]
    vuoti = tratti_vuoti(righe, fine_brano)
    assert len(vuoti) == 1 and vicino(vuoti[0][0], RESPIRO[0]) and vicino(vuoti[0][1], RESPIRO[1])
    assert 0.78 < vuoti[0][1] - vuoti[0][0] < 0.79
    ok("nel brano c'e' un solo tratto senza stream: 0,8 s fra la fine di `stream8` (278 s) e l'ingresso di `stream24`")
    gruppi = [[], []]
    for s in ss:
        gruppi[float(s["onset"]) >= RESPIRO[1] - 1e-6].append(s)
    assert [len(g) for g in gruppi] == [8, 7]
    for g, (primo, ultimo, _) in zip(gruppi, GRUPPI):
        ordine = [s["stream_id"] for s in sorted(g, key=lambda s: (float(s["onset"]), s["stream_id"]))]
        assert ordine[0] == primo and ordine[-1] == ultimo, (ordine, primo, ultimo)
    importati = {os.path.basename(v["file"])[:-4] for v in master["streams"] if "file" in v}
    assert all(s["stream_id"] in importati for s in gruppi[0])
    picchi = [max(n for a, b, n in sovrapposizioni([(float(s["onset"]), fine(s)) for s in g])) for g in gruppi]
    assert picchi == [7, 5]
    primo = sovrapposizioni([(float(s["onset"]), fine(s)) for s in gruppi[0]])
    sette = [(a, b) for a, b, n in primo if n == 7]
    assert len(sette) == 1 and vicino(sette[0][0], 112.003) and vicino(sette[0][1], 125.309)
    ok("due gruppi di 8 (tutti importati) e 7 stream, con al massimo 7 (intorno al secondo 112) e 5 stream insieme")
    tratti = sovrapposizioni([(float(s["onset"]), fine(s)) for s in ss])
    solo = [(a, b) for a, b, n in tratti if n == 1 and 278 < a < 342]
    assert len(solo) == 1 and solo[0][1] - solo[0][0] > 60
    assert vicino(solo[0][0], float(d["stream24"]["onset"])) and vicino(solo[0][1], float(d["stream21"]["onset"]))
    ok("`stream24` suona da solo per oltre un minuto (62,8 s) all'inizio del secondo gruppo")
    uno = [(a, b) for a, b, n in tratti if n == 1 and a < 278]
    assert len(uno) == 1 and uno[0][0] > 260 and vicino(uno[0][1], fine(d["stream8"]))
    ok("alla fine del primo gruppo resta il solo `stream8`, che finisce a 277,9 s")
    entra = float(d["stream23"]["onset"])
    assert all(abs(fine(d[x]) - entra) < 0.5 and round(fine(d[x])) == 567 for x in ("stream26", "stream27"))
    coda = [(a, b) for a, b, n in tratti if n == 1 and a > 560]
    assert len(coda) == 1 and vicino(coda[0][0], fine(d["stream27"])) and vicino(coda[0][1], fine_brano)
    assert 75 < coda[0][1] - coda[0][0] < 80
    ok(f"`stream26` e `stream27` si fermano intorno al secondo 567, quando entra `stream23`, "
       f"che chiude da solo per {coda[0][1] - coda[0][0]:.1f} s")


# --- 3. i campioni ----------------------------------------------------------------

def campioni():
    master, ss = master_e_stream()
    nomi = {s["sample"] for s in ss}
    frammenti = sorted(n for n in nomi if n.startswith("001-"))
    numerati = sorted(n for n in nomi if re.fullmatch(r"\d{3}\.wav", n))
    assert len(nomi) == 9 and len(frammenti) == 5 and numerati == ["004.wav", "007.wav", "011.wav", "016.wav"]
    for v in master["streams"]:
        if "file" in v:
            assert leggi(MASTER.parent / v["file"])["streams"][0]["sample"] in frammenti
        else:
            assert v["sample"] in numerati
    ok("il brano usa nove campioni: cinque frammenti `001-*`, tutti negli stream importati, "
       "e quattro file numerati (004, 007, 011, 016), negli stream scritti dentro")


# --- 4. copie e famiglia -----------------------------------------------------------

def pulito(s):
    return {k: v for k, v in s.items() if k not in ("stream_id", "onset") and not k.startswith("_")}


def appiattisci(d, pre=""):
    for k, v in d.items():
        if isinstance(v, dict) and "points" not in v:
            yield from appiattisci(v, pre + k + ".")
        else:
            yield pre + k, v


def punti(v):
    """I punti di un inviluppo ([[x, valore], ...]), o None se il valore non lo e'."""
    if isinstance(v, dict):
        v = v.get("points")
    if isinstance(v, list) and v and all(isinstance(p, list) and len(p) == 2 for p in v):
        return v
    return None


def accorciato(copia, origine, salvo=()):
    """La copia e' l'origine tagliata prima della fine: stessi valori, e ogni inviluppo
    (in tempo normalizzato, quindi riscalato) uguale in secondi fino al taglio. Le chiavi
    in `salvo` possono differire."""
    a, b = dict(appiattisci(pulito(copia))), dict(appiattisci(pulito(origine)))
    dc, do = float(copia["duration"]), float(origine["duration"])
    assert copia["time_mode"] == "normalized" and dc < do and set(a) == set(b)
    for k in a:
        if k == "duration" or k in salvo:
            continue
        pa, pb = punti(a[k]), punti(b[k])
        if pa is None or pb is None:
            assert a[k] == b[k], k
            continue
        ta = [(x * dc, v) for x, v in pa]
        tb = [(x * do, v) for x, v in pb if x * do <= dc + 0.01]
        assert len(ta) >= len(tb), k
        assert all(abs(t1 - t2) < 0.01 and v1 == v2 for (t1, v1), (t2, v2) in zip(ta, tb)), k
        for t, v in ta[len(tb):]:  # il punto che il taglio aggiunge, col valore dell'origine in quell'istante
            assert vicino(t, dc) and abs(v - np.interp(t, [x * do for x, _ in pb], [w for _, w in pb])) < 1e-4, k


def copie_e_famiglia():
    _, ss = master_e_stream()
    d = {s["stream_id"]: s for s in ss}
    assert pulito(d["stream25"]) == pulito(d["stream6"])
    ok("`stream25` ha gli stessi valori di `stream6` a ogni chiave")
    accorciato(d["stream27"], d["stream9"])
    accorciato(d["stream26"], d["stream3"], salvo=("grain.duration",))
    assert [round(float(d[x]["duration"])) for x in ("stream26", "stream27")] == [141, 152]
    assert d["stream26"]["grain"]["duration"] == [[0, 0.006]] and d["stream3"]["grain"]["duration"] != [[0, 0.006]]
    assert valori(d["stream27"]["grain"]["duration"])[-1] == 0.0092 and max(valori(d["stream9"]["grain"]["duration"])) == 0.011
    ok("`stream27` e' `stream9` accorciato a 151,9 s (il grano si ferma a 9,2 ms invece di 11); `stream26` e' "
       "`stream3` accorciato a 141,0 s, con la durata del grano fissa a 6 ms; gli inviluppi restano uguali in secondi")
    for copia, origine in (("stream25", "stream6"), ("stream26", "stream3"), ("stream27", "stream9")):
        assert float(d[copia]["onset"]) > fine(d[origine])
    assert [round(float(d[x]["onset"])) for x in ("stream25", "stream27", "stream26")] == [414, 415, 426]
    ok("le tre copie entrano a 414, 415 e 426 s, dopo la fine dei loro originali")
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
    gate = {s["stream_id"]: s["deviation_probability"] for s in ss if "deviation_probability" in s}
    assert gate == {"stream24": 40, "stream23": 70}
    ok("il gate `deviation_probability` e' in due stream: 40 in `stream24`, 70 in `stream23`")
    s21 = d["stream21"]
    assert s21["grain"]["envelope"] == {"from": "hanning", "to": "rexpodec", "curve": [[0.65, 0], [1, 1]]}
    assert s21["voices"]["num_voices"] == 1 and s21["voices"]["pitch"]["chord"] == "sus4"
    ok("`stream21`: finestra da Hann a `rexpodec` dal 65% dello stream, accordo `sus4` con una voce sola")


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


# --- 6. i grani ---------------------------------------------------------------------

def grani():
    campioni_sintetici()
    n = len(GRANI)
    with ProcessPoolExecutor(max_workers=max(1, min(4, os.cpu_count() or 1))) as pool:
        risultati = list(pool.map(_grani_dello_stream, range(n)))
    per_stream = {r["stream"]: r for r in risultati}
    assert {k: v["grani"] for k, v in per_stream.items()} == GRANI, \
        {k: (GRANI[k], per_stream[k]["grani"]) for k in GRANI if GRANI[k] != per_stream[k]["grani"]}
    assert sum(GRANI.values()) == TOTALE
    ok(f"grani del brano: {mig(TOTALE)} (circa {dec(TOTALE / 1e6)} milioni), uno stream alla volta come nella tabella")
    _, ss = master_e_stream()
    gruppi = [[], []]
    for s in ss:
        gruppi[float(s["onset"]) >= RESPIRO[1] - 1e-6].append(s["stream_id"])
    for nomi, (primo, ultimo, atteso) in zip(gruppi, GRUPPI):
        assert sum(GRANI[x] for x in nomi) == atteso, (primo, atteso)
    ok("grani per gruppo: 4 035 501 e 4 888 707")
    tre = sum(GRANI[x] for x in ("stream24", "stream9", "stream27"))
    assert tre / TOTALE > 0.60 and GRANI["stream24"] == max(GRANI.values())
    ok(f"`stream24`, `stream9` e `stream27` hanno il {100 * tre / TOTALE:.0f}% dei grani del brano")
    assert per_stream["stream24"]["picco"] > 35000 and per_stream["stream24"]["picco"] / RIVERRUN > 15
    assert per_stream["stream24"]["picco"] == max(r["picco"] for r in risultati)
    ok(f"`stream24` arriva a {per_stream['stream24']['picco']} grani al secondo, "
       f"{per_stream['stream24']['picco'] / RIVERRUN:.1f} volte il massimo di Riverrun")
    assert per_stream["stream22"]["concorrenti"] == 102 and per_stream["stream23"]["concorrenti"] == 460
    ok("grani sovrapposti: fino a 102 in `stream22` e a 460 in `stream23`")
    assert per_stream["stream23"]["voci"] == 4 and per_stream["stream3"]["voci"] == 4 and per_stream["stream9"]["voci"] == 2
    ok("voci preparate dal motore: 4 in `stream3` e `stream23`, 2 in `stream9`")


# --- 7. realizzazioni ----------------------------------------------------------------

def realizzazioni():
    _, ss = master_e_stream()
    d = {s["stream_id"]: s for s in ss}
    assert GRANI["stream25"] != GRANI["stream6"]
    ok("`stream25` ha gli stessi valori di `stream6` e un'altra realizzazione: 302 955 grani contro 302 588")
    a, b = copy.deepcopy(d["stream6"]), copy.deepcopy(d["stream25"])
    a["rng_group"] = b["rng_group"] = "gruppo"
    g = carica_documento([a, b])
    la, lb = lista(g.streams[0]), lista(g.streams[1])
    assert la.shape == lb.shape and np.allclose(la, lb, atol=1e-9, rtol=0)
    ok("con lo stesso `rng_group` i due stream hanno gli stessi grani, spostati nel tempo")


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


# --- 8. la tabella del capitolo ---------------------------------------------------------

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
    assert righe, "il capitolo non ha la tabella degli stream"
    assert set(righe) == {s["stream_id"] for s in ss}, set(righe) ^ {s["stream_id"] for s in ss}
    for s in ss:
        atteso = [codice(os.path.splitext(s["sample"])[0]), dec(float(s["onset"])), dec(float(s["duration"])),
                  testo_grano(s["grain"]), testo_voci(s), mig(GRANI[s["stream_id"]])]
        assert righe[s["stream_id"]] == atteso, (s["stream_id"], righe[s["stream_id"]], atteso)
    ordine = [m.group(1) for m in re.finditer(r"^\|\s*`(stream\d+)`", testo, re.M)]
    assert ordine == [s["stream_id"] for s in sorted(ss, key=lambda s: (float(s["onset"]), ss.index(s)))]
    ok("la tabella del capitolo (15 righe, in ordine di ingresso) coincide con i dati e con i grani")


# --- 9. il modello di costo --------------------------------------------------------------

def costo():
    master, _ = master_e_stream()
    secondi = 34e-6 * TOTALE + 1.4e-3 * master["duration"]
    assert 300 < secondi < 360  # «poco piu' di cinque minuti»
    ok(f"modello di costo del capitolo 7 (34 us per grano, 1,4 ms per secondo di uscita): "
       f"{secondi / 60:.1f} minuti a un processo solo")


# --- 10. la regola del repository del brano ---------------------------------------------------

def regola_un_file_per_stream():
    master, _ = master_e_stream()
    testa = MASTER.read_text(encoding="utf-8").splitlines()[:5]
    assert any(r.startswith("# editor:") and "PGE-ui" in r for r in testa)
    # la regola (tests/test_brano.py): ogni voce del master e' un `file:`
    dentro = [v["stream_id"] for v in master["streams"] if "file" not in v]
    assert sorted(dentro) == ["stream21", "stream22", "stream23", "stream24"]
    ok("il master, salvato da PGE-ui, ha quattro stream scritti dentro: "
       "la regola «un file per stream» del repository del brano non e' rispettata")


if __name__ == "__main__":
    for prova in (testa_e_stream, profilo, campioni, copie_e_famiglia, vocabolari, grani,
                  realizzazioni, stream21_e_voce_sola, tabella, costo, regola_un_file_per_stream):
        prova()
    print("\ntutte le verifiche passano")
