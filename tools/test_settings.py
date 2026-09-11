"""
Tests fuer das Settings-Framework von AltMinimapVehiclenames (Python 3).

Das echte Paket aus modsrc/altminimapvehiclenames wird in ein temporaeres
Verzeichnis kopiert, py2->py3-transformiert und als echte Module importiert.
ResMgr, gui.modsSettingsApi und PlayerEvents werden gestubbt.

Abgedeckt:
  - ConfigParams: Registry, Defaultwerte, Modes, __call__ (enabled/disabled)
  - jsonValue/msaValue-Roundtrips aller Param-Typen
  - CONFIG_TEMPLATE: alle Platzhalter bedient, JSON-kommentarfrei parsebar
  - ConfigFile: Default-Config erzeugen, schreiben/laden (Roundtrip)
  - Migrations: Legacy-Config (ohne __version__) -> V1
  - Config-Manager: reloadSafely, persistParamsSafely, Fehlerfall
  - Translations: DE/EN laden, Cache-Reset, Fallback, Sprachwechsel
  - ModsSettingsAPI-Support: Template-Struktur, Dropdowns, Live-Language,
    onModSettingsChanged -> Config schreiben, onConfigFileReload -> MSA
  - Utils: ObservingSemaphore, clamp, toBool, toPositiveFloat, toColorTuple
"""
import json
import os
import re
import shutil
import sys
import tempfile
import types

PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
MODSRC = os.path.join(PROJ, "modsrc")
PKG_SRC = os.path.join(MODSRC, "altminimapvehiclenames")
TRANS_DIR = os.path.join(MODSRC, "res", "gui", "altminimapvehiclenames", "translations")

# py2-only Konstrukte -> py3-kompatibel (nur fuer den Testlauf).
PY2TOPY3 = [
    ("json.dumps(obj, encoding='UTF-8')", "json.dumps(obj)"),
    ("json.loads(jsonData, encoding='UTF-8')", "json.loads(jsonData)"),
    ("json.loads(raw, encoding='UTF-8')", "json.loads(raw)"),
    ("e.message", "str(e)"),
    ("filter((lambda option: option.msaValue == msaValue), self.options)",
     "[option for option in self.options if option.msaValue == msaValue]"),
    ("filter((lambda option: option.value == value), self.options)",
     "[option for option in self.options if option.value == value]"),
    (".itervalues()", ".values()"),
    (".iteritems()", ".items()"),
]


def vendor_package():
    tmp = tempfile.mkdtemp(prefix="avn_pkg_")
    pkg_base = os.path.join(tmp, os.path.basename(PKG_SRC))
    for root, _dirs, files in os.walk(PKG_SRC):
        rel = os.path.relpath(root, PKG_SRC)
        dst_root = os.path.join(pkg_base, rel) if rel != "." else pkg_base
        os.makedirs(dst_root, exist_ok=True)
        for name in files:
            if not name.endswith(".py"):
                continue
            src_path = os.path.join(root, name)
            code = open(src_path, "r").read()
            for old, new in PY2TOPY3:
                code = code.replace(old, new)
            with open(os.path.join(dst_root, name), "w") as f:
                f.write(code)
    return tmp


class _StubSection(object):
    def __init__(self, raw):
        self.asBinary = raw


class _StubResMgr(object):
    @staticmethod
    def openSection(path):
        if not path.startswith("gui/altminimapvehiclenames/translations/"):
            return None
        name = os.path.basename(path)
        fp = os.path.join(TRANS_DIR, name)
        if not os.path.isfile(fp):
            return None
        with open(fp, "r") as f:
            return _StubSection(f.read())


class FakeModsSettingsApi(object):
    def __init__(self):
        self.templates = {}
        self.updated = []

    def setModTemplate(self, linkage, template, handler):
        self.templates[linkage] = (template, handler)

    def updateModSettings(self, linkage, newSettings=None):
        self.updated.append((linkage, newSettings))


