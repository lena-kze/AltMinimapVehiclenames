# Gefechtslog-Feature (Battle Log) – Status

Stand: 2026-09-11

## Nightly 1.1.3: funktioniert NOCH NICHT

- Der Gefechtslog-Dropdown (Immer / Nur bei ALT / Nie) ist eingebaut, greift aber nicht:
  - Mit Einstellung **"Nur bei ALT-Taste"** wird der Kill-Log ("X zerstörte Y")
    trotzdem dauerhaft angezeigt.
  - Das Drücken der ALT-Taste hat keine Auswirkung auf die Anzeige des Logs.
- Eingesetzter Ansatz (Nightly 1.1.3): Sichtbarkeit über das
  `DamageLogPanel._setSettings`-Gate (`as_setSettingsDamageLogComponentS`)
  statt über `as_detailStatsTopS` (das die AS-Ebene nach ihrem konfigurierten
  View-Mode ignoriert). Auch dieser Weg bewirkt im Spiel NICHT das erwartete
  Ausblenden bei "Nur bei ALT".
- Die Implementierung wird **später gemeinsam** überarbeitet. Dieser Build ist
  als Teststand zu verstehen, nicht als fertiges Feature.

## Vorgehen für die Überarbeitung

- Es gibt den Git-Branch **`nightly`** (Basis: stable-Master).
  Die spätere Neuimplementierung wird auf diesem Branch entwickelt und dann
  nach master gemerged. Bis dahin läuft die 1.1.3-nightly-Referenz
  (`094eb9c`, Tag `v1.1.3-nightly`) historisch weiter.
- Ein neues Nightly-Build wird also auf `nightly` gesetzt, nicht direkt auf master.

## Stable 1.1.3 / 1.1.4

- Enthält das Gefechtslog-Feature NICHT (Verhalten wie vor 1.1.2).
- 1.1.4: neue Option "Zug-Sternchen auch bei ausgeblendeten Bezeichnungen"
  (potentiell kombinierbar mit dem späteren Battle-Log-Nightly).