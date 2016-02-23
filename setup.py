#!/usr/bin/python

from os import path
from setuptools import setup

from ucp import __version__

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='ucp',
    version=__version__,
    description='Python EMI UCP protocol wrapper.',
    long_description=long_description,
    url='https://github.com/amateja/emi-ucp',
    author='Andrzej Mateja',
    author_email='mateja.and@gmail.com',
    license="GPL V2",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Communications :: Telephony'
    ],
    keywords='ucp sms smsc protocol',
    packages=['ucp'],
    platforms='Posix; MacOS X; Windows',
    install_requires=['six'],
)
