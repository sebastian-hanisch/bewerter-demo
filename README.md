# Die Bewerter sind unsicher: Rauschen und Manipulation – Streamlit-Demo

Fünfzehntes Stück der **Ranking-Linie** (Konzepte-Demo), Nachfolger von `rangaggregation-demo` und `learning-to-rank-demo`: Mehrere Bewerter bringen je eine Rangfolge, aber nicht alle sind
gleich gut, manche raten, manche manipulieren. Gemessen wird, **wie viele Bewerter man braucht**, **was gemischte Qualität und Zufalls-Bewerter ausmachen**, **was die Gewichtung nach
Übereinstimmung leistet** und **wie viele Manipulatoren den Sieger kippen** (Ziel hochsetzen gegen den Besten begraben, Minderheit gegen Mehrheit). Das Vehikel ist das neutrale, simulierte
Turnier der Wurzel (Stärken aus dem Generator Version 1, wortgleich); jeder ehrliche Bewerter bringt die Tabelle eines eigenen kleinen Turniers. Alles ist simuliert.

## Kernfrage

Wem vertraut die Rangfolge? **Rauschen mittelt sich heraus:** schlechte Bewerter (ein Spiel je Paar): Abstand zur Wahrheit (Anteil falsch geordneter Paare) bei Borda 0,24 (1 Bewerter), 0,12 (5),
0,035 (15), 0,011 (31). **Zufalls-Bewerter** kosten das Borda am meisten: bei 8 von 15 Abstand 0,13, gewichtet 0,05, Copeland 0,085; die **Gewichtung** nach Übereinstimmung mit dem Konsens
erkennt Zufall, weil Zufall mit niemandem übereinstimmt. **Manipulatoren, die den wahren Besten ans Ende setzen,** treffen Borda am schlimmsten: mit 2 von 15 steht der Beste nur noch in 0,33
der Läufe oben (Copeland 0,92), mit 4 von 15 in **0,00** (Copeland 0,67); die Gewichtung hilft dort nicht (0,07), weil die Manipulatoren sonst mit dem Konsens übereinstimmen. Das bloße
**Hochsetzen des Ziels** wirkt kaum (bis 6 von 15 gewinnt es nie). **Eine Mehrheit** (8 von 15) steuert Median, Copeland und Kemeny vollständig (Ziel gewinnt in 100 % der Läufe), Borda hält
sich (0,03): Mehrheitsregeln schützen vor Minderheiten, nicht vor Mehrheiten. **Kein Verfahren ist gegen jeden Angriff robust.**

## Modell

- **Wahrheit:** n ≤ 8 Teilnehmer mit gleichabständigen Stärken (Abstand 0,3, Generator Version 1), P(i schlägt j) = σ(s_i − s_j).
- **Bewerter:** *ehrlich* (gut: 16, mittel: 4, schlecht: 1 Partien je Paar im eigenen Turnier; Rangfolge nach den Siegen), *Zufall* (zufällige Rangfolge), *Manipulator* (urteilt wie ein
  mittlerer Bewerter, setzt aber das Ziel nach vorn und/oder den wahren Besten ans Ende). Die Manipulatoren kennen Wahrheit und Ziel: stärkster Angreifer.
- **Verfahren:** Borda (Summe der Plätze), Median-Rang, Copeland (paarweise Mehrheiten), Kemeny (exakt, Teilmengen-Rechnung), **gewichtetes Borda** (Gewicht = 1 − 2 · Abstand zum Konsens /
  größter Abstand, nicht unter 0; drei Runden).
- **Maße:** Abstand zur Wahrheit (normierte Kendall-Distanz), **Sieger richtig** (der wahre Beste steht oben) und **Ziel gewinnt** (das Ziel der Manipulatoren steht oben).
- Alle Formeln stehen im 📐-Expander der App.

## Methodik

- **Experimente** über 60 feste Läufe (`SWEEP_SEEDS`, nie ein einzelner Seed), je mit einem live berechneten Verdikt; feste Instanz mit 8 Teilnehmern, unabhängig vom Regler.
- **Gleichstände** löst für alle Verfahren derselbe feste Zufallsschlüssel je Instanz auf (nicht die Reihenfolge der Teilnehmer: sonst wäre jedes Verfahren zugunsten des wahren Besten verzerrt).
- **Zufall:** `turnier_generator.py` mit SplitMix64-Strom (wortgleich mit den Repos der Linie); je Bewerter ein eigener Strom aus (Seed, laufende Nummer): die ersten Bewerter bleiben bei
  größerem Panel dieselben.
- **Rechenzeit:** Die Experimente rechnen beim ersten Aufruf rund 20 Sekunden und werden danach zwischengespeichert.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen: 60 feste Läufe, 8 Teilnehmer; „Abstand“ ist der Anteil falsch geordneter Paare.

