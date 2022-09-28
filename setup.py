#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-lessonly",
    version="0.1.0",
    description="Singer.io tap for extracting data",
    author="Stitch",
    url="http://singer.io",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_lessonly"],
    install_requires=[
        "singer-python>=5.0.12",
        "PyJWT==1.7.1",
        "requests",
    ],
    entry_points="""
    [console_scripts]
    tap-lessonly=tap_lessonly:main
    """,
    packages=["tap_lessonly"],
    package_data = {
        "schemas": ["tap_lessonly/schemas/*.json"]
    },
    include_package_data=True,
)
