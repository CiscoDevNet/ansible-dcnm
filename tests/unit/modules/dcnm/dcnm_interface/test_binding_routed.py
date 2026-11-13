"""Routed parents: the first int_routed_host bindings, IPv6 addressing and the paired vPC module path."""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy
import inspect
import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import BINDING_TABLE
from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import resolve_binding
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface
from unittest.mock import patch
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface as module

from .helpers import binding_harness as h
from .helpers.fixture_cases import load_case
from .helpers.binding_harness import PEER_SERIAL
from .helpers.binding_harness import SERIAL
from .helpers.binding_harness import VPC_PAIR_SERIAL
from .helpers.binding_harness import VPC_ACCESS
from .helpers.binding_harness import VPC_TRUNK
from .helpers.binding_harness import ROUTED
from .helpers.binding_harness import base_for
from .helpers.binding_harness import cfg_for
from .helpers.binding_harness import diff_nvpairs
from .helpers.binding_harness import request_nvpairs
from .helpers.binding_harness import run_configs
from .helpers.binding_harness import split_calls
from .helpers.binding_harness import writes
from .helpers.binding_harness import _collect_policies


# ====================================================================================================
# Formerly test_gie_routed_bindings.py
# The first bindings registered for ``int_routed_host``.
#
# This parent is unlike the switchport parents already covered. It emits almost nothing itself:
# every one of the six nvPairs registered here ends in a child template --
#
#     DISABLE_LLDP_TRANSMIT  -> interface_lldp_disable              (creation gate)
#     DISABLE_LLDP_RECEIVE   -> interface_lldp_disable              (creation gate)
#     DISABLE_BFD_ECHO       -> bfd_no_echo_interface               (creation gate)
#     IPV4_ACL_IN            -> interface_ip_access_group_in_11_1   (gate + value)
#     DISABLE_QOS_STATS      -> interface_qos_service_policy        (DISABLE_STATS parameter)
#     DISABLE_QUEUING_STATS  -> interface_queuing_service_policy    (DISABLE_STATS parameter)
#
# -- read from the template body on the controller, not assumed. That delegation is NDFC's
# internal business: the module still writes one parent nvPair and nothing else, so the mechanism
# is ``passthrough``. The ``child_pti`` mechanism in this table means something different (a
# binding owning a dedicated compat/validation path -- the OSPF-MD case) and these cases assert
# the two are not confused, because reading "the template delegates to a child" as "therefore
# child_pti" is the obvious wrong turn here.
#
# ARP_TIMEOUT used to be excluded here on purpose, because int_subif and int_vlan declare it as
# well and all three are reachable (pol_types "sub_int_subint", "svi_vlan", "eth_routed"), so
# committing it on the routed parent alone would have made the module answer "not supported" for
# the other two. It went in as one lot across the three, which is the condition the
# exclusion was protecting. The generator is what enforced it, not a review -- it rejects a row
# claiming a committed public profile_key from an uncommitted parent, and it is also what caught
# that slice 0b_3 already held these three rows unregistered.
#
# What these cases cannot prove: that the child templates exist on the controller. They were
# verified present on 12.6.0.267 out of band. A missing child would transport the nvPair, return
# success, and produce no CLI -- exercised, never validated. Only the live run closes that.
#
# Offline: no controller and no device.
# ====================================================================================================
PARENT = "int_routed_host"

# profile_key -> (nvPair, registry type)
#
# The first six are passthrough, measured live.
#
# The four OSPF entries are the vertical slice: the first time child_pti is registered on a
# ROUTED parent rather than on the fabric loopback. Every OSPF field here is gated
# IsShow="ENABLE_OSPF==true", so none can be exercised alone -- the gate, the two the
# template marks IsMandatory, and one value field are the smallest set that produces
# observable CLI. Their removal_semantics is deliberately unresolved: the template creates a
# child per field and never deletes one, and reading that is not the same as measuring it.
EXPECTED = {
    # The authentication lot. Registered on this parent and on int_subif / int_vlan with
    # identical shape -- the only OSPF family where the three templates agree.
    "enable_ospf_auth": ("ospfAuthentication", "boolean"),
    "ospf_auth_key_id": ("OSPF_AUTH_KEY_ID", "integer"),
    "ospf_auth_key": ("OSPF_AUTH_KEY", "string"),
    "ospf_authentication_key_type": ("ospfAuthenticationKeyType", "enum"),
    "ospf_authentication_key": ("ospfAuthenticationKey", "string"),
    "disable_lldp_transmit": ("lldpTransmit", "boolean"),
    "disable_lldp_receive": ("lldpReceive", "boolean"),
    "disable_bfd_echo": ("bfdEcho", "boolean"),
    "disable_qos_stats": ("qosStatsSuppressed", "boolean"),
    "disable_queuing_stats": ("queuingStats", "boolean"),
    "ipv4_acl_in": ("ipv4AclIn", "string"),
    # Slice 0b_28. The fourth field, DISABLE_IP_REDIRECTS, is native and is not registered.
    "disable_ipv4_redirects": ("ipv4Redirects", "boolean"),
    "disable_ipv6_redirects": ("ipv6Redirects", "boolean"),
    "ipv6_nd_suppress_ra": ("ipv6NdSuppressRa", "boolean"),
    # ARP_TIMEOUT, slice 0b_3. Its declared range changed after the row was written:
    # the September 14 template batch added min=60/max=28800 to
    # `integer ARP_TIMEOUT;`, which previously had no bounds.
    "arp_timeout": ("arpTimeout", "integer"),
    # PIM, slice 0b_31. Only this parent declares all three fields. The template's `long`
    # pim_dr_priority is registered as `integer`: _TYPE_TO_VALIDATOR has no `long` type,
    # and integer validation is equivalent. A value of 1 emits no CLI line; see the slice.
    # IPv6 link-local, slice 0b_32. The template's `ipV6Address` is registered as `string`
    # with max_length 45, matching HSRP_VIPv6, which also uses ipV6Address.
    "ipv6_link_local": ("ipv6LinkLocal", "string"),
    # MACSEC, slice 0b_33. IsShow gates the three strings on the boolean. They are names,
    # not secrets: references to keychains and a policy on the switch.
    "enable_macsec_interface_policy": ("macsecInterfacePolicy", "boolean"),
    "macsec_key_chain_name": ("macsecKeyChainName", "string"),
    "macsec_policy_name": ("macsecPolicyName", "string"),
    "macsec_fallback_key_chain_name": ("macsecFallbackKeyChainName", "string"),
    "enable_pim_sparse": ("ENABLE_PIM_SPARSE", "boolean"),
    "pim_dr_priority": ("PIM_DR_PRIORITY", "integer"),
    "enable_pim_bfd_instance": ("pimBfdInstance", "boolean"),
    # SMU 017 first increment, slice 0b_37. Read from the 017 body; not measured live.
    "enable_cdp": ("CDP_ENABLE", "boolean"),
    "enable_evpn_multisite_dci_tracking": ("evpnMultisiteDciTracking", "boolean"),
    "ospf_retransmit_interval": ("ospfRetransmitInterval", "integer"),
    # Dampening, slice 0b_6. Only this parent declares it; C9300v does not support its CLI.
    "enable_dampening": ("dampening", "boolean"),
    "dampening_half_life": ("dampeningHalfLife", "integer"),
    "dampening_reuse": ("dampeningReuse", "integer"),
    "dampening_suppress": ("dampeningSuppress", "integer"),
    "dampening_max_suppress": ("dampeningMaxSuppress", "integer"),
    "dampening_restart": ("dampeningRestart", "boolean"),
    "dampening_restart_penalty": ("dampeningRestartPenalty", "integer"),
    "enable_ospf": ("ospf", "boolean"),
    "ospf_tag": ("ospfTag", "string"),
    "ospf_area_id": ("OSPF_AREA_ID", "string"),
    "ospf_cost": ("ospfCost", "integer"),
    "ospf_mtu_ignore": ("ospfMtuIgnore", "boolean"),
    "ospf_shutdown": ("ospfShutdown", "boolean"),
    "ospf_hello_interval": ("ospfHelloInterval", "integer"),
    "ospf_dead_interval": ("ospfDeadInterval", "integer"),
    "ospf_transmit_delay": ("ospfTransmitDelay", "integer"),
    "ospf_priority": ("ospfPriority", "integer"),
    "ospf_passive_mode": ("ospfPassiveMode", "enum"),
    "ospf_network_type": ("ospfNetworkType", "enum"),
    "ospf_bfd_mode": ("ospfBfdMode", "enum"),
}


