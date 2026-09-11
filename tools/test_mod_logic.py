"""
Belastungstest fuer den AltMinimapVehiclenames-Mod (Python 3, simulierte Umgebung).

Simuliert die relevante ArenaVehiclesPlugin-API und treibt die gepatchten
Methoden aus altminimapvehiclenames/core. Prueft:
  - Default-Modi: Enemy-names (hide-on-alt), Ally (show-on-alt), Zug (default)
  - Konfigurierbare Modi: always / never pro Teamgruppe
  - setVehicleInfo: sofort team-abhaengig
  - handleShowExtendedInfo ruft Original und wendet team-abhaengig an
  - Patch install/remove inkl. name mangling
"""
import sys
import types as _t

_bigworld = _t.ModuleType("BigWorld")
_bigworld.callback = lambda delay, fn: fn()
_bigworld.cancelCallback = lambda callback: None
sys.modules["BigWorld"] = _bigworld

SRC = "modsrc/altminimapvehiclenames/core/__init__.py"
src = open(SRC).read()

# Python2->3 Shim: dict.itervalues()/iteritems() existieren in py3 nicht.
src = src.replace(".itervalues()", ".values()")
src = src.replace(".iteritems()", ".items()")


class _Handlers(object):
    def __init__(self):
        self._handlers = []
    def __iadd__(self, handler):
        self._handlers.append(handler)
        return self
    def __isub__(self, handler):
        self._handlers.remove(handler)
        return self


g_playerEvents = _t.SimpleNamespace(
    onAvatarBecomePlayer=_Handlers(),
    onAvatarBecomeNonPlayer=_Handlers(),
)

# Stub das Modul "PlayerEvents".
_pymod = _t.ModuleType("PlayerEvents")
_pymod.g_playerEvents = g_playerEvents
sys.modules["PlayerEvents"] = _pymod

# --- Stub der Settings-Params (config_param) ---
class _TeamNamesMode(object):
    SHOW_ON_ALT = 'show-on-alt'
    HIDE_ON_ALT = 'hide-on-alt'
    ALWAYS = 'always'
    NEVER = 'never'


class _SquadNameContent(object):
    USERNAME = 'username'
    VEHICLE = 'vehicle'


class _EnemySquadStarPosition(object):
    BEFORE = 'before'
    BOTH = 'both'
    AFTER = 'after'


class _FakeParam(object):
    def __init__(self, value, disabledValue=None):
        self.value = value
        self.disabledValue = disabledValue if disabledValue is not None else value
    def __call__(self):
        if not g_configParams.enabled.value:
            return self.disabledValue
        return self.value


g_configParams = _t.SimpleNamespace(
    enabled=_FakeParam(True, disabledValue=False),
    enemyNames=_FakeParam(_TeamNamesMode.HIDE_ON_ALT),
    allyNames=_FakeParam(_TeamNamesMode.SHOW_ON_ALT),
    squadNames=_FakeParam(_TeamNamesMode.ALWAYS),
    squadNamesNoAlt=_FakeParam(_SquadNameContent.USERNAME),
    squadNamesAlt=_FakeParam(_SquadNameContent.VEHICLE),
    markEnemySquads=_FakeParam(True),
    enemySquadStarPosition=_FakeParam(_EnemySquadStarPosition.AFTER),
    enemySquadStarOnly=_FakeParam(False),
)

_stubParams = _t.ModuleType("altminimapvehiclenames.settings.config_param")
_stubParams.g_configParams = g_configParams
_stubParams.TeamNamesMode = _TeamNamesMode
_stubParams.SquadNameContent = _SquadNameContent
_stubParams.EnemySquadStarPosition = _EnemySquadStarPosition

# Paquet-Stubs, damit der Core die echte Settings-Datei NICHT laedt.
_pkg = _t.ModuleType("altminimapvehiclenames")
_pkg.__path__ = []
_sys = _t.ModuleType("altminimapvehiclenames.settings")
_sys.__path__ = []
sys.modules["altminimapvehiclenames"] = _pkg
sys.modules["altminimapvehiclenames.settings"] = _sys
sys.modules["altminimapvehiclenames.settings.config_param"] = _stubParams

