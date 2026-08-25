# Capacitor switch test

## Messwerte aus s1p_results (14 MHz Messreihe)

- off/off (keine zusaetzliche Kapazitaet): f0_Hz = 14089035.0
- 100p (zusaetzlich 100 pF): f1_Hz = 9545034.0
- 560p (zusaetzlich 579 pF): f2_Hz = 4901309.0

Verwendete Ergebnisdateien:
- s1p_results/20260820_0746_14MHz_off_off_14MHz_values.py
- s1p_results/20260820_0748_14MHz_100p_10MHz_values.py
- s1p_results/20260820_0750_14MHz_560p_5MHz_values.py

## Induktivitaet der Loop aus Frequenzverschiebung

Resonanzbeziehung:

f = 1 / (2 * pi * sqrt(L * C))

Mit Grundzustand (off/off) und Zusatzkapazitaet Cx gilt:

L = (1/fx^2 - 1/f0^2) / ((2*pi)^2 * Cx)

### Fall 1: Zusatzkapazitaet 100 pF

- Cx = 100e-12 F
- fx = 9545034.0 Hz
- L = 1.5041797e-06 H = 1.50418 uH

### Fall 2: Zusatzkapazitaet 579 pF

- Cx = 579e-12 F
- fx = 4901309.0 Hz
- L = 1.6007220e-06 H = 1.60072 uH

## Ergebnis

- Aus 100 pF: L = 1.504 uH
- Aus 579 pF: L = 1.601 uH
- Mittelwert: L = 1.552 uH

Die beiden Schaetzungen unterscheiden sich um ca. 6.4 %. Das ist fuer reale Schalter-/Streu-/Leitungsparasitika plausibel.

Abgeleitete Grundkapazitaet (off/off) aus f0 und L:

- aus L(100 pF): C0 = 84.84 pF
- aus L(579 pF): C0 = 79.72 pF

## Messwerte aus s1p_results (28 MHz Messreihe)

- off/off (keine zusaetzliche Kapazitaet): f0_Hz = 28178680.0
- 100p (zusaetzlich 100 pF): f1_Hz = 11447940.0
- 560p (zusaetzlich 579 pF): f2_Hz = 5095697.0

Verwendete Ergebnisdateien:
- s1p_results/20260820_0755_28MHz_off_off_28MHz_values.py
- s1p_results/20260820_0758_28MHz_100p_11MHz_values.py
- s1p_results/20260820_0759_28MHz_560p_5MHz_values.py

## Induktivitaet der Loop aus Frequenzverschiebung (28 MHz Reihe)

Gleiche Formel wie oben:

L = (1/fx^2 - 1/f0^2) / ((2*pi)^2 * Cx)

### Fall 1: Zusatzkapazitaet 100 pF

- Cx = 100e-12 F
- fx = 11447940.0 Hz
- L = 1.6137879e-06 H = 1.61379 uH

### Fall 2: Zusatzkapazitaet 579 pF

- Cx = 579e-12 F
- fx = 5095697.0 Hz
- L = 1.6297278e-06 H = 1.62973 uH

## Ergebnis (28 MHz Reihe)

- Aus 100 pF: L = 1.614 uH
- Aus 579 pF: L = 1.630 uH
- Mittelwert: L = 1.622 uH

Die beiden Schaetzungen unterscheiden sich um ca. 1.0 %.

Abgeleitete Grundkapazitaet (off/off) aus f0 und L:

- aus L(100 pF): C0 = 19.77 pF
- aus L(579 pF): C0 = 19.57 pF

## Vergleich: Falls der 100-pF Kondensator real nur 99 pF hat

Bei gleicher gemessener Frequenz gilt:

- L skaliert mit 100/99 (wird um ca. +1.01 % groesser)
- C0 skaliert mit 99/100 (wird um ca. -1.00 % kleiner)

### 14 MHz Reihe

- bisher (100 pF): L = 1.50418 uH, C0 = 84.84 pF
- mit 99 pF: L = 1.51937 uH, C0 = 83.99 pF

### 28 MHz Reihe

- bisher (100 pF): L = 1.61379 uH, C0 = 19.77 pF
- mit 99 pF: L = 1.63009 uH, C0 = 19.57 pF

Hinweis: Die 579-pF-Auswertung bleibt unveraendert.



== Aufgabe AI

bei den s1p_measurements gibt es 
*CAP_NIX.s1p
*CAP_OFF.s1p
*CAP_100P.s1p
*CAP_560P.s1p

werte aus diesen files werden für die Induktivität gebraucht. sie sollen sonst nicht in der auswertung, z.b. *.html gebraucht werden.

in das file *CAP_100P_values.py

soll neu 
L_100p_H = ...
L_560p_H = ...

L_100p_H: berechnete Induktivität aus Frequenzabweichung von *CAP_100pCAP_OFF.s1p
*CAP_100p.s1p

es werden zugeschaltet
C_100P_F = 100e-12

----
 *CAP_560P_values.py

L_560p_H
berechnete Induktivität aus Frequenzabweichung von *CAP_OFF.s1p
*CAP_560p.s1p

es werten zugeschaltet
C_560P_F = 579e-12

passe das run_0_s1p.py entsprechend an