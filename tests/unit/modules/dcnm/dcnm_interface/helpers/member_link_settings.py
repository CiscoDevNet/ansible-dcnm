"""Member duplex/speed inheritance captures and previews."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
from . import vpc_controller as V
from .ethernet_controller import SWITCH_IP, preview
from .port_channel_controller import created
from .port_channel_controller import PO_ITEM_NAME
from .fixture_cases import load_case


FX = load_case("pvlan_po_duplex_measured")
VFX = load_case("pvlan_vpc_duplex_measured")


ASSOC_2410 = [{"primary_vlan": 2410, "secondary_vlan": 2412}]


# ====================================================================================== Po through main() (retargeted names)
def _retarget_po(lines):
    return [
        x.replace("port-channel521", "port-channel10").replace("channel-group 521", "channel-group 10").replace("ethernet1/8", "ethernet1/7") for x in lines
    ]


def _po_preview(key):
    pv = FX[key]
    return preview(_retarget_po(pv["pendingConfig"]), running=_retarget_po(pv["runningConfig"]), expected=_retarget_po(pv["expectedConfig"]))


def _po_cfg(**profile):
    prof = {"mode": "pvlan", "pvlan_mode": "host"}
    prof.update(profile)
    return {"name": PO_ITEM_NAME, "type": "pc", "switch": [SWITCH_IP], "deploy": True, "profile": prof}


def _created_po(speed="1Gb", duplex="auto"):
    ctrl = created("host", ["switchport private-vlan host-association 2410 2412"], pvlan_association=ASSOC_2410)
    nv = ctrl.detail["Port-channel10"]["nvPairs"]
    nv["SPEED"], nv["PORT_DUPLEX_MODE"] = speed, duplex
    return ctrl


# ====================================================================================== vPC through main(), both peers (retargeted names)
PEER = {"SN-A": (V.SN1, V.M1), "SN-B": (V.SN2, V.M2)}


def _retarget_vpc(lines, port):
    return [
        x.replace("port-channel522", "port-channel10")
        .replace("channel-group 522", "channel-group 10")
        .replace("vpc 522", "vpc 10")
        .replace("ethernet1/9", port.lower())
        for x in lines
    ]


def _vpc_preview(alias, key, mutate=None, serial=None):
    sn, port = PEER[alias]
    pv = copy.deepcopy(VFX["peers"][alias][key])
    if mutate:
        mutate(pv)
    return V.preview(
        _retarget_vpc(pv["pendingConfig"], port),
        serial=serial or sn,
        running=_retarget_vpc(pv["runningConfig"], port),
        expected=_retarget_vpc(pv["expectedConfig"], port),
    )


def _vpc_ctrl(speed="1Gb", duplex="auto"):
    ctrl = V.created_ctrl(association=((2410, 2412),))
    parent = ctrl.parents[V.VPC]["nvPairs"]
    parent["SPEED"], parent["PORT_DUPLEX_MODE"] = speed, duplex
    ctrl._expand_children(parent)
    return ctrl


def _vpc_item(**profile):
    return V.vpc_item(pvlan_association=ASSOC_2410, **profile)


def _queue(ctrl, preflight_key, gate_key, mutate=None, serials=None):
    for alias in ("SN-A", "SN-B"):
        sn = PEER[alias][0]
        ctrl.vpc_previews[sn] = [_vpc_preview(alias, preflight_key), _vpc_preview(alias, gate_key, (mutate or {}).get(alias), (serials or {}).get(alias))]
