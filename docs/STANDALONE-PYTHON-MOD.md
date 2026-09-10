# AltMinimapVehiclenames - Standalone Python-Mod (Umgeschwenkt)

Dieser Weg ersetzt den vorherigen `battle.swf`-Patch vollstaendig.
**Kein battle.swf, kein eigenes SWF** - nur ein reiner Python-Mod.

## Ziel

1. **Enemy-Fahrzeugnamen** sind auf der Minimap **IMMER** sichtbar.
2. **Ally-Fahrzeugnamen** sind nur sichtbar, solange **Alt** gedrueckt ist.
3. **Zugmitglieder (Squad/Platoon)** sind **IMMER** sichtbar und zeigen
   - **ohne Alt** den **Spielernamen**
   - **mit Alt** den **Fahrzeugnamen**
4. **Fahrzeug-Symbole (Icons)** bleiben unberuehrt (Vanilla-Verhalten).

## Technischer Ansatz (verifiziert am offiziellen Quelltext)

Basierend auf dem dekompilierten Client-Quelltext (`ref/wot-src-2.3.1.5412/`):

- Die Battle-Minimap wird von `ArenaVehiclesPlugin` gesteuert
  (`gui/Scaleform/daapi/view/battle/shared/minimap/plugins.py`).
- Pro Fahrzeug kennt Python das Team via `VehicleEntry.isEnemy()`
  (`entries.py`).
- Die Namen-Sichtbarkeit pro Fahrzeug wird per Flash-Methode
  `showVehicleName()` / `hideVehicleName()` auf jedem Entry gesetzt
  (`VehicleMinimapEntry.as`), erreichbar via `_invoke(entryID, ...)`.
- Alt erzeugt das Event `SHOW_EXTENDED_INFO` (`event.ctx['isDown']`), das
  `__handleShowExtendedInfo` empfängt.

### Gepatchte Methoden (in `ArenaVehiclesPlugin`)

| Methode | Zweck |
|---------|-------|
| `__handleShowExtendedInfo` | Original ausfuehren, danach IMMER team-abhaengige Namen anwenden (unabhaengig von der Game-Einstellung): Enemy->show, Ally->show/hide je nach Alt. Zugmitglieder immer sichtbar, abhaengig von Alt wird Spielername/Fahrzeugname per `setVehicleInfo` nachgesetzt. Alive-Entries wieder aktivieren (Icons bleiben). |
| `_setVehicleInfo` | Bei jedem (auch neu erscheinenden) Fahrzeug sofort Namen-Sichtbarkeit setzen -> Enemy-Namen bereits VOR erster Alt-Taste sichtbar; Zugmitglieder erscheinen ohne Alt sofort mit Spielername. |

## Dateien

```
modsrc/mod_altminimap_vehiclenames.py   <- Python-2.7-Quelltext (Mod)
tools/build_windows.bat                 <- Windows: kompiliert + packt + deployt
tools/pack_py.sh                        <- (macOS nur fuer Vorbereitung) packt .pyc + meta.xml in .wotmod
tools/test_mod_logic.py                 <- (Python 3) simulierter Logik-Test
ref/wot-src-2.3.1.5412/                 <- referenzierter Client-Quelltext
```

## Build & Deploy (auf Windows, ein Schritt)

Der Mac wird NUR vorbereitet (keine Installation). Python 2.7 ist laut
wgmods.dev auch fuer WoT 2.3.x weiterhin gueltig (Magic Number 0xf303).
Daher wird auf dem Windows-Rechner gebaut:

```
tools\build_windows.bat
```

Das Skript:
1. Kompiliert `modsrc\mod_altminimap_vehiclenames.py` -> `.pyc` (Python 2.7)
2. Packt eine .wotmod (ZIP ohne Kompression, via PowerShell/.NET)
3. Haengt die .wotmod direkt nach `%WOTPATH%\mods\2.3.1.3\`

NFS-konfigurierbar oben im Skript: `PYCOMPILE` (Python-2.7-Aufruf),
`WOTPATH` (Standard `J:\Wargaming\World_of_Tanks_EU`), `MODSVER`.

Alternative (manuell mit Python 2.7):
```
C:\Python27\python.exe -m py_compile modsrc\mod_altminimap_vehiclenames.py
```
erzeugt `modsrc\mod_altminimap_vehiclenames.pyc`. Danach (nur Vorbereitung)
auf macOS `./tools/pack_py.sh`.

## Installation & Test

1. `.wotmod` nach `<Client>/mods/2.3.1.3/` legen (oder in `res_mods`).
2. Log pruefen: `<Client>/python.log`. Erwartete Eintraege:
   - `[AltMinimapVehiclenames] Registriert (Kampfstart: Patch aktivieren).`
   - Beim Kampfstart: `[AltMinimapVehiclenames] Patch aktiv. ...`
   - Kampfende: `[AltMinimapVehiclenames] Patch entfernt.`
3. Im Kampf: Enemy-Namen sichtbar ohne Alt; Ally-Namen erscheinen bei gedrueckter Alt.

## Vorteil gegenueber altem battle.swf-Pfad

- Kein Eingriff in `battle.swf` (kompatibel mit Client-Updates).
- Offizieller, unterstuetzter Modding-Weg (Python method-patching).
- Kleine .wotmod (nur kompilierte .pyc + meta.xml).

## Eingesetzte offizielle API-Referenz

- `github.com/izeberg/wot-src` (dekompilierter Client, Version 2.3.1.5412)
- `wgmods.dev/docs/wot` (Python 2.7, method-patching, init/fini)

## Hinweise / Risiken

- Der Patch greift beim Kampfstart (`onAvatarBecomePlayer`) und wird beim
  Kampfende (`onAvatarBecomeNonPlayer`) entfernt. Bei futuristischen
  Client-Aenderungen an den Methodennamen muss der Mod angepasst werden.
- Die inkrementelle `python.log`-Verifikation ist der naechste Schritt zur
  Echtpruefung auf dem Windows-Rechner.