ns = {"g_playerEvents": g_playerEvents}
exec(compile(src, SRC, "exec"), ns)


class Entry(object):
    def __init__(self, entry_id, is_enemy, in_aoi=True, was_spotted=False):
        self.id = entry_id
        self._enemy = is_enemy
        self._in_aoi = in_aoi
        self._was_spotted = was_spotted
    def getID(self):
        return self.id
    def isEnemy(self):
        return self._enemy
    def isAlive(self):
        return True
    def isInAoI(self):
        return self._in_aoi
    def wasSpotted(self):
        return self._was_spotted


class FakePlugin(object):
    def __init__(self):
        self._entries = {}
        self.invoked = []
        self.all_invokes = []
        self.active_calls = []
        self.ctrl_calls = []
        self.orig_handle_calls = 0
        self._parentObj = _t.SimpleNamespace()
        def _as_show(v):
            self.ctrl_calls.append(v)
        self._parentObj.as_showVehiclesNameS = _as_show
    def _invoke(self, entry_id, name, *args):
        self.invoked.append((entry_id, name))
        self.all_invokes.append((entry_id, name, args))
    def _ArenaVehiclesPlugin__setActive(self, entry, active):
        self.active_calls.append((entry.getID(), active))
    def _ArenaVehiclesPlugin__handleShowExtendedInfo(self, event):
        self.orig_handle_calls += 1
    def _getGuiPropsName(self, guiProps):
        return guiProps.name
    def _getDisplayedName(self, vInfo):
        return vInfo.vehicleName
    def setSettings(self):
        self.setSettings_calls = getattr(self, 'setSettings_calls', 0) + 1
    def updateSettings(self, diff):
        self.updateSettings_calls = getattr(self, 'updateSettings_calls', 0) + 1


fails = []


def check(name, cond):
    print("PASS - " + name if cond else "FAIL - " + name)
    if not cond:
        fails.append(name)


def resetParams():
    g_configParams.enabled.value = True
    g_configParams.enemyNames.value = _TeamNamesMode.HIDE_ON_ALT
    g_configParams.allyNames.value = _TeamNamesMode.SHOW_ON_ALT
    g_configParams.squadNames.value = _TeamNamesMode.ALWAYS


resetParams()
g_configParams.enemySquadStarOnly.value = False
plugin = FakePlugin()
enemy = Entry(1, True)
ally = Entry(2, False)
plugin._entries = {1: enemy, 2: ally}

A = ns["_applyEntryNameVisibility"]
A(plugin, enemy, altPressed=False)
check("Enemy ohne Alt -> showVehicleName", plugin.invoked[-1] == (1, "showVehicleName"))
A(plugin, ally, altPressed=False)
check("Ally ohne Alt -> hideVehicleName", plugin.invoked[-1] == (2, "hideVehicleName"))
A(plugin, ally, altPressed=True)
check("Ally mit Alt -> showVehicleName", plugin.invoked[-1] == (2, "showVehicleName"))
A(plugin, enemy, altPressed=True)
check("Enemy mit Alt -> hideVehicleName", plugin.invoked[-1] == (1, "hideVehicleName"))

plugin.invoked = []
ns["_applyAllNamesVisibility"](plugin, altPressed=False)
names = [m for (_, m) in plugin.invoked]
check("Alle ohne Alt: enemy show / ally hide",
      sorted(names) == ["hideVehicleName", "showVehicleName"])

plugin.invoked = []
ns["_applyAllNamesVisibility"](plugin, altPressed=True)
names = [m for (_, m) in plugin.invoked]
check("Alle mit Alt: enemy hide / ally show",
      sorted(names) == ["hideVehicleName", "showVehicleName"])

# _patched_handleShowExtendedInfo (Alt-up Event)
bp = FakePlugin()
bp._entries = {1: Entry(1, True), 2: Entry(2, False)}
ns["_orig_handleShowExtendedInfo"] = FakePlugin._ArenaVehiclesPlugin__handleShowExtendedInfo
pw = _t.MethodType(ns["_patched_handleShowExtendedInfo"], bp)
pw(_t.SimpleNamespace(ctx={"isDown": False}))
names = [m for (_, m) in bp.invoked[-2:]]
check("handleAltUp: enemy show / ally hide",
      sorted(names) == ["hideVehicleName", "showVehicleName"])
