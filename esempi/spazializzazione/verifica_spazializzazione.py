#!/usr/bin/env python3
"""Verifica le formule e le cifre del capitolo 11 (la spazializzazione per n altoparlanti).

Uso:  python esempi/spazializzazione/verifica_spazializzazione.py

Solo numpy: il capitolo descrive un metodo (Blumlein, Gerzon) e non una funzione di PGE,
quindi non c'e' un motore da interrogare. Ogni sezione controlla con `assert` una parte
del capitolo:
  1. la codifica Mid-Side: potenza costante, equivalenza con L/R del capitolo 7,
     la matrice somma/differenza che e' la propria inversa;
  2. il Mid che non e' una figura di otto: l'orientamento dei lobi di L e R;
  3. la decodifica a un microfono virtuale per altoparlante: figura di otto, cardioide,
     nucleo 1 + 2cos, fattore di direttivita';
  4. il decoder a n altoparlanti regolari: somma, potenza, guadagni della tabella;
  5. la gerarchia armonica: 2n + 1 canali, direttivita' pari al numero dei canali;
  6. il sistema a quattro altoparlanti del 1970 e il raddoppio dell'angolo.
Le citazioni e le pagine di Gerzon si controllano sulle fonti e non si verificano qui.
"""
import numpy as np

TH = np.radians(np.arange(0, 360, 0.5))          # azimut della sorgente, 0 davanti, + a sinistra
TOL = 1e-12


def direttivita(f):
    """Fattore di direttivita' sul cerchio: max |f|^2 / media di |f|^2 (Gerzon 1973, p. 5)."""
    th = np.radians(np.arange(0, 360, 0.01))
    v = f(th)
    return np.max(v ** 2) / np.mean(v ** 2)


# ---------------------------------------------------------------------------
# 1. La codifica Mid-Side
# ---------------------------------------------------------------------------
s = np.random.default_rng(1).standard_normal(8)   # un segnale qualsiasi
M = np.outer(np.cos(TH), s)
S = np.outer(np.sin(TH), s)
assert np.allclose(M ** 2 + S ** 2, s ** 2, atol=TOL)                # potenza costante a ogni angolo

L = (M + S) / np.sqrt(2)                                             # capitolo 7
R = (M - S) / np.sqrt(2)
assert np.allclose(L, np.outer(np.cos(TH - np.radians(45)), s), atol=TOL)   # L: figura di otto a +45
assert np.allclose(R, np.outer(np.cos(TH + np.radians(45)), s), atol=TOL)   # R: figura di otto a -45
assert np.allclose(L ** 2 + R ** 2, M ** 2 + S ** 2, atol=TOL)       # eq. 22 di Gerzon 1992

# in stereo il dietro si piega sul davanti: un grano a 180 - theta suona come lo speculare
# davanti (L e R scambiati), a polarita' invertita
TH2 = np.radians(180.0) - TH
L2 = np.outer(np.cos(TH2 - np.radians(45)), s)
R2 = np.outer(np.cos(TH2 + np.radians(45)), s)
assert np.allclose(L2, -R, atol=TOL) and np.allclose(R2, -L, atol=TOL)

MS = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
assert np.allclose(MS @ MS, np.eye(2), atol=TOL)                      # due matrici in cascata: l'identita'
print("1. codifica Mid-Side: ok")

# ---------------------------------------------------------------------------
# 2. Il Mid non e' sempre una figura di otto: L, R = (M +- S)/sqrt(2) con M = a + b cos
# ---------------------------------------------------------------------------
for b, atteso in ((0.0, 90.0), (0.5, 63.43), (1.0, 45.0)):            # Mid omni, a meta', figura di otto
    a = 1.0 - b
    left = (a + b * np.cos(TH) + np.sin(TH)) / np.sqrt(2)
    picco = np.degrees(TH[np.argmax(left)])
    assert abs(picco - atteso) < 0.5, (b, picco)
    assert abs(np.degrees(np.arctan2(1, b)) - atteso) < 0.01          # atan(1/b)
print("2. il Mid non e' una figura di otto: ok")

# ---------------------------------------------------------------------------
# 3. Un microfono virtuale per altoparlante: g = a + b cos(theta - phi)
# ---------------------------------------------------------------------------
otto = lambda t: np.cos(t)
cardioide = lambda t: 0.5 + 0.5 * np.cos(t)
ipercardioide = lambda t: (1 + 2 * np.cos(t)) / 3                     # il nucleo di Gerzon 1977, eq. 3
omni = lambda t: np.ones_like(t)

assert abs(direttivita(omni) - 1) < 1e-6
assert abs(direttivita(otto) - 2) < 1e-6
assert abs(direttivita(cardioide) - 8 / 3) < 1e-6
assert abs(direttivita(ipercardioide) - 3) < 1e-6
assert abs(ipercardioide(np.radians(120.0))) < 1e-12                  # il nullo a 120 gradi

b = np.linspace(0.01, 0.99, 9801)                                     # a + b = 1: il massimo e' in b = 2/3
gamma = 1 / ((1 - b) ** 2 + b ** 2 / 2)
assert abs(b[np.argmax(gamma)] - 2 / 3) < 1e-3 and abs(gamma.max() - 3) < 1e-6