def install_stubs():
    sys.modules["ResMgr"] = _StubResMgr
    helpers = types.ModuleType("helpers")
    helpers.getClientLanguage = lambda: "de"
    sys.modules["helpers"] = helpers
    fake_msa = FakeModsSettingsApi()
    _gui = types.ModuleType("gui")
    _gui.__path__ = []
    sys.modules["gui"] = _gui
    _dialogs = types.ModuleType("gui.DialogsInterface")
    _dialogs.showDialog = lambda *a, **k: None
    sys.modules["gui.DialogsInterface"] = _dialogs
    _msa_mod = types.ModuleType("gui.modsSettingsApi")
    _msa_mod.g_modsSettingsApi = fake_msa
    sys.modules["gui.modsSettingsApi"] = _msa_mod
    return fake_msa


TMP = vendor_package()
sys.path.insert(0, TMP)
FAKE_MSA = install_stubs()

import altminimapvehiclenames.settings.config as config
import altminimapvehiclenames.settings.config_file as config_file
import altminimapvehiclenames.settings.config_param as config_param
import altminimapvehiclenames.settings.migrations as migrations
import altminimapvehiclenames.settings.translations as translations
import altminimapvehiclenames.settings as settings_mod
import altminimapvehiclenames.support.mods_settings_api_support as msa_support
import altminimapvehiclenames.utils as utils

from altminimapvehiclenames.settings import ConfigException
from altminimapvehiclenames.settings.config_param import g_configParams
from altminimapvehiclenames.settings.config_param import TeamNamesMode
from altminimapvehiclenames.settings.config_template import CONFIG_TEMPLATE
from altminimapvehiclenames.settings.translations import Tr, getTranslation


def strip_comments(raw):
    return re.sub('^ *//.*$', '', raw, flags=re.MULTILINE)


def read_config_dict(path):
    with open(path, "r") as cfg_file:
        return json.loads(strip_comments(cfg_file.read()))


def set_config_dir(tmp):
    config_file.CONFIG_FILE_DIR = tmp
    config_file.g_configFiles.config.configFilePath = os.path.join(tmp, "config.json")


def dropdown(var_name):
    for part in FAKE_MSA.templates[msa_support.modLinkage][0]["column1"]:
        if part.get("type") == "Dropdown" and part.get("varName") == var_name:
            return part
    return None


fails = []


def check(name, cond):
    print("PASS - " + name if cond else "FAIL - " + name)
    if not cond:
        fails.append(name)


def same(source, target):
    return source == target


# ----------------------------------------------------------------------
# 1) ConfigParams: Parametersliste, Defaults, Modes
# ----------------------------------------------------------------------
registered = sorted(t for t, _ in g_configParams.items())
check("Params registriert",
       registered == ["ally-names", "battle-log-mode",
                      "enabled", "enemy-names",
                      "enemy-squad-star-position", "mark-enemy-squads",
                      "squad-names", "squad-names-alt", "squad-names-no-alt"])
check("enemy-names default", same(g_configParams.enemyNames.defaultValue, "hide-on-alt"))
check("ally-names default", same(g_configParams.allyNames.defaultValue, "show-on-alt"))
check("squad-names default", same(g_configParams.squadNames.defaultValue, "always"))
check("squad-names-no-alt default", same(g_configParams.squadNamesNoAlt.defaultValue, "username"))
check("squad-names-alt default", same(g_configParams.squadNamesAlt.defaultValue, "vehicle"))
check("enabled default True", g_configParams.enabled.defaultValue is True)
check("mark-enemy-squads default True", g_configParams.markEnemySquads.defaultValue is True)
check("enemy-squad-star-position default after",
      g_configParams.enemySquadStarPosition.defaultValue == "after")
