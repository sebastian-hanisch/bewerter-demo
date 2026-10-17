"""Eigenschaftstests (metamorph) für die Aggregation der Bewerter (ORACLE-PLAYBOOK §5.2).

Je Eigenschaft 20 bis 50 Zufallsprofile mit festem Seed (numpy default_rng) plus Randfälle. Geprüft werden Aussagen über das Verfahren, deren
Richtigkeit nicht vom heutigen Code abhängt:

1. Einstimmiges Profil: Borda, Median, Copeland, Kemeny und gewichtetes Borda geben genau diese Rangfolge zurück (auch ein einzelner Bewerter).
2. Reihenfolge der Bewerter ist gleichgültig (Summen, Mediane, Mehrheitsmatrix und Kemeny-Kosten sind symmetrisch in den Bewertern).
3. Umnummerieren der Kandidaten (mit mitgeführtem Gleichstandsschlüssel) ist äquivariant.
4. Umkehren aller Eingaben (Platz p -> n-1-p) kehrt Borda-Punkte um; mit negiertem Gleichstandsschlüssel kehrt es Borda, Median und Copeland
   exakt um, bei Kemeny ist die Umkehrung ein Optimum (eindeutig, wenn das Optimum eindeutig ist).
5. Pareto-Eigenschaft: setzen alle Bewerter a vor b, steht a bei jedem der fünf Verfahren vor b.
6. Condorcet-Sieger steht bei Copeland und Kemeny vorn (Beweis: Hochziehen des Siegers verbessert jedes Paar strikt), der Condorcet-Verlierer
   steht bei Copeland und Kemeny hinten und gewinnt nie bei Borda (sein Punktwert liegt strikt unter dem Mittelwert (n-1)*m/2).
7. Gewichte: ein Bewerter, der dem Konsens gleicht, hat Gewicht 1, der umgekehrte 0; das Gewicht fällt mit dem Kendall-Abstand; das gewichtete
   Borda ist invariant gegen gemeinsame positive Skalierung der Gewichte; im Mittel über Seeds hat ein ehrlicher Bewerter ein größeres Gewicht als
   ein Zufalls-Bewerter, solange die ehrlichen in der Mehrheit sind.
8. Kendall-Abstand ist eine Metrik (Symmetrie, Dreiecksungleichung, Umkehrung = n(n-1)/2) und invariant gegen gemeinsames Umnummerieren.

Quellen: nur Definitionen aus dem Code-Docstring und elementare Beweise (siehe oben), keine Messwerte.
"""

import itertools

import numpy as np
import pytest

import bwt_aggregate as A
import bwt_constants as C
import bwt_scenario as SC

METHODS = {
    "Borda": A.borda,
    "Median": A.median_rank,
    "Copeland": A.copeland,
    "Kemeny": A.kemeny,
    "Borda gewichtet": lambda r, tb: A.weighted_borda(r, tb)[0],
}
FAST = ("Borda", "Median", "Copeland", "Borda gewichtet")


def random_profile(rng, m, n):
    ranks = np.array([rng.permutation(n) for _ in range(m)], dtype=int)
    tb = rng.random(n)
    return ranks, tb


def instances(seed, count=30, n_choices=(3, 4, 5, 6), m_choices=(1, 2, 3, 5, 7, 8)):
    rng = np.random.default_rng(seed)
    for _ in range(count):
        n = int(rng.choice(n_choices))
        m = int(rng.choice(m_choices))
        yield (*random_profile(rng, m, n), n, m)


def kemeny_cost(P, order):
    return sum(P[order[b], order[a]] for a in range(len(order)) for b in range(a + 1, len(order)))


def optimal_orders(ranks):
    n = ranks.shape[1]
    P = A.pref_matrix(ranks)
    costs = {p: kemeny_cost(P, p) for p in itertools.permutations(range(n))}
    best = min(costs.values())
    return [p for p, c in costs.items() if c == best]


# --- 1 Einstimmiges Profil ----------------------------------------------------------------------------------------------------------------------

