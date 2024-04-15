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

import inspect
import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    does_not_raise, fabric_create_common_fixture,
    payloads_fabric_create_common)


def test_fabric_create_common_00010(fabric_create_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricCreateCommon
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_create_common
        instance._build_properties()
    assert isinstance(instance.endpoints, ApiEndpoints)
    assert instance.class_name == "FabricCreateCommon"
    assert instance.action == "create"
    assert instance.check_mode is False
    assert instance.path is None
    assert instance.verb is None
    assert instance.state == "merged"
    assert instance._payloads_to_commit == []
    assert instance._mandatory_payload_keys == {"BGP_AS", "FABRIC_NAME", "FABRIC_TYPE"}


def test_fabric_create_common_00020(fabric_create_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricCreateCommon
        - __init__()
    - FabricCreateCommon
        - _verify_payload()

    Summary
    -   Verify ``ValueError`` is raised when payload is not a `dict``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payload = payloads_fabric_create_common(key)

    with does_not_raise():
        instance = fabric_create_common
        instance._build_properties()

    match = r"FabricCreateCommon\._verify_payload: payload must be a dict\."
    with pytest.raises(ValueError, match=match):
        instance._verify_payload(payload)


@pytest.mark.parametrize(
    "mandatory_key",
    [
        "BGP_AS",
        "FABRIC_NAME",
        "FABRIC_TYPE",
    ],
)
def test_fabric_create_common_00021(fabric_create_common, mandatory_key) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricCreateCommon
        - __init__()
    - FabricCreateCommon
        - _verify_payload()

    Summary
    -   Verify ``ValueError`` is raised when payload is missing mandatory keys.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payload = payloads_fabric_create_common(key)

    payload.pop(mandatory_key, None)

    with does_not_raise():
        instance = fabric_create_common
        instance._build_properties()

    match = r"FabricCreateCommon\._verify_payload: "
    match += rf"payload is missing mandatory keys: \['{mandatory_key}'\]"
    with pytest.raises(ValueError, match=match):
        instance._verify_payload(payload)


def test_fabric_create_common_00030(fabric_create_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricCreateCommon
        - __init__()
        - _set_fabric_create_endpoint

    Summary
    - ``ValueError`` is raised when payload contains invalid ``FABRIC_TYPE``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payload = payloads_fabric_create_common(key)

    with does_not_raise():
        instance = fabric_create_common
        instance._build_properties()

    match = r"FabricCreateCommon\.fabric_type: FABRIC_TYPE must be one of "
    match += r"\['VXLAN_EVPN'\]. "
    match += "Got INVALID_FABRIC_TYPE"
    with pytest.raises(ValueError, match=match):
        instance._set_fabric_create_endpoint(payload)


def test_fabric_create_common_00031(fabric_create_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricCreateCommon
        - __init__()
        - _set_fabric_create_endpoint

    Summary
    -   ``ValueError`` is raised when FabricCommon().fabric_type_to_template_name_map
        does not contain ``FABRIC_TYPE``.
    -   Since test 00030 already tests for invalid ``FABRIC_TYPE``, this test simulates
        the error condition by removing a valid key (``VXLAN_EVPN``) from
        ``fabric_type_to_template_name_map``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payload = payloads_fabric_create_common(key)

    with does_not_raise():
        instance = fabric_create_common
        instance._build_properties()
        instance.fabric_type_to_template_name_map.pop("VXLAN_EVPN", None)

    match = r"FabricCreateCommon\.fabric_type_to_template_name: "
    match += "Unknown fabric type: VXLAN_EVPN"
    with pytest.raises(ValueError, match=match):
        instance._set_fabric_create_endpoint(payload)


def test_fabric_create_common_00032(monkeypatch, fabric_create_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricCreateCommon
        - __init__()
        - _set_fabric_create_endpoint
        - endpoints.fabric_create

    Summary
    -   ``ValueError`` is raised when endpoints.fabric_create() raises an exception.
    -   Since ``fabric_name`` and ``template_name`` are already verified in
        _set_fabric_create_endpoint, ApiEndpoints().fabric_create() needs
        to be mocked to raise an exception.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payload = payloads_fabric_create_common(key)

    class MockApiEndpoints:  # pylint: disable=too-few-public-methods
        """
        Mock the ApiEndpoints.fabric_create() method to raise an exception.
        """

        @property
        def fabric_create(self):
            """
            Mocked method
            """
            raise ValueError("mocked exception")

    with does_not_raise():
        instance = fabric_create_common
        instance.endpoints = MockApiEndpoints()
        instance._build_properties()

    match = "mocked exception"
    with pytest.raises(ValueError, match=match):
        instance._set_fabric_create_endpoint(payload)
