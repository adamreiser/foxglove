Foxglove - a firefox proxy profile manager
=======================

Manages ssh connections and associated Firefox proxy configurations.
This allows multiple distinct sessions to be run simultaneously. Themes
and CSS can be used to make different sessions visually distinctive.

----

When the script is called with a new profile name, a profile using the proxy
and containing the settings in prefs-base.js will be created. Subsequent
invocations with that name will use this profile. prefs.js contains some
reasonable security and privacy conscious defaults.

Installation and usage::

 python setup.py sdist
 sudo pip install dist/foxglove-0.0.1-dev1.tar.gz
 foxglove -h

Removal::

 sudo pip uninstall foxglove

