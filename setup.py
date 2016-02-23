#!/usr/bin/env python

from setuptools import setup

setup(
    name='ShadowConWebsite',
    version='1.0',
    description='ShadowConWebsite',
    author='Adrian Barnes',
    author_email='a_lost_shadow@imap.cc',
    url='http://www.python.org/sigs/distutils-sig/',
    install_requires=[
        'Django==1.9.2'
    ],
    dependency_links=[
        'https://pypi.python.org/simple/django/'
    ],
)
