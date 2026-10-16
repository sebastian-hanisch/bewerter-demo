"""Die Bewerter sind unsicher: Rauschen und Manipulation - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Fünfzehntes Stück der Ranking-Linie: Mehrere Bewerter bringen je eine Rangfolge, aber nicht alle sind gleich gut, manche raten, manche manipulieren. Fünf Experimente messen, wie viele Bewerter
man braucht, was gemischte Qualität und Zufalls-Bewerter ausmachen, was die Gewichtung nach Übereinstimmung leistet und wie viele Manipulatoren den Sieger kippen. Aufbau und Regeln:
DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import bwt_constants as C
import bwt_evaluation as ev
from bwt_pdf_export import build_pdf
from bwt_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from bwt_scenario import Settings
from bwt_visualization import (
    build_consensus,
    build_count,
    build_manip,
    build_methods,
    build_mix,
    build_random,
    build_raters,
)

st.set_page_config(page_title="Die Bewerter sind unsicher – Sebastian Hanisch", layout="wide")

SHOW = {"success": st.success, "info": st.info, "warning": st.warning}


def verdict(level, text):
    SHOW[level](text)


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return ev.analyse(settings)


@st.cache_data(show_spinner="Experiment rechnet über 60 feste Läufe …")
def _count():
    return ev.sweep_count()


@st.cache_data(show_spinner="Experiment rechnet über 60 feste Läufe …")
def _mix():
    return ev.sweep_mix()


@st.cache_data(show_spinner="Experiment rechnet über 60 feste Läufe …")
def _random():
    return ev.sweep_random()


@st.cache_data(show_spinner="Experiment rechnet über 60 feste Läufe …")
def _manip():
    return ev.sweep_manip()


st.title("🗳️ Die Bewerter sind unsicher: Rauschen und Manipulation")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n = st.slider("Teilnehmer", *bounds("n_slider"), key="n_slider", help="Wie viele Teilnehmer gerankt werden (höchstens 8, damit Kemeny exakt bleibt).")
    n_good = st.slider("Gute Bewerter", *bounds("good_slider"), key="good_slider", help="Eigenes Turnier mit 16 Partien je Paar: fast die wahre Rangfolge.")
    n_mid = st.slider("Mittlere Bewerter", *bounds("mid_slider"), key="mid_slider", help="Eigenes Turnier mit 4 Partien je Paar.")
    n_bad = st.slider("Schlechte Bewerter", *bounds("bad_slider"), key="bad_slider", help="Eigenes Turnier mit 1 Partie je Paar: viel Rauschen.")
    n_rand = st.slider("Zufalls-Bewerter", *bounds("rand_slider"), key="rand_slider", help="Bringen eine zufällige Rangfolge (raten).")
    n_manip = st.slider("Manipulatoren", *bounds("manip_slider"), key="manip_slider",
                        help="Urteilen wie mittlere Bewerter, setzen aber das Ziel nach vorn und/oder den wahren Besten ans Ende. Sie kennen die Wahrheit und das Ziel (stärkster Angreifer).")
    strategy = st.selectbox("Strategie der Manipulatoren", C.STRATEGIES, key="strategy_select", help="Ziel auf Platz 1, Besten auf den letzten Platz, oder beides.")
    st.session_state["target_slider"] = min(int(st.session_state["target_slider"]), int(n))
    target = st.slider("Wahrer Rang des Ziels", C.TARGET_MIN, int(n), key="target_slider", help="Welcher Teilnehmer nach oben gesetzt werden soll (2 = der Zweitbeste).")
    seed = st.number_input("Zufalls-Seed", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Lauf würfeln", width="stretch", on_click=randomize_seed)

sync_query_params({"n_slider": int(n), "good_slider": int(n_good), "mid_slider": int(n_mid), "bad_slider": int(n_bad), "rand_slider": int(n_rand), "manip_slider": int(n_manip),
                   "strategy_select": strategy, "target_slider": int(target), "seed_input": int(seed)})

st.markdown(
    """
Mehrere Bewerter ordnen dieselben Teilnehmer, aber nicht alle sind gleich gut: Manche urteilen mit viel Rauschen, manche raten, manche **manipulieren**. Diese Demo ist das
**fünfzehnte Stück der Ranking-Linie** und misst, **wie viele Bewerter man braucht**, **was die Gewichtung nach Übereinstimmung gegen Zufall leistet** und **wie viele Manipulatoren den
Sieger kippen**. Immer mit der Wahrheit daneben: Die Simulation kennt die wahre Rangfolge.

