"""Parsing, normalization and serialization of the int_vlan SVI address lists.

The wire cases use the representation measured on the controller readback and the shapes the
installed int_vlan template accepts (wrapper object or bare list, legacy element key for the
HSRP list). Expected values are literals, independent of the serializer under test.

Offline: no controller and no device.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.modules.dcnm_interface import (
    SviAddressListError,
    svi_address_list_desired,
    svi_address_list_from_input,
    svi_address_list_from_wire,
    svi_address_list_same,
    svi_address_list_to_wire,
    svi_address_normalize,
)

MEASURED = '{"secondaryGws":[{"gatewayIpAddress":"198.51.100.254/24"},{"gatewayIpAddress":"203.0.113.254/24"},{"gatewayIpAddress":"192.0.2.254/24"}]}'


def test_the_measured_readback_parses_with_host_bits_preserved():
    assert svi_address_list_from_wire("secondary_gws", MEASURED) == [
        ("198.51.100.254", "198.51.100.254/24"),
        ("203.0.113.254", "203.0.113.254/24"),
        ("192.0.2.254", "192.0.2.254/24"),
    ]


def test_serialization_round_trips_to_the_measured_text_byte_for_byte():
    entries = svi_address_list_from_wire("secondary_gws", MEASURED)
    assert svi_address_list_to_wire("secondary_gws", entries) == MEASURED


def test_empty_string_is_the_empty_list_and_serializes_back_to_empty_string():
    assert svi_address_list_from_wire("hsrp_secondary_vips", "") == []
    assert svi_address_list_to_wire("hsrp_secondary_vips", []) == ""


@pytest.mark.parametrize(
    "raw",
    [
        '[{"hsrpSecondaryVip":"192.0.2.123"}]',
        '{"hsrpSecondaryVips":[{"hsrpSecondaryVip":"192.0.2.123"}]}',
        '{"HSRP_SECONDARY_VIPS":[{"HSRP_SECONDARY_VIP":"192.0.2.123"}]}',
    ],
    ids=["bare-list", "wrapper", "legacy-keys"],
)
def test_every_shape_the_template_accepts_is_read(raw):
    assert svi_address_list_from_wire("hsrp_secondary_vips", raw) == [("192.0.2.123", "192.0.2.123")]


def test_an_empty_element_is_skipped_like_the_template_does():
    raw = '{"secondaryGws":[{"gatewayIpAddress":""},{"gatewayIpAddress":"192.0.2.9/24"}]}'
    assert svi_address_list_from_wire("secondary_gws", raw) == [("192.0.2.9", "192.0.2.9/24")]


@pytest.mark.parametrize(
    "raw",
    [
        None,
        7,
        "not json",
        "{}",
        '{"secondaryGws":[],"x":[]}',
        '{"secondaryGws":"a"}',
        "[1]",
        '[{"gatewayIpAddress":"192.0.2.9"}]',
        '[{"gatewayIpAddress":"192.0.2.9/24","x":1}]',
        '[{"gatewayIpAddress":"192.0.2.9/24"},{"gatewayIpAddress":"192.0.2.9/25"}]',
    ],
    ids=[
        "null",
        "int",
        "not-json",
        "empty-object",
        "two-wrappers",
        "wrapper-not-list",
        "non-object-element",
        "missing-prefix",
        "extra-element-key",
        "repeated-address",
    ],
)
def test_malformed_wire_raises(raw):
    with pytest.raises(SviAddressListError):
        svi_address_list_from_wire("secondary_gws", raw)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("192.0.2.254/24", ("192.0.2.254", "192.0.2.254/24")),
        ("192.0.2.0/24", ("192.0.2.0", "192.0.2.0/24")),
        ("192.0.2.254/32", ("192.0.2.254", "192.0.2.254/32")),
    ],
)
def test_secondary_gateway_normalization_keeps_the_host_bits(value, expected):
    assert svi_address_normalize("secondary_gws", value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "192.0.2.254",
        "192.0.2.254/0",
        "192.0.2.254/33",
        "192.0.2.254/024",
        "192.0.2.254/ 24",
        "192.0.2.254/255.255.255.0",
        "2001:db8::1/64",
        "192.0.2.256/24",
        " 192.0.2.254/24",
        24,
        "",
    ],
)
def test_secondary_gateway_rejects(value):
    with pytest.raises(SviAddressListError):
        svi_address_normalize("secondary_gws", value)


@pytest.mark.parametrize("value", ["192.0.2.123/32", "2001:db8::1", "192.0.2.1234", ""])
def test_hsrp_vip_rejects(value):
    with pytest.raises(SviAddressListError):
        svi_address_normalize("hsrp_secondary_vips", value)


def test_input_order_is_kept_and_identity_is_the_address():
    entries = svi_address_list_from_input("secondary_gws", [{"gateway_ip_address": "203.0.113.254/24"}, {"gateway_ip_address": "198.51.100.254/24"}])
    assert entries == [("203.0.113.254", "203.0.113.254/24"), ("198.51.100.254", "198.51.100.254/24")]


def test_sixteen_entries_are_accepted_and_seventeen_refused():
    sixteen = [{"hsrp_secondary_vip": "192.0.2.%d" % i} for i in range(1, 17)]
    assert len(svi_address_list_from_input("hsrp_secondary_vips", sixteen)) == 16
    with pytest.raises(SviAddressListError):
        svi_address_list_from_input("hsrp_secondary_vips", sixteen + [{"hsrp_secondary_vip": "192.0.2.99"}])


A = ("198.51.100.254", "198.51.100.254/24")
B = ("203.0.113.254", "203.0.113.254/24")
A25 = ("198.51.100.254", "198.51.100.254/25")


@pytest.mark.parametrize(
    "state,requested,have,expected",
    [
        ("merged", None, [A, B], [A, B]),
        ("merged", [], [A, B], [A, B]),
        ("merged", [A], [A, B], [A, B]),
        ("merged", [A25], [A, B], [A25, B]),
        ("merged", [B, A], [], [B, A]),
        ("replaced", None, [A, B], []),
        ("replaced", [], [A, B], []),
        ("replaced", [A], [A, B], [A]),
        ("overridden", [A], [A, B], [A]),
    ],
    ids=[
        "merged-omitted",
        "merged-empty",
        "merged-subset",
        "merged-prefix-upsert",
        "merged-create",
        "replaced-omitted",
        "replaced-empty",
        "replaced-subset",
        "overridden-subset",
    ],
)
def test_desired_list_follows_the_contract(state, requested, have, expected):
    assert svi_address_list_desired(state, requested, have) == expected


def test_order_alone_is_not_a_difference_but_a_prefix_is():
    assert svi_address_list_same([A, B], [B, A])
    assert not svi_address_list_same([A25, B], [A, B])