@pytest.mark.parametrize("key,expected", sorted(EXPECTED.items()))
def test_the_binding_is_registered_with_the_declared_type(key, expected):
    nvpair, native = expected
    b = resolve_binding(PARENT, key)
    assert b is not None, "{0} is not registered for {1}".format(key, PARENT)
    assert b["parent_nvpair"] == nvpair
    assert b["type"] == native


@pytest.mark.parametrize("key", sorted(EXPECTED))
def test_the_binding_applies_to_a_routed_ethernet_parent(key):
    """A wrong interface_type/mode silently excludes the binding from the eth routed path."""
    b = resolve_binding(PARENT, key)
    assert b["applicable_interface_type"] == "eth"
    assert b["applicable_mode"] == "routed"


@pytest.mark.parametrize("key", sorted(EXPECTED))
def test_delegation_to_a_child_template_does_not_make_it_child_pti(key):
    """The wrong turn this file exists to prevent.

    Four of these six delegate to a child template inside NDFC. That is not what ``child_pti``
    means in this table -- it marks a binding that owns a dedicated compat path. Marking these
    ``child_pti`` would route them around the generic invalid-parent guard in
    ``gie_guarded_keys``, which only collects ``passthrough`` keys.
    """
    assert resolve_binding(PARENT, key)["mechanism"] == "passthrough"


def test_every_routed_key_is_covered_by_the_generic_parent_guard():
    """The consequence of the mechanism above, asserted at the engine rather than the table."""
    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import (
        gie_guarded_keys,
    )

    from ansible_collections.cisco.dcnm.plugins.module_utils.gie_engine import GIE_NATIVE_ELSEWHERE_KEYS

    # enable_cdp is registered here and native on other parents; the generic guard leaves it to the native spec.
    assert set(EXPECTED) - GIE_NATIVE_ELSEWHERE_KEYS <= gie_guarded_keys()
    assert not (GIE_NATIVE_ELSEWHERE_KEYS & gie_guarded_keys())


def test_arp_timeout_landed_on_all_three_parents_as_one_lot():
    """INVERTED. This used to pin the EXCLUSION; the lot landed, so now it pins the condition.

    The condition it guarded was "all three parents or none": int_subif and int_vlan declare
    ARP_TIMEOUT too and all three are reachable from a playbook, so committing one alone would
    make the module answer "not supported on this interface" for the other two -- a false
    answer, which is the defect this table exists to prevent. Still asserted, from the other
    side: all three must resolve.

    Its second claim is now WRONG, and the reason is worth keeping. It said the bound lives in
    the template BODY and not in the declaration, "so the engine will not catch a 0, the
    controller will". That was true of the body it was written against:

        before the 14sep batch   integer ARP_TIMEOUT;
        current body             integer ARP_TIMEOUT { min = 60; max = 28800; }

    The declaration gained the bound and nothing announced it. So the engine DOES catch an
    out-of-range value now, and the registry carries 60..28800 -- the declaration's numbers,
    which the child template repeats -- rather than the body's laxer `<= 0`. A 30 is refused
    here before anything is sent, which makes the body's rule unreachable from the module.

    The third claim survives untouched: no default_template, because the template declares none.
    """
    for parent in (PARENT, "int_subif", "int_vlan"):
        b = resolve_binding(parent, "arp_timeout")
        assert b is not None, (
            "{0} lost arp_timeout; the three parents go in as one lot".format(parent)
        )
        assert b["parent_nvpair"] == "arpTimeout"
        assert b["type"] == "integer"
        assert b["mechanism"] == "passthrough"
        # The declaration's bound, not the body's `<= 0`. Spelled min_value/max_value in the
        # runtime table: the registry says min/max and the generator renames them, so that a
        # substring search for "min" does not also hit min_ndfc_version and min_length.
        assert (b["min_value"], b["max_value"]) == (60, 28800)
        assert "default_template" not in b, "the template declares no ARP_TIMEOUT default"


