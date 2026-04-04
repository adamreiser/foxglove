"""Tests for foxglove CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest import mock

import pytest
import requests

import foxglove
from foxglove import (
    FOXGLOVE_DIR,
    PREFS_PATH,
    _build_parser,
    _download_addon,
    _start_ssh_tunnel,
    main,
)


class TestBuildParser:
    """Tests for argument parsing."""

    def test_minimal_args(self):
        parser = _build_parser()
        args = parser.parse_args(["myprofile"])
        assert args.profile == "myprofile"
        assert args.host is None
        assert args.d is False
        assert args.e is False
        assert args.a is None
        assert args.chrome is None
        assert args.content is None

    def test_all_args(self, tmp_path: Path):
        chrome_file = tmp_path / "userChrome.css"
        chrome_file.touch()
        content_file = tmp_path / "userContent.css"
        content_file.touch()

        parser = _build_parser()
        args = parser.parse_args(
            [
                "--chrome",
                str(chrome_file),
                "--content",
                str(content_file),
                "-d",
                "-e",
                "-a",
                "ublock-origin",
                "-a",
                "privacy-badger17",
                "myprofile",
                "myhost",
            ]
        )
        assert args.profile == "myprofile"
        assert args.host == "myhost"
        assert args.d is True
        assert args.e is True
        assert args.a == ["ublock-origin", "privacy-badger17"]
        assert args.chrome == chrome_file
        assert args.content == content_file

    def test_missing_profile_exits(self):
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestStartSshTunnel:
    """Tests for SSH tunnel startup with integrated port selection."""

    def test_happy_path_returns_base_cmd_and_port(self, tmp_path: Path):
        cm_path = tmp_path / "%C"

        with mock.patch("foxglove.subprocess.check_call") as mock_call:
            mock_call.return_value = 0
            ssh_prefix, host, port = _start_ssh_tunnel("myhost", cm_path)

        assert ssh_prefix == ["ssh", "-qS", str(cm_path)]
        assert host == "myhost"
        assert isinstance(port, int)
        assert 1024 <= port <= 65535
        mock_call.assert_called_once()
        call_args = mock_call.call_args[0][0]
        assert call_args == [
            "ssh",
            "-qS",
            str(cm_path),
            "-fNTM",
            "-D",
            f"127.0.0.1:{port}",
            "-o",
            "ExitOnForwardFailure=yes",
            "--",
            "myhost",
        ]

    def test_host_option_like_value_is_placed_after_double_dash(self, tmp_path: Path):
        cm_path = tmp_path / "%C"
        injected_host = "-oProxyCommand=touch /tmp/owned"

        with mock.patch("foxglove.subprocess.check_call") as mock_call:
            mock_call.return_value = 0
            _start_ssh_tunnel(injected_host, cm_path)

        call_args = mock_call.call_args[0][0]
        dashdash_idx = call_args.index("--")
        assert call_args[dashdash_idx + 1] == injected_host
        assert call_args[-1] == injected_host

    def test_retries_on_port_conflict(self, tmp_path: Path):
        """A returncode-255 failure (port stolen) triggers a retry."""
        cm_path = tmp_path / "%C"
        conflict = subprocess.CalledProcessError(255, "ssh")

        with mock.patch("foxglove.subprocess.check_call") as mock_call:
            mock_call.side_effect = [conflict, 0]
            ssh_prefix, host, port = _start_ssh_tunnel("myhost", cm_path, max_attempts=3)

        assert mock_call.call_count == 2
        assert ssh_prefix == ["ssh", "-qS", str(cm_path)]
        assert host == "myhost"
        assert isinstance(port, int)

    def test_raises_immediately_on_non_port_error(self, tmp_path: Path):
        """Non-255 exit codes (e.g. auth failure) are not retried."""
        cm_path = tmp_path / "%C"
        auth_error = subprocess.CalledProcessError(1, "ssh")

        with mock.patch("foxglove.subprocess.check_call") as mock_call:
            mock_call.side_effect = auth_error
            with pytest.raises(subprocess.CalledProcessError) as exc_info:
                _start_ssh_tunnel("myhost", cm_path, max_attempts=3)

        assert exc_info.value.returncode == 1
        mock_call.assert_called_once()

    def test_raises_after_exhausting_attempts(self, tmp_path: Path):
        cm_path = tmp_path / "%C"
        conflict = subprocess.CalledProcessError(255, "ssh")

        with mock.patch("foxglove.subprocess.check_call") as mock_call:
            mock_call.side_effect = conflict
            with pytest.raises(subprocess.CalledProcessError):
                _start_ssh_tunnel("myhost", cm_path, max_attempts=2)

        assert mock_call.call_count == 2


class TestDownloadAddon:
    """Tests for add-on downloading."""

    def test_download_success(self, tmp_path: Path):
        fake_content = b"PK\x03\x04fake-xpi-content"

        with mock.patch("foxglove.requests.get") as mock_get:
            mock_response = mock.MagicMock()
            mock_response.iter_content.return_value = [fake_content]
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = _download_addon("test-addon")

            assert result.suffix == ".xpi"
            assert result.exists()
            assert result.read_bytes() == fake_content
            mock_get.assert_called_once_with(
                "https://addons.mozilla.org/firefox/downloads/latest/test-addon",
                stream=True,
                timeout=30,
            )
            result.unlink()

    def test_download_url_encodes_slug(self):
        """Slugs with special characters are percent-encoded, not passed to str.format."""
        with mock.patch("foxglove.requests.get") as mock_get:
            mock_response = mock.MagicMock()
            mock_response.iter_content.return_value = [b"PK"]
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = _download_addon("addon{weird}")

            mock_get.assert_called_once_with(
                "https://addons.mozilla.org/firefox/downloads/latest/addon%7Bweird%7D",
                stream=True,
                timeout=30,
            )
            result.unlink()

    def test_download_http_error(self):
        with mock.patch("foxglove.requests.get") as mock_get:
            mock_response = mock.MagicMock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response

            with pytest.raises(requests.HTTPError, match="404"):
                _download_addon("nonexistent-addon")


class TestMain:
    """Integration tests for the main() entry point."""

    def test_dry_run_creates_profile(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        profile_base = tmp_path / "foxglove_profiles"
        monkeypatch.setattr(foxglove, "FOXGLOVE_DIR", profile_base)

        result = main(["-d", "testprofile"])

        assert result == 0
        profile_dir = profile_base / "testprofile"
        assert profile_dir.exists()
        assert profile_dir.is_dir()

    def test_rejects_profile_path_traversal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ):
        profile_base = tmp_path / "foxglove_profiles"
        monkeypatch.setattr(foxglove, "FOXGLOVE_DIR", profile_base)

        escaped_path = (profile_base / "foo/../../../escape").resolve()
        result = main(["-d", "foo/../../../escape"])

        assert result == 2
        assert not escaped_path.exists()
        assert not profile_base.exists()
        assert "outside foxglove profiles directory" in capsys.readouterr().err

    def test_dry_run_allows_nested_profile_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        profile_base = tmp_path / "foxglove_profiles"
        monkeypatch.setattr(foxglove, "FOXGLOVE_DIR", profile_base)

        result = main(["-d", "nested/ok"])

        assert result == 0
        profile_dir = profile_base / "nested" / "ok"
        assert profile_dir.exists()
        assert profile_dir.is_dir()

    def test_dry_run_writes_prefs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        profile_base = tmp_path / "foxglove_profiles"
        monkeypatch.setattr(foxglove, "FOXGLOVE_DIR", profile_base)

        main(["-d", "testprofile"])

        user_js = profile_base / "testprofile" / "user.js"
        assert user_js.exists()
        content = user_js.read_text()
        assert "browser.startup.homepage" in content
        assert "toolkit.telemetry.enabled" in content

    def test_ephemeral_profile_cleaned_up(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """With -e, the profile should be scheduled for removal via atexit."""
        profile_base = tmp_path / "foxglove_profiles"
        monkeypatch.setattr(foxglove, "FOXGLOVE_DIR", profile_base)

        registered_calls: list = []
        monkeypatch.setattr(
            "atexit.register",
            lambda func, *args, **kwargs: registered_calls.append((func, args, kwargs)),
        )

        main(["-d", "-e", "ephemeral"])

        profile_dir = profile_base / "ephemeral"
        assert profile_dir.exists()
        assert any(str(profile_dir) in str(args) for func, args, kwargs in registered_calls)

    def test_chrome_css_copied(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        profile_base = tmp_path / "foxglove_profiles"
        monkeypatch.setattr(foxglove, "FOXGLOVE_DIR", profile_base)

        chrome_file = tmp_path / "myChrome.css"
        chrome_file.write_text("/* custom chrome */\n")

        main(["-d", "--chrome", str(chrome_file), "testprofile"])

        installed = profile_base / "testprofile" / "chrome" / "userChrome.css"
        assert installed.exists()
        assert installed.read_text() == "/* custom chrome */\n"

    def test_content_css_copied(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        profile_base = tmp_path / "foxglove_profiles"
        monkeypatch.setattr(foxglove, "FOXGLOVE_DIR", profile_base)

        content_file = tmp_path / "myContent.css"
        content_file.write_text("/* custom content */\n")

        main(["-d", "--content", str(content_file), "testprofile"])

        installed = profile_base / "testprofile" / "chrome" / "userContent.css"
        assert installed.exists()
        assert installed.read_text() == "/* custom content */\n"

    def test_addon_download_integrated(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        profile_base = tmp_path / "foxglove_profiles"
        monkeypatch.setattr(foxglove, "FOXGLOVE_DIR", profile_base)

        fake_xpi = tmp_path / "fake.xpi"
        fake_xpi.write_bytes(b"PK\x03\x04fake-xpi")

        with mock.patch("foxglove._download_addon", return_value=fake_xpi) as mock_dl:
            result = main(["-d", "-a", "ublock-origin", "testprofile"])

        assert result == 0
        mock_dl.assert_called_once_with("ublock-origin")
        assert not fake_xpi.exists(), "temp XPI not cleaned up"

    def test_firefox_invoked_without_dry_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        profile_base = tmp_path / "foxglove_profiles"
        monkeypatch.setattr(foxglove, "FOXGLOVE_DIR", profile_base)

        with mock.patch("foxglove.subprocess.check_call") as mock_call:
            mock_call.return_value = 0
            result = main(["testprofile"])

        assert result == 0
        mock_call.assert_called_once()
        call_args = mock_call.call_args[0][0]
        assert call_args[0] == "firefox"
        assert "--new-instance" in call_args
        assert "--no-remote" in call_args
        assert "--profile" in call_args


class TestPrefsFile:
    """Tests for the bundled prefs.js file."""

    @pytest.fixture(autouse=True)
    def _load_prefs(self):
        from mozprofile.prefs import Preferences

        self.prefs = dict(Preferences.read_prefs(str(PREFS_PATH)))

    def test_prefs_file_exists(self):
        assert PREFS_PATH.exists()

    def test_prefs_file_readable(self):
        assert len(self.prefs) > 0

    def test_telemetry_disabled(self):
        assert self.prefs["toolkit.telemetry.enabled"] is False
        assert self.prefs["toolkit.telemetry.unified"] is False
        assert self.prefs["toolkit.telemetry.server"] == "data:,"
        assert self.prefs["datareporting.policy.dataSubmissionEnabled"] is False
        assert self.prefs["datareporting.healthreport.uploadEnabled"] is False

    def test_normandy_disabled(self):
        assert self.prefs["app.normandy.enabled"] is False
        assert self.prefs["app.normandy.api_url"] == ""
        assert self.prefs["app.shield.optoutstudies.enabled"] is False

    def test_startup_prefs(self):
        assert self.prefs["browser.startup.homepage"] == "about:blank"
        assert self.prefs["browser.aboutConfig.showWarning"] is False

    def test_referer_not_spoofed(self):
        """spoofSource=true breaks CSRF protections and must be false."""
        assert self.prefs["network.http.referer.spoofSource"] is False

    def test_referer_trimming(self):
        assert self.prefs["network.http.referer.XOriginTrimmingPolicy"] == 2

    def test_cookie_behavior_is_tcp(self):
        """cookieBehavior=5 is Total Cookie Protection, not value 1."""
        assert self.prefs["network.cookie.cookieBehavior"] == 5

    def test_https_only_mode(self):
        assert self.prefs["dom.security.https_only_mode"] is True

    def test_gpc_enabled(self):
        """Global Privacy Control replaces the removed Do Not Track header."""
        assert self.prefs["privacy.globalprivacycontrol.enabled"] is True

    def test_etp_strict(self):
        assert self.prefs["browser.contentblocking.category"] == "strict"

    def test_pdf_scripting_disabled(self):
        """Ensure the correctly-cased pref name is used (capital S)."""
        assert self.prefs["pdfjs.enableScripting"] is False

    def test_no_deprecated_prefs(self):
        """Prefs that are deprecated or should not be set must not appear."""
        deprecated = [
            "app.update.doorhanger",
            "browser.fixup.alternate.enabled",
            "browser.fixup.alternate.suffix",
            "browser.selfsupport.url",
            "browser.newtabpage.activity-stream.feeds.snippets",
            "browser.newtabpage.enhanced",
            "browser.newtabpage.introShown",
            "browser.library.activity-stream.enabled",
            "browser.customizemode.tip0.shown",
            "browser.toolbars.bookmarks.2h2020",
            "experiments.enabled",
            "experiments.supported",
            "general.warnOnAboutConfig",
            "network.allow-experiments",
            "privacy.donottrackheader.enabled",
            "privacy.donottrackheader.value",
            "privacy.trackingprotection.introCount",
            "startup.homepage_welcome_url",
            "toolkit.telemetry.hybridContent.enabled",
            "toolkit.telemetry.prompted",
            "toolkit.telemetry.rejected",
            "toolkit.telemetry.unifiedIsOptIn",
            "toolkit.telemetry.reportingpolicy.firstRun",
            "trailhead.firstrun.didSeeAboutWelcome",
        ]
        for key in deprecated:
            assert key not in self.prefs, f"deprecated pref still present: {key}"


class TestConstants:
    """Tests for module-level constants."""

    def test_version_defined(self):
        assert isinstance(foxglove.__version__, str)
        assert foxglove.__version__

    def test_foxglove_dir_in_home(self):
        assert str(FOXGLOVE_DIR).startswith(str(Path.home()))

    def test_prefs_path_points_to_package(self):
        assert "foxglove" in str(PREFS_PATH)
        assert PREFS_PATH.name == "prefs.js"
