# Copyright (c) 2024 Cisco and/or its affiliates.
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

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# pylint: disable=unused-import
# Some fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-argument

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.image_upgrade.api_endpoints import \
    ApiEndpoints

from .image_upgrade_utils import (MockAnsibleModule, does_not_raise,
                                  image_policies_fixture,
                                  responses_image_policies)

PATCH_MODULE_UTILS = "ansible_collections.cisco.dcnm.plugins.module_utils."
PATCH_IMAGE_UPGRADE = PATCH_MODULE_UTILS + "image_upgrade."
DCNM_SEND_IMAGE_POLICIES = PATCH_IMAGE_UPGRADE + "image_policies.dcnm_send"


def test_image_upgrade_image_policies_00001(image_policies) -> None:
    """
    Function
    - ImagePolicies.__init__

    Test
    - Class attributes are initialized to expected values
    """
    with does_not_raise():
        instance = image_policies
    assert instance.module == MockAnsibleModule
    assert instance.class_name == "ImagePolicies"
    assert isinstance(instance.endpoints, ApiEndpoints)


def test_image_upgrade_image_policies_00002(image_policies) -> None:
    """
    Function
    - ImagePolicies._init_properties

    Test
    - Class properties are initialized to expected values
    """
    with does_not_raise():
        instance = image_policies
    assert isinstance(image_policies.properties, dict)
    assert instance.properties.get("policy_name") is None
    assert instance.properties.get("response_data") == {}
    assert instance.properties.get("response") is None
    assert instance.properties.get("result") is None


def test_image_upgrade_image_policies_00010(monkeypatch, image_policies) -> None:
    """
    Function
    - ImagePolicies.refresh
    - ImagePolicies.policy_name


    Summary
    Verify that refresh returns image policy info and that the filtered
    properties associated with policy_name are the expected values.

    Test
    -   properties for policy_name are set to reflect the response from
        the controller
    -   200 RETURN_CODE
    -   fail_json is not called

    Endpoint
    - /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies
    """
    key = "test_image_upgrade_image_policies_00010a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        return responses_image_policies(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    instance = image_policies
    with does_not_raise():
        instance.refresh()
    instance.policy_name = "KR5M"
    assert isinstance(instance.response, dict)
    assert instance.agnostic is False
    assert instance.description == "10.2.(5) with EPLD"
    assert instance.epld_image_name == "n9000-epld.10.2.5.M.img"
    assert instance.image_name == "nxos64-cs.10.2.5.M.bin"
    assert instance.nxos_version == "10.2.5_nxos64-cs_64bit"
    assert instance.package_name is None
    assert instance.platform == "N9K/N3K"
    assert instance.platform_policies is None
    assert instance.policy_name == "KR5M"
    assert instance.policy_type == "PLATFORM"
    assert instance.ref_count == 10
    assert instance.rpm_images is None


def test_image_upgrade_image_policies_00020(monkeypatch, image_policies) -> None:
    """
    Function
    - ImagePolicies.refresh
    - ImagePolicies.result

    Test
    - Imagepolicies.result contains expected key/values on 200 response from endpoint.

    Endpoint
    - /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies
    """
    key = "test_image_upgrade_image_policies_00020a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    instance = image_policies
    with does_not_raise():
        instance.refresh()
    assert isinstance(instance.result, dict)
    assert instance.result.get("found") is True
    assert instance.result.get("success") is True


def test_image_upgrade_image_policies_00021(monkeypatch, image_policies) -> None:
    """
    Function
    - ImagePolicies.refresh

    Summary
    Verify that fail_json is called when the response from the controller
    contains a 404 RETURN_CODE.

    Test
    - fail_json is called on 404 RETURN_CODE in response.

    Endpoint
    - /bad/path
    """
    key = "test_image_upgrade_image_policies_00021a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    match = "ImagePolicies.refresh: Bad response when retrieving "
    match += "image policy information from the controller."

    instance = image_policies
    with pytest.raises(AnsibleFailJson, match=match):
        instance.refresh()


def test_image_upgrade_image_policies_00022(monkeypatch, image_policies) -> None:
    """
    Function
    - ImagePolicies.refresh

    Summary
    Verify that fail_json is called when the response from the controller
    contains an empty DATA key.

    Test
    - fail_json is called on 200 RETURN_CODE with empty DATA key.

    Endpoint
    - /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies
    """
    key = "test_image_upgrade_image_policies_00022a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    match = "ImagePolicies.refresh: Bad response when retrieving "
    match += "image policy information from the controller."

    instance = image_policies
    with pytest.raises(AnsibleFailJson, match=match):
        instance.refresh()