def test_unanimous_profile_returns_that_ranking_for_every_method():
    rng = np.random.default_rng(101)
    for _ in range(30):
        n = int(rng.integers(2, 7))
        m = int(rng.integers(1, 6))
        one = rng.permutation(n)
        ranks = np.tile(one, (m, 1))
        tb = rng.random(n)
        for name, f in METHODS.items():
            assert f(ranks, tb).tolist() == one.tolist(), (name, n, m)


def test_edge_cases_single_rater_and_two_candidates():
    # (ein einzelner Kandidat liegt außerhalb des Bereichs der Demo, N_MIN = 4; das gewichtete Borda teilt dort durch 0: siehe Bericht)
    for ranks in ([[0, 1]] * 3, [[1, 0]] * 3):
        for name, f in METHODS.items():
            assert f(np.array(ranks), np.array([0.3, 0.1])).tolist() == ranks[0], name
    # ein Bewerter: jede Methode gibt dessen Rangfolge zurück
    ranks = np.array([[2, 0, 3, 1]])
    for name, f in METHODS.items():
        assert f(ranks, np.arange(4) * 0.1).tolist() == [2, 0, 3, 1], name


def test_two_opposite_raters_are_decided_by_the_tie_break_key_alone():
    ranks = np.array([[0, 1, 2], [2, 1, 0]])
    for tb, expected in (([0.1, 0.2, 0.3], [0, 1, 2]), ([0.3, 0.2, 0.1], [2, 1, 0]), ([0.2, 0.3, 0.1], [1, 2, 0])):
        for name in ("Borda", "Copeland", "Kemeny"):
            assert METHODS[name](ranks, np.array(tb)).tolist() == expected, (name, tb)


# --- 2 Reihenfolge der Bewerter -----------------------------------------------------------------------------------------------------------------

def test_order_of_raters_does_not_change_the_result():
    rng = np.random.default_rng(202)
    for ranks, tb, n, m in instances(202, 40):
        perm = rng.permutation(m)
        shuffled = ranks[perm]
        for name in FAST + ("Kemeny",):
            a = METHODS[name](ranks, tb)
            b = METHODS[name](shuffled, tb)
            assert a.tolist() == b.tolist(), (name, n, m)


def test_weights_follow_their_rater_when_the_raters_are_reordered():
    rng = np.random.default_rng(203)
    for ranks, tb, n, m in instances(203, 30):
        perm = rng.permutation(m)
        _c1, w1 = A.weighted_borda(ranks, tb)
        _c2, w2 = A.weighted_borda(ranks[perm], tb)
        assert np.allclose(w2, w1[perm], atol=1e-12)


# --- 3 Umnummerieren der Kandidaten -------------------------------------------------------------------------------------------------------------

def relabel(ranks, tb, p):
    ranks2 = np.empty_like(ranks)
    ranks2[:, p] = ranks
    tb2 = np.empty_like(tb)
    tb2[p] = tb
    return ranks2, tb2


def test_relabelling_candidates_is_equivariant():
    rng = np.random.default_rng(303)
    for ranks, tb, n, m in instances(303, 40):
        p = rng.permutation(n)            # Kandidat i heißt danach p[i]
        ranks2, tb2 = relabel(ranks, tb, p)
        for name in FAST:
            r1 = METHODS[name](ranks, tb)
            r2 = METHODS[name](ranks2, tb2)
            assert r2[p].tolist() == r1.tolist(), (name, n, m)
        # Kemeny: gilt, solange das Optimum eindeutig ist (sonst entscheidet die Gleichstandsregel, siehe den Regressionstest unten)
        if len(optimal_orders(ranks)) == 1:
            assert A.kemeny(ranks2, tb2)[p].tolist() == A.kemeny(ranks, tb).tolist(), (n, m)


