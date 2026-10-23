"""Disabling OSPF and withdrawing OSPF authentication on a loopback (int_loopback).

NaC renders `ospf_tag`, the area, the options and the authentication keys only while `enable_ospf` is true, and the
message-digest key ID and key only while `enable_ospf_auth` is true. A disable therefore omits the stored tag, and an
authentication withdrawal omits the stored key. Without dependent-field rules both were refused before any request.

What int_loopback does with those fields (installed body for SMU 4.3.1.0175006017):
  * configureOspf = ospf == "true" or (INTF_VRF is the default VRF and the fabric underlay is OSPF). Outside the default
    VRF, OSPF off renders no OSPF child, and the template refuses an OSPF option with OSPF off. In the default VRF the
    loopback stays in the underlay process under the stored tag (falling back to the fabric tag when it is empty), so
    the tag and the options stay live there. A disable cannot remove that underlay line and is not asked to.
  * The message-digest key ID and key are required and rendered only while ospfAuthentication is "true", and the
    simple-key encryption type is used only with a non-empty simple key, in every VRF.

So the tag and the options are inert with OSPF off except in the default VRF (`inert_when ... unless INTF_VRF`), and the
authentication rows follow the same single gates as int_routed_host. In the default VRF a disable that omits a stored
tag is still refused; stating the tag is the supported direct form.

The HAVE is a real NDFC 12.6.0.267 interface read (fixtures/dcnm_intf_loopback_ospf_have.json); the default-VRF HAVE
changes only INTF_VRF. Profiles are the shapes NaC renders. Real main() through gie_withdrawal_harness; assertions are
on the captured request. Synthetic secrets only.
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
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import test_gie_thin_engine as thin

FIXTURE = json.load(open(os.path.join(os.path.dirname(h.__file__), "fixtures", "dcnm_intf_loopback_ospf_have.json")))
VRF = FIXTURE["nvPairs"]["INTF_VRF"]
TAG = FIXTURE["nvPairs"]["ospfTag"]
SYN_MD5 = "SYNTH-MD5-KEY-NOT-REAL-0003"
SYN_SIMPLE = "SYNTH-SIMPLE-NOT-REAL-04"
WRITE_PATHS = ["POST interface/modify", "POST globalInterface/deploy"]
IFNAME = "Loopback" + h.IF_LO[len("loopback"):]     # the module sends the canonical name
OPTIONS_NEUTRAL = {
    "ospfAdvertiseSubnet": "false", "ospfAuthentication": "false", "ospfAuthenticationKey": "", "ospfBfdMode": "noChange",
    "ospfCost": "", "ospfDeadInterval": "", "ospfHelloInterval": "", "ospfMtuIgnore": "false",
    "ospfNetworkType": "noChange", "ospfPriority": "", "ospfRetransmitInterval": "", "ospfShutdown": "false",
    "ospfTransmitDelay": "",
}


def have(vrf=VRF, **nv):
    pairs = copy.deepcopy(FIXTURE["nvPairs"])
    pairs["INTF_VRF"] = vrf
    pairs.update(nv)
    return [{"policy": "int_loopback", "interfaces": [{"serialNumber": h.SERIAL, "ifName": h.IF_LO, "fabricName": h.FABRIC,
                                                       "interfaceType": "INTERFACE_LOOPBACK", "nvPairs": pairs}]}]


def base(vrf=VRF):
    return {"mode": "lo", "int_vrf": vrf, "description": FIXTURE["nvPairs"]["DESC"], "admin_state": True,
            "ipv4_addr": FIXTURE["nvPairs"]["IP"], "enable_pim_sparse": False, "cmds": ""}


def ospf_on(vrf=VRF, **extra):
    """The NaC profile of an OSPF-enabled loopback (authentication off, simple-key type at its default)."""
    p = base(vrf)
    p.update(enable_ospf=True, ospf_tag=TAG, ospf_area_id=FIXTURE["nvPairs"]["OSPF_AREA_ID"], enable_ospf_auth=False,
             ospf_authentication_key_type="3", ospf_advertise_subnet=False, ospf_bfd_mode="enable", ospf_mtu_ignore=False,
             ospf_network_type="no_change", ospf_shutdown=False)
    p.update(extra)
    return p


def ospf_off(vrf=VRF):
    """The NaC profile of a disable: enable_ospf false and no other OSPF key."""
    return dict(base(vrf), enable_ospf=False)


def md5_have(vrf=VRF):
    return have(vrf, ospfAuthentication="true", OSPF_AUTH_KEY_ID="5", OSPF_AUTH_KEY=SYN_MD5)


def run(profile, state="replaced", hv=None):
    return h.run(profile, state, have=hv, parent=h.LOOPBACK)


def sent(calls):
    """The single int_loopback interface entry of the request, with its policy."""
    pols = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], pols)
    assert len(pols) == 1 and pols[0]["policy"] == "int_loopback", pols
    assert len(pols[0]["interfaces"]) == 1
    intf = pols[0]["interfaces"][0]
    assert (intf["ifName"], intf["serialNumber"]) == (IFNAME, h.SERIAL)
    return intf["nvPairs"]


def paths(calls):
    return ["%s %s" % (c["method"], c["path"].split("/rest/")[-1].split("?")[0]) for c in h.writes(calls)]


def as_have(calls):
    nv = sent(calls)
    return [{"policy": "int_loopback", "interfaces": [{"serialNumber": h.SERIAL, "ifName": h.IF_LO, "fabricName": h.FABRIC,
                                                       "interfaceType": "INTERFACE_LOOPBACK", "nvPairs": copy.deepcopy(nv)}]}]


def accepted(result, calls):
    assert not result.get("failed"), result.get("msg")
    assert paths(calls) == WRITE_PATHS
    return sent(calls)


def refused(result, calls, *fields):
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    for f in fields:
        assert "%s on int_loopback" % f in result["msg"]
    for s in (SYN_MD5, SYN_SIMPLE):
        assert s not in result["msg"]
    return result["msg"]


# ------------------------------------------------------------------ non-default VRF: OSPF off makes the loopback leave OSPF
def test_nac_disable_is_accepted_and_keeps_the_inert_tag():
    nv = accepted(*run(ospf_off(), hv=have()))
    assert nv["ospf"] == "false" and nv["INTF_VRF"] == VRF
    assert nv["ospfTag"] == TAG, "the stored tag is kept, neither withdrawn nor replaced by an invented value"
    assert nv["OSPF_AREA_ID"] == "0.0.0.0" and nv["OSPF_AUTH_KEY_ID"] == "1" and nv["OSPF_AUTH_KEY"] == ""
    assert dict((k, nv[k]) for k in OPTIONS_NEUTRAL) == OPTIONS_NEUTRAL, "the template refuses options with OSPF off"


def test_the_same_disable_again_is_a_module_noop():
    _r, calls = run(ospf_off(), hv=have())
    result, calls = run(ospf_off(), hv=as_have(calls))
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


def test_unchanged_ospf_on_profile_is_a_noop():
    result, calls = run(ospf_on(), hv=have())
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


def test_merged_explicit_disable_neutralizes_the_options_and_keeps_the_tag():
    nv = accepted(*run(ospf_off(), "merged", hv=have()))
    assert nv["ospf"] == "false" and nv["ospfTag"] == TAG
    assert nv["ospfBfdMode"] == "noChange", "a stored option would make the template refuse OSPF off"
    assert nv["OSPF_AREA_ID"] == FIXTURE["nvPairs"]["OSPF_AREA_ID"], "merged keeps what it is not asked to change"


def test_merged_omission_preserves_ospf():
    nv = accepted(*run(dict(base(), description="changed"), "merged", hv=have()))
    assert (nv["ospf"], nv["ospfTag"], nv["ospfBfdMode"], nv["DESC"]) == ("true", TAG, "enable", "changed")


def test_enable_with_a_new_tag_after_a_disable():
    off = have(ospf="false", OSPF_AREA_ID="0.0.0.0", ospfBfdMode="noChange")
    nv = accepted(*run(ospf_on(ospf_tag="LAB-OSPF-2"), hv=off))
    assert (nv["ospf"], nv["ospfTag"], nv["ospfBfdMode"]) == ("true", "LAB-OSPF-2", "enable")


def test_enable_without_a_tag_over_a_stored_tag_is_refused():
    off = have(ospf="false", OSPF_AREA_ID="0.0.0.0", ospfBfdMode="noChange")
    refused(*run(dict((k, v) for k, v in ospf_on().items() if k != "ospf_tag"), hv=off), "ospf_tag")


def test_enable_with_an_empty_tag_is_refused():
    off = have(ospf="false", ospfTag="", OSPF_AREA_ID="0.0.0.0", ospfBfdMode="noChange")
    result, calls = run(ospf_on(ospf_tag=""), hv=off)
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("vrf", (VRF, "default"))
def test_md5_enable_and_key_id_change(vrf):
    nv = accepted(*run(ospf_on(vrf, enable_ospf_auth=True, ospf_auth_key_id=5, ospf_auth_key=SYN_MD5), hv=have(vrf)))
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY_ID"], nv["OSPF_AUTH_KEY"]) == ("true", "5", SYN_MD5)
    nv = accepted(*run(ospf_on(vrf, enable_ospf_auth=True, ospf_auth_key_id=6, ospf_auth_key=SYN_MD5), hv=md5_have(vrf)))
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY_ID"], nv["OSPF_AUTH_KEY"]) == ("true", "6", SYN_MD5)


@pytest.mark.parametrize("vrf", (VRF, "default"))
def test_md5_withdrawal_with_ospf_kept_clears_the_key(vrf):
    nv = accepted(*run(ospf_on(vrf), hv=md5_have(vrf)))
    assert (nv["ospf"], nv["ospfTag"]) == ("true", TAG)
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY_ID"], nv["OSPF_AUTH_KEY"]) == ("false", "1", "")


@pytest.mark.parametrize("vrf", (VRF, "default"))
def test_md5_withdrawal_again_is_a_module_noop(vrf):
    _r, calls = run(ospf_on(vrf), hv=md5_have(vrf))
    result, calls = run(ospf_on(vrf), hv=as_have(calls))
    assert not result.get("failed") and h.writes(calls) == [], result.get("msg")


@pytest.mark.parametrize("profile, hv", (
    (ospf_on(enable_ospf_auth=True, ospf_auth_key_id=5, ospf_auth_key=SYN_MD5), have()),
    (ospf_on(), md5_have()),
    (ospf_off(), md5_have()),
), ids=("enable", "withdraw", "disable"))
def test_printed_result_never_carries_the_key(profile, hv):
    """What Ansible prints (real result formatting, no_log applied): the key never appears."""
    out, calls = h.emit_real_result([h.cfg_for(h.LOOPBACK, profile)], "replaced", have=hv)
    assert out and SYN_MD5 not in out
    assert '"failed": true' not in out


def test_disable_with_md5_configured_clears_the_key():
    nv = accepted(*run(ospf_off(), hv=md5_have()))
    assert (nv["ospf"], nv["ospfTag"]) == ("false", TAG)
    assert (nv["ospfAuthentication"], nv["OSPF_AUTH_KEY_ID"], nv["OSPF_AUTH_KEY"]) == ("false", "1", "")


@pytest.mark.parametrize("vrf", (VRF, "default"))
def test_simple_key_withdrawal_with_ospf_kept(vrf):
    nv = accepted(*run(ospf_on(vrf), hv=have(vrf, ospfAuthenticationKey=SYN_SIMPLE, ospfAuthenticationKeyType="7")))
    assert (nv["ospf"], nv["ospfAuthenticationKey"], nv["ospfAuthenticationKeyType"]) == ("true", "", "3")


def test_disable_with_a_type_7_simple_key():
    nv = accepted(*run(ospf_off(), hv=have(ospfAuthenticationKey=SYN_SIMPLE, ospfAuthenticationKeyType="7")))
    assert (nv["ospf"], nv["ospfAuthenticationKey"]) == ("false", "")
    assert nv["ospfAuthenticationKeyType"] == "7", "inert once the key is empty: kept as stored, not invented"


def test_merged_disable_with_md5_clears_the_key_through_the_chained_gate():
    nv = accepted(*run(ospf_off(), "merged", hv=md5_have()))
    assert (nv["ospf"], nv["ospfAuthentication"], nv["OSPF_AUTH_KEY"]) == ("false", "false", "")


def test_deleting_the_loopback_with_ospf_and_md5_on():
    result, calls = run(base(), "deleted", hv=md5_have())
    assert not result.get("failed"), result.get("msg")
    assert paths(calls) == ["DELETE interface/markdelete", "POST globalInterface/deploy"]
    assert SYN_MD5 not in json.dumps(calls)


# ------------------------------------------------------------------ default VRF: the loopback stays in the underlay process
def test_default_vrf_nac_disable_omitting_the_tag_is_still_refused():
    msg = refused(*run(ospf_off("default"), hv=have("default")), "ospf_tag")
    assert "ospf_auth_key" not in msg


def test_default_vrf_disable_with_md5_is_refused_for_the_tag_only():
    msg = refused(*run(ospf_off("default"), hv=md5_have("default")), "ospf_tag")
    assert "ospf_auth_key" not in msg, "the key is classified (cleared with authentication off); only the live tag blocks"


def test_default_vrf_disable_stating_the_tag_keeps_the_tag():
    nv = accepted(*run(dict(ospf_off("default"), ospf_tag=TAG), hv=have("default")))
    assert (nv["ospf"], nv["ospfTag"], nv["INTF_VRF"]) == ("false", TAG, "default")


def test_default_vrf_merged_disable_keeps_the_live_options():
    nv = accepted(*run(ospf_off("default"), "merged", hv=have("default")))
    assert (nv["ospf"], nv["ospfTag"], nv["ospfBfdMode"]) == ("false", TAG, "enable"), \
        "in the default VRF the options still apply to the underlay process; they are not neutralized"


def test_empty_vrf_is_the_default_vrf():
    msg = refused(*run(ospf_off("default"), hv=have("")), "ospf_tag")
    assert "ospf_auth_key" not in msg


# ------------------------------------------------------------------ the registry and the engine
LOOPBACK_OSPF_OFF = ("ospfTag", "ospfAdvertiseSubnet", "ospfAuthentication", "ospfAuthenticationKey", "ospfBfdMode",
                     "ospfCost", "ospfDeadInterval", "ospfHelloInterval", "ospfMtuIgnore", "ospfNetworkType", "ospfPriority",
                     "ospfRetransmitInterval", "ospfShutdown", "ospfTransmitDelay")


def test_registry_rows():
    for nvpair in LOOPBACK_OSPF_OFF:
        gate = table.resolve_by_nvpair("int_loopback", nvpair)["inert_when"]
        assert (gate["nvpair"], gate["value"]) == ("ospf", "false")
        assert gate["unless"] == {"nvpair": "INTF_VRF", "values": ("", "default")}
        assert gate.get("strict", False) is (nvpair != "ospfTag") and gate.get("required", False) is (nvpair == "ospfTag")
    assert table.resolve_by_nvpair("int_loopback", "OSPF_AUTH_KEY")["inert_when"] == {
        "nvpair": "ospfAuthentication", "value": "false", "required": True, "clear": ""}
    assert table.resolve_by_nvpair("int_loopback", "OSPF_AUTH_KEY_ID")["inert_when"] == {
        "nvpair": "ospfAuthentication", "value": "false"}
    assert table.resolve_by_nvpair("int_loopback", "ospfAuthenticationKeyType")["inert_when"] == {
        "nvpair": "ospfAuthenticationKey", "value": ""}
    assert "inert_when" not in table.resolve_by_nvpair("int_loopback", "OSPF_AREA_ID")


@pytest.mark.parametrize("nvpairs, inert", (
    ({"ospf": "false", "INTF_VRF": "TENANT-A"}, True),
    ({"ospf": False, "INTF_VRF": "TENANT-A"}, True),
    ({"ospf": "false", "INTF_VRF": "default"}, False),
    ({"ospf": "false", "INTF_VRF": ""}, False),
    ({"ospf": "false"}, False),
    ({"ospf": "false", "INTF_VRF": None}, False),
    ({"ospf": "true", "INTF_VRF": "TENANT-A"}, False),
    ({"INTF_VRF": "TENANT-A"}, False),
))
def test_inert_with_an_exception(nvpairs, inert):
    assert engine.gie_binding_inert(table.resolve_by_nvpair("int_loopback", "ospfTag"), nvpairs) is inert


def test_routed_rows_have_no_exception():
    for parent in ("int_routed_host", "int_subif", "int_vlan"):
        for row in table.BINDING_TABLE:
            if row["parent_template"] == parent and row.get("inert_when"):
                assert "unless" not in row["inert_when"]


def test_dependency_plan_keeps_default_vrf_options_live():
    have_nv = dict(FIXTURE["nvPairs"], INTF_VRF="default")
    writes, conflicts = engine.gie_dependency_plan("int_loopback", {"ospf": "false", "INTF_VRF": "default"}, have_nv,
                                                   {"ospf"}, True, "12.6.0.267", h.SUPPORTED_PATCH)
    assert writes == {} and conflicts == []
    writes, conflicts = engine.gie_dependency_plan("int_loopback", {"ospf": "false", "INTF_VRF": VRF}, FIXTURE["nvPairs"],
                                                   {"ospf"}, True, "12.6.0.267", h.SUPPORTED_PATCH)
    assert writes == {"ospfBfdMode": "noChange"} and conflicts == []
    writes, conflicts = engine.gie_dependency_plan("int_loopback", {"ospf": "false"},
                                                   dict((k, v) for k, v in FIXTURE["nvPairs"].items() if k != "INTF_VRF"),
                                                   {"ospf"}, True, "12.6.0.267", h.SUPPORTED_PATCH)
    assert writes == {} and conflicts == [], "no VRF in WANT or HAVE: not judged"


def _rows_with(nvpair, **row_update):
    rows = thin._as_slice_rows(table.BINDING_TABLE)
    for r in rows:
        if r["parent_template"] == "int_loopback" and r["parent_nvpair"] == nvpair:
            r.update(row_update)
    return rows


GATE = {"nvpair": "ospf", "value": "false", "required": True}


@pytest.mark.parametrize("unless", [
    "INTF_VRF",
    {"nvpair": "INTF_VRF"},
    {"nvpair": "INTF_VRF", "values": []},
    {"nvpair": "INTF_VRF", "values": ["default", "default"]},
    {"nvpair": "INTF_VRF", "values": [False]},
    {"nvpair": "", "values": ["default"]},
    {"nvpair": "ospf", "values": ["default"]},
    {"nvpair": "ospfTag", "values": ["default"]},
    {"nvpair": "INTF_VRF", "values": ["default"], "other": 1},
])
def test_generator_rejects_a_malformed_exception(unless):
    with pytest.raises(ValueError, match="inert_when unless"):
        thin._load_generator().compile_rows(_rows_with("ospfTag", inert_when=dict(GATE, unless=unless)))


def test_generator_compiles_the_exception_in_a_fixed_form():
    rows = thin._load_generator().compile_rows(_rows_with(
        "ospfTag", inert_when={"unless": {"values": ["", "default"], "nvpair": "INTF_VRF"}, "required": True,
                               "value": "false", "nvpair": "ospf"}))
    row = [r for r in rows if r["parent_template"] == "int_loopback" and r["parent_nvpair"] == "ospfTag"][0]
    assert list(row["inert_when"]) == ["nvpair", "value", "required", "unless"]
    assert row["inert_when"]["unless"] == {"nvpair": "INTF_VRF", "values": ("", "default")}
