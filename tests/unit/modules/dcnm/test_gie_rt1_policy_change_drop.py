"""RT-1: a routed Ethernet whose redirects, inbound ACL, IPv6 link-local or ND suppress-ra is configured can be reset
to the leaf role default (int_routed_host -> int_trunk_host) in one step.

int_routed_host realizes these five fields only in child policies created with entity and source = the interface,
and its delete() removes every such child when the policy is replaced (installed template body 6d37ea6a). Their rows
declare dropped_on_policy_change, so the reset proceeds without writing them into int_trunk_host, which does not
declare them. Every other source-only field, the same-policy reset, the OSPF gate and the capability boundary are
unchanged. Real main() through gie_withdrawal_harness, with the helpers of the F2 tests. Values are synthetic.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import importlib.util
import os
from unittest.mock import patch

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_binding_table as table
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm import gie_withdrawal_harness as h
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.test_dcnm_intf_default_reset_registered_f2 import (
    NO_WITHDRAWAL,
    STATES,
    as_have,
    default_have,
    nvpairs_of_reset,
    reset_policies,
    reset_wire,
    run,
)

DROPPED = {
    "ipv4Redirects": ("disable_ipv4_redirects", "true"),
    "ipv6Redirects": ("disable_ipv6_redirects", "true"),
    "ipv4AclIn": ("ipv4_acl_in", "SYNTHETIC-ACL"),
    "ipv6LinkLocal": ("ipv6_link_local", "fe80::1"),
    "ipv6NdSuppressRa": ("ipv6_nd_suppress_ra", "true"),
}


def routed_have(**nv):
    have = default_have("border")              # int_routed_host as this module writes it
    have[0]["interfaces"][0]["nvPairs"].update(nv)
    return have


# ------------------------------------------------------------------ the five fields leave with the source parent
@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("nvpair", sorted(DROPPED))
def test_marked_field_does_not_block_the_reset_and_is_never_written(state, nvpair):
    result, calls = run(state, routed_have(**{nvpair: DROPPED[nvpair][1]}), "leaf")
    assert not result.get("failed"), result.get("msg")
    assert len(h.split_calls(calls)["updates"]) == 1
    assert reset_policies(calls)[0]["policy"] == h.TRUNK
    assert nvpair not in nvpairs_of_reset(calls)


@pytest.mark.parametrize("state", STATES)
def test_all_five_together_reset_in_one_write_identical_to_the_unconfigured_port(state):
    _r0, calls0 = run(state, routed_have(), "leaf")
    result, calls = run(state, routed_have(**{k: v[1] for k, v in DROPPED.items()}), "leaf")
    assert not result.get("failed"), result.get("msg")
    assert h.split_calls(calls)["updates"] and nvpairs_of_reset(calls) == nvpairs_of_reset(calls0)
    assert [(c["method"], c["path"]) for c in calls] == [(c["method"], c["path"]) for c in calls0]


@pytest.mark.parametrize("state", STATES)
def test_second_run_over_the_reset_it_wrote_is_a_noop(state):
    _r1, calls1 = run(state, routed_have(**{k: v[1] for k, v in DROPPED.items()}), "leaf")
    result, calls = run(state, as_have(calls1), "leaf")
    assert not result.get("failed") and result["changed"] is False and h.writes(calls) == [], result.get("msg")


# ------------------------------------------------------------------ boundaries kept
@pytest.mark.parametrize("state", STATES)
def test_a_row_without_the_marker_still_refuses_and_names_only_itself(state):
    """The refusal stays for a binding whose parent is not declared: simulated on one int_routed_host row by
    removing its marker for the duration of the test."""
    have = routed_have(eigrpIpv4Passive="true", **{k: v[1] for k, v in DROPPED.items()})
    with patch.dict(table.resolve_by_nvpair(h.ROUTED, "eigrpIpv4Passive"), {"dropped_on_policy_change": False}):
        result, calls = run(state, have, "leaf")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    msg = result["msg"]
    assert "eigrp_ipv4_passive (eigrpIpv4Passive) on %s [%s], int_routed_host -> int_trunk_host" % (h.IF_A, h.SERIAL) in msg
    assert NO_WITHDRAWAL in msg
    for nvpair, (field, value) in DROPPED.items():
        assert "%s (%s)" % (field, nvpair) not in msg
        assert value not in msg


@pytest.mark.parametrize("state", STATES)
def test_ospf_active_on_the_same_parent_is_reset_with_the_acl_in_one_write(state):
    """border: the parent stays int_routed_host; the reset sends ospf "false" (the tag is inert under that final gate,
    D-3) together with the ACL's verified reset."""
    have = routed_have(ospf="true", ospfTag="SYNTHETIC-TAG", ipv4AclIn="SYNTHETIC-ACL")
    result, calls = run(state, have, "border")
    assert not result.get("failed"), result.get("msg")
    sent = nvpairs_of_reset(calls)
    assert sent["ospf"] == "false" and "ospfTag" not in sent
    assert sent["ipv4AclIn"] == reset_wire(h.ROUTED, "ipv4AclIn")


