# Proxy Profile Manager for Firefox

## Purpose
Manages ssh connections and associated Firefox proxy configurations.
This allows multiple distinct sessions to be run simultaneously. Themes
and CSS can be used to make different sessions visually distinctive.

## Example Usage

1. Clone this repository as (e.g.) ~/scripts/ppm

2. Use the config-example.json template to create (e.g.) config.json

3. Use your preferred method to launch the script; for example, set
`alias ffproxy="~/scripts/ppm/run.sh ~/scripts/ppm/config.json"`

When ffproxy is first run, a profile using the proxy and containing the
settings in prefs-base.js will be created. Subsequent invocations with
the same config.json will use this profile.

- PPM_PROXY - the server to tunnel traffic through; must be able to `ssh server_name`
- PPM_PROFILE - the profile name to use with firefox; can be anything
- PPM_PORT - the port to open on localhost to tunnel traffic through.

prefs-base.js contains some reasonable security and privacy conscious
configurations, which will be used for the new profile. If you want a
standard firefox configuration (except for proxy settings) delete or
comment out the file contents.

## Ideas
- Enforce network isolation using a sandbox.
- Use a visually distinctive theme to distinguish proxy sessions from
normal browser windows.

## Acknowledgements
- Some ideas for default settings came from https://ffprofile.com/

- The JSON to environment converter is based on https://gist.github.com/kr/6161118

- Privacy settings were tested with https://browserleaks.com/ip
