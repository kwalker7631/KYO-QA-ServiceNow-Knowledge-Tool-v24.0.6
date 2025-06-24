import re
from pathlib import Path
import version


def test_readme_version_matches():
    readme = Path(__file__).resolve().parents[1] / "README.md"
    first_line = readme.read_text().splitlines()[0]
    match = re.search(r"v(\d+\.\d+\.\d+)", first_line)
    assert match, "Version string not found in README header"
    assert match.group(1) == version.VERSION