def test_ipv4_acl_in_carries_the_template_length_constraints():
    b = resolve_binding(PARENT, "ipv4_acl_in")
    assert b["min_length"] == 1
    assert b["max_length"] == 64


@pytest.mark.parametrize(
    "key",
    ["disable_lldp_transmit", "disable_lldp_receive", "disable_bfd_echo",
     "disable_qos_stats", "disable_queuing_stats"],
)
def test_the_boolean_bindings_declare_the_template_default(key):
    """All four are ``boolean X { defaultValue=false; }`` on the controller."""
    assert resolve_binding(PARENT, key)["default_template"] is False


def test_the_routed_spec_is_extended_with_the_registered_keys():
    """The fix on the module side.

    Registering a binding is not enough: without this call the validator rejects the key before
    anything is built, and the binding is unreachable. This is the exact failure mode the dot1q
    port-channel had -- registered, transported by the engine, rejected by the arg spec.
    """
    src = inspect.getsource(dcnm_interface.DcnmIntf.dcnm_intf_validate_ethernet_interface_input)
    assert 'gie_extend_prof_spec' in src
    assert '"int_routed_host"' in src or "'int_routed_host'" in src, (
        "eth_prof_spec_routed_host is never extended with the int_routed_host bindings"
    )


def test_the_stats_pair_has_a_reachable_qos_scaffold_on_this_parent():
    """Why these two are registered here and were a dead end on dot1q.

    DISABLE_QOS_STATS and DISABLE_QUEUING_STATS only append ``no-stats`` to the service-policy
    line ENABLE_QOS emits (IsShow="ENABLE_QOS==true" and QUEUING_POLICY!=''). On the dot1q
    port-channel the scaffold was unreachable until the spec was fixed. Here it is already
    native to eth_prof_spec_routed_host -- assert that, so a future trim of those three keys
    does not quietly turn these two bindings back into transport with no CLI.
    """
    src = inspect.getsource(dcnm_interface.DcnmIntf.dcnm_intf_validate_ethernet_interface_input)
    i = src.find("eth_prof_spec_routed_host = dict(")
    assert i != -1
    spec = src[i:src.find(")", src.find("queuing_policy", i))]
    for key in ("enable_qos", "qos_policy", "queuing_policy"):
        assert key in spec, "{0} left eth_prof_spec_routed_host".format(key)


def test_the_parent_is_registered_exactly_once_per_nvpair():
    """A duplicated row would make resolve_binding's answer order-dependent."""
    rows = [b for b in BINDING_TABLE if b["parent_template"] == PARENT]
    names = [b["parent_nvpair"] for b in rows]
    assert len(names) == len(set(names)), "duplicate nvPair rows for {0}".format(PARENT)
    # EXPECTED covers this parent's pre-EIGRP inventory. Subtracting the EIGRP rows keeps the
    # equality strict -- anything else new still fails here -- while pointing at the file that
    # owns them. Widening it to a subset check would have retired the guard instead of scoping it.
    eigrp = {b["parent_nvpair"] for b in BINDING_TABLE
             if "eigrp" in b["parent_nvpair"].lower()}
    assert set(names) - eigrp == {nvpair for nvpair, _native in EXPECTED.values()}
    assert len(eigrp & set(names)) == 13, "int_routed_host should carry 13 EIGRP rows"


# ====================================================================================================
# Formerly test_dcnm_intf_routed_ipv6.py
# IPv6 address and prefix on a routed Ethernet port (mode: routed, int_routed_host).
#
# int_routed_host declares IPv6 and IPv6_PREFIX and renders `ipv6 address` only when both are set. The module accepted
# ipv6_addr/ipv6_mask_len only for epl_routed and subinterfaces; for mode routed the inputs were dropped and the request
# carried no IPv6 nvPair.
#
# Every case runs real main() through helpers/binding_harness and asserts the CAPTURED REQUEST: policy, interface identity
# and nvPairs. The default HAVE is the module's own replaced payload with the IPv6 pair set the way the controller stores
# it ("" and "" when unset, as in the measured int_routed_host read in fixtures/routing_have_cases.json#dcnm_intf_routed_ospf_have); the
# measured-shape cases use that 84-key read itself. Roles are the lower-case values NDFC returns ("leaf" resets to
# int_trunk_host, "border" to int_routed_host). Addresses are documentation values.
#
# The pair travels only when the playbook sets ipv6_addr or ipv6_mask_len or the stored int_routed_host intent
# already carries the keys; the "stock" cases below use an intent without them.
# ====================================================================================================
V6 = "2001:db8:117::1"
V6_B = "2001:db8:118::1"
V4 = "192.0.2.1"
BASE = {"mode": "routed", "ipv4_addr": V4, "ipv4_mask_len": 24, "admin_state": False, "description": "routed-v6"}
DUAL = dict(BASE, ipv6_addr=V6, ipv6_mask_len=64)
V6_ONLY = {"mode": "routed", "ipv6_addr": V6, "ipv6_mask_len": 64, "admin_state": False}

_ORIG_TRANSPORT = h._transport
PHYSICAL = {"deletable": "false", "editAllowed": "true", "mgmtIpAddress": h.SWITCH_IP}


def _physical_transport(calls, have):
    inner = _ORIG_TRANSPORT(calls, have)

    def send(mod, method, path, payload=None):
        resp = inner(mod, method, path, payload)
        if method == "GET" and "/interface/detail" in path and isinstance(resp.get("DATA"), list):
            for e in resp["DATA"]:
                if str(e.get("isPhysical")).lower() == "true":
                    e.update(PHYSICAL)
        return resp
    return send


def _inventory(role):
    inv = load_case("dcnm_intf_binding_configs")["mock_fab_inv_data"]
    for v in inv.values():
        v["switchRole"] = role
    return inv


def run(configs, state, have=None, role="leaf", check_mode=False):
    with patch.object(h, "_transport", _physical_transport):
        return h.run_configs(configs, state, have=have, check_mode=check_mode,
                             extra_patch=patch.object(module, "get_fabric_inventory_details",
                                                      return_value=_inventory(role)))


