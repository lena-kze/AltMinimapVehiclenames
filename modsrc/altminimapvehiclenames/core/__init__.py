# AltMinimapVehiclenames - battle logic (ArenaVehiclesPlugin patching)

import logging
import BigWorld

from PlayerEvents import g_playerEvents

from altminimapvehiclenames.settings.config_param import g_configParams
from altminimapvehiclenames.settings.config_param import TeamNamesMode
from altminimapvehiclenames.settings.config_param import SquadNameContent
from altminimapvehiclenames.settings.config_param import BattleLogMode
from altminimapvehiclenames.settings.config_param import EnemySquadStarPosition

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

_TAG = '[AltMinimapVehiclenames] '

_ArenaVehiclesPlugin = None
_altDown = False
_resetDone = False
_vehInfo = {}
_logAltDown = False
_logRecords = None
_logRecordStyle = False
_logClearCallback = None
_DamageLogPanel = None
_orig_log_updateTopLog = None
_orig_log_addToTopLog = None
_orig_log_handleShowExtendedInfo = None
_LOG_PATCHED = False


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


def _battleLogMode():
    return g_configParams.battleLogMode()


def _battleLogVisible():
    mode = _battleLogMode()
    if mode == BattleLogMode.ON_ALT:
        return _logAltDown
    if mode == BattleLogMode.NEVER:
        return False
    return True


def _squadNameContent(isDown):
    """Liefert den konfigurierten Namens-Inhalt (username/vehicle) fuer
    Zugmitglieder, abhaengig davon ob Alt gedrueckt ist."""
    if isDown:
        return g_configParams.squadNamesAlt()
    return g_configParams.squadNamesNoAlt()


def _squadDisplayedName(info, isDown):
    if info.get('isForeignSquad'):
        if info.get('isEnemy') and g_configParams.markEnemySquads():
            position = g_configParams.enemySquadStarPosition()
            if position == EnemySquadStarPosition.BEFORE:
                return '*' + info['vehicleName']
            if position == EnemySquadStarPosition.BOTH:
                return '*' + info['vehicleName'] + '*'
            return info['vehicleName'] + '*'
        return info['vehicleName']
    if not info.get('isOwnSquad'):
        return info['vehicleName']
    if _squadNameContent(isDown) == SquadNameContent.VEHICLE:
        return info['vehicleName']
    return info['playerName']


