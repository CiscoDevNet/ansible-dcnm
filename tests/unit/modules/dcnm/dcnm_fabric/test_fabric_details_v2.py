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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.control.fabrics.fabrics import \
    EpFabrics
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
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details_v2 import \
    FabricDetails
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    ResponseGenerator, does_not_raise, fabric_details_v2_fixture,
    responses_fabric_details_v2)


def test_fabric_details_v2_00000(fabric_details_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetails
        - __init__()

    ### Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_details_v2
    assert instance.class_name == "FabricDetails"
    assert instance.data == {}
    assert isinstance(instance.ep_fabrics, EpFabrics)
    assert isinstance(instance.conversion, ConversionUtils)


def test_fabric_details_v2_00010() -> None:
    """
    ### Classes and Methods
    - FabricDetails
        - __init__()

    ### Test
    - ``ValueError`` is raised when ``params`` is missing key ``check_mode``.
    """
    match = r"FabricDetails\.__init__:\s+"
    match += r"check_mode is missing from params\. params:.*\."
    with pytest.raises(ValueError, match=match):
        instance = FabricDetails({"state": "merged"})  # pylint: disable=unused-variable


def test_fabric_details_v2_00020() -> None:
    """
    ### Classes and Methods
    - FabricDetails
        - __init__()

    ### Test
    - ``ValueError`` is raised when ``params`` is missing key ``state``.
    """
    match = r"FabricDetails\.__init__:\s+"
    match += r"state is missing from params\. params:.*\."
    with pytest.raises(ValueError, match=match):
        instance = FabricDetails(  # pylint: disable=unused-variable
            {"check_mode": False}
        )


def test_fabric_details_v2_00100(fabric_details_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetails()
        - __init__()
        - refresh_super()

    ### Summary
    - Verify refresh_super() behavior when:
        - RETURN_CODE is 200.
        - DATA is an empty list, indicating no fabrics
          exist on the controller.

    ### Code Flow - Setup
    -   FabricDetails() is instantiated
    -   FabricDetails().RestSend() is instantiated
    -   FabricDetails().Results() is instantiated
    -   FabricDetails().refresh_super() is called
    -   responses_FabricDetails contains a dict with:
        - RETURN_CODE == 200
        - DATA == []

    ### Code Flow - Test
    -   FabricDetails().refresh_super() is called

    ### Expected Result
    -   Exception is not raised
    -   Results() are updated
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_details_v2(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    rest_send.unit_test = True
    rest_send.timeout = 1

    with does_not_raise():
        instance = fabric_details_v2
        instance.rest_send = rest_send
        instance.results = Results()

    with does_not_raise():
        instance.refresh_super()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_details_v2_00110(fabric_details_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetails()
        - __init__()
        - refresh_super()

    ### Summary
    - Verify refresh_super() behavior when:
        -   RETURN_CODE is 200.
        -   DATA is missing (negative test)

    ### Code Flow - Setup
    -   FabricDetails() is instantiated
    -   FabricDetails().RestSend() is instantiated
    -   FabricDetails().Results() is instantiated
    -   FabricDetails().refresh_super() is called
    -   responses_FabricDetails contains a dict with:
        - RETURN_CODE == 200
        - DATA is missing

    ### Code Flow - Test
    -   FabricDetails().refresh_super() is called

    ### Expected Result
    -   Exception is not raised
    -   Results() are updated
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_details_v2(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    rest_send.unit_test = True
    rest_send.timeout = 1

    with does_not_raise():
        instance = fabric_details_v2
        instance.rest_send = rest_send
        instance.results = Results()

    with does_not_raise():
        instance.refresh_super()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 0
    assert len(instance.results.result) == 0
    assert len(instance.results.response) == 0


def test_fabric_details_v2_00120(fabric_details_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetails()
        - __init__()
        - refresh_super()

    ### Summary
    - Verify refresh_super() behavior when:
        -   RETURN_CODE is 200.
        -   Controller response contains one fabric (f1).

    ### Code Flow - Setup
    -   FabricDetails() is instantiated
    -   FabricDetails().RestSend() is instantiated
    -   FabricDetails().Results() is instantiated
    -   FabricDetails().refresh_super() is called
    -   responses_FabricDetails contains a dict with:
        - RETURN_CODE == 200
        - DATA == [<fabric_info from controller>]

    ###Code Flow - Test
    -   FabricDetails().refresh_super() is called

    ### Expected Result
    -   Exception is not raised
    -   instance.all_data returns expected fabric data
    -   Results() are updated
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_fabric_details_v2(key)

    sender = Sender()
    sender.gen = ResponseGenerator(responses())
    rest_send = RestSend({"state": "query", "check_mode": False})
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    rest_send.unit_test = True
    rest_send.timeout = 1

    with does_not_raise():
        instance = fabric_details_v2
        instance.rest_send = rest_send
        instance.results = Results()

    with does_not_raise():
        instance.refresh_super()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed

    assert instance.all_data.get("f1", {}).get("asn", None) == "65001"
    assert instance.all_data.get("f1", {}).get("nvPairs", {}).get("FABRIC_NAME") == "f1"


def test_fabric_details_v2_00200(fabric_details_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetails()
        - __init__()
        - _get()

    ### Summary
    -   Verify FabricDetails()._get() returns None since it's implemented
        only in subclasses
    """
    with does_not_raise():
        instance = fabric_details_v2
    assert instance._get("foo") is None


def test_fabric_details_v2_00300(fabric_details_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetails()
        - __init__()
        - _get_nv_pair()

    ### Summary
    -   Verify FabricDetails()._get_nv_pair() returns None since it's implemented
        only in subclasses
    """
    with does_not_raise():
        instance = fabric_details_v2
    assert instance._get_nv_pair("foo") is None


def test_fabric_details_v2_00400(fabric_details_v2) -> None:
    """
    ### Classes and Methods
    - FabricDetails()
        - __init__()
        - all_data()

    ### Summary
    -   Verify FabricDetails().all_data() returns FabricDetails().data
    """
    with does_not_raise():
        instance = fabric_details_v2
        instance.data = {"foo": "bar"}
    assert instance.all_data == {"foo": "bar"}


MATCH_00500 = r"FabricDetails\.rest_send:\s+"
MATCH_00500 += r"value must be an instance of RestSend\.\s+"
MATCH_00500 += r"Got value.*of type.*\.\s+"
MATCH_00500 += r"Error detail:.*\."


@pytest.mark.parametrize(
    "param, does_raise, expected",
    [
        (None, True, pytest.raises(TypeError, match=MATCH_00500)),
        (1, True, pytest.raises(TypeError, match=MATCH_00500)),
        ("foo", True, pytest.raises(TypeError, match=MATCH_00500)),
        ({"foo": "bar"}, True, pytest.raises(TypeError, match=MATCH_00500)),
        (RestSend({"state": "merged", "check_mode": False}), False, does_not_raise()),
    ],
)
def test_fabric_details_v2_00500(
    fabric_details_v2, param, does_raise, expected
) -> None:
    """
    ### Classes and Methods
    - FabricDetails()
        - __init__()
        - rest_send.setter

    ### Summary
    -   Verify FabricDetails().rest_send raises ``TypeError`` when
        passed a value other than a RestSend() instance.
    """
    with expected:
        instance = fabric_details_v2
        instance.rest_send = param
    if does_raise is False:
        assert instance.rest_send == param