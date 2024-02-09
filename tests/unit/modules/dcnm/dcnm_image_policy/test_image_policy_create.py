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
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.utils import (
    does_not_raise, image_policy_create_fixture, payloads_image_policy_create)


def test_image_policy_create_00010(image_policy_create) -> None:
    """
    Class
    - ImagePolicyCreate
    Function
    - __init__

    Test
    - Class attributes initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = image_policy_create
    assert instance.class_name == "ImagePolicyCreate"
    assert instance.action == "create"
    assert isinstance(instance.endpoints, ApiEndpoints)
    assert instance.path == ApiEndpoints().policy_create["path"]
    assert instance.verb == ApiEndpoints().policy_create["verb"]
    assert instance._mandatory_payload_keys == {
        "nxosVersion",
        "policyName",
        "policyType",
    }
    assert instance.payload is None


def test_image_policy_create_00020(image_policy_create) -> None:
    """
    Class
    - ImagePolicyCreate
    Function
    - payload setter

    Test
    - payload is set to expected value
    - fail_json is not called
    """
    key = "test_image_policy_create_00020a"

    with does_not_raise():
        instance = image_policy_create
        instance.payload = payloads_image_policy_create(key)
    assert instance.payload == payloads_image_policy_create(key)


def test_image_policy_create_00021(image_policy_create) -> None:
    """
    Class
    - ImagePolicyCreate
    Function
    - payload setter

    Test
    - fail_json is called because payload is not a dict
    """
    key = "test_image_policy_create_00021a"
    match = "ImagePolicyCreate._verify_payload: "
    match += "payload must be a dict. Got type list"

    with does_not_raise():
        instance = image_policy_create
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payload = payloads_image_policy_create(key)
    assert instance.payload is None


@pytest.mark.parametrize(
    "key, match",
    [
        ("test_image_policy_create_00022a", "nxosVersion"),
        ("test_image_policy_create_00022b", "policyName"),
        ("test_image_policy_create_00022c", "policyType"),
    ],
)
def test_image_policy_create_00022(image_policy_create, key, match) -> None:
    """
    Class
    - ImagePolicyCreate
    Function
    - payload setter

    Test
    - fail_json is called because payload is missing mandatory key
    """
    match = "ImagePolicyCreate._verify_payload: "
    match += "payload is missing mandatory keys: "
    match += rf".*{match}.*"

    with does_not_raise():
        instance = image_policy_create
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payload = payloads_image_policy_create(key)
    assert instance.payload is None
