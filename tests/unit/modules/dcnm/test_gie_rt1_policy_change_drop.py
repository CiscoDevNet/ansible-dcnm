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
def test_an_unmarked_source_only_field_still_refuses_and_names_only_itself(state):
    have = routed_have(eigrpIpv4Passive="true", **{k: v[1] for k, v in DROPPED.items()})
    result, calls = run(state, have, "leaf")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    msg = result["msg"]
    assert "eigrp_ipv4_passive (eigrpIpv4Passive) on %s [%s], int_routed_host -> int_trunk_host" % (h.IF_A, h.SERIAL) in msg
    assert NO_WITHDRAWAL in msg
    for nvpair, (field, value) in DROPPED.items():
        assert "%s (%s)" % (field, nvpair) not in msg
        assert value not in msg


@pytest.mark.parametrize("state", STATES)
def test_ospf_active_still_refuses_the_reset_with_its_gate_remedy(state):
    have = routed_have(ospf="true", ospfTag="SYNTHETIC-TAG", ipv4AclIn="SYNTHETIC-ACL")
    result, calls = run(state, have, "leaf")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "disable enable_ospf on the current policy first" in result["msg"]
    assert "ipv4_acl_in (ipv4AclIn)" not in result["msg"]


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
def test_border_policy_change_from_trunk_is_unchanged(state):
    """int_trunk_host is not a declared parent: its source-only aclFilter still refuses (F2 contract)."""
    have = copy.deepcopy(h.build_have(h.TRUNK, acl_filter="SYNTHETIC-ACL"))
    result, calls = run(state, have, "border")
    assert result.get("failed") and h.writes(calls) == [], result.get("msg")
    assert "acl_filter (aclFilter) on %s [%s], int_trunk_host -> int_routed_host" % (h.IF_A, h.SERIAL) in result["msg"]


# ------------------------------------------------------------------ registry: exactly these rows, and the generator gate
def test_only_the_five_int_routed_host_rows_carry_the_marker():
    marked = sorted((r["parent_template"], r["parent_nvpair"]) for r in table.BINDING_TABLE if r.get("dropped_on_policy_change"))
    assert marked == sorted(("int_routed_host", n) for n in DROPPED)
    assert all(table.BINDING_TABLE[i]["dropped_on_policy_change"] is True
               for i, r in enumerate(table.BINDING_TABLE) if r.get("dropped_on_policy_change"))


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


def test_generator_accepts_the_marker_on_a_declared_parent():
    _generator()._check_registry_schema(_row(dropped_on_policy_change=True), ("int_routed_host", "ipv4AclIn"))


@pytest.mark.parametrize("bad, text", [
    (dict(dropped_on_policy_change="true"), "the marker is the boolean True"),
    (dict(dropped_on_policy_change=False), "the marker is the boolean True"),
    (dict(dropped_on_policy_change=True, parent_template="int_trunk_host", parent_nvpair="aclFilter",
          profile_key="acl_filter", applicable_mode="trunk"), "not a parent whose delete() is shown"),
])
def test_generator_refuses_a_bad_marker(bad, text):
    with pytest.raises(ValueError) as err:
        _generator()._check_registry_schema(_row(**bad), (bad.get("parent_template", "int_routed_host"), "x"))
    assert text in str(err.value)