def test_kemeny_ties_between_several_optima_are_resolved_by_the_key_not_by_the_index():
    """Regressionstest (Befund 2026-10-17): Der frühere Gleichstandsterm 1e-9·(n−1−Rang)·|gesetzt| war nicht injektiv; bei mehreren optimalen Rangfolgen entschied der
    Kandidatenindex statt des Schlüssels (38 von 2000 Zufallsprofilen). Jetzt gewinnt unter den optimalen Rangfolgen die lexikographisch kleinste Folge der Schlüsselränge."""
    rng = np.random.default_rng(303)
    checked = 0
    for ranks, tb, n, m in instances(303, 400, n_choices=(3, 4, 5), m_choices=(1, 2, 3, 5, 7, 8)):
        p = rng.permutation(n)
        if len(optimal_orders(ranks)) == 1:
            continue
        checked += 1
        ranks2, tb2 = relabel(ranks, tb, p)
        assert A.kemeny(ranks2, tb2)[p].tolist() == A.kemeny(ranks, tb).tolist(), (n, m, ranks.tolist(), tb.tolist(), p.tolist())
    assert checked >= 20


# --- 4 Umkehren aller Eingaben ------------------------------------------------------------------------------------------------------------------

def test_reversing_all_inputs_reverses_the_borda_points():
    for ranks, tb, n, m in instances(404, 40):
        rev = n - 1 - ranks
        points = ranks.sum(axis=0)
        points_rev = rev.sum(axis=0)
        assert (points + points_rev == m * (n - 1)).all()
        got = A.borda(rev, tb)
        # ohne Punktgleichstand kehrt sich die Rangfolge genau um
        if len(set(points.tolist())) == n:
            assert got.tolist() == (n - 1 - A.borda(ranks, tb)).tolist()
        # mit negiertem Schlüssel gilt es immer
        assert A.borda(rev, -tb).tolist() == (n - 1 - A.borda(ranks, tb)).tolist()


def test_reversing_all_inputs_reverses_median_and_copeland_with_negated_key():
    for ranks, tb, n, m in instances(405, 40):
        rev = n - 1 - ranks
        for name in ("Median", "Copeland"):
            f = METHODS[name]
            assert f(rev, -tb).tolist() == (n - 1 - f(ranks, tb)).tolist(), (name, n, m)


def test_reversing_all_inputs_gives_an_optimal_kemeny_ranking_for_the_reversed_profile():
    for ranks, tb, n, m in instances(406, 25, n_choices=(3, 4, 5, 6)):
        rev = n - 1 - ranks
        got = A.kemeny(ranks, tb)
        order = tuple(np.argsort(got))
        reversed_order = order[::-1]
        opt = optimal_orders(rev)
        assert reversed_order in opt, (n, m)
        if len(opt) == 1:
            assert A.kemeny(rev, tb).tolist() == (n - 1 - got).tolist()


# --- 5 Pareto -----------------------------------------------------------------------------------------------------------------------------------

def test_pareto_if_all_raters_put_a_before_b_every_method_does():
    rng = np.random.default_rng(505)
    for _ in range(40):
        n = int(rng.integers(3, 7))
        m = int(rng.integers(1, 8))
        a, b = rng.choice(n, 2, replace=False)
        ranks, tb = random_profile(rng, m, n)
        for r in ranks:
            if r[a] > r[b]:
                r[a], r[b] = r[b], r[a]       # bleibt eine Permutation
        assert (ranks[:, a] < ranks[:, b]).all()
        for name, f in METHODS.items():
            res = f(ranks, tb)
            assert res[a] < res[b], (name, n, m, a, b)


# --- 6 Condorcet --------------------------------------------------------------------------------------------------------------------------------

def test_condorcet_winner_and_loser_for_copeland_kemeny_and_borda():
    rng = np.random.default_rng(606)
    n_winner = n_loser = 0
    for _ in range(300):
        n = int(rng.integers(3, 6))
        m = int(rng.choice([3, 5, 7]))
        ranks, tb = random_profile(rng, m, n)
        P = A.pref_matrix(ranks)
        winner = [i for i in range(n) if all(P[i, j] > P[j, i] for j in range(n) if j != i)]
        loser = [i for i in range(n) if all(P[i, j] < P[j, i] for j in range(n) if j != i)]
        if winner:
            n_winner += 1
            w = winner[0]
            assert A.copeland(ranks, tb)[w] == 0
            assert A.kemeny(ranks, tb)[w] == 0
        if loser:
            n_loser += 1
            lo = loser[0]
            assert A.copeland(ranks, tb)[lo] == n - 1
            assert A.kemeny(ranks, tb)[lo] == n - 1
            assert A.borda(ranks, tb)[lo] != 0
    assert n_winner >= 30 and n_loser >= 30          # die Prüfung ist nicht leer


