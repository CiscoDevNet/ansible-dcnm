"""The first bindings registered for ``int_routed_host``.

This parent is unlike the switchport parents already covered. It emits almost nothing itself:
every one of the six nvPairs registered here ends in a child template --

    DISABLE_LLDP_TRANSMIT  -> interface_lldp_disable              (creation gate)
    DISABLE_LLDP_RECEIVE   -> interface_lldp_disable              (creation gate)
    DISABLE_BFD_ECHO       -> bfd_no_echo_interface               (creation gate)
    IPV4_ACL_IN            -> interface_ip_access_group_in_11_1   (gate + value)
    DISABLE_QOS_STATS      -> interface_qos_service_policy        (DISABLE_STATS parameter)
    DISABLE_QUEUING_STATS  -> interface_queuing_service_policy    (DISABLE_STATS parameter)

-- read from the template body on the controller, not assumed. That delegation is NDFC's
internal business: the module still writes one parent nvPair and nothing else, so the mechanism
is ``passthrough``. The ``child_pti`` mechanism in this table means something different (a
binding owning a dedicated compat/validation path -- the OSPF-MD case) and these cases assert
the two are not confused, because reading "the template delegates to a child" as "therefore
child_pti" is the obvious wrong turn here.

ARP_TIMEOUT is declared by this template too and is deliberately NOT here: int_subif and
int_vlan declare it as well and all three are reachable (pol_types "sub_int_subint",
"svi_vlan", "eth_routed"), so committing it on the routed parent alone would make the module
answer "not supported" for the other two. It goes in as one lot across the three. The generator
caught that, not a review -- it rejects a row claiming a committed public profile_key from an
uncommitted parent.

What these cases cannot prove: that the child templates exist on the controller. They were
verified present on 12.6.0.267 out of band. A missing child would transport the nvPair, return
success, and produce no CLI -- exercised, never validated. Only the live run closes that.

Offline: no controller and no device.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import inspect

import pytest

from ansible_collections.cisco.dcnm.plugins.module_utils.gie_binding_table import (
    BINDING_TABLE,
    resolve_binding,
)
from ansible_collections.cisco.dcnm.plugins.modules import dcnm_interface

PARENT = "int_routed_host"

# profile_key -> (nvPair, registry type)
#
# The first six are passthrough, measured on Leaf-103/104 Ethernet1/5 in the r1..r4 cycle.
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
    "enable_ospf_auth": ("ENABLE_OSPF_AUTH", "boolean"),
    "ospf_auth_key_id": ("OSPF_AUTH_KEY_ID", "integer"),
    "ospf_auth_key": ("OSPF_AUTH_KEY", "string"),
    "ospf_authentication_key_type": ("OSPF_AUTHENTICATION_KEY_TYPE", "enum"),
    "ospf_authentication_key": ("OSPF_AUTHENTICATION_KEY", "string"),
    "disable_lldp_transmit": ("DISABLE_LLDP_TRANSMIT", "boolean"),
    "disable_lldp_receive": ("DISABLE_LLDP_RECEIVE", "boolean"),
    "disable_bfd_echo": ("DISABLE_BFD_ECHO", "boolean"),
    "disable_qos_stats": ("DISABLE_QOS_STATS", "boolean"),
    "disable_queuing_stats": ("DISABLE_QUEUING_STATS", "boolean"),
    "ipv4_acl_in": ("IPV4_ACL_IN", "string"),
    # slice 0b_28. El cuarto del grupo, DISABLE_IP_REDIRECTS, es nativo y no se registra.
    "disable_ipv4_redirects": ("DISABLE_IPV4_REDIRECTS", "boolean"),
    "disable_ipv6_redirects": ("DISABLE_IPV6_REDIRECTS", "boolean"),
    "ipv6_nd_suppress_ra": ("IPV6_ND_SUPPRESS_RA", "boolean"),
    # Dampening, slice 0b_6. Solo este padre lo declara; su CLI no existe en C9300v.
    "enable_dampening": ("ENABLE_DAMPENING", "boolean"),
    "dampening_half_life": ("DAMPENING_HALF_LIFE", "integer"),
    "dampening_reuse": ("DAMPENING_REUSE", "integer"),
    "dampening_suppress": ("DAMPENING_SUPPRESS", "integer"),
    "dampening_max_suppress": ("DAMPENING_MAX_SUPPRESS", "integer"),
    "dampening_restart": ("DAMPENING_RESTART", "boolean"),
    "dampening_restart_penalty": ("DAMPENING_RESTART_PENALTY", "integer"),
    "enable_ospf": ("ENABLE_OSPF", "boolean"),
    "ospf_tag": ("OSPF_TAG", "string"),
    "ospf_area_id": ("OSPF_AREA_ID", "string"),
    "ospf_cost": ("OSPF_COST", "integer"),
    "ospf_mtu_ignore": ("OSPF_MTU_IGNORE", "boolean"),
    "ospf_shutdown": ("OSPF_SHUTDOWN", "boolean"),
    "ospf_hello_interval": ("OSPF_HELLO_INTERVAL", "integer"),
    "ospf_dead_interval": ("OSPF_DEAD_INTERVAL", "integer"),
    "ospf_transmit_delay": ("OSPF_TRANSMIT_DELAY", "integer"),
    "ospf_priority": ("OSPF_PRIORITY", "integer"),
    "ospf_passive_mode": ("OSPF_PASSIVE_MODE", "enum"),
    "ospf_network_type": ("OSPF_NETWORK_TYPE", "enum"),
    "ospf_bfd_mode": ("OSPF_BFD_MODE", "enum"),
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

    assert set(EXPECTED).issubset(gie_guarded_keys())


def test_arp_timeout_stays_out_until_all_three_parents_go_in_together():
    """Pin the exclusion so it is a decision, not an oversight someone "fixes".

    int_routed_host declares ARP_TIMEOUT, so registering it here looks obviously right. It is
    not: int_subif and int_vlan declare it too and all three are reachable from a playbook.
    Committing one parent would make the module report "not supported on this interface" for
    the other two -- a false answer, which is the exact defect this table exists to prevent.

    When the lot does land, two measured facts must survive: the bound lives in the template
    BODY (`if int(arpTimeout) <= 0` rejects with "ARP timeout must be a positive integer"), not
    in the `integer ARP_TIMEOUT;` declaration -- so the engine will not catch a 0, the
    controller will; and it must carry no default_template, because the template declares none.
    """
    assert resolve_binding(PARENT, "arp_timeout") is None
    for other in ("int_subif", "int_vlan"):
        assert resolve_binding(other, "arp_timeout") is None, (
            "{0} got arp_timeout on its own; the three parents go in as one lot".format(other)
        )


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
    eigrp = {b["parent_nvpair"] for b in BINDING_TABLE if "EIGRP" in b["parent_nvpair"]}
    assert set(names) - eigrp == {nvpair for nvpair, _native in EXPECTED.values()}
    assert len(eigrp & set(names)) == 13, "int_routed_host should carry 13 EIGRP rows"
