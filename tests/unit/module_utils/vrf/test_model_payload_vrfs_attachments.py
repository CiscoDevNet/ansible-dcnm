# -*- coding: utf-8 -*-
# test_payload_vrfs_attachments.py
"""
Unit tests for the PayloadVrfsAttachments model.
"""
import pytest

from .....plugins.module_utils.vrf.model_payload_vrfs_attachments import PayloadVrfsAttachments


def valid_payload_data() -> dict:
    """
    Returns a payload that should pass validation.
    """
    return {
        "lanAttachList": [
            {
                "extensionValues": "",
                "fabricName": "f1",
                "freeformConfig": "",
                "instanceValues": "",
                "ipAddress": "10.1.1.1",
                "isLanAttached": True,
                "lanAttachState": "DEPLOYED",
                "switchName": "cvd-1211-spine",
                "switchRole": "border spine",
                "switchSerialNo": "ABC1234DEFG",
                "vlanId": 500,
                "vrfId": 9008011,
                "vrfName": "ansible-vrf-int1",
            }
        ],
        "vrfName": "ansible-vrf-int1",
    }


def invalid_payload_data() -> dict:
    """
    Returns a payload that should fail validation.
    """
    invalid_payload = valid_payload_data()
    # Remove the vrfName field from the lan_attach_list item to trigger validation error
    invalid_payload["lanAttachList"][0].pop("vrfName", None)
    return invalid_payload


@pytest.mark.parametrize("valid, payload", [(True, valid_payload_data()), (False, invalid_payload_data())])
def test_payload_vrfs_attachments(valid, payload):
    """
    Test the PayloadVrfsAttachments model with both valid and invalid payloads.
    """
    if valid:
        payload = PayloadVrfsAttachments(**payload)
        assert payload.vrf_name == "ansible-vrf-int1"
        assert len(payload.lan_attach_list) == 1
        assert payload.lan_attach_list[0].ip_address == "10.1.1.1"
    else:
        with pytest.raises(ValueError):
            PayloadVrfsAttachments(**payload)
