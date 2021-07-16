# -*- coding: utf-8 -*-
#
# This file is part of the enjoy project
#
# Copyright (c) 2021 Tiago Coutinho
# Distributed under the GPLv3 license. See LICENSE for more info.

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = ['typer', 'beautifultable']

test_requirements = ["pytest", ]

setup(
    author="Jose Tiago Macara Coutinho",
    author_email="coutinhotiago@gmail.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    description="I/O agnostic approach to linux input system",
    install_requires=requirements,
    license="GPLv3",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="enjoy, input, joystick, gamepad, linux",
    name="enjoy",
    packages=find_packages(),
    test_suite="tests",
    tests_require=test_requirements,
    python_requires=">=3.5",
    url="https://github.com/tiagocoutinho/enjoy",
    project_urls={
        "Documentation": "https://github.com/tiagocoutinho/enjoy",
        "Source": "https://github.com/tiagocoutinho/enjoy",
    },
    version="0.1.2",
    zip_safe=True,
)
