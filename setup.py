#!/usr/bin/env python3
import os
import re
import shutil
import sys
from io import open

from setuptools import find_packages, setup


def read(f):
    return open(f, "r", encoding="utf-8").read()


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, "__init__.py")).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


version = get_version("compose_tags")


if sys.argv[-1] == "publish":
    if os.system("pip freeze | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
    os.system("python setup.py sdist bdist_wheel")
    if os.system("twine check dist/*"):
        print("twine check failed. Packages might be outdated.")
        print("Try using `pip install -U twine wheel`.\nExiting.")
        sys.exit()
    os.system("twine upload dist/*")
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    shutil.rmtree("dist")
    shutil.rmtree("build")
    shutil.rmtree("django_compose_tags.egg-info")
    sys.exit()


setup(
    name="django-compose-tags",
    version=version,
    url="https://github.com/HelloWatt/django-compose-tags",
    license="BSD-3-Clause",
    description="Composition for django templates.",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Jérôme Bon",
    author_email="jerome@hellowatt.fr",
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    install_requires=["Django>=3.0"],
    python_requires=">=3.6",
    zip_safe=False,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    project_urls={
        "Source": "https://github.com/HelloWatt/django-compose-tags",
        "Changelog": "https://github.com/HelloWatt/django-compose-tags/blob/main/CHANGELOG.md",
    },
)
