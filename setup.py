from setuptools import setup, find_packages

setup(
    name="dailyblink",
    version="0.0.1",
    url="https://github.com/ptrstn/daily-blinkist",
    packages=find_packages(),
    install_requires=["requests", "beautifulsoup4"],
    entry_points={"console_scripts": ["dailyblink=blinks:main"]},
)