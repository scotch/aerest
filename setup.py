# -*- coding: utf-8 -*-
"""
aerest
======


Quick links
-----------

- `User Guide <http://code.scotchmedia.com/aerest>`_
- `Repository <http://github.com/scotch/aerest>`_
- `Issue Tracker <https://github.com/scotch/aerest/issues>`_

"""
from setuptools import setup

setup(
    name = 'aerest',
    version = '0.1.0',
    license = 'Apache Software License',
    url = 'http://code.scotchmedia.com/aerest',
    description = "Adds a RESTful api to Google App Engine Apps",
    long_description = __doc__,
    author = 'Kyle Finley',
    author_email = 'kyle.finley@gmail.com',
    zip_safe = True,
    platforms = 'any',
    packages = [
        'aerest',
        ],
    include_package_data=True,
    install_requires=[
        'aecore',
        ],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ]
)