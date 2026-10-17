"""Literatur-Referenzwerte für die Aggregation der Bewerter (ORACLE-PLAYBOOK §5.1).

Alle Werte stammen aus Quellen, die am 2026-10-17 tatsächlich abgerufen wurden (WebFetch, englischsprachige Wikipedia, jeweils der Artikel
zur Methode; Sekundärquelle, die Zahlen sind aber ein Lehrbuchbeispiel und rechnerisch nachvollziehbar):

(a) Kendall-Tau-Abstand, https://en.wikipedia.org/wiki/Kendall_tau_distance, Abschnitt "Example" (abgerufen 2026-10-17):
    Größe A>B>C>D>E gegen Gewicht C>D>A>B>E: diskordante Paare (A,C), (A,D), (B,C), (B,D), K_d = 4, normiert 4/10 = 0,4.
    Zweites Beispiel: A>B>C>D gegen B>D>A>C: K_d = 3, normiert 3/6 = 0,5.
(b) Beispiel "Hauptstadt von Tennessee" (42 % M>N>C>K, 26 % N>C>K>M, 15 % C>K>N>M, 17 % K>C>N>M; M = Memphis, N = Nashville, C = Chattanooga,
    K = Knoxville), dieselbe Wählerverteilung in allen drei Artikeln (abgerufen 2026-10-17):
    - https://en.wikipedia.org/wiki/Borda_count, Abschnitt Beispiel: Borda-Punkte (3 für Platz 1 bis 0) Memphis 126, Nashville 194,
      Chattanooga 173, Knoxville 107.
    - https://en.wikipedia.org/wiki/Copeland%27s_method, Abschnitt Beispiel: paarweise Ergebnisse M-N 42:58, M-K 42:58, M-C 42:58, N-K 68:32,
      N-C 68:32, K-C 17:83; Copeland-Wertung (1/½/0) Nashville 3, Chattanooga 2, Knoxville 1, Memphis 0.
    - https://en.wikipedia.org/wiki/Kemeny%E2%80%93Young_method, Abschnitt Beispiel: Kemeny-Wertung (Summe der "X vor Y"-Prozente) für alle
      24 Rangfolgen; Maximum 393 für N, C, K, M (Tabelle unten vollständig übernommen).
Die Wählerverteilung wird als 100 Bewerter mit 42, 26, 15 und 17 gleichen Rangfolgen abgebildet.
(c) Arrow, K. J. (1951): Social Choice and Individual Values (Cowles Commission Monograph 12, Wiley, Ausgabe 1951; Scan der Cowles-Foundation-Datei, gelesen über
    eine Archivkopie), Kapitel I Abschnitt 1, S. 2-3, gelesen 2026-10-17: Paradox der Mehrheitswahl. Drei Wähler, Alternativen A, B, C: Wähler 1: A vor B vor C,
    Wähler 2: B vor C vor A, Wähler 3: C vor A vor B. Eine Mehrheit zieht A dem B vor, eine Mehrheit B dem C und eine Mehrheit C dem A (Kreis).

NICHT eingesehen (daher kein Test, siehe Bericht "offen"): Kemeny 1959 (Daedalus 88), Young und Levenglick 1978 (SIAM J. Appl. Math. 35), Gibbard 1973;
Satterthwaite 1975 nur in der Arbeitspapierfassung (Northwestern Discussion Paper 122, 1974, ohne Zahlenbeispiel); für Median-Rang und das gewichtete Borda
dieser Demo gibt es keine Literaturwerte (eigene Konstruktion).
"""

import itertools

import numpy as np
import pytest

import bwt_aggregate as A
import bwt_evaluation as ev

M, N, C, K = 0, 1, 2, 3
NAMES = "MNCK"


def tennessee_profile():
    """Platzziffern je Wähler (0 = erster Platz), Spalten M, N, C, K, mit den Wählerzahlen 42, 26, 15 und 17."""
    groups = [(42, "MNCK"), (26, "NCKM"), (15, "CKNM"), (17, "KCNM")]
    rows = []
    for count, order in groups:
        rank = [order.index(c) for c in NAMES]
        rows += [rank] * count
    return np.array(rows)


TB = np.array([0.0, 0.1, 0.2, 0.3])

# Kemeny-Wertung aller 24 Rangfolgen laut Wikipedia "Kemeny-Young method", Abschnitt Example (abgerufen 2026-10-17).
KEMENY_TABLE = {
    "MNCK": 345, "MNKC": 279, "MCNK": 309, "MCKN": 273, "MKNC": 243, "MKCN": 207,
    "NMCK": 361, "NMKC": 295, "NCMK": 377, "NCKM": 393, "NKMC": 311, "NKCM": 327,
    "CMNK": 325, "CMKN": 289, "CNMK": 341, "CNKM": 357, "CKMN": 305, "CKNM": 321,
    "KMNC": 259, "KMCN": 223, "KNMC": 275, "KNCM": 291, "KCMN": 239, "KCNM": 255,
}


