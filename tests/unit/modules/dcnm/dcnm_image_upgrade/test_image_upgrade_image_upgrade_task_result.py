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
# Some tests require calling protected methods
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from typing import Any, Dict

import pytest
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upgrade import \
    ImageUpgradeTaskResult
from .image_upgrade_utils import (does_not_raise, image_upgrade_task_result_fixture)


def test_image_upgrade_upgrade_task_result_00010(image_upgrade_task_result) -> None:
    """
    Function
    - ImageUpgradeTaskResult.__init__
    - ImageUpgradeTaskResult._build_properties

    Test
    - Class attributes and properties are initialized to expected values
    """
    instance = image_upgrade_task_result
    assert isinstance(instance, ImageUpgradeTaskResult)
    assert instance.class_name == "ImageUpgradeTaskResult"
    assert isinstance(instance.diff_properties, dict)
    assert instance.diff_attach_policy == []
    assert instance.diff_detach_policy == []
    assert instance.diff_issu_status == []
    assert instance.diff_stage == []
    assert instance.diff_upgrade == []
    assert instance.diff_validate == []
    assert isinstance(instance.response_properties, dict)
    assert instance.response_attach_policy == []
    assert instance.response_detach_policy == []
    assert instance.response_issu_status == []
    assert instance.response_stage == []
    assert instance.response_upgrade == []
    assert instance.response_validate == []
    assert isinstance(instance.properties, dict)


@pytest.mark.parametrize(
    "state, return_value",
    [
        ("no_change", False),
        ("attach_policy", True),
        ("detach_policy", True),
        ("issu_status", False),
        ("stage", True),
        ("upgrade", True),
        ("validate", True),
    ],
)
def test_image_upgrade_upgrade_task_result_00020(
    image_upgrade_task_result, state, return_value
) -> None:
    """
    Function
    - ImageUpgradeTaskResult.__init__
    - ImageUpgradeTaskResult.did_anything_change

    Summary
    Verify that did_anything_change:
    -   returns False when no changes have been made
    -   returns True when changes have been made to attach_policy,
        detach_policy, stage, upgrade, or validate
    -   returns False when changes have been made to issu_status
    """
    diff = {"diff": "diff"}
    with does_not_raise():
        instance = image_upgrade_task_result
    if state == "attach_policy":
        instance.diff_attach_policy = diff
    elif state == "detach_policy":
        instance.diff_detach_policy = diff
    elif state == "issu_status":
        instance.diff_issu_status = diff
    elif state == "stage":
        instance.diff_stage = diff
    elif state == "upgrade":
        instance.diff_upgrade = diff
    elif state == "validate":
        instance.diff_validate = diff
    elif state == "no_change":
        pass
    assert instance.did_anything_change() == return_value


MATCH_00030 = r"ImageUpgradeTaskResult\._verify_is_dict: value must be a dict\."


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ("not a dict", pytest.raises(AnsibleFailJson, match=MATCH_00030)),
    ],
)
def test_image_upgrade_upgrade_task_result_00030(
    image_upgrade_task_result, value, expected
) -> None:
    """
    Function
    - ImageUpgradeTaskResult._verify_is_dict

    Summary
    Verify that _verify_is_dict does not call fail_json when value is a dict
    and does call fail_json value is not a dict.
    """
    with does_not_raise():
        instance = image_upgrade_task_result
    with expected:
        instance._verify_is_dict(value)


def test_image_upgrade_upgrade_task_result_00040(image_upgrade_task_result) -> None:
    """
    Function
    - ImageUpgradeTaskResult.failed_result

    Summary
    Verify that failed_result returns a dict with expected values
    """
    test_diff_keys = [
        "diff_attach_policy",
        "diff_detach_policy",
        "diff_issu_status",
        "diff_stage",
        "diff_upgrade",
        "diff_validate",
    ]
    test_response_keys = [
        "response_attach_policy",
        "response_detach_policy",
        "response_issu_status",
        "response_stage",
        "response_upgrade",
        "response_validate",
    ]
    with does_not_raise():
        instance = image_upgrade_task_result
        result = instance.failed_result
    assert isinstance(result, dict)
    assert result["changed"] == False
    assert result["failed"] == True
    for key in test_diff_keys:
        assert result["diff"][key] == []
    for key in test_response_keys:
        assert result["response"][key] == []


def test_image_upgrade_upgrade_task_result_00050(image_upgrade_task_result) -> None:
    """
    Function
    - ImageUpgradeTaskResult.module_result

    Summary
    Verify that module_result returns a dict with expected values when
    no changes have been made.
    """
    test_keys = [
        "attach_policy",
        "detach_policy",
        "issu_status",
        "stage",
        "upgrade",
        "validate",
    ]
    with does_not_raise():
        instance = image_upgrade_task_result
        result = instance.module_result
    assert isinstance(result, dict)
    assert result["changed"] == False
    for key in test_keys:
        assert result["diff"][key] == []
    for key in test_keys:
        assert result["response"][key] == []


