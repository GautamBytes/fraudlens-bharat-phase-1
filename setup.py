import re
from pathlib import Path

from setuptools import find_packages, setup


version_match = re.search(
    r'^__version__ = "([^"]+)"$',
    (Path(__file__).parent / "src" / "fraudlens" / "__init__.py").read_text(encoding="utf-8"),
    re.MULTILINE,
)
if version_match is None:
    raise RuntimeError("Package version is unavailable")


setup(
    name="fraudlens-bharat",
    version=version_match.group(1),
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.10",
)
