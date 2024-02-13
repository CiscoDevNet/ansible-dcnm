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
# pylint: disable=unused-import
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=unused-argument
# pylint: disable=invalid-name
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
    does_not_raise, image_policies_all_policies,
    image_policy_create_bulk_fixture, payloads_image_policy_create_bulk,
    responses_image_policy_create_bulk)


def test_image_policy_create_bulk_00010(image_policy_create_bulk) -> None:
    """
    Method
    - ImagePolicyCreateBulk()__init__()

    Test
    - Class attributes are initialized to expected values
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
    Method
    - ImagePolicyCreateBulk().payloads setter

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
    Method
    - ImagePolicyCreateBulk().payloads setter

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
    Method
    - ImagePolicyCreateBulk().payloads setter

    Test
    - fail_json is called because a payload in the payloads list is missing a mandatory key
    """
    with does_not_raise():
        instance = image_policy_create_bulk
    with pytest.raises(AnsibleFailJson, match=match):
        instance.payloads = payloads_image_policy_create_bulk(key)
    assert instance.payloads is None


def test_image_policy_create_bulk_00030(monkeypatch, image_policy_create_bulk) -> None:
    """
    Function
    - ImagePolicyCreateBulk()._build_payloads_to_commit()

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two image policies (KR5M, NR3F) exist on the
        controller.
    -   ImagePolicyCreateBulk().payloads is set to contain one payload (KR5M)
        that is present in all_policies.

    Test
    -   payloads_to_commit will an empty list because all payloads in
        instance.payloads exist on the controller.
    """
    key = "test_image_policy_create_bulk_00030a"

    class MockImagePolicies:
        """
        Mock the ImagePolicies class to return various values for all_policies
        """
        def refresh(self) -> None:
            """
            bypass dcnm_send
            """

        @property
        def all_policies(self, *args):
            """
            Mock the return value of all_policies
            all_policies contains all image policies that exist on the controller
            """
            return image_policies_all_policies(key)

    instance = image_policy_create_bulk
    instance.payloads = payloads_image_policy_create_bulk(key)
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies())
    instance._build_payloads_to_commit()
    assert instance._payloads_to_commit == []


def test_image_policy_create_bulk_00031(monkeypatch, image_policy_create_bulk) -> None:
    """
    Function
    - ImagePolicyCreateBulk()._build_payloads_to_commit()

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two image policies (KR5M, NR3F) exist on the
        controller.
    -   ImagePolicyCreateBulk().payloads is set to contain one payload containing
        an image policy (FOO) that is not present in all_policies.

    Test
    -   _payloads_to_commit will equal instance.payloads since none of the
        image policies in instance.payloads exist on the controller.
    """
    key = "test_image_policy_create_bulk_00031a"

    class MockImagePolicies:
        """
        Mock the ImagePolicies class to return various values for all_policies
        """
        def refresh(self) -> None:
            """
            bypass dcnm_send
            """

        @property
        def all_policies(self, *args):
            """
            Mock the return value of all_policies
            all_policies contains all image policies that exist on the controller
            """
            return image_policies_all_policies(key)

    instance = image_policy_create_bulk
    instance.payloads = payloads_image_policy_create_bulk(key)
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies())
    instance._build_payloads_to_commit()
    assert instance._payloads_to_commit == payloads_image_policy_create_bulk(key)


def test_image_policy_create_bulk_00032(monkeypatch, image_policy_create_bulk) -> None:
    """
    Function
    - ImagePolicyCreateBulk()._build_payloads_to_commit()

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that two image policies (KR5M, NR3F) exist on the
        controller.
    -   ImagePolicyCreateBulk().payloads is set to contain one payload containing
        an image policy (FOO) that is not present in all_policies and one payload
        containing an image policy (KR5M) that does exist on the controller.

    Test
    -   _payloads_to_commit will contain one payload
    -   The policyName for this payload will be "FOO", which is the image policy that
        does not exist on the controller
    """
    key = "test_image_policy_create_bulk_00032a"

    class MockImagePolicies:
        """
        Mock the ImagePolicies class to return various values for all_policies
        """
        def refresh(self) -> None:
            """
            bypass dcnm_send
            """

        @property
        def all_policies(self, *args):
            """
            Mock the return value of all_policies
            all_policies contains all image policies that exist on the controller
            """
            return image_policies_all_policies(key)

    instance = image_policy_create_bulk
    instance.payloads = payloads_image_policy_create_bulk(key)
    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies())
    instance._build_payloads_to_commit()
    assert len(instance._payloads_to_commit) == 1
    assert instance._payloads_to_commit[0]["policyName"] == "FOO"


