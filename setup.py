#!/usr/bin/env python

from setuptools import setup

setup(
    # GETTING-STARTED: set your app name:
    name='ShadowConWebsite',
    # GETTING-STARTED: set your app version:
    version='1.0',
    # GETTING-STARTED: set your app description:
    description='ShadowConWebsite',
    # GETTING-STARTED: set author name (your name):
    author='Adrian Barnes',
    # GETTING-STARTED: set author email (your email):
    author_email='a_lost_shadow@imap.cc',
    # GETTING-STARTED: set author url (your url):
    url='http://www.python.org/sigs/distutils-sig/',
    # GETTING-STARTED: define required django version:
    install_requires=[
        'Django==1.9.2'
    ],
    dependency_links=[
        'https://pypi.python.org/simple/django/'
    ],
)
