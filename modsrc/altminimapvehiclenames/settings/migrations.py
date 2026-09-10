import logging

from altminimapvehiclenames.settings import ConfigException
from altminimapvehiclenames.settings.config_file import g_configFiles

logger = logging.getLogger(__name__)


class ConfigVersion(object):
    V1 = 1
    V2 = 2
    V3 = 3
    V4 = 4
    V5 = 5
    CURRENT = V5


def _migrateV1ToV2(configDict):
    # V1: squad-names "default" (Spielername/Fahrzeugname-Tausch) wurde durch
    # die einheitlichen Modi ersetzt; der alte Standard entspricht "always".
    if configDict.get('squad-names') == 'default':
        configDict['squad-names'] = 'always'


def _migrateV2ToV3(configDict):
    # V2: squad-names-no-alt/-alt wurden eingefuehrt; Defaults entsprechen
    # dem bisherigen Zug-Standard (ohne Alt Spielername, mit Alt Fahrzeugname).
    if 'squad-names-no-alt' not in configDict:
        configDict['squad-names-no-alt'] = 'username'
    if 'squad-names-alt' not in configDict:
        configDict['squad-names-alt'] = 'vehicle'


def _migrateV3ToV4(configDict):
    configDict.setdefault('mark-enemy-squads', True)


def _migrateV4ToV5(configDict):
    configDict.setdefault('battle-log-mode', 'always')
    configDict.setdefault('battle-log-duration', 5.0)


_MIGRATIONS = {
    ConfigVersion.V2: _migrateV1ToV2,
    ConfigVersion.V3: _migrateV2ToV3,
    ConfigVersion.V4: _migrateV3ToV4,
    ConfigVersion.V5: _migrateV4ToV5,
}


def _currentVersion(configDict):
    if '__version__' not in configDict:
        return ConfigVersion.V1
    return int(configDict['__version__'])


def performConfigMigrations():
    try:
        if not g_configFiles.config.exists():
            return
        configDict = g_configFiles.config.loadConfigDict()
        version = _currentVersion(configDict)
        targetVersion = ConfigVersion.CURRENT
        while version < targetVersion:
            version += 1
            migration = _MIGRATIONS.get(version)
            if migration is not None:
                migration(configDict)
            configDict['__version__'] = version
        g_configFiles.config.writeConfigDict(configDict)
    except ConfigException:
        logger.error('Failed to perform config file migration.')
        raise
    except Exception:
        logger.error('Failed to perform config file migration.', exc_info=True)
        raise ConfigException('Failed to perform config file migration due to unknown error.\nContact mod developer for further support with provided logs.')


def isLegacyConfig(configDict):
    return '__version__' not in configDict and set(configDict.keys()).issubset(['enabled', 'enemy-names', 'ally-names', 'squad-names'])


def progressVersion(configDict):
    if '__version__' not in configDict:
        configDict['__version__'] = ConfigVersion.V1
        return
    configDict['__version__'] = int(configDict['__version__']) + 1


def isVersion(configDict, version):
    if '__version__' not in configDict:
        return ConfigVersion.V1 == version
    return int(configDict['__version__']) == version
