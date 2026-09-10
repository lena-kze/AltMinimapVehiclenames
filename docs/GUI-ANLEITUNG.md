# FFDec (GUI)-Anleitung – AltMinimapVehiclenames

Du patchest die `battle.swf` von Hand in der FFDec-GUI (so wie früher). Davor wirf bitte einen Blick
in den fertigen Quellcode unter `src/scripts/` – dort sind alle drei Klassen bereits fertig
implementiert. Die Schritte unten sagen dir, welche Änderungen du in jeder Klasse eintragen musst.

## Zielverhalten
- **Gegner (Enemy): Namen IMMER sichtbar** (standard unabhängig von Alt)
- **Verbündete (Ally): Namen nur sichtbar, solange ALT gedrückt**
- **Spieler/-Squadman: immer sichtbar**
- Symbole (Fahrzeugmarker) bleiben immer sichtbar – die Alt-Logik steuert NUR die Textlabels.

---

## Vorbereitung

1. Starte FFDec (GUI).
2. Öffne: `patch_work/battle.swf`
   (eine 1:1-Kopie des Originals; du kannst sie jederzeit neu aus `orig/battle.swf` kopieren)
3. Navigiere zu „Scripts“-Ordner, Package:
   `net.wg.gui.battle.views.minimap`

---

## Klasse 1: MinimapEntryController

Pfad im Tree: `net.wg.gui.battle.views.minimap.MinimapEntryController`
Vollständig fertige Datei: `src/scripts/net/wg/gui/battle/views/minimap/MinimapEntryController.as`

Im Quellcode dieser Datei (compare/Oeffne die Originalversion und passe an):

1. **Neue Importe** (ganz oben zu den anderen imports):
   ```
   import flash.events.KeyboardEvent;
   import flash.ui.Keyboard;
   ```

2. **Neues statisches Feld** (direkt nach `private static var _instance:MinimapEntryController = null;`):
   ```
   private static var _altPressed:Boolean = false;
   ```

3. **Im Konstruktor** (nach `_instance = this;` bzw. am Ende des Konstruktors):
   ```
   if(App.stage != null)
   {
      App.stage.addEventListener(KeyboardEvent.KEY_DOWN,this.onKeyDownHandler);
      App.stage.addEventListener(KeyboardEvent.KEY_UP,this.onKeyUpHandler);
   }
   ```

4. **Neue statische Zugriffe + Methoden** (z.B. direkt nach dem Konstruktor / vor `get instance()`):
   ```
   public static function get isAltPressed() : Boolean
   {
      return _altPressed;
   }

   public static function setIsAltPressed(param1:Boolean) : void
   {
      if(_altPressed != param1)
      {
         _altPressed = param1;
         var _loc1_:MinimapEntryController = _instance;
         if(_loc1_ != null)
         {
            _loc1_.notifyEntriesAltChanged();
         }
      }
   }

   private function notifyEntriesAltChanged() : void
   {
      var _loc1_:IVehicleMinimapEntry = null;
      for each(_loc1_ in this._vehicleLabelsEntries)
      {
         if(_loc1_ != null)
         {
            _loc1_.onAltChanged();
         }
      }
   }

   private function onKeyDownHandler(param1:KeyboardEvent) : void
   {
      if(param1.keyCode == Keyboard.ALTERNATE)
      {
         setIsAltPressed(true);
      }
   }

   private function onKeyUpHandler(param1:KeyboardEvent) : void
   {
      if(param1.keyCode == Keyboard.ALTERNATE)
      {
         setIsAltPressed(false);
      }
   }
   ```

5. **In `dispose()`** (ganz am Anfang, bevor etwas annulliert wird) Listener entfernen:
   ```
   if(App.stage != null)
   {
      App.stage.removeEventListener(KeyboardEvent.KEY_DOWN,this.onKeyDownHandler);
      App.stage.removeEventListener(KeyboardEvent.KEY_UP,this.onKeyUpHandler);
   }
   ```

> Tipp: Du kannst die komplette `MinimapEntryController.as` aus `src/scripts/...` als Referenz
> nehmen und im FFDec die Methoden Body für Body gleich einstellen.

---

## Klasse 2: IVehicleMinimapEntry

Pfad im Tree: `net.wg.gui.battle.views.minimap.components.entries.interfaces.IVehicleMinimapEntry`
Fertige Datei: `src/scripts/.../interfaces/IVehicleMinimapEntry.as`

**Einzige Änderung:** am Ende des Interface-Körpers, nach `function updateSizeIndex(param1:int) : void;`:

```
function onAltChanged() : void;
```

---

## Klasse 3: VehicleMinimapEntry

Pfad im Tree: `net.wg.gui.battle.views.minimap.components.entries.vehicle.VehicleMinimapEntry`
Fertige Datei: `src/scripts/.../vehicle/VehicleMinimapEntry.as`

