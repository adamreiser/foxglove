# Foxglove - a Firefox profile manager

Foxglove is a Firefox wrapper with two purposes:

1. Programatically generate Firefox profiles with preferences that I consider
   desirable for the majority of use cases. These disable, where possible,
   Firefox's built-in advertising, pop-ups, telemetry, experiments, and similar
   features. Generated profiles are stored in `~/.foxglove`.

2. Optionally ssh to a remote host and configure the Firefox profile to use
   that connection as a SOCKS proxy.

```
usage: foxglove [-h] [--config path] [--chrome path] [--content path] [--options string] [-d] [-e] [-a [add-on]] profile [host]

foxglove - a Firefox profile and proxy manager

positional arguments:
  profile           the name of the foxglove-managed profile to use or create
  host              ssh server hostname. If this option is given, foxglove will attempt to use ssh(1) to connect to the host and configure Firefox to use
                    it as a SOCKS proxy

optional arguments:
  -h, --help        show this help message and exit
  --config path     path to a specific ssh config file to use
  --chrome path     path to a userChrome.css file to add to the Firefox profile
  --content path    path to a userContent.css file to add to the Firefox profile
  --options string  additional options to pass to Firefox. Space-separated options should be entered as a single (e.g., double-quoted) argument. (--no-
                    remote, --new-instance, and --profile <path> will be automatically prepended)
  -d                dry run (don't launch Firefox).
  -e                ephemeral profile (delete on exit)
  -a [add-on]       download and install add-on with this name. May be used multiple times
```

To use the "host" argument, configure a corresponding Host entry in your
`~/.ssh/config` such that you can ssh to it with no additional arguments. The
remote host must allow port forwarding.

Foxglove launches Firefox via a subprocess call to "firefox". On MacOS,
foxglove first appends `/Applications/Firefox.app/Contents/MacOS` to PATH.
Prepending a directory to PATH may be used to select a particular Firefox
installation. For example, you might launch Firefox Nightly on MacOS like this:

```bash
PATH="/Applications/Firefox Nightly.app/Contents/MacOS:$PATH" foxglove example
```

All foxglove data including profiles is stored in `~/.foxglove`, which will be
created on first run. Foxglove will not touch your regular Firefox profiles in
any way.

## Preferences
These settings have changed substantially during Firefox's development, so some
may be unsupported or meaningless in current versions.

Preference changes made to a foxglove-managed profile will reset to foxglove's
default values on the next run. To retain changes, you can either use the
generated profile as a normal Firefox profile without foxglove, or modify your
installation of foxglove's prefs.js file with your desired preferences.

Some foxglove defaults to consider changing:

| Key                               | Default | Foxglove | Comments                                       |
| --------------------------------- | ------- | -------- | -----------------------------------------------|
| dom.event.clipboardevents.enabled | true    | false    | May break some sites                           |
| privacy.resistFingerprinting      | false   | false    | May break some sites; can be counterproductive |
| privacy.donottrackheader.enabled  | false   | true     | May be used for fingerprinting                 |
| network.trr.mode                  | 0       | 0        | TRRs can interfere with test environments      |

## Related projects
- [Firefox Profilemaker](https://github.com/allo-/firefox-profilemaker)