check("handleAltUp: Original aufgerufen", bp.orig_handle_calls == 1)

# _patched_handleShowExtendedInfo (Alt-down Event: Gegner deaktivieren)
bpD = FakePlugin()
bpD._entries = {1: Entry(1, True), 2: Entry(2, False)}
pwD = _t.MethodType(ns["_patched_handleShowExtendedInfo"], bpD)
pwD(_t.SimpleNamespace(ctx={"isDown": True}))
namesD = [m for (_, m) in bpD.invoked[-2:]]
check("handleAltDown: enemy hide / ally show",
      sorted(namesD) == ["hideVehicleName", "showVehicleName"])
# Enemy-names Modus "always": Namen immer, Icons bleiben aktiv
g_configParams.enemyNames.value = _TeamNamesMode.ALWAYS
bpEA3 = FakePlugin()
bpEA3._entries = {1: Entry(1, True)}
A(bpEA3, Entry(1, True), altPressed=True)
check("enemy=always: Name auch mit Alt -> showVehicleName",
      bpEA3.invoked[-1] == (1, "showVehicleName"))

# Enemy-names Modus "never": nie Namen
g_configParams.enemyNames.value = _TeamNamesMode.NEVER
A(bpEA3, Entry(1, True), altPressed=True)
check("enemy=never: mit Alt -> hideVehicleName",
      bpEA3.invoked[-1] == (1, "hideVehicleName"))
A(bpEA3, Entry(1, True), altPressed=False)
check("enemy=never: ohne Alt -> hideVehicleName",
      bpEA3.invoked[-1] == (1, "hideVehicleName"))
bpEA4 = FakePlugin()
bpEA4._entries = {1: Entry(1, True)}
check("enemy=never: kein Enemy-Deaktivieren bei Alt (Vanilla tritt)", bpEA4.active_calls == [])

# Enemy-names Modus "show-on-alt": Name nur bei Alt
g_configParams.enemyNames.value = _TeamNamesMode.SHOW_ON_ALT
A(bpEA3, Entry(1, True), altPressed=False)
check("enemy=show-on-alt: ohne Alt -> hideVehicleName",
      bpEA3.invoked[-1] == (1, "hideVehicleName"))
A(bpEA3, Entry(1, True), altPressed=True)
check("enemy=show-on-alt: mit Alt -> showVehicleName",
      bpEA3.invoked[-1] == (1, "showVehicleName"))

# Ally-names Modus "always"/"never"
g_configParams.enemyNames.value = _TeamNamesMode.HIDE_ON_ALT
g_configParams.allyNames.value = _TeamNamesMode.ALWAYS
A(FakePlugin(), Entry(2, False), altPressed=False)
fpA = FakePlugin()
fpA._entries = {2: Entry(2, False)}
fpA.invoked = []
fpA.all_invokes = []
A(fpA, Entry(2, False), altPressed=False)
check("ally=always: ohne Alt -> showVehicleName", fpA.invoked[-1] == (2, "showVehicleName"))
g_configParams.allyNames.value = _TeamNamesMode.NEVER
fpA2 = FakePlugin()
fpA2._entries = {2: Entry(2, False)}
A(fpA2, Entry(2, False), altPressed=True)
check("ally=never: mit Alt -> hideVehicleName", fpA2.invoked[-1] == (2, "hideVehicleName"))
g_configParams.allyNames.value = _TeamNamesMode.HIDE_ON_ALT
fpA3 = FakePlugin()
fpA3._entries = {2: Entry(2, False)}
A(fpA3, Entry(2, False), altPressed=False)
check("ally=hide-on-alt: ohne Alt -> showVehicleName", fpA3.invoked[-1] == (2, "showVehicleName"))
A(fpA3, Entry(2, False), altPressed=True)
check("ally=hide-on-alt: mit Alt -> hideVehicleName", fpA3.invoked[-1] == (2, "hideVehicleName"))

# _patched_setVehicleInfo
g_configParams.allyNames.value = _TeamNamesMode.SHOW_ON_ALT
bp3 = FakePlugin()
e = Entry(3, True)
ns["_orig_setVehicleInfo"] = (
    lambda self, vehicleID, entry, vInfo, guiProps, isSpotted=False: None)
ns["_altDown"] = False
sw = _t.MethodType(ns["_patched_setVehicleInfo"], bp3)
vE = _t.SimpleNamespace(
    isSquadMan=lambda: False, vehicleType=_t.SimpleNamespace(classTag='HT-1'),
    player=_t.SimpleNamespace(name='EnemyKiller'), vehicleName='Maus')
sw(3, e, vE, _t.SimpleNamespace(isFriend=False, name='enemy'))
check("setVehicleInfo Enemy -> showVehicleName", bp3.invoked[-1] == (3, "showVehicleName"))
e4 = Entry(4, False)
bp3.invoked = []
vA = _t.SimpleNamespace(
    isSquadMan=lambda: False, vehicleType=_t.SimpleNamespace(classTag='MT-1'),
    player=_t.SimpleNamespace(name='AllyBuddy'), vehicleName='Leopard')
sw(4, e4, vA, _t.SimpleNamespace(isFriend=True, name='ally'))
check("setVehicleInfo Ally -> hideVehicleName", bp3.invoked[-1] == (4, "hideVehicleName"))

# ---------------- ZUGMITGLIEDER (Squad) ----------------
sq_veh = ns["_vehInfo"]
sq_veh.clear()
sq_veh[5] = {'isSquad': True, 'classTag': 'MT-XX', 'guiPropsName': 'squad',
             'isEnemy': False, 'isOwnSquad': True, 'isForeignSquad': False,
             'playerName': 'Lena_Kze', 'vehicleName': 'Tank-X'}

plugin5 = FakePlugin()
plugin5._entries = {5: Entry(5, False)}

ns["_applyAllNamesVisibility"](plugin5, False)
check("Zug ohne Alt: sichtbar", plugin5.invoked[-1] == (5, "showVehicleName"))

plugin5.invoked = []
plugin5.all_invokes = []
ns["_applySquadNames"](plugin5, False)
inv = [a for (i, n, a) in plugin5.all_invokes if n == "setVehicleInfo"][-1]
check("Zug ohne Alt: Name=Spielername", inv[2] == "Lena_Kze")
check("Zug ohne Alt: danach sichtbar", plugin5.invoked[-1] == (5, "showVehicleName"))

plugin5.invoked = []
plugin5.all_invokes = []
ns["_applySquadNames"](plugin5, True)
inv = [a for (i, n, a) in plugin5.all_invokes if n == "setVehicleInfo"][-1]
check("Zug mit Alt: Name=Fahrzeugname", inv[2] == "Tank-X")
check("Zug mit Alt: weiterhin sichtbar", plugin5.invoked[-1] == (5, "showVehicleName"))

# Fremder Zug: nur gegnerische Fahrzeugbezeichnung mit Stern, niemals Username.
enemySquadInfo = {'isSquad': True, 'isEnemy': True, 'isOwnSquad': False,
                  'isForeignSquad': True, 'classTag': 'HT-XX',
                  'guiPropsName': 'enemy-squad', 'playerName': 'EnemyPlayer',
                  'vehicleName': 'EnemyTank'}
ns["_vehInfo"][8] = enemySquadInfo
enemySquadPlugin = FakePlugin()
enemySquadPlugin._entries = {8: Entry(8, True)}
ns["_applySquadNames"] (enemySquadPlugin, False)
enemyNames = [a for (i, n, a) in enemySquadPlugin.all_invokes if n == "setVehicleInfo"]
check("Gegnerischer Zug: Fahrzeugname mit Stern", enemyNames[-1][2] == "EnemyTank*")
check("Gegnerischer Zug: kein Username", enemyNames[-1][2] != "EnemyPlayer")
for position, expected in ((_EnemySquadStarPosition.BEFORE, '*EnemyTank'),
                           (_EnemySquadStarPosition.BOTH, '*EnemyTank*'),
                           (_EnemySquadStarPosition.AFTER, 'EnemyTank*')):
    g_configParams.enemySquadStarPosition.value = position
    enemySquadPlugin.invoked = []
    enemySquadPlugin.all_invokes = []
    ns["_applySquadNames"](enemySquadPlugin, True)
    inv = [a for (i, n, a) in enemySquadPlugin.all_invokes if n == "setVehicleInfo"][-1]
    check("Gegnerischer Zug Sternposition %s" % position, inv[2] == expected)
g_configParams.enemySquadStarPosition.value = _EnemySquadStarPosition.AFTER

# Nur-Sternchen fuer gegnerische Zugmitglieder (enemy-squad-star-only)
g_configParams.enemySquadStarOnly.value = True
g_configParams.enemyNames.value = _TeamNamesMode.SHOW_ON_ALT
starOnlyPlugin = FakePlugin()
starOnlyPlugin._entries = {8: Entry(8, True)}
ns["_applySquadNames"](starOnlyPlugin, False)
starInv = [a for (i, n, a) in starOnlyPlugin.all_invokes if n == "setVehicleInfo"][-1]
check("Nur-Sternchen: Name ist nur '*'", starInv[2] == "*")
check("Nur-Sternchen: trotz show-on-alt ohne Alt sichtbar",
      starOnlyPlugin.invoked[-1] == (8, "showVehicleName"))
g_configParams.enemySquadStarOnly.value = False
starOffPlugin = FakePlugin()
starOffPlugin._entries = {8: Entry(8, True)}
ns["_applySquadNames"](starOffPlugin, False)
starOffInv = [a for (i, n, a) in starOffPlugin.all_invokes if n == "setVehicleInfo"][-1]
check("Nur-Sternchen aus: Rueckfall auf markieren (Stern+Name)",
      starOffInv[2] == "EnemyTank*")
g_configParams.markEnemySquads.value = False
g_configParams.enemySquadStarOnly.value = True
starNoMarkPlugin = FakePlugin()
starNoMarkPlugin._entries = {8: Entry(8, True)}
ns["_applySquadNames"](starNoMarkPlugin, False)
starNoMarkInv = [a for (i, n, a) in starNoMarkPlugin.all_invokes if n == "setVehicleInfo"][-1]
check("Nur-Sternchen auch ohne Markierung: nur '*'", starNoMarkInv[2] == "*")
g_configParams.enemySquadStarOnly.value = False
g_configParams.markEnemySquads.value = True
g_configParams.enemyNames.value = _TeamNamesMode.HIDE_ON_ALT

# _patched_setVehicleInfo: gegnerischer Zug erscheint neu, nur-Sternchen
bpSqF = FakePlugin()
eF = Entry(8, True)
vF = _t.SimpleNamespace(
    isSquadMan=lambda: True, vehicleType=_t.SimpleNamespace(classTag='HT-XX'),
    player=_t.SimpleNamespace(name='EnemyPlayer'), vehicleName='EnemyTank')
swF = _t.MethodType(ns["_patched_setVehicleInfo"], bpSqF)
ns["_altDown"] = False
g_configParams.enemySquadStarOnly.value = True
swF(8, eF, vF, _t.SimpleNamespace(isFriend=False, name='enemy'))
invF = [a for (i, n, a) in bpSqF.all_invokes if n == "setVehicleInfo"][-1]
check("setVehicleInfo gegn. Zug: nur-Sternchen Name '*'", invF[2] == "*")
check("setVehicleInfo gegn. Zug: sichtbar",
      (8, "showVehicleName") in bpSqF.invoked)
g_configParams.enemySquadStarOnly.value = False
ns["_vehInfo"].pop(8, None)

# Squad-names Modus "always" (Standard): ohne Alt Spielername, mit Alt Fahrzeugname
plugin5.invoked = []
plugin5.all_invokes = []
ns["_applySquadNames"](plugin5, False)
inv = [a for (i, n, a) in plugin5.all_invokes if n == "setVehicleInfo"][-1]
check("Zug=always ohne Alt: Name=Spielername", inv[2] == "Lena_Kze")
plugin5.invoked = []
plugin5.all_invokes = []
ns["_applySquadNames"](plugin5, True)
inv = [a for (i, n, a) in plugin5.all_invokes if n == "setVehicleInfo"][-1]
check("Zug=always mit Alt: Name=Fahrzeugname", inv[2] == "Tank-X")

# Squad-names Modus "show-on-alt": Name nur bei Alt (Fahrzeugname)
g_configParams.squadNames.value = _TeamNamesMode.SHOW_ON_ALT
plugin5.invoked = []
plugin5.all_invokes = []
ns["_applySquadNames"](plugin5, False)
check("Zug=show-on-alt ohne Alt: hideVehicleName",
      plugin5.invoked[-1] == (5, "hideVehicleName"))
plugin5.invoked = []
plugin5.all_invokes = []
ns["_applySquadNames"](plugin5, True)
inv = [a for (i, n, a) in plugin5.all_invokes if n == "setVehicleInfo"][-1]
check("Zug=show-on-alt mit Alt: Name=Fahrzeugname", inv[2] == "Tank-X")

# Squad-names Modus "hide-on-alt": ohne Alt Spielername, mit Alt ausgeblendet
g_configParams.squadNames.value = _TeamNamesMode.HIDE_ON_ALT
plugin5.invoked = []
plugin5.all_invokes = []
ns["_applySquadNames"](plugin5, False)
inv = [a for (i, n, a) in plugin5.all_invokes if n == "setVehicleInfo"][-1]
check("Zug=hide-on-alt ohne Alt: Name=Spielername", inv[2] == "Lena_Kze")
plugin5.invoked = []
plugin5.all_invokes = []
ns["_applySquadNames"](plugin5, True)
check("Zug=hide-on-alt mit Alt: hideVehicleName",
      plugin5.invoked[-1] == (5, "hideVehicleName"))

# Squad-names Modus "never": versteckt
g_configParams.squadNames.value = _TeamNamesMode.NEVER
plugin5.invoked = []
plugin5.all_invokes = []
ns["_applySquadNames"](plugin5, True)
check("Zug=never: hideVehicleName", plugin5.invoked[-1] == (5, "hideVehicleName"))
check("Zug=never: kein setVehicleInfo",
      not [a for (i, n, a) in plugin5.all_invokes if n == "setVehicleInfo"])
g_configParams.squadNames.value = _TeamNamesMode.ALWAYS

# Individueller Namens-INHALT: ohne Alt Fahrzeugbezeichnung
g_configParams.squadNamesNoAlt.value = _SquadNameContent.VEHICLE
plugin5.invoked = []
plugin5.all_invokes = []
ns["_applySquadNames"](plugin5, False)
inv = [a for (i, n, a) in plugin5.all_invokes if n == "setVehicleInfo"][-1]
check("Zug noAlt=vehicle ohne Alt: Name=Fahrzeugbezeichnung", inv[2] == "Tank-X")
g_configParams.squadNamesNoAlt.value = _SquadNameContent.USERNAME

# Individueller Namens-INHALT: mit Alt Username
g_configParams.squadNamesAlt.value = _SquadNameContent.USERNAME
plugin5.invoked = []
plugin5.all_invokes = []
ns["_applySquadNames"](plugin5, True)
inv = [a for (i, n, a) in plugin5.all_invokes if n == "setVehicleInfo"][-1]
check("Zug alt=username mit Alt: Name=Spielername", inv[2] == "Lena_Kze")
g_configParams.squadNamesAlt.value = _SquadNameContent.VEHICLE

# Beispielkombination: hide-on-alt + noAlt=vehicle -> ohne Alt Fahrzeugname
g_configParams.squadNames.value = _TeamNamesMode.HIDE_ON_ALT
g_configParams.squadNamesNoAlt.value = _SquadNameContent.VEHICLE
plugin5.invoked = []
plugin5.all_invokes = []
ns["_applySquadNames"](plugin5, False)
inv = [a for (i, n, a) in plugin5.all_invokes if n == "setVehicleInfo"][-1]
check("hide-on-alt + noAlt=vehicle: Name=Fahrzeugname", inv[2] == "Tank-X")
g_configParams.squadNames.value = _TeamNamesMode.ALWAYS
g_configParams.squadNamesNoAlt.value = _SquadNameContent.USERNAME

# normaler Ally im selben Durchlauf bleibt ohne Alt versteckt
bpMix = FakePlugin()
bpMix._entries = {2: Entry(2, False), 5: Entry(5, False)}
ns["_applyAllNamesVisibility"](bpMix, False)
names = sorted(m for (_, m) in bpMix.invoked)
check("Ohne Alt gemischt: Ally hide / Zug show",
      names == ["hideVehicleName", "showVehicleName"])

# Zug erscheint NEU OHNE Alt -> sofort Spielername
bp6 = FakePlugin()
e6 = Entry(6, False)
vSq = _t.SimpleNamespace(
    isSquadMan=lambda: True, vehicleType=_t.SimpleNamespace(classTag='LT-9'),
    player=_t.SimpleNamespace(name='Lena_Kze'), vehicleName='Scout')
sw = _t.MethodType(ns["_patched_setVehicleInfo"], bp6)
ns["_altDown"] = False
sw(6, e6, vSq, _t.SimpleNamespace(isFriend=True, name='squad'))
inv = [a for (i, n, a) in bp6.all_invokes if n == "setVehicleInfo"][-1]
check("Neuer Zug ohne Alt: sofort Spielername", inv[2] == "Lena_Kze")
check("Neuer Zug ohne Alt: sichtbar", (6, "showVehicleName") in bp6.invoked)

# Zug erscheint NEU MIT Alt -> Fahrzeugname (kein Extra-Setze mit Spielername)
bp7 = FakePlugin()
e7 = Entry(7, False)
ns["_altDown"] = True
sw = _t.MethodType(ns["_patched_setVehicleInfo"], bp7)
sw(7, e7, vSq, _t.SimpleNamespace(isFriend=True, name='squad'))
overrides = [n for (_, n, a) in bp7.all_invokes
             if n == "setVehicleInfo" and a[2] == "Lena_Kze"]
check("Neuer Zug mit Alt: kein Spielername-Ueberschreiben", not overrides)

# _patched_setActive (Staging/Reaktivierung -> Einzel-Regel NACH Original)
ns["_altDown"] = False
bpA = FakePlugin()
bpA._entries = {2: Entry(2, False)}
ns["_orig_setActive"] = FakePlugin._ArenaVehiclesPlugin__setActive
sa = _t.MethodType(ns["_patched_setActive"], bpA)
sa(Entry(2, False), True)
check("setActive Ally: zuletzt hideVehicleName",
      bpA.invoked[-1] == (2, "hideVehicleName"))
bpA2 = FakePlugin()
bpA2._entries = {1: Entry(1, True)}
sa2 = _t.MethodType(ns["_patched_setActive"], bpA2)
sa2(Entry(1, True), True)
check("setActive Enemy: zuletzt showVehicleName",
      bpA2.invoked[-1] == (1, "showVehicleName"))

# _patched_setActive waehrend drueckender Alt: neu erscheinender Gegner
# bleibt aktiv; nur die Bezeichnung folgt der Einstellung.
ns["_altDown"] = True
bpA3 = FakePlugin()
bpA3._entries = {9: Entry(9, True)}
sa3 = _t.MethodType(ns["_patched_setActive"], bpA3)
sa3(Entry(9, True), True)
check("setActive Enemy bei Alt: bleibt aktiv",
      bpA3.active_calls == [(9, True)])
ns["_altDown"] = False

# enemy=always: kein sofortiges Deaktivieren neuer Gegner bei Alt
g_configParams.enemyNames.value = _TeamNamesMode.ALWAYS
bpA4 = FakePlugin()
bpA4._entries = {9: Entry(9, True)}
sa4 = _t.MethodType(ns["_patched_setActive"], bpA4)
ns["_altDown"] = True
sa4(Entry(9, True), True)
check("enemy=always: setActive Enemy bei Alt NICHT deaktiviert",
      bpA4.active_calls == [(9, True)])
ns["_altDown"] = False
g_configParams.enemyNames.value = _TeamNamesMode.HIDE_ON_ALT

