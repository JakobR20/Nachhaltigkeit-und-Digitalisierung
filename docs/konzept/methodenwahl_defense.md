# Methodenwahl-Verteidigung — DatenWerKIOS Anomalieerkennung

> **Status:** durch `docs/CLAUDE_patch_v4.md` (26.05.2026) teilweise revidiert – siehe dort für aktuellen Stand.
> Konkret betroffen: die LSTM-/Deep-Learning-Position (Entscheidungen #11/#12). v4 führt den **Autoencoder (Dense + LSTM) als gleichberechtigte Hauptmethode B** im empirischen Methodenvergleich ein; der hier dokumentierte Ausschluss gilt damit nicht mehr unverändert. Dieses Dokument bleibt als **Argumentationshistorie** erhalten.

> Interne Verteidigungsgrundlage für jede methodische Entscheidung im Projekt.
> Adressatin: u. a. Marja Wahl (Data Scientist, RAUSCH) und Prof. Müßig — fachlich
> versiert, daher technisch präzise statt oberflächlich.
>
> **Format je Entscheidung:** Entscheidung · Begründung · Verworfene Alternativen ·
> Ehrliche Gegenargumente & Replik · Antizipierte Verteidigungsfragen · Literatur.
>
> Querverweise: `docs/konzept/konzept.md`, `docs/konzept/datenprofil.md`,
> Notebooks `01_eda` / `02_features` / `03_baseline_zscore`, Skills
> `smart-meter-eda` / `anomalie-methodenwahl` / `external-data-apis`.
>
> **Literaturhinweis:** Alle bibliografischen Angaben sind vor der finalen Abgabe gegen
> die Originale zu verifizieren (Jahr, Seiten, DOI). Es wurden keine Quellen erfunden;
> wo eine Referenz unsicher ist, ist das markiert.

## Inhaltsverzeichnis

- A. Scope & Daten — Entscheidungen 1, 2, 16, 17, 18
- B. Saisonzerlegung & Clustering — 3, 4, 5, 6
- C. Anomalieerkennungs-Methoden — 7, 8, 9, 10, 11, 12
- D. Handlungsempfehlungen (LLM) — 13, 14
- E. Übertragbarkeit — 15
- Literaturverzeichnis

---

# A. Scope & Daten

## 1. Hauptdatensatz Baumärkte, Validierung Handel/Lastgang_34

**Entscheidung.** Wir entwickeln und trainieren die Pipeline auf den 26 Baumarkt-Zählern (ZRV-Format, kW) und nutzen `Handel/Lastgang_34` (kWh + Status-Flag) als unabhängigen Validierungsfall.

**Begründung.**
- **Größte homogene Kohorte:** Baumärkte sind mit 26 Zählern die größte Gruppe gleichartiger Liegenschaften → erlaubt Clusterbildung und Querschnittsvergleiche, die bei Einzelzählern unmöglich wären.
- **Klare, gut interpretierbare Saisonstruktur:** ausgeprägte Öffnungszeiten-Profile (Tages-/Wochenzyklus, ACF-Peaks bei lag 24/168, siehe `01_eda`) sind ideal, um Saisonzerlegung und Forecasting methodisch sauber zu demonstrieren.
- **Lastgang_34 als methodischer Gegentest:** anderes Quellformat (kWh statt kW), anderer Zeitraum, **mit** Qualitäts-Flag (`Ersatzwert`). Damit prüfen wir, ob die Pipeline format- und einheitenrobust ist, statt sie nur auf einer homogenen Quelle zu zeigen.
- **Reproduzierbarkeit:** ein fester Hauptscope verhindert „cherry-picking" über alle Branchen hinweg.

**Verworfene Alternativen.**
- *Alle 5 Branchen gleichzeitig:* zu heterogen (Ladestationen-Lastspitzen bis 1.218 kW vs. Büro mit einem Zähler) — vermischt Methodenentwicklung mit Generalisierung und verwässert die Argumentation.
- *Nur ein einzelner Zähler:* keine Cluster-/Übertragbarkeitsaussage möglich.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „Baumärkte sind ein Sonderfall (planbare Öffnungszeiten); die Methode könnte auf unregelmäßigeren Lasten (Ladestationen) scheitern." — *Replik:* Korrekt, und genau deshalb ist die **Übertragbarkeit** (Entscheidung 15) ein eigener, ergebnisoffener Testteil; wir behaupten nicht, dass die auf Baumärkten trainierte Pipeline ungetestet auf andere Branchen läuft.
- *Gegenargument:* „Nur ein Validierungszähler ist dünn." — *Replik:* Stimmt; Lastgang_34 ist ein **Format-/Einheiten-**Test, kein statistischer Generalisierungsbeleg. Letzterer ist der branchenübergreifende Übertragbarkeitstest.

**Antizipierte Verteidigungsfragen.**
- *„Warum nicht die datenreichste Branche (Ladestationen, 26 Zähler) als Hauptscope?"* → Ladestationen haben hochvolatile, ereignisgetriebene Lastprofile mit extremer Magnituden-Spreizung; die Saison-/Forecasting-Methodik lässt sich dort weniger sauber isoliert demonstrieren. Sie sind aber ein guter Kandidat für den Übertragbarkeitstest.

**Literatur.** —

## 2. Ausschluss der flachen Zähler (Baumarkt_01, _02, _04)

**Entscheidung.** Drei Zähler mit Maximalleistung < 1 kW werden aus der Hauptanalyse ausgeschlossen (nicht gelöscht), siehe `01_eda` Block 2b und `02_features` Block 1.

**Begründung.**
- **Physikalisch unplausibel:** ein Baumarkt mit Spitzenlast < 1 kW ist betrieblich nicht plausibel (übrige Zähler: bis ~165 kW).
- **Datengenerierende Ursache unklar:** wahrscheinlichste Hypothese ist ein **Einheiten-Bug (Faktor 1000, W statt kW)**, da `× 1000` die Maxima in den plausiblen Bereich der übrigen Zähler hebt; alternativ Teilstrang-/Unterzähler oder Defekt.
- **Verzerrungsvermeidung:** normalisierte Tagesprofile dieser Zähler sind faktisch Rauschen (Division durch ~0-Varianz) → würden Clustering und Score-Verteilungen verzerren.
- **Transparenz:** Ausschluss ist dokumentiert und reversibel; die konkreten `meter_id` sind festgehalten.

**Verworfene Alternativen.**
- *Behalten und mitskalieren:* ohne Klärung der Ursache spekulativ; ein falsch angenommener Faktor 1000 würde künstliche Werte erzeugen.
- *Stilles Löschen:* verletzt Reproduzierbarkeit und DSGVO-Sorgfalt.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „Ihr werft echte Daten weg — vielleicht sind das valide Unterzähler." — *Replik:* Deshalb **ausschließen, nicht löschen**, und explizit als **offener Punkt für Marja** geführt (Standort/Einheit klären). Sobald die Ursache feststeht, können sie korrekt skaliert wieder aufgenommen werden.

**Antizipierte Verteidigungsfragen.**
- *„Schwelle 1 kW — willkürlich?"* → Sie trennt eine klar separierte Gruppe (vmax ≈ 0,1 kW) von der nächsten Größenordnung (≥ 5 kW); es gibt keine Zähler im Bereich 1–5 kW, die Wahl ist also robust gegen die genaue Schwelle.

**Literatur.** —

## 16. Würzburg als Wetter-Proxy

**Entscheidung.** Bis zur Klärung der echten Standorte (Marja-Call) nutzen wir Würzburg (DWD/Brightsky, `DEFAULT_LAT/LON` = 49.7913, 9.9534) als Wetter-Proxy.

**Begründung.**
- **Räumliche Korrelation des Wetters:** Temperatur und Großwetterlagen sind in Deutschland über mehrere hundert Kilometer stark korreliert; der Proxy verzerrt **Absolutwerte** minimal, die **zeitliche Struktur** (Tag/Nacht, Warm-/Kaltphasen) jedoch kaum.
- **Empirisch entschärft:** Wie `02_features` zeigt, ist das STL-Residuum ohnehin nahezu wetterunabhängig (median r ≈ 0,02). Der für die Anomalieerkennung genutzte Score hängt also kaum an der exakten Wetterstation.
- **Pragmatisch & reproduzierbar:** ein definierter Proxy ist besser als gar kein Wetter; Standort ist eine `.env`-Konstante, später ohne Code-Änderung austauschbar.

**Verworfene Alternativen.**
- *Auf Wetter ganz verzichten:* verschenkt ein erklärendes Feature und die Plausibilisierung (Kältetag vs. Defekt).
- *Mit Wetter warten bis Standorte bekannt:* blockiert die Pipeline-Entwicklung unnötig.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „Falscher Standort = falsche Heizgradtage." — *Replik:* Auf Tagesaggregat-Ebene zeigt sich zwar ein reales Heizsignal (median r ≈ −0,32), aber dieses landet via STL in Trend/Saison, nicht im Anomalie-Score. Der Proxy-Fehler propagiert also **nicht** in die Detektion; für eine spätere absolute Effizienzbewertung wären echte Standorte nötig — das ist ein offener Punkt.

**Antizipierte Verteidigungsfragen.**
- *„Wie groß ist der Proxy-Fehler quantitativ?"* → Nicht final quantifiziert (Standorte unbekannt); die Sensitivität ist durch die ≈0-Residuum-Korrelation aber nach oben begrenzt.

**Literatur.** —

## 17. Zielzeitzone Europe/Berlin mit expliziter DST-Regel

**Entscheidung.** Alle Reihen werden auf `Europe/Berlin` (tz-aware) gebracht; die DST-Mehrdeutigkeit wird **explizit** geregelt statt über `ambiguous='infer'`.

**Begründung.**
- **Korrektheit an DST-Wenden:** `tz_localize(..., ambiguous='infer')` von pandas funktioniert nur über genau einen Übergang und scheitert an mehrjährigen Reihen mit Lücken (Fehler „N dst switches"); es liefe faktisch immer in den lossy Fallback `ambiguous=False`.
- **Definierte Konvention:** Herbst-Rückstellung — erste (frühere) Belegung = Sommerzeit, zweite = Winterzeit; Frühjahrslücke — `nonexistent='shift_forward'`. Dokumentiert im Loader-Docstring und `datenprofil.md`.
- **Reproduzierbar & verlustfrei:** kein stilles Zusammenfallen doppelter Stunden (verifiziert: 0 doppelte Index-Paare über alle Zähler).

**Verworfene Alternativen.**
- *Naive Zeitstempel belassen:* DST-Brüche erzeugen Geister-/NaT-Zeilen beim Join mit UTC-Wetter/Preisen.
- *Alles in UTC rechnen:* erschwert die fachliche Interpretation (Öffnungszeiten sind Wanduhrzeit).

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „`ambiguous='infer'` ist Standard — warum abweichen?" — *Replik:* Es ist Standard *für Einzelübergänge*. Bei 3 Jahren mit Lücken ist es nachweislich unbrauchbar; unsere explizite Regel ist genau das, was `infer` zu tun versucht, nur robust.

**Antizipierte Verteidigungsfragen.**
- *„Wie viele Datenpunkte betrifft das überhaupt?"* → Pro Jahr eine doppelte/fehlende Stunde je Zähler — quantitativ klein, aber ein unbehandelter Bruch kann den ganzen Reindex/Join verschieben, daher die Sorgfalt.

**Literatur.** —

## 18. Zieleinheit kW (statt kWh)

**Entscheidung.** Einheitliche Zielgröße ist **Leistung in kW**; kWh-Lastgänge werden über das Messintervall umgerechnet (`kW = kWh / Intervall_h`, bei 15 min `/0,25`).

**Begründung.**
- **Mehrheitliche Quelllage:** die große Mehrzahl der Dateien (ZRV) liegt bereits in kW vor; eine Umrechnung der wenigen kWh-Lastgänge ist der kleinere Eingriff.
- **Auflösungsunabhängigkeit:** Leistung (kW) ist eine Momentangröße, unabhängig vom Aggregationsintervall — robust gegen die später nötige Resampling-Schritte (z. B. EPEX-Granularitätswechsel).
- **Direkte Interpretierbarkeit:** Lastgänge, Tagesprofile und ARIMA-Konfidenzbänder sind in kW intuitiv lesbar; der Loader normalisiert intervallabhängig (`src/eda/loader.py`).

**Verworfene Alternativen.**
- *kWh als Ziel:* Energie ist intervallabhängig; beim Mischen von 15-min- und (späteren) Stundenaggregaten fehleranfällig.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „Für Effizienz-/Kostenaussagen ist kWh die natürliche Einheit." — *Replik:* Stimmt; kWh ist jederzeit als `kW × Intervall` rekonstruierbar. Für die **Detektion** ist kW robuster, für die **Berichterstattung** (z. B. „Mehrverbrauch in kWh" im Dashboard) rechnen wir zurück.

**Antizipierte Verteidigungsfragen.**
- *„Verfälscht die Umrechnung etwas?"* → Nein, sie ist eine lineare, exakte Transformation bei bekanntem Intervall.

**Literatur.** —

---

# B. Saisonzerlegung & Clustering

## 3. STL statt (dow, hour)-Mittel zur Saisonbereinigung

**Entscheidung.** Saison/Trend werden per **STL** (Seasonal-Trend decomposition using Loess, `period=168`, robust) entfernt, nicht über ein einfaches (Wochentag, Stunde)-Mittel.

**Begründung.**
- **Explizite Trendkomponente:** über 3 Jahre ist ein Trend (z. B. Geschäftsentwicklung, Effizienzmaßnahmen) real; ein (dow,hour)-Mittel ignoriert ihn und schiebt ihn ins Residuum.
- **Robustheit:** der robuste Loess-Smoother dämpft den Einfluss von Ausreißern auf die Saisonschätzung — wichtig, weil wir Ausreißer ja gerade *suchen* und nicht in die Baseline einbacken wollen.
- **Zitierbare Standardmethode** (Cleveland et al. 1990) statt einer ad-hoc-Heuristik.
- **Empirisch validiert:** das STL-Residuum korreliert praktisch nicht mehr mit der Temperatur (median r ≈ 0,02, `02_features`) → Saison + Wetter sind sauber absorbiert, das Residuum ist die „echte" Untypischkeit.

**Verworfene Alternativen.**
- *(dow,hour)-Mittel:* einfach, aber ohne Trend, nicht robust, ohne Referenz.
- *Klassische additive/multiplikative Zerlegung (`seasonal_decompose`):* gleitender Mittelwert ist weniger ausreißerrobust und unflexibler als Loess.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „STL mit period=168 modelliert nur die Wochensaison; die Tagesform steckt mit drin, aber eine echte multi-saisonale Zerlegung (Tag *und* Woche) wäre sauberer (z. B. MSTL)." — *Replik:* Berechtigt. Der 168er-Zyklus enthält die 7 Tagesprofile, fängt die dominante Struktur also ab; MSTL ist ein sinnvoller Ausbau und in der Diskussion als Erweiterung genannt.
- *Gegenargument:* „STL kennt keine Feiertage." — *Replik:* Exakt der in `03_baseline` belegte Befund; daraus folgt nicht „STL verwerfen", sondern „Feiertage als exogene Information in die **Hauptmethode** (SARIMAX, Entscheidung 10)".

**Antizipierte Verteidigungsfragen.**
- *„Warum period=168 und nicht 24?"* → 24 würde nur die Tagessaison entfernen und die Werktag/Wochenende-Differenz im Residuum lassen; 168 erfasst beides.

**Literatur.** Cleveland et al. (1990); Hyndman & Athanasopoulos (2021, Kap. zu STL/MSTL).

## 4. k-Means statt DBSCAN für die Zähler-Cluster

**Entscheidung.** Zähler werden anhand normierter mittlerer Tagesprofile mit **k-Means** geclustert (siehe `01_eda` Block 5).

**Begründung.**
- **Form, nicht Dichte:** wir suchen *prototypische Tagesprofile* (Centroide), die später für die Cluster-Zuordnung neuer Zähler dienen — k-Means liefert genau interpretierbare Centroide.
- **Kleine, vollbesetzte Menge:** 23 Zähler ohne ausgeprägte „Noise"-Punkte (flache Zähler sind bereits ausgeschlossen) — der DBSCAN-Vorteil (Rauschpunkte als „kein Cluster") greift hier kaum.
- **Definierte Clusterzahl nötig:** für „ein ARIMA-Modell pro Cluster" brauchen wir eine feste, kleine Anzahl Cluster — k-Means liefert das direkt.

