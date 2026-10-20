#!/usr/bin/env python3
"""Il grafo degli import di pge, per verificare la regola di dipendenza del capitolo 3.

Uso:  python esempi/architettura/dipendenze.py [percorso/di/src/pge]

PGE_DIR (default ../PythonGranularEngine) indica il repo del motore. Legge i sorgenti
come alberi sintattici (non importa nulla) e stampa:
  - quanti moduli e quanti archi di import ci sono, e se tra i moduli esiste un ciclo;
  - quali pacchetti importano `rendering`, `engine`, `export` e la radice (`api`, `cli`);
  - le coppie di pacchetti che si importano a vicenda.
Gli archi sono tutti gli import, anche quelli dentro le funzioni; `--solo-modulo`
tiene soltanto quelli in testa al modulo.
"""
import ast, os, sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PGE = Path(os.environ.get("PGE_DIR", AQUI.parents[1].parent / "PythonGranularEngine"))


def moduli(radice):
    """{nome del modulo: file}, per tutti i .py sotto `radice` (la cartella `pge`)."""
    nomi = {}
    for f in radice.rglob("*.py"):
        parti = f.relative_to(radice.parent).with_suffix("").parts
        nomi[".".join(parti[:-1] if parti[-1] == "__init__" else parti)] = f
    return nomi


def archi(nomi, solo_modulo):
    """{modulo: {moduli pge che importa}}. Un import dentro una funzione o sotto
    TYPE_CHECKING conta soltanto se `solo_modulo` è falso."""
    def risolvi(nome):
        parti = nome.split(".")
        while parti:
            if ".".join(parti) in nomi:
                return ".".join(parti)
            parti.pop()
    grafo = defaultdict(set)
    for nome, f in nomi.items():
        albero = ast.parse(f.read_text(encoding="utf-8"))
        padre = {c: n for n in ast.walk(albero) for c in ast.iter_child_nodes(n)}
        def interno(n):
            while n in padre:
                n = padre[n]
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) or (
                        isinstance(n, ast.If) and "TYPE_CHECKING" in ast.dump(n.test)):
                    return True
            return False
        for n in ast.walk(albero):
            if solo_modulo and interno(n):
                continue
            if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("pge"):
                cand = [n.module] + [f"{n.module}.{a.name}" for a in n.names]
            elif isinstance(n, ast.Import):
                cand = [a.name for a in n.names if a.name.startswith("pge")]
            else:
                continue
            for c in cand:
                dest = risolvi(c)
                if dest and dest != nome:
                    grafo[nome].add(dest)
    return grafo


def cicli(grafo, nomi):
    """Componenti fortemente connesse con più di un modulo (algoritmo di Tarjan)."""
    sys.setrecursionlimit(10000)
    indice, basso, pila, sulla, trovati = {}, {}, [], set(), []
    def visita(v):
        indice[v] = basso[v] = len(indice)
        pila.append(v); sulla.add(v)
        for w in grafo.get(v, ()):
            if w not in indice:
                visita(w); basso[v] = min(basso[v], basso[w])
            elif w in sulla:
                basso[v] = min(basso[v], indice[w])
        if basso[v] == indice[v]:
            comp = []
            while True:
                w = pila.pop(); sulla.discard(w); comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                trovati.append(sorted(comp))
    for v in sorted(nomi):
        if v not in indice:
            visita(v)
    return trovati


RADICE = "radice (api, cli)"


def pacchetto(modulo):
    """Il sotto-pacchetto di un modulo; `pge`, `pge.api` e `pge.cli` stanno alla radice."""
    parti = modulo.split(".")
    return parti[1] if len(parti) > 1 and parti[1] not in ("api", "cli") else RADICE


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    radice = Path(args[0]) if args else PGE / "src" / "pge"
    solo_modulo = "--solo-modulo" in sys.argv
    nomi = moduli(radice)
    grafo = archi(nomi, solo_modulo)
    print(f"{len(nomi)} moduli, {sum(len(v) for v in grafo.values())} archi di import "
          f"({'solo in testa al modulo' if solo_modulo else 'anche dentro le funzioni'})")
    c = cicli(grafo, nomi)
    print(f"cicli tra moduli: {len(c)}")
    for comp in c:
        print("   ", comp)

    tra = defaultdict(set)
    for src, dsts in grafo.items():
        for d in dsts:
            if pacchetto(src) != pacchetto(d):
                tra[(pacchetto(src), pacchetto(d))].add(src)
    print("\nchi importa rendering, engine, export, radice:")
    for bersaglio in ("rendering", "engine", "export", RADICE):
        chi = sorted({a for (a, b) in tra if b == bersaglio})
        print(f"  {bersaglio:10s} <- {', '.join(chi) or 'nessuno'}")
    print("\npacchetti che si importano a vicenda:")
    for (a, b) in sorted(tra):
        if a < b and (b, a) in tra:
            print(f"  {a} <-> {b}")


if __name__ == "__main__":
    main()
