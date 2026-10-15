"""JEDE Zahl und Aussage aus App-Texten und README wird hier nachgerechnet (über die festen Instanzen SWEEP_SEEDS, 60 Läufe; nie ein einzelner Seed).
Der Generator hängt nur von Seed und Position ab (SplitMix64), die Zahlen sind plattformunabhängig bis auf Gleitkommarand; Schwellen daher mit Abstand zur Messung."""

import pytest

import bwt_constants as C
import bwt_evaluation as ev

UP, BURY, BOTH = C.STRATEGIES
BORDA, MEDIAN, COPE, KEM, WEIGHT = C.METHODS


@pytest.fixture(scope="module")
def e1():
    return ev.sweep_count()


@pytest.fixture(scope="module")
def e2():
    return ev.sweep_mix()


@pytest.fixture(scope="module")
def e3():
    return ev.sweep_random()


@pytest.fixture(scope="module")
def e4():
    return ev.sweep_manip()


def d(cell, m):
    return cell[m][0]


def win(cell, m):
    return cell[m][1]


def tgt(cell, m):
    return cell[m][2]


# --- Experiment 1: Zahl der Bewerter ----------------------------------------------------------------------------------------------------------

def test_more_raters_average_out_the_noise(e1):
    assert [d(e1[m], BORDA) for m in C.EXP_BAD_COUNTS] == pytest.approx([0.239, 0.133, 0.119, 0.070, 0.035, 0.011], abs=0.025)
    assert [win(e1[m], BORDA) for m in (1, 5, 15, 31)] == pytest.approx([0.433, 0.683, 0.783, 0.90], abs=0.10)
    ds = [d(e1[m], BORDA) for m in C.EXP_BAD_COUNTS]
    assert ds == sorted(ds, reverse=True)
    assert len({round(d(e1[1], m), 6) for m in C.METHODS}) == 1                      # ein einziger Bewerter: alle Verfahren gleich
    assert d(e1[31], COPE) == pytest.approx(0.021, abs=0.015) and d(e1[31], KEM) == pytest.approx(0.021, abs=0.015)
    assert d(e1[31], BORDA) <= d(e1[31], COPE) + 0.005                                 # bei gleichem Rauschen kein Vorteil für Copeland oder Kemeny


# --- Experiment 2: Mischung -------------------------------------------------------------------------------------------------------------------

def test_mixed_quality_hardly_matters_without_spam(e2):
    uniform, mixed, few = (e2[m] for m in C.EXP_MIXES)
    assert d(uniform, BORDA) == pytest.approx(0.032, abs=0.015) and d(mixed, BORDA) == pytest.approx(0.032, abs=0.015)
    assert d(few, BORDA) == pytest.approx(0.051, abs=0.02) and d(few, COPE) == pytest.approx(0.043, abs=0.02) and d(few, WEIGHT) == pytest.approx(0.046, abs=0.02)
    for cell in (uniform, mixed, few):
        assert max(d(cell, m) for m in C.METHODS) < 0.08


# --- Experiment 3: Zufall -----------------------------------------------------------------------------------------------------------------------

def test_random_raters_hurt_borda_most_and_the_weights_catch_them(e3):
    assert [d(e3[z], BORDA) for z in C.EXP_RANDOM_COUNTS] == pytest.approx([0.014, 0.054, 0.130, 0.234], abs=0.03)
    assert [d(e3[z], WEIGHT) for z in C.EXP_RANDOM_COUNTS] == pytest.approx([0.012, 0.030, 0.051, 0.131], abs=0.025)
    assert d(e3[8], COPE) == pytest.approx(0.085, abs=0.025) and d(e3[8], KEM) == pytest.approx(0.083, abs=0.025)
    for z in (4, 8, 11):
        assert d(e3[z], WEIGHT) < d(e3[z], BORDA) - 0.02
        assert d(e3[z], WEIGHT) <= min(d(e3[z], COPE), d(e3[z], KEM), d(e3[z], MEDIAN)) + 0.01
    assert win(e3[8], BORDA) == pytest.approx(0.583, abs=0.10) and win(e3[8], WEIGHT) == pytest.approx(0.80, abs=0.10)


# --- Experiment 4: Manipulation -------------------------------------------------------------------------------------------------------------------

def test_burying_the_best_is_what_hurts(e4):
    assert [win(e4[(BURY, c)], BORDA) for c in (2, 4, 6)] == pytest.approx([0.333, 0.0, 0.0], abs=0.10)
    assert [win(e4[(BURY, c)], COPE) for c in (2, 4, 6)] == pytest.approx([0.917, 0.667, 0.367], abs=0.10)
    assert [win(e4[(BURY, c)], MEDIAN) for c in (2, 4, 6)] == pytest.approx([0.833, 0.567, 0.30], abs=0.12)
    assert win(e4[(BURY, 2)], WEIGHT) == pytest.approx(0.733, abs=0.12) and win(e4[(BURY, 4)], WEIGHT) < 0.2
    for c in (2, 4):
        assert win(e4[(BURY, c)], COPE) > win(e4[(BURY, c)], BORDA) + 0.3
    assert win(e4[(BURY, 4)], WEIGHT) < win(e4[(BURY, 4)], COPE) - 0.4              # Gewichtung hilft nicht gegen Strategie


def test_pushing_the_target_up_changes_little_below_a_majority(e4):
    for c in (2, 4, 6):
        for m in C.METHODS:
            assert win(e4[(UP, c)], m) > 0.9 and tgt(e4[(UP, c)], m) < 0.05, (c, m)
    assert d(e4[(UP, 6)], BORDA) == pytest.approx(0.064, abs=0.025)


# --- Experiment 5: Mehrheit ---------------------------------------------------------------------------------------------------------------------

def test_a_majority_captures_the_majority_rules_but_not_borda(e4):
    cell = e4[(BOTH, 8)]
    assert [tgt(cell, m) for m in (MEDIAN, COPE, KEM)] == [1.0, 1.0, 1.0]
    assert tgt(cell, BORDA) < 0.1 and tgt(cell, WEIGHT) == pytest.approx(0.167, abs=0.12)
    assert tgt(e4[(BOTH, 6)], COPE) < 0.1 and tgt(e4[(BOTH, 4)], COPE) == 0.0
    assert all(win(cell, m) < 0.05 for m in C.METHODS)


# --- Verdikte nennen die Zahlen aus den Daten ---------------------------------------------------------------------------------------------------

def test_verdicts_quote_the_measured_numbers(e1, e2, e3, e4):
    t = ev.verdict_count(e1)[1]
    assert "1 Bewerter **0,239**" in t and "31 **0,011**" in t
    m = ev.verdict_mix(e2)[1]
    assert "Neun mittlere Bewerter: Abstand 0,032" in m
    r = ev.verdict_random(e3)[1]
    assert "Wenn 8 von 15 Bewertern raten" in r and "Borda bei **0,13" in r
    b = ev.verdict_bury(e4)[1]
    assert "nur noch bei **33 %** der Läufe beim Borda oben" in b
    mj = ev.verdict_majority(e4)[1]
    assert "Median 100 %, Copeland 100 %, Kemeny 100 %" in mj
