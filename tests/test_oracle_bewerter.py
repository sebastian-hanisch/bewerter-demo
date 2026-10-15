"""Orakel: Aggregation gegen Aufzählen und scipy, Eigenschaften der Verfahren über feste Läufe."""

import itertools

import numpy as np
import pytest

import bwt_aggregate as A
import bwt_constants as C
import bwt_evaluation as ev
import bwt_scenario as SC


def test_kendall_equals_scipy_discordant_pairs():
    stats = pytest.importorskip("scipy.stats")
    rng = np.random.default_rng(1)
    for _ in range(15):
        a, b = rng.permutation(7), rng.permutation(7)
        tau = stats.kendalltau(a, b).statistic
        assert A.kendall(a, b) == pytest.approx((1 - tau) * 21 / 2)


def test_borda_equals_a_scalar_enumeration():
    rng = np.random.default_rng(2)
    tb = np.arange(6) * 0.01
    for _ in range(10):
        ranks = [rng.permutation(6) for _ in range(5)]
        scores = [sum(r[i] for r in ranks) for i in range(6)]
        order = sorted(range(6), key=lambda i: (scores[i], tb[i]))
        assert A.borda(ranks, tb).tolist() == A.order_to_rank(order).tolist()


def test_copeland_equals_a_scalar_enumeration():
    rng = np.random.default_rng(4)
    tb = np.arange(6) * 0.01
    for _ in range(10):
        ranks = [rng.permutation(6) for _ in range(5)]
        pts = []
        for i in range(6):
            p = 0.0
            for j in range(6):
                if i == j:
                    continue
                pij = sum(1 for r in ranks if r[i] < r[j])
                pji = sum(1 for r in ranks if r[j] < r[i])
                p += 1.0 if pij > pji else (0.5 if pij == pji else 0.0)
            pts.append(p)
        order = sorted(range(6), key=lambda i: (-pts[i], tb[i]))
        assert A.copeland(ranks, tb).tolist() == A.order_to_rank(order).tolist()


def test_kemeny_cost_is_minimal_on_random_profiles_up_to_six():
    rng = np.random.default_rng(5)
    for _ in range(6):
        n = 6
        ranks = [rng.permutation(n) for _ in range(7)]
        best = min(sum(A.kendall(A.order_to_rank(p), r) for r in ranks) for p in itertools.permutations(range(n)))
        got = A.kemeny(ranks, np.arange(n) * 0.01)
        assert sum(A.kendall(got, r) for r in ranks) == best


def test_without_noise_every_method_returns_the_truth():
    inst = SC.build(6, 5, 0, 0, 0, 0, C.STRATEGIES[0], 3, 1)
    # gute Bewerter (16 Partien je Paar) sind fast, aber nicht ganz fehlerfrei: nur sehr starke Unterschiede sind sicher
    s = np.array([5.0, 3.0, 1.0, -1.0, -3.0, -5.0])
    ranks = [SC.honest_ranking(s, 16, SC.T.SplitMix64(sd)) for sd in range(9)]
    out = A.aggregate_all(ranks, inst.tb)
    for m in C.METHODS:
        assert out[m].tolist() == [0, 1, 2, 3, 4, 5], m


def test_random_raters_get_small_weights_and_a_perfect_rater_the_largest():
    s = SC.strengths_for(8)
    honest = [SC.honest_ranking(s, 16, SC.T.SplitMix64(sd)) for sd in range(8)]
    spam = [SC.spam_ranking(8, SC.T.SplitMix64(100 + sd)) for sd in range(4)]
    _cons, w = A.weighted_borda(honest + spam, np.arange(8) * 0.01)
    assert np.mean(w[:8]) > 0.8 and np.mean(w[8:]) < 0.35
    assert max(w[:8]) >= max(w[8:])


def test_more_raters_lower_the_average_distance():
    d = [np.mean([ev.measure(SC.build(8, 0, 0, m, 0, 0, C.STRATEGIES[0], 5, sd))["Borda"][0] for sd in range(40)]) for m in (1, 5, 21)]
    assert d[0] > d[1] > d[2]


def test_a_manipulating_majority_makes_the_target_the_copeland_winner():
    wins = 0
    for sd in range(20):
        m = ev.measure(SC.build(8, 0, 7, 0, 0, 8, C.STRATEGIES[2], 5, sd))
        wins += int(m["Copeland"][2] == 1.0)
    assert wins == 20


def test_a_small_manipulating_minority_cannot_make_the_target_win_but_can_bury_the_best():
    tgt, best = [], []
    for sd in range(40):
        m = ev.measure(SC.build(8, 0, 13, 0, 0, 2, C.STRATEGIES[2], 5, sd))
        tgt.append(m["Borda"][2])
        best.append(m["Borda"][1])
    assert np.mean(tgt) < 0.05 and np.mean(best) < 0.7