@pytest.mark.parametrize(
    "state, changed",
    [
        ("attach_policy", True),
        ("detach_policy", True),
        ("issu_status", False),
        ("stage", True),
        ("upgrade", True),
        ("validate", True),
    ],
)
def test_image_upgrade_upgrade_task_result_00051(
    image_upgrade_task_result, state, changed
) -> None:
    """
    Function
    - ImageUpgradeTaskResult.module_result
    - ImageUpgradeTaskResult.did_anything_change
    - ImageUpgradeTaskResult.diff_*
    - ImageUpgradeTaskResult.response_*

    Summary
    Verify that module_result returns a dict with expected values when
    changes have been made to each of the supported states.

    Test
    -   For non-query-state properties, "changed" should be True
    -   The diff should be a list containing the dict passed to
        the state's diff property (e.g. diff_stage, diff_issu_status, etc)
    -   The response should be a list containing the dict passed to
        the state's response property (e.g. response_stage, response_issu_status, etc)
    -   All other diffs should be empty lists
    -   All other responses should be empty lists
    """
    test_key = state
    test_keys = [
        "attach_policy",
        "detach_policy",
        "issu_status",
        "stage",
        "upgrade",
        "validate",
    ]
    diff = {"diff": "diff"}
    response = {"response": "response"}

    with does_not_raise():
        instance = image_upgrade_task_result
        if state == "attach_policy":
            instance.diff_attach_policy = diff
            instance.response_attach_policy = response
        elif state == "detach_policy":
            instance.diff_detach_policy = diff
            instance.response_detach_policy = response
        elif state == "issu_status":
            instance.diff_issu_status = diff
            instance.response_issu_status = response
        elif state == "stage":
            instance.diff_stage = diff
            instance.response_stage = response
        elif state == "upgrade":
            instance.diff_upgrade = diff
            instance.response_upgrade = response
        elif state == "validate":
            instance.diff_validate = diff
            instance.response_validate = response
        result = instance.module_result
    assert isinstance(result, dict)
    assert result["changed"] == changed
    for key in test_keys:
        if key == test_key:
            assert result["diff"][key] == [diff]
            assert result["response"][key] == [response]
        else:
            assert result["diff"][key] == []
            assert result["response"][key] == []


@pytest.mark.parametrize(
    "state",
    [
        ("attach_policy"),
        ("detach_policy"),
        ("issu_status"),
        ("stage"),
        ("upgrade"),
        ("validate"),
    ],
)
def test_image_upgrade_upgrade_task_result_00060(
    image_upgrade_task_result, state
) -> None:
    """
    Function
    - ImageUpgradeTaskResult.module_result
    - ImageUpgradeTaskResult.did_anything_change
    - ImageUpgradeTaskResult.diff_*

    Summary
    Verify that fail_json is called by instance.diff_* when the diff
    is not a dict.
    """
    diff = "not a dict"
    match = r"ImageUpgradeTaskResult\._verify_is_dict: value must be a dict\."
    with does_not_raise():
        instance = image_upgrade_task_result
    with pytest.raises(AnsibleFailJson, match=match):
        if state == "attach_policy":
            instance.diff_attach_policy = diff
        elif state == "detach_policy":
            instance.diff_detach_policy = diff
        elif state == "issu_status":
            instance.diff_issu_status = diff
        elif state == "stage":
            instance.diff_stage = diff
        elif state == "upgrade":
            instance.diff_upgrade = diff
        elif state == "validate":
            instance.diff_validate = diff
        else:
            pass


@pytest.mark.parametrize(
    "state",
    [
        ("attach_policy"),
        ("detach_policy"),
        ("issu_status"),
        ("stage"),
        ("upgrade"),
        ("validate"),
    ],
)
def test_image_upgrade_upgrade_task_result_00070(
    image_upgrade_task_result, state
) -> None:
    """
    Function
    - ImageUpgradeTaskResult.module_result
    - ImageUpgradeTaskResult.did_anything_change
    - ImageUpgradeTaskResult.response_*

    Summary
    Verify that fail_json is called by instance.response_* when the response
    is not a dict.
    """
    response = "not a dict"
    match = r"ImageUpgradeTaskResult\._verify_is_dict: value must be a dict\."
    with does_not_raise():
        instance = image_upgrade_task_result
    with pytest.raises(AnsibleFailJson, match=match):
        if state == "attach_policy":
            instance.response_attach_policy = response
        elif state == "detach_policy":
            instance.response_detach_policy = response
        elif state == "issu_status":
            instance.response_issu_status = response
        elif state == "stage":
            instance.response_stage = response
        elif state == "upgrade":
            instance.response_upgrade = response
        elif state == "validate":
            instance.response_validate = response
        else:
            pass