# ---------------------------------------------------------------------------
# Team-abhaengige Namen-Sichtbarkeit
# ---------------------------------------------------------------------------
def _modeFor(entry, info=None):
    """Liefert den konfigurierten Anzeige-Modus fuer einen Entry."""
    if entry.isEnemy():
        return _enemyMode()
    if info is not None and info.get('isSquad'):
        return _squadMode()
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
    """Setzt fuer alle Zugmitglieder den anzuzeigenden Namen neu.

    Sichtbarkeit folgt dem squad-names Modus (wie bei Feind/Ally):
      show-on-alt -> nur bei Alt sichtbar
      hide-on-alt -> nur ohne Alt sichtbar
      always      -> immer sichtbar
      never       -> versteckt

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
                if g_configParams.markEnemySquads():
                    plugin._invoke(entry.getID(), 'setVehicleInfo', vehicleID,
                                 info['classTag'], _squadDisplayedName(info, isDown),
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


def _clearBattleLog(panel):
    try:
        panel._topLog.clear()
    except Exception:
        _logger.exception('%s Fehler beim Leeren des Gefechtslogs', _TAG)


def _scheduleBattleLogClear(panel):
    global _logClearCallback
    if _logClearCallback is not None:
        try:
            BigWorld.cancelCallback(_logClearCallback)
        except Exception:
            pass
    _logClearCallback = BigWorld.callback(
        float(g_configParams.battleLogDuration()),
        lambda: _clearBattleLog(panel))


def _applyBattleLogVisibility(panel):
    if _logRecords is None:
        return
    _orig_log_updateTopLog(
        panel, _battleLogVisible(), _logRecordStyle, _logRecords)


def _patched_log_updateTopLog(self, isVisible, isShortMode, records):
    global _logRecords, _logRecordStyle
    _logRecords = records
    _logRecordStyle = isShortMode
    _orig_log_updateTopLog(self, _battleLogVisible(), isShortMode, records)


def _patched_log_addToTopLog(self, value, actionTypeImg, vehicleTypeImg,
                             vehicleName, shellTypeStr, shellTypeBG,
                             shellModeImg=None):
    _orig_log_addToTopLog(self, value, actionTypeImg, vehicleTypeImg,
                          vehicleName, shellTypeStr, shellTypeBG, shellModeImg)
    if _battleLogMode() != BattleLogMode.NEVER:
        _scheduleBattleLogClear(self)


def _patched_log_handleShowExtendedInfo(self, event):
    global _logAltDown
    _orig_log_handleShowExtendedInfo(self, event)
    _logAltDown = bool(event.ctx['isDown'])
    _applyBattleLogVisibility(self)


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
        info = {
            'isSquad': isSquad,
            'isEnemy': isEnemy,
            'isOwnSquad': isSquad and not isEnemy,
            'isForeignSquad': isSquad and isEnemy,
            'classTag': vInfo.vehicleType.classTag,
            'guiPropsName': self._getGuiPropsName(guiProps),
            'playerName': _getPlayerName(vInfo),
            'vehicleName': self._getDisplayedName(vInfo),
        }
        _vehInfo[vehicleID] = info
        _applyEntryNameVisibility(self, entry, _altDown, info)
        if isSquad and isEnemy and g_configParams.markEnemySquads():
            self._invoke(entry.getID(), 'setVehicleInfo', vehicleID,
                         info['classTag'], _squadDisplayedName(info, _altDown),
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


def _applyBattleLogPatch():
    global _DamageLogPanel, _orig_log_updateTopLog
    global _orig_log_addToTopLog, _orig_log_handleShowExtendedInfo
    global _LOG_PATCHED, _logAltDown, _logRecords
    if _LOG_PATCHED:
        return
    try:
        from gui.Scaleform.daapi.view.battle.shared.damage_log_panel import DamageLogPanel
        _DamageLogPanel = DamageLogPanel
        _orig_log_updateTopLog = DamageLogPanel._updateTopLog
        _orig_log_addToTopLog = DamageLogPanel._addToTopLog
        _orig_log_handleShowExtendedInfo = DamageLogPanel._handleShowExtendedInfo
        DamageLogPanel._updateTopLog = _patched_log_updateTopLog
        DamageLogPanel._addToTopLog = _patched_log_addToTopLog
        DamageLogPanel._handleShowExtendedInfo = _patched_log_handleShowExtendedInfo
        _logAltDown = False
        _logRecords = None
        _LOG_PATCHED = True
        _log('Gefechtslog-Patch aktiv.')
    except Exception:
        _logger.exception('%s Konnte Gefechtslog-Patch nicht setzen', _TAG)


def _removeBattleLogPatch():
    global _orig_log_updateTopLog, _orig_log_addToTopLog
    global _orig_log_handleShowExtendedInfo, _LOG_PATCHED
    global _logClearCallback, _logAltDown, _logRecords, _DamageLogPanel
    if _logClearCallback is not None:
        try:
            BigWorld.cancelCallback(_logClearCallback)
        except Exception:
            pass
        _logClearCallback = None
    if not _LOG_PATCHED:
        return
    if _orig_log_updateTopLog is not None:
        _DamageLogPanel._updateTopLog = _orig_log_updateTopLog
    if _orig_log_addToTopLog is not None:
        _DamageLogPanel._addToTopLog = _orig_log_addToTopLog
    if _orig_log_handleShowExtendedInfo is not None:
        _DamageLogPanel._handleShowExtendedInfo = _orig_log_handleShowExtendedInfo
    _orig_log_updateTopLog = None
    _orig_log_addToTopLog = None
    _orig_log_handleShowExtendedInfo = None
    _DamageLogPanel = None
    _logAltDown = False
    _logRecords = None
    _LOG_PATCHED = False


def _applyPatch():
    global _orig_handleShowExtendedInfo, _orig_setVehicleInfo, _orig_setActive
    global _orig_setSettings, _orig_updateSettings, _PATCHED
    global _altDown, _vehInfo, _resetDone
    global _orig_log_updateTopLog, _orig_log_addToTopLog
    global _orig_log_handleShowExtendedInfo, _logAltDown, _logRecords
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
    _applyBattleLogPatch()
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
    _removeBattleLogPatch()
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
