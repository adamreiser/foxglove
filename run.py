#!/usr/bin/env python3

import os, sys, subprocess, atexit, shutil, warnings, re
import socket, argparse

work_dir = os.path.dirname(sys.argv[0])
ssh_dir = os.path.join(os.path.expanduser('~'), '.ssh')

parser = argparse.ArgumentParser(description='Manages Firefox proxy sessions.')

config = dict()

parser.add_argument('profile', type=str, help='The name of the profile to use')
parser.add_argument('host', type=str, help='The server to connect to')
parser.add_argument('-p', type=int, metavar='N', nargs='?', default=0, help='The port to forward over (default: random)')

args = parser.parse_args()

# TODO: try another port if it fails to bind
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('127.0.0.1', args.p))
    args.p = str(s.getsockname()[1])

cm_path = os.path.join(ssh_dir, args.profile + '_%r@%h:%p')
ssh_base = ['ssh', '-S', cm_path, args.host]
cm_connect = ssh_base + ['-fNTM', '-D 127.0.0.1:' + args.p, \
        '-o', 'ExitOnForwardFailure=yes']
cm_check = ssh_base + ['-O', 'check', args.host]
cm_exit = ssh_base + ['-O', 'exit', args.host]

# Register exit handler before connecting
atexit.register(subprocess.call, cm_exit)

# Connect to proxy
subprocess.check_call(cm_connect)

# Set up profile
profile_dir = os.path.join(work_dir, 'profiles', args.profile)

# Workaround for < 3.4.1 https://docs.python.org/3/library/os.html#os.makedirs
try:
    os.makedirs(profile_dir, 0o700, exist_ok = True)
except FileExistsError:
    pass

prefs_path = os.path.join(profile_dir, 'prefs.js')

# If no prefs file exists, create it
if not os.path.exists(prefs_path):
    if os.path.exists(os.path.join(work_dir, 'prefs.js')):
        shutil.copyfile(os.path.join(work_dir, 'prefs.js'), prefs_path)
    else:
        warnings.warn("Could not find prefs.js.")

    with open(prefs_path, 'a') as p_file:
        p_file.write("""user_pref("network.proxy.socks", "127.0.0.1");\n""")
        p_file.write("""user_pref("network.proxy.socks_port", {});\n""".
                format(args.p))
        p_file.write("""user_pref("network.proxy.socks_remote_dns", true);\n""")
        p_file.write("""user_pref("network.proxy.type", 1);\n""")

# Update existing prefs with correct port
else:
    with open(prefs_path, 'r') as p_file:
        prefs = []
        for line in p_file.readlines():
            line = re.sub("^user_pref\(\"network.proxy.socks_port\", \d+", \
                    "user_pref(\"network.proxy.socks_port\", {}"\
                    .format(args.p), line)
            prefs.append(line)
    with open(prefs_path, 'w') as p_file:
        for line in prefs:
            p_file.write(line)

subprocess.call(['firefox', '--new-instance', '--no-remote', '--profile', profile_dir])