def test_image_upgrade_image_policies_00023(monkeypatch, image_policies) -> None:
    """
    Function
    - ImagePolicies.refresh

    Summary
    Verify that fail_json is not called when a 200 response from the controller
    contains DATA.lastOperDataObject with length == 0.

    Test
    - do not fail_json when DATA.lastOperDataObject length == 0
    - 200 response

    Endpoint
    - /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies

    Discussion
    dcnm_image_policy classes ImagePolicyCreate and ImagePolicyCreateBulk
    both call ImagePolicies.refresh() when checking if the image policies
    they are creating already exist on the controller.  Hence, we cannot
    fail_json when the length of DATA.lastOperDataObject is zero.
    """
    key = "test_image_upgrade_image_policies_00023a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    instance = image_policies
    with does_not_raise():
        instance.refresh()


def test_image_upgrade_image_policies_00024(monkeypatch, image_policies) -> None:
    """
    Function
    - ImagePolicies.refresh
    - ImagePolicies.policy_name

    Summary
    Verify when policy_name is set to a policy that does not exist on the
    controller, instance.policy returns None.

    Setup
    - instance.policy_name is set to a policy that does not exist on the controller.

    Test
    - instance.policy returns None

    Endpoint
    - /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies
    """
    key = "test_image_upgrade_image_policies_00024a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    with does_not_raise():
        instance = image_policies
        instance.refresh()
        image_policies.policy_name = "FOO"

    assert image_policies.policy is None


def test_image_upgrade_image_policies_00025(monkeypatch, image_policies) -> None:
    """
    Function
    - ImagePolicies.refresh

    Summary
    Verify that fail_json is called when the response from the controller
    is missing the policyName key.

    Test
    - fail_json is called on response with missing policyName key.

    Endpoint
    - /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt/policies

    NOTES
    - This is to cover a check in ImagePolicies.refresh()
    - This scenario should happen only with a bug, or API change, on the controller.
    """
    key = "test_image_upgrade_image_policies_00025a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    match = "ImagePolicies.refresh: "
    match += "Cannot parse policy information from the controller."

    instance = image_policies
    with pytest.raises(AnsibleFailJson, match=match):
        instance.refresh()


def test_image_upgrade_image_policies_00026(monkeypatch, image_policies) -> None:
    """
    Function
    - ImagePolicies.refresh
    - ImageUpgradeCommon._handle_response

    Summary
    Verify that fail_json is called when ImageUpgradeCommon._handle_response()
    returns a non-successful result.

    Test
    - fail_json is called when result["success"] is False.

    """
    key = "test_image_upgrade_image_policies_00026a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    match = "ImagePolicies.refresh: Bad result when retrieving image policy "
    match += r"information from the controller\."

    instance = image_policies
    with pytest.raises(AnsibleFailJson, match=match):
        instance.refresh()


def test_image_upgrade_image_policies_00040(image_policies) -> None:
    """
    Function
    - ImagePolicies._get

    Summary
    Verify that fail_json is called when _get() is called prior to setting policy_name.

    Test
    - fail_json is called when _get() is called prior to setting policy_name.
    - Appropriate error message is provided.
    """
    match = "ImagePolicies._get: instance.policy_name must be "
    match += "set before accessing property imageName."

    instance = image_policies
    with pytest.raises(AnsibleFailJson, match=match):
        instance._get("imageName")  # pylint: disable=protected-access


def test_image_upgrade_image_policies_00041(monkeypatch, image_policies) -> None:
    """
    Function
    - ImagePolicies._get

    Summary
    Verify that fail_json is called when ImagePolicies._get is called
    with an argument that does not match an item in the response data
    for the policy_name returned by the controller.

    Setup
    -   instance.commit() is called and retrieves a response from the
        controller containing informationi for policy KR5M.
    - policy_name is set to KR5M.

    Test
    - fail_json is called when _get() is called with a bad parameter FOO
    - An appropriate error message is provided.
    """
    key = "test_image_upgrade_image_policies_00041a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    match = r"ImagePolicies\._get: KR5M does not have a key named FOO\."

    with does_not_raise():
        instance = image_policies
        instance.refresh()
        instance.policy_name = "KR5M"

    with pytest.raises(AnsibleFailJson, match=match):
        instance._get("FOO")  # pylint: disable=protected-access


