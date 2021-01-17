"""Foxglove - a Firefox profile and proxy manager."""
import os
import subprocess
import atexit
import socket
import argparse
import tempfile
import shlex
from shutil import copyfile, rmtree
import glob
from io import BytesIO
import requests
import mozprofile


def main():

    pkg_dir = os.path.split(os.path.abspath(__file__))[0]

    work_dir = os.path.join(os.path.expanduser('~'), '.foxglove')

    parser = argparse.ArgumentParser(description='foxglove - a Firefox \
                                     profile and proxy manager')

    parser.add_argument('--config', type=str, metavar="path", default=None,
                        help="path to a specific ssh config file to use")

    parser.add_argument('profile', type=str, help='the name of an existing \
                        foxglove profile or the name of the new profile to \
                        create')

    parser.add_argument('host', type=str, nargs='?', help='ssh server. If \
                        this is given, foxglove will attempt to establish an \
                        ssh connetion to the server and configure the browser \
                        to use it as a SOCKS proxy')

    parser.add_argument('--options', type=str, metavar="string", default="",
                        help='additional options to pass to firefox. \
                        Space-separated options should be entered as a single \
                        (e.g., double-quoted) argument.  (--no-remote, \
                        --new-instance, and --profile <path> will be \
                        automatically prepended)')

    # Note that this will prevent the profile from being saved
    parser.add_argument('-d', action="store_true", default=False,
                        help='dry run (don\'t launch browser)')

    parser.add_argument('-e', action="store_true", default=False,
                        help='ephemeral browser profile (delete on exit)')

    # Parse args before writing to disk (in case of error or -h)
    args = parser.parse_args()

    # Create the working directory
    if not os.path.isdir(work_dir):
        os.mkdir(work_dir, 0o700)

    # Create profiles subdirectory
    if not os.path.isdir(os.path.join(work_dir, 'profiles')):
        os.mkdir(os.path.join(work_dir, 'profiles'), 0o700)

    # Copy these files to the working directory if not present
    for data_file in ['prefs.js', 'addons.txt']:
        if not os.path.exists(os.path.join(work_dir, data_file)):
            copyfile(os.path.join(pkg_dir, data_file),
                     os.path.join(work_dir, data_file))

    # Create directory for add-on preferences
    if not os.path.isdir(os.path.join(work_dir, 'addon_prefs')):
        os.mkdir(os.path.join(work_dir, 'addon_prefs'), 0o700)

    # Populate add-on preference files from package directory
    for pref_path in glob.glob(os.path.join(pkg_dir, 'addon_prefs', '*.js')):
        if not os.path.exists(os.path.join(work_dir, 'addon_prefs',
                                           os.path.basename(pref_path))):
            copyfile(pref_path, os.path.join(work_dir, 'addon_prefs',
                                             os.path.basename(pref_path)))

    # Set up profile
    profile_dir = os.path.join(work_dir, 'profiles', args.profile)

    if not os.path.isdir(profile_dir):
        os.mkdir(profile_dir, 0o700)
        # Only install add-ons on new profile creation
        # FIXME automated add-on install is broken at present
        # install_addons = True
        install_addons = False
    else:
        install_addons = False

    # Preferences set in prefs.js persist across reloads
    prefs_obj = mozprofile.prefs.Preferences()
    prefs_obj.add(prefs_obj.read_prefs(os.path.join(work_dir, 'prefs.js')))

    # Persist add-on preferences
    for addon_pref_path in glob.glob(os.path.join(work_dir, 'addon_prefs',
                                                  '*.js')):
        prefs_obj.add(prefs_obj.read_prefs(addon_pref_path))

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

        # Get a random ephemeral port
        for attempt in range(0, 5):
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
                if attempt == 4:
                    raise(e)

        # Set proxy prefs
        prefs_obj.add({
            'network.proxy.socks_port': port,
            'network.proxy.socks': '127.0.0.1',
            'network.proxy.socks_remote_dns': True,
            'network.proxy.type': 1
        })

    addons_paths = []

    if install_addons:
        # Read list of add-ons to install
        with open(os.path.join(work_dir, 'addons.txt')) as addons_file:
            addons_list = addons_file.read().splitlines()

        # Filter comments
        addons_list = [i for i in addons_list if i[0] != '#']

        # mozprofile >=1.0.0 doesn't support automatic XPI downloading
        for addon_name in addons_list:
            rsp = requests.get(
                'https://addons.mozilla.org/firefox/downloads/latest/{}/'
                .format(addon_name), stream=True)

            rsp.raise_for_status()

            handle, name = tempfile.mkstemp(suffix=".xpi")
            addons_paths.append(name)
            # Needed to download at reasonable speed
            addon_io = BytesIO()
            for chunk in rsp.iter_content(chunk_size=1024):
                addon_io.write(chunk)
            addon_content = addon_io.getvalue()
            addon_io.close()
            os.write(handle, addon_content)
            os.close(handle)

            addon_prefs_file = os.path.join(work_dir, 'addon_prefs',
                                            '{}.js'.format(addon_name))

            # Set add-on prefs
            if os.path.exists(addon_prefs_file):
                prefs_obj.add(prefs_obj.read_prefs(addon_prefs_file))

    mozprofile.FirefoxProfile(profile=profile_dir,
                              preferences=prefs_obj._prefs,
                              addons=addons_paths,
                              restore=False)

    for addon_path in addons_paths:
        os.unlink(addon_path)

    if not args.d:
        subprocess.check_call(['firefox'] + ['--new-instance', '--no-remote',
                                             '--profile', profile_dir] +
                              shlex.split(args.options))
