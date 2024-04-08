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
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_summary import \
    FabricSummary
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, ResponseGenerator, does_not_raise,
    fabric_update_bulk_fixture, params, payloads_fabric_update_bulk,
    responses_fabric_details, responses_fabric_summary,
    responses_fabric_update_bulk)


def test_fabric_update_bulk_00010(fabric_update_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricUpdateBulk
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = fabric_update_bulk
        instance.fabric_details = FabricDetailsByName(params)
    assert instance.class_name == "FabricUpdateBulk"
    assert instance.action == "update"
    assert instance.state == "merged"
    assert isinstance(instance.fabric_details, FabricDetailsByName)


def test_fabric_update_bulk_00020(fabric_update_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricUpdateBulk
        - __init__()

    Summary
    A valid payloads list is presented to the payloads setter

    Test
    - payloads is set to expected value
    - ``ValueError`` is not raised
    """
    key = "test_fabric_update_bulk_00020a"
    with does_not_raise():
        instance = fabric_update_bulk
        instance.fabric_details = FabricDetailsByName(params)
        instance.results = Results()
        instance.payloads = payloads_fabric_update_bulk(key)
    assert instance.payloads == payloads_fabric_update_bulk(key)


def test_fabric_update_bulk_00021(fabric_update_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricUpdateBulk
        - __init__()

    Summary
    ``payloads`` setter is presented with input that is not a list.

    Test
    - ``ValueError`` is raised because payloads is not a list
    - instance.payloads retains its initial value of None
    """
    match = r"FabricUpdateBulk\.payloads: "
    match += r"payloads must be a list of dict\."

    with does_not_raise():
        instance = fabric_update_bulk
        instance.fabric_details = FabricDetailsByName(params)
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.payloads = "NOT_A_LIST"
    assert instance.payloads is None


def test_fabric_update_bulk_00022(fabric_update_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricUpdateBulk
        - __init__()

    Summary
    ``payloads`` setter is presented with a list that contains a non-dict element.

    Test
    - ``ValueError`` is raised because payloads is a list with non-dict elements
    - instance.payloads retains its initial value of None
    """
    match = r"FabricUpdateBulk._verify_payload: "
    match += r"payload must be a dict\."

    with does_not_raise():
        instance = fabric_update_bulk
        instance.fabric_details = FabricDetailsByName(params)
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.payloads = [1, 2, 3]
    assert instance.payloads is None


def test_fabric_update_bulk_00023(fabric_update_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricUpdateBulk
        - __init__()

    Summary
    payloads is not set prior to calling commit

    Test
    - ValueError is raised because payloads is not set prior to calling commit
    - instance.payloads retains its initial value of None
    """
    match = r"FabricUpdateBulk\.commit: "
    match += r"payloads must be set prior to calling commit\."

    with does_not_raise():
        instance = fabric_update_bulk
        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_summary = FabricSummary(params)
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.commit()
    assert instance.payloads is None


def test_fabric_update_bulk_00024(fabric_update_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricUpdateBulk
        - __init__()

    Summary
    payloads is set to an empty list

    Setup
    -   FabricUpdatebulk().payloads is set to an empty list

    Test
    -   ``ValueError`` is not raised
    -   payloads is set to an empty list

    NOTES:
    -   element_spec in dcnm_fabric.py.main() is configured such that AnsibleModule will
        raise an exception when config is not a list of dict.  Hence, we do not test
        instance.commit() here since it would never be reached.
    """
    with does_not_raise():
        instance = fabric_update_bulk
        instance.results = Results()
        instance.payloads = []
    assert instance.payloads == []


def test_fabric_update_bulk_00025(fabric_update_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricUpdateBulk
        - __init__()

    Summary
    payloads is set to a list of one dict with missing mandatory key BGP_AS

    Test
    -   ``ValueError`` is raised
    -   instance.payloads retains its initial value of None

    """
    key = "test_fabric_update_bulk_00025a"
    with does_not_raise():
        instance = fabric_update_bulk
        instance.fabric_details = FabricDetailsByName(params)
        instance.results = Results()

    match = r"FabricUpdateBulk\._verify_payload: "
    match += r"payload is missing mandatory keys:"
    with pytest.raises(ValueError, match=match):
        instance.payloads = payloads_fabric_update_bulk(key)
    assert instance.payloads is None


def test_fabric_update_bulk_00030(monkeypatch, fabric_update_bulk) -> None:
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
    - FabricUpdateBulk
        - __init__()
        - commit()

    Summary
    Verify behavior when user attempts to update a fabric and no
    fabrics exist on the controller.

    Code Flow
    -   FabricUpdateBulk.payloads is set to contain one payload for a fabric (f1)
        that does not exist on the controller.
    -   FabricUpdateBulk.commit() calls FabricUpdateCommon()._build_payloads_to_commit()
    -   FabricUpdateCommon()._build_payloads_to_commit() calls FabricDetails().refresh()
        which returns a dict with keys DATA == [], RETURN_CODE == 200
    -   FabricUpdateCommon()._build_payloads_to_commit() sets FabricUpdate()._payloads_to_commit
        to an empty list.
    -   FabricUpdateBulk.commit() updates the following:
        -   instance.results.diff_current to an empty dict
        -   instance.results.response_current a synthesized response dict
            { "RETURN_CODE": 200, "MESSAGE": "No fabrics to update." }
        -  instance.results.result_current to a synthesized result dict
           {"success": True, "changed": False}
    -   FabricUpdateBulk.commit() calls Results().register_task_result()
    """
    key = "test_fabric_update_bulk_00030a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details(key)
        yield responses_fabric_update_bulk(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_update_bulk

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.results = Results()
        instance.payloads = payloads_fabric_update_bulk(key)

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

    assert instance.results.metadata[0].get("action", None) == "update"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "merged"

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.response[0].get("MESSAGE", None) == "No fabrics to update."

    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_update_bulk_00031(monkeypatch, fabric_update_bulk) -> None:
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
    - FabricQuery
        - __init__()
        - fabric_names setter
        - commit()
    - FabricUpdateBulk()
        - __init__()
        - commit()

    Summary
    -   Verify behavior when user attempts to update a fabric and the
        fabric exists on the controller and the RestSend() RETURN_CODE is 200.
    -   The fabric payload includes ANYCAST_GW_MAC, formatted to be incompatible
        with the controller's requirements, but able to be fixed by
        FabricUpdateCommon()._fixup_payloads_to_commit().
    -   The fabric payload also contains keys that include ``bool`
        and ``int`` values.


    Code Flow
    -   FabricUpdateBulk.payloads is set to contain one payload for a fabric (f1)
        that exists on the controller.
    -   FabricUpdateBulk.commit() calls FabricUpdateCommon()._build_payloads_to_commit()
    -   FabricUpdateCommon()._build_payloads_to_commit() calls FabricDetails().refresh()
        which returns a dict with fabric f1 information and RETURN_CODE == 200
    -   FabricUpdateCommon()._build_payloads_to_commit() appends the payload in
        FabricUpdateBulk.payloads to FabricUpdate()._payloads_to_commit
    -   FabricUpdateBulk.commit() updates the following:
        -   instance.results.diff_current to an empty dict
        -   instance.results.response_current a synthesized response dict
            { "RETURN_CODE": 200, "MESSAGE": "No fabrics to update." }
        -  instance.results.result_current to a synthesized result dict
           {"success": True, "changed": False}
    -   FabricUpdateBulk.commit() calls FabricUpdateCommon()._send_payloads()
    -   FabricUpdateCommon()._send_payloads() calls
        FabricUpdateCommon()._build_fabrics_to_config_deploy()
    -   FabricUpdateCommon()._build_fabrics_to_config_deploy() calls
        FabricUpdateCommon()._can_be_deployed()
    -   FabricUpdateCommon()._can_be_deployed() calls
        FabricSummary().refresh() and then references
        FabricSummary().fabric_is_empty to determine if the fabric is empty.
        If the fabric is empty, it can be deployed, otherwise it cannot.
        Hence, _can_be_deployed() returns either True or False.
        In this testcase, the fabric is empty, so _can_be_deployed() returns True.
    -   FabricUpdateCommon()._build_fabrics_to_config_deploy() appends fabric f1 to both:
        -   FabricUpdateCommon()._fabrics_to_config_deploy
        -   FabricUpdateCommon()._fabrics_to_config_save
    -   FabricUpdateCommon()._send_payloads() calls
        FabricUpdateCommon()._fixup_payloads_to_commit()
    -   FabricUpdateCommon()._fixup_payloads_to_commit() updates ANYCAST_GW_MAC,
        if present, to conform with the controller's requirements.
    -   FabricUpdateCommon()._send_payloads() calls
        FabricUpdateCommon()._send_payload() for each fabric in
        FabricUpdateCommon()._payloads_to_commit

    """
    key = "test_fabric_update_bulk_00031a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details(key)
        yield responses_fabric_summary(key)
        yield responses_fabric_update_bulk(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_update_bulk

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.results = Results()
        instance.payloads = payloads_fabric_update_bulk(key)

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

    assert instance.results.metadata[0].get("action", None) == "update"
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
    assert instance.results.response[0].get("METHOD", None) == "PUT"

    assert instance.results.result[0].get("changed", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert True in instance.results.changed
    assert False not in instance.results.changed


def test_fabric_update_bulk_00032(monkeypatch, fabric_update_bulk) -> None:
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
    - FabricQuery
        - __init__()
        - fabric_names setter
        - commit()
    - FabricUpdateBulk()
        - __init__()
        - commit()

    Summary
    Verify behavior when user attempts to update a fabric and the
    fabric exists on the controller but the RestSend() RETURN_CODE is 500.

    Code Flow
    -   FabricUpdateBulk.payloads is set to contain one payload for a fabric (f1)
        that exists on the controller.
    -   FabricUpdateBulk.commit() calls FabricUpdateCommon()._build_payloads_to_commit()
    -   FabricUpdateCommon()._build_payloads_to_commit() calls FabricDetails().refresh()
        which returns a dict with fabric f1 information and RETURN_CODE == 200
    -   FabricUpdateCommon()._build_payloads_to_commit() calls
        FabricUpdateCommon()._fabric_needs_update() which updates:
        -   Results().result_current to add a synthesized failed result dict
        -   Results().changed adding False
        -   Results().failed adding True
        -   Results().failed_result to add a message indicating the reason for the failure
        And calls Results().register_task_result()
        It raises ValueError because the payload contains an invalid key.
    """
    key = "test_fabric_update_bulk_00032a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details(key)
        yield responses_fabric_summary(key)
        yield responses_fabric_update_bulk(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_update_bulk

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())

        instance.results = Results()
        instance.payloads = payloads_fabric_update_bulk(key)
        instance.fabric_details.rest_send.unit_test = True
        instance.rest_send.unit_test = True

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    match = r"FabricUpdateBulk\._fabric_needs_update: Invalid key:.*found in payload for fabric.*"

    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1

    assert instance.results.metadata[0].get("action", None) == "update"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "merged"

    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is False

    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_update_bulk_00033(monkeypatch, fabric_update_bulk) -> None:
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
    - FabricQuery
        - __init__()
        - fabric_names setter
        - commit()
    - FabricUpdateBulk()
        - __init__()
        - commit()

    Summary
    Verify behavior when user attempts to update a fabric when the payload
    includes ANYCAST_GW_MAC, formatted to be incompatible with the controller's
    expectations, and not able to be fixed by
    FabricUpdateCommon()._fixup_payloads_to_commit().

    Setup
    -   FabricUpdateBulk().payloads is set to contain one payload for a fabric (f1)
        that exists on the controller, and the payload includes ANYCAST_GW_MAC
        formatted to be incompatible with the controller's expectations.

    Code Flow
    -   FabricUpdateBulk.payloads is set to contain one payload for a fabric (f1)
        that exists on the controller.
    -   FabricUpdateBulk.commit() calls FabricUpdateCommon()._build_payloads_to_commit()
    -   FabricUpdateCommon()._build_payloads_to_commit() calls
        FabricUpdateCommon()._fabric_needs_update()
    -   FabricUpdateCommon()._fabric_needs_update() calls
        FabricUpdateCommon()._prepare_anycast_gw_mac_for_comparison() because ANYCAST_GW_MAC
        key is present in the payload.
    -   FabricUpdateCommon()._prepare_anycast_gw_mac_for_comparison():
        -   Updates Results()
        -   raises ValueError because the mac address is not convertable.
    """
    key = "test_fabric_update_bulk_00033a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details(key)
        yield responses_fabric_summary(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_update_bulk

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())

        instance.results = Results()
        instance.payloads = payloads_fabric_update_bulk(key)
        instance.fabric_details.rest_send.unit_test = True

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)
    match = r"FabricUpdateBulk\._prepare_anycast_gw_mac_for_comparison: "
    match += r"Error translating ANYCAST_GW_MAC"
    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1

    assert instance.results.metadata[0].get("action", None) == "update"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "merged"

    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert False in instance.results.changed
