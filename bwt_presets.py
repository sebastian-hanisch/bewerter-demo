"""Permalink (Begrenzen), Presets und Zufalls-Seed-Button. Es gibt keinen ausblendbaren Regler: alle Regler sind in jedem Szenario sichtbar."""

import random
from dataclasses import dataclass

import streamlit as st

import bwt_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: object
    default: object
    lo: float | None = None
    hi: float | None = None
    choices: tuple | None = None


SETTING_SPECS = {
    "n_slider": SettingSpec("n", int, C.DEFAULT_N, C.N_MIN, C.N_MAX),
    "good_slider": SettingSpec("g", int, C.DEFAULT_GOOD, 0, C.GOOD_MAX),
    "mid_slider": SettingSpec("m", int, C.DEFAULT_MID, 0, C.MID_MAX),
    "bad_slider": SettingSpec("b", int, C.DEFAULT_BAD, 0, C.BAD_MAX),
    "rand_slider": SettingSpec("z", int, C.DEFAULT_RAND, 0, C.RAND_MAX),
    "manip_slider": SettingSpec("x", int, C.DEFAULT_MANIP, 0, C.MANIP_MAX),
    "strategy_select": SettingSpec("st", str, C.DEFAULT_STRATEGY, choices=C.STRATEGIES),
    "target_slider": SettingSpec("t", int, C.DEFAULT_TARGET, C.TARGET_MIN, C.N_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"n": "n_slider", "n_good": "good_slider", "n_mid": "mid_slider", "n_bad": "bad_slider", "n_rand": "rand_slider", "n_manip": "manip_slider",
               "strategy": "strategy_select", "target_rank": "target_slider", "seed": "seed_input"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt bzw. auf gültige Auswahlwerte geprüft."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param not in qp:
            continue
        try:
            value = spec.caster(qp[spec.url_param])
        except (ValueError, TypeError):
            continue
        if spec.choices is not None and value not in spec.choices:
            continue
        if spec.lo is not None:
            value = max(spec.lo, value)
        if spec.hi is not None:
            value = min(spec.hi, value)
        st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