def order_to_rank_vector(order):
    return [order.index(c) for c in NAMES]


def test_kendall_tau_distance_examples_of_the_wikipedia_article():
    # Größe A>B>C>D>E, Gewicht C>D>A>B>E (Platzziffern 0-basiert, Reihenfolge A, B, C, D, E)
    height = [0, 1, 2, 3, 4]
    weight = [2, 3, 0, 1, 4]
    assert A.kendall(height, weight) == 4
    assert A.kendall(height, weight) / ev.max_distance(5) == pytest.approx(0.4)
    # A>B>C>D gegen B>D>A>C
    first = [0, 1, 2, 3]
    second = [2, 0, 3, 1]                         # A dritter, B erster, C vierter, D zweiter
    assert A.kendall(first, second) == 3
    assert A.kendall(first, second) / ev.max_distance(4) == pytest.approx(0.5)


def test_tennessee_profile_reproduces_the_borda_points():
    ranks = tennessee_profile()
    assert ranks.shape == (100, 4)
    points = (3 - ranks).sum(axis=0)
    assert points.tolist() == [126, 194, 173, 107]
    # Borda der Demo (Platzsumme, kleiner = besser) ordnet nach den Punkten 194 > 173 > 126 > 107, also N, C, M, K (Borda ordnet anders als Copeland und Kemeny)
    assert A.borda(ranks, TB).tolist() == order_to_rank_vector("NCMK")


def test_tennessee_pairwise_counts_and_copeland_score():
    ranks = tennessee_profile()
    P = A.pref_matrix(ranks)
    expected = {("M", "N"): 42, ("M", "K"): 42, ("M", "C"): 42, ("N", "K"): 68, ("N", "C"): 68, ("K", "C"): 17}
    for (x, y), v in expected.items():
        assert P[NAMES.index(x), NAMES.index(y)] == v
        assert P[NAMES.index(y), NAMES.index(x)] == 100 - v
    wins = (P > P.T).sum(axis=1)                   # kein Gleichstand im Beispiel
    assert wins.tolist() == [0, 3, 2, 1]           # M, N, C, K = 0, 3, 2, 1
    assert A.copeland(ranks, TB).tolist() == order_to_rank_vector("NCKM")


def test_tennessee_kemeny_scores_of_all_24_rankings_and_the_optimum():
    ranks = tennessee_profile()
    P = A.pref_matrix(ranks)
    for order, score in KEMENY_TABLE.items():
        idx = [NAMES.index(c) for c in order]
        got = sum(P[idx[a], idx[b]] for a in range(4) for b in range(a + 1, 4))
        assert got == score, order
    assert len(KEMENY_TABLE) == 24 and set(KEMENY_TABLE) == {"".join(p) for p in itertools.permutations(NAMES)}
    assert max(KEMENY_TABLE.values()) == 393
    assert A.kemeny(ranks, TB).tolist() == order_to_rank_vector("NCKM")
    # der Kemeny-Abstand der Demo (Summe der Kendall-Abstände) ist die Gesamtzahl der Paarentscheidungen minus Wertung: 6 * 100 - 393
    got = A.kemeny(ranks, TB)
    assert sum(A.kendall(got, r) for r in ranks) == 6 * 100 - 393


def test_arrow_paradox_of_voting_gives_a_majority_cycle():
    # Arrow 1951, Kapitel I Abschnitt 1, S. 2-3: Wähler 1: A>B>C, Wähler 2: B>C>A, Wähler 3: C>A>B (Platzziffern 0-basiert, Spalten A, B, C)
    ranks = np.array([[0, 1, 2], [2, 0, 1], [1, 2, 0]])
    P = A.pref_matrix(ranks)
    assert P[0, 1] == 2 and P[1, 0] == 1           # eine Mehrheit zieht A dem B vor
    assert P[1, 2] == 2 and P[2, 1] == 1           # eine Mehrheit zieht B dem C vor
    assert P[2, 0] == 2 and P[0, 2] == 1           # aber eine Mehrheit zieht C dem A vor: Kreis
    tb = np.array([0.0, 0.1, 0.2])
    # Im Kreis schlägt jeder genau einen anderen: Copeland-Wertung gleich (je 1 Sieg), also entscheidet allein der Gleichstandsschlüssel
    wins = (P > P.T).sum(axis=1)
    assert wins.tolist() == [1, 1, 1]
    assert A.copeland(ranks, tb).tolist() == [0, 1, 2]
