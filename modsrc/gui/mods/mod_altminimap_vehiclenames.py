import logging

logger = logging.getLogger(__name__)


def init():
    from altminimapvehiclenames import g_altMinimapVehiclenamesMod
    g_altMinimapVehiclenamesMod.init()


def fini():
    from altminimapvehiclenames import g_altMinimapVehiclenamesMod
    g_altMinimapVehiclenamesMod.fini()