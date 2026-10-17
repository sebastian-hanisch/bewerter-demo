"""Analyse des gezeigten Panels, fünf Experimente über die festen Läufe (SWEEP_SEEDS) und die Verdikte.

Fünf Verfahren fassen die Rangfolgen der Bewerter zusammen (Borda, Median, Copeland, Kemeny, gewichtetes Borda). Maße: normierte Kendall-Distanz zur Wahrheit (Anteil falsch geordneter
Paare), Sieger richtig (der wahre Beste steht oben) und Ziel gewinnt (das Ziel der Manipulatoren steht oben)."""

import functools
import math
from dataclasses import dataclass

import numpy as np

import bwt_aggregate as A
import bwt_constants as C
import bwt_scenario as SC
from bwt_scenario import Settings

NAN = float("nan")
STRATEGY_UP, STRATEGY_BURY, STRATEGY_BOTH = C.STRATEGIES


def de(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x: float, digits: int = 0) -> str:
    return de(100 * x, digits)


def _mean(values) -> float:
    v = [x for x in values if not (isinstance(x, float) and math.isnan(x))]
    return float(sum(v) / len(v)) if v else NAN


def max_distance(n: int) -> float:
    return n * (n - 1) / 2.0


# --- Ein Panel --------------------------------------------------------------------------------------------------------------------------------

def measure(inst: SC.Instance) -> dict:
    """Je Verfahren: (normierter Abstand zur Wahrheit, Sieger richtig, Ziel gewinnt)."""
    n = len(inst.strengths)
    truth = np.arange(n)
    out = {}
    for name, rank in A.aggregate_all(inst.ranks, inst.tb).items():
        out[name] = (A.kendall(rank, truth) / max_distance(n), float(rank[inst.best] == 0), float(rank[inst.target] == 0))
    return out


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    instance: SC.Instance
    rater_distance: np.ndarray      # normierter Abstand je Bewerter zur Wahrheit
    weights: np.ndarray             # Gewicht je Bewerter im gewichteten Borda
    consensus: dict                 # Verfahren -> Rangfolge
    metrics: dict                   # Verfahren -> (Abstand, Sieger richtig, Ziel gewinnt)
    manipulators: int


def analyse(s: Settings) -> Analysis:
    inst = SC.simulate(s)
    n = s.n
    truth = np.arange(n)
    dist = np.array([A.kendall(r, truth) / max_distance(n) for r in inst.ranks]) if len(inst.ranks) else np.zeros(0)
    _, w = A.weighted_borda(inst.ranks, inst.tb) if len(inst.ranks) else (None, np.zeros(0))
    cons = A.aggregate_all(inst.ranks, inst.tb) if len(inst.ranks) else {}
    return Analysis(s, inst, dist, w, cons, measure(inst) if len(inst.ranks) else {}, s.n_manip)


def total_raters(s: Settings) -> int:
    return s.n_good + s.n_mid + s.n_bad + s.n_rand + s.n_manip


def verdict_analysis(a: Analysis):
    s = a.settings
    if not a.metrics:
        return "warning", "Es gibt keinen Bewerter: Bitte mindestens einen Bewerter einstellen."
    best = min(C.METHODS, key=lambda k: a.metrics[k][0])
    text = (f"Abstand zur Wahrheit (Anteil falsch geordneter Paare) bei {total_raters(s)} Bewertern: " + ", ".join(f"{k} {de(a.metrics[k][0], 3)}" for k in C.METHODS) +
            f"; am nächsten **{best}**. Sieger richtig: " + ", ".join(f"{k} {de(a.metrics[k][1], 0)}" for k in C.METHODS) + ".")
    if s.n_manip:
        wins = [k for k in C.METHODS if a.metrics[k][2] == 1.0]
        text += f" Das Ziel gewinnt bei: {', '.join(wins) if wins else 'keinem Verfahren'}."
    return "info", text


# --- Feste Läufe der Experimente --------------------------------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=8192)
def _measure(n, n_good, n_mid, n_bad, n_rand, n_manip, strategy, target_rank, seed):
    return measure(SC.build(n, n_good, n_mid, n_bad, n_rand, n_manip, strategy, target_rank, seed))


def cell(n_good=0, n_mid=0, n_bad=0, n_rand=0, n_manip=0, strategy=STRATEGY_BOTH, target_rank=C.DEFAULT_TARGET, n=C.EXP_N) -> dict:
    """Mittel je Verfahren über die festen Läufe: {Verfahren: (Abstand, Sieger richtig, Ziel gewinnt)}."""
    res = [_measure(n, n_good, n_mid, n_bad, n_rand, n_manip, strategy, target_rank, sd) for sd in C.SWEEP_SEEDS]
    return {m: tuple(_mean([r[m][i] for r in res]) for i in range(3)) for m in C.METHODS}


def sweep_count() -> dict:
    """Experiment 1: wie viele schlechte Bewerter (ein Spiel je Paar)?"""
    return {m: cell(n_bad=m) for m in C.EXP_BAD_COUNTS}


