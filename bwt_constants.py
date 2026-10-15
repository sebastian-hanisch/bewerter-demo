"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 4, 8, 8
DELTA = 0.3                                   # Stärkeabstand der Teilnehmer (Generator Version 1, gleichabständig)
K_GOOD, K_MID, K_BAD = 16, 4, 1               # Partien je Paar im eigenen kleinen Turnier der ehrlichen Bewerter
COUNT_MAX = 31
GOOD_MAX, MID_MAX, BAD_MAX, RAND_MAX, MANIP_MAX = 15, COUNT_MAX, COUNT_MAX, COUNT_MAX, 15
DEFAULT_GOOD, DEFAULT_MID, DEFAULT_BAD, DEFAULT_RAND, DEFAULT_MANIP = 0, 9, 0, 0, 0
STRATEGIES = ("Ziel hochsetzen", "Besten begraben", "Beides")
DEFAULT_STRATEGY = STRATEGIES[2]
TARGET_MIN, DEFAULT_TARGET = 2, 5             # wahrer Rang des Ziels (2 bis n)
SEED_MAX, DEFAULT_SEED = 999999, 7

METHODS = ("Borda", "Median", "Copeland", "Kemeny", "Borda gewichtet")
WEIGHT_ROUNDS = 3

# Feste Instanzen für alle Experimente: nie ein einzelner Seed als Befund.
SWEEP_SEEDS = tuple(range(100000, 100060))
EXP_N = 8
EXP_PANEL = 15
EXP_BAD_COUNTS = (1, 3, 5, 9, 15, 31)
EXP_RANDOM_COUNTS = (0, 4, 8, 11)
EXP_MANIP_COUNTS = (0, 2, 4, 6, 8)
EXP_MIXES = ((0, 9, 0), (3, 3, 3), (2, 0, 7))                   # (gute, mittlere, schlechte)

COLORS = {"Borda": "#2F6B65", "Median": "#9aa0a6", "Copeland": "#4c78a8", "Kemeny": "#8e6bb0", "Borda gewichtet": "#c0392b"}
TYPE_COLORS = {"gut": "#2F6B65", "mittel": "#9cc5bf", "schlecht": "#c9b6e0", "Zufall": "#9aa0a6", "Manipulator": "#c0392b"}
COLOR_TRUTH = "#e67e22"

_BASE = {"n": DEFAULT_N, "n_good": DEFAULT_GOOD, "n_mid": DEFAULT_MID, "n_bad": DEFAULT_BAD, "n_rand": DEFAULT_RAND, "n_manip": DEFAULT_MANIP,
         "strategy": DEFAULT_STRATEGY, "target_rank": DEFAULT_TARGET, "seed": DEFAULT_SEED}
PRESETS = {
    "Viele ehrliche Bewerter": dict(_BASE),
    "Zufall im Panel": {**_BASE, "n_mid": 7, "n_rand": 8},
    "Zwei Manipulatoren": {**_BASE, "n_mid": 13, "n_manip": 2, "strategy": STRATEGIES[1]},
    "Die Mehrheit manipuliert": {**_BASE, "n_mid": 7, "n_manip": 8},
}
PRESET_HELP = {
    "Viele ehrliche Bewerter": "Neun Bewerter mit einem kleinen eigenen Turnier: Alle Verfahren liegen dicht an der Wahrheit.",
    "Zufall im Panel": "Acht von fünfzehn Bewertern raten: Borda verliert viel, das gewichtete Borda fängt es auf.",
    "Zwei Manipulatoren": "Zwei von fünfzehn setzen den wahren Besten ans Ende: Borda verliert den richtigen Sieger fast immer, Copeland und Kemeny halten besser.",
    "Die Mehrheit manipuliert": "Acht von fünfzehn setzen das Ziel auf Platz 1 und den Besten ans Ende: Median, Copeland und Kemeny sind vollständig gekapert.",
}
