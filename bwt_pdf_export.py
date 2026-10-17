"""PDF-Export der aktuellen Konfiguration und der Kennzahlen (fpdf2, Kernschrift: nur Zeichen aus Latin-1)."""

from fpdf import FPDF

import bwt_constants as C
import bwt_evaluation as ev


def _latin(text: str) -> str:
    for old, new in (("–", "-"), ("—", "-"), ("τ", "Tau"), ("σ", "sigma"), ("λ", "lambda"), ("µ", "mu"), ("θ", "theta"), ("≈", "ca."), ("≥", ">="), ("≤", "<="),
                     ("→", "->"), ("**", ""), ("€", "EUR"), ("−", "-"), ("„", '"'), ("“", '"'), ("f̂", "f"), ("̂", "")):
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: ev.Analysis) -> bytes:
    s = a.settings
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 15)
    pdf.multi_cell(0, 8, _latin("Die Bewerter sind unsicher: Rauschen und Manipulation"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(2)
    pdf.multi_cell(0, 5.5, _latin(f"Teilnehmer: {s.n}; Bewerter: {s.n_good} gute, {s.n_mid} mittlere, {s.n_bad} schlechte, {s.n_rand} Zufall, {s.n_manip} Manipulatoren "
                                  f"({s.strategy}, Ziel: wahrer Rang {s.target_rank}); Seed: {s.seed}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    _level, text = ev.verdict_analysis(a)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Kernaussage", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5.5, _latin(text), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    headers = ("Verfahren", "Abstand", "Sieger richtig", "Ziel gewinnt")
    widths = (60, 30, 40, 40)
    pdf.set_font("Helvetica", "B", 9)
    for h, w in zip(headers, widths):
        pdf.cell(w, 6, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for name in C.METHODS:
        if name not in a.metrics:
            continue
        d, win, tgt = a.metrics[name]
        for value, w in zip((name, f"{d:.3f}", f"{win:.0f}", f"{tgt:.0f}"), widths):
            pdf.cell(w, 6, _latin(value), border=1)
        pdf.ln()
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4.5, _latin(
        "Alles ist simuliert (Stärken aus dem Generator der Ranking-Linie, Rangfolgen aus eigenen kleinen Turnieren). Die Manipulatoren kennen die Wahrheit und das Ziel, spielen aber nur zwei einfache Strategien."
        "Quelle: Demo von Sebastian Hanisch, sebastianhanisch.net."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