**Verworfene Alternativen.**
- *DBSCAN:* keine festen Centroide, Cluster­zahl datenabhängig, sehr sensitiv gegenüber `eps`/`minPts` in standardisierten 96-dim-Profilen; eignet sich eher zum Finden untypischer *Tage* als zum Gruppieren *Zähler*.
- *Hierarchisches Clustering:* gute Alternative (Dendrogramm), aber ohne native Centroide für die Zuordnung; als Robustheitscheck denkbar.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „k-Means nimmt sphärische, gleich große Cluster an (euklidisch) — bei Lastprofilen fragwürdig." — *Replik:* Zutreffend; wir mildern das durch **Normierung pro Profil** (Form statt Magnitude) und prüfen die Clustergüte via Silhouette. Eine korrelationsbasierte Distanz wäre ein sinnvoller Robustheitscheck (Diskussion).
- *Gegenargument:* „k-Means ist nicht deterministisch (Init)." — *Replik:* fester `random_state`, `n_init=10`.

**Antizipierte Verteidigungsfragen.**
- *„Warum nicht direkt auf den Rohprofilen clustern?"* → Dann dominiert die Magnitude (große Zähler), nicht die Form; daher Normierung — und die Magnitude wird separat betrachtet (Entscheidung 6).

**Literatur.** Lloyd (1982); MacQueen (1967); Ester et al. (1996, DBSCAN, als Kontrast).

