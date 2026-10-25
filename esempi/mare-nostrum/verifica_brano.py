#!/usr/bin/env python3
"""Verifica le cifre del capitolo 10 sul brano *mare-nostrum*.

Uso:  python esempi/mare-nostrum/verifica_brano.py [../mare-nostrum/configs/mare-nostrum.yml]

Il brano non e' in questo repo: lo script legge il master dal repository del
brano, accanto a questo (o dal percorso passato come argomento), e controlla con
`assert` che cosa del capitolo un programma puo' verificare. Le cifre sono quelle
del master al commit a26b0f8 del repository del brano, col motore alla versione
che quel repository fissa (1188dbc). Se il brano e' andato avanti le verifiche
falliscono: e' il segnale che il capitolo va riletto, non che lo script sia
sbagliato.

Il motore e' quello del submodule `engine/` del repository del brano, se c'e';
altrimenti `PGE_DIR` (default ../PythonGranularEngine). Il numero di grani
dipende da durata, densita' e seme, non dal contenuto audio: il corpus non e'
versionato, e i campioni sono rumore sintetico dai nomi giusti (come fanno i
test del brano). Ogni sezione controlla una parte del capitolo:
  1. la testa del master e gli stream: sedici, tutti importati da file;
  2. il profilo del brano nel tempo: due gruppi, un respiro, la sovrapposizione massima;
  3. i campioni: nove;
  4. le riprese (`stream25`, `stream26`, `stream27`, `stream6-2`) e la famiglia dei primi stream;
  5. i due vocabolari: durate dei grani, densita', gate, voci, finestre;
  6. i grani di ogni stream, sul motore vero, e le densita' che ne vengono;
  7. la realizzazione dipende dall'identificativo, e con `rng_group` no;
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

from disposizione import (codice, leggi, stream_del_master, tratti_vuoti, valori)  # noqa: E402

CAPITOLO = REPO / "docs" / "sezioni" / "10-USO-COMPOSITIVO.md"

# I grani che il motore produce con il seme dichiarato, uno stream alla volta
# (la colonna «Grani» della tabella del capitolo).
GRANI = {
    "stream2": 304042, "stream3": 1499017, "stream9": 1524526, "stream5": 112093,
    "stream6": 170570, "stream7": 34053, "stream8": 190663, "stream10": 633356,
    "stream24": 2727140, "stream21": 22201, "stream22": 2296, "stream23": 12428,
    "stream26": 376309, "stream25": 302955, "stream27": 1452100, "stream6-2": 131601,
}
TOTALE_BRANO = 9495350
GRUPPI = (  # primo e ultimo stream per ingresso, e i grani del gruppo
    ("stream2", "stream8", 4599921), ("stream24", "stream26", 4895429))
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


def per_id():
    return {s["stream_id"]: s for _, ss in [master_e_stream()] for s in ss}


# --- 1. la testa e gli stream -------------------------------------------------------

def testa_e_stream():
    master, ss = master_e_stream()
    assert master["duration"] == 590.978 and master["bpm"] == 120 and master["seed"] == 1441
    ok("testa del master: seed 1441, 590,978 s, 120 bpm")
    voci = master["streams"]
    assert len(voci) == 16 and all("file" in v for v in voci)
    assert len({s["stream_id"] for s in ss}) == 16
    assert sorted(os.path.basename(v["file"])[:-4] for v in voci) == sorted(
        ["stream2", "stream3", "stream5", "stream6", "stream6-2", "stream7", "stream8", "stream9",
         "stream10", "stream21", "stream22", "stream23", "stream24", "stream25", "stream26", "stream27"])
    assert not any(s.get("mute") or s.get("solo") for s in ss)
    ok("16 stream, tutti importati da file, nessuno silenziato")


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
    assert vicino(fine_brano, 580.978) and int(fine_brano // 60) == 9 and 40.9 < fine_brano % 60 < 41
    assert vicino(fine_brano, fine(d["stream26"]))
    ok("il brano finisce con `stream26` a 580,978 s: nove minuti e quarantun secondi")
    assert vicino(master["duration"], fine_brano + 10)
    ok("la `duration` del master (590,978 s) e' dieci secondi dopo l'ultimo stream")
    righe = [dict(onset=float(s["onset"]), durata=float(s["duration"]), muto=False) for s in ss]
    vuoti = tratti_vuoti(righe, fine_brano)
    assert len(vuoti) == 1 and vicino(vuoti[0][0], RESPIRO[0]) and vicino(vuoti[0][1], RESPIRO[1])
    assert 0.78 < vuoti[0][1] - vuoti[0][0] < 0.79
    ok("nel brano c'e' un solo tratto senza stream: 0,8 s fra la fine di `stream8` (278 s) e l'ingresso di `stream24`")
    gruppi = [[], []]
    for s in ss:
        gruppi[float(s["onset"]) >= RESPIRO[1] - 1e-6].append(s)
    assert [len(g) for g in gruppi] == [9, 7]
    for g, (primo, ultimo_stream, _) in zip(gruppi, GRUPPI):
        ordine = [s["stream_id"] for s in sorted(g, key=lambda s: (float(s["onset"]), s["stream_id"]))]
        assert ordine[0] == primo and ordine[-1] == ultimo_stream, (ordine, primo, ultimo_stream)
    assert sorted(s["stream_id"] for s in gruppi[0]) == sorted(
        ["stream2", "stream3", "stream9", "stream5", "stream6", "stream6-2", "stream7", "stream8", "stream10"])
    picchi = [max(n for a, b, n in sovrapposizioni([(float(s["onset"]), fine(s)) for s in g])) for g in gruppi]
    assert picchi == [7, 5]
    primo = sovrapposizioni([(float(s["onset"]), fine(s)) for s in gruppi[0]])
    sette = [(a, b) for a, b, n in primo if n == 7]
    assert len(sette) == 2 and vicino(sette[1][0], 116.934) and vicino(sette[1][1], 125.309)
    ok("due gruppi, di 9 e di 7 stream, con al massimo 7 (fra i secondi 117 e 125) e 5 stream insieme")
    tratti = sovrapposizioni([(float(s["onset"]), fine(s)) for s in ss])
    assert max(n for a, b, n in tratti) == 7
    solo = [(a, b) for a, b, n in tratti if n == 1 and 278 < a < 342]
    assert len(solo) == 1 and solo[0][1] - solo[0][0] > 60
    assert vicino(solo[0][0], float(d["stream24"]["onset"])) and vicino(solo[0][1], float(d["stream21"]["onset"]))
    ok("`stream24` suona da solo per oltre un minuto (62,8 s) all'inizio del secondo gruppo")
    uno = [(a, b) for a, b, n in tratti if n == 1 and 200 < a < 278]
    assert len(uno) == 1 and vicino(uno[0][0], fine(d["stream9"])) and vicino(uno[0][1], fine(d["stream8"]))
    ok("alla fine del primo gruppo resta il solo `stream8`, che finisce a 277,9 s")
    ultimo = [(a, b) for a, b, n in tratti if n == 1 and a > 500]
    assert len(ultimo) == 1 and vicino(ultimo[0][0], fine(d["stream23"])) and vicino(ultimo[0][1], fine_brano)
    ok("alla fine resta il solo `stream26`, per gli ultimi 3,9 s")


# --- 3. i campioni ----------------------------------------------------------------

def campioni():
    _, ss = master_e_stream()
    nomi = {s["sample"] for s in ss}
    frammenti = sorted(n for n in nomi if n.startswith("001-"))
    numerati = sorted(n for n in nomi if re.fullmatch(r"\d{3}\.wav", n))
    assert len(nomi) == 9 and len(frammenti) == 5 and numerati == ["004.wav", "007.wav", "011.wav", "016.wav"]
    for s in ss:
        assert s["sample"] in (numerati if s["stream_id"] in ("stream21", "stream22", "stream23", "stream24")
                               else frammenti)
    ok("il brano usa nove campioni: cinque frammenti `001-*`, nei dodici stream della famiglia, "
       "e quattro file numerati (004, 007, 011, 016), negli altri quattro")


# --- 4. riprese e famiglia -----------------------------------------------------------

def pulito(s):
    return {k: v for k, v in s.items() if k not in ("stream_id", "onset") and not k.startswith("_")}


def chiavi_diverse(a, b, pre=""):
    """Le chiavi (col punto per i blocchi annidati) in cui due stream differiscono."""
    out = set()
    for k in set(a) | set(b):
        x, y = a.get(k), b.get(k)
        if isinstance(x, dict) and isinstance(y, dict) and "points" not in x:
            out |= chiavi_diverse(x, y, pre + k + ".")
        elif x != y:
            out.add(pre + k)
    return out


def riprese_e_famiglia():
    d = per_id()
    base = {"duration", "grain.duration", "grain.read_direction"}
    assert chiavi_diverse(pulito(d["stream25"]), pulito(d["stream6"])) == base | {"volume"}
    assert chiavi_diverse(pulito(d["stream27"]), pulito(d["stream9"])) == base | {"volume"}
    assert chiavi_diverse(pulito(d["stream26"]), pulito(d["stream3"])) == base | {"grain.envelope", "pointer.offset_range"}
    assert chiavi_diverse(pulito(d["stream6-2"]), pulito(d["stream6"])) == base | {"pointer.start"}
    assert valori(d["stream26"]["grain"]["duration"]) == [0.006] and d["stream26"]["grain"]["envelope"] == "bartlett"
    assert valori(d["stream6-2"]["grain"]["duration"]) == [0.001]
    assert d["stream6-2"]["grain"]["read_direction"] == [[0, -1]]
    for ripresa, origine in (("stream25", "stream6"), ("stream26", "stream3"), ("stream27", "stream9"),
                             ("stream6-2", "stream6")):
        assert float(d[ripresa]["onset"]) > fine(d[origine]) and d[ripresa]["sample"] == d[origine]["sample"]
    assert [round(float(d[x]["onset"])) for x in ("stream6-2", "stream25", "stream27", "stream26")] == [117, 414, 415, 440]
    ok("`stream25`, `stream26`, `stream27` e `stream6-2` riprendono `stream6`, `stream3`, `stream9` e `stream6`: "
       "stesso campione, e cambiano la durata, la durata del grano e il verso di lettura "
       "(`stream26` anche la finestra e lo scarto del puntatore); entrano dopo la fine dell'originale")
    famiglia = [d[x] for x in ("stream2", "stream3", "stream9", "stream5", "stream6", "stream10", "stream7",
                               "stream6-2", "stream8", "stream25", "stream26", "stream27")]
    assert len(famiglia) == 12
    assert sum(valori(s["fill_factor"]) == [4.0] for s in famiglia) == 11 and valori(d["stream10"]["fill_factor"]) == [2.0]
    assert sum("read_direction" in s["grain"] for s in famiglia) == 11 and "read_direction" not in d["stream10"]["grain"]
    assert all(s["pan_range"] == 360 for s in famiglia)
    rapporto = {}
    for s in famiglia:
        rapporto.setdefault(max(valori(s["pitch"]["ratio"])) if s["stream_id"] != "stream2" else 0.2,
                            []).append(s["stream_id"])
    assert {k: len(v) for k, v in rapporto.items()} == {0.2: 7, 0.5: 2, 1.0: 3}
    assert valori(d["stream2"]["pitch"]["ratio"]) == [0.2, 0.4, 0.2]
    assert all(s["pitch"].get("range", 0) == 0.05 for s in famiglia if max(valori(s["pitch"]["ratio"])) <= 0.4)
    assert max(v for s in famiglia for v in valori(s["pointer"]["speed_ratio"])) == 0.35
    assert max(valori(d["stream8"]["pointer"]["speed_ratio"])) == 0.35
    assert max(v for s in famiglia if s["stream_id"] != "stream8" for v in valori(s["pointer"]["speed_ratio"])) == 0.1
    brevi = [v for s in famiglia for v in valori(s["grain"]["duration"])]
    assert min(brevi) == 0.0004 and max(brevi) < 0.019
    ok("famiglia di dodici stream: fattore di riempimento 4 in undici, verso di lettura in undici, pan su 360 gradi, "
       "rapporto di altezza 0,2 / 0,5 / 1 in sette / due / tre, puntatore a 0,1 o meno (0,35 solo in `stream8`)")


# --- 5. i due vocabolari --------------------------------------------------------------

def vocabolari():
    d = per_id()
    durate = {k: valori(s["grain"]["duration"]) for k, s in d.items()}
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
    for sid, lo, hi in (("stream22", 3.09, 32.9), ("stream23", 2.53, 53.11)):
        assert "fill_factor" not in d[sid] and min(valori(d[sid]["density"])) == lo and max(valori(d[sid]["density"])) == hi
        assert isinstance(d[sid]["grain"]["envelope"], list) and len(d[sid]["grain"]["envelope"]) == 4
    s23 = d["stream23"]
    assert s23["voices"]["num_voices"] == 4 and s23["volume_range"] == 20
    assert s23["sample"] == "007.wav" and s23["pitch"] == {"ratio": 0.3, "range": 0.4}
    assert s23["voices"]["pitch"] == {"pitch_range": 38, "strategy": "range", "unit": "quarter_tone"}
    assert s23["grain"]["duration"] == 3 and s23["grain"]["duration_range"] == 1
    assert s23["grain"]["envelope"] == ["hanning", "expodec", "rexporise", "exporise"]
    assert min(valori(s23["volume"])) == -90 and max(valori(s23["volume"])) == -4.76 and valori(s23["volume"])[-2] == -4.76
    assert 1 / 0.1 == 10 and 3 / 0.1 == 30
    ok("`stream22` e `stream23`: densita' dichiarata (3-33 e 2,5-53 grani/s), lista di quattro finestre, "
       "grani da 10 a 30 volte il limite di 100 ms; `stream23`: `007.wav`, rapporto 0,3 con banda 0,4, "
       "quattro voci a `range` su 38 quarti di tono, grano di 3 s con banda di 1 s, volume fino a -4,76 dB")
    gate = {k: s["deviation_probability"] for k, s in d.items() if "deviation_probability" in s}
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
    assert sum(GRANI.values()) == TOTALE_BRANO
    ok(f"grani del brano: {TOTALE_BRANO:,} (circa {TOTALE_BRANO / 1e6:.1f} milioni), uno stream alla volta come "
       f"nella tabella".replace(",", " "))
    _, ss = master_e_stream()
    gruppi = [[], []]
    for s in ss:
        gruppi[float(s["onset"]) >= RESPIRO[1] - 1e-6].append(s["stream_id"])
    for nomi, (primo, ultimo, atteso) in zip(gruppi, GRUPPI):
        assert sum(GRANI[x] for x in nomi) == atteso, (primo, atteso)
    ok("grani per gruppo: 4 599 921 e 4 895 429")
    tre = sum(GRANI[x] for x in ("stream24", "stream9", "stream3"))
    assert tre / TOTALE_BRANO > 0.60 and GRANI["stream24"] == max(GRANI.values())
    assert sorted(GRANI, key=GRANI.get)[-3:] == ["stream3", "stream9", "stream24"]
    ok(f"`stream24`, `stream9` e `stream3` hanno il {100 * tre / TOTALE_BRANO:.0f}% dei grani del brano")
    assert per_stream["stream24"]["picco"] > 35000 and per_stream["stream24"]["picco"] / RIVERRUN > 15
    assert per_stream["stream24"]["picco"] == max(r["picco"] for r in risultati)
    ok(f"`stream24` arriva a {per_stream['stream24']['picco']} grani al secondo, "
       f"{per_stream['stream24']['picco'] / RIVERRUN:.1f} volte il massimo di Riverrun")
    assert per_stream["stream22"]["concorrenti"] == 102 and per_stream["stream23"]["concorrenti"] == 615
    ok("grani sovrapposti: fino a 102 in `stream22` e a 615 in `stream23`")
    assert per_stream["stream23"]["voci"] == 4 and per_stream["stream3"]["voci"] == 4
    assert per_stream["stream9"]["voci"] == 2 and per_stream["stream27"]["voci"] == 2


# --- 7. realizzazioni ----------------------------------------------------------------

def realizzazioni():
    d = per_id()
    a = copy.deepcopy(d["stream6"])
    b = copy.deepcopy(d["stream6"])
    a["onset"], b["onset"] = 0.0, 10.0
    a["stream_id"], b["stream_id"] = "primo", "secondo"
    g = carica_documento([a, b])
    la, lb = lista(g.streams[0]), lista(g.streams[1])
    assert la.shape != lb.shape or not np.allclose(la, lb, atol=1e-9, rtol=0)
    ok("due stream con gli stessi valori e identificativi diversi hanno un'altra realizzazione")
    a["rng_group"] = b["rng_group"] = "gruppo"
    g = carica_documento([a, b])
    la, lb = lista(g.streams[0]), lista(g.streams[1])
    assert la.shape == lb.shape and np.allclose(la, lb, atol=1e-9, rtol=0)
    ok("con lo stesso `rng_group` hanno gli stessi grani, spostati nel tempo")


def stream21_e_voce_sola():
    d = per_id()
    s21 = d["stream21"]
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


def righe_tabella(ss):
    """Le righe della tabella, in ordine di ingresso: (stream, [colonne])."""
    out = []
    for s in sorted(ss, key=lambda s: (float(s["onset"]), ss.index(s))):
        out.append((s["stream_id"],
                    [codice(os.path.splitext(s["sample"])[0]), dec(float(s["onset"])), dec(float(s["duration"])),
                     testo_grano(s["grain"]), testo_voci(s), mig(GRANI[s["stream_id"]])]))
    return out


def tabella():
    _, ss = master_e_stream()
    testo = CAPITOLO.read_text(encoding="utf-8")
    trovate = [(m.group(1), [c.strip() for c in m.group(2).split("|")])
               for m in re.finditer(r"^\|\s*`(stream[\w-]+)`\s*\|(.*)\|\s*$", testo, re.M)]
    assert trovate, "il capitolo non ha la tabella degli stream"
    assert trovate == righe_tabella(ss), [(a, b) for a, b in zip(trovate, righe_tabella(ss)) if a != b]
    ok("la tabella del capitolo (16 righe, in ordine di ingresso) coincide con i dati e con i grani")


# --- 9. il modello di costo --------------------------------------------------------------

def costo():
    _, ss = master_e_stream()
    fine_brano = max(fine(s) for s in ss)
    secondi = 34e-6 * TOTALE_BRANO + 1.4e-3 * fine_brano
    assert 300 < secondi < 360  # «poco piu' di cinque minuti»
    ok(f"modello di costo del capitolo 7 (34 us per grano, 1,4 ms per secondo di uscita): "
       f"{secondi / 60:.1f} minuti a un processo solo")


# --- 10. la regola del repository del brano ---------------------------------------------------

def regola_un_file_per_stream():
    master, ss = master_e_stream()
    testa = MASTER.read_text(encoding="utf-8").splitlines()[:5]
    assert any(r.startswith("# editor:") and "PGE-ui" in r for r in testa)
    # la regola (tests/test_brano.py): ogni voce del master e' un `file:`
    assert all("file" in v for v in master["streams"]) and len(master["streams"]) == 16
    assert set(master) >= {"duration", "bpm", "seed", "streams"}
    for v in master["streams"]:
        assert set(v) <= {"file", "onset", "mute", "solo"}, v  # il master tiene il piazzamento
    ok("il master, salvato da PGE-ui, ha sedici voci e tutte sono `file:`: la regola «un file per stream» "
       "del repository del brano e' rispettata, e il master tiene solo il piazzamento")


if __name__ == "__main__":
    for prova in (testa_e_stream, profilo, campioni, riprese_e_famiglia, vocabolari, grani,
                  realizzazioni, stream21_e_voce_sola, tabella, costo, regola_un_file_per_stream):
        prova()
    print("\ntutte le verifiche passano")
