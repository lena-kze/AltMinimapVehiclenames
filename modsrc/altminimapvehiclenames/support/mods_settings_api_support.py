import logging

from altminimapvehiclenames.settings.translations import Tr
from altminimapvehiclenames.settings.config import g_config
from altminimapvehiclenames.settings.config_param import g_configParams
from altminimapvehiclenames.utils import ObservingSemaphore

logger = logging.getLogger(__name__)

from gui.modsSettingsApi import g_modsSettingsApi

modLinkage = 'com.github.lena.altminimapvehiclenames'
modDisplayName = 'AltMinimapVehiclenames'


def registerSoftDependencySupport():
    template = {'modDisplayName': (modDisplayName), 
       'enabled': (g_configParams.enabled.defaultMsaValue), 
       'column1': (_createTeamSettingsPart() + _createBattleLogSettingsPart() + _createCreditsPart())}
    g_modsSettingsApi.setModTemplate(modLinkage, template, onModSettingsChanged)


settingsChangedSemaphore = ObservingSemaphore()


def onConfigFileReload():
    msaSettings = {}
    for tokenName, param in g_configParams.items():
        msaSettings[tokenName] = param.msaValue

    logger.info('Synchronizing config file -> ModsSettingsAPI')
    g_modsSettingsApi.updateModSettings(modLinkage, newSettings=msaSettings)


@settingsChangedSemaphore.withIgnoringLock(returnForIgnored=None)
def onModSettingsChanged(linkage, newSettings):
    if linkage != modLinkage:
        return
    try:
        serializedSettings = {}
        for tokenName, param in g_configParams.items():
            if tokenName not in newSettings:
                continue
            value = param.fromMsaValue(newSettings[tokenName])
            jsonValue = param.toJsonValue(value)
            serializedSettings[param.tokenName] = jsonValue

        logger.info('Synchronizing ModsSettingsAPI -> config file')
        g_config.updateConfigSafely(serializedSettings)
    except Exception:
        logger.error('Error occurred while ModsSettingsAPI settings change.', exc_info=True)


def _endSection():
    return _emptyLine(3)


def _emptyLine(count=1):
    return [{'type': 'Empty'}] * count


def _createTeamSettingsPart():
    return [{'type': 'Label', 'text': (Tr.ENEMY_SETTINGS_LABEL)}] + _emptyLine(2) + [
     g_configParams.enemyNames.renderParam(header=Tr.ENEMY_NAMES_HEADER, body=Tr.ENEMY_NAMES_BODY),
     g_configParams.allyNames.renderParam(header=Tr.ALLY_NAMES_HEADER, body=Tr.ALLY_NAMES_BODY)] + _emptyLine(2) + [
      g_configParams.squadNames.renderParam(header=Tr.SQUAD_NAMES_HEADER, body=Tr.SQUAD_NAMES_BODY),
      g_configParams.squadNamesNoAlt.renderParam(header=Tr.SQUAD_NAMES_NO_ALT_HEADER, body=Tr.SQUAD_NAMES_NO_ALT_BODY),
      g_configParams.squadNamesAlt.renderParam(header=Tr.SQUAD_NAMES_ALT_HEADER, body=Tr.SQUAD_NAMES_ALT_BODY),
      g_configParams.markEnemySquads.renderParam(header=Tr.MARK_ENEMY_SQUADS_HEADER, body=Tr.MARK_ENEMY_SQUADS_BODY)]


def _createCreditsPart():
    return [{'type': 'Label', 'text': Tr.CREDITS_LABEL}]


def _createBattleLogSettingsPart():
    return _emptyLine(2) + [
        {'type': 'Label', 'text': Tr.BATTLE_LOG_SETTINGS_LABEL},
        g_configParams.battleLogMode.renderParam(
            header=Tr.BATTLE_LOG_MODE_HEADER, body=Tr.BATTLE_LOG_MODE_BODY),
        g_configParams.battleLogDuration.renderParam(
            header=Tr.BATTLE_LOG_DURATION_HEADER, body=Tr.BATTLE_LOG_DURATION_BODY)]


def _createRainbowText(text):
    parts = []
    characterCount = len(text)
    for index, character in enumerate(text):
        color = _hueToHex(index / float(max(characterCount - 1, 1)))
        character = character.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        parts.append("<font color='%s'>%s</font>" % (color, character))
    return ''.join(parts)


def _hueToHex(fraction):
    hue = fraction * 360
    chroma = (1 - abs(2 * 0.55 - 1)) * 1.0
    scaledHue = hue / 60.0
    secondary = chroma * (1 - abs(scaledHue % 2 - 1))
    if scaledHue < 1:
        red, green, blue = chroma, secondary, 0
    elif scaledHue < 2:
        red, green, blue = secondary, chroma, 0
    elif scaledHue < 3:
        red, green, blue = 0, chroma, secondary
    elif scaledHue < 4:
        red, green, blue = 0, secondary, chroma
    elif scaledHue < 5:
        red, green, blue = secondary, 0, chroma
    else:
        red, green, blue = chroma, 0, secondary
    match = 0.55 - chroma / 2.0
    red = int(round((red + match) * 255))
    green = int(round((green + match) * 255))
    blue = int(round((blue + match) * 255))
    return '#%02x%02x%02x' % (red, green, blue)
