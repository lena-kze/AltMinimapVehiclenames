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

## Stable 1.1.3

- Enthält das Gefechtslog-Feature NICHT (Verhalten wie vor 1.1.2).