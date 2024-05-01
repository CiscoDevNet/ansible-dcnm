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
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_summary import \
    FabricSummary
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_types import \
    FabricTypes
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.param_info import \
    ParamInfo
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.ruleset import \
    RuleSet
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.template_get import \
    TemplateGet
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.verify_playbook_params import \
    VerifyPlaybookParams
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, does_not_raise, fabric_replaced_bulk_fixture, params,
    payloads_fabric_replaced_bulk, responses_config_deploy,
    responses_config_save, responses_fabric_details_by_name,
    responses_fabric_replaced_bulk, responses_fabric_summary)


def test_fabric_replaced_bulk_00010(fabric_replaced_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_summary = FabricSummary(params)
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.results = Results()
    assert instance.class_name == "FabricReplacedBulk"
    assert instance.action == "replace"
    assert instance.path is None
    assert instance.verb is None
    assert instance.state == "replaced"
    assert instance._fabrics_to_config_deploy == []
    assert isinstance(instance.endpoints, ApiEndpoints)
    assert isinstance(instance.fabric_details, FabricDetailsByName)
    assert isinstance(instance.fabric_summary, FabricSummary)
    assert isinstance(instance.fabric_types, FabricTypes)
    assert isinstance(instance.param_info, ParamInfo)
    assert isinstance(instance.rest_send, RestSend)
    assert isinstance(instance.results, Results)
    assert isinstance(instance.ruleset, RuleSet)
    assert isinstance(instance.template_get, TemplateGet)
    assert isinstance(instance.verify_playbook_params, VerifyPlaybookParams)


def test_fabric_replaced_bulk_00020(fabric_replaced_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricReplacedBulk
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
        instance = fabric_replaced_bulk
        instance.fabric_details = FabricDetailsByName(params)
        instance.results = Results()
        instance.payloads = payloads_fabric_replaced_bulk(key)
    assert instance.payloads == payloads_fabric_replaced_bulk(key)


def test_fabric_replaced_bulk_00021(fabric_replaced_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricReplacedBulk
        - __init__()

    Summary
    ``payloads`` setter is presented with input that is not a list.

    Test
    - ``ValueError`` is raised because payloads is not a list
    - instance.payloads retains its initial value of None
    """
    match = r"FabricReplacedBulk\.payloads: "
    match += r"payloads must be a list of dict\."

    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.fabric_details = FabricDetailsByName(params)
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.payloads = "NOT_A_LIST"
    assert instance.payloads is None


def test_fabric_replaced_bulk_00022(fabric_replaced_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricReplacedBulk
        - __init__()

    Summary
    ``payloads`` setter is presented with a list that contains a non-dict element.

    Test
    - ``ValueError`` is raised because payloads is a list with non-dict elements
    - instance.payloads retains its initial value of None
    """
    match = r"FabricReplacedBulk._verify_payload:\s+"
    match += r"Playbook configuration for fabrics must be a dict\.\s+"
    match += r"Got type int, value 1\."

    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.fabric_details = FabricDetailsByName(params)
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.payloads = [1, 2, 3]
    assert instance.payloads is None


def test_fabric_replaced_bulk_00023(fabric_replaced_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricReplacedBulk
        - __init__()

    Summary
    payloads is not set prior to calling commit

    Test
    -   ``ValueError`` is raised because payloads is not set
        prior to calling commit
    -   instance.payloads retains its initial value of None
    """
    match = r"FabricReplacedBulk\.commit: "
    match += r"payloads must be set prior to calling commit\."

    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_summary = FabricSummary(params)
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.commit()
    assert instance.payloads is None


def test_fabric_replaced_bulk_00024(fabric_replaced_bulk) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricReplacedBulk
        - __init__()

    Summary
    payloads is set to an empty list

    Setup
    -   FabricReplacedBulk().payloads is set to an empty list

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
        instance = fabric_replaced_bulk
        instance.results = Results()
        instance.payloads = []
    assert instance.payloads == []


@pytest.mark.parametrize(
    "mandatory_parameter",
    ["BGP_AS", "FABRIC_NAME", "FABRIC_TYPE"],
)
def test_fabric_replaced_bulk_00025(fabric_replaced_bulk, mandatory_parameter) -> None:
    """
    Classes and Methods
    - FabricReplacedCommon
        - __init__()
        - payloads setter
    - FabricReplacedBulk
        - __init__()

    Summary
    -   Verify FabricReplacedCommon().payloads setter re-raises ``ValueError``
        raised by FabricCommon()._verify_payload() when payloads is missing
        mandatory keys.
    -   Verify instance.payloads retains its initial value of None.

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.results = Results()

    payloads = payloads_fabric_replaced_bulk(key)
    payloads[0].pop(mandatory_parameter, None)
    payloads[1].pop(mandatory_parameter, None)
    payloads[2].pop(mandatory_parameter, None)

    match = r"FabricReplacedBulk\._verify_payload: "
    match += r"Playbook configuration for fabric .* is missing mandatory\s+"
    match += r"parameter.*"
    with pytest.raises(ValueError, match=match):
        instance.payloads = payloads
    assert instance.payloads is None


def test_fabric_replaced_bulk_00030(fabric_replaced_bulk) -> None:
    """
    Classes and Methods
    - FabricReplacedCommon
        - __init__()
        - payloads setter
        - _translate_payload_for_comparison()

    Summary
    -   Verify FabricReplacedCommon()._translate_payload_for_comparison()
        translates correctly-spelled payload keys to the incorrectly-spelled
        keys expected by the controller.
    -   Verify the original correctly-spelled keys are removed from
        the payload.
    -   Verify ANYCAST_GW_MAC is translated from "0001aabbccdd"
        to "0001.aabb.ccdd"
    -   Verify STATIC_UNDERLAY_IP_ALLOC is translated from False
        to "false"
    -   Verify VPC_DELAY_RESTORE_TIME is translated from 300
        to "300"

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payloads = payloads_fabric_replaced_bulk(key)

    with does_not_raise():
        instance = fabric_replaced_bulk
        payload = instance._translate_payload_for_comparison(payloads[0])
    # fixture contains expected test keys and values
    assert payloads[0].get("ANYCAST_GW_MAC") == "0001aabbccdd"
    assert payloads[0].get("STATIC_UNDERLAY_IP_ALLOC") is False
    assert payloads[0].get("VPC_DELAY_RESTORE_TIME") == 300
    assert payloads[0].get("DEFAULT_QUEUING_POLICY_CLOUDSCALE") == "a"
    assert payloads[0].get("DEFAULT_QUEUING_POLICY_OTHER") == "b"
    assert payloads[0].get("DEFAULT_QUEUING_POLICY_R_SERIES") == "c"
    # translated payload contains incorrectly-spelled keys
    assert payload.get("DEAFULT_QUEUING_POLICY_CLOUDSCALE", None) == "a"
    assert payload.get("DEAFULT_QUEUING_POLICY_OTHER", None) == "b"
    assert payload.get("DEAFULT_QUEUING_POLICY_R_SERIES", None) == "c"
    # translated payload does not contain incorrectly-spelled keys
    assert payload.get("DEFAULT_QUEUING_POLICY_CLOUDSCALE", None) is None
    assert payload.get("DEFAULT_QUEUING_POLICY_OTHER", None) is None
    assert payload.get("DEFAULT_QUEUING_POLICY_R_SERIES", None) is None
    # translated payload contains expected value translations
    assert payload.get("ANYCAST_GW_MAC") == "0001.aabb.ccdd"
    assert payload.get("STATIC_UNDERLAY_IP_ALLOC") == "false"
    assert payload.get("VPC_DELAY_RESTORE_TIME") == "300"


def test_fabric_replaced_bulk_00031(fabric_replaced_bulk) -> None:
    """
    Classes and Methods
    - FabricReplacedCommon
        - __init__()
        - payloads setter
        - _translate_payload_for_comparison()

    Summary
    -   Verify FabricReplacedCommon()._translate_payload_for_comparison()
        re-raises ``ValueError`` if ANYCAST_GW_MAC cannot be translated.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    payloads = payloads_fabric_replaced_bulk(key)

    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.results = Results()
    match = r"FabricReplacedBulk\._prepare_anycast_gw_mac_for_comparison:\s+"
    match += r"Error translating ANYCAST_GW_MAC: for fabric f1,\s+"
    match += r"ANYCAST_GW_MAC: 0001, Error detail: Invalid MAC address: 0001"
    with pytest.raises(ValueError, match=match):
        payload = instance._translate_payload_for_comparison(  # pylint: disable=unused-variable
            payloads[0]
        )


@pytest.mark.parametrize(
    "parameter, playbook, controller, default, expected",
    [
        ("PARAM_1", "a", "a", "c", None),
        ("PARAM_2", "a", "c", "c", {"PARAM_2": "a"}),
        ("PARAM_3", "a", "b", "c", {"PARAM_3": "a"}),
        ("PARAM_4", "c", "b", "c", {"PARAM_4": "c"}),
        ("PARAM_5", "c", "c", "c", None),
        ("PARAM_6", None, "c", "c", None),
        ("PARAM_7", None, "b", "c", {"PARAM_7": "c"}),
        ("PARAM_8", None, "b", None, None),
        ("PARAM_9", None, None, None, None),
        ("PARAM_10", "a", None, None, {"PARAM_10": "a"}),
        ("PARAM_11", "a", "b", None, {"PARAM_11": "a"}),
        ("PARAM_12", "a", None, "c", {"PARAM_12": "a"}),
        ("PARAM_13", None, None, "c", None),
    ],
)
def test_fabric_replaced_bulk_00040(
    fabric_replaced_bulk, parameter, playbook, controller, default, expected
) -> None:
    """
    Classes and Methods
    - FabricReplacedCommon
        - __init__()
        - update_replaced_payload()

    Summary
    -   Verify FabricReplacedCommon().update_replaced_payload() returns
        expected values for all possible input combinations.
    """
    with does_not_raise():
        instance = fabric_replaced_bulk
    assert expected == instance.update_replaced_payload(
        parameter, playbook, controller, default
    )


MATCH_00050 = r"FabricReplacedBulk\._verify_value_types_for_comparison:\s+"
MATCH_00050 += r"parameter: PARAM_1, fabric: MyFabric,\s+"
MATCH_00050 += r"conflicting value types .* between the following sources:\s+"
MATCH_00050a = MATCH_00050 + r"\['controller', 'default', 'playbook'\]\."
MATCH_00050b = MATCH_00050 + r"\['controller', 'default'\]\."
MATCH_00050c = MATCH_00050 + r"\['default', 'playbook'\]\."


@pytest.mark.parametrize(
    "user_value, controller_value, default_value, expected",
    [
        ("a", "a", "c", does_not_raise()),
        (None, 10, 20, does_not_raise()),
        (10, None, 20, does_not_raise()),
        (10, 20, None, does_not_raise()),
        ("a", 10, "c", pytest.raises(ValueError, match=MATCH_00050a)),
        (None, 10, "c", pytest.raises(ValueError, match=MATCH_00050b)),
        ("a", None, {}, pytest.raises(ValueError, match=MATCH_00050c)),
    ],
)
def test_fabric_replaced_bulk_00050(
    fabric_replaced_bulk, user_value, controller_value, default_value, expected
) -> None:
    """
    Classes and Methods
    - FabricReplacedCommon
        - __init__()
        - _verify_value_types_for_comparison()

    Summary
    -   Verify FabricReplacedCommon()._verify_value_types_for_comparison()
        does not raise ``ValueError`` when input types are consistent.
    -   Verify FabricReplacedCommon()._verify_value_types_for_comparison()
        raises ``ValueError`` when input types are inconsistent.
    -   Verify the error message when ``ValueError`` is raised.
    """
    fabric = "MyFabric"
    parameter = "PARAM_1"
    with does_not_raise():
        instance = fabric_replaced_bulk
    with expected:
        instance._verify_value_types_for_comparison(
            fabric, parameter, user_value, controller_value, default_value
        )
