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
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.inventory.inventory import \
    EpAllSwitches
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.plugins.module_utils.common.switch_details import \
    SwitchDetails
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    ResponseGenerator, does_not_raise)

PARAMS = {"state": "merged", "check_mode": False}


def responses():
    """
    Dummy coroutine for ResponseGenerator()

    See e.g. test_switch_details_00800
    """
    yield {}


def test_switch_details_00000() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   __init__()

    ### Summary
    -   Verify class properties are initialized to expected values
    """
    with does_not_raise():
        instance = SwitchDetails()
    assert instance.action == "switch_details"
    assert instance.class_name == "SwitchDetails"
    assert isinstance(instance.conversion, ConversionUtils)
    assert isinstance(instance.ep_all_switches, EpAllSwitches)
    assert instance.path == EpAllSwitches().path
    assert instance.verb == EpAllSwitches().verb
    assert instance._filter is None
    assert instance._info is None
    assert instance._rest_send is None
    assert instance._results is None


def test_switch_details_00100() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   commit()

    ### Summary
    Verify ``validate_refresh_parameters()`` raises ``ValueError``
    due to ``rest_send`` not being set.

    ### Setup - Code
    -   SwitchDetails() is initialized.
    -   SwitchDetails().rest_send is NOT set.
    -   SwitchDetails().results is set.

    ### Setup - Data
    None

    ### Trigger
    -   SwitchDetails().refresh() is called.

    ### Expected Result
    -   SwitchDetails().validate_refresh_parameters() raises ``ValueError``.
    -   SwitchDetails().refresh() catches and re-raises ``ValueError``.
    """
    with does_not_raise():
        instance = SwitchDetails()
        instance.results = Results()

    match = r"SwitchDetails\.refresh:\s+"
    match += r"Mandatory parameters need review\.\s+"
    match += r"Error detail:\s+"
    match += r"SwitchDetails\.validate_refresh_parameters:\s+"
    match += r"SwitchDetails\.rest_send must be set before calling\s+"
    match += r"SwitchDetails\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_switch_details_00110() -> None:
    """
    ### Classes and Methods
    -   SwitchDetails()
            -   validate_refresh_parameters()
            -   commit()

    ### Summary
    Verify ``validate_refresh_parameters()`` raises ``ValueError``
    due to ``results`` not being set.

    ### Setup - Code
    -   SwitchDetails() is initialized.
    -   SwitchDetails().rest_send is set.
    -   SwitchDetails().results is NOT set.

    ### Setup - Data
    None

    ### Trigger
    -   SwitchDetails().refresh() is called.

    ### Expected Result
    -   SwitchDetails().validate_refresh_parameters() raises ``ValueError``.
    -   SwitchDetails().refresh() catches and re-raises ``ValueError``.
    """
    with does_not_raise():
        instance = SwitchDetails()
        instance.rest_send = RestSend(PARAMS)

    match = r"SwitchDetails\.refresh:\s+"
    match += r"Mandatory parameters need review\.\s+"
    match += r"Error detail:\s+"
    match += r"SwitchDetails\.validate_refresh_parameters:\s+"
    match += r"SwitchDetails\.results must be set before calling\s+"
    match += r"SwitchDetails\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()
