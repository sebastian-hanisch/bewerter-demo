"""Borda, Median, Copeland, Kemeny und gewichtetes Borda an Handwerten; Kendall-Abstand."""

import itertools

import numpy as np
import pytest

import bwt_aggregate as A
import bwt_constants as C

TB = np.arange(4) * 0.1                      # fester Gleichstandsschlüssel: kleinerer Index gewinnt


def R(order):
    """Platzziffern aus einer Reihenfolge der Teilnehmer (bester zuerst)."""
    return A.order_to_rank(order)


def test_kendall_by_hand():
    assert A.kendall(R([0, 1, 2, 3]), R([0, 1, 2, 3])) == 0
    assert A.kendall(R([0, 1, 2, 3]), R([3, 2, 1, 0])) == 6
    assert A.kendall(R([0, 1, 2, 3]), R([1, 0, 2, 3])) == 1
    assert A.kendall(R([0, 1, 2, 3]), R([0, 2, 3, 1])) == 2


def test_borda_by_hand_and_ties_follow_the_key():
    ranks = [R([0, 1, 2, 3]), R([0, 2, 1, 3]), R([1, 0, 2, 3])]
    # Platzsummen: 0 -> 0+0+1 = 1, 1 -> 1+2+0 = 3, 2 -> 2+1+2 = 5, 3 -> 9
    assert A.borda(ranks, TB).tolist() == [0, 1, 2, 3]
    tie = [R([0, 1, 2, 3]), R([1, 0, 2, 3])]                                     # 0 und 1 gleich: Schlüssel entscheidet
    assert A.borda(tie, TB).tolist() == [0, 1, 2, 3]
    assert A.borda(tie, np.array([0.5, 0.1, 0.2, 0.3])).tolist() == [1, 0, 2, 3]


def test_borda_with_weights_by_hand():
    ranks = [R([0, 1, 2, 3]), R([3, 2, 1, 0])]
    assert A.borda(ranks, TB, np.array([3.0, 1.0])).tolist() == [0, 1, 2, 3]
    assert A.borda(ranks, TB, np.array([1.0, 3.0])).tolist() == [3, 2, 1, 0]


def test_median_by_hand():
    ranks = [R([0, 1, 2, 3]), R([0, 1, 2, 3]), R([3, 2, 1, 0])]
    assert A.median_rank(ranks, TB).tolist() == [0, 1, 2, 3]                    # Median-Plätze (0,1,2,3): zwei von drei Bewertern


def test_copeland_and_the_condorcet_cycle_by_hand():
    cyc = [R([0, 1, 2]), R([1, 2, 0]), R([2, 0, 1])]
    P = A.pref_matrix(cyc)
    assert P.tolist() == [[0, 2, 1], [1, 0, 2], [2, 1, 0]]
    assert A.copeland(cyc, np.array([0.1, 0.2, 0.3])).tolist() == [0, 1, 2]       # alle gleich: Schlüssel
    pos = [R([0, 1, 2, 3]), R([0, 1, 2, 3]), R([1, 0, 2, 3])]
    assert A.copeland(pos, TB).tolist() == [0, 1, 2, 3]


def test_kemeny_equals_enumeration_on_random_profiles():
    rng = np.random.default_rng(3)
    for _ in range(10):
        n = 5
        ranks = [rng.permutation(n) for _ in range(5)]
        best_cost, best = None, None
        for perm in itertools.permutations(range(n)):
            r = A.order_to_rank(perm)
            cost = sum(A.kendall(r, x) for x in ranks)
            if best_cost is None or cost < best_cost:
                best_cost, best = cost, r
        got = A.kemeny(ranks, np.arange(n) * 0.01)
        assert sum(A.kendall(got, x) for x in ranks) == best_cost


def test_kemeny_breaks_ties_by_the_key():
    ranks = [R([0, 1, 2]), R([1, 0, 2])]                                         # 0 und 1: gleich viele Stimmen
    assert A.kemeny(ranks, np.array([0.1, 0.2, 0.3])).tolist() == [0, 1, 2]
    assert A.kemeny(ranks, np.array([0.2, 0.1, 0.3])).tolist() == [1, 0, 2]


