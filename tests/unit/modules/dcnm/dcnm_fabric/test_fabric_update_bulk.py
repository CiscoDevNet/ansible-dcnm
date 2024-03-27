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
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import \
    AnsibleFailJson
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    GenerateResponses, does_not_raise, fabric_update_bulk_fixture, payloads_fabric_update_bulk,
    responses_fabric_update_bulk, responses_fabric_details, responses_fabric_summary,
    rest_send_response_current)


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

    Test
    - payloads is set to expected value
    - fail_json is not called
    """
    key = "test_fabric_update_bulk_00020a"
    with does_not_raise():
        instance = fabric_update_bulk
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

    Test
    - fail_json is called because payloads is not a list
    - instance.payloads is not modified, hence it retains its initial value of None
    """
    match = r"FabricUpdateBulk\.payloads: "
    match += r"payloads must be a list of dict\."

    with does_not_raise():
        instance = fabric_update_bulk
        instance.results = Results()
    with pytest.raises(AnsibleFailJson, match=match):
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

    Test
    - fail_json is called because payloads is a list with a non-dict element
    - instance.payloads is not modified, hence it retains its initial value of None
    """
    match = r"FabricUpdateBulk._verify_payload: "
    match += r"payload must be a dict\."

    with does_not_raise():
        instance = fabric_update_bulk
        instance.results = Results()
    with pytest.raises(AnsibleFailJson, match=match):
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
    Verify behavior when payloads is not set prior to calling commit

    Test
    - fail_json is called because payloads is not set prior to calling commit
    - instance.payloads is not modified, hence it retains its initial value of None
    """
    match = r"FabricUpdateBulk\.commit: "
    match += r"payloads must be set prior to calling commit\."

    with does_not_raise():
        instance = fabric_update_bulk
        instance.results = Results()
    with pytest.raises(AnsibleFailJson, match=match):
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
    Verify behavior when payloads is set to an empty list

    Setup
    -   FabricUpdatebulk().payloads is set to an empty list

    Test
    -   fail_json not called
    -   payloads is set to an empty list

    NOTES:
    -   element_spec is configured such that AnsibleModule will raise an exception when
        config is not a list of dict.  Hence, we do not test instance.commit() here since
        it would never be reached.
    """
    with does_not_raise():
        instance = fabric_update_bulk
        instance.results = Results()
        instance.payloads = []
    assert instance.payloads == []


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

    gen = GenerateResponses(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_update_bulk
        instance.results = Results()
        instance.payloads = payloads_fabric_update_bulk(key)
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

    assert instance.results.metadata[0].get("action", None) == "update"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "merged"

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.response[0].get("MESSAGE", None) == "No fabrics to update."

    assert instance.results.result[0].get("changed", None) == False
    assert instance.results.result[0].get("success", None) == True

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
    Verify behavior when user attempts to update a fabric and the
    fabric exists on the controller and the RestSend() RETURN_CODE is 200.
    The fabric payload includes ANYCAST_GW_MAC, formatted to be incompatible
    with the controller's requirements, but able to be fixed by
    FabricUpdateCommon()._fixup_payloads_to_commit().

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
    -   FabricUpdateCommon()._send_payloads() calls FabricUpdateCommon()._build_fabrics_to_config_deploy()
    -   FabricUpdateCommon()._build_fabrics_to_config_deploy() calls FabricUpdateCommon()._can_be_deployed()
    -   FabricUpdateCommon()._can_be_deployed() calls FabricSummary().refresh() and then references
        FabricSummary().fabric_is_empty to determine if the fabric is empty.  If the fabric is empty,
        it can be deployed, otherwise it cannot.  Hence, _can_be_deployed() returns either True or False.
        In this testcase, the fabric is empty, so _can_be_deployed() returns True.
    -   FabricUpdateCommon()._build_fabrics_to_config_deploy() appends fabric f1 to both:
        -   FabricUpdateCommon()._fabrics_to_config_deploy
        -   FabricUpdateCommon()._fabrics_to_config_save
    -   FabricUpdateCommon()._send_payloads() calls FabricUpdateCommon()._fixup_payloads_to_commit()
    -   FabricUpdateCommon()._fixup_payloads_to_commit() updates ANYCAST_GW_MAC, if present, to
        conform with the controller's requirements.
    -   FabricUpdateCommon()._send_payloads() calls FabricUpdateCommon()._send_payload() for each
        fabric in FabricUpdateCommon()._payloads_to_commit

    """
    key = "test_fabric_update_bulk_00031a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details(key)
        yield responses_fabric_summary(key)
        yield responses_fabric_update_bulk(key)

    gen = GenerateResponses(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_update_bulk
        instance.results = Results()
        instance.payloads = payloads_fabric_update_bulk(key)
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

    assert instance.results.metadata[0].get("action", None) == "update"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "merged"

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.response[0].get("DATA", {}).get("nvPairs", {}).get("BGP_AS", None) == "65001"
    assert instance.results.response[0].get("METHOD", None) == "PUT"

    assert instance.results.result[0].get("changed", None) == True
    assert instance.results.result[0].get("success", None) == True

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
    -   FabricUpdateCommon()._build_payloads_to_commit() appends the payload in
        FabricUpdateBulk.payloads to FabricUpdatee()._payloads_to_commit
    -   FabricUpdateBulk.commit() updates the following:
        -   instance.results.diff_current to an empty dict
        -   instance.results.response_current a synthesized response dict
            { "RETURN_CODE": 200, "MESSAGE": "No fabrics to update." }
        -  instance.results.result_current to a synthesized result dict
           {"success": True, "changed": False}
    -   FabricUpdateBulk.commit() calls FabricUpdateCommon()._send_payloads()
    -   FabricUpdateCommon()._send_payloads() calls FabricUpdateCommon()._build_fabrics_to_config_deploy()
    -   FabricUpdateCommon()._build_fabrics_to_config_deploy() calls FabricUpdateCommon()._can_be_deployed()
    -   FabricUpdateCommon()._can_be_deployed() calls FabricSummary().refresh() and then references
        FabricSummary().fabric_is_empty to determine if the fabric is empty.  If the fabric is empty,
        it can be deployed, otherwise it cannot.  Hence, _can_be_deployed() returns either True or False.
        In this testcase, the fabric is empty, so _can_be_deployed() returns True.
    -   FabricUpdateCommon()._build_fabrics_to_config_deploy() appends fabric f1 to both:
        -   FabricUpdateCommon()._fabrics_to_config_deploy
        -   FabricUpdateCommon()._fabrics_to_config_save
    -   FabricUpdateCommon()._send_payloads() calls FabricUpdateCommon()._fixup_payloads_to_commit()
    -   FabricUpdateCommon()._fixup_payloads_to_commit() updates ANYCAST_GW_MAC, if present, to
        conform with the controller's requirements.
    -   FabricUpdateCommon()._send_payloads() calls FabricUpdateCommon()._send_payload() for each
        fabric in FabricUpdateCommon()._payloads_to_commit

    """
    key = "test_fabric_update_bulk_00032a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details(key)
        yield responses_fabric_summary(key)
        yield responses_fabric_update_bulk(key)

    gen = GenerateResponses(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_update_bulk
        instance.results = Results()
        instance.payloads = payloads_fabric_update_bulk(key)
        instance.fabric_details.rest_send.unit_test = True

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)
    with does_not_raise():
        instance.rest_send.unit_test = True
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

    assert instance.results.response[0].get("RETURN_CODE", None) == 500
    error_message = "Failed to update the fabric, due to invalid field [BOO] "
    error_message += f"in payload, please provide valid fields for fabric-settings"
    assert instance.results.response[0].get("DATA", None) == error_message
    assert instance.results.response[0].get("METHOD", None) == "PUT"
    assert instance.results.response[0].get("MESSAGE", None) == "Internal Server Error"

    assert instance.results.result[0].get("changed", None) == False
    assert instance.results.result[0].get("success", None) == False

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
    Verify behavior when user attempts to update a fabric and the
    fabric exists on the controller and the RestSend() RETURN_CODE is 500.
    The fabric payload includes ANYCAST_GW_MAC, formatted to be incompatible
    with the controller's requirements, and not able to be fixed by
    FabricUpdateCommon()._fixup_payloads_to_commit().

    Code Flow
    -   FabricUpdateBulk.payloads is set to contain one payload for a fabric (f1)
        that exists on the controller.
    -   FabricUpdateBulk.commit() calls FabricUpdateCommon()._build_payloads_to_commit()
    -   FabricUpdateCommon()._build_payloads_to_commit() calls FabricDetails().refresh()
        which returns a dict with fabric f1 information and RETURN_CODE == 200
    -   FabricUpdateCommon()._build_payloads_to_commit() appends the payload in
        FabricUpdateBulk.payloads to FabricUpdate()._payloads_to_commit
    -   FabricUpdateBulk.commit() updates the following:
        -   instance.results.action to self.action
        -   instance.results.state to self.state
        -   instance.results.check_mode to self.check_mode
    -   FabricUpdateBulk.commit() calls FabricUpdateCommon()._send_payloads()
    -   FabricUpdateCommon()._send_payloads() calls FabricUpdateCommon()._build_fabrics_to_config_deploy()
    -   FabricUpdateCommon()._build_fabrics_to_config_deploy() calls FabricUpdateCommon()._can_be_deployed()
    -   FabricUpdateCommon()._can_be_deployed() calls FabricSummary().refresh() and then references
        FabricSummary().fabric_is_empty to determine if the fabric is empty.  If the fabric is empty,
        it can be deployed, otherwise it cannot.  Hence, _can_be_deployed() returns either True or False.
        In this testcase, the fabric is empty, so _can_be_deployed() returns True.
    -   FabricUpdateCommon()._build_fabrics_to_config_deploy() appends fabric f1 to both:
        -   FabricUpdateCommon()._fabrics_to_config_deploy
        -   FabricUpdateCommon()._fabrics_to_config_save
    -   FabricUpdateCommon()._send_payloads() calls FabricUpdateCommon()._fixup_payloads_to_commit()
    -   FabricCommon()._fixup_payloads_to_commit() calls FabricCommon().translate_mac_address()
        to update ANYCAST_GW_MAC to conform with the controller's requirements, but the
        mac address is not convertable, so translate_mac_address() raises a ValueError.
    -   Responding to the ValueError FabricCommon()._fixup_payloads_to_commit() takes the except
        path of its try/except block, which:
        -   Updates results and calls results.register_task_result()
        -   Calls fail_json()

    """
    key = "test_fabric_update_bulk_00033a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details(key)
        yield responses_fabric_summary(key)

    gen = GenerateResponses(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_update_bulk
        instance.results = Results()
        instance.payloads = payloads_fabric_update_bulk(key)
        instance.fabric_details.rest_send.unit_test = True

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)
    match = r"FabricUpdateBulk\._fixup_payloads_to_commit: "
    match += r"Error translating ANYCAST_GW_MAC"
    with pytest.raises(AnsibleFailJson, match=match):
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