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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, ResponseGenerator, does_not_raise,
    fabric_create_fixture, params, payloads_fabric_create,
    responses_fabric_create, responses_fabric_details,
    rest_send_response_current)


def test_fabric_create_00010(fabric_create) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricCreate
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_create
        instance.fabric_details = FabricDetailsByName(params)
    assert instance.class_name == "FabricCreate"
    assert instance.action == "create"
    assert instance.state == "merged"
    assert isinstance(instance.fabric_details, FabricDetailsByName)


def test_fabric_create_00020(fabric_create) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payload setter
    - FabricCreate
        - __init__()
        - payload setter

    Summary
    -   Verify that payload is set to expected value when a valid payload is
        passed to FabricCreate().payload
    -   Verify that an Exception is not raised
    """
    key = "test_fabric_create_00020a"
    with does_not_raise():
        instance = fabric_create
        instance.results = Results()
        instance.payload = payloads_fabric_create(key)
    assert instance.payload == payloads_fabric_create(key)


def test_fabric_create_00021(fabric_create) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricCreate
        - __init__()
        - payloads setter

    Summary
    -   Verify ``ValueError`` is raised because payloads is not a ``dict``
    -   Verify ``instance.payload`` is not modified, hence it retains its
        initial value of None
    """
    match = r"FabricCreate\.payload: "
    match += r"payload must be a dict\."

    with does_not_raise():
        instance = fabric_create
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.payload = "NOT_A_DICT"
    assert instance.payload is None


def test_fabric_create_00022(fabric_create) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricCreate
        - __init__()
        - payload setter

    Summary
    Verify that ``ValueError`` is raised because payload is empty
    """
    with does_not_raise():
        instance = fabric_create
        instance.results = Results()
        instance.rest_send = RestSend(MockAnsibleModule())
    match = r"FabricCreate\.payload: payload is empty."
    with pytest.raises(ValueError, match=match):
        instance.payload = {}
    assert instance.payload is None


@pytest.mark.parametrize(
    "mandatory_key",
    ["BGP_AS", "FABRIC_NAME", "FABRIC_TYPE"],
)
def test_fabric_create_00023(fabric_create, mandatory_key) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricCreate
        - __init__()
        - payload setter

    Summary
    -   Verify that ``ValueError`` is raised because payload is missing
        mandatory keys.

    """
    key = "test_fabric_create_00023a"
    payload = payloads_fabric_create(key)
    payload.pop(mandatory_key, None)

    with does_not_raise():
        instance = fabric_create
        instance.results = Results()
        instance.rest_send = RestSend(MockAnsibleModule())

    match = r"FabricCreate\._verify_payload: "
    match += r"payload is missing mandatory keys:"
    with pytest.raises(ValueError, match=match):
        instance.payload = payload
    assert instance.payload is None


def test_fabric_create_00024(fabric_create) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricCreate
        - __init__()
        - commit()

    Summary
    -   Verify ``ValueError`` is raised because payload is not set prior
        to calling commit
    -   Verify instance.payloads is not modified, hence it retains its
        initial value of None
    """
    match = r"FabricCreate\.commit: "
    match += r"payload must be set prior to calling commit\."

    with does_not_raise():
        instance = fabric_create
        instance.results = Results()
        instance.rest_send = RestSend(MockAnsibleModule())
    with pytest.raises(ValueError, match=match):
        instance.commit()
    assert instance.payload is None


def test_fabric_create_00025(monkeypatch, fabric_create) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payload setter
    - FabricCreate
        - __init__()

    Summary
    -   Verify behavior when payload contains FABRIC_TYPE key with
        an unexpected value.

    Test
    -   ``ValueError`` is raised because the value of FABRIC_TYPE is invalid
    """
    key = "test_fabric_create_00025a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_create

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()
        instance.payload = payloads_fabric_create(key)

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    match = r"FabricCreate\.fabric_type: FABRIC_TYPE must be one of"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_create_00026(fabric_create) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricCreateBulk
        - __init__()

    Summary
    -   Verify behavior when rest_send is not set prior to calling commit

    Test
    -   ``ValueError`` is raised because rest_send is not set prior
        to calling commit
    """
    key = "test_fabric_create_00026a"
    match = r"FabricCreate\.commit: "
    match += r"rest_send must be set prior to calling commit\."

    with does_not_raise():
        instance = fabric_create
        instance.fabric_details = FabricDetailsByName(params)
        instance.results = Results()
        instance.payload = payloads_fabric_create(key)
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_create_00030(monkeypatch, fabric_create) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
        - payloads setter
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricCreate
        - __init__()
        - commit()

    Summary
    -   Verify behavior when user attempts to create a fabric and no fabrics
        exist on the controller and the RestSend() RETURN_CODE is 200.

    Code Flow
    -   FabricCreate.payloads is set to contain one payload for a fabric (f1)
        that does not exist on the controller.
    -   FabricCreate.commit() calls FabricCreate()._build_payloads_to_commit()
    -   FabricCreate()._build_payloads_to_commit() calls FabricDetails().refresh()
        which returns a dict with keys DATA == [], RETURN_CODE == 200
    -   FabricCreate()._build_payloads_to_commit() sets FabricCreate()._payloads_to_commit
        to a list containing fabric f1 payload
    -   FabricCreate.commit() calls RestSend().commit() which sets RestSend().response_current
        to a dict with keys:
        -   DATA == {f1 fabric data dict}
            RETURN_CODE == 200
    """
    key = "test_fabric_create_00030a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details(key)
        yield responses_fabric_create(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_create
        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()
        instance.payload = payloads_fabric_create(key)
        instance.fabric_details.rest_send.unit_test = True

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)
    with does_not_raise():
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

    assert instance.results.metadata[0].get("action", None) == "create"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "merged"

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    print(f"response[0] {instance.results.response[0]}")
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


