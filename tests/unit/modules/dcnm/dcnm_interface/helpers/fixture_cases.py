"""Location of the dcnm unit-test fixtures shared by the interface helpers."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "fixtures")
