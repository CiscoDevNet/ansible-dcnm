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
    responses_config_deploy, responses_config_save,
    responses_fabric_details_by_name, responses_fabric_summary,
    responses_fabric_update_bulk)


def test_fabric_update_bulk_00010(fabric_update_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
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
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

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
    -   ``ValueError`` is raised because payloads is not set
        prior to calling commit
    -   instance.payloads retains its initial value of None
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
    -   element_spec in dcnm_fabric.py.main() is configured such that
        AnsibleModule will raise an exception when config is not a list
        of dict.  Hence, we do not test instance.commit() here since it
        would never be reached.
    """
    with does_not_raise():
        instance = fabric_update_bulk
        instance.results = Results()
        instance.payloads = []
    assert instance.payloads == []


@pytest.mark.parametrize(
    "mandatory_key",
    ["BGP_AS", "DEPLOY", "FABRIC_NAME", "FABRIC_TYPE"],
)
def test_fabric_update_bulk_00025(fabric_update_bulk, mandatory_key) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricUpdateBulk
        - __init__()

    Summary
    -   Verify ``ValueError`` is raised when payloads is missing mandatory keys.
    -   Verify instance.payloads retains its initial value of None.

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_update_bulk
        instance.fabric_details = FabricDetailsByName(params)
        instance.results = Results()

    payloads = payloads_fabric_update_bulk(key)
    payloads[0].pop(mandatory_key, None)

    match = r"FabricUpdateBulk\._verify_payload: "
    match += r"payload is missing mandatory keys:"
    with pytest.raises(ValueError, match=match):
        instance.payloads = payloads
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
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
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
    -   Verify behavior when user requests to update a fabric and the
        fabric exists on the controller and the payload contains
        values that would result in changes to the fabric.
    -   The fabric payload includes ANYCAST_GW_MAC, formatted to be incompatible
        with the controller's requirements, but able to be fixed by
        FabricUpdateCommon()._fixup_payloads_to_commit().
    -   The fabric payload also contains keys that include ``bool`
        and ``int`` values.
    -   The fabric is empty, so is updated, but not deployed/saved.

    See Also
    -   test_fabric_update_bulk_00035 for case where fabric is not empty.

    Code Flow
    -   FabricUpdateBulk.payloads is set to contain one payload for a fabric
        (f1) that exists on the controller.
    -   The payload keys contain values that would result in changes to
        the fabric.
    -   FabricUpdateBulk.commit() calls
        FabricUpdateCommon()._build_payloads_to_commit()
    -   FabricUpdateCommon()._build_payloads_to_commit() calls
        FabricDetails().refresh() which returns a dict with fabric f1
        information and RETURN_CODE == 200
    -   FabricUpdateCommon()._build_payloads_to_commit() sets
        _fabric_update_required to an empty set() and calls
        FabricUpdateCommon()._fabric_needs_update() with the payload.
    -   FabricUpdateCommon()._fabric_needs_update() updates compares the
        payload to the fabric details and determines that changes are
        required.  Hence, it adds True to _fabric_update_required.
    -   FabricUpdateCommon()._build_payloads_to_commit() finds True in
        _fabric_update_required and appends the payload to the
        _payloads_to_commit list.
    -   FabricUpdateBulk.commit() calls FabricUpdateCommon()._send_payloads()
    -   FabricUpdateCommon()._send_payloads() calls
        FabricUpdateCommon()._build_fabrics_to_config_deploy()
    -   FabricUpdateCommon()._build_fabrics_to_config_deploy() calls
        FabricUpdateCommon()._can_fabric_be_deployed()
    -   FabricUpdateCommon()._can_fabric_be_deployed() calls
        FabricSummary().refresh() and then references
        FabricSummary().fabric_is_empty to determine if the fabric is empty.
        If the fabric is empty, it cannot be deployed, otherwise it can.
        Hence, _can_fabric_be_deployed() returns either True or False.
        In this testcase, the fabric is empty, so _can_fabric_be_deployed()
        returns False.
    -   FabricUpdateCommon()._send_payloads() calls
        FabricUpdateCommon()._fixup_payloads_to_commit()
    -   FabricUpdateCommon()._fixup_payloads_to_commit() updates ANYCAST_GW_MAC
        to conform with the controller's requirements.
    -   FabricUpdateCommon()._send_payloads() calls
        FabricUpdateCommon()._send_payload() for each fabric in
        FabricUpdateCommon()._payloads_to_commit
    -   FabricUpdateCommon()._send_payload() calls
        FabricUpdateCommon()._config_save() if no errors were encountered during
        the fabric update.
    -   FabricUpdateCommon()._config_save() returns without saving since fabric f1
        is not in list FabricUpdateCommon()._fabrics_to_config_save
    -   FabricUpdateCommon()._send_payload() calls
        FabricUpdateCommon()._config_deploy() if no errors were encountered during
        the fabric update or the config_save.
    -   FabricUpdateCommon()._config_deploy() returns without deploying since
        fabric f1 is not in list FabricUpdateCommon()._fabrics_to_config_deploy
    -   FabricUpdateBulk.commit() returns.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
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

    assert instance.results.diff[0].get("ANYCAST_GW_MAC", None) == "0001.aabb.ccdd"
    assert instance.results.diff[0].get("FABRIC_NAME", None) == "f1"
    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[0].get("VPC_DELAY_RESTORE_TIME", None) == "300"

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
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
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
    -   Verify behavior when user attempts to update a fabric when the payload
        includes ANYCAST_GW_MAC, formatted to be incompatible with the
        controller's expectations, and not able to be fixed by
        FabricUpdateCommon()._fixup_payloads_to_commit().

    Setup
    -   FabricUpdateBulk().payloads is set to contain one payload for a fabric
        (f1) that exists on the controller, and the payload includes
        ANYCAST_GW_MAC formatted to be incompatible with the controller's
        expectations.

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
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
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


def test_fabric_update_bulk_00034(monkeypatch, fabric_update_bulk) -> None:
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
    -   Idempotence test.
    -   Verify behavior when user requests to update a fabric and the
        fabric exists on the controller but the payload does not contain
        any values that would result in changes to the fabric.

    Code Flow
    -   FabricUpdateBulk.payloads is set to contain one payload for a fabric
        (f1) that exists on the controller.
    -   The payload key/values do not contain any values that would result
        in changes to the fabric.
    -   FabricUpdateBulk.commit() calls
        FabricUpdateCommon()._build_payloads_to_commit()
    -   FabricUpdateCommon()._build_payloads_to_commit() calls
        FabricDetails().refresh() which returns a dict with fabric f1
        information and RETURN_CODE == 200
    -   FabricUpdateCommon()._build_payloads_to_commit() sets
        _fabric_update_required to an empty set() and calls
        FabricUpdateCommon()._fabric_needs_update() with the payload.
    -   FabricUpdateCommon()._fabric_needs_update() compares the
        payload to the fabric details and determines that no changes are
        required.  Hence, it does not update _fabric_update_required set().
    -   FabricUpdateCommon()._build_payloads_to_commit() returns without
        adding the fabric to the _payloads_to_commit list.
    -   FabricUpdateBulk.commit() updates the following, since the
        _payloads_to_commit list is empty:
        -   instance.results.diff_current to an empty dict
        -   instance.results.response_current a synthesized response dict
            { "RETURN_CODE": 200, "MESSAGE": "No fabrics to update." }
        -  instance.results.result_current to a synthesized result dict
           {"success": True, "changed": False}
    -   FabricUpdateBulk.commit() returns
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
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

    assert instance.results.metadata[0].get("action", None) == "update"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "merged"

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.response[0].get("MESSAGE", None) == "No fabrics to update."
    assert instance.results.response[0].get("sequence_number", None) == 1

    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is True
    assert instance.results.result[0].get("sequence_number", None) == 1

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_update_bulk_00035(monkeypatch, fabric_update_bulk) -> None:
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
    -   Verify behavior when user requests to update a fabric and the
        fabric exists on the controller and the payload contains
        values that would result in changes to the fabric.
    -   The fabric payload includes ANYCAST_GW_MAC, formatted to be incompatible
        with the controller's requirements, but able to be fixed by
        FabricUpdateCommon()._fixup_payloads_to_commit().
    -   The fabric payload also contains keys that include ``bool`
        and ``int`` values.
    -   The fabric is not empty, so is also deployed/saved.

    See Also
    -   test_fabric_update_bulk_00031 for case where fabric is empty.

    Code Flow
    -   FabricUpdateBulk.payloads is set to contain one payload for a fabric
        (f1) that exists on the controller.
    -   The payload keys contain values that would result in changes to
        the fabric.
    -   FabricUpdateBulk.commit() calls
        FabricUpdateCommon()._build_payloads_to_commit()
    -   FabricUpdateCommon()._build_payloads_to_commit() calls
        FabricDetails().refresh() which returns a dict with fabric f1
        information and RETURN_CODE == 200
    -   FabricUpdateCommon()._build_payloads_to_commit() sets
        _fabric_update_required to an empty set() and calls
        FabricUpdateCommon()._fabric_needs_update() with the payload.
    -   FabricUpdateCommon()._fabric_needs_update() updates compares the
        payload to the fabric details and determines that changes are
        required.  Hence, it adds True to _fabric_update_required.
    -   FabricUpdateCommon()._build_payloads_to_commit() finds True in
        _fabric_update_required and appends the payload to the
        _payloads_to_commit list.
    -   FabricUpdateBulk.commit() calls FabricUpdateCommon()._send_payloads()
    -   FabricUpdateCommon()._send_payloads() calls
        FabricUpdateCommon()._build_fabrics_to_config_deploy()
    -   FabricUpdateCommon()._build_fabrics_to_config_deploy() calls
        FabricUpdateCommon()._can_fabric_be_deployed()
    -   FabricUpdateCommon()._can_fabric_be_deployed() calls
        FabricSummary().refresh() and then references
        FabricSummary().fabric_is_empty to determine if the fabric is empty.
        If the fabric is empty, it cannot be deployed, otherwise it can.
        Hence, _can_fabric_be_deployed() returns either True or False.
        In this testcase, the fabric is not empty, so _can_fabric_be_deployed()
        returns True.
    -   FabricUpdateCommon()._send_payloads() calls
        FabricUpdateCommon()._fixup_payloads_to_commit()
    -   FabricUpdateCommon()._fixup_payloads_to_commit() updates ANYCAST_GW_MAC
        to conform with the controller's requirements.
    -   FabricUpdateCommon()._send_payloads() calls
        FabricUpdateCommon()._send_payload() for each fabric in
        FabricUpdateCommon()._payloads_to_commit
    -   FabricUpdateCommon()._send_payload() calls
        FabricUpdateCommon()._config_save() if no errors were encountered during
        the fabric update.
    -   FabricUpdateCommon()._config_save() performs a config_save on fabric f1
        since it is in list FabricUpdateCommon()._fabrics_to_config_save.
    -   FabricUpdateCommon()._send_payload() calls
        FabricUpdateCommon()._config_deploy() if no errors were encountered during
        the fabric update or the config_save.
    -   FabricUpdateCommon()._config_deploy() deploys fabric f1 since it is in
        list FabricUpdateCommon()._fabrics_to_config_deploy
    -   FabricUpdateBulk.commit() returns.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
        yield responses_fabric_summary(key)
        yield responses_fabric_update_bulk(key)
        yield responses_config_save(key)
        yield responses_config_deploy(key)

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

    assert len(instance.results.diff) == 3
    assert len(instance.results.metadata) == 3
    assert len(instance.results.response) == 3
    assert len(instance.results.result) == 3

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[0].get("VPC_DELAY_RESTORE_TIME", None) == "300"
    assert instance.results.diff[0].get("ANYCAST_GW_MAC", None) == "0001.aabb.ccdd"

    assert instance.results.diff[1].get("sequence_number", None) == 2
    assert instance.results.diff[1].get("config_save", None) == "OK"
    assert instance.results.diff[1].get("FABRIC_NAME", None) == "f1"

    assert instance.results.diff[2].get("sequence_number", None) == 3
    assert instance.results.diff[2].get("config_deploy", None) == "OK"
    assert instance.results.diff[2].get("FABRIC_NAME", None) == "f1"

    assert instance.results.metadata[0].get("action", None) == "update"
    assert instance.results.metadata[1].get("action", None) == "config_save"
    assert instance.results.metadata[2].get("action", None) == "config_deploy"

    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[1].get("check_mode", None) is False
    assert instance.results.metadata[2].get("check_mode", None) is False

    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[1].get("sequence_number", None) == 2
    assert instance.results.metadata[2].get("sequence_number", None) == 3

    assert instance.results.metadata[0].get("state", None) == "merged"
    assert instance.results.metadata[1].get("state", None) == "merged"
    assert instance.results.metadata[2].get("state", None) == "merged"

    assert instance.results.response[0].get("sequence_number", None) == 1
    assert instance.results.response[1].get("sequence_number", None) == 2
    assert instance.results.response[2].get("sequence_number", None) == 3

    assert instance.results.response[0].get("METHOD", None) == "PUT"
    assert instance.results.response[1].get("METHOD", None) == "POST"
    assert instance.results.response[2].get("METHOD", None) == "POST"

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.response[1].get("RETURN_CODE", None) == 200
    assert instance.results.response[2].get("RETURN_CODE", None) == 200

    assert (
        instance.results.response[0]
        .get("DATA", {})
        .get("nvPairs", {})
        .get("VPC_DELAY_RESTORE_TIME", None)
        == "300"
    )

    assert (
        instance.results.response[0]
        .get("DATA", {})
        .get("nvPairs", {})
        .get("ANYCAST_GW_MAC", None)
        == "0001.aabb.ccdd"
    )

    assert (
        instance.results.response[1].get("DATA", {}).get("status", None)
        == "Config save is completed"
    )

    assert (
        instance.results.response[2].get("DATA", {}).get("status", None)
        == "Configuration deployment completed."
    )

    assert instance.results.result[0].get("changed", None) is True
    assert instance.results.result[1].get("changed", None) is True
    assert instance.results.result[2].get("changed", None) is True

    assert instance.results.result[0].get("success", None) is True
    assert instance.results.result[1].get("success", None) is True
    assert instance.results.result[2].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert True in instance.results.changed
    assert False not in instance.results.changed


def test_fabric_update_bulk_00040(monkeypatch, fabric_update_bulk) -> None:
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
        - _can_fabric_be_deployed()

    Summary
    -   Verify behavior when user attempts to update a fabric which
        exists on the controller, but a ``ControllerResponseError``
        is raised by FabricSummary().refresh() when called from
        FabricUpdateBulk()._can_fabric_be_deployed().

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
        FabricUpdateCommon()._can_fabric_be_deployed()
    -   FabricUpdateCommon()._can_fabric_be_deployed() calls
        FabricSummary().refresh() which raises ``ControllerResponseError``.
    -   FabricUpdateCommon()._can_fabric_be_deployed() re-raises the exception
        as a ``ValueError``.
    -   FabricUpdateCommon()._build_fabrics_to_config_deploy()
        re-raises the ``ValueError``.
    -   FabricUpdateCommon()._send_payloads() re-raises the ``ValueError``.
    -   FabricUpdateBulk.commit() re-raises the ``ValueError``.

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
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

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)
    match = r"FabricSummary\._verify_controller_response:\s+"
    match += r"Failed to retrieve fabric_summary for fabric_name f1.\s+"
    match += r"RETURN_CODE: 404.\s+"
    match += r"MESSAGE: Not Found."
    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

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


def test_fabric_update_bulk_00050(fabric_update_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricUpdateBulk()
        - __init__()
        - commit()

    Summary
    -   Verify commit() raises ``ValueError`` if ``fabric_details`` is not set.
    """
    with does_not_raise():
        instance = fabric_update_bulk

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.results = Results()
        instance.payloads = [
            {
                "BGP_AS": "65001",
                "DEPLOY": "true",
                "FABRIC_NAME": "f1",
                "FABRIC_TYPE": "VXLAN_EVPN",
            }
        ]

    match = r"FabricUpdateBulk\.commit:\s+"
    match += r"fabric_details must be set prior to calling commit\."
    with pytest.raises(ValueError, match=match):
        fabric_update_bulk.commit()


def test_fabric_update_bulk_00060(fabric_update_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricUpdateBulk()
        - __init__()
        - commit()

    Summary
    -   Verify commit() raises ``ValueError`` if ``fabric_summary`` is not set.
    """
    with does_not_raise():
        instance = fabric_update_bulk

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.results = Results()
        instance.payloads = [
            {
                "BGP_AS": "65001",
                "DEPLOY": "true",
                "FABRIC_NAME": "f1",
                "FABRIC_TYPE": "VXLAN_EVPN",
            }
        ]

    match = r"FabricUpdateBulk\.commit:\s+"
    match += r"fabric_summary must be set prior to calling commit\."
    with pytest.raises(ValueError, match=match):
        fabric_update_bulk.commit()


def test_fabric_update_bulk_00070(fabric_update_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricUpdateBulk()
        - __init__()
        - commit()

    Summary
    -   Verify commit() raises ``ValueError`` if ``rest_send`` is not set.
    """
    with does_not_raise():
        instance = fabric_update_bulk

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.results = Results()
        instance.payloads = [
            {
                "BGP_AS": "65001",
                "DEPLOY": "true",
                "FABRIC_NAME": "f1",
                "FABRIC_TYPE": "VXLAN_EVPN",
            }
        ]

    match = r"FabricUpdateBulk\.commit:\s+"
    match += r"rest_send must be set prior to calling commit\."
    with pytest.raises(ValueError, match=match):
        fabric_update_bulk.commit()


def test_fabric_update_bulk_00080(monkeypatch, fabric_update_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricUpdateBulk()
        - __init__()
        - _config_deploy()

    Summary
    -   Verify _config_deploy() re-raises ``ValueError`` raised by ApiEndpoints().
    """
    class MockApiEndpoints:  # pylint: disable=too-few-public-methods
        """
        Mock the ApiEndpoints.fabric_name() setter to raise ``ValueError``.
        """
        @property
        def fabric_name(self):
            """
            Mocked method
            """
            return "f1"
        @fabric_name.setter
        def fabric_name(self, value):
            raise ValueError("mocked exception")

    with does_not_raise():
        instance = fabric_update_bulk

        instance.endpoints = MockApiEndpoints()

        instance._fabrics_to_config_deploy = ["f1"]
        instance.config_save_result = {"f1": True}

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.results = Results()
        instance.payloads = [
            {
                "BGP_AS": "65001",
                "DEPLOY": "true",
                "FABRIC_NAME": "f1",
                "FABRIC_TYPE": "VXLAN_EVPN",
            }
        ]

    match = "mocked exception"
    with pytest.raises(ValueError, match=match):
        fabric_update_bulk._config_deploy()
