"""Foxglove - a Firefox profile and proxy manager."""

from __future__ import annotations

import argparse
import atexit
import os
import platform
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from shutil import copyfile, rmtree
from urllib.parse import quote

import requests
from mozprofile import FirefoxProfile
from mozprofile.prefs import Preferences

try:
    import importlib.metadata as metadata

    __version__ = metadata.version("foxglove")
except metadata.PackageNotFoundError:
    __version__ = "0.0.0"

FOXGLOVE_DIR = Path.home() / ".foxglove" / "profiles"
PREFS_PATH = Path(__file__).parent / "prefs.js"
AMO_DOWNLOAD_URL = "https://addons.mozilla.org/firefox/downloads/latest/"
MACOS_FIREFOX_PATH = Path("/Applications/Firefox.app/Contents/MacOS")


def _start_ssh_tunnel(
    host: str, cm_path: Path, *, max_attempts: int = 5
) -> tuple[list[str], str, int]:
    """Start an SSH SOCKS tunnel, returning the control command and bound port.

    Finds an available ephemeral port and immediately attempts to start the SSH
    tunnel on it. If another process grabs the port in the window between
    discovery and SSH binding (TOCTOU race), the attempt fails and a new port
    is selected. Non-port-related SSH failures (e.g. auth, network) are
    re-raised immediately.
    """
    ssh_prefix = ["ssh", "-qS", str(cm_path)]

    for attempt in range(max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]

        cm_connect = [
            *ssh_prefix,
            "-fNTM",
            "-D",
            f"127.0.0.1:{port}",
            "-o",
            "ExitOnForwardFailure=yes",
            "--",
            host,
        ]
        try:
            subprocess.check_call(cm_connect)
            return ssh_prefix, host, port
        except subprocess.CalledProcessError as exc:
            # Exit code 255 is SSH's generic connection/forwarding error,
            # which includes port-bind failures. Any other code likely
            # indicates a non-transient problem (e.g. auth failure).
            if exc.returncode != 255 or attempt == max_attempts - 1:
                raise


def _download_addon(name: str) -> Path:
    """Download an add-on from AMO and return the path to the temp XPI file."""
    url = AMO_DOWNLOAD_URL + quote(name, safe="")
    rsp = requests.get(url, stream=True, timeout=30)
    rsp.raise_for_status()

    handle, path_str = tempfile.mkstemp(suffix=".xpi")
    try:
        for chunk in rsp.iter_content(chunk_size=8192):
            os.write(handle, chunk)
    finally:
        os.close(handle)

    return Path(path_str)


def _resolve_profile_dir(profile: str, *, root: Path) -> Path:
    """Resolve and validate the target profile directory under root."""
    if not profile.strip():
        raise ValueError("profile name must not be empty")

    root_resolved = root.resolve()
    profile_dir = (root / profile).resolve()
    if not profile_dir.is_relative_to(root_resolved):
        raise ValueError(f"profile path resolves outside foxglove profiles directory: {profile!r}")

    return profile_dir


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        description="foxglove - a Firefox profile and proxy manager",
    )
    parser.add_argument(
        "--chrome",
        type=Path,
        metavar="path",
        default=None,
        help="path to a userChrome.css file to add to the profile",
    )
    parser.add_argument(
        "--content",
        type=Path,
        metavar="path",
        default=None,
        help="path to a userContent.css file to add to the profile",
    )
    parser.add_argument(
        "profile",
        type=str,
        help="the name of the foxglove-managed profile to use or create",
    )
    parser.add_argument(
        "host",
        type=str,
        nargs="?",
        help="ssh server hostname; foxglove will connect via ssh(1) and configure "
        "Firefox to use it as a SOCKS proxy",
    )
    parser.add_argument(
        "-d",
        action="store_true",
        default=False,
        help="dry run (don't launch Firefox)",
    )
    parser.add_argument(
        "-e",
        action="store_true",
        default=False,
        help="ephemeral (delete profile on exit)",
    )
    parser.add_argument(
        "-a",
        type=str,
        metavar="add-on",
        default=[],
        action="append",
        help="download and install this add-on (name from the AMO URL); repeatable",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the foxglove CLI."""
    args = _build_parser().parse_args(argv)

    try:
        profile_dir = _resolve_profile_dir(args.profile, root=FOXGLOVE_DIR)
    except ValueError as exc:
        print(f"foxglove: {exc}", file=sys.stderr)
        return 2

    profile_dir.mkdir(parents=True, mode=0o700, exist_ok=True)

    prefs = Preferences.read_prefs(str(PREFS_PATH))

    if args.e:
        atexit.register(rmtree, str(profile_dir))

    if args.host:
        # Use /tmp explicitly — macOS has socket path length limits
        ssh_dir = Path(tempfile.mkdtemp(dir="/tmp"))
        cm_path = ssh_dir / "%C"

        ssh_prefix, host, port = _start_ssh_tunnel(args.host, cm_path)

        cm_exit = [*ssh_prefix, "-O", "exit", "--", host]
        atexit.register(os.rmdir, str(ssh_dir))
        atexit.register(subprocess.call, cm_exit)

        prefs.extend(
            [
                ("network.proxy.socks_port", port),
                ("network.proxy.socks", "127.0.0.1"),
                ("network.proxy.socks_remote_dns", True),
                ("network.proxy.type", 1),
            ]
        )

    addon_paths = [_download_addon(name) for name in args.a]

    try:
        FirefoxProfile(
            profile=str(profile_dir),
            preferences=dict(prefs),
            addons=[str(p) for p in addon_paths],
            restore=False,
        )
    finally:
        for p in addon_paths:
            p.unlink(missing_ok=True)

    chrome_dir = profile_dir / "chrome"
    if args.chrome:
        chrome_dir.mkdir(exist_ok=True)
        copyfile(args.chrome, chrome_dir / "userChrome.css")
    if args.content:
        chrome_dir.mkdir(exist_ok=True)
        copyfile(args.content, chrome_dir / "userContent.css")

    if platform.system() == "Darwin":
        os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + str(MACOS_FIREFOX_PATH)

    if not args.d:
        subprocess.check_call(
            [
                "firefox",
                "--new-instance",
                "--no-remote",
                "--profile",
                str(profile_dir),
            ]
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
