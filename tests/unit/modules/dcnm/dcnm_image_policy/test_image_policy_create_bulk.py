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
# Also, fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-import redefined-outer-name protected-access unused-argument

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
    does_not_raise, image_policy_create_bulk_fixture,
    payloads_image_policy_create_bulk)


def test_image_policy_create_bulk_00010(image_policy_create_bulk) -> None:
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
        instance = image_policy_create_bulk
    assert instance.class_name == "ImagePolicyCreateBulk"
    assert instance.action == "create"
    assert isinstance(instance.endpoints, ApiEndpoints)
    assert instance.path == ApiEndpoints().policy_create["path"]
    assert instance.verb == ApiEndpoints().policy_create["verb"]
    assert instance._mandatory_payload_keys == {
        "nxosVersion",
        "policyName",
        "policyType",
    }
    assert instance.payloads is None


def test_image_policy_create_bulk_00020(image_policy_create_bulk) -> None:
    """
    Class
    - ImagePolicyCreate
    Function
    - payloads setter

    Test
    - payloads is set to expected value
    - fail_json is not called
    """
    key = "test_image_policy_create_bulk_00020a"

    with does_not_raise():
        instance = image_policy_create_bulk
        instance.payloads = payloads_image_policy_create_bulk(key)
    assert instance.payloads == payloads_image_policy_create_bulk(key)


def test_image_policy_create_bulk_00021(image_policy_create_bulk) -> None:
    """
    Class
    - ImagePolicyCreate
    Function
    - payloads setter

    Test
    - fail_json is called because payloads is not a list of dict
    """
    key = "test_image_policy_create_bulk_00021a"
    match = "ImagePolicyCreateBulk.payloads: "
    match += "payloads must be a list of dict. got dict for value"

    with does_not_raise():
        instance = image_policy_create_bulk
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payloads = payloads_image_policy_create_bulk(key)
    assert instance.payloads is None


@pytest.mark.parametrize(
    "key, match",
    [
        ("test_image_policy_create_bulk_00022a", "nxosVersion"),
        ("test_image_policy_create_bulk_00022b", "policyName"),
        ("test_image_policy_create_bulk_00022c", "policyType"),
    ],
)
def test_image_policy_create_bulk_00022(image_policy_create_bulk, key, match) -> None:
    """
    Class
    - ImagePolicyCreateBulk
    Function
    - payloads setter

    Test
    - fail_json is called because a payload in the payloads list is missing a mandatory key
    """
    with does_not_raise():
        instance = image_policy_create_bulk
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payloads = payloads_image_policy_create_bulk(key)
    assert instance.payloads is None
