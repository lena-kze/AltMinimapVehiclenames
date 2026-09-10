# AltMinimapVehiclenames - shared utilities

import logging

logger = logging.getLogger(__name__)


def overrideIn(cls, condition=lambda: True):

    def _overrideMethod(func):
        if not condition():
            return func
        funcName = func.__name__
        if funcName.startswith('__'):
            funcName = '_' + cls.__name__ + funcName
        old = getattr(cls, funcName)

        def wrapper(*args, **kwargs):
            return func(old, *args, **kwargs)

        setattr(cls, funcName, wrapper)
        return wrapper

    return _overrideMethod


def addMethodTo(cls, condition=lambda: True):

    def _overrideMethod(func):
        if not condition():
            return func
        setattr(cls, func.__name__, func)
        return func

    return _overrideMethod


def displayDialog(message):
    """Zeigt Fehlermeldungen im WoT-Dialog an (falls moeglich).

    Schlaegt die Anzeige fehl (z. B. nicht in der richtigen UI-Zeit),
    wird die Meldung nur ins Log geschrieben, damit sie nie crasht.
    """
    logger.error('%s', message)
    try:
        from gui import DialogsInterface
        from gui.Scaleform.daapi.view.dialogs import SimpleDialogMeta, I18nInfoDialogButtons
        DialogsInterface.showDialog(SimpleDialogMeta(title='AltMinimapVehiclenames', message=message, buttons=I18nInfoDialogButtons(i18nKey='common/error')), (lambda result: None))
    except Exception:
        logger.warning('Failed to display warning dialog window.', exc_info=True)


class ObservingSemaphore(object):

    def __init__(self):
        self.observerCount = 0

    def __enter__(self):
        self.observerCount += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.observerCount -= 1

    def __bool__(self):
        return self.observerCount > 0

    def __nonzero__(self):
        return self.observerCount > 0

    def withIgnoringLock(self, returnForIgnored):

        def _withIgnoringLock(func):

            def wrapper(*args, **kwargs):
                if self:
                    return returnForIgnored
                with self:
                    return func(*args, **kwargs)

            return wrapper

        return _withIgnoringLock