def cfg(profile, ifname=h.IF_A):
    return h.cfg(ifname, profile)


def routed_have(ifname=h.IF_A, ipv6="", prefix="", **profile):
    """HAVE = the module's own replaced payload for a routed port, with the IPv6 pair as the controller stores it."""
    p = dict(BASE, **profile)
    p.pop("ipv6_addr", None)
    p.pop("ipv6_mask_len", None)
    _result, calls = run([cfg(p, ifname)], "replaced")
    have = h._payload_as_have(calls)
    nv = have[0]["interfaces"][0]["nvPairs"]
    nv["IPv6"] = ipv6
    nv["IPv6_PREFIX"] = prefix
    have[0]["interfaces"][0]["ifName"] = ifname
    return have


def measured_have(ipv6="", prefix=""):
    """The measured 84-key int_routed_host read (OSPF gate set to its disabled value, tag kept stored as NDFC does)."""
    m = load_case("dcnm_intf_routed_ospf_have")
    nv = copy.deepcopy(m["nvPairs"])
    nv.update({"ospf": "false", "IPv6": ipv6, "IPv6_PREFIX": prefix, "INTF_NAME": h.IF_A})
    intf = {"ifName": h.IF_A, "serialNumber": h.SERIAL, "fabricName": h.FABRIC,
            "interfaceType": "INTERFACE_ETHERNET", "nvPairs": nv}
    return [{"policy": m["policy"], "interfaces": [intf]}]


def sent(calls):
    """{ifName: (policy, nvPairs)} of every interface in every configuration update."""
    found = []
    h._collect_policies([c["payload"] for c in h.split_calls(calls)["updates"]], found)
    out = {}
    for p in found:
        for i in p["interfaces"]:
            out[i["ifName"]] = (p["policy"], i.get("nvPairs", {}))
    return out


def pair(nv):
    return nv.get("IPv6", "<absent>"), nv.get("IPv6_PREFIX", "<absent>")


# ------------------------------------------------------------------ merged
def test_merged_ipv6_only_create_sends_the_pair():
    result, calls = run([cfg(V6_ONLY)], "merged")
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A] and out[h.IF_A][0] == h.ROUTED
    assert pair(out[h.IF_A][1]) == (V6, "64")
    assert (out[h.IF_A][1]["IP"], out[h.IF_A][1]["PREFIX"]) == ("", "")


def test_merged_dual_stack_create_sends_both_families():
    result, calls = run([cfg(DUAL)], "merged")
    nv = sent(calls)[h.IF_A][1]
    assert not result.get("failed"), result.get("msg")
    assert (nv["IP"], nv["PREFIX"]) == (V4, "24")
    assert pair(nv) == (V6, "64")


def test_merged_changes_address_and_prefix():
    have = routed_have(ipv6=V6, prefix="64")
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6_B, ipv6_mask_len=127))], "merged", have)
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A]
    assert pair(out[h.IF_A][1]) == (V6_B, "127")


def test_merged_description_only_keeps_the_stored_ipv6():
    have = routed_have(ipv6=V6, prefix="64")
    result, calls = run([cfg({"mode": "routed", "description": "only-description"})], "merged", have)
    nv = sent(calls)[h.IF_A][1]
    assert not result.get("failed"), result.get("msg")
    assert nv["DESC"] == "only-description"
    assert pair(nv) == (V6, "64")
    assert (nv["IP"], nv["PREFIX"]) == (V4, "24")


def test_merged_repeat_is_a_no_op():
    have = routed_have(ipv6=V6, prefix="64")
    result, calls = run([cfg(DUAL)], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_merged_address_without_prefix_on_a_port_without_ipv6_uses_the_validated_default():
    have = routed_have()
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6))], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == (V6, "64")


def test_merged_address_without_prefix_keeps_the_stored_prefix():
    have = routed_have(ipv6=V6, prefix="127")
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6_B))], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == (V6_B, "127")


