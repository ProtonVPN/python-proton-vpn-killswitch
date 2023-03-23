#!/usr/bin/env python

from setuptools import setup, find_namespace_packages

setup(
    name="proton-vpn-killswitch",
    version="0.1.0",
    description="Proton Technologies VPN Kill Switch for linux",
    author="Proton Technologies",
    author_email="contact@protonmail.com",
    url="https://github.com/ProtonMail/pyhon-protonvpn-connection",
    packages=find_namespace_packages(include=['proton.vpn.killswitch.interface']),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=["proton-core"],
    extras_require={
        "development": ["pytest", "pytest-cov", "flake8", "pylint", "mypy"]
    },
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
