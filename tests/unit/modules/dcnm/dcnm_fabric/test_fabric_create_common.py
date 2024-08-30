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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.control.fabrics.fabrics import \
    EpFabricCreate
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, does_not_raise, fabric_create_common_fixture,
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
    assert instance.ep_fabric_create.class_name == "EpFabricCreate"
    assert instance.fabric_types.class_name == "FabricTypes"
    assert instance.class_name == "FabricCreateCommon"
    assert instance.action == "fabric_create"
    assert instance.path is None
    assert instance.verb is None
    assert instance._payloads_to_commit == []


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

    match = r"FabricCreateCommon\.fabric_type: FABRIC_TYPE must be one of\s+.*"
    match += "Got INVALID_FABRIC_TYPE"
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
        - ep_fabric_create.fabric_name setter

    Summary
    -   ``ValueError`` is raised when ep_fabric_create.fabric_name raises an exception.
    -   Since ``fabric_name`` and ``template_name`` are already verified in
        _set_fabric_create_endpoint, EpFabricCreate().fabric_name setter needs
        to be mocked to raise an exception.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payload = payloads_fabric_create_common(key)

    class MockEpFabricCreate:  # pylint: disable=too-few-public-methods
        """
        Mock the EpFabricCreate.fabric_name setter property
        to raise ``ValueError``.
        """

        @property
        def fabric_name(self):
            """
            Mocked method
            """

        @fabric_name.setter
        def fabric_name(self, value):
            """
            Mocked method
            """
            msg = "MockEpFabricCreate.fabric_name: mocked exception."
            raise ValueError(msg)

    with does_not_raise():
        instance = fabric_create_common
        monkeypatch.setattr(instance, "ep_fabric_create", MockEpFabricCreate())
        instance.ep_fabric_create = MockEpFabricCreate()

    match = r"MockEpFabricCreate\.fabric_name: mocked exception\."
    with pytest.raises(ValueError, match=match):
        instance._set_fabric_create_endpoint(payload)


def test_fabric_create_common_00033(monkeypatch, fabric_create_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricCreateCommon
        - __init__()
        - _set_fabric_create_endpoint
        - ep_fabric_create.template_name setter

    Summary
    -   ``ValueError`` is raised when ep_fabric_create.template_name raises an exception.
    -   Since ``fabric_name`` and ``template_name`` are already verified in
        _set_fabric_create_endpoint, EpFabricCreate().template_name setter needs
        to be mocked to raise an exception.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payload = payloads_fabric_create_common(key)

    class MockEpFabricCreate:  # pylint: disable=too-few-public-methods
        """
        Mock the EpFabricCreate.template_name setter property
        to raise ``ValueError``.
        """

        @property
        def template_name(self):
            """
            Mocked method
            """

        @template_name.setter
        def template_name(self, value):
            """
            Mocked method
            """
            msg = "MockEpFabricCreate.template_name: mocked exception."
            raise ValueError(msg)

    with does_not_raise():
        instance = fabric_create_common
        monkeypatch.setattr(instance, "ep_fabric_create", MockEpFabricCreate())
        instance.ep_fabric_create = MockEpFabricCreate()

    match = r"MockEpFabricCreate\.template_name: mocked exception\."
    with pytest.raises(ValueError, match=match):
        instance._set_fabric_create_endpoint(payload)


def test_fabric_create_common_00040(monkeypatch, fabric_create_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricCreateCommon
        - __init__()
        - _set_fabric_create_endpoint
        - fabric_types.template_name getter

    Summary
    -   ``ValueError`` is raised when fabric_types.template_name getter raises
        an exception.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payload = payloads_fabric_create_common(key)

    class MockFabricTypes:  # pylint: disable=too-few-public-methods
        """
        Mock the FabricTypes.template_name setter property
        to raise ``ValueError``.
        """

        @property
        def valid_fabric_types(self):
            """
            Return fabric_type matching payload FABRIC_TYPE
            """
            return ["VXLAN_EVPN"]

        @property
        def template_name(self):
            """
            Mocked method
            """
            msg = "MockEpFabricCreate.template_name: mocked exception."
            raise ValueError(msg)

    with does_not_raise():
        instance = fabric_create_common
        monkeypatch.setattr(instance, "fabric_types", MockFabricTypes())

    match = r"MockEpFabricCreate\.template_name: mocked exception\."
    with pytest.raises(ValueError, match=match):
        instance._set_fabric_create_endpoint(payload)


def test_fabric_create_common_00050(monkeypatch, fabric_create_common) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricCreateCommon
        - __init__()
        - _set_fabric_create_endpoint
        - _send_payloads()

    Summary
    -   _send_payloads() re-raises ``ValueError`` when
        _set_fabric_create_endpoint() raises ``ValueError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payload = payloads_fabric_create_common(key)

    def mock_set_fabric_create_endpoint(
        *args,
    ):  # pylint: disable=too-few-public-methods
        """
        Mock the FabricCreateCommon()._set_fabric_create_endpoint()
        to raise ``ValueError``.
        """
        msg = "mock_set_fabric_endpoint(): mocked exception."
        raise ValueError(msg)

    with does_not_raise():
        instance = fabric_create_common
        instance.rest_send = RestSend(MockAnsibleModule())
        monkeypatch.setattr(
            instance, "_set_fabric_create_endpoint", mock_set_fabric_create_endpoint
        )
        instance._payloads_to_commit = [payload]

    match = r"mock_set_fabric_endpoint\(\): mocked exception\."
    with pytest.raises(ValueError, match=match):
        instance._send_payloads()