def test_merged_prefix_only_change_keeps_the_stored_address():
    have = routed_have(ipv6=V6, prefix="64")
    result, calls = run([cfg({"mode": "routed", "ipv6_mask_len": 127})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == (V6, "127")


def test_merged_explicit_empty_address_clears_the_pair():
    have = routed_have(ipv6=V6, prefix="64")
    result, calls = run([cfg(dict(BASE, ipv6_addr=""))], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == ("", "")


def test_merged_prefix_without_any_address_is_not_stored():
    have = routed_have()
    result, calls = run([cfg(dict(BASE, ipv6_mask_len=127, description="other"))], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == ("", "")


def test_merged_without_ipv6_input_ignores_a_have_without_the_ipv6_keys():
    """An intent without IPv6 keys (synthetic: the measured read carries them) is compared only on requested keys."""
    have = routed_have()
    for k in ("IPv6", "IPv6_PREFIX"):
        have[0]["interfaces"][0]["nvPairs"].pop(k)
    result, calls = run([cfg({"mode": "routed", "description": "only-description"})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    nv = sent(calls)[h.IF_A][1]
    assert nv["DESC"] == "only-description" and (nv["IP"], nv["PREFIX"]) == (V4, "24")
    assert pair(nv) == ("<absent>", "<absent>")


def test_merged_ipv6_input_is_sent_when_the_have_lacks_the_ipv6_keys():
    have = routed_have()
    for k in ("IPv6", "IPv6_PREFIX"):
        have[0]["interfaces"][0]["nvPairs"].pop(k)
    result, calls = run([cfg({"mode": "routed", "ipv6_addr": V6, "ipv6_mask_len": 127})], "merged", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == (V6, "127")


def test_merged_repeat_on_the_measured_controller_shape_is_a_no_op():
    result, calls = run([cfg({"mode": "routed", "ipv6_addr": V6, "ipv6_mask_len": 64})], "merged",
                        measured_have(V6, "64"))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_merged_mixed_case_address_matches_the_stored_lower_case_value():
    result, calls = run([cfg({"mode": "routed", "ipv6_addr": V6.upper(), "ipv6_mask_len": 64})], "merged",
                        measured_have(V6, "64"))
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


# ------------------------------------------------------------------ replaced
def test_replaced_changes_address_and_prefix():
    have = routed_have(ipv6=V6, prefix="64")
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6_B, ipv6_mask_len=127))], "replaced", have)
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A] and out[h.IF_A][0] == h.ROUTED
    assert pair(out[h.IF_A][1]) == (V6_B, "127")


def test_replaced_omission_withdraws_address_and_prefix_together():
    have = routed_have(ipv6=V6, prefix="127")
    result, calls = run([cfg(BASE)], "replaced", have)
    nv = sent(calls)[h.IF_A][1]
    assert not result.get("failed"), result.get("msg")
    assert pair(nv) == ("", "")
    assert (nv["IP"], nv["PREFIX"]) == (V4, "24")


def test_replaced_prefix_without_address_does_not_reintroduce_a_prefix():
    have = routed_have(ipv6=V6, prefix="127")
    result, calls = run([cfg(dict(BASE, ipv6_mask_len=127))], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == ("", "")


def test_replaced_repeat_after_withdrawal_is_stable():
    result, calls = run([cfg(BASE)], "replaced", routed_have())
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_replaced_repeat_on_the_measured_controller_shape_is_stable():
    profile = {"mode": "routed", "ipv4_addr": "192.0.2.17", "ipv4_mask_len": 8, "ipv6_addr": V6, "ipv6_mask_len": 64}
    have = measured_have(V6, "64")
    have[0]["interfaces"][0]["nvPairs"]["PREFIX"] = "8"
    result, calls = run([cfg(profile)], "replaced", have)
    assert not result.get("failed"), result.get("msg")
    # The measured read also holds an OSPF passive value this profile omits, so replaced writes for that key; the
    # IPv6 pair is not a reported change and travels unchanged.
    assert not any(k in d for d in h.diff_nvpairs(result) for k in ("IPv6", "IPv6_PREFIX"))
    assert pair(sent(calls)[h.IF_A][1]) == (V6, "64")


# ------------------------------------------------------------------ overridden
def test_overridden_retained_interface_withdraws_omitted_ipv6_and_leaves_the_control_alone():
    have = routed_have(h.IF_A, ipv6=V6, prefix="64") + routed_have(h.IF_B)
    result, calls = run([cfg(BASE, h.IF_A), cfg(BASE, h.IF_B)], "overridden", have)
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A]
    assert out[h.IF_A][0] == h.ROUTED and pair(out[h.IF_A][1]) == ("", "")


@pytest.mark.parametrize("role, policy", [("leaf", h.TRUNK), ("border", h.ROUTED)])
def test_overridden_omitted_routed_port_is_reset_to_the_role_default_without_ipv6(role, policy):
    have = routed_have(h.IF_A, ipv6=V6, prefix="64") + routed_have(h.IF_B)
    result, calls = run([cfg(BASE, h.IF_B)], "overridden", have, role=role)
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A]
    assert out[h.IF_A][0] == policy
    assert pair(out[h.IF_A][1]) == (("", "") if policy == h.ROUTED else ("<absent>", "<absent>"))


# ------------------------------------------------------------------ deleted
@pytest.mark.parametrize("role, policy", [("leaf", h.TRUNK), ("border", h.ROUTED)])
def test_deleted_resets_a_routed_port_with_ipv6_to_the_role_default(role, policy):
    have = routed_have(h.IF_A, ipv6=V6, prefix="64")
    result, calls = run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", have, role=role)
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A]
    assert out[h.IF_A][0] == policy
    if policy == h.ROUTED:
        assert pair(out[h.IF_A][1]) == ("", "")
    else:
        assert "IPv6" not in out[h.IF_A][1] and "IPv6_PREFIX" not in out[h.IF_A][1]


@pytest.mark.parametrize("role", ["leaf", "border"])
def test_deleted_repeat_on_the_default_is_stable(role):
    have = routed_have(h.IF_A, ipv6=V6, prefix="64")
    _result, calls = run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", have, role=role)
    reset = []
    h._collect_policies([c["payload"] for c in h.split_calls(calls)["updates"]], reset)
    reset[0]["interfaces"][0].update({"interfaceType": "INTERFACE_ETHERNET", "fabricName": h.FABRIC})
    result, calls = run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", reset, role=role)
    assert not result.get("failed"), result.get("msg")
    assert h.split_calls(calls)["updates"] == []


def test_border_deleted_repeat_with_an_intent_without_ipv6_keys_is_stable():
    """An intent that lacks the IPv6 keys (not observed: the measured read carries them) reads as default."""
    _result, calls = run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", routed_have(), role="border")
    reset = []
    h._collect_policies([c["payload"] for c in h.split_calls(calls)["updates"]], reset)
    reset[0]["interfaces"][0].update({"interfaceType": "INTERFACE_ETHERNET", "fabricName": h.FABRIC})
    for k in ("IPv6", "IPv6_PREFIX"):
        reset[0]["interfaces"][0]["nvPairs"].pop(k)
    result, calls = run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", reset, role="border")
    assert not result.get("failed"), result.get("msg")
    assert h.split_calls(calls)["updates"] == []


# ------------------------------------------------------------------ query
def test_query_returns_the_stored_pair_without_writes():
    have = measured_have(V6, "127")
    result, calls = run([{"name": h.IF_A, "switch": [h.SWITCH_IP]}], "query", have)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []
    got = [i for p in result["response"] for i in p["interfaces"] if i["ifName"] == h.IF_A]
    assert len(got) == 1 and pair(got[0]["nvPairs"]) == (V6, "127")
    assert any("ifName=" + h.IF_A in c["path"] for c in calls if c["method"] == "GET")


# ------------------------------------------------------------------ validation
@pytest.mark.parametrize("profile", [
    dict(BASE, ipv6_addr="2001:db8::zz"),
    dict(BASE, ipv6_addr="192.0.2.9"),
    dict(BASE, ipv6_addr=V6, ipv6_mask_len=0),
    dict(BASE, ipv6_addr=V6, ipv6_mask_len=128),
])
def test_invalid_ipv6_input_is_refused_before_any_request(profile):
    result, calls = run([cfg(profile)], "merged")
    assert result.get("failed")
    assert h.writes(calls) == []


