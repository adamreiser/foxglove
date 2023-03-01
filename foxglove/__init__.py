"""Foxglove - a Firefox profile and proxy manager."""
import os
import platform
import subprocess
import atexit
import socket
import argparse
import tempfile
import shlex
from shutil import copyfile, rmtree
import mozprofile


def main():

    pkg_dir = os.path.split(os.path.abspath(__file__))[0]

    work_dir = os.path.join(os.path.expanduser('~'), '.foxglove')

    parser = argparse.ArgumentParser(description='foxglove - a Firefox \
                                     profile and proxy manager')

    parser.add_argument('--config', type=str, metavar="path", default=None,
                        help="path to a specific ssh config file to use")

    parser.add_argument('--chrome', type=str, metavar="path", default=None,
                        help="path to a userChrome.css file to add to the \
                        Firefox profile")

    parser.add_argument('--content', type=str, metavar="path", default=None,
                        help="path to a userContent.css file to add to the \
                        Firefox profile")

    parser.add_argument('profile', type=str, help="The name of the \
                        foxglove-managed profile to use or create")

    parser.add_argument('host', type=str, nargs='?', help='ssh server \
                        hostname. If this option is given, foxglove will \
                        attempt to use ssh(1) to connect to the host and \
                        configure Firefox to use it as a SOCKS proxy')

    parser.add_argument('--options', type=str, metavar="string", default="",
                        help='additional options to pass to Firefox. \
                        Space-separated options should be entered as a single \
                        (e.g., double-quoted) argument.  (--no-remote, \
                        --new-instance, and --profile <path> will be \
                        automatically prepended)')

    # Note that this will prevent the profile from being saved
    parser.add_argument('-d', action="store_true", default=False,
                        help='dry run (don\'t launch Firefox)')

    parser.add_argument('-e', action="store_true", default=False,
                        help='ephemeral profile (delete on exit)')

    # Parse args before writing to disk (in case of error or -h)
    args = parser.parse_args()

    os.makedirs(work_dir, 0o700, exist_ok=True)

    # Create profiles subdirectory
    os.makedirs(os.path.join(work_dir, 'profiles'), 0o700, exist_ok=True)

    # Set up profile
    profile_dir = os.path.join(work_dir, 'profiles', args.profile)

    if not os.path.isdir(profile_dir):
        os.mkdir(profile_dir, 0o700)

    prefs_obj = mozprofile.prefs.Preferences()
    prefs_obj.add(prefs_obj.read_prefs(os.path.join(pkg_dir, 'prefs.js')))

    if args.e:
        atexit.register(rmtree, profile_dir)

    # If host option is specified, connect to proxy
    if args.host:

        ssh_dir = tempfile.mkdtemp()
        cm_path = os.path.join(ssh_dir, '%C')
        ssh_base = ['ssh', '-qS', cm_path, args.host]

        if args.config is not None:
            ssh_base += ['-F', args.config]

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
                    raise(e)

        # Set proxy prefs
        prefs_obj.add({
            'network.proxy.socks_port': port,
            'network.proxy.socks': '127.0.0.1',
            'network.proxy.socks_remote_dns': True,
            'network.proxy.type': 1
        })

    mozprofile.FirefoxProfile(profile=profile_dir,
                              preferences=prefs_obj._prefs,
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
        append_path = os.path.join(os.sep, "Applications", "Firefox.app",
                                   "Contents", "MacOS")

        os.environ["PATH"] = os.getenv("PATH") + os.pathsep + append_path

    if not args.d:
        subprocess.check_call(['firefox'] + ['--new-instance', '--no-remote',
                                             '--profile', profile_dir] +
                              shlex.split(args.options))