1. **Zwei statische Felder entfernen** (aktuell vorhanden):
   ```
   private static var _altPressed:Boolean = false;
   private static var _initialized:Boolean = false;
   ```
   Beide raus – die Alt-Info kommt jetzt aus `MinimapEntryController.isAltPressed`.

2. **`showVehicleHp()`** – die Zeile `_altPressed = param1;` entfernen
   (da gibt es sie nicht mehr).

3. **`updateLabelVisibilityBasedOnAlt()`** – ersetze den Rumpf durch:
   ```
   private function updateLabelVisibilityBasedOnAlt() : void
   {
      if(this._guiLabel == VehicleMarkersConstants.ENTITY_NAME_ENEMY)
      {
         this._isVehicleLabelVisible = true;
      }
      else if(this._guiLabel == VehicleMarkersConstants.ENTITY_NAME_ALLY)
      {
         this._isVehicleLabelVisible = MinimapEntryController.isAltPressed;
      }
      else if(this._guiLabel == LABEL_SQUADMAN)
      {
         this._isVehicleLabelVisible = true;
      }
      this._labelHelper.validateLabel();
      invalidate(INVALID_VEHICLE_LABEL);
   }
   ```

4. **Neue öffentliche Methode** (direkt nach `updateLabelVisibilityBasedOnAlt()`):
   ```
   public function onAltChanged() : void
   {
      this.updateLabelVisibilityBasedOnAlt();
   }
   ```

---

## Speichern & Fertigstellen

1. In FFDec: **Datei → Speichern** (Cmd+S). Dadurch wird `patch_work/battle.swf` überschrieben.
2. Optional Kontrolle: In FFDec bei `VehicleMinimapEntry` prüfen, dass `onAltChanged` existiert
   und `updateLabelVisibilityBasedOnAlt` den Enemy-Zweig `= true` enthält.
3. Im Terminal / VS Code Task: `tools/pack.sh` ausführen
   → erzeugt `build/AltMinimapVehiclenames.wotmod`.

---

## Kontrolle der fertigen .wotmod
Die .wotmod ist ein ZIP. Inhalt muss sein:
- `meta.xml`
- `res/gui/flash/battle.swf` (die gepatchte)

Diese `AltMinimapVehiclenames.wotmod` kopierst du auf den Windows-Rechner
nach `World_of_Tanks_EU/mods/<version>/` (bzw. Aslain Custom_mods) und testest.

---

## Benötigte Werkzeuge auf dem Mac (alles lokal, keine System-Vermüllung)

| Werkzeug | Installiert? | Wofür | Ort |
|---|---|---|---|
| Temurin OpenJDK 21 | ja | Lässt FFDec laufen | User-Basis |
| JPEXS FFDec | ja | GUI-Patchen der battle.swf | /Applications |
| Apache Flex SDK | **nicht nötig** (wieder entfernt) | CLI-AS3-Import war unbrauchbar | – |
| Homebrew / pyenv / Python 2.7 | nie installiert | nicht gebraucht (Ansatz B) | – |

**Hinweis:** Kein Homebrew, kein Python 2.7. Das Flex-SDK wurde entfernt. Nur Java + FFDec bleiben
– beides essenziell fürs Patchen. `~/.ffdec` ist nur die normale FFDec-Config (kein Müll).

Der FFDec-CLI-Befehl `-importScript` importiert AS3-Quellcode NICHT zuverlässig (ohne Compiler tut
er nichts, mit Flex-Compiler sucht er fälschlich `mxmlc.exe`). Darum patchen wir immer über die GUI,
nicht per CLI.

## Kompatibilität mit anderen WoT-Mods

Eine `.wotmod` überlagert Dateien im Spiel. Diese Mod liefert genau **eine** Datei:
`res/gui/flash/battle.swf`.

- ✅ **Kompatibel** mit allen Mods, die andere Dateien liefern (Python-Mods unter
  `scripts/client/...`, andere SWFs, Texturen, Sounds, XML-Konfiguration).
- ⚠️ **Nur Konflikt** mit Mods, die **ebenfalls `res/gui/flash/battle.swf`** ersetzen
  (z.B. ältere XVM-Builds, manche Minimap-Mods). Dann gewinnt genau eine Datei; es gibt keinen
  Crash, aber die „verlierende“ Mod wirkt nicht.

**Beim Testen:**
1. Zuerst ohne XVM / ohne Minimap-Mods testen, um die reine Funktion zu bestätigen.
2. Danach weitere Mods dazulegen und prüfen, ob die Minimap noch korrekt funktioniert.
3. Bei Konflikt eine der beiden `battle.swf`-ersetzenden Mods deaktivieren.