| Frage | Befund | Test |
|---|---|---|
| Zahl der schlechten Bewerter (1 / 3 / 5 / 9 / 15 / 31), Borda | Abstand **0,239 / 0,133 / 0,119 / 0,070 / 0,035 / 0,011**; Sieger richtig 0,43 / 0,63 / 0,68 / 0,75 / 0,78 / 0,90. Bei 31 Bewertern Copeland und Kemeny 0,021. | `test_more_raters_average_out_the_noise` |
| Gemischte Qualität, 9 Bewerter (9 mittlere / 3 + 3 + 3 / 2 gute + 7 schlechte), Borda | 0,032 / 0,032 / **0,051**; Copeland 0,030 / 0,018 / 0,043; gewichtet 0,032 / 0,023 / 0,046. | `test_mixed_quality_hardly_matters_without_spam` |
| Zufalls-Bewerter, 15 Bewerter (0 / 4 / 8 / 11 zufällig), Abstand Borda → gewichtet | **0,014 → 0,012; 0,054 → 0,030; 0,130 → 0,051; 0,234 → 0,131**; Copeland 0,085 und Kemeny 0,083 bei 8; Sieger richtig bei 8: Borda 0,58, gewichtet 0,80. | `test_random_raters_hurt_borda_most_and_the_weights_catch_them` |
| Besten ans Ende (2 / 4 / 6 von 15), Sieger richtig | Borda **0,33 / 0,00 / 0,00**; Median 0,83 / 0,57 / 0,30; Copeland 0,92 / 0,67 / 0,37; Kemeny 0,92 / 0,67 / 0,37; gewichtet 0,73 / 0,07 / 0,00. | `test_burying_the_best_is_what_hurts` |
| Ziel hochsetzen (2 / 4 / 6 von 15) | Sieger richtig bei allen Verfahren über 0,95, Ziel gewinnt nie; Abstand Borda 0,064 bei 6. | `test_pushing_the_target_up_changes_little_below_a_majority` |
| Mehrheit, beides (8 von 15), Ziel gewinnt | Median, Copeland, Kemeny **1,00**; Borda 0,03; gewichtet 0,17; Sieger richtig bei allen 0,00. | `test_a_majority_captures_the_majority_rules_but_not_borda` |
| Verdikte nennen dieselben Zahlen | Die live berechneten Texte der App geben die obigen Werte wieder. | `test_verdicts_quote_the_measured_numbers` |

## Befunde und Korrekturen gegenüber dem Plan

- **Die Gleichstandsregel verzerrte die Vorab-Messung:** Sie sortierte stabil nach dem Index des Teilnehmers, also zugunsten des wahren Besten (Index 0). Mit einem festen Zufallsschlüssel je
  Instanz liegen die Zahlen etwas schlechter: Borda-Sieger richtig ohne Manipulation 0,95 statt 0,98; Zufall 8 von 15: Borda 0,130 statt 0,112, gewichtet 0,051 statt 0,040, Copeland 0,085 statt
  0,067; Besten ans Ende, 2 von 15: Borda 0,33 statt 0,24. Die Aussagen bleiben.
- **Gewichtung gegen Zufall ist stark, gegen Strategie wirkungslos:** das stand so im Plan; das Verdikt der App sagt es mit den Zahlen der Läufe.
- **Der Vorteil von Borda bei gleichem Rauschen bleibt klein, aber stabil:** bei 31 schlechten Bewertern 0,011 gegen 0,021 bei Copeland und Kemeny (Plan: 0,023 gegen 0,033).
- Die Zahlen verschieben sich sonst um wenige Hundertstel (60 statt 100 Läufe, SplitMix64-Strom).

## Abgrenzung

- **Borda, Copeland, Kemeny** (Stück 3): vier Verfahren bei gleich guten Bewertern; hier **Bewerter unterschiedlicher Qualität, Zufall und Angriff** und das gewichtete Borda.
- **Learning to Rank** (Stück 14): „Stufen kommen von Bewertern“; hier die Bewerter selbst.
- **Rangumkehr** (Linie Mehrkriterien): Umkehrung der Rangfolge durch eine Alternative; hier keine Eingriffe in die Alternativenmenge, sondern in die Bewertungen.
- **Turnierplanung** (Absprachen im Spielplan): dort geht es um Spielergebnisse, hier um Bewertungen.
- **Nachfolger (nur beim Namen):** Welches Verfahren, gemessen woran?

## Ehrliche Grenzen

- **Die Manipulatoren kennen die Wahrheit und das Ziel:** stärkster Angreifer; echte Angreifer kennen nur das Feld und treffen schlechter.
- **Die Rangfolgen sind vollständig und aus eigenen kleinen Turnieren:** künstliches Rauschen, keine echten Bewerter (Vorlieben, Ermüdung, Absprachen); keine Lücken, keine Stufen.
- **n ≤ 8:** wegen exaktem Kemeny; größere Felder nicht gemessen.
- **Gewichtung nach Übereinstimmung:** Ein Panel mit Mehrheit schlechter Bewerter zieht den Konsens (und damit die Gewichte) in die falsche Richtung.
- **Unmöglichkeitssätze nicht gemessen:** Arrow und Gibbard–Satterthwaite stehen nur als Hinweis in einem Satz.
- **Alles simuliert:** keine Aussage über echte Jurys oder Plattformen.

## Quellen