## 5. k = 3 (begründet über Elbow + Silhouette)

**Entscheidung.** Die Clusterzahl wird **nicht** fix gesetzt, sondern über Elbow (Inertia) und Silhouette über k = 2…8 gewählt; das Maximum der Silhouette liegt bei **k = 3** (`01_eda` Block 5).

**Begründung.**
- **Datengetrieben statt angenommen:** explizite Modellselektion statt eines Bauchwerts.
- **Silhouette als Trennschärfemaß** (Rousseeuw 1987) bewertet Kohäsion vs. Separation; k=3 maximiert sie.
- **Sparsamkeit:** wenige, klar unterscheidbare Tagesprofil-Typen sind interpretierbar und tragen die „ein ARIMA-Modell pro Cluster"-Logik.

**Verworfene Alternativen.**
- *Fixes k=4 o. ä.:* explizit vermieden (kein Beleg).
- *Großes k:* überanpassend, kleine Cluster mit zu wenig Zählern für stabile ARIMA-Modelle.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „Elbow ist subjektiv, Silhouette bei nur 23 Punkten instabil." — *Replik:* Stimmt, deshalb **beide** Kriterien gemeinsam und der Plot offengelegt; k=3 ist zudem fachlich plausibel (z. B. unterschiedliche Öffnungs-/Lüftungsregime). Eine Bootstrap-Stabilitätsanalyse wäre ein sinnvoller Zusatz.
- *Gegenargument:* „Mit n=23 ist jede Clusterzahl fragil." — *Replik:* Zugestanden; daher dient das Clustering primär der **Strukturierung** (Modellsparsamkeit, Übertragbarkeit), nicht als harte wissenschaftliche Typologie.

