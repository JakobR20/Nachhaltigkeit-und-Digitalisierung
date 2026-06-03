# 2 Stand der Technik

> Wortbudget **~600**. Aufbau: klassische Statistik → klassisches ML/Clustering →
> Deep Learning → LLM → Forschungslücke. Jede Methodenfamilie kurz, mit Beleg.

## 2.1 Anomalieerkennung in Zeitreihen — klassische Verfahren (~180 W)

- Begriff und Taxonomie der Anomalieerkennung (Punkt-, Kontext-, Kollektiv-Anomalien).
  [hier @chandola2009anomaly als Survey-Anker; @blazquezgarcia2021review für
  Zeitreihen-spezifische Taxonomie]
- **Z-Score / statistische Ausreißer** auf Residuen als einfachste, voll erklärbare Baseline.
- **STL-Dekomposition** (Saison-Trend-Zerlegung via Loess) als Vorverarbeitung, um
  Saisonalität vom Residuum zu trennen. [@cleveland1990stl]
- **Forecasting-basierte Erkennung:** Abweichung von der prognostizierten Dynamik;
  ARIMA/Box-Jenkins-Modellierung und Prädiktionsintervalle. [@box2015time; @hyndman2021forecasting]
- Überblick klassischer Detektionstechniken und Evaluations-Problematik. [@patcha2007overview]

## 2.2 Clustering und distanzbasierte Verfahren (~100 W)

- Zeitreihen-Clustering als Strukturierungs- und Diagnose-Werkzeug; Distanz zum
  Cluster-Zentrum als kontinuierliches Anomalie-Signal. [@aghabozorgi2015time]
- Übergang: Clustering hier doppelt genutzt (Peer-Gruppen für ARIMA + Segment-Diagnose) —
  Detail in Kapitel 3. [hier auf eigene Methodik vorverweisen, nicht ausführen]

## 2.3 Deep Learning für Anomalieerkennung in Energie (~150 W)

- Deep-Learning-Survey für Anomalieerkennung allgemein. [@pang2021deep; @chalapathy2019deep]
- **Autoencoder / LSTM-Encoder-Decoder:** Rekonstruktionsfehler als Anomalie-Maß.
  [@malhotra2016lstm für LSTM-Encoder-Decoder]
- **Energiekontext:** KI-basierte Anomalieerkennung im Gebäude-/Verbrauchskontext,
  aktuelle Trends und offene Punkte. [@himeur2021artificial]
- Aktueller Bewertungsstand: umfassende empirische Evaluationen zeigen, dass „bestes
  Verfahren" stark datensatzabhängig ist — Motivation für den eigenen Methodenvergleich.
  [@schmidl2022anomaly]

## 2.4 LLM-Anwendungen und strukturierte Ausgabe (~120 W)

- **Few-Shot-Prompting** als Paradigma: Aufgabenlösung über Beispiele im Prompt statt
  Fine-Tuning. [@brown2020language]
- **Lokale Open-Weight-LLMs** (Qwen 2.5) als datenschutzfreundliche, cloud-freie Option.
  [@qwen2024technical]
- **Structured Output / Constrained Decoding:** Grammatik-erzwungene JSON-Ausgabe für
  maschinell weiterverarbeitbare, schema-konforme Empfehlungen. [@willard2023efficient]
- LLM in domänenspezifischen/industriellen Anwendungen — Überblick und Grenzen.
  [@minaee2024large]

## 2.5 Forschungslücke / Positionierung (~50 W)

- Einzelmethoden, Deep-Learning-Detektoren und LLM-Anwendungen existieren je für sich;
  eine **kombinierte Pipeline** aus statistischem Ensemble + Deep-Learning-Detektor +
  lokaler LLM-Empfehlung für **KMU-Energieanwendungen** ist nicht standardmäßig vertreten.
- Hier setzt der Beitrag an (Rückbezug auf Forschungsfrage Kap. 1.3).
