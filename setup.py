#!/usr/bin/python

import glob
import os

from distutils.core import setup

setup(name = "emi-ucp",
      version = "1.0",
      py_modules = ["ucp"],
      description = "This module is based on EMI - UCP INTERFACE Specification Version 3.5 of December 1999 (C) CMG telecommunication and Utilities BV Division Advanced Technology",
      url = "http://www.nemux.org/",
      author = "Marco Romano",
      author_email = "nemux@nemux.org",
      license = "GPL V2",
      )

