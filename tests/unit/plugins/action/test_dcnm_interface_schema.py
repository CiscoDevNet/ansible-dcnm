from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from ansible_collections.cisco.dcnm.plugins.action.tests.plugin_utils.pydantic_schemas.dcnm_interface.schemas import (
    DcnmInterfaceQuerySchema,
)


def get_nvpairs_by_interface_name(data):
    return {
        interface["ifName"]: interface["nvPairs"]
        for policy in data["response"]
        for interface in policy["interfaces"]
    }


def test_copy_description_is_mapped_for_port_channel_and_vpc():
    config = [
        {
            "name": "port-channel511",
            "type": "pc",
            "switch": ["10.122.84.181"],
            "profile": {
                "mode": "access",
                "copy_description": True,
            },
        },
        {
            "name": "vpc513",
            "type": "vpc",
            "switch": ["10.122.84.181", "10.122.84.182"],
            "profile": {
                "mode": "access",
                "copy_description": False,
            },
        },
    ]
    switch_serials = {
        "10.122.84.181": "SERIAL1",
        "10.122.84.182": "SERIAL2",
    }

    expected = DcnmInterfaceQuerySchema.yaml_config_to_dict(
        config,
        "test_fabric",
        switch_serials,
    )
    parsed = DcnmInterfaceQuerySchema.model_validate(expected).model_dump(
        exclude_none=True
    )
    nvpairs = get_nvpairs_by_interface_name(parsed)

    assert nvpairs["port-channel511"]["COPY_DESC"] == "true"
    assert nvpairs["vpc513"]["COPY_DESC"] == "false"


def test_copy_description_is_omitted_when_not_configured():
    config = [
        {
            "name": "port-channel511",
            "type": "pc",
            "switch": ["10.122.84.181"],
            "profile": {
                "mode": "access",
            },
        },
    ]

    expected = DcnmInterfaceQuerySchema.yaml_config_to_dict(
        config,
        "test_fabric",
        {"10.122.84.181": "SERIAL1"},
    )
    parsed = DcnmInterfaceQuerySchema.model_validate(expected).model_dump(
        exclude_none=True
    )
    nvpairs = get_nvpairs_by_interface_name(parsed)

    assert "COPY_DESC" not in nvpairs["port-channel511"]


def test_storm_control_default_action_maps_to_controller_no():
    config = [
        {
            "name": "port-channel511",
            "type": "pc",
            "switch": ["10.122.84.181"],
            "profile": {
                "mode": "access",
                "enable_storm_control": True,
                "storm_control_action": "default",
            },
        },
    ]

    expected = DcnmInterfaceQuerySchema.yaml_config_to_dict(
        config,
        "test_fabric",
        {"10.122.84.181": "SERIAL1"},
    )
    parsed = DcnmInterfaceQuerySchema.model_validate(expected).model_dump(
        exclude_none=True
    )
    nvpairs = get_nvpairs_by_interface_name(parsed)

    assert nvpairs["port-channel511"]["STORM_CONTROL_ACTION"] == "no"


def test_ospf_auth_message_digest_is_mapped_for_fabric_loopback():
    config = [
        {
            "name": "lo0",
            "type": "lo",
            "switch": ["10.122.84.181"],
            "profile": {
                "mode": "fabric",
                "ipv4_addr": "10.2.0.1",
                "enable_ospf_auth_message_digest": True,
            },
        },
        {
            "name": "lo1",
            "type": "lo",
            "switch": ["10.122.84.181"],
            "profile": {
                "mode": "fabric",
                "ipv4_addr": "10.3.0.1",
                "enable_ospf_auth_message_digest": False,
            },
        },
    ]

    expected = DcnmInterfaceQuerySchema.yaml_config_to_dict(
        config,
        "test_fabric",
        {"10.122.84.181": "SERIAL1"},
    )
    parsed = DcnmInterfaceQuerySchema.model_validate(expected).model_dump(
        exclude_none=True
    )
    nvpairs = get_nvpairs_by_interface_name(parsed)

    assert nvpairs["loopback0"]["ENABLE_OSPF_AUTH_MESSAGE_DIGEST"] == "true"
    assert nvpairs["loopback1"]["ENABLE_OSPF_AUTH_MESSAGE_DIGEST"] == "false"


def test_ospf_auth_message_digest_is_omitted_when_not_configured():
    config = [
        {
            "name": "lo0",
            "type": "lo",
            "switch": ["10.122.84.181"],
            "profile": {
                "mode": "fabric",
                "ipv4_addr": "10.2.0.1",
            },
        },
        {
            "name": "lo100",
            "type": "lo",
            "switch": ["10.122.84.181"],
            "profile": {
                "mode": "lo",
                "ipv4_addr": "10.9.0.1",
            },
        },
    ]

    expected = DcnmInterfaceQuerySchema.yaml_config_to_dict(
        config,
        "test_fabric",
        {"10.122.84.181": "SERIAL1"},
    )
    parsed = DcnmInterfaceQuerySchema.model_validate(expected).model_dump(
        exclude_none=True
    )
    nvpairs = get_nvpairs_by_interface_name(parsed)

    assert "ENABLE_OSPF_AUTH_MESSAGE_DIGEST" not in nvpairs["loopback0"]
    # The key must never leak into an ordinary loopback policy.
    assert "ENABLE_OSPF_AUTH_MESSAGE_DIGEST" not in nvpairs["loopback100"]