check("battle-log-mode default always", g_configParams.battleLogMode.defaultValue == "always")
check("TeamNamesMode-Konstanten",
      {TeamNamesMode.SHOW_ON_ALT, TeamNamesMode.HIDE_ON_ALT,
       TeamNamesMode.ALWAYS, TeamNamesMode.NEVER}
      == {"show-on-alt", "hide-on-alt", "always", "never"})
check("Alle Teamgruppen nutzen identische 4 Modi",
      [o.value for o in g_configParams.enemyNames.options]
      == [o.value for o in g_configParams.allyNames.options]
      == [o.value for o in g_configParams.squadNames.options]
      == ["show-on-alt", "hide-on-alt", "always", "never"])
check("Squad-Inhalt: 2 Optionen (username/vehicle)",
      [o.value for o in g_configParams.squadNamesNoAlt.options]
      == [o.value for o in g_configParams.squadNamesAlt.options]
      == ["username", "vehicle"])

# ----------------------------------------------------------------------
# 2) __call__: enabled/disabled-Verhalten (disabledValue)
# ----------------------------------------------------------------------
g_configParams.enabled.value = True
g_configParams.enemyNames.value = TeamNamesMode.HIDE_ON_ALT
check("enabled: enemyNames() = aktueller Wert",
      same(g_configParams.enemyNames(), "hide-on-alt"))
g_configParams.enabled.value = False
check("disabled: enemyNames() = disabledValue (hide-on-alt)",
      same(g_configParams.enemyNames(), "hide-on-alt"))
check("disabled: enabled() = False", g_configParams.enabled() is False)
g_configParams.enabled.value = True
resetv = g_configParams.enemyNames.value
g_configParams.enemyNames.value = TeamNamesMode.ALWAYS
check("enabled: enemyNames(always) voruebergehend",
      same(g_configParams.enemyNames(), "always"))
g_configParams.enemyNames.value = resetv

# ----------------------------------------------------------------------
# 3) jsonValue / msaValue Roundtrips (Options- und Boolean-Param)
# ----------------------------------------------------------------------
# jsonValue-Getter liefert den JSON-kodierten Wert fuer die Config-Datei;
# der Setter erwartet den rohen, aus JSON gelesenen Wert.
for token, param in g_configParams.items():
    encoded = param.jsonValue
    raw = json.loads(encoded)
    param.jsonValue = raw
check("Roundtrip jsonValue: gesetzte rohe Werte werden uebernommen",
      all(same(p.value, json.loads(p.jsonValue)) for _, p in g_configParams.items()))
for token, param in g_configParams.items():
    param.msaValue = param.msaValue
check("Roundtrip msaValue fuer alle Params stabil",
      all(same(p.value, p.fromMsaValue(p.msaValue))
          for _, p in g_configParams.items()))

enemy = g_configParams.enemyNames
check("enemy-names msa show-on-alt = 0", enemy.toMsaValue("show-on-alt") == 0)
check("enemy-names msa hide-on-alt = 1", enemy.toMsaValue("hide-on-alt") == 1)
check("enemy-names msa always = 2", enemy.toMsaValue("always") == 2)
check("enemy-names msa never = 3", enemy.toMsaValue("never") == 3)
check("enemy-names fromMsa(2) = always", same(enemy.fromMsaValue(2), "always"))
check("enemy-squad-star-position options",
      [o.value for o in g_configParams.enemySquadStarPosition.options]
      == ["before", "both", "after"])
check("enabled jsonValue True -> 'true'", same(g_configParams.enabled.jsonValue, "true"))
g_configParams.enabled.jsonValue = "false"
check("enabled jsonValue 'false' setzt value False",
      g_configParams.enabled.value is False)
g_configParams.enabled.jsonValue = True

# ----------------------------------------------------------------------
# 4) CONFIG_TEMPLATE: Platzhalter vollstaendig, JSON parsebar
# ----------------------------------------------------------------------
default_tokens = settings_mod.getDefaultConfigTokens()
check("getDefaultConfigTokens: alle 8 Tokens",
      sorted(default_tokens) == ["ally-names", "battle-log-mode", "enabled", "enemy-names", "enemy-squad-star-position", "mark-enemy-squads", "squad-names", "squad-names-alt", "squad-names-no-alt"])
