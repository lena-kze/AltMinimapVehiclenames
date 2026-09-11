# Config parameters for AltMinimapVehiclenames.

from altminimapvehiclenames.settings.config_param_types import *


class TeamNamesMode(object):
    SHOW_ON_ALT = 'show-on-alt'
    HIDE_ON_ALT = 'hide-on-alt'
    ALWAYS = 'always'
    NEVER = 'never'


class SquadNameContent(object):
    USERNAME = 'username'
    VEHICLE = 'vehicle'


class EnemySquadStarPosition(object):
    BEFORE = 'before'
    BOTH = 'both'
    AFTER = 'after'


_TEAM_OPTIONS = [
    Option(TeamNamesMode.SHOW_ON_ALT, 0, 'option.show-on-alt'),
    Option(TeamNamesMode.HIDE_ON_ALT, 1, 'option.hide-on-alt'),
    Option(TeamNamesMode.ALWAYS, 2, 'option.always'),
    Option(TeamNamesMode.NEVER, 3, 'option.never'),
]

_SQUAD_CONTENT_OPTIONS = [
    Option(SquadNameContent.USERNAME, 0, 'option.username'),
    Option(SquadNameContent.VEHICLE, 1, 'option.vehicle'),
]

_ENEMY_SQUAD_STAR_OPTIONS = [
    Option(EnemySquadStarPosition.BEFORE, 0, 'star-position.option.before'),
    Option(EnemySquadStarPosition.BOTH, 1, 'star-position.option.both'),
    Option(EnemySquadStarPosition.AFTER, 2, 'star-position.option.after'),
]


class ConfigParams(object):

    def __init__(self):
        self.enabled = BooleanParam([
            'enabled'], defaultValue=True, disabledValue=False)
        self.enemyNames = OptionsParam([
            'enemy-names'], list(_TEAM_OPTIONS), defaultValue=TeamNamesMode.HIDE_ON_ALT, disabledValue=TeamNamesMode.HIDE_ON_ALT)
        self.allyNames = OptionsParam([
            'ally-names'], list(_TEAM_OPTIONS), defaultValue=TeamNamesMode.SHOW_ON_ALT, disabledValue=TeamNamesMode.SHOW_ON_ALT)
        self.squadNames = OptionsParam([
            'squad-names'], list(_TEAM_OPTIONS), defaultValue=TeamNamesMode.ALWAYS, disabledValue=TeamNamesMode.ALWAYS)
        self.squadNamesNoAlt = OptionsParam([
            'squad-names-no-alt'], list(_SQUAD_CONTENT_OPTIONS), defaultValue=SquadNameContent.USERNAME, disabledValue=SquadNameContent.USERNAME)
        self.squadNamesAlt = OptionsParam([
            'squad-names-alt'], list(_SQUAD_CONTENT_OPTIONS), defaultValue=SquadNameContent.VEHICLE, disabledValue=SquadNameContent.VEHICLE)
        self.markEnemySquads = BooleanParam([
            'mark-enemy-squads'], defaultValue=True)
        self.enemySquadStarPosition = OptionsParam([
            'enemy-squad-star-position'], list(_ENEMY_SQUAD_STAR_OPTIONS),
            defaultValue=EnemySquadStarPosition.AFTER,
            disabledValue=EnemySquadStarPosition.AFTER)

    @staticmethod
    def items():
        return PARAM_REGISTRY.items()


g_configParams = ConfigParams()
