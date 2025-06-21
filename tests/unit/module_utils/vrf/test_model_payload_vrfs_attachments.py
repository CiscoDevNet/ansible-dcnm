# Copyright (c) 2025 Cisco and/or its affiliates.
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
"""
Test cases for PayloadfVrfsDeployments.
"""
from functools import partial

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.vrf.model_payload_vrfs_attachments import PayloadVrfsAttachments

from ..common.common_utils import does_not_raise
from .fixtures.load_fixture import payloads_vrfs_attachments

vrf_name_tests = [
    ("test_vrf", "test_vrf", True),
    (
        "vrf_5678901234567890123456789012",
        "vrf_5678901234567890123456789012",
        True,
    ),  # Valid, exactly 32 characters
    (123, None, False),  # Invalid, int
    (
        "vrf_56789012345678901234567890123",
        None,
        False,
    ),  # Invalid, longer than 32 characters
]


# pylint: disable=too-many-arguments
def base_test(value, expected, valid: bool, model_field: str, payload_field: str, key: str, model):
    """
    Base test function called by other tests to validate the model.

    :param value: vrf_model value to validate.
    :param expected: Expected value after model conversion or validation (None for no expectation).
    :param valid: Whether the input value is expected to be valid or not.
    :param field: The field in the playbook to modify.
    :param key: The key in the playbooks fixture to use.
    :param model: The model class to instantiate.
    """
    payload = payloads_vrfs_attachments(key)
    print(f"payload before: {payload}")
    if value == "MISSING":
        payload.pop(payload_field, None)
    else:
        payload[payload_field] = value
    print(f"payload after: {payload}")

    if valid:
        with does_not_raise():
            instance = model(**payload)
            print(f"instance: {instance}")
            if value != "MISSING":
                assert getattr(instance, model_field) == expected
            else:
                assert expected == model.model_fields[model_field].default
    else:
        with pytest.raises(ValueError):
            print(f"FINAL PAYLOAD: {payload}")
            model(**payload)


base_test_vrf_name = partial(
    base_test,
    model_field="vrf_name",
    payload_field="vrfName",
    key="payload_full",
    model=PayloadVrfsAttachments,
)

# pylint: enable=too-many-arguments


@pytest.mark.parametrize("value, expected, valid", vrf_name_tests)
def test_payload_vrfs_attachments_00000(value, expected, valid) -> None:
    """
    vrf_name
    """
    base_test_vrf_name(value, expected, valid)