# int_routed_host declares IPv6_PREFIX with min 1 and max 127.
@pytest.mark.parametrize("mask", [1, 48, 63, 64, 127])
def test_prefix_boundaries_are_accepted(mask):
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6, ipv6_mask_len=mask))], "merged")
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == (V6, str(mask))


# ------------------------------------------------------------------ controls
def test_ipv4_only_routed_create_without_a_stored_intent_sends_no_ipv6_keys():
    result, calls = run([cfg(BASE)], "merged")
    nv = sent(calls)[h.IF_A][1]
    assert not result.get("failed"), result.get("msg")
    assert (nv["IP"], nv["PREFIX"], nv["INTF_VRF"], nv["DESC"], nv["ADMIN_STATE"]) == (V4, "24", "default", "routed-v6", "false")
    assert pair(nv) == ("<absent>", "<absent>")


def test_epl_routed_still_sends_its_ipv6_pair():
    profile = {"mode": "epl_routed", "ipv4_addr": V4, "ipv4_mask_len": 24, "ipv6_addr": V6, "ipv6_mask_len": 127}
    result, calls = run([cfg(profile)], "merged")
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert out[h.IF_A][0] == "epl_routed_intf"
    assert pair(out[h.IF_A][1]) == (V6, "127")


@pytest.mark.parametrize("profile, iftype, ifname", [
    ({"mode": "epl_routed", "ipv4_addr": V4, "ipv4_mask_len": 24, "ipv6_addr": V6, "ipv6_mask_len": 63},
     "eth", h.IF_A),
    ({"mode": "subint", "vlan": h.SUB_VLAN, "ipv4_addr": V4, "ipv4_mask_len": 24, "ipv6_addr": V6,
      "ipv6_mask_len": 63}, "sub_int", h.IF_SUB),
])
def test_other_families_keep_their_prefix_range(profile, iftype, ifname):
    result, calls = run([h.cfg(ifname, profile, iftype=iftype)], "merged")
    assert result.get("failed")
    assert "ipv6_mask_len" in result.get("msg", "")
    assert h.writes(calls) == []


# ------------------------------------------------------------------ stored intent without the IPv6 keys
# Some int_routed_host bodies do not declare IPv6 or IPv6_PREFIX (stock captures of NDFC 12.5 and 12.6), so
# their stored intent has neither key. An IPv4-only request must not introduce them, even as empty strings.
# An explicit request still sends the pair; whether such a body accepts it is not known.
def stock_have(ifname=h.IF_A, **profile):
    """A routed intent shaped like a body without IPv6 parameters: the keys are absent, not empty."""
    have = routed_have(ifname, **profile)
    for k in ("IPv6", "IPv6_PREFIX"):
        have[0]["interfaces"][0]["nvPairs"].pop(k)
    return have


def trunk_have(ifname=h.IF_A):
    """The module's own int_trunk_host payload, as the stored intent before a port becomes routed."""
    _result, calls = run([cfg({"mode": "trunk"}, ifname)], "replaced")
    found = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], found)
    found[0]["interfaces"][0].update({"interfaceType": "INTERFACE_ETHERNET", "fabricName": h.FABRIC})
    return found


def no_ipv6_keys(nv):
    return "IPv6" not in nv and "IPv6_PREFIX" not in nv


def test_stock_merged_ipv4_conversion_from_trunk_sends_no_ipv6_keys():
    result, calls = run([cfg(BASE)], "merged", trunk_have())
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert out[h.IF_A][0] == h.ROUTED and out[h.IF_A][1]["IP"] == V4
    assert no_ipv6_keys(out[h.IF_A][1])


def test_stock_merged_ipv4_update_sends_no_ipv6_keys():
    result, calls = run([cfg({"mode": "routed", "description": "changed"})], "merged", stock_have())
    nv = sent(calls)[h.IF_A][1]
    assert not result.get("failed"), result.get("msg")
    assert nv["DESC"] == "changed" and no_ipv6_keys(nv)


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_stock_ipv4_repeat_is_a_no_op(state):
    result, calls = run([cfg(BASE)], state, stock_have())
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []


def test_stock_replaced_ipv4_change_sends_no_ipv6_keys():
    result, calls = run([cfg(dict(BASE, ipv4_addr="192.0.2.5"))], "replaced", stock_have())
    nv = sent(calls)[h.IF_A][1]
    assert not result.get("failed"), result.get("msg")
    assert nv["IP"] == "192.0.2.5" and no_ipv6_keys(nv)


def test_stock_overridden_retained_ipv4_change_sends_no_ipv6_keys():
    result, calls = run([cfg(dict(BASE, description="changed"))], "overridden", stock_have())
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A] and no_ipv6_keys(out[h.IF_A][1])


@pytest.mark.parametrize("state", ["deleted", "overridden"])
@pytest.mark.parametrize("role, policy", [("leaf", h.TRUNK), ("border", h.ROUTED)])
def test_stock_reset_to_the_role_default_sends_no_ipv6_keys(state, role, policy):
    have = stock_have(h.IF_A) + routed_have(h.IF_B)
    configs = ([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}] if state == "deleted"
               else [cfg(BASE, h.IF_B)])
    result, calls = run(configs, state, have, role=role)
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert list(out) == [h.IF_A] and out[h.IF_A][0] == policy
    assert no_ipv6_keys(out[h.IF_A][1])


def test_stock_border_reset_repeat_is_a_no_op():
    have = stock_have(h.IF_A)
    _result, calls = run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", have, role="border")
    reset = []
    h._collect_policies([c["payload"] for c in h.split_calls(calls)["updates"]], reset)
    reset[0]["interfaces"][0].update({"interfaceType": "INTERFACE_ETHERNET", "fabricName": h.FABRIC})
    result, calls = run([{"name": h.IF_A, "type": "eth", "switch": [h.SWITCH_IP]}], "deleted", reset, role="border")
    assert not result.get("failed"), result.get("msg")
    assert h.split_calls(calls)["updates"] == []


def test_stock_query_returns_no_pair_and_writes_nothing():
    result, calls = run([{"name": h.IF_A, "switch": [h.SWITCH_IP]}], "query", stock_have())
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []
    got = [i for r in result["response"] for i in r.get("interfaces", []) if i.get("ifName") == h.IF_A]
    assert len(got) == 1 and no_ipv6_keys(got[0]["nvPairs"])


