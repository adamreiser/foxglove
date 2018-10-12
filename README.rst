Foxglove - a firefox proxy profile manager
==========================================

Foxglove is a combined Firefox profile and ssh connection manager with two purposes:

1. Quick creation of Firefox profiles from a template.

2. ssh into a server and automatically configure Firefox to SOCKS
   proxy through that connection.

For the first case, simply call foxglove with the profile name: foxglove
newprofile

To add a proxy server, include it as the second argument: foxglove newprofile host

Obviously you must be able to ssh into "host" for this to work. Foxglove will
do this automatically, configure the profile to use the connection as a proxy,
and tear down the connection when Firefox quits.

Foxglove launches the browser via a subprocess call to "firefox". Setting PATH
prior to running foxglove can be used to launch a specific version of Firefox.

All foxglove data including profiles is stored in .foxglove in your home
directory, which will be created on first run. Foxglove will not touch your
regular Firefox profiles in any way.

prefs.js contains some reasonable security and privacy conscious defaults that
will be applied to all foxglove profiles and may be changed as needed.
Preferences may also be changed during a session, but will reset to the value
in prefs.js on the next run.

Note that if prefs.js or addons.txt are not found in .foxglove (which should be
in your home directory), they will be added from the package install directory
the next time foxglove is run. Foxglove updates will not overwrite the home
directory files, so you can delete them or merge your customizations after
updating foxglove.