def test_fabric_create_00031(monkeypatch, fabric_create) -> None:
    """
    Classes and Methods
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
    - FabricCreate()
        - __init__()
        - commit()

    Summary
    -   Verify behavior when FabricCreate() is used to create a fabric and
        the fabric exists on the controller.

    Setup
    -   FabricDetails().refresh() is set to indicate that fabric f1 exists
        on the controller

    Code Flow
    -   FabricCreate.payload is set to contain one payload for a fabric (f1)
        that already exists on the controller.
    -   FabricCreate.commit() calls FabricCreate()._build_payloads_to_commit()
    -   FabricCreate()._build_payloads_to_commit() calls FabricDetails().refresh()
        which returns a dict with keys DATA == [{f1 fabric data dict}], RETURN_CODE == 200
    -   FabricCreate()._build_payloads_to_commit() sets FabricCreate()._payloads_to_commit
        to an empty list since fabric f1 already exists on the controller
    -   FabricCreate.commit() returns without doing anything.

    """
    key = "test_fabric_create_00031a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_create
        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()
        instance.payload = payloads_fabric_create(key)
        instance.fabric_details.rest_send.unit_test = True

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)
    with does_not_raise():
        instance.commit()

    assert instance._payloads_to_commit == []
    assert instance.results.diff == []
    assert instance.results.metadata == []
    assert instance.results.response == []
    assert instance.results.result == []


def test_fabric_create_00032(monkeypatch, fabric_create) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
        - payloads setter
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricCreate
        - __init__()
        - commit()

    Summary
    -   Verify behavior when user attempts to create a fabric but the
        controller RETURN_CODE is 500.

    Setup
    -   FabricDetails().refresh() is set to indicate that no fabrics exist on
        the controller

    Code Flow
    -   FabricCreate.payload is set to contain one payload for a fabric (f1)
        that does not exist on the controller.
    -   FabricCreate.commit() calls FabricCreate()._build_payloads_to_commit()
    -   FabricCreate()._build_payloads_to_commit() calls FabricDetails().refresh()
        which returns a dict with keys DATA == [], RETURN_CODE == 200
    -   FabricCreate()._build_payloads_to_commit() sets FabricCreate()._payloads_to_commit
        to a list containing fabric f1 payload
    -   FabricCreate.commit() calls RestSend().commit() which sets RestSend().response_current
        to a dict with keys:
        -   DATA == "Error in validating provided name value pair: [BGP_AS]"
            RETURN_CODE == 500,
            MESSAGE = "Internal Server Error"
    """
    key = "test_fabric_create_00032a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details(key)
        yield responses_fabric_create(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_create

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()
        instance.payload = payloads_fabric_create(key)

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)
    with does_not_raise():
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1

    assert instance.results.metadata[0].get("action", None) == "create"
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


def test_fabric_create_00033(monkeypatch, fabric_create) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
        - payloads setter
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricCreate
        - __init__()
        - commit()

    Summary
    -   Verify ``ValueError`` is raised when user attempts to create a fabric
        but the payload contains ``ANYCAST_GW_MAC`` with a malformed mac address.

    Setup
    -   FabricDetails().refresh() is set to indicate that no fabrics exist on
        the controller

    Code Flow
    -   FabricCreate.payloads is set to contain one payload for a fabric (f1)
        that does not exist on the controller.  ``ANYCAST_GW_MAC`` in this payload
        has a malformed mac address.
    -   FabricCreate.commit() calls FabricCreate()._build_payloads_to_commit()
    -   FabricCreate()._build_payloads_to_commit() calls FabricDetails().refresh()
        which returns a dict with keys DATA == [], RETURN_CODE == 200
    -   FabricCreate()._build_payloads_to_commit() sets FabricCreate()._payloads_to_commit
        to a list containing fabric f1 payload
    -   FabricCreate.commit() calls FabricCommon_fixup_payloads_to_commit() which
        raises ``ValueError`` because the mac address is malformed.
    """
    key = "test_fabric_create_00033a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_create

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()
        instance.payload = payloads_fabric_create(key)

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    match = r"FabricCreate\._fixup_payloads_to_commit: "
    match += "Error translating ANYCAST_GW_MAC for fabric f1, "
    match += "ANYCAST_GW_MAC: 00:12:34:56:78:9, "
    match += "Error detail: Invalid MAC address: 00123456789"

    with pytest.raises(ValueError, match=match):
        instance.commit()
