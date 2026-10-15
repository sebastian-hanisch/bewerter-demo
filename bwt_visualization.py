"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import numpy as np
import plotly.graph_objects as go

import bwt_constants as C
import bwt_evaluation as ev


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.3), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_raters(a: ev.Analysis):
    """Abstand je Bewerter zur Wahrheit (Balken, nach Typ gefärbt) und sein Gewicht im gewichteten Borda (Punkte)."""
    types = list(a.instance.types)
    x = [f"{i + 1}" for i in range(len(types))]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=a.rater_distance, marker_color=[C.TYPE_COLORS[t] for t in types], name="Abstand zur Wahrheit", text=types, textposition="none",
                         hovertemplate="Bewerter %{x} (%{text}): Abstand %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=x, y=a.weights, mode="markers", name="Gewicht im gewichteten Borda", marker=dict(color="#2c3e50", size=8, symbol="diamond"), yaxis="y2",
                             hovertemplate="Bewerter %{x}: Gewicht %{y:.2f}<extra></extra>"))
    fig.update_layout(yaxis=dict(title="Abstand zur Wahrheit (Anteil falsch geordneter Paare)", range=[0, max(0.6, float(a.rater_distance.max()) * 1.1)]),
                      yaxis2=dict(title="Gewicht", overlaying="y", side="right", range=[0, 1.05]))
    fig.update_xaxes(title_text="Bewerter (nach Typ sortiert: gut, mittel, schlecht, Zufall, Manipulator)", type="category")
    return _base(fig, height=360)


def build_methods(a: ev.Analysis):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=list(C.METHODS), y=[a.metrics[m][0] for m in C.METHODS], marker_color=[C.COLORS[m] for m in C.METHODS],
                         hovertemplate="%{x}: Abstand %{y:.3f}<extra></extra>"))
    fig.update_yaxes(title_text="Abstand zur Wahrheit")
    return _base(fig, height=320)


def build_consensus(a: ev.Analysis):
    """Platz je Verfahren und Teilnehmer; Teilnehmer nach wahrer Stärke geordnet (links der Beste)."""
    n = a.settings.n
    z = np.array([a.consensus[m] for m in C.METHODS] + [np.arange(n)], dtype=float) + 1
    labels = list(C.METHODS) + ["Wahrheit"]
    fig = go.Figure(go.Heatmap(z=z, x=[f"{i + 1}" for i in range(n)], y=labels, colorscale="Teal", reversescale=True, zmin=1, zmax=n,
                               colorbar=dict(title="Platz"), hovertemplate="Teilnehmer mit wahrem Rang %{x}: Platz %{z} bei %{y}<extra></extra>"))
    fig.update_xaxes(title_text="Teilnehmer nach wahrem Rang (1 = Bester)", type="category")
    fig.update_yaxes(autorange="reversed")
    return _base(fig, height=320)


def _group(cells: dict, key_fmt, metric: int, ylabel: str, yrange=None, xtitle=""):
    fig = go.Figure()
    for m in C.METHODS:
        fig.add_trace(go.Scatter(x=[key_fmt(k) for k in cells], y=[cells[k][m][metric] for k in cells], mode="lines+markers", name=m, line=dict(color=C.COLORS[m], width=3)))
    fig.update_xaxes(title_text=xtitle, type="category")
    fig.update_yaxes(title_text=ylabel, **({"range": yrange} if yrange else {}))
    return _base(fig, height=340)


def build_count(e1):
    return _group(e1, str, 0, "Abstand zur Wahrheit", xtitle="schlechte Bewerter (ein Spiel je Paar)")


def build_mix(e2):
    fig = go.Figure()
    labels = [f"{g} gut, {m} mittel, {b} schlecht" for g, m, b in e2]
    for m in C.METHODS:
        fig.add_trace(go.Bar(x=labels, y=[e2[k][m][0] for k in e2], name=m, marker_color=C.COLORS[m]))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Abstand zur Wahrheit")
    return _base(fig, height=340)


def build_random(e3):
    return _group(e3, lambda z: f"{z} von 15", 0, "Abstand zur Wahrheit", xtitle="Zufalls-Bewerter im Panel von 15")


def build_manip(e4, strategy: str, metric: int = 1):
    cells = {c: e4[(strategy, c)] for c in C.EXP_MANIP_COUNTS}
    label = "Sieger richtig (Anteil der Läufe)" if metric == 1 else "Ziel gewinnt (Anteil der Läufe)"
    return _group(cells, lambda c: f"{c} von 15", metric, label, yrange=[-0.02, 1.02], xtitle="Manipulatoren im Panel von 15")