# --- 7 Gewichte ---------------------------------------------------------------------------------------------------------------------------------

def test_weight_is_one_for_the_consensus_zero_for_its_reverse_and_falls_with_distance():
    rng = np.random.default_rng(707)
    for _ in range(40):
        n = int(rng.integers(3, 8))
        consensus = rng.permutation(n)
        group = [consensus, n - 1 - consensus] + [rng.permutation(n) for _ in range(5)]
        w = A.weights_by_agreement(group, consensus)
        assert w[0] == 1.0 and w[1] == 0.0
        assert ((w >= 0) & (w <= 1)).all()
        d = np.array([A.kendall(r, consensus) for r in group])
        for i, j in itertools.combinations(range(len(group)), 2):
            if d[i] < d[j]:
                assert w[i] >= w[j] and (w[j] == 0.0 or w[i] > w[j])      # ab dem halben größten Abstand ist das Gewicht auf 0 beschnitten
            elif d[i] == d[j]:
                assert w[i] == w[j]


def test_weighted_borda_is_invariant_to_scaling_all_weights_by_a_power_of_two():
    for ranks, tb, n, m in instances(708, 30):
        w = np.random.default_rng(n * 100 + m).random(m) + 0.1
        base = A.borda(ranks, tb, w)
        assert A.borda(ranks, tb, 4.0 * w).tolist() == base.tolist()
        assert A.borda(ranks, tb, 0.5 * w).tolist() == base.tolist()


def test_on_average_over_seeds_an_honest_rater_outweighs_a_random_rater():
    mid, rnd = [], []
    for seed in range(200000, 200030):
        inst = SC.build(8, 0, 9, 0, 4, 0, C.STRATEGIES[0], 5, seed)
        _c, w = A.weighted_borda(inst.ranks, inst.tb)
        types = np.array(inst.types)
        mid.append(w[types == "mittel"].mean())
        rnd.append(w[types == "Zufall"].mean())
    assert np.mean(mid) > np.mean(rnd) + 0.2
    assert sum(a > b for a, b in zip(mid, rnd)) >= 27


# --- 8 Kendall-Abstand --------------------------------------------------------------------------------------------------------------------------

def test_kendall_distance_is_a_metric_invariant_under_relabelling():
    rng = np.random.default_rng(808)
    for _ in range(40):
        n = int(rng.integers(2, 8))
        a, b, c = (rng.permutation(n) for _ in range(3))
        assert A.kendall(a, a) == 0
        assert A.kendall(a, b) == A.kendall(b, a)
        assert A.kendall(a, c) <= A.kendall(a, b) + A.kendall(b, c)
        assert A.kendall(a, n - 1 - a) == n * (n - 1) // 2
        p = rng.permutation(n)
        a2, b2 = np.empty_like(a), np.empty_like(b)
        a2[p], b2[p] = a, b
        assert A.kendall(a2, b2) == A.kendall(a, b)
        if A.kendall(a, b) == 0:
            assert a.tolist() == b.tolist()


def test_a_single_candidate_does_not_divide_by_zero():
    """Regressionstest (Befund 2026-10-17): weighted_borda teilte bei n = 1 durch null (außerhalb des Demo-Bereichs, aber eine Division durch null bleibt ein Fehler)."""
    ranks = np.zeros((3, 1), dtype=int)
    order, w = A.weighted_borda(ranks, np.zeros(1))
    assert order.tolist() == [0] and w.tolist() == [1.0, 1.0, 1.0]
