# AltMinimapVehiclenames - mod main package

import logging

logger = logging.getLogger(__name__)


class AltMinimapVehiclenamesMod(object):

    @property
    def isModsSettingsApiPresent(self):
        return self.__isModsSettingsApiPresent

    def __init__(self):
        self.__isModsSettingsApiPresent = False

    def init(self):
        try:
            logger.info('Initializing AltMinimapVehiclenames mod ...')
            from altminimapvehiclenames.settings import translations
            translations.loadTranslations()
            from altminimapvehiclenames import core
            core.init()
            self.__resolveSoftDependenciesSafely()
            if self.isModsSettingsApiPresent:
                from altminimapvehiclenames.support import mods_settings_api_support
                mods_settings_api_support.registerSoftDependencySupport()
            from altminimapvehiclenames.settings.config import g_config
            g_config.reloadSafely()
            logger.info('AltMinimapVehiclenames mod initialized')
        except Exception:
            logger.error('Error occurred while initializing AltMinimapVehiclenames mod', exc_info=True)
            from altminimapvehiclenames.utils import displayDialog
            displayDialog('Error occurred while initializing AltMinimapVehiclenames mod.\nContact mod developer with error logs for further support.')

    def __resolveSoftDependenciesSafely(self):
        try:
            from gui.modsSettingsApi import g_modsSettingsApi
            self.__isModsSettingsApiPresent = g_modsSettingsApi is not None
            if not self.isModsSettingsApiPresent:
                logger.warn('Error probably occurred in ModsSettingsAPI because it is None, ignore its presence.')
        except ImportError:
            self.__isModsSettingsApiPresent = False
        except Exception:
            logger.warn('Error occurred in ModsSettingsAPI, ignore its presence.', exc_info=True)
            self.__isModsSettingsApiPresent = False

        return

    def fini(self):
        try:
            from altminimapvehiclenames import core
            core.fini()
        except Exception:
            logger.error('Error occurred while finalizing AltMinimapVehiclenames mod', exc_info=True)


g_altMinimapVehiclenamesMod = AltMinimapVehiclenamesMod()


def init():
    g_altMinimapVehiclenamesMod.init()


def fini():
    g_altMinimapVehiclenamesMod.fini()
