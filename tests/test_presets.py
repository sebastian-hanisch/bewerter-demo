"""Presets: Vollständigkeit, gültige Werte, erstes Preset = Standardeinstellungen; Adressparameter, Szenario und PDF."""

import bwt_constants as C
import bwt_evaluation as ev
import bwt_pdf_export as X
import bwt_presets as P
from bwt_scenario import Settings


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for name, p in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            if spec.lo is not None:
                assert spec.lo <= p[key] <= spec.hi, (name, key)
            if spec.choices is not None:
                assert p[key] in spec.choices, (name, key)


def test_first_preset_equals_the_default_settings():
    assert Settings(**C.PRESETS["Viele ehrliche Bewerter"]) == Settings()


def test_preset_keys_are_exactly_the_settings_fields():
    assert set(P.PRESET_KEYS) == set(Settings.__dataclass_fields__)


def test_setting_specs_cover_every_preset_key_and_have_unique_parameters():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    params = [spec.url_param for spec in P.SETTING_SPECS.values()]
    assert len(params) == len(set(params))


def test_presets_show_their_mechanism():
    p = C.PRESETS
    assert p["Zufall im Panel"]["n_rand"] == 8 and p["Zufall im Panel"]["n_mid"] + p["Zufall im Panel"]["n_rand"] == 15
    assert p["Zwei Manipulatoren"]["n_manip"] == 2 and p["Zwei Manipulatoren"]["strategy"] == C.STRATEGIES[1]
    assert p["Die Mehrheit manipuliert"]["n_manip"] == 8 and p["Die Mehrheit manipuliert"]["n_mid"] == 7


def test_constants_are_sound():
    assert len(C.SWEEP_SEEDS) == len(set(C.SWEEP_SEEDS)) == 60
    assert set(C.COLORS) == set(C.METHODS) and set(C.TYPE_COLORS) == {"gut", "mittel", "schlecht", "Zufall", "Manipulator"}
    assert C.K_GOOD > C.K_MID > C.K_BAD and C.N_MAX == 8 and C.EXP_N == C.N_MAX
    assert all(sum(mix) in (9, 6) or mix == (2, 0, 7) for mix in C.EXP_MIXES)


def test_pdf_is_built_for_every_preset():
    for name, p in C.PRESETS.items():
        data = X.build_pdf(ev.analyse(Settings(**p)))
        assert data[:5] == b"%PDF-" and len(data) > 1500


def test_latin_filter_replaces_greek_and_math_symbols():
    out = X._latin("λ ≈ 0,5; σ → τ µ θ − **fett** „Zitat“")
    assert out == 'lambda ca. 0,5; sigma -> Tau mu theta - fett "Zitat"'
    assert out.encode("latin-1")
