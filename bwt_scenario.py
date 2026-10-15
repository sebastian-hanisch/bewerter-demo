"""Szenario: Reglerwerte (Settings) und die simulierten Bewerter einer Instanz.

Wahrheit: n Teilnehmer mit gleichabständigen Stärken (Generator Version 1), Teilnehmer 0 ist der Beste; P(i schlägt j) = σ(s_i − s_j). Jeder ehrliche Bewerter bringt die Rangfolge nach den Siegen
seines eigenen kleinen Turniers (k Partien je Paar: gut 16, mittel 4, schlecht 1). Zufalls-Bewerter bringen eine zufällige Rangfolge. Manipulatoren bringen die Rangfolge eines mittleren
Bewerters, setzen aber das Ziel auf Platz 1 und/oder den wahren Besten auf den letzten Platz.

Zufall nur über SplitMix64 (Generator der Linie), je Bewerter ein eigener Strom aus (Seed, laufende Nummer), Reihenfolge der Bewerter: gute, mittlere, schlechte, Zufall, Manipulatoren.
Strom eines Bewerters: je Paar k Werte für die Ausgänge, dann n Werte für Gleichstände der Siegzahl (ehrlich) bzw. n Werte für die zufällige Rangfolge (Zufall)."""

from dataclasses import dataclass

import numpy as np

import bwt_constants as C
import turnier_generator as T

_SALT_RATER, _SALT_TB = 0xB3A7, 0x7B11
_MASK = (1 << 64) - 1
TYPES = ("gut", "mittel", "schlecht", "Zufall", "Manipulator")


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    n_good: int = C.DEFAULT_GOOD
    n_mid: int = C.DEFAULT_MID
    n_bad: int = C.DEFAULT_BAD
    n_rand: int = C.DEFAULT_RAND
    n_manip: int = C.DEFAULT_MANIP
    strategy: str = C.DEFAULT_STRATEGY
    target_rank: int = C.DEFAULT_TARGET
    seed: int = C.DEFAULT_SEED


@dataclass(frozen=True)
class Instance:
    strengths: np.ndarray
    types: tuple                # Typ je Bewerter
    ranks: np.ndarray           # (Bewerter, Teilnehmer) Platzziffern, 0 = bester
    tb: np.ndarray              # fester Gleichstandsschlüssel je Teilnehmer
    target: int                 # Index des Ziels
    best: int                   # Index des wahren Besten (0)


def strengths_for(n: int) -> np.ndarray:
    return C.DELTA * (np.arange(n) - (n - 1) / 2.0)[::-1].copy()


def _rater_rng(seed: int, index: int) -> T.SplitMix64:
    return T.SplitMix64((int(seed) * 0x9E3779B97F4A7C15 + (int(index) + 1) * 0xBF58476D1CE4E5B9 + _SALT_RATER) & _MASK)


def _to_rank(order) -> np.ndarray:
    rank = np.empty(len(order), dtype=int)
    rank[list(order)] = np.arange(len(order))
    return rank


def honest_ranking(s: np.ndarray, k: int, rng: T.SplitMix64) -> np.ndarray:
    """Rangfolge nach den Siegen eines eigenen Turniers mit k Partien je Paar; Gleichstände nach einem eigenen kleinen Zufallswert."""
    n = len(s)
    iu = np.triu_indices(n, 1)
    u = rng.uniform(len(iu[0]) * k).reshape(k, len(iu[0]))
    p = 1.0 / (1.0 + np.exp(-(s[iu[0]] - s[iu[1]])))
    w_i = (u < p[None, :]).sum(axis=0)
    wins = np.zeros(n)
    np.add.at(wins, iu[0], w_i)
    np.add.at(wins, iu[1], k - w_i)
    key = wins + 1e-6 * rng.uniform(n)
    return _to_rank(np.argsort(-key, kind="stable"))


def spam_ranking(n: int, rng: T.SplitMix64) -> np.ndarray:
    return _to_rank(np.argsort(rng.uniform(n), kind="stable"))


def manipulate(base: np.ndarray, target: int, best: int, strategy: str) -> np.ndarray:
    """Aus der ehrlichen Rangfolge `base` eine manipulierte machen: Ziel nach vorn und/oder der Beste ans Ende."""
    order = [int(i) for i in np.argsort(base, kind="stable")]
    if strategy in (C.STRATEGIES[0], C.STRATEGIES[2]) and target != order[0]:
        order.remove(target)
        order.insert(0, target)
    if strategy in (C.STRATEGIES[1], C.STRATEGIES[2]) and best != order[-1]:
        order.remove(best)
        order.append(best)
    return _to_rank(order)


def build(n: int, n_good: int, n_mid: int, n_bad: int, n_rand: int, n_manip: int, strategy: str, target_rank: int, seed: int) -> Instance:
    s = strengths_for(n)
    target = min(max(int(target_rank), 2), n) - 1
    types, ranks = [], []
    j = 0
    for count, kind in ((n_good, "gut"), (n_mid, "mittel"), (n_bad, "schlecht"), (n_rand, "Zufall"), (n_manip, "Manipulator")):
        for _ in range(count):
            rng = _rater_rng(seed, j)
            if kind == "Zufall":
                r = spam_ranking(n, rng)
            else:
                k = {"gut": C.K_GOOD, "mittel": C.K_MID, "schlecht": C.K_BAD, "Manipulator": C.K_MID}[kind]
                r = honest_ranking(s, k, rng)
                if kind == "Manipulator":
                    r = manipulate(r, target, 0, strategy)
            types.append(kind)
            ranks.append(r)
            j += 1
    tb = T.SplitMix64(int(seed) ^ _SALT_TB).uniform(n)
    return Instance(s, tuple(types), np.array(ranks, dtype=int).reshape(len(ranks), n), tb, target, 0)


def simulate(s: Settings) -> Instance:
    return build(s.n, s.n_good, s.n_mid, s.n_bad, s.n_rand, s.n_manip, s.strategy, s.target_rank, s.seed)