missing = re.findall(r'%\(([^)]*)\)s', CONFIG_TEMPLATE)
check("Template-Platzhalter = Tokenliste", sorted(set(missing)) == sorted(default_tokens))
rendered = CONFIG_TEMPLATE % default_tokens
json.loads(strip_comments(rendered))
check("TEMPLATE + Defaults -> valid JSON (kommentarfrei)", True)
check("TEMPLATE keine Rest-Platzhalter", "%(" not in (CONFIG_TEMPLATE % default_tokens))

# ----------------------------------------------------------------------
# 5) ConfigFile: Default erzeugen, Roundtrip schreiben/laden
# ----------------------------------------------------------------------
cfg_tmp = tempfile.mkdtemp(prefix="avn_cfg_")
set_config_dir(cfg_tmp)
config_file.g_configFiles.createMissingConfigFiles()
check("Config-Datei erzeugt", config_file.g_configFiles.config.exists())
d_cfg = config_file.g_configFiles.config.loadConfigDict()
check("Default-Config: enabled", d_cfg.get("enabled") is True)
check("Default-Config: enemy-names", same(d_cfg.get("enemy-names"), "hide-on-alt"))
config_dict = read_config_dict(config_file.g_configFiles.config.configFilePath)
config_dict["enemy-names"] = "always"
config_file.g_configFiles.config.writeConfigDict(config_dict)
d2 = config_file.g_configFiles.config.loadConfigDict()
check("Roundtrip write/load: enemy-names", same(d2.get("enemy-names"), "always"))

# ----------------------------------------------------------------------
# 6) Migrations: V1 -> V2 -> V3 -> V4 -> V5
# ----------------------------------------------------------------------
legacy = {
    "enabled": True,
    "enemy-names": "always",
    "ally-names": "show-on-alt",
    "squad-names": "default",
}
legacy_json = json.dumps(legacy)
with open(config_file.g_configFiles.config.configFilePath, "w") as f:
    f.write(legacy_json)
migrations.performConfigMigrations()
d_legacy = config_file.g_configFiles.config.loadConfigDict()
check("Migration V1->V3: squad-names default -> always",
      d_legacy.get("squad-names") == "always")
check("Migration V1->V5: __version__ = 5",
      d_legacy.get("__version__") == migrations.ConfigVersion.V5)
check("Migration V1->V3: squad-names-no-alt/alt Standard",
      d_legacy.get("squad-names-no-alt") == "username"
       and d_legacy.get("squad-names-alt") == "vehicle")
check("Migration V3->V4: Platoon-Markierungen aktiv",
      d_legacy.get("mark-enemy-squads") is True)
check("Migration V4->V5: Gefechtslog-Default",
      d_legacy.get("battle-log-mode") == "always")
check("Migration V1->V3: uebrige Werte unveraendert",
      d_legacy.get("enemy-names") == "always"
       and d_legacy.get("ally-names") == "show-on-alt")
second = dict(d_legacy)
migrations.performConfigMigrations()
check("Migration idempotent (V5 bleibt)", 
      config_file.g_configFiles.config.loadConfigDict() == second)
check("isVersion(V1, 1) True",
      migrations.isVersion({"__version__": 1}, migrations.ConfigVersion.V1))
check("isVersion(ohne Version, 1) True (gilt als V1)",
      migrations.isVersion({}, migrations.ConfigVersion.V1))
check("isVersion(V3, 3) True",
      migrations.isVersion({"__version__": 3}, migrations.ConfigVersion.V3))
check("isVersion(V2, 3) False",
      not migrations.isVersion({"__version__": 2}, migrations.ConfigVersion.V3))
