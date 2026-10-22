"""R-F4: disabling OSPF and retiring a routed port after an OSPF tag was set.

NaC rule 323 refuses any OSPF sub-field without `enable_ospf: true`, so disabling OSPF sends
`enable_ospf: false` and no `ospf_tag`. The registry has no verified reset for `ospfTag`
(the template declares `minLength = 1` and no default), so the omitted tag was classified as
"cannot be classified as already withdrawn" and every later reset to the leaf default was
refused with "no verified withdrawal": once a tag was set, the port could not leave
int_routed_host through the module.

The int_routed_host, int_subif and int_vlan template bodies validate and render `ospfTag` only
under `ospf == true`, and with OSPF off they neither check it nor create the OSPF child. Those
rows declare `inert_when: {nvpair: ospf, value: 'false'}`: a stored tag under a disabled gate is
not a withdrawal target, is kept as stored, and transports nothing new. In the default VRF int_loopback
falls back to the fabric underlay when OSPF is off, so its tag stays live there (test_gie_loopback_ospf_withdrawal.py).

The routed HAVE is a real NDFC 12.6.0.267 interface read (fixtures/dcnm_intf_routed_ospf_have.json).
Real main() through gie_withdrawal_harness.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import json
import os

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import test_dcnm_intf_default_reset_registered_f2 as F2
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import test_gie_thin_engine as thin

FIXTURE = json.load(open(os.path.join(os.path.dirname(h.__file__), "fixtures", "dcnm_intf_routed_ospf_have.json")))
OSPF_OPTIONS_NEUTRAL = {
    "ospfAuthentication": "false", "ospfAuthenticationKey": "", "ospfBfdMode": "noChange", "ospfCost": "",
    "ospfDeadInterval": "", "ospfHelloInterval": "", "ospfMtuIgnore": "false", "ospfNetworkType": "noChange",
    "ospfPassiveMode": "noChange", "ospfPriority": "", "ospfShutdown": "false", "ospfTransmitDelay": "",
}
# The NaC P-OSPF-OFF item for this port: enable_ospf false and no ospf_* key (rule 323).
OSPF_OFF = {"mode": "routed", "enable_ospf": False, "ipv4_addr": "192.0.2.17", "ipv4_mask_len": 30}
STATES = ("deleted", "overridden")


def real_have(**nvpairs):
    nv = copy.deepcopy(FIXTURE["nvPairs"])
    nv.update(nvpairs)
    return [{"policy": FIXTURE["policy"], "interfaces": [{"serialNumber": h.SERIAL, "ifName": h.IF_A, "fabricName": h.FABRIC,
                                                          "interfaceType": "INTERFACE_ETHERNET", "nvPairs": nv}]}]


def ospf_off_have():
    """What the accepted OSPF-off replacement leaves: gate off, options neutral, the tag still stored."""
    return real_have(ospf="false", **OSPF_OPTIONS_NEUTRAL)


def sent_policies(calls):
    return F2.reset_policies(calls)


def replaced(profile, have):
    return F2.run("replaced", have, "border", configs=[h.cfg(h.IF_A, profile, deploy=False)])


def retire(state, have):
    return F2.run(state, have, "leaf", configs=None if state == "deleted" else [])


# ------------------------------------------------------------------ disabling OSPF through the caller's shape
def test_nac_ospf_off_is_accepted_and_keeps_the_inert_tag():
    result, calls = replaced(OSPF_OFF, real_have())
    assert not result.get("failed"), result.get("msg")
    pol = sent_policies(calls)
    assert len(pol) == 1 and pol[0]["policy"] == "int_routed_host"
    nv = pol[0]["interfaces"][0]["nvPairs"]
    assert nv["ospf"] == "false"
    assert nv["ospfTag"] == FIXTURE["nvPairs"]["ospfTag"], "the stored tag is kept, not withdrawn and not invented"
    # The template refuses OSPF options with OSPF off: every one of them is at its neutral value.
    assert dict((k, nv[k]) for k in OSPF_OPTIONS_NEUTRAL) == OSPF_OPTIONS_NEUTRAL


def test_the_same_request_again_is_a_noop():
    first, calls = replaced(OSPF_OFF, real_have())
    assert not first.get("failed"), first.get("msg")
    have = F2.as_have(calls)
    result, calls = replaced(OSPF_OFF, have)
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


def test_omitting_the_gate_resets_it_and_keeps_the_tag():
    profile = dict((k, v) for k, v in OSPF_OFF.items() if k != "enable_ospf")
    result, calls = replaced(profile, real_have())
    assert not result.get("failed"), result.get("msg")
    nv = sent_policies(calls)[0]["interfaces"][0]["nvPairs"]
    assert nv["ospf"] == table.resolve_by_nvpair("int_routed_host", "ospf")["reset_wire"]
    assert nv["ospfTag"] == FIXTURE["nvPairs"]["ospfTag"]


def test_keeping_ospf_on_still_refuses_an_omitted_tag():
    result, calls = replaced(dict(OSPF_OFF, enable_ospf=True), real_have())
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "cannot be classified as already withdrawn" in result["msg"] and "ospf_tag on int_routed_host" in result["msg"]


# ------------------------------------------------------------------ retiring the port to the leaf default
@pytest.mark.parametrize("state", STATES)
def test_retiring_after_disabling_resets_to_trunk(state):
    result, calls = retire(state, ospf_off_have())
    assert not result.get("failed"), result.get("msg")
    pol = sent_policies(calls)
    assert len(pol) == 1 and pol[0]["policy"] == "int_trunk_host"
    nv = pol[0]["interfaces"][0]["nvPairs"]
    assert "ospf" not in nv and "ospfTag" not in nv, "a source-only nvPair is never written into the destination"


@pytest.mark.parametrize("state", STATES)
def test_retiring_with_ospf_on_to_the_leaf_default_drops_ospf_with_the_policy(state):
    """int_routed_host drops every binding with a policy change (its delete() removes the OSPF child policies), so a
    leaf reset with OSPF still on proceeds with one write and sends neither ospf nor the tag."""
    result, calls = retire(state, real_have())
    assert not result.get("failed"), result.get("msg")
    pol = sent_policies(calls)
    assert len(pol) == 1 and pol[0]["policy"] == "int_trunk_host"
    nv = pol[0]["interfaces"][0]["nvPairs"]
    assert "ospf" not in nv and "ospfTag" not in nv
    assert FIXTURE["nvPairs"]["ospfTag"] not in str(calls)


@pytest.mark.parametrize("state", STATES)
def test_resetting_with_ospf_on_to_the_same_parent_turns_the_gate_off_and_keeps_the_tag_inert(state):
    """border: the default is int_routed_host itself; the reset sends ospf "false" and the stored tag, inert under that
    final gate, is neither sent nor refused (D-3)."""
    result, calls = F2.run(state, real_have(), "border", configs=None if state == "deleted" else [])
    assert not result.get("failed"), result.get("msg")
    pol = sent_policies(calls)
    assert len(pol) == 1 and pol[0]["policy"] == "int_routed_host"
    nv = pol[0]["interfaces"][0]["nvPairs"]
    assert nv["ospf"] == table.resolve_by_nvpair("int_routed_host", "ospf")["reset_wire"] and "ospfTag" not in nv


# ------------------------------------------------------------------ the other declared parents, and the excluded one
@pytest.mark.parametrize("parent", (h.SUBIF, h.SVI))
def test_ospf_off_keeps_the_inert_tag_on_subif_and_svi(parent):
    have = h.build_have(parent, **h.OSPF_CTX)
    assert have[0]["interfaces"][0]["nvPairs"]["ospfTag"] == h.OSPF_CTX["ospf_tag"]
    profile = h.base_for(parent, enable_ospf=False)
    result, calls = h.run(profile, "replaced", have=have, parent=parent)
    assert not result.get("failed"), result.get("msg")
    nv = sent_policies(calls)[0]["interfaces"][0]["nvPairs"]
    assert nv["ospf"] == "false" and nv["ospfTag"] == h.OSPF_CTX["ospf_tag"]


def test_default_vrf_loopback_tag_stays_live_and_is_still_refused():
    """int_loopback configures OSPF from the fabric underlay when ospf is false in the default VRF, with the stored tag
    first: there the tag is not inert (`unless` INTF_VRF), and a disable that omits it is still refused."""
    assert table.resolve_by_nvpair(h.LOOPBACK, "ospfTag")["inert_when"]["unless"] == {
        "nvpair": "INTF_VRF", "values": ("", "default")}
    assert h.base_for(h.LOOPBACK)["int_vrf"] == "default"
    have = h.build_have(h.LOOPBACK, **h.OSPF_CTX)
    result, calls = h.run(h.base_for(h.LOOPBACK, enable_ospf=False), "replaced", have=have, parent=h.LOOPBACK)
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "ospf_tag on int_loopback" in result["msg"]


# ------------------------------------------------------------------ engine and generator contract
def test_engine_inertness_compares_the_gate_in_wire_form():
    row = table.resolve_by_nvpair("int_routed_host", "ospfTag")
    assert row["inert_when"] == {"nvpair": "ospf", "value": "false", "required": True}
    assert engine.gie_binding_inert(row, {"ospf": "false"}) and engine.gie_binding_inert(row, {"ospf": False})
    assert not engine.gie_binding_inert(row, {"ospf": "true"}) and not engine.gie_binding_inert(row, {})
    assert not engine.gie_binding_inert(table.resolve_by_nvpair("int_routed_host", "aclFilter"), {"ospf": "false"})


def _rows_with(parent, nvpair, **row_update):
    rows = thin._as_slice_rows(table.BINDING_TABLE)
    for r in rows:
        if r["parent_template"] == parent and r["parent_nvpair"] == nvpair:
            r.update(row_update)
    return rows


@pytest.mark.parametrize("inert_when, match", [
    (("ospf", "false"), "must be a mapping"),
    ({"nvpair": "ospf"}, "must be a mapping"),
    ({"nvpair": "ospf", "value": False}, "must be a mapping"),
    ({"nvpair": "aclFilter", "value": "false"}, "not another committed binding of the same parent"),
    ({"nvpair": "ospfTag", "value": "false"}, "not another committed binding of the same parent"),
    ({"nvpair": "ospf", "value": "true"}, "verified reset or declared default"),
])
def test_generator_rejects_an_unsupported_inert_when(inert_when, match):
    generator = thin._load_generator()
    with pytest.raises(ValueError, match=match):
        generator.compile_rows(_rows_with("int_routed_host", "ospfTag", inert_when=inert_when))
