# AltMinimapVehiclenames - battle logic (ArenaVehiclesPlugin patching)

import logging

from PlayerEvents import g_playerEvents

from altminimapvehiclenames.settings.config_param import g_configParams
from altminimapvehiclenames.settings.config_param import TeamNamesMode
from altminimapvehiclenames.settings.config_param import SquadNameContent
from altminimapvehiclenames.settings.config_param import EnemySquadStarPosition

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

_TAG = '[AltMinimapVehiclenames] '

_SUPERSCRIPT_DIGITS = {
    '0': u'\u2070',
    '1': u'\u00b9',
    '2': u'\u00b2',
    '3': u'\u00b3',
    '4': u'\u2074',
    '5': u'\u2075',
    '6': u'\u2076',
    '7': u'\u2077',
    '8': u'\u2078',
    '9': u'\u2079',
}

_ArenaVehiclesPlugin = None
_altDown = False
_resetDone = False
_vehInfo = {}


def _log(msg):
    _logger.info(_TAG + msg)


def _importPlugin(force=False):
    global _ArenaVehiclesPlugin
    if _ArenaVehiclesPlugin is None or force:
        from gui.Scaleform.daapi.view.battle.shared.minimap.plugins import ArenaVehiclesPlugin
        _ArenaVehiclesPlugin = ArenaVehiclesPlugin
    return _ArenaVehiclesPlugin


def _modEnabled():
    return bool(g_configParams.enabled())


def _enemyMode():
    return g_configParams.enemyNames()


def _allyMode():
    return g_configParams.allyNames()


def _squadMode():
    return g_configParams.squadNames()


def _squadNameContent(isDown):
    """Liefert den konfigurierten Namens-Inhalt (username/vehicle) fuer
    Zugmitglieder, abhaengig davon ob Alt gedrueckt ist."""
    if isDown:
        return g_configParams.squadNamesAlt()
    return g_configParams.squadNamesNoAlt()


def _squadDisplayedName(info, isDown):
    if info.get('isForeignSquad'):
        if info.get('isEnemy') and g_configParams.markEnemySquads():
            marker = _enemySquadMarker(info)
            position = g_configParams.enemySquadStarPosition()
            if position in (EnemySquadStarPosition.BEFORE,
                            EnemySquadStarPosition.NUMBER_BEFORE):
                return marker + info['vehicleName']
            if position in (EnemySquadStarPosition.BOTH,
                            EnemySquadStarPosition.NUMBER_BOTH):
                return marker + info['vehicleName'] + marker
            return info['vehicleName'] + marker
        return info['vehicleName']
    if not info.get('isOwnSquad'):
        return info['vehicleName']
    if _squadNameContent(isDown) == SquadNameContent.VEHICLE:
        return info['vehicleName']
    return info['playerName']


def _superscriptNumber(number):
    try:
        digits = str(int(number))
    except (TypeError, ValueError):
        return ''
    if not digits or digits.startswith('-'):
        return ''
    return u''.join(_SUPERSCRIPT_DIGITS.get(digit, digit) for digit in digits)


def _enemySquadMarker(info):
    position = g_configParams.enemySquadStarPosition()
    if position in (EnemySquadStarPosition.NUMBER_BEFORE,
                    EnemySquadStarPosition.NUMBER_BOTH,
                    EnemySquadStarPosition.NUMBER_AFTER):
        marker = _superscriptNumber(info.get('squadIndex', 0))
        if marker:
            return marker
    return '*'


def _enemySquadMarkerFallbackVisible(entry, info, altPressed):
    """True, wenn fuer diesen gegnerischen Zug-Eintrag nur der Marker
    angezeigt wird, obwohl die Bezeichnung laut Feind-Modus und Alt-Status
    gerade ausgeblendet waere.

    Sinnvoll nur bei den ALT-abhaengigen Modi: Bei "always" wird die
    Bezeichnung ohnehin angezeigt, bei "never" sollen auch die Sternchen
    ausgeblendet bleiben.
    """
    if not g_configParams.enemySquadStarOnly():
        return False
    if not g_configParams.markEnemySquads():
        return False
    if info is None:
        return False
    if not (entry.isEnemy() and info.get('isSquad') and info.get('isEnemy')):
        return False
    mode = _enemyMode()
    if mode not in (TeamNamesMode.SHOW_ON_ALT, TeamNamesMode.HIDE_ON_ALT):
        return False
    return not _visibleInMode(mode, altPressed)


