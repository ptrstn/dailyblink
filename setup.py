from setuptools import setup, find_packages

setup(
    name="dailyblink",
    version="0.2.0",
    url="https://github.com/ptrstn/daily-blinkist",
    packages=find_packages(),
    install_requires=["requests", "beautifulsoup4", "mutagen"],
    entry_points={"console_scripts": ["dailyblink=dailyblink.blinks:main"]},
)
