# Proxy Profile Manager for Firefox

## Purpose
Manages ssh connections and associated Firefox proxy configurations.
This allows multiple distinct sessions to be run simultaneously. Themes
and CSS can be used to make different sessions visually distinctive.

## Usage

```bash
$ ./run.py -h
usage: run.py [-h] profile host

Manages Firefox proxy sessions.

positional arguments:
  profile     The name of the profile to use
  host        The server to connect to

optional arguments:
  -h, --help  show this help message and exit
```

When the script is called with a new profile name, a profile using the proxy
and containing the settings in prefs-base.js will be created. Subsequent
invocations with that name will use this profile.

prefs-base.js contains some reasonable security and privacy conscious
defaults for the new profile. If you want a standard firefox configuration 
(except for proxy settings) delete or comment out the file contents.

## Ideas
- Enforce network isolation using a sandbox.
- Use a visually distinctive theme to distinguish proxy sessions from
normal browser windows.

## Acknowledgements
- Some ideas for default settings came from https://ffprofile.com/

- Privacy settings were tested with https://browserleaks.com/ip
