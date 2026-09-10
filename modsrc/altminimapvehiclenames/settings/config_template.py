CONFIG_TEMPLATE = '''{
    // To generate default config, delete config file and launch a game again

    // Global features toggle
    // Valid values: true/false (default: true)
    //
    // When set to false, it globally disables all features of this mod.
    "enabled": %(enabled)s,

    // Valid values: ["show-on-alt", "hide-on-alt", "always", "never"]
    // Default value: "hide-on-alt"
    //
    // Controls display of enemy vehicle names:
    // - "show-on-alt"  - visible only while ALT is pressed,
    // - "hide-on-alt"  - visible, hidden while ALT is pressed,
    // - "always"       - always visible,
    // - "never"        - never visible.
    "enemy-names": %(enemy-names)s,

    // Valid values: ["show-on-alt", "hide-on-alt", "always", "never"]
    // Default value: "show-on-alt"
    //
    // Controls display of ally vehicle names:
    // - "show-on-alt"  - visible only while ALT is pressed,
    // - "hide-on-alt"  - visible, hidden while ALT is pressed,
    // - "always"       - always visible,
    // - "never"        - never visible.
    "ally-names": %(ally-names)s,

    // Valid values: ["show-on-alt", "hide-on-alt", "always", "never"]
    // Default value: "always"
    //
    // Controls display of squad (platoon) member names:
    // - "show-on-alt"  - visible only while ALT is pressed,
    // - "hide-on-alt"  - visible, hidden while ALT is pressed,
    // - "always"       - always visible,
    // - "never"        - never visible.
    "squad-names": %(squad-names)s,

    // Valid values: ["username", "vehicle"]
    // Default value: "username"
    //
    // Name shown for squad members while ALT is NOT pressed:
    // - "username"  - player name,
    // - "vehicle"   - vehicle name.
    "squad-names-no-alt": %(squad-names-no-alt)s,

    // Valid values: ["username", "vehicle"]
    // Default value: "vehicle"
    //
    // Name shown for squad members while ALT is pressed:
    // - "username"  - player name,
    // - "vehicle"   - vehicle name.
    "squad-names-alt": %(squad-names-alt)s,

    // Valid values: true/false (default: true)
    // Mark platoon members from the enemy team with a '*' after the vehicle name.
    "mark-enemy-squads": %(mark-enemy-squads)s,

    // Valid values: ["always", "on-alt", "never"] (default: "always")
    // Controls visibility of the battle log above the minimap.
    "battle-log-mode": %(battle-log-mode)s,

    // Display duration of a battle log entry in seconds (default: 5.0).
    "battle-log-duration": %(battle-log-duration)s,

    // DO NOT touch "__version__" field
    "__version__": 5
}
'''
