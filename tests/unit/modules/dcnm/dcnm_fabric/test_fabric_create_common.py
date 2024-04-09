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
    assert instance._mandatory_payload_keys == {"BGP_AS", "FABRIC_NAME"}
