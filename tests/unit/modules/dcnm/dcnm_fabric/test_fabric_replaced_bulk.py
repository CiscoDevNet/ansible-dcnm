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
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_summary import \
    FabricSummary
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, does_not_raise, fabric_replaced_bulk_fixture,
    payloads_fabric_replaced_bulk, responses_config_deploy,
    responses_config_save, responses_fabric_replaced_bulk,
    responses_fabric_summary)

PARAMS = {"state": "replaced", "check_mode": False}


def test_fabric_replaced_bulk_00000(fabric_replaced_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()

    ### Test

    - Class attributes are initialized to expected values.
    - Exception is not raised.
    """
    with does_not_raise():
        instance = fabric_replaced_bulk
    assert instance.class_name == "FabricReplacedBulk"
    assert instance.action == "fabric_replace"
    assert instance.ep_fabric_update.class_name == "EpFabricUpdate"
    assert instance.fabric_details is None
    assert instance.fabric_summary is None
    assert instance.param_info.class_name == "ParamInfo"
    assert instance.rest_send is None
    assert instance.results is None
    assert instance.ruleset.class_name == "RuleSet"
    assert instance.template_get.class_name == "TemplateGet"
    assert instance.verify_playbook_params.class_name == "VerifyPlaybookParams"
    assert instance.path is None
    assert instance.verb is None


def test_fabric_replaced_bulk_00020(fabric_replaced_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
        - payloads setter
    - FabricReplacedBulk
        - __init__()

    ### Summary
    A valid payloads list is presented to the ``payloads`` setter.

    ### Test

    -   ``payloads`` is set to expected value.
    -   Exception is not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.payloads = payloads_fabric_replaced_bulk(key)
    assert instance.payloads == payloads_fabric_replaced_bulk(key)


def test_fabric_replaced_bulk_00021(fabric_replaced_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
        - payloads setter
    - FabricReplacedBulk
        - __init__()

    ### Summary
    ``payloads`` setter is presented with input that is not a list.

    ### Test

    -   ``ValueError`` is raised because ``payloads`` is not a list.
    -   ``payloads`` retains its initial value of None.
    """
    with does_not_raise():
        instance = fabric_replaced_bulk

    match = r"FabricReplacedBulk\.payloads: "
    match += r"payloads must be a list of dict\."

    with pytest.raises(ValueError, match=match):
        instance.payloads = "NOT_A_LIST"

    assert instance.payloads is None


def test_fabric_replaced_bulk_00022(fabric_replaced_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
        - payloads setter
    - FabricReplacedBulk
        - __init__()

    ### Summary
    ``payloads`` setter is presented with a list that contains a non-dict element.

    ### Test

    -   ``ValueError`` is raised because payloads is a list with non-dict
        elements.
    -   ``payloads`` retains its initial value of None.
    """
    with does_not_raise():
        instance = fabric_replaced_bulk

    match = r"FabricReplacedBulk._verify_payload:\s+"
    match += r"Playbook configuration for fabrics must be a dict\.\s+"
    match += r"Got type int, value 1\."

    with pytest.raises(ValueError, match=match):
        instance.payloads = [1, 2, 3]

    assert instance.payloads is None


def test_fabric_replaced_bulk_00023(fabric_replaced_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
        - payloads setter
    - FabricReplacedBulk
        - __init__()

    ### Summary
    Verify behavior when ``payloads`` is set to an empty list.

    Setup
    -   ``payloads`` is set to an empty list.

    ### Test
    -   ``ValueError`` is not raised.
    -   ``payloads`` is set to an empty list.

    ### NOTES

    -   element_spec in dcnm_fabric.py.main() is configured such that
        AnsibleModule will raise an exception when config is not a list
        of dict.  Hence, we do not test commit() here since it would
        never be reached.
    """
    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.payloads = []
    assert instance.payloads == []


@pytest.mark.parametrize(
    "mandatory_parameter",
    ["BGP_AS", "FABRIC_NAME", "FABRIC_TYPE"],
)
def test_fabric_replaced_bulk_00024(fabric_replaced_bulk, mandatory_parameter) -> None:
    """
    ### Classes and Methods

    - FabricReplacedCommon
        - __init__()
        - payloads setter
    - FabricReplacedBulk
        - __init__()

    ### Summary

    -   Verify FabricReplacedCommon().payloads setter re-raises ``ValueError``
        raised by FabricCommon()._verify_payload() when payloads is missing
        mandatory keys.
    -   Verify instance.payloads retains its initial value of None.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = fabric_replaced_bulk

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


def test_fabric_replaced_bulk_00025(fabric_replaced_bulk) -> None:
    """
    ### Classes and Methods

    - FabricCommon
        - __init__()
        - commit()
    - FabricReplacedBulk
        - __init__()

    ### Summary
    ``payloads`` is not set prior to calling commit.

    ### Test

    -   ``ValueError`` is raised because payloads is not set
        prior to calling commit
    -   instance.payloads retains its initial value of None
    """
    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_summary = FabricSummary()
        instance.results = Results()

    match = r"FabricReplacedBulk\.commit: "
    match += r"payloads must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()
    assert instance.payloads is None


def test_fabric_replaced_bulk_00030(fabric_replaced_bulk) -> None:
    """
    ### Classes and Methods

    - FabricReplacedCommon
        - __init__()
        - payloads setter
        - _translate_payload_for_comparison()

    ### Summary

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


MATCH_00031a = r"FabricReplacedBulk\.translate_anycast_gw_mac:\s+"
MATCH_00031a += r"Error translating ANYCAST_GW_MAC: for fabric MyFabric,\s+"
MATCH_00031a += r"ANYCAST_GW_MAC: .*, Error detail: Invalid MAC address:\s+.*"


@pytest.mark.parametrize(
    "mac_in, mac_out, raises, expected",
    [
        ("0001aabbccdd", "0001.aabb.ccdd", False, does_not_raise()),
        ("00:01:aa:bb:cc:dd", "0001.aabb.ccdd", False, does_not_raise()),
        ("00:---01:***aa:b//b:cc:dd", "0001.aabb.ccdd", False, does_not_raise()),
        ("00zz.aabb.ccdd", None, True, pytest.raises(ValueError, match=MATCH_00031a)),
        ("0001", None, True, pytest.raises(ValueError, match=MATCH_00031a)),
    ],
)
def test_fabric_replaced_bulk_00031(
    fabric_replaced_bulk, mac_in, mac_out, raises, expected
) -> None:
    """
    ### Classes and Methods

    - FabricCommon()
        - __init__()
        - translate_anycast_gw_mac()
    - FabricReplacedCommon
        - __init__()
        - _translate_payload_for_comparison()

    ### Summary

    -   Verify FabricReplacedCommon()._translate_payload_for_comparison()
        re-raises ``ValueError`` if ANYCAST_GW_MAC cannot be translated.
    -   Verify the error message when ``ValueError`` is raised.
    -   Verify ``ValueError`` is not raised when ANYCAST_GW_MAC can be
        translated.
    """
    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.results = Results()
    payload = {
        "BGP_AS": 65000,
        "ANYCAST_GW_MAC": mac_in,
        "DEPLOY:": True,
        "FABRIC_NAME": "MyFabric",
        "FABRIC_TYPE": "VXLAN_EVPN",
    }
    with expected:
        result = instance._translate_payload_for_comparison(payload)
    if raises is False:
        assert result.get("ANYCAST_GW_MAC", None) == mac_out


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
        ("PARAM_8", None, "b", None, {"PARAM_8": ""}),
        ("PARAM_9", None, None, None, None),
        ("PARAM_10", "a", None, None, {"PARAM_10": "a"}),
        ("PARAM_11", "a", "a", None, None),
        ("PARAM_12", "a", "b", None, {"PARAM_12": "a"}),
        ("PARAM_13", "a", None, "a", {"PARAM_13": "a"}),
        ("PARAM_14", "a", None, "c", {"PARAM_14": "a"}),
        ("PARAM_15", None, None, "c", {"PARAM_15": "c"}),
    ],
)
def test_fabric_replaced_bulk_00040(
    fabric_replaced_bulk, parameter, playbook, controller, default, expected
) -> None:
    """
    ### Classes and Methods

    - FabricReplacedCommon
        - __init__()
        - update_replaced_payload()

    ### Summary
    Verify ``update_replaced_payload`` returns expected values for all possible
    input combinations.
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
    ### Classes and Methods

    - FabricReplacedCommon
        - __init__()
        - _verify_value_types_for_comparison()

    ### Summary

    -   Verify ``_verify_value_types_for_comparison`` does not raise
        ``ValueError`` when input types are consistent.
    -   Verify ``_verify_value_types_for_comparison`` raises
        ``ValueError`` when input types are inconsistent.
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


def test_fabric_replaced_bulk_00200(fabric_replaced_bulk) -> None:
    """
    ### Classes and Methods

    - FabricReplacedBulk
        - commit()

    ### Summary
    Verify `ValueError`` is raised when ``fabric_details`` is not set before
    calling ``commit``.
    """
    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.fabric_summary = FabricSummary()
        instance.payloads = []
        instance.rest_send = RestSend(PARAMS)
        instance.results = Results()

    match = r"FabricReplacedBulk\.commit:\s+"
    match += r"fabric_details must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_replaced_bulk_00210(fabric_replaced_bulk) -> None:
    """
    ### Classes and Methods

    - FabricReplacedBulk
        - commit()

    ### Summary
    Verify `ValueError`` is raised when ``fabric_summary`` is not set before
    calling ``commit``.
    """
    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.fabric_details = FabricDetailsByName()
        instance.payloads = []
        instance.rest_send = RestSend(PARAMS)
        instance.results = Results()

    match = r"FabricReplacedBulk\.commit:\s+"
    match += r"fabric_summary must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_replaced_bulk_00220(fabric_replaced_bulk) -> None:
    """
    ### Classes and Methods

    - FabricReplacedBulk
        - commit()

    ### Summary
    Verify `ValueError`` is raised when ``payloads`` is not set before
    calling ``commit``.
    """
    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_summary = FabricSummary()
        instance.rest_send = RestSend(PARAMS)
        instance.results = Results()

    match = r"FabricReplacedBulk\.commit:\s+"
    match += r"payloads must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_replaced_bulk_00230(fabric_replaced_bulk) -> None:
    """
    ### Classes and Methods

    - FabricReplacedBulk
        - commit()

    ### Summary
    Verify `ValueError`` is raised when ``rest_send`` is not set before
    calling ``commit``.
    """
    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_summary = FabricSummary()
        instance.payloads = []
        instance.results = Results()

    match = r"FabricReplacedBulk\.commit:\s+"
    match += r"rest_send must be set prior to calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_replaced_bulk_00240(fabric_replaced_bulk) -> None:
    """
    ### Classes and Methods

    - FabricReplacedCommon
        - __init__()
    - FabricReplacedBulk
        - __init__()
        - commit()

    ### Summary

    -   Verify FabricReplacedBulk().Results() properties are
        set by FabricReplacedBulk().commit().
    -   Verify FabricReplacedBulk().rest_send.state is set to "replaced"
    -   Verify FabricReplacedBulk().results.action is set to "fabric_replace"
    -   Verify FabricReplacedBulk().results.state is set to "replaced"
    -   Verify FabricReplacedBulk().template_get.rest_send is set to
        FabricReplacedBulk().rest_send
    -   Verify FabricReplacedBulk()._build_payloads_for_replaced_state()
        does not raise ``ValueError`` when called by commit().
    -   Verify FabricReplacedBulk()._payloads_to_commit is set to an empty
        because FabricReplacedBulk().payloads is empty.
    -   Verify FabricReplacedBulk().results.failed contains False
    -   Verify FabricReplacedBulk().results.failed does not contain True
    -   Verify FabricReplacedBulk().results.changed contains False
    -   Verify FabricReplacedBulk().results.changed does not contain True
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_replaced_bulk(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(PARAMS)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_replaced_bulk
        instance.rest_send = rest_send
        instance.fabric_details = FabricDetailsByName()
        instance.fabric_details.rest_send = rest_send
        instance.fabric_details.results = Results()
        instance.fabric_summary = FabricSummary()
        instance.fabric_summary.rest_send = rest_send
        instance.payloads = []
        instance.results = Results()
        instance.commit()

    assert instance.rest_send.state == "replaced"
    assert instance.results.action == "fabric_replace"
    assert instance.results.state == "replaced"
    assert instance.template_get.rest_send == instance.rest_send
    assert instance._payloads_to_commit == []
    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed

    assert instance.results.metadata[0].get("sequence_number") == 1
    assert instance.results.response[0].get("sequence_number") == 1
    assert instance.results.result[0].get("sequence_number") == 1

    assert instance.results.metadata[0].get("action") == "fabric_replace"
    assert instance.results.metadata[0].get("check_mode") is False
    assert instance.results.metadata[0].get("state") == "replaced"

    assert (
        instance.results.response[0].get("MESSAGE")
        == "No fabrics to update for replaced state."
    )
    assert instance.results.response[0].get("RETURN_CODE") == 200

    assert instance.results.result[0].get("changed") is False
    assert instance.results.result[0].get("success") is True
