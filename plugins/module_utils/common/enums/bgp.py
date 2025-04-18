#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
bgp.py

Enumerations for BGP parameters.
"""
from enum import Enum


class BgpPasswordEncrypt(Enum):
    """
    Enumeration for BGP password encryption types.
    """
    MD5 = 3
    TYPE7 = 7
    NONE = -1

    @classmethod
    def choices(cls):
        """
        Returns a list of all the encryption types.
        """
        return [cls.NONE, cls.MD5, cls.TYPE7]
