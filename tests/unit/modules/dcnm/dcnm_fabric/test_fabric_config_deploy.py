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
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, does_not_raise, fabric_config_deploy_fixture,
    fabric_details_by_name_v2_fixture, fabric_summary_fixture, params,
    responses_ep_fabric_config_deploy, responses_fabric_details_by_name_v2,
    responses_fabric_summary)


def test_fabric_config_deploy_00010(fabric_config_deploy) -> None:
    """
    Classes and Methods
    - FabricConfigDeploy
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_config_deploy
    assert instance.class_name == "FabricConfigDeploy"
    assert instance.action == "config_deploy"
    assert instance.config_deploy_result == {}
    assert instance.fabric_name is None
    assert instance.rest_send is None
    assert instance.results is None
    assert instance.conversion.class_name == "ConversionUtils"
    assert instance.ep_config_deploy.class_name == "EpFabricConfigDeploy"


MATCH_00020a = r"ConversionUtils\.validate_fabric_name: "
MATCH_00020a += r"Invalid fabric name\. "
MATCH_00020a += r"Expected string\. Got.*\."

MATCH_00020b = r"ConversionUtils\.validate_fabric_name: "
MATCH_00020b += r"Invalid fabric name:.*\. "
MATCH_00020b += "Fabric name must start with a letter A-Z or a-z and "
MATCH_00020b += r"contain only the characters in: \[A-Z,a-z,0-9,-,_\]\."


@pytest.mark.parametrize(
    "fabric_name, expected, does_raise",
    [
        ("MyFabric", does_not_raise(), False),
        ("My_Fabric", does_not_raise(), False),
        ("My-Fabric", does_not_raise(), False),
        ("M", does_not_raise(), False),
        (1, pytest.raises(ValueError, match=MATCH_00020a), True),
        ({}, pytest.raises(ValueError, match=MATCH_00020a), True),
        ([1, 2, 3], pytest.raises(ValueError, match=MATCH_00020a), True),
        ("1", pytest.raises(ValueError, match=MATCH_00020b), True),
        ("-MyFabric", pytest.raises(ValueError, match=MATCH_00020b), True),
        ("_MyFabric", pytest.raises(ValueError, match=MATCH_00020b), True),
        ("1MyFabric", pytest.raises(ValueError, match=MATCH_00020b), True),
        ("My Fabric", pytest.raises(ValueError, match=MATCH_00020b), True),
        ("My*Fabric", pytest.raises(ValueError, match=MATCH_00020b), True),
    ],
)
def test_fabric_config_deploy_00020(
    fabric_config_deploy, fabric_name, expected, does_raise
) -> None:
    """
    Classes and Methods
    - FabricConfigDeploy
        - __init__()
        - fabric_name getter/setter

    Summary
    -   Verify FabricConfigDeploy().fabric_name re-raises ``ValueError``
        when fabric_name is invalid.
    -   Verify FabricConfigDeploy().fabric_name re-raises ``ValueError``
        when ``KeyError`` is raised by ConversionUtils.validate_fabric_name().
    -   Verify FabricConfigDeploy().fabric_name is set to a valid value
        when fabric_name is valid.

    Code Flow - Setup
    -   FabricConfigDeploy() is instantiated

    Code Flow - Test
    -   FabricConfigDeploy().fabric_name is set to a value that would
        cause the controller to return an error.

    Expected Result
    -   ``ValueError`` is raised
    -   Exception message matches expected
    """
    with does_not_raise():
        instance = fabric_config_deploy
    with expected:
        instance.fabric_name = fabric_name
    if does_raise is False:
        assert instance.fabric_name == fabric_name


MATCH_00030 = r"FabricConfigDeploy\.rest_send: "
MATCH_00030 += r"value must be an instance of RestSend\."


@pytest.mark.parametrize(
    "value, does_raise, expected",
    [
        (RestSend(params), False, does_not_raise()),
        (Results(), True, pytest.raises(TypeError, match=MATCH_00030)),
        (None, True, pytest.raises(TypeError, match=MATCH_00030)),
        ("foo", True, pytest.raises(TypeError, match=MATCH_00030)),
        (10, True, pytest.raises(TypeError, match=MATCH_00030)),
        ([10], True, pytest.raises(TypeError, match=MATCH_00030)),
        ({10}, True, pytest.raises(TypeError, match=MATCH_00030)),
    ],
)
def test_fabric_config_deploy_00030(
    fabric_config_deploy, value, does_raise, expected
) -> None:
    """
    Classes and Methods
    - FabricConfigDeploy
        - __init__()
        - rest_send setter

    Summary
    -   Verify that an exception is not raised, and that rest_send
        is set to expected value when a valid instance of RestSend
        is passed to FabricConfigDeploy().rest_send.
    -   Verify that ``TypeError`` is raised, when an invalid value
        is passed to FabricConfigDeploy().rest_send.
    """
    with does_not_raise():
        instance = fabric_config_deploy
    with expected:
        instance.rest_send = value
    if not does_raise:
        assert instance.rest_send == value


MATCH_00040 = r"FabricConfigDeploy\.results: "
MATCH_00040 += r"value must be an instance of Results\."


@pytest.mark.parametrize(
    "value, does_raise, expected",
    [
        (Results(), False, does_not_raise()),
        (MockAnsibleModule(), True, pytest.raises(TypeError, match=MATCH_00040)),
        (None, True, pytest.raises(TypeError, match=MATCH_00040)),
        ("foo", True, pytest.raises(TypeError, match=MATCH_00040)),
        (10, True, pytest.raises(TypeError, match=MATCH_00040)),
        ([10], True, pytest.raises(TypeError, match=MATCH_00040)),
        ({10}, True, pytest.raises(TypeError, match=MATCH_00040)),
    ],
)
def test_fabric_config_deploy_00040(
    fabric_config_deploy, value, does_raise, expected
) -> None:
    """
    Classes and Methods
    - FabricConfigDeploy
        - __init__()
        - results setter

    Summary
    -   Verify that an exception is not raised, and that results
        is set to expected value when a valid instance of Results
        is passed to FabricConfigDeploy().results.
    -   Verify that ``TypeError`` is raised, when an invalid value
        is passed to FabricConfigDeploy().results.
    """
    with does_not_raise():
        instance = fabric_config_deploy
    with expected:
        instance.results = value
    if not does_raise:
        assert instance.results == value


def test_fabric_config_deploy_00120(
    fabric_config_deploy, fabric_details_by_name_v2, fabric_summary
) -> None:
    """
    Classes and Methods
    - FabricConfigDeploy
        - __init__()
        - payload setter
        - commit()

    Summary
    -   Verify behavior when payload is not set before calling commit()

    Test
    -   ValueError is raised because payload is not set before
        calling commit()
    """

    with does_not_raise():
        instance = fabric_config_deploy
        instance.fabric_details = fabric_details_by_name_v2
        instance.fabric_summary = fabric_summary
        instance.rest_send = RestSend(params)
        instance.results = Results()

    match = r"FabricConfigDeploy\.commit: "
    match += r"FabricConfigDeploy\.payload must be set "
    match += r"before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_config_deploy_00130(
    fabric_config_deploy, fabric_details_by_name_v2, fabric_summary
) -> None:
    """
    Classes and Methods
    - FabricConfigDeploy
        - __init__()
        - rest_send setter
        - commit()

    Summary
    -   Verify behavior when rest_send is not set before calling commit()

    Test
    -   ValueError is raised because rest_send is not set before
        calling commit()
    """
    with does_not_raise():
        instance = fabric_config_deploy
        instance.fabric_details = fabric_details_by_name_v2
        instance.payload = {"FABRIC_NAME": "MyFabric"}
        instance.fabric_summary = fabric_summary
        instance.results = Results()

    match = r"FabricConfigDeploy\.commit: "
    match += r"FabricConfigDeploy\.rest_send must be set "
    match += r"before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_config_deploy_00140(
    fabric_config_deploy, fabric_details_by_name_v2, fabric_summary
) -> None:
    """
    Classes and Methods
    - FabricConfigDeploy
        - __init__()
        - results setter
        - commit()

    Summary
    -   Verify behavior when results is not set before calling commit()

    Test
    -   ValueError is raised because results is not set before
        calling commit()
    """
    with does_not_raise():
        instance = fabric_config_deploy
        instance.fabric_details = fabric_details_by_name_v2
        instance.payload = {"FABRIC_NAME": "MyFabric"}
        instance.fabric_summary = fabric_summary
        instance.rest_send = RestSend(params)

    match = r"FabricConfigDeploy\.commit: "
    match += r"FabricConfigDeploy\.results must be set "
    match += r"before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_config_deploy_00150(fabric_config_deploy, fabric_summary) -> None:
    """
    Classes and Methods
    - FabricConfigDeploy
        - __init__()
        - fabric_details setter
        - commit()

    Summary
    -   Verify behavior when fabric_details is not set before calling commit()

    Test
    -   ValueError is raised because results is not set before
        calling commit()
    """

    with does_not_raise():
        instance = fabric_config_deploy
        instance.payload = {"FABRIC_NAME": "MyFabric"}
        instance.fabric_summary = fabric_summary
        instance.rest_send = RestSend(params)
        instance.results = Results()

    match = r"FabricConfigDeploy\.commit: "
    match += r"FabricConfigDeploy\.fabric_details must be set "
    match += r"before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_config_deploy_00160(
    fabric_config_deploy, fabric_details_by_name_v2
) -> None:
    """
    Classes and Methods
    - FabricConfigDeploy
        - __init__()
        - fabric_summary setter
        - commit()

    Summary
    -   Verify behavior when fabric_summary is not set before calling commit()

    Test
    -   ValueError is raised because fabric_summary is not set before
        calling commit()
    """
    with does_not_raise():
        instance = fabric_config_deploy
        instance.fabric_details = fabric_details_by_name_v2
        instance.payload = {"FABRIC_NAME": "MyFabric"}
        instance.rest_send = RestSend(params)

    match = r"FabricConfigDeploy\.commit: "
    match += r"FabricConfigDeploy\.fabric_summary must be set "
    match += r"before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_config_deploy_00200(
    monkeypatch, fabric_config_deploy, fabric_details_by_name_v2, fabric_summary
) -> None:
    """
    ### Classes and Methods

    - FabricConfigDeploy()
        - __init__()
        - commit()

    ### Summary

    -   Verify that FabricConfigDeploy().commit()
        re-raises ``ValueError`` when EpFabricConfigDeploy() raises
        ``ValueError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    class MockEpFabricConfigDeploy:  # pylint: disable=too-few-public-methods
        """
        Mock the EpFabricConfigDeploy.path getter property
        to raise ``ValueError``.
        """

        @property
        def path(self):
            """
            -   Mocked property getter.
            -   Raise ``ValueError``.
            """
            msg = "mocked EpFabricConfigDeploy().path getter exception"
            print(f"ZZZ msg {msg}")
            raise ValueError(msg)

    def responses():
        yield responses_fabric_summary(key)
        yield responses_fabric_details_by_name_v2(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    payload = {
        "FABRIC_NAME": "f1",
        "FABRIC_TYPE": "VXLAN_EVPN",
        "BGP_AS": 65000,
        "DEPLOY": True,
    }

    with does_not_raise():
        instance = fabric_config_deploy
        monkeypatch.setattr(instance, "ep_config_deploy", MockEpFabricConfigDeploy())
        instance.fabric_details = fabric_details_by_name_v2
        instance.fabric_details.rest_send = rest_send
        instance.payload = payload
        instance.fabric_summary = fabric_summary
        instance.fabric_summary.rest_send = rest_send
        instance.rest_send = rest_send
        instance.results = Results()

    match = r"mocked EpFabricConfigDeploy\(\)\.path getter exception"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_config_deploy_00210(
    fabric_config_deploy, fabric_details_by_name_v2, fabric_summary
) -> None:
    """
    Classes and Methods
    - FabricConfigDeploy
        - __init__()
        - fabric_details setter
        - fabric_names setter
        - fabric_summary setter
        - rest_send setter
        - results setter
        - commit()

    Summary
    -   Verify commit() "happy path" behavior.

    Setup
    -   All properties are properly set prior to calling commit()
    -   RestSend() is patched with response containing:
        -   RETURN_CODE == 200
        -   MESSAGE == "OK"

    Code Flow
    -   FabricConfigDeploy() is instantiated
    -   FabricConfigDeploy() properties are set
    -   FabricConfigDeploy.fabric_name is set "f1"
    -   FabricConfigDeploy().commit() is called.
    -   FabricConfigDeploy().commit() sets EpFabricConfigDeploy().fabric_name
    -   FabricConfigDeploy().commit() accesses
        EpFabricConfigDeploy().path/verb to set path and verb
    -   FabricConfigDeploy().commit() calls
        FabricConfigDeploy()_can_fabric_be_deployed()
    -   FabricConfigDeploy()._can_fabric_be_deployed() calls
        FabricSummary().fabric_is_empty which returns False
        (hence, the fabric can be deployed).
    -   FabricConfigDeploy()._can_fabric_be_deployed() calls
        FabricDetailsByName().deployment_freeze which returns False
        (hence, the fabric can be deployed).
    -   FabricConfigDeploy()._can_fabric_be_deployed() calls
        FabricDetailsByName().is_read_only which returns False
        (hence, the fabric can be deployed).
    -   FabricConfigDeploy().commit() calls RestSend().commit() which calls
        RestSend().response_current to a dict with keys:
        -   DATA == {"status": "Configuration deployment completed."}
        -   RETURN_CODE == 200
        -   METHOD == "POST"
        -   MESSAGE == "OK"
    -   Since rest_send.result_current["success] is True,
        FabricConfigDeploy() sets results.diff_current to a dict containing:
        -   FABRIC_NAME: "f1"
        -   config_deploy: "OK"
    -   FabricConfigDeploy.commit() sets Results() properties and calls
        Results().register_task_result()
    -   Results().register_task_result() adds sequence_number (with value 1) to
        each of the results dicts
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_summary(key)
        yield responses_fabric_details_by_name_v2(key)
        yield responses_ep_fabric_config_deploy(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    payload = {
        "FABRIC_NAME": "f1",
        "FABRIC_TYPE": "VXLAN_EVPN",
        "BGP_AS": 65000,
        "DEPLOY": True,
    }

    with does_not_raise():
        instance = fabric_config_deploy
        instance.rest_send = rest_send
        instance.fabric_details = fabric_details_by_name_v2
        instance.fabric_details.rest_send = instance.rest_send
        instance.payload = payload
        instance.fabric_summary = fabric_summary
        instance.fabric_summary.rest_send = instance.rest_send
        instance.results = Results()
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.response[0].get("sequence_number", None) == 1
    assert instance.results.result[0].get("sequence_number", None) == 1

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.response[0].get("MESSAGE", None) == "OK"

    assert instance.results.result[0].get("changed", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert True in instance.results.changed
    assert False not in instance.results.changed


def test_fabric_config_deploy_00220(
    fabric_config_deploy, fabric_details_by_name_v2, fabric_summary
) -> None:
    """
    Classes and Methods
    - FabricConfigDeploy
        - __init__()
        - fabric_names setter
        - rest_send setter
        - results setter
        - commit()

    Summary
    -   Verify commit() "sad path" behavior.

    Setup
    -   All properties are properly set prior to calling commit()
    -   RestSend() is patched with response containing:
        -   RETURN_CODE == 500
        -   MESSAGE == "Internal server error"

    Code Flow
    -   FabricConfigDeploy() is instantiated
    -   FabricConfigDeploy().fabric_name is set "f1"
    -   FabricConfigDeploy().rest_send is set with the following
        to configure it for this test to try only once before failing
        and not to wait between attempts:
        -   timeout == 1
        -   unit_test == True
    -   FabricConfigDeploy().results is set to Results() class.
    -   FabricConfigDeploy().commit() is called.
    -   FabricConfigDeploy().commit() sets EpFabricConfigDeploy().fabric_name
    -   FabricConfigDeploy().commit() accesses
        EpFabricConfigDeploy().path/verb to set path and verb
    -   FabricConfigDeploy() calls RestSend().commit() which sets
        RestSend().response_current to a dict with keys:
        -   DATA == {"status": "Configuration deployment failed."}
        -   RETURN_CODE == 500
        -   METHOD == "POST"
        -   MESSAGE == "Internal server error"
    -   Since rest_send.result_current["success] is False,
        FabricConfigDeploy() sets results.diff_current to an empty dict.
    -   FabricConfigDeploy.commit() sets Results() properties and calls
        Results().register_task_result()
    -   Results().register_task_result() adds sequence_number (with value 1) to
        each of the results dicts
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_summary(key)
        yield responses_fabric_details_by_name_v2(key)
        yield responses_ep_fabric_config_deploy(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    payload = {
        "FABRIC_NAME": "f1",
        "FABRIC_TYPE": "VXLAN_EVPN",
        "BGP_AS": 65000,
        "DEPLOY": True,
    }

    with does_not_raise():
        instance = fabric_config_deploy
        instance.rest_send = rest_send
        instance.fabric_details = fabric_details_by_name_v2
        instance.fabric_details.rest_send = rest_send
        instance.payload = payload
        instance.fabric_summary = fabric_summary
        instance.fabric_summary.rest_send = rest_send
        instance.results = Results()
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.response[0].get("sequence_number", None) == 1
    assert instance.results.result[0].get("sequence_number", None) == 1

    assert instance.results.response[0].get("RETURN_CODE", None) == 500
    assert instance.results.response[0].get("MESSAGE", None) == "Internal server error"

    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is False

    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed
