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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details_v2 import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, does_not_raise, fabric_create_bulk_fixture, params,
    payloads_fabric_create_bulk, responses_fabric_create_bulk,
    responses_fabric_details_by_name_v2, rest_send_response_current)


def test_fabric_create_bulk_00000(fabric_create_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
    - FabricCreateBulk
        - __init__()

    ### Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_create_bulk
        instance.fabric_details = FabricDetailsByName()
    assert instance.class_name == "FabricCreateBulk"
    assert instance.action == "fabric_create"
    assert instance.fabric_details.class_name == "FabricDetailsByName"


def test_fabric_create_bulk_00020(fabric_create_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
        - payloads setter
    - FabricCreateBulk
        - __init__()

    ### Test
    - payloads is set to expected value
    - Exception is not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_create_bulk
        instance.results = Results()
        instance.payloads = payloads_fabric_create_bulk(key)
    assert instance.payloads == payloads_fabric_create_bulk(key)


def test_fabric_create_bulk_00021(fabric_create_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
        - payloads setter
    - FabricCreateBulk
        - __init__()
        - payloads setter

    ### Summary
    -   Verify ``ValueError`` is raised because payloads is not a list
    -   Verify ``instance.payloads`` is not modified, hence it retains its
        initial value of None
    """
    with does_not_raise():
        instance = fabric_create_bulk
        instance.results = Results()

    match = r"FabricCreateBulk\.payloads: "
    match += r"payloads must be a list of dict\."

    with pytest.raises(ValueError, match=match):
        instance.payloads = "NOT_A_LIST"
    assert instance.payloads is None


def test_fabric_create_bulk_00022(fabric_create_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
        - payloads setter
    - FabricCreateBulk
        - __init__()

    ### Summary
    -   Verify ``ValueError`` is raised because payloads is a list with
        a non-dict element
    -   Verify instance.payloads is not modified, hence it retains its
        initial value of None
    """
    with does_not_raise():
        instance = fabric_create_bulk
        instance.results = Results()

    match = r"FabricCreateBulk._verify_payload: "
    match += r"Playbook configuration for fabrics must be a dict\.\s+"
    match += r"Got type int, value 1\."

    with pytest.raises(ValueError, match=match):
        instance.payloads = [1, 2, 3]
    assert instance.payloads is None


def test_fabric_create_bulk_00023(fabric_create_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
        - payloads setter
    - FabricCreateBulk
        - __init__()
        - commit()

    ### Summary
    Verify behavior when payloads is not set prior to calling commit.

    ### Test
    -   ``ValueError`` is raised because payloads is not set prior
        to calling commit
    -   instance.payloads is not modified, hence it retains its
        initial value of None
    """
    with does_not_raise():
        instance = fabric_create_bulk
        instance.results = Results()
        instance.rest_send = RestSend(params)
        instance.rest_send.unit_test = True

    match = r"FabricCreateBulk\.commit: "
    match += r"payloads must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()
    assert instance.payloads is None


def test_fabric_create_bulk_00024(fabric_create_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
        - payloads setter
    - FabricCreateBulk
        - __init__()

    ### Summary
    Verify behavior when ``payloads`` is set to an empty list.

    ### Setup

    -   ``payloads`` is set to an empty list.

    ### Test

    -   Exception is not raised
    -   ``payloads`` is set to an empty list.

    ### NOTES
    -   element_spec is configured such that an exception is raised when
        config is not a list of dict.  Hence, we do not test ``commit``
        here since it would never be reached.
    """
    with does_not_raise():
        instance = fabric_create_bulk
        instance.results = Results()
        instance.payloads = []
    assert instance.payloads == []


def test_fabric_create_bulk_00025(fabric_create_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCreateCommon
        - __init__()
        - payloads setter
    - FabricCreateBulk
        - __init__()

    ### Summary
    Verify behavior when payloads contains a dict with an unexpected
    value for the FABRIC_TYPE key.

    ### Setup
    -   FabricCreatebulk().payloads is set to contain a dict with FABRIC_TYPE
        set to "INVALID_FABRIC_TYPE".

    ### Test
    -   ``ValueError`` is raised because the value of FABRIC_TYPE is invalid.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_create_bulk

        instance.fabric_details = FabricDetailsByName()
        instance.fabric_details.rest_send = RestSend(params)
        instance.fabric_details.rest_send.unit_test = True
        instance.rest_send = RestSend(params)
        instance.rest_send.unit_test = True
        instance.results = Results()

    match = r"FabricCreateBulk\._verify_payload:\s+"
    match += r"Playbook configuration for fabric f1 contains an invalid\s+"
    match += r"FABRIC_TYPE \(INVALID_FABRIC_TYPE\)\.\s+"
    match += r"Valid values for FABRIC_TYPE:"

    with pytest.raises(ValueError, match=match):
        instance.payloads = payloads_fabric_create_bulk(key)


def test_fabric_create_bulk_00026(fabric_create_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
        - payloads setter
    - FabricCreateBulk
        - __init__()

    ### Summary
    Verify behavior when ``rest_send`` is not set prior to calling ``commit``.

    ### Test
    -   ``ValueError`` is raised because rest_send is not set prior
        to calling commit
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_create_bulk
        instance.fabric_details = FabricDetailsByName()
        instance.results = Results()
        instance.payloads = payloads_fabric_create_bulk(key)

    match = r"FabricCreateBulk\.commit: "
    match += r"rest_send must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_create_bulk_00030(fabric_create_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon()
        - __init__()
        - payloads setter
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricCreateBulk
        - __init__()
        - commit()

    ### Summary
    Verify behavior when user attempts to create a fabric and no fabrics
    exist on the controller and the RestSend() RETURN_CODE is 200.

    ### Code Flow

    -   FabricCreateBulk.payloads is set to contain one payload for a fabric (f1)
        that does not exist on the controller.
    -   FabricCreateBulk.commit() calls FabricCreate()._build_payloads_to_commit()
    -   FabricCreate()._build_payloads_to_commit() calls FabricDetails().refresh()
        which returns a dict with keys DATA == [], RETURN_CODE == 200
    -   FabricCreate()._build_payloads_to_commit() sets FabricCreate()._payloads_to_commit
        to a list containing fabric f1 payload
    -   FabricCreateBulk.commit() calls RestSend().commit() which sets RestSend().response_current
        to a dict with keys:
        -   DATA == {f1 fabric data dict}
            RETURN_CODE == 200
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_details_by_name_v2(key)
        yield responses_fabric_create_bulk(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_create_bulk
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_details.results = Results()
        instance.fabric_details.rest_send = rest_send
        instance.rest_send = rest_send
        instance.results = Results()
        instance.payloads = payloads_fabric_create_bulk(key)
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[0].get("BGP_AS", None) == 65001
    assert instance.results.diff[0].get("FABRIC_NAME", None) == "f1"

    assert instance.results.metadata[0].get("action", None) == "fabric_create"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "merged"

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert (
        instance.results.response[0]
        .get("DATA", {})
        .get("nvPairs", {})
        .get("BGP_AS", None)
        == "65001"
    )
    assert instance.results.response[0].get("METHOD", None) == "POST"

    assert instance.results.result[0].get("changed", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert True in instance.results.changed
    assert False not in instance.results.changed


def test_fabric_create_bulk_00031(fabric_create_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricCreateCommon()
        - __init__()
        - payloads setter
    - FabricCreateBulk()
        - __init__()
        - commit()

    ### Summary
    Verify behavior when FabricCreateBulk() is used to create a fabric and
    the fabric exists on the controller.

    ### Setup
    -   FabricDetails().refresh() is set to indicate that fabric f1 exists
        on the controller

    ### Code Flow
    -   FabricCreateBulk.payloads is set to contain one payload for a fabric (f1)
        that already exists on the controller.
    -   FabricCreateBulk.commit() calls FabricCreate()._build_payloads_to_commit()
    -   FabricCreate()._build_payloads_to_commit() calls FabricDetails().refresh()
        which returns a dict with keys DATA == [{f1 fabric data dict}], RETURN_CODE == 200
    -   FabricCreate()._build_payloads_to_commit() sets FabricCreate()._payloads_to_commit
        to an empty list since fabric f1 already exists on the controller
    -   FabricCreateBulk.commit() returns without doing anything.

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_details_by_name_v2(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_create_bulk
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_details.results = Results()
        instance.fabric_details.rest_send = rest_send
        instance.rest_send = rest_send
        instance.results = Results()
        instance.payloads = payloads_fabric_create_bulk(key)
        instance.fabric_details.rest_send.unit_test = True
        instance.commit()

    assert instance._payloads_to_commit == []
    assert instance.results.diff == []
    assert instance.results.metadata == []
    assert instance.results.response == []
    assert instance.results.result == []


def test_fabric_create_bulk_00032(fabric_create_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon()
        - __init__()
        - payloads setter
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricCreateBulk
        - __init__()
        - commit()

    ### Summary
    Verify behavior when user attempts to create a fabric but the
    controller RETURN_CODE is 500.

    ### Setup
    -   FabricDetails().refresh() is set to indicate that no fabrics exist on
        the controller

    ### Code Flow
    -   FabricCreateBulk.payloads is set to contain one payload for a fabric (f1)
        that does not exist on the controller.
    -   FabricCreateBulk.commit() calls FabricCreate()._build_payloads_to_commit()
    -   FabricCreate()._build_payloads_to_commit() calls FabricDetails().refresh()
        which returns a dict with keys DATA == [], RETURN_CODE == 200
    -   FabricCreate()._build_payloads_to_commit() sets FabricCreate()._payloads_to_commit
        to a list containing fabric f1 payload
    -   FabricCreateBulk.commit() calls RestSend().commit() which sets RestSend().response_current
        to a dict with keys:
        -   DATA == "Error in validating provided name value pair: [BGP_AS]"
            RETURN_CODE == 500,
            MESSAGE = "Internal Server Error"
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_details_by_name_v2(key)
        yield responses_fabric_create_bulk(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_create_bulk
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_details.results = Results()
        instance.fabric_details.rest_send = rest_send
        instance.rest_send = rest_send
        instance.results = Results()
        instance.payloads = payloads_fabric_create_bulk(key)
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1

    assert instance.results.metadata[0].get("action", None) == "fabric_create"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "merged"

    assert instance.results.response[0].get("RETURN_CODE", None) == 500
    assert (
        instance.results.response[0].get("DATA", {})
        == "Error in validating provided name value pair: [BGP_AS]"
    )
    assert instance.results.response[0].get("METHOD", None) == "POST"

    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is False

    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_create_bulk_00033(monkeypatch, fabric_create_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon()
        - __init__()
        - payloads setter
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricCreateBulk
        - __init__()
        - commit()

    ### Summary
    Verify ``ValueError`` is raised when user attempts to create a fabric
    but the payload contains ``ANYCAST_GW_MAC`` with a malformed mac address.

    ### Setup

    -   FabricDetails().refresh() is set to indicate that no fabrics exist on
        the controller

    ### Code Flow
    -   FabricCreateBulk.payloads is set to contain one payload for a fabric (f1)
        that does not exist on the controller.  ``ANYCAST_GW_MAC`` in this payload
        has a malformed mac address.
    -   FabricCreateBulk().commit() calls
        FabricCreate()._build_payloads_to_commit()
    -   FabricCreate()._build_payloads_to_commit() calls
        FabricDetails().refresh() which returns a dict with keys
        DATA == [], RETURN_CODE == 200
    -   FabricCreate()._build_payloads_to_commit() sets
        FabricCreate()._payloads_to_commit to a list containing fabric f1 payload
    -   FabricCreateBulk().commit() calls FabricCommon()._fixup_payloads_to_commit()
    -   FabricCommon()._fixup_payloads_to_commit() calls
        FabricCommon()._fixup_anycast_gw_mac() which raises ``ValueError``
        because the mac address is malformed.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_details_by_name_v2(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_create_bulk

        instance.fabric_details = FabricDetailsByName()
        instance.fabric_details.results = Results()
        instance.fabric_details.rest_send = rest_send
        instance.rest_send = rest_send
        instance.results = Results()
        instance.payloads = payloads_fabric_create_bulk(key)

    match = r"FabricCreateBulk\._fixup_anycast_gw_mac: "
    match += "Error translating ANYCAST_GW_MAC for fabric f1, "
    match += "ANYCAST_GW_MAC: 00:12:34:56:78:9, "
    match += "Error detail: Invalid MAC address: 00123456789"

    with pytest.raises(ValueError, match=match):
        instance.commit()
