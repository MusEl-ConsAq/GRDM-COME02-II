#!/usr/bin/env python3
"""Verifica le affermazioni del capitolo 3 su generazione lazy e riproducibilità.

Uso:  python esempi/architettura/lazy_e_riproducibilita.py

PGE_DIR (default ../PythonGranularEngine) indica il repo del motore: se ne usano src/
e refs/ (il campione `voice.wav`). Costruisce un brano di tre stream stocastici, poi
controlla, con `assert`, che
  1. dopo il caricamento nessuno stream ha generato i suoi grani, e che il primo accesso
     a `.voices` li genera una volta sola;
  2. i grani non dipendono dall'ordine in cui gli stream si materializzano;
  3. mettere in mute uno stream non cambia i grani degli altri;
  4. un altro seme dà altri grani, e lo stesso seme dà gli stessi grani in processi
     con PYTHONHASHSEED diverso;
  5. un secondo rendering con la cache a regime non genera nessun grano;
  6. il costo della lazy evaluation: uno `Stream` costruito fuori dal `Generator` si
     costruisce senza errori e fallisce soltanto al primo accesso a `.voices`.
"""
import hashlib, os, subprocess, sys, tempfile
from dataclasses import astuple
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
PGE = Path(os.environ.get("PGE_DIR", AQUI.parents[1].parent / "PythonGranularEngine"))
REFS = str(PGE / "refs")
sys.path.insert(0, str(PGE / "src"))

BRANO = {
    "seed": 1441,
    "streams": [
        {"stream_id": "a", "onset": 0, "duration": 4, "sample": "voice.wav",
         "density": 40, "distribution": 0.5,
         "grain": {"duration": 0.05, "duration_range": 0.02},
         "pointer": {"start": 0.2, "speed_ratio": 0.5, "offset_range": 0.1},
         "pitch": {"semitones": 0, "range": 3}, "pan_range": 40,
         "voices": {"num_voices": 2, "pitch": {"strategy": "stochastic", "pitch_range": 6.0}}},
        {"stream_id": "b", "onset": 1, "duration": 4, "sample": "voice.wav",
         "density": 25, "distribution": 1, "grain": {"duration": 0.08},
         "pointer": {"start": 0.5, "speed_ratio": 1, "offset_range": 0.3},
         "pitch": {"semitones": 7, "range": 2}, "pan_range": 60},
        {"stream_id": "c", "onset": 2, "duration": 4, "sample": "voice.wav",
         "density": 60, "distribution": 0.2,
         "grain": {"duration": 0.03, "duration_range": 0.01},
         "pointer": {"start": 0.8, "speed_ratio": 0.25}, "pitch": {"semitones": -5, "range": 1}},
    ],
}


def scrivi(cartella, **modifiche):
    brano = yaml.safe_load(yaml.safe_dump(BRANO))
    brano.update({k: v for k, v in modifiche.items() if k != "mute_b"})
    if modifiche.get("mute_b"):
        brano["streams"][1]["mute"] = True
    percorso = os.path.join(cartella, "brano.yml")
    with open(percorso, "w") as f:
        yaml.safe_dump(brano, f)
    return percorso


def grani(stream):
    return [[astuple(g) for g in voce] for voce in stream.voices]


def impronta(percorso):
    """sha256 di tutti i grani del brano, calcolato in un altro processo."""
    codice = (
        "import sys, hashlib; sys.path.insert(0, sys.argv[1]);"
        "from dataclasses import astuple; from pge import api;"
        "g = api.load_generator(sys.argv[2], samples_dir=sys.argv[3]); h = hashlib.sha256();"
        "[h.update(repr(astuple(x)).encode()) for s in g.streams for v in s.voices for x in v];"
        "print(h.hexdigest()[:16])")
    out = subprocess.run([sys.executable, "-c", codice, str(PGE / "src"), percorso, REFS],
                         capture_output=True, text=True, check=True).stdout
    return out.strip().splitlines()[-1]


def main():
    from pge import api
    with tempfile.TemporaryDirectory() as tmp:
        brano = scrivi(tmp)
        gen = api.load_generator(brano, samples_dir=REFS)
        a = gen.streams[0]

        assert [s.generated for s in gen.streams] == [False] * 3
        assert "grains=lazy" in repr(a)
        riferimento = {s.stream_id: grani(s) for s in gen.streams}
        assert a.generated and f"grains={sum(map(len, a._voices))}" in repr(a)
        assert a.voices is a._voices                                    # memoizzato
        print(f"1. alla costruzione nessun grano; primo accesso: "
              f"{sum(map(len, riferimento['a']))} grani, poi la stessa lista")

        inverso = api.load_generator(brano, samples_dir=REFS)
        assert {s.stream_id: grani(s) for s in reversed(inverso.streams)} == riferimento
        print("2. materializzando c, b, a invece di a, b, c i grani sono identici")

        muto = api.load_generator(scrivi(tmp, mute_b=True), samples_dir=REFS)
        assert [s.stream_id for s in muto.streams] == ["a", "c"]
        assert all(grani(s) == riferimento[s.stream_id] for s in muto.streams)
        print("3. con lo stream b in mute, a e c hanno gli stessi grani")

        altro = api.load_generator(scrivi(tmp, seed=7), samples_dir=REFS)
        assert grani(altro.streams[0]) != riferimento["a"]
        brano = scrivi(tmp)
        impronte = {}
        for hashseed in ("0", "1", "12345"):
            os.environ["PYTHONHASHSEED"] = hashseed
            impronte[hashseed] = impronta(brano)
        assert len(set(impronte.values())) == 1
        print(f"4. seme 7 dà altri grani; seme 1441 in tre processi con PYTHONHASHSEED "
              f"diverso: sempre {next(iter(impronte.values()))}")

        manifesto, uscita = os.path.join(tmp, "manifesto.json"), os.path.join(tmp, "o.aif")
        prima = api.load_generator(brano, samples_dir=REFS)
        api.render(prima, uscita, renderer="numpy", per_stream=True,
                   cache_manifest_path=manifesto, samples_dir=REFS)
        assert all(s.generated for s in prima.streams)
        seconda = api.load_generator(brano, samples_dir=REFS)
        api.render(seconda, uscita, renderer="numpy", per_stream=True,
                   cache_manifest_path=manifesto, samples_dir=REFS)
        assert [s.generated for s in seconda.streams] == [False] * 3
        print("5. primo rendering con la cache: tre stream generati; secondo: nessun grano generato")

        from pge.core.stream import Stream
        solo = Stream({"stream_id": "x", "sample": "voice.wav", "duration": 1, "density": 20},
                      seed=1, samples_dir=REFS + "/")
        try:
            solo.voices
        except AttributeError as errore:
            assert "window_table_map" in str(errore)
            print(f"6. Stream fuori dal Generator: si costruisce ({solo}); "
                  f"il primo accesso a .voices solleva AttributeError: {errore}")
        else:
            raise AssertionError("lo Stream senza Generator avrebbe dovuto fallire")


if __name__ == "__main__":
    main()
