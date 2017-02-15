import os
import subprocess
import atexit
import socket
import argparse
import tempfile
import mozprofile
from shutil import copyfile


def main():
    pkg_dir = os.path.split(os.path.abspath(__file__))[0]

    # TODO: make sure we're not appropriating someone else's directory
    work_dir = os.path.join(os.environ['HOME'], '.foxglove')

    if not os.path.isdir(work_dir):
        os.mkdir(work_dir, 0o700)

    if not os.path.isdir(os.path.join(work_dir, 'profiles')):
        os.mkdir(os.path.join(work_dir, 'profiles'), 0o700)

    if not os.path.exists(os.path.join(work_dir, 'prefs.js')):
        copyfile(os.path.join(pkg_dir, 'prefs.js'),
                 os.path.join(work_dir, 'prefs.js'))

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

    parser.add_argument('-d', action="store_true", default=False,
                        help='Dry run (don\'t launch browser)')

    parser.add_argument('--prefs', metavar='PATH',
                        default=os.path.join(work_dir, 'prefs.js'),
                        help="Path to the common preferences file \
                             (default: {})".format(os.path.join(
                             '~', '.foxglove', 'prefs.js')))

    args = parser.parse_args()

    assert(os.path.exists(args.prefs))

    if args.port == 0:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', args.port))
        args.port = s.getsockname()[1]
        s.close()

    # Set up profile
    profile_dir = os.path.join(work_dir, 'profiles', args.profile)

    if not os.path.isdir(profile_dir):
        os.mkdir(profile_dir, 0o700)

    # Preferences set in common prefs.js will stick across reloads
    prefs_obj = mozprofile.prefs.Preferences()
    prefs_obj.add(prefs_obj.read_prefs(args.prefs))
    prefs_dict = dict(prefs_obj._prefs)

    # If host is specified, do proxy
    if args.host:
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

        # Set proxy args if using one
        prefs_dict.update({
            'network.proxy.socks_port': args.port,
            'network.proxy.socks': '127.0.0.1',
            'network.proxy.socks_remote_dns': True,
            'network.proxy.type': 1
        })

    # No proxy - use system proxy settings
    else:
        prefs_dict.update({'network.proxy.type': 5})

    # The assignment is necessary even though we don't use mod_profile
    mod_profile = mozprofile.FirefoxProfile(profile=profile_dir,
                                            preferences=prefs_dict)

    if (not args.d):
        subprocess.call(['firefox', '--new-instance',
                         '--no-remote', '--profile', profile_dir])
