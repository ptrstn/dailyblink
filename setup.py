from setuptools import setup, find_packages

setup(
    name="dailyblink",
    version="0.5.1",
    url="https://github.com/ptrstn/dailyblink",
    packages=find_packages(),
    install_requires=["requests", "beautifulsoup4", "mutagen", "cloudscraper"],
    entry_points={
        "console_scripts": [
            "dailyblink=dailyblink.blinks:main",
            "allblinks=dailyblink.blinkist:main",
        ]
    },
)