def test_stock_check_mode_ipv4_change_writes_nothing_and_reports_no_ipv6_keys():
    result, calls = run([cfg(dict(BASE, description="changed"))], "merged", stock_have(), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []
    assert result["changed"] is True
    assert h.diff_nvpairs(result) and all(no_ipv6_keys(nv) for nv in h.diff_nvpairs(result))


def test_check_mode_explicit_ipv6_reports_the_pair_and_writes_nothing():
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6, ipv6_mask_len=48))], "merged", stock_have(), check_mode=True)
    assert not result.get("failed"), result.get("msg")
    assert h.writes(calls) == []
    assert any(pair(nv) == (V6, "48") for nv in h.diff_nvpairs(result))


@pytest.mark.parametrize("state", ["merged", "replaced"])
def test_stock_explicit_ipv6_is_sent(state):
    """Positive control. Sending it does not show that a body without IPv6 parameters accepts it."""
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6, ipv6_mask_len=48))], state, stock_have())
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == (V6, "48")


def test_stock_explicit_ipv6_over_trunk_is_sent():
    result, calls = run([cfg(dict(BASE, ipv6_addr=V6, ipv6_mask_len=48))], "merged", trunk_have())
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert out[h.IF_A][0] == h.ROUTED and pair(out[h.IF_A][1]) == (V6, "48")


def test_stock_explicit_empty_address_is_sent_as_an_empty_pair():
    """Explicit empty is a request; omission is not (see the IPv4-only cases above)."""
    result, calls = run([cfg(dict(BASE, ipv6_addr="", description="changed"))], "merged", stock_have())
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == ("", "")


def test_stored_empty_keys_ipv4_update_keeps_the_empty_pair():
    """Keys present but empty: the stored intent declares them, so the pair travels unchanged."""
    result, calls = run([cfg(dict(BASE, description="changed"))], "replaced", routed_have())
    nv = sent(calls)[h.IF_A][1]
    assert not result.get("failed"), result.get("msg")
    assert nv["DESC"] == "changed" and pair(nv) == ("", "")


def test_stored_address_is_withdrawn_when_omitted_under_replaced():
    """The guard keeps the withdrawal: the stored intent carries the keys."""
    result, calls = run([cfg(BASE)], "replaced", routed_have(ipv6=V6, prefix="48"))
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == ("", "")


def test_stock_merged_address_without_prefix_uses_the_validated_default():
    result, calls = run([cfg({"mode": "routed", "ipv6_addr": V6})], "merged", stock_have())
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == (V6, "64")


def test_stock_merged_prefix_without_address_stores_nothing():
    result, calls = run([cfg({"mode": "routed", "ipv6_mask_len": 48, "description": "changed"})], "merged",
                        stock_have())
    assert not result.get("failed"), result.get("msg")
    assert pair(sent(calls)[h.IF_A][1]) == ("", "")


def test_ipv6_keys_stored_under_another_policy_do_not_count():
    """epl_routed_intf stores IPv6 keys; they say nothing about the int_routed_host body."""
    epl = {"mode": "epl_routed", "ipv4_addr": V4, "ipv4_mask_len": 24, "ipv6_addr": V6, "ipv6_mask_len": 64}
    _result, calls = run([cfg(epl)], "replaced")
    have = []
    h._collect_policies([c["payload"] for c in h.writes(calls)], have)
    have[0]["interfaces"][0].update({"interfaceType": "INTERFACE_ETHERNET", "fabricName": h.FABRIC})
    assert "IPv6" in have[0]["interfaces"][0]["nvPairs"]
    result, calls = run([cfg(BASE)], "merged", have)
    out = sent(calls)
    assert not result.get("failed"), result.get("msg")
    assert out[h.IF_A][0] == h.ROUTED and no_ipv6_keys(out[h.IF_A][1])


# ====================================================================================================
# Formerly test_gie_smu197_vpc_module_path.py
# Paired vPC withdrawal through the real dcnm_interface.main() path.
#
# The VPC_SNO response shape and reversed pair order mirror captured GET responses. All addresses, serials, members and policy names here are synthetic.
# Controller and device behavior remains outside this offline test.
# ====================================================================================================
TARGETS = {
    VPC_ACCESS: {"aclFilter": "", "lldpReceive": "false", "lldpTransmit": "false",
                 "qosStatsSuppressed": "false", "queuingStats": "false",
                 "spanningTreePortType": "no"},
    VPC_TRUNK: {"aclFilter": "", "lldpReceive": "false", "lldpTransmit": "false",
                "qosStatsSuppressed": "false", "queuingStats": "false",
                "spanningTreePortType": "no", "GUARD_MODE": "no"},
}
PUBLIC_KEYS = ("acl_filter", "disable_lldp_receive", "disable_lldp_transmit",
               "disable_qos_stats", "disable_queuing_stats", "spanning_tree_port_type",
               "guard_mode")


def _configs(positive):
    configs = []
    for parent in (VPC_ACCESS, VPC_TRUNK):
        profile = base_for(parent)
        if positive:
            profile.update(acl_filter="PILOT-ACL", disable_lldp_receive=True,
                           disable_lldp_transmit=True, disable_qos_stats=True,
                           disable_queuing_stats=True,
                           spanning_tree_port_type=("normal" if parent == VPC_ACCESS
                                                    else "network"))
            if parent == VPC_TRUNK:
                profile["guard_mode"] = "root"
        else:
            assert not set(PUBLIC_KEYS) & set(profile)
        configs.append(cfg_for(parent, profile))
    return configs


def _policies(calls):
    found = []
    _collect_policies([call["payload"] for call in writes(calls)], found)
    return {p["policy"]: p for p in found}


def _wire(policy):
    return policy["interfaces"][0]["nvPairs"]


