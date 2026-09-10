"""
Parity-Test der Uebersetzungsdateien (DE/EN) fuer AltMinimapVehiclenames.

Prueft:
  - Beide JSON-Dateien sind gueltiges JSON.
  - Jeder Token aus translations_de.json existiert in translations_en.json und
    umgekehrt (keine fehlenden, keine ueberzaehligen Keys).
  - Alle Token-Werte sind nicht leer (nur Label-Tokens duerfen leer sein).
  - Alle Token-Namen, die im Code (TranslationElement) verwendet werden,
    sind in beiden Sprachdateien vorhanden.
"""
import json
import os
import re
import sys

PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
TRANS_DIR = os.path.join(PROJ, "modsrc", "res", "gui",
                         "altminimapvehiclenames", "translations")
TOKENS_PY = os.path.join(PROJ, "modsrc", "altminimapvehiclenames",
                         "settings", "translations.py")

# Label-Tokens, die bewusst leer sein duerfen (verschachtelte Ueberschriften).
ALLOWED_EMPTY = {"ally-settings.label", "squad-settings.label"}

fails = []


def check(name, cond):
    print("PASS - " + name if cond else "FAIL - " + name)
    if not cond:
        fails.append(name)


def load_language(name):
    with open(os.path.join(TRANS_DIR, name), "r") as f:
        return json.load(f)


de = load_language("translations_de.json")
en = load_language("translations_en.json")
check("translations_de.json: gueltiges JSON, %d Tokens" % len(de), isinstance(de, dict))
check("translations_en.json: gueltiges JSON, %d Tokens" % len(en), isinstance(en, dict))

check("Key-Menge DE == EN", set(de.keys()) == set(en.keys()))
check("Keine fehlenden Keys in EN", set(de) - set(en) == set())
check("Keine ueberzaehligen Keys in DE", set(en) - set(de) == set())

empty_de = [k for k, v in de.items() if not v]
empty_en = [k for k, v in en.items() if not v]
check("Leere DE-Tokens nur erlaubte Labels",
      set(empty_de) <= ALLOWED_EMPTY)
check("Leere EN-Tokens nur erlaubte Labels",
      set(empty_en) <= ALLOWED_EMPTY)

# Token-Namen im Code pruefen.
code = open(TOKENS_PY, "r").read()
used_tokens = set(re.findall(r"TranslationElement\('([^']+)'\)", code))
check("Code-Tokens in DE vorhanden", used_tokens <= set(de))
check("Code-Tokens in EN vorhanden", used_tokens <= set(en))

# Konkrete Kernwerte.
check("modname DE", de.get("modname") == "AltMinimapVehiclenamesLena")
check("option.hide-on-alt DE == 'Bei ALT verstecken'",
      de.get("option.hide-on-alt") == "Bei ALT verstecken")
check("option.hide-on-alt EN == 'Hide on ALT'",
      en.get("option.hide-on-alt") == "Hide on ALT")
check("option.show-on-alt DE == 'Nur bei ALT'",
      de.get("option.show-on-alt") == "Nur bei ALT")
check("option.show-on-alt EN == 'Only on ALT'",
      en.get("option.show-on-alt") == "Only on ALT")
check("option.username DE == 'Username'", de.get("option.username") == "Username")
check("option.vehicle DE == 'Fahrzeugbezeichnung'",
      de.get("option.vehicle") == "Fahrzeugbezeichnung")
check("option.username EN == 'Username'", en.get("option.username") == "Username")
check("option.vehicle EN == 'Vehicle'", en.get("option.vehicle") == "Vehicle")
check("squad-names-no-alt.header DE",
      de.get("squad-names-no-alt.header") == "Zugmitgliedsbezeichnungsvariable Ohne ALT")
check("squad-names-alt.header DE",
      de.get("squad-names-alt.header") == "Zugmitgliedsbezeichnungsvariable Mit ALT Taste")
check("squad-names-no-alt.header EN",
      en.get("squad-names-no-alt.header") == "Squad member label variable Without ALT")
check("squad-names-alt.header EN",
      en.get("squad-names-alt.header") == "Squad member label variable With ALT key")
check("credits DE", de.get("credits.label") == "Von Lena_Kze in Deutschland erstellt. <3")

print("")
if fails:
    print("FEHLGESCHLAGEN: %d" % len(fails))
    sys.exit(1)
print("Alle Tests bestanden.")
sys.exit(0)