offset = np.radians([0, 45, 90, 135, 180])                            # la tabella del capitolo, normalizzata al picco
tabella = np.array([f(offset) for f in (otto, cardioide, ipercardioide)])
atteso = np.array([[1, 0.707, 0, -0.707, -1],
                   [1, 0.854, 0.5, 0.146, 0],
                   [1, 0.805, 0.333, -0.138, -0.333]])
assert np.allclose(tabella, atteso, atol=1e-3), tabella
print("3. microfono virtuale per altoparlante: ok")

# ---------------------------------------------------------------------------
# 4. Il decoder a n altoparlanti regolari: g_k = (1/N)(W + 2 (M cos phi_k + S sin phi_k))
# ---------------------------------------------------------------------------
def decoder(theta, N, phi0=0.0, w=1.0, m=2.0):
    """Guadagni degli N altoparlanti per un segnale unitario a theta (rad); w pesa W, m pesa M e S."""
    phi = phi0 + 2 * np.pi * np.arange(N) / N
    W, M_, S_ = 1.0, np.cos(theta), np.sin(theta)
    return (w * W + m * (M_ * np.cos(phi) + S_ * np.sin(phi))) / N


for N in range(3, 13):
    for t in np.radians((0, 17, 45, 90, 133, 251)):
        g = decoder(t, N)
        assert abs(g.sum() - 1) < 1e-12                               # la pressione al centro e' quella del segnale
        assert abs((g ** 2).sum() - 3 / N) < 1e-12                    # potenza costante in theta, 3/N
        f8 = decoder(t, N, w=0.0, m=1.0 * N)                          # solo M e S: figura di otto pura
        assert abs(f8.sum()) < 1e-12 and abs((f8 ** 2).sum() - N / 2) < 1e-12   # somma nulla: nessuna pressione

g4 = decoder(0.0, 4)
assert np.allclose(g4, [0.75, 0.25, -0.25, 0.25])
g4m = decoder(np.radians(45), 4)
assert np.allclose(g4m, [0.6036, 0.6036, -0.1036, -0.1036], atol=1e-4)
g8 = decoder(0.0, 8)
assert np.allclose(g8, [0.375, 0.3018, 0.125, -0.0518, -0.125, -0.0518, 0.125, 0.3018], atol=1e-4)
assert np.allclose(decoder(0.0, 4, w=0.0, m=4.0), [1, 0, -1, 0])      # M e S soli, quattro altoparlanti: dietro in controfase
print("4. decoder a n altoparlanti: ok")

# ---------------------------------------------------------------------------
# 5. La gerarchia armonica: 1, cos m, sin m  (m = 1..n), 2n + 1 canali, direttivita' 2n + 1
# ---------------------------------------------------------------------------
def nucleo(n):
    return lambda t: 1 + 2 * sum(np.cos(m * t) for m in range(1, n + 1))


for n in (1, 2, 3, 4):
    assert abs(direttivita(nucleo(n)) - (2 * n + 1)) < 1e-6           # direttivita' = numero di canali
assert abs(nucleo(1)(np.radians(120.0))) < 1e-12                      # il caso n = 1 e' il nucleo 1 + 2cos
for n in (1, 2, 3):
    for N in range(2 * n + 1, 13):
        phi = 2 * np.pi * np.arange(N) / N
        for t in np.radians((0, 17, 133)):
            assert abs(nucleo(n)(t - phi).sum() / N - 1) < 1e-9       # la somma resta il segnale
print("5. gerarchia armonica: ok")

# ---------------------------------------------------------------------------
# 6. Il 1970: L, R, L+R, L-R su quattro altoparlanti, e il raddoppio dell'angolo
# ---------------------------------------------------------------------------
def quattro(alfa):
    c, sn = np.cos(alfa), np.sin(alfa)
    l, r = (c + sn) / np.sqrt(2), (c - sn) / np.sqrt(2)               # coppia Blumlein
    return {"davanti": (l + r) / np.sqrt(2), "sinistra": l, "dietro": (l - r) / np.sqrt(2), "destra": r}


piu_forte = lambda a: max(quattro(np.radians(a)).items(), key=lambda kv: abs(kv[1]))[0]
assert [piu_forte(a) for a in (0, 45, 90, 135, 180, 225, 270, 315, 360)] == \
    ["davanti", "sinistra", "dietro", "destra", "davanti", "sinistra", "dietro", "destra", "davanti"]
# mezzo giro attorno ai microfoni (180 gradi) e' un giro intero attorno agli altoparlanti:
# un giro attorno ai microfoni sono due giri.

c, sn = np.cos(TH), np.sin(TH)
l, r = (c + sn) / np.sqrt(2), (c - sn) / np.sqrt(2)
A, B, C, D = 0.924 * l - 0.383 * r, 0.924 * l + 0.383 * r, 0.383 * l + 0.924 * r, -0.383 * l + 0.924 * r
for x, ang in ((A, 67.5), (B, 22.5), (C, -22.5), (D, -67.5)):         # i coefficienti sono cos e sin di 22,5 gradi
    assert np.allclose(x, np.cos(TH - np.radians(ang)), atol=2e-3)
assert abs(np.cos(np.radians(22.5)) - 0.924) < 1e-3 and abs(np.sin(np.radians(22.5)) - 0.383) < 1e-3
print("6. il sistema a quattro altoparlanti del 1970: ok")

print("tutte le verifiche passano")