def test_image_upgrade_image_policies_00042(monkeypatch, image_policies) -> None:
    """
    Function
    - ImagePolicies._get

    Summary
    Verify that the correct image policy information is returned when
    ImagePolicies._get is called with the "policy" arguement.

    Setup
    -   instance.commit() is called and retrieves a response from the
        controller containing informationi for policy KR5M.
    - policy_name is set to KR5M.
    - _get("policy") is called.

    Test
    - fail_json is not called
    - The expected policy information is returned.
    """
    key = "test_image_upgrade_image_policies_00042a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    with does_not_raise():
        instance = image_policies
        instance.refresh()
        instance.policy_name = "KR5M"
        value = instance._get("policy")  # pylint: disable=protected-access
    assert value["agnostic"] == "false"
    assert value["epldImgName"] == "n9000-epld.10.2.5.M.img"
    assert value["imageName"] == "nxos64-cs.10.2.5.M.bin"
    assert value["nxosVersion"] == "10.2.5_nxos64-cs_64bit"
    assert value["packageName"] == ""
    assert value["platform"] == "N9K/N3K"
    assert value["platformPolicies"] == ""
    assert value["policyDescr"] == "10.2.(5) with EPLD"
    assert value["policyName"] == "KR5M"
    assert value["policyType"] == "PLATFORM"
    assert value["ref_count"] == 10
    assert value["rpmimages"] == ""


def test_image_upgrade_image_policies_00050(image_policies) -> None:
    """
    Function
    - ImagePolicies.all_policies

    Summary
    Verify that all_policies returns an empty dict when no policies exist
    on the controller.

    Test
    - fail_json is not called.
    - all_policies returns an empty dict.
    """
    with does_not_raise():
        instance = image_policies
        value = instance.all_policies
    assert value == {}


def test_image_upgrade_image_policies_00051(monkeypatch, image_policies) -> None:
    """
    Function
    - ImagePolicies.all_policies

    Summary
    Verify that, when policies exist on the controller, all_policies returns a dict
    containing these policies.

    Test
    - fail_json is not called.
    - all_policies returns a dict containing the controller's policies.
    """
    key = "test_image_upgrade_image_policies_00051a"

    def mock_dcnm_send_image_policies(*args) -> Dict[str, Any]:
        print(f"mock_dcnm_send_image_policies: {responses_image_policies(key)}")
        return responses_image_policies(key)

    monkeypatch.setattr(DCNM_SEND_IMAGE_POLICIES, mock_dcnm_send_image_policies)

    instance = image_policies
    with does_not_raise():
        instance.refresh()
        value = instance.all_policies
    assert value["KR5M"]["agnostic"] == "false"
    assert value["KR5M"]["epldImgName"] == "n9000-epld.10.2.5.M.img"
    assert value["KR5M"]["imageName"] == "nxos64-cs.10.2.5.M.bin"
    assert value["KR5M"]["nxosVersion"] == "10.2.5_nxos64-cs_64bit"
    assert value["KR5M"]["packageName"] == ""
    assert value["KR5M"]["platform"] == "N9K/N3K"
    assert value["KR5M"]["platformPolicies"] == ""
    assert value["KR5M"]["policyDescr"] == "10.2.(5) with EPLD"
    assert value["KR5M"]["policyName"] == "KR5M"
    assert value["KR5M"]["policyType"] == "PLATFORM"
    assert value["KR5M"]["ref_count"] == 10
    assert value["KR5M"]["rpmimages"] == ""
    assert value["OR1F"]["agnostic"] == "false"
    assert value["OR1F"]["epldImgName"] == "n9000-epld.10.4.1.F.img"
    assert value["OR1F"]["imageName"] == "nxos64-cs.10.4.1.F.bin"
    assert value["OR1F"]["nxosVersion"] == "10.4.1_nxos64-cs_64bit"
    assert value["OR1F"]["packageName"] == ""
    assert value["OR1F"]["platform"] == "N9K/N3K"
    assert value["OR1F"]["platformPolicies"] == ""
    assert value["OR1F"]["policyDescr"] == "OR1F EPLD"
    assert value["OR1F"]["policyName"] == "OR1F"
    assert value["OR1F"]["policyType"] == "PLATFORM"
    assert value["OR1F"]["ref_count"] == 0
    assert value["OR1F"]["rpmimages"] == ""