def sweep_mix() -> dict:
    """Experiment 2: gemischte Qualität (gute, mittlere, schlechte)."""
    return {mix: cell(n_good=mix[0], n_mid=mix[1], n_bad=mix[2]) for mix in C.EXP_MIXES}


def sweep_random() -> dict:
    """Experiment 3: z von 15 Bewertern raten."""
    return {z: cell(n_mid=C.EXP_PANEL - z, n_rand=z) for z in C.EXP_RANDOM_COUNTS}


def sweep_manip() -> dict:
    """Experimente 4 und 5: c von 15 Bewertern manipulieren, nach Strategie."""
    return {(st, c): cell(n_mid=C.EXP_PANEL - c, n_manip=c, strategy=st) for st in C.STRATEGIES for c in C.EXP_MANIP_COUNTS}


# --- Verdikte ---------------------------------------------------------------------------------------------------------------------------------

def verdict_count(e1):
    first, five, fifteen, last = (e1[m] for m in (1, 5, 15, 31))
    return "info", (f"Schlechte Bewerter (ein Spiel je Paar), Abstand beim Borda: 1 Bewerter **{de(first['Borda'][0], 3)}**, 5 {de(five['Borda'][0], 3)}, 15 {de(fifteen['Borda'][0], 3)}, "
                    f"31 **{de(last['Borda'][0], 3)}**; Sieger richtig {de(first['Borda'][1])} → {de(last['Borda'][1])}. Mehr Bewerter mitteln das Rauschen. Bei gleich "
                    f"gutem Rauschen hat Borda nichts gegen Copeland ({de(last['Copeland'][0], 3)}) und Kemeny ({de(last['Kemeny'][0], 3)}) zu fürchten.")


def verdict_mix(e2):
    uniform, mixed, few = (e2[m] for m in C.EXP_MIXES)
    return "info", (f"Neun mittlere Bewerter: Abstand {de(uniform['Borda'][0], 3)} (Borda). Drei gute, drei mittlere, drei schlechte: {de(mixed['Borda'][0], 3)}; zwei gute und sieben "
                    f"schlechte: Borda {de(few['Borda'][0], 3)}, Copeland {de(few['Copeland'][0], 3)}, gewichtet {de(few['Borda gewichtet'][0], 3)}. Die Unterschiede sind klein: "
                    "Wenige gute Bewerter gehen im Rauschen der vielen schlechten unter, solange ehrlich geurteilt wird.")


def verdict_random(e3):
    half = e3[8]
    return "warning", (f"Wenn 8 von 15 Bewertern raten, liegt der Abstand beim Borda bei **{de(half['Borda'][0], 3)}**, beim gewichteten Borda bei **{de(half['Borda gewichtet'][0], 3)}**, "
                       f"bei Copeland {de(half['Copeland'][0], 3)}; Sieger richtig {de(half['Borda'][1])} gegen {de(half['Borda gewichtet'][1])}. Das Gewicht (Übereinstimmung mit dem "
                       "Konsens) erkennt Zufall, weil Zufall mit niemandem übereinstimmt.")


def verdict_bury(e4):
    c2, c4 = e4[(STRATEGY_BURY, 2)], e4[(STRATEGY_BURY, 4)]
    up6 = e4[(STRATEGY_UP, 6)]
    return "warning", (f"Setzen 2 von 15 den wahren Besten ans Ende, steht er nur noch bei **{pct(c2['Borda'][1])} %** der Läufe beim Borda oben (Copeland {pct(c2['Copeland'][1])} %, Kemeny "
                       f"{pct(c2['Kemeny'][1])} %, gewichtet {pct(c2['Borda gewichtet'][1])} %); bei 4 von 15: Borda {pct(c4['Borda'][1])} %, Copeland {pct(c4['Copeland'][1])} %, gewichtet "
                       f"{pct(c4['Borda gewichtet'][1])} %. Das bloße Hochsetzen des Ziels wirkt kaum (6 von 15: Sieger richtig {pct(up6['Borda'][1])} %, Ziel gewinnt {pct(up6['Borda'][2])} %).")


def verdict_majority(e4):
    r = {m: e4[(STRATEGY_BOTH, 8)][m][2] for m in C.METHODS}
    return "warning", ("Mit 8 von 15 (Mehrheit) steht das Ziel in diesen Anteilen der Läufe oben: " + ", ".join(f"{m} {pct(r[m])} %" for m in C.METHODS) +
                       ". Eine Mehrheit steuert Median, Copeland und Kemeny vollständig; Borda hält sich besser, weil das Ziel bei den ehrlichen Bewertern schlecht liegt. "
                       "Kein Verfahren ist gegen jede Art Angriff robust: für Manipulation sagt das der Satz von Gibbard und Satterthwaite, für faire Aggregation überhaupt Arrows Unmöglichkeitssatz.")