- Arrow, K. J. (1951): *Social Choice and Individual Values* (nicht eingesehen).
- Gibbard, A. (1973): Manipulation of voting schemes: a general result. *Econometrica* 41, 587–601 (nicht eingesehen).
- Satterthwaite, M. A. (1975): Strategy-proofness and Arrow's conditions. *Journal of Economic Theory* 10, 187–217 (nicht eingesehen).
- Kemeny, J. G. (1959): Mathematics without numbers. *Daedalus* 88, 577–591 (nicht eingesehen).
- Dawid, A. P., Skene, A. M. (1979): Maximum likelihood estimation of observer error-rates using the EM algorithm. *Journal of the Royal Statistical Society C* 28, 20–28 (nicht eingesehen).
- Chen, X., Bennett, P. N., Collins-Thompson, K., Horvitz, E. (2013): Pairwise ranking aggregation in a crowdsourced setting. *WSDM 2013* (nicht eingesehen).
- Steele, G. L., Lea, D., Flood, C. H. (2014): Fast splittable pseudorandom number generators. *OOPSLA 2014*, 453–472 (Zufallsstrom des Generators).
- **Nicht herangezogen:** Arbeiten zu Crowd-BT und zur Rater-Modellierung mit Bias und Schwere; die Zahlen dieser Demo sind Simulation.

## Tests

83 Tests, einige Minuten (die Experimente rechnen über 60 feste Läufe): Einheiten gegen Handwerte (`test_aggregate.py`: Kendall-Abstand, Borda, Median, Copeland, Kemeny, Gewichte;
`test_scenario.py`: Wahrheit, ehrliche Rangfolgen, Zufall, Manipulation, Ströme), Generator (`test_generator.py`, wortgleich), **Orakel** (`test_oracle_bewerter.py`: Kendall-Abstand gegen
scipy, Borda und Copeland gegen skalare Aufzählung, Kemeny gegen Aufzählen aller Permutationen, Eigenschaften über feste Läufe), Maße und Verdikte (`test_evaluation.py`), alle Zahlen dieses
README (`test_claims.py`), Presets, Szenario und PDF (`test_presets.py`), Laufzeit-Importe und AppTest-Rauchtests.

**Mutationstest** (`tools/oracle_mutation.py` der Website, eingeschränkt auf die drei `bwt_`-Module; schnelle Testdateien zuerst, Überlebende gegen die Claims-Tests): **103 Stellen, 87 getötet, 16 äquivalent.** Im ersten, schnellen Lauf überlebten 33 Stellen (70 getötet); 17 davon sind mit neuen Einheitentests oder gegen die Claims-Tests getötet. **Echte Lücken** waren: die Halbpunkt-Wertung bei Gleichstand in Copeland, der Median mit Gleichstand (Mittel entscheidet), die Zahl der Runden und der Rückfall auf gleiche Gewichte beim gewichteten Borda, ein Kemeny mit dem letzten Teilnehmer vorn, die Wahl des Verfahrens mit dem kleinsten Abstand im Verdikt und die Liste der Verfahren, bei denen das Ziel gewinnt; sie sind mit Tests geschlossen und einzeln getötet. **16 sind äquivalent:** die konstanten Verschiebungen in der Gleichstandszählung von Copeland (gleich für alle Teilnehmer), `<` gegen `<=` bei Rangvektoren ohne Gleichstand, die Randmasken der Teilmengen-Rechnung (die volle Menge braucht keine Erweiterung, überzählige Masken entfallen), die Richtung des Gleichstandsschlüssels in den Kemeny-Kosten (nur die Monotonie zählt), die Maske `& (2⁶⁴ − 1)` der Strom-Kennung (der Generator maskiert selbst) und `<` gegen `<=` bei stetigen Würfen.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `turnier_generator.py` | gemeinsamer Generator (wortgleich in allen Repos der Linie) |
| `bwt_aggregate.py` | Kendall-Abstand, Borda, Median, Copeland, Kemeny, gewichtetes Borda |
| `bwt_scenario.py` | Reglerwerte (`Settings`), Wahrheit, Bewerter, Manipulation |
| `bwt_evaluation.py` | Analyse, fünf Experimente über die festen Läufe, Verdikte |
| `bwt_presets.py`, `bwt_constants.py` | Permalink, Presets, Grenzen |
| `bwt_visualization.py`, `bwt_pdf_export.py` | Plotly-Abbildungen, PDF-Export |
| `tests/` | Einheiten-, Orakel-, Claims- und App-Tests |

## Bewusst nicht umgesetzt

- **Crowd-BT, Dawid–Skene und andere Modelle der Bewerter-Güte** (nur das gewichtete Borda).
- **Bewerter mit Systematik** (Strenge, Vorlieben, Erschöpfung) und **Absprachen** unter Manipulatoren über das gemeinsame Ziel hinaus.
- **Unvollständige Rangfolgen und Stufenbewertungen.**

## Lokal ausführen

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt` (enthält scipy für das Orakel) und `python -m pytest tests -q`.

Gebaut mit Streamlit, Plotly, numpy, pandas und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
