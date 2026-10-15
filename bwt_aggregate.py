"""Zusammenfassen mehrerer Rangfolgen zu einer: Borda, Median-Rang, Copeland, Kemeny (exakt, Teilmengen-DP) und gewichtetes Borda; Kendall-Abstand.

Eine Rangfolge ist ein Vektor `rank` der Platzziffern je Teilnehmer (0 = bester). Gleichstände löst ein fester Schlüssel `tb` (kleinerer Wert gewinnt) auf, derselbe für alle Verfahren,
damit kein Verfahren durch die Reihenfolge der Teilnehmer begünstigt wird."""

import numpy as np

import bwt_constants as C


def order_to_rank(order) -> np.ndarray:
    rank = np.empty(len(order), dtype=int)
    rank[list(order)] = np.arange(len(order))
    return rank


def _sorted(score, tb) -> np.ndarray:
    """Rang aus Werten (kleiner = besser); Gleichstände nach tb."""
    order = np.lexsort((tb, np.asarray(score, dtype=float)))
    return order_to_rank(order)


def kendall(a, b) -> int:
    """Anzahl der Paare, die die Platzziffern a und b verschieden ordnen."""
    a, b = np.asarray(a), np.asarray(b)
    iu = np.triu_indices(len(a), 1)
    return int((np.sign(a[iu[0]] - a[iu[1]]) * np.sign(b[iu[0]] - b[iu[1]]) < 0).sum())


def borda(ranks, tb, w=None) -> np.ndarray:
    ranks = np.asarray(ranks, dtype=float)
    w = np.ones(len(ranks)) if w is None else np.asarray(w, dtype=float)
    return _sorted((ranks * w[:, None]).sum(axis=0), tb)


def median_rank(ranks, tb) -> np.ndarray:
    ranks = np.asarray(ranks, dtype=float)
    return _sorted(np.median(ranks, axis=0) + 1e-3 * ranks.mean(axis=0), tb)


def pref_matrix(ranks, w=None) -> np.ndarray:
    """P[i, j] = (gewichtete) Zahl der Bewerter, die i vor j setzen."""
    ranks = np.asarray(ranks)
    w = np.ones(len(ranks)) if w is None else np.asarray(w, dtype=float)
    return np.einsum("k,kij->ij", w, (ranks[:, :, None] < ranks[:, None, :]).astype(float))


def copeland(ranks, tb) -> np.ndarray:
    P = pref_matrix(ranks)
    n = P.shape[0]
    wins = (P > P.T).sum(axis=1) + 0.5 * ((P == P.T).sum(axis=1) - 1)
    return _sorted(-wins, tb)


def kemeny(ranks, tb) -> np.ndarray:
    """Rangfolge mit der kleinsten Summe der Kendall-Abstände zu den Eingaben (exakt, O(2^n n²)); Gleichstände nach tb."""
    P = pref_matrix(ranks)
    n = P.shape[0]
    tb_rank = np.argsort(np.argsort(tb, kind="stable"), kind="stable")
    cost_table = {0: (0.0, None)}
    for mask in range(1 << n):
        if mask not in cost_table:
            continue
        base = cost_table[mask][0]
        placed = [i for i in range(n) if mask >> i & 1]
        for j in range(n):
            if mask >> j & 1:
                continue
            cost = base + sum(P[j, i] for i in placed) + 1e-9 * (n - 1 - tb_rank[j]) * len(placed)
            nm = mask | 1 << j
            if nm not in cost_table or cost < cost_table[nm][0] - 1e-12:
                cost_table[nm] = (cost, (mask, j))
    mask, order = (1 << n) - 1, []
    while mask:
        prev, j = cost_table[mask][1]
        order.append(j)
        mask = prev
    return order_to_rank(order[::-1])


def weights_by_agreement(ranks, consensus) -> np.ndarray:
    n = len(consensus)
    maxd = n * (n - 1) / 2
    return np.array([max(0.0, 1.0 - 2.0 * kendall(r, consensus) / maxd) for r in ranks])


def weighted_borda(ranks, tb, rounds: int = C.WEIGHT_ROUNDS) -> tuple:
    """Borda mit Gewichten = Übereinstimmung mit dem Konsens (1 − 2 · Abstand / größter Abstand, nicht unter 0), `rounds` Runden. Rückgabe: (Rangfolge, Gewichte)."""
    consensus = borda(ranks, tb)
    w = np.ones(len(ranks))
    for _ in range(rounds):
        w = weights_by_agreement(ranks, consensus)
        if w.sum() == 0:
            w = np.ones(len(ranks))
        consensus = borda(ranks, tb, w)
    return consensus, w


def aggregate_all(ranks, tb) -> dict:
    return {"Borda": borda(ranks, tb), "Median": median_rank(ranks, tb), "Copeland": copeland(ranks, tb), "Kemeny": kemeny(ranks, tb),
            "Borda gewichtet": weighted_borda(ranks, tb)[0]}
