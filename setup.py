import codecs
import os
import re

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), "r") as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name="dailyblink",
    version=find_version("dailyblink", "__init__.py"),
    url="https://github.com/ptrstn/dailyblink",
    packages=find_packages(),
    install_requires=["requests", "beautifulsoup4", "mutagen", "cloudscraper"],
    entry_points={"console_scripts": ["dailyblink=dailyblink.__main__:main"]},
)
