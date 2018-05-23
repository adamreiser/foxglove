import os
import subprocess
import atexit
import socket
import argparse
import tempfile
from shutil import copyfile
import glob
from io import BytesIO
import requests
import mozprofile


def main():
    pkg_dir = os.path.split(os.path.abspath(__file__))[0]

    # TODO: make sure we're not appropriating someone else's directory
    work_dir = os.path.join(os.environ['HOME'], '.foxglove')

    parser = argparse.ArgumentParser(description='Manages Firefox profiles')

    parser.add_argument('profile',
                        type=str, help='Firefox profile name - \
                        only foxglove-managed profiles')

    parser.add_argument('host', type=str, nargs='?',
                        help='ssh server. If this is given, foxglove \
                             will attempt to establish an ssh tunnel to \
                             the server and configure the browser to use \
                             it as a SOCKS proxy.')

    # TODO: port range
    parser.add_argument('--port', type=int,
                        metavar='N', nargs='?', default=0,
                        help='The local port to forward the proxy over \
                             (default: random)')

    # Note that this will prevent the profile from being saved
    parser.add_argument('-d', action="store_true", default=False,
                        help='Dry run (don\'t launch browser)')

    parser.add_argument('--prefs', metavar='PATH',
                        default=os.path.join(work_dir, 'prefs.js'),
                        help="Path to the common preferences file \
                             (default: {})".format(os.path.join(
                             '~', '.foxglove', 'prefs.js')))

    # Parse args before writing to disk (in case of error or -h)
    args = parser.parse_args()

    # TODO: All this should really be done on install
    # Create the working directory
    if not os.path.isdir(work_dir):
        os.mkdir(work_dir, 0o700)

    # Create profiles subdirectory
    if not os.path.isdir(os.path.join(work_dir, 'profiles')):
        os.mkdir(os.path.join(work_dir, 'profiles'), 0o700)

    # Copy these files to the working directory
    for data_file in ['prefs.js', 'addons.txt']:
        if not os.path.exists(os.path.join(work_dir, data_file)):
            copyfile(os.path.join(pkg_dir, data_file),
                     os.path.join(work_dir, data_file))

    # Create directory for add-on preferences
    if not os.path.isdir(os.path.join(work_dir, 'addon_prefs')):
        os.mkdir(os.path.join(work_dir, 'addon_prefs'), 0o700)

    # Populate addon preferences
    for pref in glob.glob(os.path.join(pkg_dir, 'addon_prefs', '*.js')):
        if not os.path.exists(os.path.join(work_dir, 'addon_prefs',
                                           os.path.basename(pref))):
            copyfile(pref, os.path.join(work_dir, 'addon_prefs',
                                        os.path.basename(pref)))

    assert os.path.exists(args.prefs)

    # Set up profile
    profile_dir = os.path.join(work_dir, 'profiles', args.profile)

    if not os.path.isdir(profile_dir):
        os.mkdir(profile_dir, 0o700)
        # Only install add-ons on new profile creation
        install_addons = True
    else:
        install_addons = False

    # Preferences set in prefs.js persist across reloads
    # Add-on prefs do not, however (FIXME?)
    prefs_obj = mozprofile.prefs.Preferences()
    prefs_obj.add(prefs_obj.read_prefs(args.prefs))
    prefs_dict = dict(prefs_obj._prefs)

    # If host option is specified, set up proxy
    if args.host:
        # Get a random port
        if args.port == 0:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('127.0.0.1', args.port))
            args.port = s.getsockname()[1]
            s.close()

        ssh_dir = tempfile.mkdtemp()
        cm_path = os.path.join(ssh_dir, args.profile + '_%r@%h:%p')
        ssh_base = ['ssh', '-S', cm_path, args.host]
        cm_connect = ssh_base + ['-fNTM', '-D 127.0.0.1:' + str(args.port),
                                 '-o', 'ExitOnForwardFailure=yes']
        cm_exit = ssh_base + ['-O', 'exit', args.host]

        # Exit functions run in reverse order
        atexit.register(os.rmdir, ssh_dir)
        atexit.register(subprocess.call, cm_exit)

        # Connect to proxy
        subprocess.check_call(cm_connect)

        # Set proxy prefs
        prefs_dict.update({
            'network.proxy.socks_port': args.port,
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
            r = requests.get(
                'https://addons.mozilla.org/firefox/downloads/latest/{}/'
                .format(addon_name), stream=True)

            if r.status_code == 200:
                handle, name = tempfile.mkstemp(suffix=".xpi")
                addons_paths.append(name)
                addon_io = BytesIO()
                for chunk in r.iter_content(chunk_size=1024):
                    addon_io.write(chunk)
                addon_content = addon_io.getvalue()
                addon_io.close()
                os.write(handle, addon_content)
                os.close(handle)

                addon_prefs_file = os.path.join(work_dir, 'addon_prefs',
                                                '{}.js'.format(addon_name))

                # TODO error handling

                # Set addon-specific prefs
                if os.path.exists(addon_prefs_file):
                    prefs_obj.add(prefs_obj.read_prefs(addon_prefs_file))
                    prefs_dict.update(dict(prefs_obj._prefs))

    mozprofile.FirefoxProfile(profile=profile_dir,
                              preferences=prefs_dict,
                              addons=addons_paths,
                              restore=False)

    for addon_path in addons_paths:
        os.unlink(addon_path)

    if not args.d:
        subprocess.call(['firefox', '--new-instance',
                         '--no-remote', '--profile', profile_dir])