def test_image_policy_create_bulk_00033(image_policy_create_bulk) -> None:
    """
    Function
    - ImagePolicyCreateBulk().commit()

    Setup
    -   ImagePolicyCreateBulk().payloads is not set

    Test
    -   fail_json is called because payloads is None
    """
    with does_not_raise():
        instance = image_policy_create_bulk

    match = (
        "ImagePolicyCreateBulk.commit: payloads must be set prior to calling commit."
    )
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


def test_image_policy_create_bulk_00034(monkeypatch, image_policy_create_bulk) -> None:
    """
    Function
    - ImagePolicyCreateBulk().commit()

    Setup
    -   ImagePolicyCreateBulk().payloads is set to an empty list

    Test
    -   commit returns without doing anything
    """
    key = "test_image_policy_create_bulk_00034a"

    class MockImagePolicies:
        """
        Mock the ImagePolicies class to return various values for all_policies
        """
        def refresh(self) -> None:
            """
            bypass dcnm_send
            """

        @property
        def all_policies(self, *args):
            """
            Mock the return value of all_policies
            all_policies contains all image policies that exist on the controller
            """
            return image_policies_all_policies(key)

    with does_not_raise():
        instance = image_policy_create_bulk
        instance.payloads = []

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies())

    with does_not_raise():
        instance.commit()


def test_image_policy_create_bulk_00035(monkeypatch, image_policy_create_bulk) -> None:
    """
    Function
    - ImagePolicyCreateBulk().commit()

    Setup
    -   ImagePolicies().all_policies, called from instance._build_payloads_to_commit(),
        is mocked to indicate that no policies exist on the controller.
    -   ImagePolicyCreateBulk().payloads is set to contain one payload that
        contains an image policy (FOO) which does not exist on the controller.
    -   dcnm_send is mocked to return a successful (200) response.

    Test
    -   commit calls _build_payloads_to_commit which returns one payload
    -   commit calls _send_payloads, which populates response_ok, result_ok,
        diff_ok, response_nok, result_nok, and diff_nok based on the payload
        returned from _build_payloads_to_commit
    -  response_ok, result_ok, and diff_ok are set to the expected values
    -  response_nok, result_nok, and diff_nok are set to empty lists
    """
    key = "test_image_policy_create_bulk_00035a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.image_policy.create.dcnm_send"

    class MockImagePolicies:
        """
        Mock the ImagePolicies class to return various values for all_policies
        """
        def refresh(self) -> None:
            """
            bypass dcnm_send
            """

        @property
        def all_policies(self, *args):
            """
            Mock the return value of all_policies
            all_policies contains all image policies that exist on the controller
            """
            return image_policies_all_policies(key)

    def mock_dcnm_send(*args, **kwargs):
        return responses_image_policy_create_bulk(key)

    with does_not_raise():
        instance = image_policy_create_bulk
        instance.payloads = payloads_image_policy_create_bulk(key)

    monkeypatch.setattr(instance, "_image_policies", MockImagePolicies())
    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.payloads = payloads_image_policy_create_bulk(key)
        instance.commit()

    assert instance.response_current == responses_image_policy_create_bulk(key)
    assert instance.response_ok[0]["RETURN_CODE"] == 200
    assert instance.result_ok[0]["changed"] is True
    assert instance.result_ok[0]["success"] is True
    assert instance.diff_ok[0]["agnostic"] is False
    assert instance.diff_ok[0]["policyName"] == "FOO"
    assert instance.response_nok == []
    assert instance.result_nok == []
    assert instance.diff_nok == []