check("isLegacyConfig(altes Format) True",
      migrations.isLegacyConfig({"enabled": True, "enemy-names": "always",
                                 "ally-names": "never", "squad-names": "default"}))
check("isLegacyConfig(mit Version) False",
      not migrations.isLegacyConfig({"__version__": 1}))
_progress = {"enemy-names": "always"}
migrations.progressVersion(_progress)
check("progressVersion fuegt __version__ hinzu", _progress.get("__version__") == 1)

# ----------------------------------------------------------------------
# 7) Config-Manager: reloadSafely, persistParamsSafely, Fehlerfall
# ----------------------------------------------------------------------
cfg_tmp2 = tempfile.mkdtemp(prefix="avn_mgr_")
set_config_dir(cfg_tmp2)
config.g_config.reloadSafely()
check("reloadSafely erzeugt Config", config_file.g_configFiles.config.exists())
check("reloadSafely laedt Defaults",
      same(config_param.g_configParams.enemyNames.value, "hide-on-alt"))

with open(config_file.g_configFiles.config.configFilePath, "w") as f:
    f.write(json.dumps({"enemy-names": "never",
                        "enabled": True, "ally-names": "always",
                        "squad-names": "always"}))
config.g_config.reloadSafely()
check("reloadSafely uebernimmt Datei-Edit",
      same(config_param.g_configParams.enemyNames.value, "never"))
check("reloadSafely V3-Migration: squad-Inhalt Standard",
      same(config_param.g_configParams.squadNamesNoAlt.value, "username")
      and same(config_param.g_configParams.squadNamesAlt.value, "vehicle"))

config_param.g_configParams.enemyNames.value = "always"
config.g_config.persistParamsSafely()
d_persist = read_config_dict(config_file.g_configFiles.config.configFilePath)
check("persistParamsSafely schreibt Wert in Datei",
      same(d_persist.get("enemy-names"), "always"))
check("persistParamsSafely reloadt Params",
      same(config_param.g_configParams.enemyNames.value, "always"))

invalid_json_tmp = tempfile.mkdtemp(prefix="avn_bad_")
set_config_dir(invalid_json_tmp)
with open(config_file.g_configFiles.config.configFilePath, "w") as f:
    f.write("{ this is no json ")
config.g_config.reloadSafely()
check("Kaputte JSON: reloadSafely wirft nicht",
      config.g_config._Config__loadedSuccessfully is False)
try:
    config_file.g_configFiles.config.loadConfigDict()
    raised = False
except ConfigException:
    raised = True
check("Kaputte JSON: loadConfigDict wirft ConfigException", raised)

# ----------------------------------------------------------------------
# 8) Translations: DE/EN, Cache-Reset, Fallback, Sprachwechsel
# ----------------------------------------------------------------------
translations.loadTranslations("de")
check("Tr.MODNAME DE", same(Tr.MODNAME, "AltMinimapVehiclenames"))
check("Tr.OPTION_HIDE_ON_ALT DE",
      same(Tr.OPTION_HIDE_ON_ALT, "Bei ALT verstecken"))
de_modname = Tr.MODNAME
translations.loadTranslations("en")
check("Sprachwechsel: Tr.MODNAME NEU (Cache-Reset)",
      same(Tr.MODNAME, "AltMinimapVehiclenames"))
check("Tr.OPTION_HIDE_ON_ALT EN",
      same(Tr.OPTION_HIDE_ON_ALT, "Hide on ALT"))
check("getTranslation Untranslated-Token", same(getTranslation("fake.token"), "fake.token"))
check("getSupportedLanguages", translations.getSupportedLanguages() == ("de", "en"))
check("getAvailableLanguage unbekannt -> de",
      same(translations.getAvailableLanguage("fr"), "de"))
translations.loadTranslations("de")
check("reloadTranslations en -> True (Wechsel)",
      translations.reloadTranslations("en") is True)
