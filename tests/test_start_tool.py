import os
import sys
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import start_tool


def test_check_and_install_packages_success(monkeypatch):
    """Function returns True when packages are present."""
    packages = []

    def fake_version(pkg):
        packages.append(pkg)
        return "1.0"

    monkeypatch.setattr(start_tool.importlib.metadata, "version", fake_version)
    result = start_tool.check_and_install_packages()
    assert result is True
    assert packages == start_tool.REQUIRED_PACKAGES


def test_check_and_install_packages_failure(monkeypatch):
    """Function returns False when installation fails."""
    call_args = []

    def fake_version(pkg):
        raise start_tool.importlib.metadata.PackageNotFoundError

    def fake_run(cmd, check):
        call_args.append(cmd)
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd)

    monkeypatch.setattr(start_tool.importlib.metadata, "version", fake_version)
    monkeypatch.setattr(subprocess, "run", fake_run)
    result = start_tool.check_and_install_packages()
    assert result is False
    assert call_args
