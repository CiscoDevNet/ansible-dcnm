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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.control.switches.switches import \
    EpFabricSummary
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    does_not_raise

PATH_PREFIX = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/switches"
FABRIC_NAME = "MyFabric"


def test_ep_switches_00010():
    """
    ### Class
    -   EpFabricSummary

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpFabricSummary()
        instance.fabric_name = FABRIC_NAME
    assert f"{PATH_PREFIX}/{FABRIC_NAME}/overview" in instance.path
    assert instance.verb == "GET"


def test_ep_switches_00040():
    """
    ### Class
    -   EpFabricSummary

    ### Summary
    -   Verify ``ValueError`` is raised if path is accessed
        before setting ``fabric_name``.

    """
    with does_not_raise():
        instance = EpFabricSummary()
    match = r"EpFabricSummary.path_fabric_name:\s+"
    match += r"fabric_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_switches_00050():
    """
    ### Class
    -   EpFabricSummary

    ### Summary
    -   Verify ``ValueError`` is raised if ``fabric_name``
        is invalid.
    """
    fabric_name = "1_InvalidFabricName"
    with does_not_raise():
        instance = EpFabricSummary()
    match = r"EpFabricSummary.fabric_name:\s+"
    match += r"ConversionUtils\.validate_fabric_name:\s+"
    match += rf"Invalid fabric name: {fabric_name}\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_name = fabric_name  # pylint: disable=pointless-statement