def _enemySquadDisplayedName(entry, info, isDown):
    """Label fuer gegnerische Zugmitglieder inkl. Marker-Fallback.

    Ist die Bezeichnung laut Modus/Alt gerade ausgeblendet und der
    Marker-Fallback aktiv, wird nur der gewaehlte Marker angezeigt; sonst
    die normale Bezeichnung (ggf. mit Marker).
    """
    if _enemySquadMarkerFallbackVisible(entry, info, isDown):
        return _enemySquadMarker(info)
    return _squadDisplayedName(info, isDown)


# ---------------------------------------------------------------------------
# Team-abhaengige Namen-Sichtbarkeit
# ---------------------------------------------------------------------------
def _modeFor(entry, info=None):
    """Liefert den konfigurierten Anzeige-Modus fuer einen Entry."""
    if info is not None and info.get('isOwnSquad'):
        return _squadMode()
    if entry.isEnemy():
        return _enemyMode()
    return _allyMode()


def _visibleInMode(mode, altPressed):
    """Berechnet aus einem Modus + Alt-Status, ob Namen sichtbar sind."""
    if mode == TeamNamesMode.ALWAYS:
        return True
    if mode == TeamNamesMode.NEVER:
        return False
    if mode == TeamNamesMode.SHOW_ON_ALT:
        return altPressed
    return not altPressed


def _applyEntryNameVisibility(plugin, entry, altPressed, info=None):
    """Setzt die Sichtbarkeit des Fahrzeug-Namens fuer EINEN Entry.

    Alle Teamgruppen (Feind, Ally, Zugmitglied) nutzen die gleichen vier
    Modi (show-on-alt / hide-on-alt / always / never):

      show-on-alt -> Name nur bei gedrueckter Alt sichtbar
      hide-on-alt -> Name ohne Alt sichtbar, bei Alt ausgeblendet
      always      -> Name immer sichtbar
      never       -> Name nie sichtbar

    Der eigentliche Namens-INHALT fuer Zugmitglieder (Spielername/
    Fahrzeugname) wird separat in _applySquadNames gesteuert.
    """
    if _enemySquadMarkerFallbackVisible(entry, info, altPressed):
        plugin._invoke(entry.getID(), 'showVehicleName')
        return
    mode = _modeFor(entry, info)
    if _visibleInMode(mode, altPressed):
        plugin._invoke(entry.getID(), 'showVehicleName')
    else:
        plugin._invoke(entry.getID(), 'hideVehicleName')


def _applyAllNamesVisibility(plugin, altPressed):
    entries = getattr(plugin, '_entries', None)
    if not entries:
        return
    for vehicleID, entry in entries.iteritems():
        try:
            _applyEntryNameVisibility(plugin, entry, altPressed, _vehInfo.get(vehicleID))
        except Exception:
            _logger.exception('%s Fehler bei einzel-Entry', _TAG)


def _applySquadNames(plugin, isDown):
    """Setzt fuer den eigenen Zug und markierte Gegner den Namen neu.

    Fuer den eigenen Zug folgt die Sichtbarkeit dem squad-names Modus:
      show-on-alt -> nur bei Alt sichtbar
      hide-on-alt -> nur ohne Alt sichtbar
      always      -> immer sichtbar
      never       -> versteckt

    Andere verbuendete Zuege bleiben unter der ally-names-Regel; gegnerische
    Zuege werden nur mit Fahrzeugname und optionalem Marker behandelt.

    Der Namens-INHALT wird separat gewaehlt:
      squad-names-no-alt -> Name ohne Alt (username/vehicle)
      squad-names-alt    -> Name mit Alt (username/vehicle)
    """
    entries = getattr(plugin, '_entries', None)
    if not entries:
        return
    mode = _squadMode()
    for vehicleID, entry in entries.iteritems():
        info = _vehInfo.get(vehicleID)
        if info is None or not info.get('isSquad'):
            continue
        try:
            if info.get('isForeignSquad'):
                if info.get('isEnemy') and g_configParams.markEnemySquads():
                    plugin._invoke(entry.getID(), 'setVehicleInfo', vehicleID,
                                 info['classTag'], _enemySquadDisplayedName(entry, info, isDown),
                                 info['guiPropsName'], '')
                    _applyEntryNameVisibility(plugin, entry, isDown, info)
                continue
            if not info.get('isOwnSquad'):
                continue
            if mode == TeamNamesMode.NEVER:
                plugin._invoke(entry.getID(), 'hideVehicleName')
                continue
            if mode == TeamNamesMode.SHOW_ON_ALT:
                if not isDown:
                    plugin._invoke(entry.getID(), 'hideVehicleName')
                    continue
            elif mode == TeamNamesMode.HIDE_ON_ALT:
                if isDown:
                    plugin._invoke(entry.getID(), 'hideVehicleName')
                    continue
            name = _squadDisplayedName(info, isDown)
            plugin._invoke(entry.getID(), 'setVehicleInfo', vehicleID,
                           info['classTag'], name, info['guiPropsName'], '')
            plugin._invoke(entry.getID(), 'showVehicleName')
        except Exception:
            _logger.exception('%s Fehler bei Zug-Namenswechsel', _TAG)


def _entryVehicleID(plugin, entry):
    entries = getattr(plugin, '_entries', None)
    if not entries:
        return None
    for vehicleID, candidate in entries.iteritems():
        if candidate is entry:
            return vehicleID
    return None


def _isOwnSquad(plugin, vehicleID, entry, isSquad):
    """Nutze die Arena-DP-Zuordnung statt des allgemeinen Squad-Flags.

    vInfo.isSquadMan() markiert jeden erkannten Zug im Gefecht. Die Arena-DP
    filtert zusaetzlich auf eigenes Team und eigene prebattleID.
    """
    if not isSquad or entry.isEnemy():
        return False
    arenaDP = getattr(plugin, '_arenaDP', None)
    if arenaDP is None:
        return False
    try:
        return bool(arenaDP.isSquadMan(vehicleID))
    except Exception:
        _logger.exception('%s Eigener Zug nicht ermittelbar', _TAG)
        return False


def _applyNameRules(plugin):
    # Globaler Namen-Toggle aus, damit unsere per-Entry-Regel das letzte
    # Wort hat (Vorgehen wie bisher).
    try:
        plugin._parentObj.as_showVehiclesNameS(False)
    except Exception:
        _logger.info('%s Toggle n/a: as_showVehiclesNameS', _TAG)
    _applyAllNamesVisibility(plugin, _altDown)
    _applySquadNames(plugin, _altDown)


def _ensureInitialReset(plugin):
    global _altDown, _vehInfo, _resetDone
    if _resetDone:
        return
    _resetDone = True
    _altDown = False
    _vehInfo.clear()
    _applyNameRules(plugin)


# ---------------------------------------------------------------------------
# Patch-Methoden
# ---------------------------------------------------------------------------
_orig_handleShowExtendedInfo = None
_orig_setVehicleInfo = None
_orig_setActive = None
_orig_setSettings = None
_orig_updateSettings = None
_PATCHED = False


def _patched_handleShowExtendedInfo(self, event):
    _ensureInitialReset(self)
    _orig_handleShowExtendedInfo(self, event)
    try:
        global _altDown
        isDown = bool(event.ctx['isDown'])
        _altDown = isDown
        _applyAllNamesVisibility(self, isDown)
        _applySquadNames(self, isDown)
    except Exception:
        _logger.exception('%s Fehler in _patched_handleShowExtendedInfo', _TAG)


def _patched_setVehicleInfo(self, vehicleID, entry, vInfo, guiProps, isSpotted=False):
    _ensureInitialReset(self)
    _orig_setVehicleInfo(self, vehicleID, entry, vInfo, guiProps, isSpotted)
    try:
        isSquad = bool(vInfo.isSquadMan())
        isEnemy = bool(entry.isEnemy())
        isOwnSquad = _isOwnSquad(self, vehicleID, entry, isSquad)
        info = {
            'isSquad': isSquad,
            'isEnemy': isEnemy,
            'isOwnSquad': isOwnSquad,
            'isForeignSquad': isSquad and not isOwnSquad,
            'classTag': vInfo.vehicleType.classTag,
            'guiPropsName': self._getGuiPropsName(guiProps),
            'playerName': _getPlayerName(vInfo),
            'vehicleName': self._getDisplayedName(vInfo),
            'squadIndex': getattr(vInfo, 'squadIndex', 0),
        }
        _vehInfo[vehicleID] = info
        _applyEntryNameVisibility(self, entry, _altDown, info)
        if isSquad and isEnemy and g_configParams.markEnemySquads():
            self._invoke(entry.getID(), 'setVehicleInfo', vehicleID,
                         info['classTag'], _enemySquadDisplayedName(entry, info, _altDown),
                         info['guiPropsName'], '')
            _applyEntryNameVisibility(self, entry, _altDown, info)
        elif info['isOwnSquad'] and not _altDown and _squadMode() in (
                TeamNamesMode.ALWAYS, TeamNamesMode.HIDE_ON_ALT):
            # ohne Alt: sofort den gewaehlten Namen (squad-names-no-alt) zeigen
            self._invoke(entry.getID(), 'setVehicleInfo', vehicleID,
                         info['classTag'], _squadDisplayedName(info, False),
                         info['guiPropsName'], '')
    except Exception:
        _logger.exception('%s Fehler in _patched_setVehicleInfo', _TAG)


def _patched_setActive(self, entry, active):
    _ensureInitialReset(self)
    _orig_setActive(self, entry, active)
    if not active:
        return
    try:
        vehicleID = _entryVehicleID(self, entry)
        _applyEntryNameVisibility(self, entry, _altDown,
                                  _vehInfo.get(vehicleID) if vehicleID is not None else None)
    except Exception:
        _logger.exception('%s Fehler in _patched_setActive', _TAG)


def _patched_setSettings(self):
    _orig_setSettings(self)
    try:
        _applyNameRules(self)
    except Exception:
        _logger.exception('%s Fehler in _patched_setSettings', _TAG)


def _patched_updateSettings(self, diff):
    _orig_updateSettings(self, diff)
    try:
        _applyNameRules(self)
    except Exception:
        _logger.exception('%s Fehler in _patched_updateSettings', _TAG)


def _getPlayerName(vInfo):
    try:
        player = vInfo.player
        if player is not None:
            name = getattr(player, 'name', None)
            if name:
                return name
    except Exception:
        _logger.exception('%s Kein Spielername abrufbar', _TAG)
    return None


def _applyPatch():
    global _orig_handleShowExtendedInfo, _orig_setVehicleInfo, _orig_setActive
    global _orig_setSettings, _orig_updateSettings, _PATCHED
    global _altDown, _vehInfo, _resetDone
    if _PATCHED:
        return
    if not _modEnabled():
        _log('Mod deaktiviert (enabled=false), kein Patch.')
        return
    _altDown = False
    _vehInfo.clear()
    _resetDone = False
    cls = _importPlugin()
    _orig_handleShowExtendedInfo = cls._ArenaVehiclesPlugin__handleShowExtendedInfo
    _orig_setVehicleInfo = cls._setVehicleInfo
    _orig_setActive = cls._ArenaVehiclesPlugin__setActive
    _orig_setSettings = cls.setSettings
    _orig_updateSettings = cls.updateSettings
    cls._ArenaVehiclesPlugin__handleShowExtendedInfo = _patched_handleShowExtendedInfo
    cls._setVehicleInfo = _patched_setVehicleInfo
    cls._ArenaVehiclesPlugin__setActive = _patched_setActive
    cls.setSettings = _patched_setSettings
    cls.updateSettings = _patched_updateSettings
    _PATCHED = True
    _log('Patch aktiv.')


def _removePatch():
    global _orig_handleShowExtendedInfo, _orig_setVehicleInfo, _orig_setActive
    global _orig_setSettings, _orig_updateSettings, _PATCHED
    global _altDown, _vehInfo, _resetDone
    if not _PATCHED:
        return
    cls = _importPlugin()
    if _orig_handleShowExtendedInfo is not None:
        cls._ArenaVehiclesPlugin__handleShowExtendedInfo = _orig_handleShowExtendedInfo
        _orig_handleShowExtendedInfo = None
    if _orig_setVehicleInfo is not None:
        cls._setVehicleInfo = _orig_setVehicleInfo
        _orig_setVehicleInfo = None
    if _orig_setActive is not None:
        cls._ArenaVehiclesPlugin__setActive = _orig_setActive
        _orig_setActive = None
    if _orig_setSettings is not None:
        cls.setSettings = _orig_setSettings
        _orig_setSettings = None
    if _orig_updateSettings is not None:
        cls.updateSettings = _orig_updateSettings
        _orig_updateSettings = None
    _PATCHED = False
    _altDown = False
    _vehInfo.clear()
    _resetDone = False
    _log('Patch entfernt.')


# ---------------------------------------------------------------------------
# init / fini (Battle-Events)
# ---------------------------------------------------------------------------
def _onBattleEnter():
    try:
        _applyPatch()
    except Exception:
        _logger.exception('%s Konnte Patch beim Kampfstart nicht setzen', _TAG)


def _onBattleExit():
    try:
        _removePatch()
    except Exception:
        _logger.exception('%s Konnte Patch beim Kampfende nicht entfernen', _TAG)


def init():
    g_playerEvents.onAvatarBecomePlayer += _onBattleEnter
    g_playerEvents.onAvatarBecomeNonPlayer += _onBattleExit
    _log('Registriert (Kampfstart: Patch aktivieren).')


def fini():
    _removePatch()
    g_playerEvents.onAvatarBecomePlayer -= _onBattleEnter
    g_playerEvents.onAvatarBecomeNonPlayer -= _onBattleExit
