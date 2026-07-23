from __future__ import absolute_import, division, print_function

__metaclass__ = type

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