Weiter unten: fünf **🔬 Experimente** mit Verdikt, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("Wem vertraut die Rangfolge?", expanded=True):
    st.markdown(
        """
1. **Bewerter:** Jeder ehrliche Bewerter spielt ein eigenes kleines Turnier und bringt die Rangfolge nach seinen Siegen: je mehr Partien, desto näher an der Wahrheit.
2. **Zufall und Manipulation:** Zufalls-Bewerter raten. Manipulatoren urteilen sonst wie mittlere Bewerter, setzen aber ihr **Ziel** auf Platz 1 und/oder den **wahren Besten** ans Ende.
3. **Verfahren:** **Borda** summiert die Plätze, **Median** nimmt den mittleren Platz, **Copeland** zählt die paarweisen Mehrheiten, **Kemeny** minimiert die Summe der Abstände zu allen
   Eingaben (exakt). **Borda gewichtet** gibt jedem Bewerter das Gewicht seiner Übereinstimmung mit dem Konsens (iteriert).
4. **Maße:** Abstand zur Wahrheit (Anteil falsch geordneter Paare), **Sieger richtig** und **Ziel gewinnt**. Immer beide Seiten.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
cols = st.columns(len(C.PRESETS))
for col, name in zip(cols, C.PRESETS):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

settings = Settings(int(n), int(n_good), int(n_mid), int(n_bad), int(n_rand), int(n_manip), strategy, int(target), int(seed))
a = _analysis(settings)

st.markdown("---")

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🗳️ Die zusammengefasste Rangfolge")
if not a.metrics:
    verdict(*ev.verdict_analysis(a))
else:
    cols = st.columns(len(C.METHODS))
    for col, m in zip(cols, C.METHODS):
        d, win, tgt = a.metrics[m]
        col.metric(m, ev.de(d, 3), delta=f"Sieger {'richtig' if win else 'falsch'}" + (f" · Ziel {'gewinnt' if tgt else 'verliert'}" if settings.n_manip else ""), delta_color="off",
                   help="Anteil der Teilnehmerpaare, die diese Rangfolge anders ordnet als die Wahrheit (0 = richtig).")
    verdict(*ev.verdict_analysis(a))
    cl, cr = st.columns(2)
    with cl:
        st.plotly_chart(build_raters(a), width="stretch", key="raters_chart")
        st.caption("Abstand jedes Bewerters zur Wahrheit (Balken) und sein Gewicht im gewichteten Borda (Raute). Zufalls-Bewerter haben Gewicht nahe 0; Manipulatoren behalten es.")
    with cr:
        st.plotly_chart(build_consensus(a), width="stretch", key="consensus_chart")
        st.caption("Platz jedes Teilnehmers bei jedem Verfahren; die untere Zeile ist die Wahrheit.")
    st.plotly_chart(build_methods(a), width="stretch", key="methods_chart")
    st.download_button("📄 PDF des aktuellen Panels", data=build_pdf(a), file_name="bewerter.pdf", mime="application/pdf", key="pdf_download")

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Wie viele Bewerter braucht man?")
st.caption("8 Teilnehmer (feste Instanz), alle Bewerter schlecht (ein Spiel je Paar), 60 feste Läufe; Abstand zur Wahrheit.")
e1 = _count()
st.plotly_chart(build_count(e1), width="stretch", key="exp1_chart")
verdict(*ev.verdict_count(e1))

st.subheader("🔬 Experiment 2: Gemischte Qualität")
st.caption("9 Bewerter in drei Mischungen; Abstand zur Wahrheit.")
e2 = _mix()
st.plotly_chart(build_mix(e2), width="stretch", key="exp2_chart")
verdict(*ev.verdict_mix(e2))

st.subheader("🔬 Experiment 3: Zufalls-Bewerter und die Gewichtung")
st.caption("15 Bewerter, davon z Zufall, die übrigen mittel.")
e3 = _random()
st.plotly_chart(build_random(e3), width="stretch", key="exp3_chart")
verdict(*ev.verdict_random(e3))
st.dataframe(pd.DataFrame([{"Zufall von 15": z, **{f"{m}: Sieger richtig": round(e3[z][m][1], 2) for m in C.METHODS}} for z in C.EXP_RANDOM_COUNTS]), hide_index=True, width="stretch")

st.subheader("🔬 Experiment 4: Manipulation: hochsetzen oder begraben?")
st.caption("15 Bewerter, davon c Manipulatoren (urteilen sonst mittel); Ziel ist der Teilnehmer mit wahrem Rang 5. Sieger richtig = der wahre Beste steht oben.")
e4 = _manip()
c1, c2 = st.columns(2)
with c1:
    st.markdown("**Ziel hochsetzen**")
    st.plotly_chart(build_manip(e4, C.STRATEGIES[0]), width="stretch", key="exp4a_chart")
with c2:
    st.markdown("**Besten begraben**")
    st.plotly_chart(build_manip(e4, C.STRATEGIES[1]), width="stretch", key="exp4b_chart")
verdict(*ev.verdict_bury(e4))

st.subheader("🔬 Experiment 5: Minderheit gegen Mehrheit")
st.caption("Beides zugleich (Ziel auf Platz 1, Bester auf den letzten Platz): Anteil der Läufe, in denen das Ziel gewinnt, nach Zahl der Manipulatoren.")
st.plotly_chart(build_manip(e4, C.STRATEGIES[2], metric=2), width="stretch", key="exp5_chart")
verdict(*ev.verdict_majority(e4))
st.dataframe(pd.DataFrame([{"Manipulatoren von 15": c, **{m: f"{ev.pct(e4[(C.STRATEGIES[2], c)][m][2])} %" for m in C.METHODS}} for c in C.EXP_MANIP_COUNTS]), hide_index=True, width="stretch")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Manipulatoren kennen die Wahrheit** | Das ist der stärkste Angreifer; echte Angreifer kennen nur das Feld und treffen schlechter. | – |
| **Die Rangfolgen sind vollständig** | Echte Bewerter ordnen nicht alle Teilnehmer; Lücken und Mehrfachbewertungen sind nicht modelliert. | Massey und Colley |
| **Das Rauschen ist künstlich** | Es entsteht aus kleinen Turnieren; echte Bewerter haben Vorlieben, Ermüdung, Absprachen. | – |
| **Ein Panel mit Mehrheit schlechter Bewerter** | Die Gewichtung nach Übereinstimmung zieht Konsens und Gewichte in die falsche Richtung. | – |
| **Nur 8 Teilnehmer** | Kemeny ist exakt gerechnet (Teilmengen-Rechnung); größere Felder sind nicht gemessen. | – |
| **Kein Verfahren ist angriffssicher** | Das sagen die Unmöglichkeitssätze von Arrow und Gibbard–Satterthwaite in einem Satz; hier wird nur gemessen, gegen welchen Angriff bei welchem Anteil. | – |
| **Alles ist simuliert** | Die Zahlen gelten für dieses Rauschen und diese Angriffe. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Wahrheit.** $n$ Teilnehmer mit Stärken $s_i = 0{,}3\,\bigl(\tfrac{n-1}{2} - i\bigr)$ (Teilnehmer 0 ist der Beste); $P(i \text{ schlägt } j) = \sigma(s_i - s_j)$.

**Bewerter.** *Ehrlich:* spielt $k$ Partien je Paar (gut 16, mittel 4, schlecht 1) und ordnet nach den Siegen (Gleichstände nach einem kleinen Zufallswert). *Zufall:* gleichverteilte
Rangfolge. *Manipulator:* ordnet wie ein mittlerer Bewerter, setzt aber das Ziel auf Platz 1 und/oder den wahren Besten auf den letzten Platz.

**Verfahren.** Eingaben sind Platzziffern $r_{k i}$ (Bewerter $k$, Teilnehmer $i$; 0 = Beste).
- *Borda:* sortiert nach $\sum_k r_{ki}$. *Median:* nach dem Median der $r_{ki}$ über $k$ (Gleichstand nach dem Mittel).
- *Copeland:* $P_{ij} = \#\{k : r_{ki} < r_{kj}\}$; Punktzahl $=\#\{j : P_{ij} > P_{ji}\} + \tfrac12\#\{j \ne i : P_{ij} = P_{ji}\}$.
- *Kemeny:* die Rangfolge $\pi$, die $\sum_k d_K(\pi, r_k)$ minimiert, exakt über alle Teilmengen (Kosten, wenn $j$ hinter der Menge $S$ steht: $\sum_{i \in S} P_{ji}$).
- *Borda gewichtet:* $w_k = \max\{0,\, 1 - 2\,d_K(r_k, c)/\binom n2\}$ mit dem Konsens $c$, dann Borda mit Gewichten $w_k$; drei Runden ab dem einfachen Borda.
Gleichstände löst für alle Verfahren derselbe feste Zufallsschlüssel auf.

**Maße.** $d_K$ ist die Zahl der Teilnehmerpaare, die zwei Rangfolgen verschieden ordnen. *Abstand* $= d_K(\hat\pi, \pi^*)/\binom n2$ mit der Wahrheit $\pi^*$. *Sieger richtig:* der wahre Beste
steht auf Platz 1. *Ziel gewinnt:* das Ziel steht auf Platz 1.

**Zufall.** SplitMix64-Strom des Generators; je Bewerter ein eigener Strom aus (Seed, laufende Nummer).

**Literatur.**
- Arrow, K. J. (1951): *Social Choice and Individual Values* (nicht eingesehen).
- Gibbard, A. (1973): Manipulation of voting schemes: a general result. *Econometrica* 41, 587–601 (nicht eingesehen).
- Satterthwaite, M. A. (1975): Strategy-proofness and Arrow's conditions. *Journal of Economic Theory* 10, 187–217 (nicht eingesehen).
- Kemeny, J. G. (1959): Mathematics without numbers. *Daedalus* 88, 577–591 (nicht eingesehen).
- Dawid, A. P., Skene, A. M. (1979): Maximum likelihood estimation of observer error-rates using the EM algorithm. *Journal of the Royal Statistical Society C* 28, 20–28 (nicht eingesehen).
- Chen, X., Bennett, P. N., Collins-Thompson, K., Horvitz, E. (2013): Pairwise ranking aggregation in a crowdsourced setting. *WSDM 2013* (nicht eingesehen).
- Steele, G. L., Lea, D., Flood, C. H. (2014): Fast splittable pseudorandom number generators. *OOPSLA 2014*, 453–472 (Zufallsstrom des Generators).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Ranking: von der Siegtabelle bis Learning to Rank](https://sebastianhanisch.net/konzepte-ranking.html)."
)
