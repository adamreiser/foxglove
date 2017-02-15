Foxglove - a firefox proxy profile manager
=======================

Manages ssh connections and associated Firefox proxy configurations.
This allows multiple distinct sessions to be run simultaneously. Themes
and CSS can be used to make different sessions visually distinctive.

When the script is called with a new profile name, a profile using the proxy
and containing the settings in prefs.js will be created. Subsequent
invocations with that name will use that profile. Application data, including
prefs.js and profiles, is stored in ~/.foxglove.

prefs.js contains some reasonable security and privacy conscious defaults and is
intended to be common across profiles. Preferences may be changed during a session,
but will revert to the value in prefs.js on the next run. Delete or comment out lines
as needed, but if the file doesn't exist, it will be restored using foxglove's default
values.