@pytest.mark.parametrize("state", STATES)
@pytest.mark.parametrize("nvpair", ["ipv4AclIn", "ipv6LinkLocal", "ipv6NdSuppressRa"])
def test_same_policy_reset_still_sends_the_verified_reset(state, nvpair):
    """border: the role default IS int_routed_host. The marker is not a reset: the row's own reset_wire is sent."""
    result, calls = run(state, routed_have(**{nvpair: DROPPED[nvpair][1]}), "border")
    assert not result.get("failed"), result.get("msg")
    assert reset_policies(calls)[0]["policy"] == h.ROUTED
    assert nvpairs_of_reset(calls)[nvpair] == reset_wire(h.ROUTED, nvpair)


@pytest.mark.parametrize("state", STATES)
def test_capability_disabled_keeps_the_published_behaviour(state):
    result, calls = run(state, routed_have(**{k: v[1] for k, v in DROPPED.items()}), "leaf", patch_version=None)
    assert not result.get("failed"), result.get("msg")
    for nvpair in DROPPED:
        assert all(nvpair not in p["interfaces"][0]["nvPairs"] for p in reset_policies(calls))


@pytest.mark.parametrize("state", STATES)
def test_border_policy_change_from_trunk_uses_the_inline_declaration_not_the_child_marker(state):
    """int_trunk_host is not a child-policy parent (no dropped_on_policy_change); its aclFilter leaves through the
    destination's compliance (cleared_on_change_to, P2), so the reset is the ordinary routed default."""
    assert not table.resolve_by_nvpair(h.TRUNK, "aclFilter").get("dropped_on_policy_change")
    have = copy.deepcopy(h.build_have(h.TRUNK, acl_filter="SYNTHETIC-ACL"))
    result, calls = run(state, have, "border")
    assert not result.get("failed"), result.get("msg")
    assert reset_policies(calls)[0]["policy"] == h.ROUTED and "aclFilter" not in nvpairs_of_reset(calls)


# ------------------------------------------------------------------ registry: exactly these rows, and the generator gate
def test_every_int_routed_host_row_and_no_other_carries_the_marker():
    marked = sorted((r["parent_template"], r["parent_nvpair"]) for r in table.BINDING_TABLE if r.get("dropped_on_policy_change"))
    routed = sorted((r["parent_template"], r["parent_nvpair"]) for r in table.BINDING_TABLE if r["parent_template"] == h.ROUTED)
    assert marked == routed and len(routed) == 59   # + 3 SMU 017 routed rows (slice 0b_37)
    assert set(("int_routed_host", n) for n in DROPPED) <= set(marked)
    assert all(r["dropped_on_policy_change"] is True for r in table.BINDING_TABLE if r.get("dropped_on_policy_change"))


def _generator():
    # tests/unit/modules/dcnm -> collection root
    root = os.path.abspath(os.path.join(os.path.dirname(h.__file__), os.pardir, os.pardir, os.pardir, os.pardir))
    spec = importlib.util.spec_from_file_location("gie_gen", os.path.join(root, "tools", "gie_generate_binding_table.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _row(**over):
    row = {"parent_template": "int_routed_host", "parent_nvpair": "ipv4AclIn", "profile_key": "ipv4_acl_in",
           "applicable_interface_type": "eth", "applicable_mode": "routed", "type": "string", "string_compare": "exact",
           "presence_model": "two_axis", "emit_when": "explicit_only", "mechanism": "passthrough",
           "min_ndfc_version": "12.6.0.267", "parent_resolution": "desired_parent", "reset_wire": ""}
    row.update(over)
    return row


def test_generator_declares_only_the_child_policy_parent():
    assert _generator().POLICY_CHANGE_DROPS_CHILDREN == {"int_routed_host"}
    _generator()._check_registry_schema(_row(), ("int_routed_host", "ipv4AclIn"))


def test_generator_accepts_a_row_that_repeats_the_computed_marker():
    _generator()._check_registry_schema(_row(dropped_on_policy_change=True), ("int_routed_host", "ipv4AclIn"))


@pytest.mark.parametrize("bad", [
    dict(dropped_on_policy_change="true"),
    dict(dropped_on_policy_change=False),
    dict(dropped_on_policy_change=True, parent_template="int_trunk_host", parent_nvpair="aclFilter",
         profile_key="acl_filter", applicable_mode="trunk"),
])
def test_generator_refuses_a_marker_that_differs_from_the_parent(bad):
    with pytest.raises(ValueError) as err:
        _generator()._check_registry_schema(_row(**bad), (bad.get("parent_template", "int_routed_host"), "x"))
    assert "a row may only repeat the computed value" in str(err.value)
