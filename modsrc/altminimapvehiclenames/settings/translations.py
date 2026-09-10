# AltMinimapVehiclenames - translations

import json, logging, ResMgr
from helpers import getClientLanguage

_LOGGER = logging.getLogger(__name__)

TRANSLATIONS_MAP = {}
DEFAULT_TRANSLATIONS_MAP = {}
CURRENT_LANGUAGE = 'de'
_TRANSLATION_INSTANCES = []


class Language(object):
    DE = 'de'
    EN = 'en'


_SUPPORTED_LANGUAGES = (Language.DE, Language.EN)


def getSupportedLanguages():
    return _SUPPORTED_LANGUAGES


def _loadLanguage(language):
    section = ResMgr.openSection('gui/altminimapvehiclenames/translations/translations_%s.json' % language)
    if section is None:
        return None
    raw = str(section.asBinary)
    return json.loads(raw, encoding='UTF-8')


def getAvailableLanguage(language):
    if language in _SUPPORTED_LANGUAGES:
        return language
    return Language.DE


def loadTranslations(language=None):
    """Laedt die Uebersetzungen fuer eine Sprache.

    Wird keine Sprache uebergeben, wird zuerst die Sprache aus der
    Config-Datei, danach Deutsch als Fallback verwendet.
    Setzt den Cache aller TranslationElement-Objekte zurueck, damit die
    Settings-Seite in der neuen Sprache gerendert wird.
    """
    global DEFAULT_TRANSLATIONS_MAP, TRANSLATIONS_MAP, CURRENT_LANGUAGE
    if language is None:
        language = getClientLanguage()
    resolved = getAvailableLanguage(language)
    translationsMap = _loadLanguage(resolved)
    if translationsMap is not None:
        TRANSLATIONS_MAP = translationsMap
    else:
        TRANSLATIONS_MAP = {}
    defaultMap = _loadLanguage(Language.DE)
    DEFAULT_TRANSLATIONS_MAP = defaultMap if defaultMap is not None else {}
    CURRENT_LANGUAGE = resolved
    _clearTranslationCache()
    _LOGGER.info('Loaded translations for language "%s".', resolved)


def reloadTranslations(language):
    """Laedt die Uebersetzungen neu; liefert True, wenn sich die Sprache
    tatsaechlich geaendert hat."""
    global CURRENT_LANGUAGE
    resolved = getAvailableLanguage(language)
    if resolved == CURRENT_LANGUAGE:
        return False
    loadTranslations(resolved)
    return True


def _clearTranslationCache():
    for instance in _TRANSLATION_INSTANCES:
        instance.clearCache()


def getTranslation(token):
    value = TRANSLATIONS_MAP.get(token)
    if value is None:
        value = DEFAULT_TRANSLATIONS_MAP.get(token)
    if value is None:
        return token
    if isinstance(value, (list, tuple)):
        value = ''.join(value)
    return value


class TranslationElement(object):
    """Deskriptor, der beim Zugriff den aktuell geladenen Text liefert.

    Der Wert wird gecacht; bei einem Sprachwechsel wird der Cache
    zurueckgesetzt, sodass beim naechsten Zugriff die neue Sprache gilt.
    """

    def __init__(self, tokenName):
        self._tokenName = tokenName
        self._value = None
        _TRANSLATION_INSTANCES.append(self)

    def __get__(self, instance, owner=None):
        if self._value is None:
            self._value = getTranslation(self._tokenName)
        return self._value

    def clearCache(self):
        self._value = None


class Tr(object):
    MODNAME = TranslationElement('modname')
    CHECKED = TranslationElement('checked')
    UNCHECKED = TranslationElement('unchecked')
    DEFAULT_VALUE = TranslationElement('defaultValue')
    ENEMY_SETTINGS_LABEL = TranslationElement('enemy-settings.label')
    ENEMY_NAMES_HEADER = TranslationElement('enemy-names.header')
    ENEMY_NAMES_BODY = TranslationElement('enemy-names.body')
    ALLY_SETTINGS_LABEL = TranslationElement('ally-settings.label')
    ALLY_NAMES_HEADER = TranslationElement('ally-names.header')
    ALLY_NAMES_BODY = TranslationElement('ally-names.body')
    SQUAD_SETTINGS_LABEL = TranslationElement('squad-settings.label')
    SQUAD_NAMES_HEADER = TranslationElement('squad-names.header')
    SQUAD_NAMES_BODY = TranslationElement('squad-names.body')
    SQUAD_NAMES_NO_ALT_HEADER = TranslationElement('squad-names-no-alt.header')
    SQUAD_NAMES_NO_ALT_BODY = TranslationElement('squad-names-no-alt.body')
    SQUAD_NAMES_ALT_HEADER = TranslationElement('squad-names-alt.header')
    SQUAD_NAMES_ALT_BODY = TranslationElement('squad-names-alt.body')
    MARK_ENEMY_SQUADS_HEADER = TranslationElement('mark-enemy-squads.header')
    MARK_ENEMY_SQUADS_BODY = TranslationElement('mark-enemy-squads.body')
    BATTLE_LOG_SETTINGS_LABEL = TranslationElement('battle-log-settings.label')
    BATTLE_LOG_MODE_HEADER = TranslationElement('battle-log-mode.header')
    BATTLE_LOG_MODE_BODY = TranslationElement('battle-log-mode.body')
    BATTLE_LOG_DURATION_HEADER = TranslationElement('battle-log-duration.header')
    BATTLE_LOG_DURATION_BODY = TranslationElement('battle-log-duration.body')
    BATTLE_LOG_OPTION_ALWAYS = TranslationElement('battle-log.option.always')
    BATTLE_LOG_OPTION_ON_ALT = TranslationElement('battle-log.option.on-alt')
    BATTLE_LOG_OPTION_NEVER = TranslationElement('battle-log.option.never')
    OPTION_SHOW_ON_ALT = TranslationElement('option.show-on-alt')
    OPTION_HIDE_ON_ALT = TranslationElement('option.hide-on-alt')
    OPTION_ALWAYS = TranslationElement('option.always')
    OPTION_NEVER = TranslationElement('option.never')
    OPTION_USERNAME = TranslationElement('option.username')
    OPTION_VEHICLE = TranslationElement('option.vehicle')
    CREDITS_LABEL = TranslationElement('credits.label')
