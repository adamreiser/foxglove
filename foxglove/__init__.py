"""Foxglove - a Firefox profile and proxy manager."""
import os
import platform
import subprocess
import atexit
import socket
import argparse
import tempfile
from io import BytesIO
from shutil import copyfile, rmtree
import requests
import mozprofile


def main():

    parser = argparse.ArgumentParser(description='foxglove - a Firefox \
                                     profile and proxy manager')

    parser.add_argument('--chrome', type=str, metavar="path", default=None,
                        help="path to a userChrome.css file to add to the \
                        profile")

    parser.add_argument('--content', type=str, metavar="path", default=None,
                        help="path to a userContent.css file to add to the \
                        profile")

    parser.add_argument('profile', type=str, help="the name of the \
                        foxglove-managed profile to use or create")

    parser.add_argument('host', type=str, nargs='?', help='ssh server \
                        hostname. If this option is given, foxglove will \
                        attempt to use ssh(1) to connect to the host and \
                        configure Firefox to use it as a SOCKS proxy')

    parser.add_argument('-d', action="store_true", default=False,
                        help='dry run (don\'t launch Firefox)')

    parser.add_argument('-e', action="store_true", default=False,
                        help='ephemeral (delete profile on exit)')

    parser.add_argument('-a', type=str, metavar="add-on", default=[],
                        action="append", help='download and install this \
                        add-on. Use the name as it appears in the Mozilla \
                        add-ons site URL. May be used multiple times')

    args = parser.parse_args()

    # Create the profile directory (and any intermediates) if necessary
    profile_dir = os.path.join(os.path.expanduser('~'), '.foxglove',
                               'profiles', args.profile)
    os.makedirs(os.path.join(profile_dir), 0o700, exist_ok=True)

    prefs_obj = mozprofile.prefs.Preferences()
    prefs_obj.add(prefs_obj.read_prefs(os.path.join(
                  os.path.split(os.path.abspath(__file__))[0], 'prefs.js')))

    if args.e:
        atexit.register(rmtree, profile_dir)

    if args.host:
        ssh_dir = tempfile.mkdtemp()
        cm_path = os.path.join(ssh_dir, '%C')
        ssh_base = ['ssh', '-qS', cm_path, args.host]
        cm_exit = ssh_base + ['-O', 'exit', args.host]

        # Exit functions run in reverse order
        atexit.register(os.rmdir, ssh_dir)
        atexit.register(subprocess.call, cm_exit)

        # Get a random ephemeral port and test to see if it's available.  Since
        # this imposes a TOCTOU race condition, try up to 5 times.
        max_tries = 5
        for attempt in range(0, max_tries):
            tmp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tmp_socket.bind(('127.0.0.1', 0))
            port = tmp_socket.getsockname()[1]
            tmp_socket.close()

            try:
                cm_connect = ssh_base + [
                                '-fNTM',
                                '-D',
                                '127.0.0.1:{:d}'.format(port), '-o',
                                'ExitOnForwardFailure=yes']

                # Connect to the ssh server
                if subprocess.check_call(cm_connect) == 0:
                    break
            except subprocess.CalledProcessError as e:
                if attempt == max_tries - 1:
                    raise e

        # Set proxy prefs
        prefs_obj.add({
            'network.proxy.socks_port': port,
            'network.proxy.socks': '127.0.0.1',
            'network.proxy.socks_remote_dns': True,
            'network.proxy.type': 1
        })

    addon_paths = []
    for addon_name in args.a:
        rsp = requests.get(
            'https://addons.mozilla.org/firefox/downloads/latest/{}'
            .format(addon_name), stream=True)
        rsp.raise_for_status()
        handle, name = tempfile.mkstemp(suffix=".xpi")
        addon_paths.append(name)
        with BytesIO() as addon_io:
            for chunk in rsp.iter_content(chunk_size=1024):
                addon_io.write(chunk)
            os.write(handle, addon_io.getvalue())
        os.close(handle)

    mozprofile.FirefoxProfile(profile=profile_dir,
                              preferences=prefs_obj._prefs,
                              addons=addon_paths,
                              restore=False)

    if args.chrome:
        os.makedirs(os.path.join(profile_dir, "chrome"), exist_ok=True)
        copyfile(args.chrome,
                 os.path.join(profile_dir, "chrome", "userChrome.css"))

    if args.content:
        os.makedirs(os.path.join(profile_dir, "chrome"), exist_ok=True)
        copyfile(args.content,
                 os.path.join(profile_dir, "chrome", "userContent.css"))

    if platform.system() == "Darwin":
        os.environ["PATH"] = os.getenv("PATH") + os.pathsep + os.path.join(
                             os.sep, "Applications", "Firefox.app", "Contents",
                             "MacOS")

    if not args.d:
        subprocess.check_call(['firefox'] + ['--new-instance', '--no-remote',
                                             '--profile', profile_dir])