def _raw_ndfc_query_response(value):
    """Shape a raw NDFC query response carrying one nvPair value."""
    nvpairs = {"INTF_NAME": "loopback0", "IP": "10.2.0.1"}
    if value is not None:
        nvpairs["ENABLE_OSPF_AUTH_MESSAGE_DIGEST"] = value
    return {
        "failed": False,
        "response": [
            {
                "policy": "int_fabric_loopback_11_1",
                "interfaces": [
                    {
                        "ifName": "loopback0",
                        "serialNumber": "SERIAL1",
                        "nvPairs": nvpairs,
                    }
                ],
            }
        ],
    }


@pytest.mark.parametrize(
    "raw_value,expected",
    [
        (True, "true"),            # NDFC returns a native JSON boolean
        (False, "false"),          # native boolean, false
        ("true", "true"),          # NDFC returns the string form
        ("TRUE", "true"),          # mixed case from the controller
        ("false", "false"),
    ],
)
def test_ospf_auth_message_digest_accepts_raw_ndfc_representations(
    raw_value, expected
):
    """
    Raw NDFC query data is parsed through this same model by
    ndfc_interface_validate. A native boolean must be coerced rather than
    rejected as a non-string, otherwise validation fails before any interface
    assertion can run.
    """
    parsed = DcnmInterfaceQuerySchema.model_validate(
        _raw_ndfc_query_response(raw_value)
    ).model_dump(exclude_none=True)
    nvpairs = get_nvpairs_by_interface_name(parsed)

    assert nvpairs["loopback0"]["ENABLE_OSPF_AUTH_MESSAGE_DIGEST"] == expected


def test_ospf_auth_message_digest_absent_in_raw_response_stays_absent():
    parsed = DcnmInterfaceQuerySchema.model_validate(
        _raw_ndfc_query_response(None)
    ).model_dump(exclude_none=True)
    nvpairs = get_nvpairs_by_interface_name(parsed)

    assert "ENABLE_OSPF_AUTH_MESSAGE_DIGEST" not in nvpairs["loopback0"]


def test_flowcontrol_receive_is_mapped_for_access_and_trunk():
    config = [
        {
            "name": "eth1/4",
            "type": "eth",
            "switch": ["10.122.84.181"],
            "profile": {"mode": "access", "flowcontrol_receive": "on"},
        },
        {
            "name": "eth1/5",
            "type": "eth",
            "switch": ["10.122.84.181"],
            "profile": {"mode": "trunk", "flowcontrol_receive": "off"},
        },
    ]
    expected = DcnmInterfaceQuerySchema.yaml_config_to_dict(
        config, "test_fabric", {"10.122.84.181": "SERIAL1"}
    )
    parsed = DcnmInterfaceQuerySchema.model_validate(expected).model_dump(
        exclude_none=True
    )
    nvpairs = get_nvpairs_by_interface_name(parsed)
    assert nvpairs["ethernet1/4"]["FLOWCONTROL_RECEIVE"] == "on"
    assert nvpairs["ethernet1/5"]["FLOWCONTROL_RECEIVE"] == "off"


def test_flowcontrol_receive_is_omitted_when_not_configured():
    config = [{
        "name": "eth1/4",
        "type": "eth",
        "switch": ["10.122.84.181"],
        "profile": {"mode": "access"},
    }]
    expected = DcnmInterfaceQuerySchema.yaml_config_to_dict(
        config, "test_fabric", {"10.122.84.181": "SERIAL1"}
    )
    parsed = DcnmInterfaceQuerySchema.model_validate(expected).model_dump(
        exclude_none=True
    )
    nvpairs = get_nvpairs_by_interface_name(parsed)
    assert "FLOWCONTROL_RECEIVE" not in nvpairs["ethernet1/4"]


@pytest.mark.parametrize("value", ["on", "off"])
def test_flowcontrol_receive_raw_query_preserves_native_string(value):
    raw = {
        "failed": False,
        "response": [{
            "policy": "int_access_host",
            "interfaces": [{
                "ifName": "ethernet1/4",
                "serialNumber": "SERIAL1",
                "nvPairs": {
                    "INTF_NAME": "ethernet1/4",
                    "FLOWCONTROL_RECEIVE": value,
                },
            }],
        }],
    }
    parsed = DcnmInterfaceQuerySchema.model_validate(raw).model_dump(
        exclude_none=True
    )
    actual = get_nvpairs_by_interface_name(parsed)["ethernet1/4"][
        "FLOWCONTROL_RECEIVE"
    ]
    assert actual == value and isinstance(actual, str)
