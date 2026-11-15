"""NetFlow on twelve parents and the sampler on the SVI parent (registry lot rp5).

The bodies of the supported patch release declare ENABLE_NETFLOW, NETFLOW_MONITOR (required while NetFlow is enabled)
and NETFLOW_SAMPLER (shown while NetFlow is enabled, described for N7K only) on the Ethernet trunk, access, routed and
dot1q-tunnel parents, the four port-channel parents, the three vPC host parents and the subinterface. The SVI parent
declares the sampler beside its native NetFlow fields. enable_netflow and netflow_monitor reuse the native SVI keys.
Replaced and overridden withdrawal of each row runs in test_binding_withdrawal.py through the shared fixture matrix.

Real main() through helpers/binding_harness: only inventory, transport and sleep are mocked, and every HAVE is the
payload the module itself emits for a public profile. Values are synthetic. Nothing here is live evidence.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils import gie_engine
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding

from .helpers import binding_harness as h

PARENTS = (h.TRUNK, h.ACCESS, h.ROUTED, h.ETH_DOT1Q, h.PC_TRUNK, h.PC_ACCESS, h.PC_L3, h.PC_DOT1Q, h.VPC_TRUNK,
           h.VPC_ACCESS, h.VPC_DOT1Q, h.SUBIF)
NV = ("ENABLE_NETFLOW", "NETFLOW_MONITOR", "NETFLOW_SAMPLER")
ON = {"enable_netflow": True, "netflow_monitor": "PILOT-FM"}
FULL = {**ON, "netflow_sampler": "PILOT-FS"}
ON_WIRE = {"ENABLE_NETFLOW": "true", "NETFLOW_MONITOR": "PILOT-FM"}
FULL_WIRE = {**ON_WIRE, "NETFLOW_SAMPLER": "PILOT-FS"}
OFF_WIRE = {"ENABLE_NETFLOW": "false", "NETFLOW_MONITOR": "", "NETFLOW_SAMPLER": ""}


def _base(parent, **extra):
    return h.base_for(parent, **extra)


def _plain(parent, **extra):
    """base_for without the registered OSPF keys of the routed base, so a refusal can only come from the keys here."""
    prof = h.base_for(parent, **extra)
    if parent == h.ROUTED:
        prof.pop("enable_ospf", None)
        prof.pop("ospf_area_id", None)
    return prof


def _nv(calls, parent):
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    found = [p for p in found if p["policy"] == parent]
    assert len(found) == 1 and len(found[0]["interfaces"]) == 1, found
    return found[0]["interfaces"][0]["nvPairs"]


def _sel(nv):
    return {k: nv.get(k) for k in NV if k in nv}


def _run(parent, profile, state="merged", have=None, **kw):
    return h.run_configs([h.cfg_for(parent, profile)], state, have or [], **kw)


def _have(parent, **extra):
    """The module's own replaced payload for `parent` with `extra`, as the controller would return it: the controller
    also returns every declared nvPair, so an unset NetFlow field comes back as its default."""
    have = h.build_have(parent, **extra)
    nv = have[0]["interfaces"][0]["nvPairs"]
    for nvpair, default in (("ENABLE_NETFLOW", "false"), ("NETFLOW_MONITOR", ""), ("NETFLOW_SAMPLER", "")):
        nv.setdefault(nvpair, default)
    return have


def _refused(result, calls, *needles):
    msg = str(result.get("msg", ""))
    assert result.get("failed"), "the request was accepted"
    for needle in needles:
        assert needle in msg, msg
    assert h.writes(calls) == []


# ------------------------------------------------------------------ the rows
@pytest.mark.parametrize("parent", PARENTS)
def test_the_three_rows_are_one_contract_on_every_parent(parent):
    en, mon, smp = (resolve_binding(parent, k) for k in ("enable_netflow", "netflow_monitor", "netflow_sampler"))
    assert (en["parent_nvpair"], en["type"], en["default_template"], en["reset_wire"]) == (
        "ENABLE_NETFLOW", "boolean", False, "false")
    assert (mon["parent_nvpair"], mon["type"], mon["reset_wire"], mon["string_compare"]) == (
        "NETFLOW_MONITOR", "string", "", "unverified")
    assert mon["inert_when"] == {"nvpair": "ENABLE_NETFLOW", "value": "false", "required": True}
    assert (smp["parent_nvpair"], smp["type"], smp["reset_wire"], smp["string_compare"]) == (
        "NETFLOW_SAMPLER", "string", "", "unverified")
    assert smp["inert_when"] == {"nvpair": "ENABLE_NETFLOW", "value": "false"}
    assert all(b["mechanism"] == "passthrough" and "max_length" not in b for b in (en, mon, smp))


def test_the_svi_carries_only_the_sampler_and_keeps_its_native_fields():
    assert resolve_binding(h.SVI, "enable_netflow") is None and resolve_binding(h.SVI, "netflow_monitor") is None
    smp = resolve_binding(h.SVI, "netflow_sampler")
    assert (smp["parent_nvpair"], smp["reset_wire"], smp["string_compare"]) == ("NETFLOW_SAMPLER", "", "unverified")
    assert "inert_when" not in smp, "its gate is a native field, not a registry row"
    assert {"enable_netflow", "netflow_monitor"} <= gie_engine.GIE_NATIVE_ELSEWHERE_KEYS


# ------------------------------------------------------------------ create, update, clear
@pytest.mark.parametrize("profile,wire", [(ON, ON_WIRE), (FULL, FULL_WIRE)], ids=["monitor", "monitor_and_sampler"])
@pytest.mark.parametrize("parent", PARENTS)
def test_merged_create_sends_the_netflow_values(parent, profile, wire):
    result, calls = _run(parent, _base(parent, **profile))
    assert not result.get("failed"), result.get("msg")
    assert _sel(_nv(calls, parent)) == wire


@pytest.mark.parametrize("parent", PARENTS)
def test_a_plain_profile_carries_no_netflow_nvpair(parent):
    result, calls = _run(parent, _base(parent))
    assert not result.get("failed"), result.get("msg")
    assert _sel(_nv(calls, parent)) == {}


@pytest.mark.parametrize("parent", PARENTS)
def test_merged_disable_also_clears_the_stored_monitor_and_sampler(parent):
    have = _have(parent, **FULL)
    result, calls = _run(parent, _base(parent, enable_netflow=False), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _sel(_nv(calls, parent)) == OFF_WIRE


@pytest.mark.parametrize("parent", PARENTS)
def test_merged_sampler_change_keeps_the_stored_monitor_and_a_repeat_writes_nothing(parent):
    have = _have(parent, **FULL)
    result, calls = _run(parent, _base(parent, netflow_sampler="PILOT-FS-B"), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _sel(_nv(calls, parent)) == {**FULL_WIRE, "NETFLOW_SAMPLER": "PILOT-FS-B"}
    for state in ("merged", "replaced"):
        result, calls = _run(parent, _base(parent, **FULL), state, have)
        assert not result.get("failed"), result.get("msg")
        assert h.writes(calls) == [], state


@pytest.mark.parametrize("parent", PARENTS)
def test_merged_sampler_clear_differs_from_omission(parent):
    have = _have(parent, **FULL)
    result, calls = _run(parent, _base(parent, netflow_sampler=""), "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert _sel(_nv(calls, parent)) == {**FULL_WIRE, "NETFLOW_SAMPLER": ""}


@pytest.mark.parametrize("parent", PARENTS)
def test_replaced_without_netflow_resets_the_three(parent):
    have = _have(parent, **FULL)
    result, calls = _run(parent, _base(parent), "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert _sel(_nv(calls, parent)) == OFF_WIRE


# ------------------------------------------------------------------ the monitor is required while NetFlow is on
@pytest.mark.parametrize("parent", PARENTS)
def test_an_explicit_empty_monitor_with_netflow_on_is_refused(parent):
    result, calls = _run(parent, _base(parent, enable_netflow=True, netflow_monitor=""))
    _refused(result, calls, "netflow_monitor (with enable_netflow enabled)")


@pytest.mark.parametrize("parent", PARENTS)
def test_enabling_netflow_over_a_stored_empty_monitor_is_refused(parent):
    result, calls = _run(parent, _base(parent, enable_netflow=True), "merged", _have(parent))
    _refused(result, calls, "netflow_monitor (with enable_netflow enabled)")


def test_a_new_interface_with_netflow_and_no_monitor_is_left_to_the_template():
    """Absent from both the request and HAVE, the monitor is not judged; the template requires it (IsMandatory)."""
    result, calls = _run(h.TRUNK, _base(h.TRUNK, enable_netflow=True))
    assert not result.get("failed"), result.get("msg")
    assert _sel(_nv(calls, h.TRUNK)) == {"ENABLE_NETFLOW": "true"}


@pytest.mark.parametrize("parent", PARENTS)
def test_a_monitor_with_netflow_off_is_transported(parent):
    """The template hides it (IsShow) and renders nothing; it does not refuse it."""
    result, calls = _run(parent, _base(parent, enable_netflow=False, netflow_monitor="PILOT-FM"))
    assert not result.get("failed"), result.get("msg")
    assert _sel(_nv(calls, parent)) == {"ENABLE_NETFLOW": "false", "NETFLOW_MONITOR": "PILOT-FM"}


# ------------------------------------------------------------------ the SVI sampler beside the native fields
def test_the_svi_sampler_rides_with_the_native_netflow_fields():
    result, calls = _run(h.SVI, h.base_for(h.SVI, **FULL))
    assert not result.get("failed"), result.get("msg")
    nv = _nv(calls, h.SVI)
    assert (str(nv["ENABLE_NETFLOW"]).lower(), nv["NETFLOW_MONITOR"], nv["NETFLOW_SAMPLER"]) == (
        "true", "PILOT-FM", "PILOT-FS")


def test_the_svi_native_netflow_fields_are_unchanged():
    result, calls = _run(h.SVI, h.base_for(h.SVI, **ON))
    assert not result.get("failed"), result.get("msg")
    nv = _nv(calls, h.SVI)
    assert (str(nv["ENABLE_NETFLOW"]).lower(), nv["NETFLOW_MONITOR"]) == ("true", "PILOT-FM")
    assert "NETFLOW_SAMPLER" not in nv
    result, calls = _run(h.SVI, h.base_for(h.SVI))
    assert not result.get("failed"), result.get("msg")
    assert str(_nv(calls, h.SVI)["ENABLE_NETFLOW"]).lower() == "false", "the native default is still sent"


def test_the_svi_sampler_replaced_omission_resets_it():
    have = h.build_have(h.SVI, **{k: v for k, v in h.base_for(h.SVI, **FULL).items() if k != "mode"})
    result, calls = _run(h.SVI, h.base_for(h.SVI, **ON), "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert _nv(calls, h.SVI)["NETFLOW_SAMPLER"] == ""


# ------------------------------------------------------------------ version gate, check mode and query
@pytest.mark.parametrize("patch_version", [None, h.UNSUPPORTED_PATCH], ids=["no_patch_version", "unsupported_patch"])
@pytest.mark.parametrize("parent", PARENTS + (h.SVI,))
def test_the_sampler_needs_an_approved_patch_version(parent, patch_version):
    profile = h.base_for(h.SVI, **FULL) if parent == h.SVI else _plain(parent, **FULL)
    result, calls = _run(parent, profile, patch_version=patch_version)
    msg = result.get("msg", "")
    assert result.get("failed") and ("netflow_sampler" in msg or "enable_netflow" in msg), msg
    assert h.writes(calls) == []


@pytest.mark.parametrize("patch_version", [None, h.UNSUPPORTED_PATCH], ids=["no_patch_version", "unsupported_patch"])
@pytest.mark.parametrize("parent", PARENTS)
def test_enable_netflow_needs_an_approved_patch_version(parent, patch_version):
    result, calls = _run(parent, _plain(parent, enable_netflow=False), patch_version=patch_version)
    _refused(result, calls, "enable_netflow")


@pytest.mark.parametrize("parent", [h.TRUNK, h.PC_L3, h.VPC_ACCESS, h.SUBIF])
def test_check_mode_reports_the_change_and_writes_nothing(parent):
    result, calls = _run(parent, _base(parent), "replaced", _have(parent, **FULL), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == [] and result.get("changed") is True


@pytest.mark.parametrize("parent", PARENTS)
def test_values_must_be_typed(parent):
    result, calls = _run(parent, _base(parent, enable_netflow="maybe", netflow_monitor="PILOT-FM"))
    _refused(result, calls, "enable_netflow")
