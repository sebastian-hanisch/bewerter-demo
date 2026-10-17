"""Analyse des gezeigten Panels, Verdikt-Zweige an handgesetzten Werten; die Experimente selbst prüft test_claims.py."""

import numpy as np
import pytest

import bwt_constants as C
import bwt_evaluation as ev
import bwt_scenario as SC
from bwt_scenario import Settings

UP, BURY, BOTH = C.STRATEGIES


def test_formatting_and_helpers():
    assert ev.de(1.5, 1) == "1,5" and ev.de(0.666) == "0,67" and ev.pct(0.256) == "26" and ev.pct(0.256, 1) == "25,6"
    assert ev._mean([1.0, float("nan"), 3.0]) == 2.0 and np.isnan(ev._mean([float("nan")]))
    assert ev.max_distance(8) == 28.0 and ev.max_distance(4) == 6.0
    assert ev.total_raters(Settings(n_good=1, n_mid=2, n_bad=3, n_rand=4, n_manip=5)) == 15


def test_measure_by_hand_for_perfect_and_reversed_panels():
    n = 4
    s = SC.strengths_for(n)
    perfect = SC.Instance(s, ("gut",) * 3, np.array([np.arange(n)] * 3), np.arange(n) * 0.1, 2, 0)
    m = ev.measure(perfect)
    assert all(v == (0.0, 1.0, 0.0) for v in m.values()) and set(m) == set(C.METHODS)
    reversed_ = SC.Instance(s, ("Manipulator",) * 3, np.array([np.arange(n)[::-1]] * 3), np.arange(n) * 0.1, 3, 0)
    m2 = ev.measure(reversed_)
    assert all(v == (1.0, 0.0, 1.0) for v in m2.values())                              # das Ziel (Index 3) steht oben


def test_analysis_is_consistent_and_deterministic():
    s = Settings(n=6, n_mid=5, n_rand=2, n_manip=1, seed=4)
    a = ev.analyse(s)
    assert len(a.rater_distance) == 8 and len(a.weights) == 8 and set(a.metrics) == set(C.METHODS) == set(a.consensus)
    assert (0 <= a.rater_distance).all() and (a.rater_distance <= 1).all() and (0 <= a.weights).all() and (a.weights <= 1).all()
    for m, rank in a.consensus.items():
        assert sorted(rank.tolist()) == list(range(6))
        assert a.metrics[m][0] == pytest.approx(ev.A.kendall(rank, np.arange(6)) / 15)
    b = ev.analyse(s)
    assert a.metrics == b.metrics and np.array_equal(a.weights, b.weights)


def test_empty_panel_is_reported_not_computed():
    a = ev.analyse(Settings(n_mid=0))
    assert a.metrics == {} and len(a.rater_distance) == 0
    level, text = ev.verdict_analysis(a)
    assert level == "warning" and "keinen Bewerter" in text


def test_analysis_verdict_branches():
    a = ev.analyse(Settings(n_mid=9, seed=3))
    level, text = ev.verdict_analysis(a)
    assert level == "info" and "bei 9 Bewertern" in text and "am nächsten **" in text and "Ziel gewinnt" not in text
    b = ev.analyse(Settings(n_mid=7, n_manip=8, seed=3))
    text2 = ev.verdict_analysis(b)[1]
    assert "bei 15 Bewertern" in text2 and "Das Ziel gewinnt bei:" in text2


# --- Verdikt-Zweige ---------------------------------------------------------------------------------------------------------------------------

def _cell(abstand=0.1, winner=0.5, target=0.0, **per_method):
    out = {m: (abstand, winner, target) for m in C.METHODS}
    for m, v in per_method.items():
        out[m.replace("_", " ")] = v
    return out


def test_count_verdict_quotes_the_numbers():
    e1 = {1: _cell(0.239, 0.433), 5: _cell(0.119, 0.68), 15: _cell(0.035, 0.78), 31: _cell(0.011, 0.9, Copeland=(0.021, 0.93, 0), Kemeny=(0.022, 0.93, 0))}
    t = ev.verdict_count(e1)[1]
    assert "1 Bewerter **0,239**, 5 0,119, 15 0,035, 31 **0,011**" in t and "Sieger richtig 0,43 → 0,90" in t and "Copeland (0,021) und Kemeny (0,022)" in t


