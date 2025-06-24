import subprocess


def test_no_f401_warnings():
    """Ensure flake8 does not report unused-import warnings."""
    result = subprocess.run([
        "flake8",
        "--select=F401",
    ], capture_output=True, text=True)
    assert result.stdout.strip() == ""