**Antizipierte Verteidigungsfragen.**
- *„Wie robust ist k=3 gegenüber dem Zählerausschluss?"* → Sollte geprüft werden (Sensitivität gegen Ein-/Ausschluss einzelner Zähler) — offener Robustheitscheck.

**Literatur.** Rousseeuw (1987); Lloyd (1982).

## 6. Form-Cluster und Magnitude-Sicht getrennt

**Entscheidung.** Zwei separate Analysen: (B1) Form-Cluster auf **normierten** Tagesprofilen, (B2) Magnitude-Sicht (Median-Tagesenergie vs. Werktag/Wochenend-Ratio) ohne Clustering (`01_eda` Block 5).

**Begründung.**
- **Zwei orthogonale Fragen:** „Wer hat ein ähnliches *Muster*?" (Form) vs. „Wer ist groß/klein und arbeitet wann?" (Magnitude). Sie zu vermischen, lässt die Magnitude die Form dominieren.
- **Beide sind für die Anomalieerkennung relevant:** Form steuert die Cluster-/ARIMA-Zuordnung; Magnitude ist Kontext für Schweregrad und Plausibilisierung.
- **Interpretierbarkeit:** der Magnitude-Scatter ist ohne Cluster direkt lesbar.

**Verworfene Alternativen.**
- *Ein gemeinsames Clustering über Form + Magnitude:* Skalenmischung, schwer interpretierbar, Magnitude überlagert die Form.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „Zwei Sichten verdoppeln den Erklärungsaufwand." — *Replik:* Ja, aber sie verhindern eine klassische Fehlinterpretation (Form-Ähnlichkeit ≠ Größen-Ähnlichkeit) und sind je für sich knapp.

**Antizipierte Verteidigungsfragen.**
- *„Sollte die Magnitude nicht ins Modell?"* → Sie geht über die zählerindividuelle Standardisierung (Z-Score/ARIMA pro Zähler) implizit ein; die getrennte Sicht dient der Exploration/Argumentation.

**Literatur.** —

---

# C. Anomalieerkennungs-Methoden

## 7. Z-Score als Baseline — warum überhaupt eine Baseline?

**Entscheidung.** Wir implementieren zuerst eine bewusst simple Z-Score-Baseline auf dem STL-Residuum (`03_baseline_zscore`), bevor die Hauptmethode kommt.