def test_weights_by_agreement_by_hand():
    cons = R([0, 1, 2, 3])
    w = A.weights_by_agreement([R([0, 1, 2, 3]), R([3, 2, 1, 0]), R([1, 0, 2, 3])], cons)
    assert w[0] == 1.0 and w[1] == 0.0 and w[2] == pytest.approx(1 - 2 / 6)
    random_like = A.weights_by_agreement([R([0, 2, 1, 3, 4, 5]) ], R([0, 1, 2, 3, 4, 5]))
    assert random_like[0] == pytest.approx(1 - 2 / 15)


def test_weighted_borda_downweights_a_spammer_and_returns_weights():
    good = [R([0, 1, 2, 3, 4])] * 3 + [R([0, 2, 1, 3, 4])]
    spam = [R([4, 3, 2, 1, 0])]
    cons, w = A.weighted_borda(good + spam, np.arange(5) * 0.01)
    assert cons.tolist() == [0, 1, 2, 3, 4] and w[-1] == 0.0 and (w[:3] == 1.0).all() and 0.0 < w[3] < 1.0


def test_aggregate_all_returns_every_method_as_a_permutation():
    rng = np.random.default_rng(1)
    ranks = [rng.permutation(5) for _ in range(7)]
    out = A.aggregate_all(ranks, np.arange(5) * 0.01)
    assert set(out) == set(C.METHODS)
    for r in out.values():
        assert sorted(r.tolist()) == [0, 1, 2, 3, 4]


def test_kemeny_can_put_the_highest_index_first():
    ranks = [R([3, 2, 1, 0])] * 3
    assert A.kemeny(ranks, TB).tolist() == [3, 2, 1, 0]                               # Platzziffern: Teilnehmer 3 ist der Beste
    ranks5 = [R([4, 0, 3, 1, 2])] * 2
    assert A.kemeny(ranks5, np.arange(5) * 0.1).tolist() == R([4, 0, 3, 1, 2]).tolist()


def test_copeland_gives_half_a_point_for_a_tie():
    ranks = [np.array([0, 2, 3, 1]), np.array([0, 3, 1, 2])]
    # P: 0 schlägt alle (2 Punkte + ... ), 1/2/3 stehen paarweise 1 : 1; Punkte nur mit halbem Punkt je Gleichstand: 0: 3, 1..3: 1,0 + 0,5 ·2 = 1
    P = A.pref_matrix(ranks)
    assert P[1, 2] == P[2, 1] == 1 and P[0, 1] == 2
    assert A.copeland(ranks, np.arange(4) * 0.1).tolist() == [0, 3, 2, 1]               # Gleichstände: Schlüssel, aber in anderer Reihenfolge als bei anderen Gewichten


def test_median_breaks_a_tied_median_by_the_mean():
    ranks = [np.array([1, 2, 3, 0]), np.array([1, 3, 2, 0]), np.array([0, 2, 3, 1]), np.array([0, 1, 2, 3])]
    assert A.median_rank(ranks, np.arange(4) * 0.1).tolist() == [0, 2, 3, 1]


def test_weighted_borda_runs_the_requested_number_of_rounds():
    ranks = [np.array(r) for r in ([2, 5, 3, 4, 0, 1], [0, 5, 4, 3, 2, 1], [4, 0, 1, 2, 3, 5], [0, 3, 1, 5, 4, 2], [5, 2, 3, 0, 4, 1], [3, 1, 0, 4, 5, 2], [1, 0, 4, 2, 5, 3])]
    tb = np.arange(6) * 0.01
    assert A.weighted_borda(ranks, tb, rounds=2)[0].tolist() == [0, 1, 2, 4, 5, 3]
    assert A.weighted_borda(ranks, tb, rounds=3)[0].tolist() == [1, 0, 2, 4, 5, 3]
    assert A.weighted_borda(ranks, tb)[0].tolist() == [1, 0, 2, 4, 5, 3]                # Standard: drei Runden


def test_weighted_borda_falls_back_to_equal_weights_when_nobody_agrees():
    ranks = [np.array([2, 0, 3, 1]), np.array([1, 3, 0, 2])]
    tb = np.arange(4) * 0.1
    cons = A.borda(ranks, tb)
    assert A.weights_by_agreement(ranks, cons).sum() == 0.0
    out, w = A.weighted_borda(ranks, tb)
    assert w.tolist() == [1.0, 1.0]
    assert out.tolist() == A.borda(ranks, tb).tolist()