def _assert_pair(policy, parent):
    iface = policy["interfaces"][0]
    assert policy["policy"] == parent
    assert iface["serialNumber"] == VPC_PAIR_SERIAL
    assert iface["interfaceType"] == "INTERFACE_VPC"
    assert iface["ifName"] == ("vPC11" if parent == VPC_ACCESS else "vPC12")
    nv = iface["nvPairs"]
    assert nv["PEER1_MEMBER_INTERFACES"] == nv["PEER2_MEMBER_INTERFACES"] == "Ethernet1/51"
    # The pair response orders peer 2 before peer 1. The module must remap
    # descriptions with that order rather than silently treating it as input order.
    assert nv["PEER1_PO_DESC"] == "pilot peer2"
    assert nv["PEER2_PO_DESC"] == "pilot peer1"
    assert nv["PORTTYPE_FAST_ENABLED"] == "false"
    assert nv["QOS_POLICY"] == "pilot_qos" and nv["QUEUING_POLICY"] == "pilot_queue"


def test_pair_main_path_positive_merged_check_replaced_and_rerun():
    positive, pos_calls = run_configs(_configs(True), "merged", [])
    assert not positive.get("failed") and positive["changed"]
    lookups = [c for c in pos_calls if c["method"] == "GET"
               and "vpcpair_serial_number" in c["path"]]
    assert len(lookups) == 2
    assert {c["path"].split("serial_number=")[1] for c in lookups} == {SERIAL, PEER_SERIAL}
    have_by_parent = _policies(pos_calls)
    assert set(have_by_parent) == set(TARGETS)
    for parent, policy in have_by_parent.items():
        _assert_pair(policy, parent)
        assert all(_wire(policy)[name] != reset for name, reset in TARGETS[parent].items())

    have = list(copy.deepcopy(have_by_parent).values())
    omitted = _configs(False)
    merged, merged_calls = run_configs(omitted, "merged", have)
    assert not merged.get("failed") and not merged["changed"]
    assert not request_nvpairs(merged_calls) and not split_calls(merged_calls)["updates"]

    checked, check_calls = run_configs(omitted, "replaced", have, check_mode=True)
    assert not checked.get("failed") and checked["changed"]
    assert not writes(check_calls)
    check_diff = {p["interfaces"][0]["ifName"]: _wire(p)
                  for p in checked["diff"][0]["replaced"]}
    assert set(check_diff) == {"vPC11", "vPC12"}
    for parent, name in ((VPC_ACCESS, "vPC11"), (VPC_TRUNK, "vPC12")):
        assert {k: check_diff[name][k] for k in TARGETS[parent]} == TARGETS[parent]

    replaced, replace_calls = run_configs(omitted, "replaced", have)
    assert not replaced.get("failed") and replaced["changed"]
    requests = _policies(replace_calls)
    assert set(requests) == set(TARGETS)
    assert len(split_calls(replace_calls)["updates"]) == 1
    assert len(split_calls(replace_calls)["deploys"]) == 1
    assert len(diff_nvpairs(replaced)) == 2
    for parent, policy in requests.items():
        _assert_pair(policy, parent)
        assert {k: _wire(policy)[k] for k in TARGETS[parent]} == TARGETS[parent]

    converged = copy.deepcopy(have)
    for item in converged:
        parent = item["policy"]
        _wire(item).update({k: _wire(requests[parent])[k] for k in TARGETS[parent]})
    rerun, rerun_calls = run_configs(omitted, "replaced", converged)
    assert not rerun.get("failed") and not rerun["changed"]
    assert not diff_nvpairs(rerun) and not writes(rerun_calls)


def test_pim_vpc_and_prior_routed_reset_coexist_as_separate_valid_interfaces():
    """One invocation carries a routed PIM profile and a distinct vPC profile."""
    routed = dict(base_for(ROUTED), enable_pim_sparse=True,
                  pim_dr_priority=77, disable_lldp_receive=True)
    vpc = dict(base_for(VPC_ACCESS), acl_filter="PILOT-ACL",
               disable_lldp_receive=True)
    positive = [cfg_for(ROUTED, routed), cfg_for(VPC_ACCESS, vpc)]
    applied, calls = run_configs(positive, "merged", [])
    assert not applied.get("failed") and applied["changed"]
    have = list(copy.deepcopy(_policies(calls)).values())
    assert {p["policy"] for p in have} == {ROUTED, VPC_ACCESS}

    routed.pop("pim_dr_priority")
    routed.pop("disable_lldp_receive")
    vpc.pop("acl_filter")
    vpc.pop("disable_lldp_receive")
    omitted = [cfg_for(ROUTED, routed), cfg_for(VPC_ACCESS, vpc)]
    result, replacement_calls = run_configs(omitted, "replaced", have)
    assert not result.get("failed") and result["changed"]
    sent = _policies(replacement_calls)
    assert set(sent) == {ROUTED, VPC_ACCESS}
    assert _wire(sent[ROUTED])["PIM_DR_PRIORITY"] == "1"
    assert _wire(sent[ROUTED])["ENABLE_PIM_SPARSE"] == "true"
    assert _wire(sent[ROUTED])["lldpReceive"] == "false"
    assert _wire(sent[VPC_ACCESS])["aclFilter"] == ""
    assert _wire(sent[VPC_ACCESS])["lldpReceive"] == "false"
    _assert_pair(sent[VPC_ACCESS], VPC_ACCESS)


@pytest.mark.parametrize("family", ("PIM/ACL", "vPC"))
def test_combined_case_fails_when_one_source_family_is_removed_in_memory(monkeypatch, family):
    """A green combined case must depend on both source families' registrations."""
    if family == "PIM/ACL":
        rows = [row for row in BINDING_TABLE
                if row["profile_key"] in ("enable_pim_sparse", "pim_dr_priority",
                                          "ipv4_acl_in", "enable_pim_bfd_instance")
                and row["parent_template"] in
                ("int_loopback", ROUTED, "int_subif", "int_vlan")]
        assert len(rows) == 11   # + int_subif pimBfdInstance (slice 0b_37)
    else:
        rows = [row for row in BINDING_TABLE
                if row["parent_template"] in (VPC_ACCESS, VPC_TRUNK)]
        assert len(rows) == 13
    with monkeypatch.context() as patcher:
        for row in rows:
            patcher.delitem(row, "reset_wire")
        with pytest.raises(AssertionError):
            test_pim_vpc_and_prior_routed_reset_coexist_as_separate_valid_interfaces()
