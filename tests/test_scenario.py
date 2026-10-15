"""Simulation der Bewerter: Wahrheit, ehrliche Rangfolgen, Zufall, Manipulation, Reihenfolge und Ströme."""

import numpy as np
import pytest

import bwt_constants as C
import bwt_scenario as SC
import turnier_generator as T

BURY = C.STRATEGIES[1]


def test_strengths_are_equally_spaced_and_descending():
    s = SC.strengths_for(6)
    assert s == pytest.approx(0.3 * np.array([2.5, 1.5, 0.5, -0.5, -1.5, -2.5]))
    assert abs(s.mean()) < 1e-12


def test_honest_ranking_is_a_permutation_and_better_with_more_games():
    s = SC.strengths_for(8)
    truth = np.arange(8)
    few, many = [], []
    for sd in range(40):
        few.append(np.sum(np.sign(np.subtract.outer(SC.honest_ranking(s, 1, T.SplitMix64(sd)), truth)) != 0) - 8)
        r = SC.honest_ranking(s, 16, T.SplitMix64(sd))
        assert sorted(r.tolist()) == list(range(8))
        many.append(np.mean([r[i] < r[j] for i in range(8) for j in range(i + 1, 8)]))
    assert np.mean(many) > 0.9                                                    # 16 Partien je Paar: fast die Wahrheit
    mid = np.mean([np.mean([SC.honest_ranking(s, 1, T.SplitMix64(sd))[i] < SC.honest_ranking(s, 1, T.SplitMix64(sd))[j] for i in range(8) for j in range(i + 1, 8)]) for sd in range(40)])
    assert mid < np.mean(many) and mid > 0.6


def test_honest_ranking_by_hand_for_two_clear_players():
    s = np.array([5.0, -5.0])                                                       # praktisch sicher: Spieler 0 gewinnt alle Partien
    assert SC.honest_ranking(s, 4, T.SplitMix64(1)).tolist() == [0, 1]


def test_spam_is_a_permutation_and_has_no_trend():
    ranks = np.array([SC.spam_ranking(8, T.SplitMix64(sd)) for sd in range(400)])
    assert all(sorted(r.tolist()) == list(range(8)) for r in ranks[:20])
    assert ranks.mean(axis=0) == pytest.approx([3.5] * 8, abs=0.5)


def test_manipulate_by_hand():
    base = SC.honest_ranking(SC.strengths_for(6), 16, T.SplitMix64(3))
    order = list(np.argsort(base))
    up = SC.manipulate(base, 3, 0, C.STRATEGIES[0])
    assert up[3] == 0 and sorted(up.tolist()) == list(range(6))
    bury = SC.manipulate(base, 3, 0, BURY)
    assert bury[0] == 5 and bury[3] == base[3] - (1 if base[3] > base[0] else 0)
    both = SC.manipulate(base, 3, 0, C.STRATEGIES[2])
    assert both[3] == 0 and both[0] == 5
    ident = SC.manipulate(np.array([0, 1, 2]), 0, 2, C.STRATEGIES[2])              # Ziel schon vorn, Bester schon hinten: unverändert
    assert ident.tolist() == [0, 1, 2]


def test_build_orders_the_raters_by_type_and_is_deterministic():
    inst = SC.build(8, 1, 2, 3, 2, 1, C.STRATEGIES[2], 5, 9)
    assert inst.types == ("gut", "mittel", "mittel", "schlecht", "schlecht", "schlecht", "Zufall", "Zufall", "Manipulator")
    assert inst.ranks.shape == (9, 8) and inst.target == 4 and inst.best == 0
    assert inst.ranks[-1][4] == 0 and inst.ranks[-1][0] == 7                         # der Manipulator: Ziel vorn, Bester hinten
    again = SC.build(8, 1, 2, 3, 2, 1, C.STRATEGIES[2], 5, 9)
    assert np.array_equal(inst.ranks, again.ranks) and np.array_equal(inst.tb, again.tb)
    assert not np.array_equal(inst.ranks, SC.build(8, 1, 2, 3, 2, 1, C.STRATEGIES[2], 5, 10).ranks)


def test_rater_streams_depend_only_on_seed_and_position():
    a = SC.build(8, 0, 4, 0, 0, 0, C.STRATEGIES[0], 5, 2)
    b = SC.build(8, 0, 6, 0, 0, 0, C.STRATEGIES[0], 5, 2)
    assert np.array_equal(a.ranks, b.ranks[:4])                                      # die ersten Bewerter bleiben dieselben
    assert np.array_equal(a.tb, b.tb)


def test_target_rank_is_clamped_to_the_field():
    inst = SC.build(4, 0, 3, 0, 0, 0, C.STRATEGIES[0], 8, 1)
    assert inst.target == 3
    assert SC.build(4, 0, 3, 0, 0, 0, C.STRATEGIES[0], 1, 1).target == 1


def test_no_raters_gives_an_empty_panel():
    inst = SC.build(5, 0, 0, 0, 0, 0, C.STRATEGIES[0], 3, 1)
    assert inst.ranks.shape == (0, 5)
