Foxglove - a firefox proxy profile manager
==========================================

Foxglove is a combined Firefox profile and ssh connection manager with two purposes:

1. Quick creation of profiles from a template.

2. ssh into a server and automatically configure a Firefox session to SOCKS
   proxy through that connection.

For the first case, simply call foxglove with the profile name: foxglove
newprofile

To add a proxy server, just include it as the second argument: foxglove newprofile jumphost

Obviously you must be able to ssh into jumphost for this to work. Foxglove will
do this automatically and tear down the connection when Firefox quits.

Foxglove will invoke 'firefox' using normal path resolution. Prepending a
directory to PATH allows you to select the version in that directory. This is
useful for switching between releases (e.g., ESR, regular, and Beta)

self-explanatory. prefs.js contains some reasonable security and privacy
conscious defaults that may be changed as needed. Preferences may also be
changed during a session, but will reset to the value in prefs.js on the next
run.  Add-on preferences (specified in addon_prefs/NAME.js, with NAME
corresponding to a line in addons.txt) are set only on new profile creation,
when add-ons are installed.

Note that if prefs.js and addons.txt are not found in ~/.foxglove, they may be
re-created.
