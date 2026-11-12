"""Physical-port role-default reset helpers shared by the binding withdrawal suites."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
from unittest.mock import patch
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_interface.helpers import binding_harness as h
from .fixture_cases import load_case


STATES = ("deleted", "overridden")


_ORIG_TRANSPORT = h._transport


def _physical_transport(flags):
    def factory(calls, have):
        inner = _ORIG_TRANSPORT(calls, have)

        def send(mod, method, path, payload=None):
            resp = inner(mod, method, path, payload)
            if method == "GET" and "/interface/detail" in path and isinstance(resp.get("DATA"), list):
                for e in resp["DATA"]:
                    if str(e.get("isPhysical")).lower() == "true":
                        e.update(flags)
            return resp
        return send
    return factory


PHYSICAL = {"deletable": "false", "editAllowed": "true", "mgmtIpAddress": h.SWITCH_IP}


def _inventory(role):
    inv = load_case("dcnm_intf_binding_configs")["mock_fab_inv_data"]
    for v in inv.values():
        v["switchRole"] = role
    return inv


def run(state, have, role, configs=None, flags=None, patch_version=h._UNSET):
    if configs is None:
        configs = [{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}] if state == "deleted" else []
    with patch.object(h, "_transport", _physical_transport(flags or PHYSICAL)):
        return h.run_configs(configs, state, have=have, patch_version=patch_version,
                             extra_patch=patch.object(module, "get_fabric_inventory_details", return_value=_inventory(role)))


def reset_policies(calls):
    found = []
    h._collect_policies([c["payload"] for c in h.split_calls(calls)["updates"]], found)
    return found


def as_have(calls):
    found = reset_policies(calls)
    assert len(found) == 1, found
    have = copy.deepcopy(found)
    have[0]["interfaces"][0]["interfaceType"] = "INTERFACE_ETHERNET"
    have[0]["interfaces"][0]["fabricName"] = h.FABRIC
    return have


def nvpairs_of_reset(calls):
    return reset_policies(calls)[0]["interfaces"][0]["nvPairs"]


def reset_wire(parent, nvpair):
    return table.resolve_by_nvpair(parent, nvpair)["reset_wire"]


def _emitted(calls):
    """Every interface of every write, as {(serial, ifName): (policy, nvPairs)}."""
    out = {}
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    for pol in found:
        for intf in pol["interfaces"]:
            key = (intf["serialNumber"], intf["ifName"])
            assert key not in out, ("identity written twice", key)
            out[key] = (pol["policy"], intf.get("nvPairs") or {})
    return out


def _deploys(calls):
    return sorted((e.get("serialNumber"), e.get("ifName")) for c in h.writes(calls) if "deploy" in c["path"]
                  for e in (c["payload"] or []))


def _have_for(ifname, profile, iftype="eth"):
    """The payload the module emits for `profile` on `ifname`, as the controller would return it."""
    result, calls = h.run_configs([h.cfg(ifname, profile, iftype=iftype)], "replaced", [])
    assert not result.get("failed"), result.get("msg")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    assert len(found) == 1 and found[0]["interfaces"][0]["ifName"] == ifname, found
    have = copy.deepcopy(found)
    have[0]["interfaces"][0]["interfaceType"] = "INTERFACE_ETHERNET"
    have[0]["interfaces"][0]["fabricName"] = h.FABRIC
    return have


def _as_have(policy, ifname, nv):
    return [{"policy": policy, "interfaces": [{"interfaceType": "INTERFACE_ETHERNET", "serialNumber": h.SERIAL,
                                               "ifName": ifname, "fabricName": h.FABRIC, "nvPairs": copy.deepcopy(nv)}]}]


_ORIG_PHYSICAL = _physical_transport(PHYSICAL)


def _detail_transport(calls, have):
    """The F2 physical-port flags plus the subinterface flag the harness does not model: a live 12.6.0.267
    interface/detail read returned a user subinterface with `isPhysical: "false"` and `deletable: true`.
    `overridden` deletes a non-physical interface only when `deletable` is true."""
    inner = _ORIG_PHYSICAL(calls, have)

    def send(mod, method, path, payload=None):
        resp = inner(mod, method, path, payload)
        if method == "GET" and "/interface/detail" in path and isinstance(resp.get("DATA"), list):
            for e in resp["DATA"]:
                if str(e.get("isPhysical")).lower() == "false" and "." in str(e.get("ifName")):
                    e["deletable"] = True
        return resp
    return send


def _run(configs, state, have, role="leaf"):
    with patch.object(h, "_transport", _detail_transport):
        return h.run_configs(configs, state, have=have,
                             extra_patch=patch.object(module, "get_fabric_inventory_details",
                                                      return_value=_inventory(role)))