check("reloadTranslations en erneut -> False (kein Wechsel)",
      translations.reloadTranslations("en") is False)
translations.loadTranslations("de")

lang_cfg_tmp = tempfile.mkdtemp(prefix="avn_lang_")
set_config_dir(lang_cfg_tmp)
with open(config_file.g_configFiles.config.configFilePath, "w") as f:
    f.write(json.dumps({"enabled": True}))
translations.loadTranslations(None)
check("Sprache aus Spieleinstellung gelesen",
      translations.CURRENT_LANGUAGE in ("de", "en"))
config_file.g_configFiles.config.writeConfigDict({
    "enabled": True, "enemy-names": "hide-on-alt", "ally-names": "show-on-alt",
    "squad-names": "always", "squad-names-no-alt": "username",
     "squad-names-alt": "vehicle"})
translations.loadTranslations(None)

# ----------------------------------------------------------------------
# 9) ModsSettingsAPI-Support: Template, Dropdowns, Live-Language
# ----------------------------------------------------------------------
# Frischen, gueltigen Config-State herstellen (erzeugt Default-Config).
msa_tmp = tempfile.mkdtemp(prefix="avn_msa_")
set_config_dir(msa_tmp)
config.g_config.reloadSafely()
check("MSA-Test: Default-Config geladen",
      config.g_config._Config__loadedSuccessfully is True)

msa_support.registerSoftDependencySupport()
modal, handler = FAKE_MSA.templates[msa_support.modLinkage]
check("modLinkage", same(msa_support.modLinkage, "com.github.lena.altminimapvehiclenames"))
check("modDisplayName", same(msa_support.modDisplayName, "AltMinimapVehiclenames"))
credits = [p for p in modal["column1"] if p.get("type") == "Label"][-1]
check("Credits ohne Regenbogen", credits["text"] == "Von Lena_Kze in Deutschland gemacht. <3")
check("Gegnerische-Züge-Beschriftung",
      same(Tr.MARK_ENEMY_SQUADS_HEADER, "Gegnerische Züge auf Minimap mit * markieren"))
check("Template enabled default True", modal["enabled"] is True)

def dropdown_names():
    return [p.get("varName") for p in modal["column1"] if p.get("type") == "Dropdown"]

check("Dropdowns vorhanden", sorted(dropdown_names()) ==
      sorted(["enemy-names", "ally-names", "squad-names",
              "squad-names-no-alt", "squad-names-alt", "battle-log-mode",
              "enemy-squad-star-position"]))
check("Platoon-Markierungen vorhanden",
       sorted(p.get("varName") for p in modal["column1"] if p.get("type") == "CheckBox")
       == ["mark-enemy-squads"])
check("Sternposition-Dropdown vorhanden",
      [p.get("varName") for p in modal["column1"] if p.get("type") == "Dropdown"].count("enemy-squad-star-position") == 1)
check("enemy-names 4 Optionen (DE)",
      [o["label"] for o in dropdown("enemy-names")["options"]]
      == ["Nur bei ALT", "Bei ALT verstecken", "Immer", "Nie"])
check("battle-log-mode 3 Optionen (DE)",
      [o["label"] for o in dropdown("battle-log-mode")["options"]]
      == ["Immer", "Nur bei ALT", "Nie"])
check("squad-names-no-alt 2 Optionen (DE)",
      [o["label"] for o in dropdown("squad-names-no-alt")["options"]]
      == ["Username", "Fahrzeugbezeichnung"])
check("squad-names-alt 2 Optionen (DE)",
      [o["label"] for o in dropdown("squad-names-alt")["options"]]
      == ["Username", "Fahrzeugbezeichnung"])
check("Dropdown hat Tooltip", "tooltip" in dropdown("enemy-names"))
enemy_msa_before = g_configParams.enemyNames.value

