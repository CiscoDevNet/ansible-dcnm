# Copyright (c) 2020-2024 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_policies import \
    ImagePolicies

from .fixture import load_fixture

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

"""
controller_version: 12
description: Verify functionality of class ImagePolicies
"""

patch_module_utils = "ansible_collections.cisco.dcnm.plugins.module_utils."
patch_image_mgmt = patch_module_utils + "image_mgmt."

dcnm_send_image_policies = patch_image_mgmt + "image_policies.dcnm_send"


class MockAnsibleModule:
    """
    Mock the AnsibleModule class
    """

    params = {}

    def fail_json(msg) -> AnsibleFailJson:
        """
        mock the fail_json method
        """
        raise AnsibleFailJson(msg)


def responses_image_policies(key: str) -> Dict[str, str]:
    response_file = f"image_upgrade_responses_ImagePolicies"
    response = load_fixture(response_file).get(key)
    print(f"responses_image_policies: {key} : {response}")
    return response


@pytest.fixture
def image_policies():
    return ImagePolicies(MockAnsibleModule)


def test_image_mgmt_image_policies_00001(image_policies) -> None:
    """
    Function
    - __init__

    Test
    - Class attributes are initialized to expected values
    """
    image_policies.__init__(MockAnsibleModule)
    assert image_policies.module == MockAnsibleModule
    assert image_policies.class_name == "ImagePolicies"
    assert isinstance(image_policies.endpoints, ApiEndpoints)


def test_image_mgmt_image_policies_00002(image_policies) -> None:
    """
    Function
    - _init_properties

    Test
    - Class properties are initialized to expected values
    """
    image_policies._init_properties()
    assert isinstance(image_policies.properties, dict)
    assert image_policies.properties.get("policy_name") == None
    assert image_policies.properties.get("response_data") == None
    assert image_policies.properties.get("response") == None
    assert image_policies.properties.get("result") == None


def test_image_mgmt_image_policies_00010(monkeypatch, image_policies) -> None:
    """
    Function
    - refresh

    Test
    - properties are initialized to expected values
    - 200 RETURN_CODE

    Endpoint
    - /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies
    """
    key = "test_image_mgmt_image_policies_00010a"

    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        return responses_image_policies(key)

    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)

    image_policies.refresh()
    image_policies.policy_name = "KR5M"
    assert isinstance(image_policies.response, dict)
    assert image_policies.agnostic is False
    assert image_policies.description == "10.2.(5) with EPLD"
    assert image_policies.epld_image_name == "n9000-epld.10.2.5.M.img"
    assert image_policies.image_name == "nxos64-cs.10.2.5.M.bin"
    assert image_policies.nxos_version == "10.2.5_nxos64-cs_64bit"
    assert image_policies.package_name == None
    assert image_policies.platform == "N9K/N3K"
    assert image_policies.platform_policies == None
    assert image_policies.policy_name == "KR5M"
    assert image_policies.policy_type == "PLATFORM"
    assert image_policies.ref_count == 10
    assert image_policies.rpm_images == None


def test_image_mgmt_image_policies_00020(monkeypatch, image_policies) -> None:
    """
    Function
    - refresh

    Test
    - result contains expected key/values on 200 response from endpoint.

    Endpoint
    - /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies
    """
    key = "test_image_mgmt_image_policies_00020a"

    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)

    image_policies.refresh()
    assert isinstance(image_policies.result, dict)
    assert image_policies.result.get("found") is True
    assert image_policies.result.get("success") is True


def test_image_mgmt_image_policies_00021(monkeypatch, image_policies) -> None:
    """
    Function
    - refresh

    Test
    - fail_json is called on 404 RETURN_CODE in response.

    Endpoint
    - /bad/path
    """
    key = "test_image_mgmt_image_policies_00021a"

    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)

    match = "ImagePolicies.refresh: Bad response when retrieving "
    match += "image policy information from the controller."
    with pytest.raises(AnsibleFailJson, match=match):
        image_policies.refresh()


def test_image_mgmt_image_policies_00022(monkeypatch, image_policies) -> None:
    """
    Function
    - refresh

    Test
    - fail_json is called on 200 RETURN_CODE with empty DATA key.

    Endpoint
    - /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies
    """
    key = "test_image_mgmt_image_policies_00022a"

    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)

    match = "ImagePolicies.refresh: Bad response when retrieving "
    match += "image policy information from the controller."
    with pytest.raises(AnsibleFailJson, match=match):
        image_policies.refresh()


def test_image_mgmt_image_policies_00023(monkeypatch, image_policies) -> None:
    """
    Function
    - refresh

    Test
    - fail_json is called when DATA.lastOperDataObject length == 0
    - 200 response

    Endpoint
    - /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies
    """
    key = "test_image_mgmt_image_policies_00023a"

    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)

    match = "ImagePolicies.refresh: "
    match += "the controller has no defined image policies."
    with pytest.raises(AnsibleFailJson, match=match):
        image_policies.refresh()


def test_image_mgmt_image_policies_00024(monkeypatch, image_policies) -> None:
    """
    Function
    - refresh

    Test
    - fail_json() is called if response does not contain policy_name.
    - i.e. image policy with name FOO has not yet been created on NDFC.

    Endpoint
    - /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies
    """
    key = "test_image_mgmt_image_policies_00024a"

    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)

    image_policies.refresh()
    image_policies.policy_name = "FOO"

    match = "ImagePolicies._get: "
    match += "policy_name FOO is not defined on the controller."
    with pytest.raises(AnsibleFailJson, match=match):
        image_policies.policy_type == "PLATFORM"


def test_image_mgmt_image_policies_00025(monkeypatch, image_policies) -> None:
    """
    Function
    - refresh

    Test
    - fail_json is called on response with missing policyName key.
    - 200 RETURN_CODE

    Endpoint
    - /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies

    NOTES
    - This is to cover a check in ImagePolicies.refresh()
    - This scenario should never happen.

    TODO
    - Consider removing this check, and this testcase.
    """
    key = "test_image_mgmt_image_policies_00025a"

    def mock_dcnm_send_image_policies(*args, **kwargs) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(dcnm_send_image_policies, mock_dcnm_send_image_policies)

    match = "ImagePolicies.refresh: "
    match += "Cannot parse policy information from the controller."
    with pytest.raises(AnsibleFailJson, match=match):
        image_policies.refresh()


def test_image_mgmt_image_policies_00040(image_policies) -> None:
    """
    Function
    - _get

    Test
    - fail_json is called when _get() is called prior to setting policy_name.
    """
    match = "ImagePolicies._get: instance.policy_name must be "
    match += "set before accessing property imageName."
    with pytest.raises(AnsibleFailJson, match=match):
        image_policies._get("imageName")
