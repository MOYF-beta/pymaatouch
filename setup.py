from setuptools import setup, find_packages


setup(
    name="pymaatouch",
    version="0.1.0",
    description="python wrapper of maatouch, API-compatible with pyminitouch",
    author="pymaatouch",
    packages=find_packages(),
    install_requires=["loguru", "requests"],
)