**Begründung.**
- **Vergleichsmaßstab:** eine komplexe Methode ist nur dann gerechtfertigt, wenn sie eine einfache, voll erklärbare schlägt — sonst Overengineering. Die Baseline definiert die Messlatte.
- **Erkenntnisgewinn vor Modellierung:** die Baseline hat empirisch die zentralen Eigenschaften der Daten aufgedeckt (fat tails 2,84 % vs. 0,27 %; Top-10 = Feiertage; Heteroskedastizität) — das motiviert die Hauptmethode datenbasiert statt aus dem Lehrbuch.
- **Wissenschaftliche Redlichkeit:** „simpel zuerst" ist methodischer Standard und entspricht dem Projekt-Skill `anomalie-methodenwahl` (Stufe 0).

**Verworfene Alternativen.**
- *Direkt mit der komplexen Methode starten:* kein Vergleichswert, keine Rechtfertigung des Mehraufwands.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „Eine Baseline, die fast nur Feiertage findet, ist nutzlos." — *Replik:* Als *Detektor* begrenzt — als *Diagnoseinstrument* sehr wertvoll: genau dieser „Fehlschlag" liefert die vier konkreten Anforderungen an die Hauptmethode (L1–L4 in `konzept.md` §8).

**Antizipierte Verteidigungsfragen.**
- *„Ist die Baseline nur Pflichtübung?"* → Nein; sie hat die Methodenwahl (SARIMAX mit Feiertags-Exogen) empirisch begründet.

**Literatur.** Hyndman & Athanasopoulos (2021).

## 8. Globaler statt rollender Z-Score

**Entscheidung.** Der Z-Score wird **global** über die volle Historie je Zähler berechnet, nicht in einem rollenden Fenster.

**Begründung.**
- **Trend ist bereits raus:** STL hat den Trend entfernt; das Hauptargument für ein rollendes Fenster (Drift-Robustheit) entfällt weitgehend.
- **Maximale Einfachheit/Erklärbarkeit** für eine Baseline; 1:1 als Lehrbuch-3-Sigma zitierbar.
- **Keine Fenster-Hyperparameter** (Fensterlänge, min_periods), die die Baseline „unfair" stark machen würden.

**Verworfene Alternativen.**
- *Rollender Z-Score (z. B. 7-Tage):* robuster gegen schleichende Drift, aber führt Hyperparameter ein und verschiebt die Baseline Richtung „Methode"; gehört eher in die Vergleichsmethoden.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „Global ignoriert lokale Varianzänderungen (Heteroskedastizität)." — *Replik:* Korrekt, und das ist als Limitation L3 dokumentiert — es ist ein *bewusster* Schwachpunkt der Baseline, der die kontextabhängige Varianz der Hauptmethode motiviert. Eine Baseline soll simpel sein, nicht alle Probleme lösen.

**Antizipierte Verteidigungsfragen.**
- *„Würde ein rollender Z-Score die Feiertags-Fehlalarme reduzieren?"* → Nein — Feiertage sind irregulär und kalenderbedingt, kein Drift-Problem; ein rollendes Fenster hilft dagegen nicht. Nur Kalenderwissen (SARIMAX) hilft.

**Literatur.** —

## 9. ARIMA/SARIMAX als Hauptmethode statt Isolation Forest

**Entscheidung.** Die Hauptmethode ist ein cluster-weises (S)ARIMA(X)-Forecasting; das standardisierte Residuum/Prädiktionsintervall ist der Anomalie-Score. Isolation Forest läuft nur als Vergleichsmethode mit.

**Begründung.**
- **Zeitliche Struktur explizit:** ARIMA modelliert die Erwartung *für jeden Zeitpunkt im Kontext*; das Residuum ist per Konstruktion die „Untypischkeit für diesen Zeitpunkt" (Kontext-Anomalie). Isolation Forest behandelt Punkte als unabhängige Beobachtungen im Merkmalsraum und ignoriert Saisonalität, sofern man sie nicht künstlich als Features einbaut.
- **Erklärbarkeit:** ARIMA liefert ein Konfidenzband; „erwarteter Verlauf + Band + Ist-Wert" ist im Dashboard unmittelbar nachvollziehbar — ein IF-Score (0–1) hat keine physikalische Bedeutung. Erklärbarkeit ist im Projekt ein nicht-funktionales Pflichtmerkmal (kritische Energieinfrastruktur).
- **Konfidenzintervall = native Schwelle:** statistisch fundierte Schwelle statt heuristischer Quantil-Wahl.
- **Skalierung via Clustering gelöst:** ein Modell pro Cluster statt pro Zähler (Entscheidung 15).

**Verworfene Alternativen.**
- *Isolation Forest als Hauptmethode:* stark bei vielen heterogenen Features ohne dominante Zeitstruktur — hier liegt aber eine **dominante Zeitstruktur** vor; daher nur als Vergleich.
- *Reines STL-Residuum + Schwelle (= Baseline):* an L1–L4 gescheitert.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „ARIMA skaliert schlecht bei vielen Zählern und nimmt Stationarität an." — *Replik:* Skalierung durch Cluster-Modelle adressiert; Stationarität durch Differenzierung/Saisondifferenzierung (das ‚I' bzw. saisonales ‚I'); Reststruktur per ACF/PACF und Residualdiagnostik prüfen.
- *Gegenargument:* „Isolation Forest ist schneller und annahmefrei." — *Replik:* Stimmt, aber um den Preis fehlender Erklärbarkeit und Zeitkontext. Wir führen ihn als Vergleich, um genau diesen Trade-off zu zeigen, statt ihn zu behaupten.
- *Gegenargument:* „Klassische Punkt-Residuen erkennen keine kollektiven Anomalien (mehrstündige Plateaus)." — *Replik:* Berechtigt (Baseline-L4); ARIMA-Residuen über aufeinanderfolgende Schritte bzw. eine Aggregation des Scores über Fenster adressieren das — als Erweiterung benannt.

