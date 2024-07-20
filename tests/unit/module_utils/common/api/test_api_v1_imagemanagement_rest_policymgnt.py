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

from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.imagemanagement.rest.policymgnt.policymgnt import (
    EpPolicies, EpPoliciesAllAttached, EpPolicyAttach, EpPolicyCreate,
    EpPolicyDetach, EpPolicyInfo)
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    does_not_raise

PATH_PREFIX = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/policymgnt"


def test_ep_policy_mgnt_00010():
    """
    ### Class
    -   EpPolicies

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpPolicies()
    assert instance.path == f"{PATH_PREFIX}/policies"
    assert instance.verb == "GET"


def test_ep_policy_mgnt_00020():
    """
    ### Class
    -   EpPolicyInfo

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpPolicyInfo()
        instance.policy_name = "MyPolicy"
    assert instance.path == f"{PATH_PREFIX}/image-policy/MyPolicy"
    assert instance.verb == "GET"


def test_ep_policy_mgnt_00021():
    """
    ### Class
    -   EpPolicyInfo

    ### Summary
    -   Verify ``ValueError`` is raised if path is accessed before
        setting policy_name.
    """
    with does_not_raise():
        instance = EpPolicyInfo()
    match = r"EpPolicyInfo\.path:\s+"
    match += r"EpPolicyInfo\.policy_name must be set before accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_policy_mgnt_00030():
    """
    ### Class
    -   EpPoliciesAllAttached

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpPoliciesAllAttached()
    assert instance.path == f"{PATH_PREFIX}/all-attached-policies"
    assert instance.verb == "GET"


def test_ep_policy_mgnt_00040():
    """
    ### Class
    -   EpPolicyAttach

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpPolicyAttach()
    assert instance.path == f"{PATH_PREFIX}/attach-policy"
    assert instance.verb == "POST"


def test_ep_policy_mgnt_00050():
    """
    ### Class
    -   EpPolicyDetach

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpPolicyDetach()
        instance.serial_numbers = ["AB12345CD"]
    assert instance.path == f"{PATH_PREFIX}/detach-policy?serialNumber=AB12345CD"
    assert instance.verb == "DELETE"


def test_ep_policy_mgnt_00060():
    """
    ### Class
    -   EpPolicyCreate

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpPolicyCreate()
    assert instance.path == f"{PATH_PREFIX}/platform-policy"
    assert instance.verb == "POST"