def test_mix_verdict_quotes_the_numbers():
    e2 = {C.EXP_MIXES[0]: _cell(0.032), C.EXP_MIXES[1]: _cell(0.0316), C.EXP_MIXES[2]: _cell(0.05, Borda=(0.051, 0.8, 0), Copeland=(0.043, 0.8, 0), Borda_gewichtet=(0.046, 0.8, 0))}
    t = ev.verdict_mix(e2)[1]
    assert "Borda 0,051, Copeland 0,043, gewichtet 0,046" in t and "Neun mittlere Bewerter: Abstand 0,032" in t and "Drei gute, drei mittlere, drei schlechte: 0,032" in t


def test_random_verdict_quotes_the_numbers():
    e3 = {8: _cell(0.1, 0.5, Borda=(0.130, 0.583, 0), Borda_gewichtet=(0.051, 0.8, 0), Copeland=(0.085, 0.72, 0))}
    t = ev.verdict_random(e3)[1]
    assert "Borda bei **0,130**" in t and "gewichteten Borda bei **0,051**" in t and "Copeland 0,085" in t and "Sieger richtig 0,58 gegen 0,80" in t


def test_bury_verdict_quotes_the_numbers():
    e4 = {(BURY, 2): _cell(0.1, 0.5, Borda=(0.1, 0.333, 0), Copeland=(0.1, 0.917, 0), Kemeny=(0.1, 0.917, 0), Borda_gewichtet=(0.1, 0.733, 0)),
          (BURY, 4): _cell(0.1, 0.5, Borda=(0.1, 0.0, 0), Copeland=(0.1, 0.667, 0), Borda_gewichtet=(0.1, 0.067, 0)),
          (UP, 6): _cell(0.1, 0.5, Borda=(0.064, 0.967, 0.0))}
    t = ev.verdict_bury(e4)[1]
    assert "nur noch bei **33 %** der Läufe beim Borda oben (Copeland 92 %, Kemeny 92 %, gewichtet 73 %)" in t
    assert "bei 4 von 15: Borda 0 %, Copeland 67 %, gewichtet 7 %" in t and "Sieger richtig 97 %, Ziel gewinnt 0 %" in t


def test_majority_verdict_quotes_the_numbers():
    e4 = {(BOTH, 8): _cell(0.2, 0.0, Borda=(0.2, 0.0, 0.033), Median=(0.3, 0, 1.0), Copeland=(0.3, 0, 1.0), Kemeny=(0.3, 0, 1.0), Borda_gewichtet=(0.2, 0, 0.167))}
    t = ev.verdict_majority(e4)[1]
    assert "Borda 3 %, Median 100 %, Copeland 100 %, Kemeny 100 %, Borda gewichtet 17 %" in t and "für Manipulation sagt das der Satz von Gibbard und Satterthwaite, für faire Aggregation überhaupt Arrows Unmöglichkeitssatz" in t


def test_analysis_verdict_names_the_nearest_method_and_the_methods_the_target_wins():
    from types import SimpleNamespace
    metrics = {"Borda": (0.20, 1.0, 0.0), "Median": (0.30, 0.0, 1.0), "Copeland": (0.05, 1.0, 0.0), "Kemeny": (0.10, 0.0, 1.0), "Borda gewichtet": (0.15, 1.0, 0.0)}
    a = SimpleNamespace(settings=Settings(n_mid=7, n_manip=8), metrics=metrics)
    t = ev.verdict_analysis(a)[1]
    assert "am nächsten **Copeland**" in t and "Das Ziel gewinnt bei: Median, Kemeny." in t
    none = {m: (0.1, 1.0, 0.0) for m in C.METHODS}
    t2 = ev.verdict_analysis(SimpleNamespace(settings=Settings(n_mid=7, n_manip=2), metrics=none))[1]
    assert "Das Ziel gewinnt bei: keinem Verfahren." in t2
    assert "Das Ziel gewinnt" not in ev.verdict_analysis(SimpleNamespace(settings=Settings(n_mid=7), metrics=none))[1]