# _patched_setSettings / _patched_updateSettings
bpS = FakePlugin()
bpS._entries = {1: Entry(1, True), 2: Entry(2, False)}
ns["_orig_setSettings"] = FakePlugin.setSettings
ss = _t.MethodType(ns["_patched_setSettings"], bpS)
ss()
check("setSettings: Original aufgerufen", bpS.setSettings_calls == 1)
check("setSettings: globaler Toggle False", bpS.ctrl_calls[-1] is False)
names = [m for (_, m) in bpS.invoked[-2:]]
check("setSettings: Ally hide / Enemy show",
      sorted(names) == ["hideVehicleName", "showVehicleName"])
bpU = FakePlugin()
bpU._entries = {1: Entry(1, True), 2: Entry(2, False)}
ns["_orig_updateSettings"] = FakePlugin.updateSettings
su = _t.MethodType(ns["_patched_updateSettings"], bpU)
su(_t.SimpleNamespace())
check("updateSettings: Original aufgerufen", bpU.updateSettings_calls == 1)
check("updateSettings: globaler Toggle False", bpU.ctrl_calls[-1] is False)

# ---------------- PATCH INSTALL/REMOVE (Mangling-Falle) ----------------
class FakeAVP(object):
    _setVehicleInfo = 'ORIG_SET'
    _ArenaVehiclesPlugin__handleShowExtendedInfo = 'ORIG_HANDLE'
    _ArenaVehiclesPlugin__setActive = 'ORIG_ACTIVE'
    setSettings = 'ORIG_SETTINGS'
    updateSettings = 'ORIG_UPDATES'

ns["_PATCHED"] = False
ns["_importPlugin"] = lambda force=False: FakeAVP
ns["_applyPatch"]()
check("Patch: _setVehicleInfo ersetzt",
      FakeAVP._setVehicleInfo != 'ORIG_SET')
check("Patch: __handleShowExtendedInfo ersetzt",
      FakeAVP._ArenaVehiclesPlugin__handleShowExtendedInfo != 'ORIG_HANDLE')
check("Patch: __setActive ersetzt",
      FakeAVP._ArenaVehiclesPlugin__setActive != 'ORIG_ACTIVE')
check("Patch: setSettings ersetzt", FakeAVP.setSettings != 'ORIG_SETTINGS')
check("Patch: updateSettings ersetzt", FakeAVP.updateSettings != 'ORIG_UPDATES')
ns["_removePatch"]()
check("Patch entfernt: _setVehicleInfo zurueck", FakeAVP._setVehicleInfo == 'ORIG_SET')
check("Patch entfernt: __handleShowExtendedInfo zurueck",
      FakeAVP._ArenaVehiclesPlugin__handleShowExtendedInfo == 'ORIG_HANDLE')
check("Patch entfernt: __setActive zurueck",
      FakeAVP._ArenaVehiclesPlugin__setActive == 'ORIG_ACTIVE')
check("Patch entfernt: setSettings zurueck", FakeAVP.setSettings == 'ORIG_SETTINGS')
check("Patch entfernt: updateSettings zurueck",
      FakeAVP.updateSettings == 'ORIG_UPDATES')

# enabled=false -> kein Patch
ns["_PATCHED"] = False
g_configParams.enabled.value = False
ns["_applyPatch"]()
check("enabled=false: kein Patch installiert",
      FakeAVP._setVehicleInfo == 'ORIG_SET')
resetParams()

# ---------------- INITIAL-RESET + REVEAL-SCHUTZ ----------------
bpR = FakePlugin()
bpR._entries = {1: Entry(1, True), 2: Entry(2, False)}
ns["_vehInfo"][9] = {'isSquad': True, 'classTag': 'MT', 'guiPropsName': 'squad',
                     'playerName': 'X', 'vehicleName': 'Y'}
ns["_altDown"] = True
ns["_resetDone"] = False
ns["_ensureInitialReset"](bpR)
check("Reset: globaler Namen-Toggle False", bpR.ctrl_calls == [False])
check("Reset: _altDown geleert", ns["_altDown"] is False)
check("Reset: _vehInfo geleert", 9 not in ns["_vehInfo"])
ns["_ensureInitialReset"](bpR)
check("Reset: laeuft nur einmal", bpR.ctrl_calls == [False])


print("")
if fails:
    print("FEHLGESCHLAGEN: %d" % len(fails))
    sys.exit(1)
print("Alle Tests bestanden.")
