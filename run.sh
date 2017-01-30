#!/bin/bash

# Usage: run.sh config.json

# Existing environment variables override config.json

PPM_PROJECT_DIR=$(dirname "$0")

ppm_cleanup () {
    rm "${PPM_PROJECT_DIR}/.env"
    $PPM_CM_CLOSE
    exit "$1"
}

python - "$1" <<EOF

import sys, pipes, json, os

config = open(sys.argv[1], 'r').read()
output = open("${PPM_PROJECT_DIR}/.env", 'w')

for k, v in json.loads(config).items():
    k = pipes.quote(k)
    v = pipes.quote(v)
    if k not in os.environ:
        output.write("export %s=%s;\n" % (k, v))

output.close()
EOF

if [ $? == 0 ]; then
    source "${PPM_PROJECT_DIR}/.env"
else
    echo "Could not source environment"
    ppm_cleanup 1
fi

# Define after sourcing the environment
PPM_TEST_PORT="nc -nvz 127.0.0.1 ${PPM_PORT}"
PPM_CM_PATH=~/.ssh/cm_PPM-${PPM_PROFILE}_%r@%h:%p
PPM_CM_BASE_CMD="ssh -S ${PPM_CM_PATH} -O"
PPM_CM_CHECK="${PPM_CM_BASE_CMD} check ${PPM_PROXY}"
PPM_CM_CLOSE="${PPM_CM_BASE_CMD} exit ${PPM_PROXY}"

trap 'cleanup 1' SIGHUP SIGINT SIGTERM

if $PPM_TEST_PORT > /dev/null 2>&1; then
    echo "Port ${PPM_PORT} already in use"
    if $PPM_CM_CHECK > /dev/null 2>&1; then
        echo "...and we control it; continuing"
    else
        ppm_cleanup 1
    fi
else
    if ssh -fNT "${PPM_PROXY}" -M -S "${PPM_CM_PATH}" -D "127.0.0.1:${PPM_PORT}"; then
        echo "Opened tunnel on port ${PPM_PORT}"
    else
        echo "Failed to open tunnel on port ${PPM_PORT}"
        ppm_cleanup 1
    fi
fi

if [ ! -d "${PPM_PROJECT_DIR}/profiles" ]; then
    echo "Could not find profiles directory; check that it exists in project directory"
    ppm_cleanup 1
fi

# If this profile doesn't already exist, create it
if [ ! -d "${PPM_PROJECT_DIR}/profiles/${PPM_PROFILE}" ]; then
    mkdir "${PPM_PROJECT_DIR}/profiles/${PPM_PROFILE}"

    if [ -e "${PPM_PROJECT_DIR}/prefs-base.js" ]; then
        cp  "${PPM_PROJECT_DIR}/prefs-base.js" \
            "${PPM_PROJECT_DIR}/profiles/${PPM_PROFILE}/prefs.js"
    else
        echo "Could not find prefs-base.js; check that it exists in project directory"
        ppm_cleanup 1
    fi

    cat << EOF >> ${PPM_PROJECT_DIR}/profiles/${PPM_PROFILE}/prefs.js
    user_pref("network.proxy.socks", "127.0.0.1");
    user_pref("network.proxy.socks_port", ${PPM_PORT});
    user_pref("network.proxy.socks_remote_dns", true);
    user_pref("network.proxy.type", 1);
EOF
fi

firefox --new-instance --no-remote --profile "${PPM_PROJECT_DIR}/profiles/${PPM_PROFILE}"

ppm_cleanup 0
