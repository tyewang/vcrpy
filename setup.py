#!/usr/bin/env python

import sys
from setuptools import setup, find_packages

setup(
    name='vcrpy',
    version='1.4.1',
    description=(
        "Automatically mock your HTTP interactions to simplify and "
        "speed up testing"
    ),
    author='Kevin McCarthy',
    author_email='me@kevinmccarthy.org',
    url='https://github.com/kevin1024/vcrpy',
    packages=find_packages(exclude=("tests*",)),
    install_requires=['PyYAML', 'mock', 'six', 'contextlib2',
                      'wrapt', 'backport_collections'],
    license='MIT',
    tests_require=['pytest', 'mock', 'pytest-localserver', 'pytest-httpbin'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Testing',
        'Topic :: Internet :: WWW/HTTP',
        'License :: OSI Approved :: MIT License',
    ]
)