**Antizipierte Verteidigungsfragen.**
- *„Warum nicht Isolation Forest *mit* Zeit-Features (hour, dow, lag)?"* → Möglich und genau der Vergleichsaufbau; er bleibt aber eine statische Dichteschätzung ohne Konfidenzband — der Erklärbarkeitsnachteil bleibt.
- *„SARIMA vs. Prophet?"* → Prophet ist bequem, aber stärker black-box bei der Komponenten-Kalibrierung; SARIMAX mit exogenen Regressoren ist transparenter und statistisch fundierter.

**Literatur.** Box & Jenkins (1970); Liu et al. (2008, Isolation Forest); Hyndman & Athanasopoulos (2021).

## 10. SARIMAX mit Feiertags-Exogen (motiviert durch Baseline-Befund)

**Entscheidung.** Die Hauptmethode nutzt **SARIMAX** mit `is_holiday` (und ggf. Kalender-/Wetter-Regressoren) als exogener Variable.

**Begründung.**
- **Direkt datenmotiviert:** die Baseline zeigte, dass *alle* Top-10-Anomalien Feiertage/Schließtage sind (negative Residuen), weil STL irreguläre Kalenderereignisse nicht lernt. Ein exogener Feiertagsregressor adressiert genau diese systematische Fehlerquelle.
- **Features liegen bereit:** `is_holiday` plus alle 16 Bundesländer in `features.parquet` (`02_features`), umschaltbar sobald Standorte bekannt sind.
- **Erklärbar:** der exogene Effekt ist als Koeffizient quantifizierbar („Feiertag senkt die erwartete Last um X kW").

**Verworfene Alternativen.**
- *Feiertage nachträglich aus den Ergebnissen filtern:* heilt das Symptom, nicht das Modell; der Score bliebe an Feiertagen unbrauchbar.
- *Feiertage ignorieren:* reproduziert den Baseline-Fehler.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „Feiertage variieren je Bundesland — ohne Standort ist das exogene Signal unsicher." — *Replik:* Bundesweite Feiertage (die wirkungsstärksten Schließtage: Weihnachten, Ostermontag, Einheitstag) sind unstrittig; landesspezifische sind vorbereitet und nach Marja-Klärung aktivierbar. Heilige Drei Könige (in unseren Top-10) deutet bereits auf Süddeutschland/Bayern hin — konsistent mit dem Würzburg-Proxy.
- *Gegenargument:* „Exogene Regressoren erhöhen die Overfitting-Gefahr." — *Replik:* `is_holiday` ist ein einzelner, fachlich begründeter Binärregressor — geringes Overfitting-Risiko, hohe Erklärkraft.

**Antizipierte Verteidigungsfragen.**
- *„Warum nicht auch Ferien/verkaufsoffene Sonntage?"* → Sinnvolle Erweiterung; zunächst der dominante Effekt (Feiertage), dann iterativ.

**Literatur.** Box & Jenkins (1970); Hyndman & Athanasopoulos (2021, dynamische Regression).

## 11. Kein LSTM(-Autoencoder)

**Entscheidung.** Wir setzen **kein** rekurrentes Deep-Learning-Modell ein.

**Begründung.**
- **Erklärbarkeit:** ein LSTM-Autoencoder-Rekonstruktionsfehler ist schwer einem Betreiber zu erklären — Konflikt mit dem nicht-funktionalen Pflichtmerkmal.
- **Datenmenge/Aufwand-Nutzen:** kein Labelsatz, hoher Tuning- und Rechenaufwand; klassische Verfahren lösen die dominante (saisonale) Struktur bereits gut.
- **Wissenschaftlicher Rahmen:** Master-Hausarbeit mit Fokus Methodenvielfalt + Begründung, nicht maximale Detektionsrate.

**Verworfene Alternativen.**
- *LSTM-Autoencoder:* erst zu rechtfertigen, wenn Stufe 0–4 nachweislich scheitern (Skill `anomalie-methodenwahl`, Stufe 5).

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „LSTMs erfassen nichtlineare, langreichweitige Muster, die ARIMA entgehen." — *Replik:* Zutreffend für komplexe multivariate Lasten; bei den stark saisonal-strukturierten Baumarktlasten ist der Mehrwert fraglich und der Erklärbarkeitsverlust real. Wir nennen es als Ausblick, nicht als Verzicht aus Bequemlichkeit.

**Antizipierte Verteidigungsfragen.**
- *„Habt ihr es getestet?"* → Bewusst nicht implementiert; die Begründung ist methodisch (Erklärbarkeit + Aufwand-Nutzen), nicht „keine Zeit".

**Literatur.** Malhotra et al. (2016, LSTM-Encoder-Decoder).

## 12. Kein Foundation Model (Chronos, TimeRCD, TranAD)

**Entscheidung.** Zeitreihen-Foundation-/Transformer-Modelle werden **diskutiert, aber nicht implementiert**.

**Begründung.**
- **Erklärbarkeit als Ausschlusskriterium:** Foundation Models sind Black Boxes; in kritischer Energieinfrastruktur muss ein Alarm nachvollziehbar und verantwortbar sein.
- **Betriebs-Footprint:** großes Modellgewicht/Compute steht im Widerspruch zur lokalen, ressourcenschonenden Verarbeitung (vgl. Entscheidungen 13/14).
- **Aufwand-Nutzen:** ohne Labels und mit dominanter Saisonstruktur ist der erwartete Mehrwert gegenüber SARIMAX gering, der Erklärbarkeitsverlust hoch.

**Verworfene Alternativen.**
- *Chronos (Ansari et al. 2024)* (Zero-/Few-Shot-Forecasting), *TranAD (Tuli et al. 2022)* (Transformer-Anomalieerkennung), *TimeRCD/THEMIS* — als State-of-the-Art referenziert, nicht eingesetzt.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „Chronos braucht kein Training und ist oft sehr stark — warum nicht wenigstens als Vergleich?" — *Replik:* Fairer Punkt; als *Vergleichsbenchmark* (nicht als Produktivkomponente) wäre Chronos ein legitimer Ausbau und ist als solcher in der Diskussion benannt. Gegen den **produktiven** Einsatz spricht die Erklärbarkeit.
- *Gegenargument:* „Erklärbarkeit von Transformern verbessert sich (Attention, SHAP)." — *Replik:* Diese Erklärungen sind post-hoc und für Betreiber selten intuitiv; ein ARIMA-Konfidenzband ist direkt verständlich.

**Antizipierte Verteidigungsfragen.**
- *„Ist ‚Erklärbarkeit' nicht ein Vorwand, um Aufwand zu sparen?"* → Es ist ein dokumentiertes, im Energiekontext anerkanntes nicht-funktionales Requirement; zudem zeigen wir mit dem mehrstufigen Vorgehen, dass wir die Alternativen kennen und bewusst abwägen.

**Literatur.** Ansari et al. (2024, Chronos); Tuli et al. (2022, TranAD). *TimeRCD/THEMIS: genaue Referenzen vor Abgabe ergänzen/verifizieren.*

---

# D. Handlungsempfehlungen (LLM)

## 13. LLM lokal via Ollama statt Cloud-API

**Entscheidung.** Handlungsempfehlungen werden von einem **lokalen** LLM via Ollama erzeugt, nicht über eine Cloud-API.

**Begründung.**
- **DSGVO/Datenschutz:** Smart-Meter-Daten sind personenbeziehbar (Verbrauchsmuster lassen Rückschlüsse auf Anwesenheit/Betrieb zu); lokale Verarbeitung vermeidet jeden Cloud-Datenabfluss.
- **Reproduzierbarkeit & Kosten:** feste lokale Modelle, keine API-Drift, keine laufenden Kosten, offline lauffähig.
- **Kontrollierbarkeit:** Modell, Version und Prompt sind vollständig in unserer Hand.

**Verworfene Alternativen.**
- *Cloud-LLM (z. B. GPT-/Claude-API):* höhere Sprachqualität, aber Datenschutz-/Compliance-Risiko und externe Abhängigkeit.

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „Man könnte anonymisiert/aggregiert an die Cloud senden." — *Replik:* Möglich, aber Anonymisierung von Lastzeitreihen ist nichttrivial (Re-Identifikation über Muster); lokal zu bleiben ist die konservative, im Energiekontext gut begründbare Wahl.
- *Gegenargument:* „Lokale 3B-Modelle sind sprachlich schwächer." — *Replik:* Zutreffend (siehe Entscheidung 14); durch erzwungenes Ausgabeformat (Structured Outputs) und enge Prompts ist die Aufgabe aber eng gefasst.

**Antizipierte Verteidigungsfragen.**
- *„Ist das LLM sicherheitskritisch?"* → Nein — es **erklärt/empfiehlt**, entscheidet nicht autonom; regelbasierte Leitplanken + strukturierter Output begrenzen das Risiko.

**Literatur.** McKenna et al. (2012); Asghar et al. (2017, Smart-Meter-Datenschutz).

## 14. LLM-Modellgröße: 3B (Llama 3.2) statt 7B

**Entscheidung.** Wir nutzen **Llama 3.2 3B** (statt eines 7B-Modells) als lokales Empfehlungs-LLM.

**Begründung.**
- **Format wird erzwungen, nicht ‚erhofft':** Ollama Structured Outputs (JSON-Schema, constrained decoding auf Token-Ebene) garantiert das Ausgabeformat **modellunabhängig** — der Hauptgrund für ein größeres Modell (zuverlässige Strukturtreue) entfällt weitgehend.
- **Footprint/Geschwindigkeit:** 3B passt in ~2–3 GB (Q4), läuft auf M-Series-MacBooks deutlich schneller und mit geringerem RAM — passend zu „lokal, ressourcenschonend".
- **Enge Aufgabe:** kurze, schemagebundene Empfehlungs-Karten (Schweregrad, Vermutung, Maßnahme) aus strukturiertem Kontext — kein freier Langtext, der ein großes Modell erfordern würde.

**Verworfene Alternativen.**
- *Qwen2.5 7B / Llama 3.1 8B:* sprachlich/benchmarktechnisch stärker, aber für die enge, formatgebundene Aufgabe überdimensioniert und schwerer im Footprint. (Hinweis: die frühere Doku nannte 7B; `konzept.md` 5.3 und der Skill werden auf 3B angeglichen.)

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument (ernst zu nehmen):* „3B-Modelle sind in **deutscher** Fachsprache und im logischen Schließen spürbar schwächer; Empfehlungen könnten generisch oder fehlerhaft sein." — *Replik:* Bewusster Trade-off. Mitigation: (a) strenges JSON-Schema, (b) Kontext wird vom System geliefert (Zähler, Zeit, Abweichung, Wetter/Feiertag), das LLM formuliert nur, (c) regelbasierte Plausibilitätsprüfung der Felder, (d) bei Bedarf ist ein größeres Modell ein einzeiliger Ollama-Tausch. Wir werden die Empfehlungsqualität qualitativ prüfen und den Trade-off offen berichten.
- *Gegenargument:* „Warum nicht ein deutsch-optimiertes 7B (z. B. ein EM-German-Derivat)?" — *Replik:* Legitim; für den Prototyp priorisieren wir Footprint + erzwungenes Format. Ein deutsch-spezialisiertes Modell ist ein klar benannter Ausbaupfad.

**Antizipierte Verteidigungsfragen.**
- *„Habt ihr 3B vs. 7B empirisch verglichen?"* → Im Prototyp-Stadium nicht systematisch; die Wahl ist durch die Aufgabencharakteristik (formatgebunden, kontextgespeist) begründet, und ein Vergleich ist als Evaluationsschritt vorgesehen.

**Literatur.** —

---

# E. Übertragbarkeit

## 15. Cluster-basierte Übertragbarkeit statt pro-Zähler-Training

**Entscheidung.** Eine neue Liegenschaft/Branche wird über ihr mittleres Tagesprofil einem bestehenden Cluster-Centroid zugeordnet und nutzt dessen ARIMA-Modell; nur bei zu großer Distanz folgt Warnung „neues Cluster nötig" bzw. ein Default-Modell. Kein Training pro Einzelzähler.

**Begründung.**
- **Skalierbarkeit:** ein Modell pro Cluster (statt pro Zähler) ist sparsam, schneller und weniger überanpassungsanfällig bei kurzen Reihen.
- **Echte Übertragbarkeit ohne Retraining:** adressiert Teil (a) der Forschungsfrage („ohne pro-Standort-Training übertragbar").
- **Eingebaute Selbstkontrolle:** die Distanz-zum-Centroid liefert ein Maß, *ob* die Übertragung überhaupt zulässig ist — ehrlicher als blindes Anwenden.

**Verworfene Alternativen.**
- *Pro-Zähler-Training:* genauer pro Zähler, aber nicht übertragbar und teuer; widerspricht der Forschungsfrage.
- *Ein globales Modell für alle:* ignoriert die belegte Heterogenität der Profile (k=3).

**Ehrliche Gegenargumente & Replik.**
- *Gegenargument:* „Cluster-Centroide aus Baumärkten passen vielleicht auf keine andere Branche — dann trägt nichts." — *Replik:* Genau deshalb ist der Übertragbarkeitstest **ergebnisoffen** formuliert („Wie weit trägt die Cluster-Zuordnung?") und nicht als Behauptung. Ein Negativergebnis („Fremdbranche braucht eigenes Cluster") ist ein verwertbares Resultat.
- *Gegenargument:* „Ein Cluster-Mittelmodell ist pro Zähler suboptimal." — *Replik:* Zugestanden; wir tauschen etwas zählerindividuelle Genauigkeit gegen Übertragbarkeit und Sparsamkeit — ein bewusster, benannter Trade-off.

**Antizipierte Verteidigungsfragen.**
- *„Wie wird die Distanzschwelle gesetzt?"* → Datengetrieben aus der Intra-Cluster-Distanzverteilung der Trainingszähler (z. B. oberes Quantil); offen und im Übertragbarkeitstest zu kalibrieren.

**Literatur.** Lloyd (1982); Rousseeuw (1987).

---

# Literaturverzeichnis (APA — vor Abgabe verifizieren)

- Ansari, A. F., Stella, L., Türkmen, C., et al. (2024). *Chronos: Learning the language of time series.* arXiv:2403.07815.
- Asghar, M. R., Dán, G., Miorandi, D., & Chlamtac, I. (2017). Smart meter data privacy: A survey. *IEEE Communications Surveys & Tutorials, 19*(4), 2820–2835.
- Box, G. E. P., & Jenkins, G. M. (1970). *Time series analysis: Forecasting and control.* Holden-Day.
- Cleveland, R. B., Cleveland, W. S., McRae, J. E., & Terpenning, I. (1990). STL: A seasonal-trend decomposition procedure based on loess. *Journal of Official Statistics, 6*(1), 3–73.
- Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. *KDD-96*, 226–231.
- Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and practice* (3rd ed.). OTexts.
- Liu, F. T., Ting, K. M., & Zhou, Z.-H. (2008). Isolation Forest. *ICDM 2008*, 413–422.
- Lloyd, S. P. (1982). Least squares quantization in PCM. *IEEE Transactions on Information Theory, 28*(2), 129–137.
- MacQueen, J. (1967). Some methods for classification and analysis of multivariate observations. *Proc. 5th Berkeley Symposium on Mathematical Statistics and Probability, 1*, 281–297.
- Malhotra, P., Ramakrishnan, A., Anand, G., Vig, L., Agarwal, P., & Shroff, G. (2016). LSTM-based encoder-decoder for multi-sensor anomaly detection. *ICML Anomaly Detection Workshop.*
- McKenna, E., Richardson, I., & Thomson, M. (2012). Smart meter data: Balancing consumer privacy concerns with legitimate applications. *Energy Policy, 41*, 807–814.
- Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics, 20*, 53–65.
- Tuli, S., Casale, G., & Jennings, N. R. (2022). TranAD: Deep transformer networks for anomaly detection in multivariate time series data. *Proc. VLDB Endowment, 15*(6), 1201–1214.
- *TimeRCD, THEMIS: Referenzen vor Abgabe ergänzen und verifizieren.*
