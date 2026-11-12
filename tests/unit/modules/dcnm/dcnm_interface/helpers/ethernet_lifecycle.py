"""Ethernet PVLAN lifecycle controller shared by the companion suite."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
from .ethernet_controller import IF7, PVLAN, TPROM_A11, FakeController


def ctrl(nv=TPROM_A11, policy=PVLAN, ifname=IF7):
    c = FakeController()
    c.detail[ifname] = {"policy": policy, "nvPairs": copy.deepcopy(nv)}
    return c
