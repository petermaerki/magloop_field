## Umbau auf elliptische Integrale

Die aktuelle H-Feld-Berechnung ist im Wesentlichen für Punkte mit größerem Abstand von der Magnetic Loop geeignet. Ziel ist eine exakte, analytische Lösung auf Basis der geschlossenen Biot-Savart-Form mit elliptischen Integralen, damit Nah- und Fernfeld konsistent berechnet werden.

## Aufgabe

Implementiere die exakte magnetische Feldberechnung einer kreisförmigen Magnetic Loop mit elliptischen Integralen.

### Eingangsgrößen

- Magnetisches Dipolmoment `m_Am2`
- Schleifendurchmesser `D_m` (und daraus Radius `R_m = D_m/2`)
- Frequenz `f_Hz`
- Beobachtungspunkt `x_m`, `y_m`, `z_m`

### Abgeleitete Größe

- Strom aus Dipolmoment und Radius:
  `I_main_loop_A = m_Am2 / (pi * R_m^2)`

### Zu implementieren

- Primär den exakten Feldbetrag `|H|` für beliebige Punkte `x_m`, `y_m`, `z_m`
- Optional zusätzlich `Hx`, `Hy`, `Hz` nur falls für interne Plausibilisierung nötig
- Verwendung der vollständigen elliptischen Integrale 1. und 2. Art `K(k)` und `E(k)`
- Numerisch stabile und effiziente Berechnung (geeignet für WASM im Browser)

## Nahbereich am Leiter

Zur Vermeidung der Singularität direkt am idealisierten Leiter gilt:

- Abstand zur Leiterachse definieren als:
  `d_abstand_zu_wire = sqrt((rho_m - R_m)^2 + x_m^2)` mit `rho_m = sqrt(y_m^2 + z_m^2)`
- Parameter `d_min_abstand_m` einführen (Default: `0.01 m`)
- Falls `d_abstand_zu_wire < d_min_abstand_m`: Feld nicht berechnen (z. B. `NaN` zurückgeben)
- Im UI in diesem Fall klaren Hinweis anzeigen, z. B. `Too close to conductor`
- Diese Regel muss sowohl für Einzelpunkt-Berechnung als auch für Plot/Contour gelten

## Akzeptanzkriterien

- Standardwert: `d_min_abstand_m = 0.01 m`

- Für Punkte mit `d_abstand_zu_wire >= d_min_abstand_m` liefert die Funktion stabile Werte ohne numerische Singularitäten
- Für Punkte mit `d_abstand_zu_wire < d_min_abstand_m` wird kein Feldwert berechnet/angezeigt
- Fernfeldwerte bleiben mit der bisherigen Lösung kompatibel
- Alte Logik entfernen: Die 1.5D-Zentrum-Logik (gepunktete Linien im Plot) entfällt vollständig.
- Alte Warntext-Logik entfernen: Der bisherige Warntext auf Basis `r < 1.5D` entfällt.
- Neue Warntext-Logik: Warnung stattdessen ausschließlich über `d_abstand_zu_wire < d_min_abstand_m` steuern.