#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="python-protonvpn-killswitch",
    version="0.0.0",
    description="Proton Technologies VPN Killswitch for linux",
    author="Proton Technologies",
    author_email="contact@protonmail.com",
    url="https://github.com/ProtonMail/pyhon-protonvpn-connection",
    packages=find_packages(),
    include_package_data=True,
    license="GPLv3",
    platforms="OS Independent",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python",
        "Topic :: Security",
    ]
)
