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
    // Controls display of your own squad (platoon) member names:
    // - "show-on-alt"  - visible only while ALT is pressed,
    // - "hide-on-alt"  - visible, hidden while ALT is pressed,
    // - "always"       - always visible,
    // - "never"        - never visible.
    "squad-names": %(squad-names)s,

    // Valid values: ["username", "vehicle"]
    // Default value: "username"
    //
    // Name shown for your own squad members while ALT is NOT pressed:
    // - "username"  - player name,
    // - "vehicle"   - vehicle name.
    "squad-names-no-alt": %(squad-names-no-alt)s,

    // Valid values: ["username", "vehicle"]
    // Default value: "vehicle"
    //
    // Name shown for your own squad members while ALT is pressed:
    // - "username"  - player name,
    // - "vehicle"   - vehicle name.
    "squad-names-alt": %(squad-names-alt)s,

    // Valid values: true/false (default: true)
    // Mark detected enemy platoon members with a star or a platoon number,
    // according to the marker-position setting below.
    "mark-enemy-squads": %(mark-enemy-squads)s,

    // Valid values: ["before", "both", "after", "number-before",
    // "number-both", "number-after"] (default: "after")
    // Controls marker type and position on enemy platoon vehicle names.
    "enemy-squad-star-position": %(enemy-squad-star-position)s,

    // Valid values: true/false (default: false)
    //
    // Keeps the selected enemy platoon marker visible on the minimap even
    // while the enemy vehicle names are hidden by the enemy-names mode (only
    // relevant for "show-on-alt"/"hide-on-alt"). Requires "mark-enemy-squads".
    "enemy-squad-star-only": %(enemy-squad-star-only)s,

    // DO NOT touch "__version__" field
    "__version__": 7
}
'''
