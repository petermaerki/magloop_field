# H-Feld-Berechnung einer Magnetic Loop

## Überblick

Die Berechnung des Magnetfeldes einer Magnetic Loop wird in zwei physikalisch sinnvolle Bereiche gegliedert:

- Im Nahfeld wird das Feld exakt über die geschlossene Biot-Savart-Lösung mit elliptischen Integralen beschrieben.
- Im Fernfeld wird auf das retardierte Dipolmodell zurückgegriffen, das die korrekte Wellenausbreitung berücksichtigt.

Beide Ansätze fließen in ein gemeinsames Modell ein. Dadurch entsteht ein konsistentes Bild über den gesamten Raum.

## Der Übergang zwischen Nah- und Fernfeld

Der Übergang wird über den dimensionslosen Parameter $kr = 2\pi r / \lambda$ gesteuert. Dabei ist:

- $r$ der Abstand zum Beobachtungspunkt
- $\lambda$ die Wellenlänge

Damit lässt sich einordnen, ob ein Punkt eher dem Nahfeld oder dem Fernfeld zuzuordnen ist.

Die beiden Parameter für den Übergang sind:

- $kr_{near}$: Ab diesem Wert dominiert die elliptische Beschreibung (Standard: 0,3).
- $kr_{far}$: Ab diesem Wert dominiert die retardierte Beschreibung (Standard: 1,0).

Zwischen diesen beiden Werten wird ein weicher Übergang verwendet. So bleibt die Rechnung im Nahfeld präzise und im Fernfeld korrekt, ohne Sprünge in der Übergangszone.

## Was die Berechnung leistet

- eine exakte Nahfeldbeschreibung
- eine korrekte Fernfeldbeschreibung
- einen konsistenten Übergang zwischen beiden Bereichen
- stabile und verständliche Darstellungen in Plots und Konturen

## Besonderheit im unmittelbaren Nahbereich

Direkt am Leiter wäre die Rechnung singulär. Deshalb wird ein Mindestabstand verwendet. Punkte, die zu nahe an der Leiterachse liegen, werden nicht als Feldwert dargestellt. So bleibt die Darstellung stabil und numerisch sauber.

## Exakte Berechnung

Für eine noch präzisere Rechnung könnte das Feld auch mit einer vollständigen elektromagnetischen Simulation berechnet werden. Solche Verfahren sind sehr genau, aber deutlich rechenintensiver. Für solche Aufgaben kommen typischerweise Programme wie NEC, FEKO oder ähnliche Feldsolversoftware in Frage.