translations.loadTranslations("en")
msa_support.registerSoftDependencySupport()
modal_en, _handler_en = FAKE_MSA.templates[msa_support.modLinkage]
check("Live-Language: enemy-names Optionen EN",
      [o["label"] for o in dropdown("enemy-names")["options"]]
      == ["Only on ALT", "Hide on ALT", "Always", "Never"])
check("Live-Language: squad-names-no-alt EN",
      [o["label"] for o in dropdown("squad-names-no-alt")["options"]]
      == ["Username", "Vehicle"])
g_configParams.enemyNames.value = enemy_msa_before

# onModSettingsChanged: falsche Linkage -> ignoriert
config.g_config.reloadSafely()
g_configParams.enemyNames.value = "hide-on-alt"
d_before = read_config_dict(config_file.g_configFiles.config.configFilePath)
handler("wrong-linkage", {"enemy-names": 1})
d_after = read_config_dict(config_file.g_configFiles.config.configFilePath)
check("onModSettingsChanged false Linkage ignoriert",
      same(g_configParams.enemyNames.value, "hide-on-alt")
      and d_before == d_after)

# onModSettingsChanged: korrekte Linkage -> Config schreiben
handler(msa_support.modLinkage, {"enemy-names": 2})
d_msa = read_config_dict(config_file.g_configFiles.config.configFilePath)
check("onModSettingsChanged schreibt Datei",
      same(d_msa.get("enemy-names"), "always"))
check("onModSettingsChanged laedt Params neu",
      same(g_configParams.enemyNames.value, "always"))

# onConfigFileReload: Params -> MSA pushen
g_configParams.enemyNames.value = "hide-on-alt"
msa_support.onConfigFileReload()
linkage_pushed, pushed = FAKE_MSA.updated[-1]
check("onConfigFileReload pusht alle Tokens",
      linkage_pushed == msa_support.modLinkage
      and sorted(pushed) == sorted(["enemy-names", "ally-names", "squad-names",
                                      "squad-names-no-alt", "squad-names-alt",
                                      "mark-enemy-squads", "enemy-squad-star-position",
                                      "enabled", "battle-log-mode"]))
check("onConfigFileReload enemy-names msa 1 (hide-on-alt)",
      pushed["enemy-names"] == 1)

# ----------------------------------------------------------------------
# 10) Utils: ObservingSemaphore, clamp, toBool, toPositiveFloat, toColorTuple
# ----------------------------------------------------------------------
sem = utils.ObservingSemaphore()
check("Semaphore initial frei", not bool(sem))
with sem:
    check("Semaphore im Kontext belegt", bool(sem))
calls = []

@sem.withIgnoringLock(returnForIgnored="IGNORED")
def guarded():
    calls.append("x")
    return "OK"


check("withIgnoringLock: frei -> Aufruf", guarded() == "OK" and calls == ["x"])
with sem:
    check("withIgnoringLock: belegt -> ignoriert",
          guarded() == "IGNORED" and calls == ["x"])
check("withIgnoringLock: danach wieder frei",
      guarded() == "OK" and calls == ["x", "x"])

check("clamp(min,val,max)", settings_mod.clamp(0, 150, 100) == 100)
check("clamp unten", settings_mod.clamp(10, 5, 20) == 10)
check("toBool true", settings_mod.toBool("true") is True)
check("toBool True", settings_mod.toBool("True") is True)
check("toBool false", settings_mod.toBool("false") is False)
check("toPositiveFloat", settings_mod.toPositiveFloat("2.5") == 2.5)
check("toPositiveFloat <= 0 -> 0", settings_mod.toPositiveFloat("-1") == 0.0)
check("toColorTuple", settings_mod.toColorTuple([1, 2, 300]) == (1, 2, 255))

# ----------------------------------------------------------------------
print("")
if fails:
    print("FEHLGESCHLAGEN: %d" % len(fails))
    shutil.rmtree(TMP, ignore_errors=True)
    sys.exit(1)
print("Alle Tests bestanden.")
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0)
