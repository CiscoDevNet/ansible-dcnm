"""S2 of the SMU adaptation: special renames, enum vocabularies, and the unsupported identity.

WHAT THE BODIES SAY, WHICH IS WHY NOTHING IS INVERTED

Every `DISABLE_*` name that lost its prefix kept its MEANING. Read from the freshly captured
bodies (capture-S2, byte-identical to capture-R2 at 12.6.0.267):

  boolean lldpReceive          DisplayName "Disable LLDP receive"      defaultValue=false
  boolean queuingStats         DisplayName "Disable queuing policy statistics"
                               content: noStats = " no-stats" if queuingStats == "true" else ""
  boolean qosStatsSuppressed   content: noStats = " no-stats" if qosStatsSuppressed == "true"
  boolean ipv4Redirects        content: disableIpv4Redirects = interfaceOptions["ipv4Redirects"]

So `true` still means "disable" on every one of them; the template even renames ipv4Redirects
back to a `disable`-prefixed local. All 21 unique pairs adjudicated RENAME_ONLY, none inverted,
and the public option names (`disable_lldp_receive`, …) keep their meaning unchanged.

THE THREE ENUM VOCABULARIES DID CHANGE

    ospfNetworkType   no_change,broadcast,point_to_point -> noChange,broadcast,pointToPoint
    ospfBfdMode       no_change,enable,disable           -> noChange,enable,disable
    ospfPassiveMode   no_change,passive,no_passive       -> noChange,passive,noPassive

and the installed body validates the SMU spelling directly:

    if ospfPassiveMode not in ["noChange", "passive", "noPassive"]:

`valid_values` stays the PUBLIC contract, so a playbook still writes `no_change` and an SMU
spelling is still refused as input. Translation happens only at the wire boundary.

Expected values below are hand-written from those declarations, never read back from the
registry or computed by a helper.

NOT LIVE TESTED ON SMU. Offline; nothing contacts a controller.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine as engine

from .gie_withdrawal_harness import (
    ACCESS,
    ROUTED,
    PC_TRUNK,
    base_for,
    build_have,
    cfg_for,
    run,
    run_configs,
    split_calls,
    request_nvpairs,
)

# Reviewed literals from the captured declarations.
SMU_LLDP_RECEIVE = "lldpReceive"
SMU_LLDP_TRANSMIT = "lldpTransmit"
SMU_QOS_STATS = "qosStatsSuppressed"
SMU_QUEUING_STATS = "queuingStats"
SMU_OSPF_GATE = "ospf"
SMU_PASSIVE_MODE = "ospfPassiveMode"

OLD_LLDP_RECEIVE = "DISABLE_LLDP_RECEIVE"
OLD_QOS_STATS = "DISABLE_QOS_STATS"
OLD_OSPF_GATE = "ENABLE_OSPF"

# The fabric-owned key that merely CONTAINS "ENABLE_OSPF" and must never be renamed with it.
FABRIC_OSPF_MD = "ENABLE_OSPF_AUTH_MESSAGE_DIGEST"


def rows():
    t = table.BINDING_TABLE
    return list(t.values()) if isinstance(t, dict) else list(t)


def row_of(parent, profile_key):
    for r in rows():
        if r["parent_template"] == parent and r["profile_key"] == profile_key:
            return r
    raise AssertionError("no registry row for %s::%s" % (parent, profile_key))


def emitted(calls):
    out = {}
    for nv in request_nvpairs(calls):
        out.update(nv)
    return out


# --------------------------------------------------------------- special renames, no inversion
def test_special_renames_landed_on_the_declared_names():
    assert row_of(ACCESS, "disable_lldp_receive")["parent_nvpair"] == SMU_LLDP_RECEIVE
    assert row_of(ACCESS, "disable_lldp_transmit")["parent_nvpair"] == SMU_LLDP_TRANSMIT
    assert row_of(ACCESS, "disable_qos_stats")["parent_nvpair"] == SMU_QOS_STATS
    assert row_of(ACCESS, "disable_queuing_stats")["parent_nvpair"] == SMU_QUEUING_STATS
    assert row_of(ROUTED, "enable_ospf")["parent_nvpair"] == SMU_OSPF_GATE


def test_the_fabric_ospf_md_key_was_not_dragged_along_by_its_prefix():
    """ENABLE_OSPF_AUTH_MESSAGE_DIGEST contains ENABLE_OSPF. It is fabric-owned and must keep
    its name; a substring rename would have silently taken it."""
    assert FABRIC_OSPF_MD in open(engine.__file__).read()
    assert not any(r["parent_nvpair"] == "ospfAuthMessageDigest" for r in rows())


@pytest.mark.parametrize("public_value,wire", [(True, "true"), (False, "false")])
def test_both_boolean_values_survive_the_special_rename(public_value, wire):
    """The rename did not invert anything: true still means "disable" on the wire."""
    profile = base_for(ACCESS, disable_lldp_receive=public_value)
    result, calls = run(profile, "merged")

    assert not result.get("failed"), result.get("msg")
    nv = emitted(calls)
    assert nv.get(SMU_LLDP_RECEIVE) == wire, nv
    assert OLD_LLDP_RECEIVE not in nv, "the pre-SMU key was emitted as well"


def test_the_public_option_names_and_meanings_are_unchanged():
    keys = {r["profile_key"] for r in rows()}
    for public in ("disable_lldp_receive", "disable_lldp_transmit", "disable_qos_stats",
                   "disable_queuing_stats", "enable_ospf"):
        assert public in keys, public


# ----------------------------------------------------------------------- enum vocabularies
def test_public_enum_contract_is_unchanged_and_refuses_the_smu_spelling():
    r = row_of(ROUTED, "ospf_passive_mode")
    assert r["valid_values"] == ("no_change", "passive", "no_passive"), r["valid_values"]
    with pytest.raises(engine.GieBindingError):
        engine.gie_validate_binding_value(ROUTED, "ospf_passive_mode", "noPassive")


def test_public_enum_value_is_translated_on_the_wire():
    profile = base_for(ROUTED, enable_ospf=True, ospf_passive_mode="no_passive")
    result, calls = run(profile, "merged", parent=ROUTED)

    assert not result.get("failed"), result.get("msg")
    nv = emitted(calls)
    assert nv.get(SMU_PASSIVE_MODE) == "noPassive", nv
    assert "no_passive" not in nv.values(), "a public spelling reached the wire"


def test_a_have_in_the_smu_vocabulary_is_accepted_not_rejected():
    """A controller answer of noChange must not be refused by the public validator."""
    engine.gie_validate_binding_value(
        ROUTED, "ospf_passive_mode", "noChange", value_source="have"
    )
    r = row_of(ROUTED, "ospf_passive_mode")
    assert engine.gie_public_value(r, "noPassive") == "no_passive"
    assert engine.gie_wire_value(r, "no_passive") == "noPassive"


def test_a_binding_without_wire_values_is_identity():
    r = row_of(ACCESS, "acl_filter")
    assert "wire_values" not in r
    assert engine.gie_wire_value(r, "ACL-PILOT") == "ACL-PILOT"
    assert engine.gie_public_value(r, "ACL-PILOT") == "ACL-PILOT"


def test_a_second_invocation_against_the_smu_have_sends_nothing():
    """The rerun that proves the wire spelling round-trips, at the stub boundary."""
    have = build_have(ROUTED, "ospf_passive_mode", "no_passive")
    nv = have[0]["interfaces"][0]["nvPairs"]
    assert nv.get(SMU_PASSIVE_MODE) == "noPassive", sorted(nv)

    profile = base_for(ROUTED, enable_ospf=True, ospf_passive_mode="no_passive")
    result, calls = run(profile, "replaced", have=copy.deepcopy(have), parent=ROUTED)

    assert not result.get("failed"), result.get("msg")
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "the second invocation configured again"
    assert buckets["deploys"] == []


def test_an_omitted_smu_field_survives_an_unrelated_change():
    """A no-op alone would not prove the omitted field survives a LATER write, so this
    changes a different field in the same payload and checks the omitted one is still there."""
    have = build_have(ACCESS, "disable_lldp_receive", True)
    want = base_for(ACCESS, description="changed-by-this-run")
    result, calls = run(want, "merged", have=copy.deepcopy(have))

    assert not result.get("failed"), result.get("msg")
    nv = emitted(calls)
    assert nv.get("DESC") == "changed-by-this-run", nv
    assert nv.get(SMU_LLDP_RECEIVE) == "true", "the omitted SMU field was dropped by the write"


# -------------------------------------------------------- the identity with no counterpart
def test_the_unsupported_identity_is_kept_in_the_registry():
    """Its history is preserved; it is marked, not deleted."""
    r = row_of(PC_TRUNK, "enable_vpc_peer_link")
    assert r["smu_unsupported"] is True
    assert r["parent_nvpair"] == "ENABLE_VPC_PEER_LINK", "do not rename what has no counterpart"


@pytest.mark.parametrize("value", [True, False])
def test_explicit_unsupported_input_refuses_before_any_write(value):
    """Both values, and the refusal happens with NO mutating call at the stub."""
    profile = base_for(PC_TRUNK, enable_vpc_peer_link=value)
    result, calls = run(profile, "merged", parent=PC_TRUNK)

    assert result.get("failed"), "an unsupported field was accepted"
    assert "not supported by the interface templates installed" in str(result.get("msg"))
    buckets = split_calls(calls)
    assert buckets["updates"] == [] and buckets["deploys"] == [], calls


@pytest.mark.parametrize("value", [True, False])
def test_the_refusal_also_holds_in_check_mode(value):
    profile = base_for(PC_TRUNK, enable_vpc_peer_link=value)
    result, calls = run(profile, "merged", parent=PC_TRUNK, check_mode=True)

    assert result.get("failed"), "check mode accepted an unsupported field"
    assert split_calls(calls)["updates"] == []


def test_a_valid_object_before_the_unsupported_one_is_still_not_written():
    """The refusal is invocation-wide: a supported interface listed FIRST must not be
    configured before the unsupported one is reached."""
    good = cfg_for(ACCESS, base_for(ACCESS, disable_lldp_receive=True))
    bad = cfg_for(PC_TRUNK, base_for(PC_TRUNK, enable_vpc_peer_link=True))
    result, calls = run_configs([good, bad], "merged")

    assert result.get("failed"), "the unsupported object did not fail the invocation"
    buckets = split_calls(calls)
    assert buckets["updates"] == [], "the preceding valid object was written anyway"
    assert buckets["deploys"] == []


def test_omitting_the_unsupported_field_does_not_block_a_supported_sibling():
    """Omission must never reach the refusal, and must not invent a withdrawal."""
    profile = base_for(PC_TRUNK, disable_lldp_receive=True)
    assert "enable_vpc_peer_link" not in profile
    result, calls = run(profile, "merged", parent=PC_TRUNK)

    assert not result.get("failed"), result.get("msg")
    nv = emitted(calls)
    assert nv.get(SMU_LLDP_RECEIVE) == "true", nv
    assert "ENABLE_VPC_PEER_LINK" not in nv, "the pre-SMU key leaked onto the wire"
