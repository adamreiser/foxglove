# foxglove

Foxglove is a Firefox wrapper with two purposes:

1. Programmatically generate Firefox profiles with preferences that disable,
   where possible, Firefox's built-in advertising, pop-ups, telemetry,
   experiments, and similar features. Generated profiles are stored in
   `~/.foxglove/profiles`.

2. Optionally ssh to a remote host and configure the Firefox profile to use
   that connection as a SOCKS proxy.

## Installation

Requires Python 3.10+.

```bash
pip install foxglove
```

## Usage

```text
usage: foxglove [-h] [--chrome path] [--content path] [-d] [-e] [-a add-on]
                profile [host]

foxglove - a Firefox profile and proxy manager

positional arguments:
  profile         the name of the foxglove-managed profile to use or create
  host            SSH server hostname; foxglove will connect via ssh(1) and
                  configure Firefox to use it as a SOCKS proxy

options:
  -h, --help      show this help message and exit
  --chrome path   path to a userChrome.css file to add to the profile
  --content path  path to a userContent.css file to add to the profile
  -d              dry run (don't launch Firefox)
  -e              ephemeral (delete profile on exit)
  -a add-on       download and install an add-on from addons.mozilla.org;
                  repeatable
```

**Add-ons (`-a`) —** The value for `-a` is the URL slug after `/firefox/addon/`
on the [Mozilla Add-ons](https://addons.mozilla.org/) page; for example,
`https://addons.mozilla.org/firefox/addon/ublock-origin/` → `-a ublock-origin`.
You can pass `-a` multiple times to install several extensions.

To use the "host" argument, configure a corresponding Host entry in your
`~/.ssh/config` such that you can ssh to it with no additional arguments. The
remote host must allow port forwarding.

Foxglove launches Firefox via a subprocess call to "firefox". On macOS, the
Firefox binary is not typically in PATH, so foxglove first appends
`/Applications/Firefox.app/Contents/MacOS` to PATH. Prepending another
directory to PATH may be used to select a particular Firefox installation. For
example, you might launch Firefox Nightly on macOS like this:

```bash
PATH="/Applications/Firefox Nightly.app/Contents/MacOS:$PATH" foxglove example
```

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Test
uv run pytest
```

## Preferences

Foxglove preferences target Firefox 135+ and are cross-referenced with
[arkenfox user.js](https://github.com/arkenfox/user.js). See
[prefs.js](foxglove/prefs.js) for the full list.

Preference changes made to a foxglove-managed profile will reset to foxglove's
default values on the next run. To retain changes, you can either use the
generated profile as a normal Firefox profile without foxglove, or modify your
installation of foxglove's prefs.js file with your desired preferences.

Some foxglove defaults to consider changing:

| Key                               | Default | Foxglove | Comments                                              |
| --------------------------------- | ------- | -------- | ----------------------------------------------------- |
| dom.event.clipboardevents.enabled | true    | false    | May break copy/paste on some sites                    |
| media.peerconnection.enabled      | true    | false    | Breaks video calls                                    |
| network.trr.mode                  | 0       | 0        | Set to 2 or 3 to enable DNS-over-HTTPS                |

## Related projects

- [Firefox Profilemaker](https://github.com/allo-/firefox-profilemaker)
