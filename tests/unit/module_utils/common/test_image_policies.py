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
# pylint: disable=unused-argument

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.imagemanagement.rest.policymgnt.policymgnt import \
    EpPolicies
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    MockAnsibleModule, ResponseGenerator, does_not_raise,
    image_policies_fixture, params, responses_ep_policies)


def test_image_policies_00000(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``__init__``

    ### Test

    -   Class attributes and properties are initialized to expected values.
    """
    with does_not_raise():
        instance = image_policies
    assert instance.all_policies == {}
    assert instance.class_name == "ImagePolicies"
    assert instance.conversion.class_name == "ConversionUtils"
    assert instance.data == {}
    assert instance.ep_policies.class_name == "EpPolicies"
    assert instance.policy_name is None
    assert instance.response_data == {}
    assert instance.results is None
    assert instance.rest_send is None


def test_image_policies_00100(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``refresh``
            -   ``policy_name``

    ### Summary
    Verify that ``refresh`` returns image policy info and that the filtered
    properties associated with ``policy_name`` are the expected values.

    ### Test

    -   properties for ``policy_name`` are set to reflect the response from
        the controller.
    -   200 RETURN_CODE.
    -   Exception is not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()

    instance.policy_name = "KR5M"
    assert instance.agnostic is False
    assert instance.description == "10.2.(5) with EPLD"
    assert instance.epld_image_name == "n9000-epld.10.2.5.M.img"
    assert instance.image_name == "nxos64-cs.10.2.5.M.bin"
    assert instance.nxos_version == "10.2.5_nxos64-cs_64bit"
    assert instance.package_name is None
    assert instance.platform == "N9K/N3K"
    assert instance.platform_policies is None
    assert instance.policy_name == "KR5M"
    assert instance.policy_type == "PLATFORM"
    assert instance.ref_count == 10
    assert instance.rpm_images is None


def test_image_policies_00200(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``refresh``
            -   ``rest_send.result_current``

    ### Summary
    -   ``Imagepolicies.rest_send.result`` contains expected key/values on 200
        response from endpoint.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()

    assert isinstance(instance.rest_send.result_current, dict)
    assert instance.rest_send.result_current.get("found") is True
    assert instance.rest_send.result_current.get("success") is True


def test_image_policies_00300(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``refresh``

    ### Summary
    Verify that ``ControllerResponseError`` is raised when the controller
    response RETURN_CODE == 404.

    ### Test

    -   ``ControllerResponseError`` is called on response with RETURN_CODE == 404.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()

    match = r"ImagePolicies\.refresh:\s+"
    match += r"Bad response when retrieving image policy information\s+"
    match += r"from the controller\."

    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()


def test_image_policies_00400(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``refresh``

    ### Summary
    Verify that ``ControllerResponseError`` is raised when the controller
    response contains an empty DATA key.

    ### Test

    -   ``ControllerResponseError`` is raised on RETURN_CODE == 200 with empty
        DATA key.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()

    match = r"ImagePolicies\.refresh:\s+"
    match += r"Bad response when retrieving image policy information\s+"
    match += r"from the controller\."

    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()


def test_image_policies_00500(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``refresh``

    ### Summary
    Verify that exceptions are not raised on controller response with
    RETURN_CODE == 200 containing ``DATA.lastOperDataObject`` with
    length == 0.

    ### Test

    -   Exception is not raised for ``DATA.lastOperDataObject`` length == 0.
    -   RETURN_CODE == 200.

    ### Discussion
    dcnm_image_policy classes ``ImagePolicyCreate`` and
    ``ImagePolicyCreateBulk`` both call ``ImagePolicies.refresh()`` when
    checking if the image policies they are creating already exist on the
    controller.  Hence, we cannot raise an exception when the length of
    ``DATA.lastOperDataObject`` is zero.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()

    assert (
        instance.rest_send.response_current.get("DATA").get("lastOperDataObject") == []
    )
    assert instance.rest_send.response_current.get("RETURN_CODE") == 200


def test_image_policies_00600(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``refresh``
            -   ``policy_name``

    ### Summary
    Verify when ``policy_name`` is set to a policy that does not exist on the
    controller, ``policy`` returns None.

    ### Setup

    -   ``policy_name`` is set to a policy that does not exist on
        the controller.

    ### Test

    -   ``policy`` returns None.

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        image_policies.policy_name = "FOO"

    assert image_policies.policy is None


def test_image_policies_00700(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``refresh``

    ### Summary
    Verify that ``ValueError`` is raised when the controller response
    is missing the "policyName" key.

    ### Test

    -   ``ValueError`` is raised on response with missing "policyName" key.

    ### NOTES

    -   This is to cover a check in ``ImagePolicies.refresh()``.
    -   This scenario should happen only with a controller bug or API change.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()

    match = r"ImagePolicies\.refresh:\s+"
    match += r"Cannot parse policy information from the controller\."

    instance = image_policies
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_image_policies_00800(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``refresh``

    ### Summary
    Verify that ``ControllerResponseError`` is raised when
    ``RestSend().result_current`` indicates an unsuccessful response.

    ### Test

    -   ``ControllerResponseError`` is raised when
        ``RestSend().result_current["success"]`` is False.

    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

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
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()

    match = r"ImagePolicies\.refresh:\s+"
    match += r"Failed to retrieve image policy information\s+"
    match += r"from the controller\.\s+"
    match += r"Controller response:.*"

    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()


def test_image_policies_02000(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``_get()``

    ### Summary
    Verify that ``ValueError`` is raised when ``_get()`` is called prior to
    setting ``policy_name``.

    ### Test

    -   ``ValueError`` is raised when _get() is called prior to setting
        ``policy_name``.
    -   Error messages matches expectation.
    """

    def responses():
        yield None

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()

    match = "ImagePolicies._get: instance.policy_name must be "
    match += "set before accessing property imageName."

    with pytest.raises(ValueError, match=match):
        instance._get("imageName")  # pylint: disable=protected-access


def test_image_policies_02100(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``_get()``

    ### Summary
    Verify that ``ValueError`` is raised when ``_get`` is called
    with an argument that does not match an item in the response data
    for the policy_name returned by the controller.

    ### Setup

    -   ``refresh`` is called and retrieves a response from the
        controller containing information for image policy KR5M.
    -   ``policy_name`` is set to KR5M.

    ### Test

    -   ``ValueError`` is raised when ``_get()`` is called with a
        parameter name "FOO" that does not match any key in the
        response data for the ``policy_name``.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

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
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.policy_name = "KR5M"

    match = r"ImagePolicies\._get: KR5M does not have a key named FOO\."

    with pytest.raises(ValueError, match=match):
        instance._get("FOO")  # pylint: disable=protected-access


def test_image_policies_02200(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``_get()``

    ### Summary
    Verify that the correct image policy information is returned when
    ``ImagePolicies._get()`` is called with the "policy" arguement.

    ### Setup

    -   ``refresh`` is called and retrieves a response from the
        controller containing information for image policy KR5M.
    -   ``policy_name`` is set to KR5M.
    -   _get("policy") is called.

    ### Test

    -   Exception is not raised.
    -   The expected policy information is returned.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

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
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        instance.policy_name = "KR5M"
        value = instance._get("policy")  # pylint: disable=protected-access
    assert value["agnostic"] == "false"
    assert value["epldImgName"] == "n9000-epld.10.2.5.M.img"
    assert value["imageName"] == "nxos64-cs.10.2.5.M.bin"
    assert value["nxosVersion"] == "10.2.5_nxos64-cs_64bit"
    assert value["packageName"] == ""
    assert value["platform"] == "N9K/N3K"
    assert value["platformPolicies"] == ""
    assert value["policyDescr"] == "10.2.(5) with EPLD"
    assert value["policyName"] == "KR5M"
    assert value["policyType"] == "PLATFORM"
    assert value["ref_count"] == 10
    assert value["rpmimages"] == ""


def test_image_policies_03000(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``all_policies``

    ### Summary
    Verify that ``all_policies`` returns an empty dict when no policies exist
    on the controller.

    Test
    -   Exception is not raised.
    -   ``all_policies`` returns an empty dict.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

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
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        value = instance.all_policies
    assert value == {}


def test_image_policies_03100(image_policies) -> None:
    """
    ### Classes and Methods

    -   ``ImagePolicies()``
            -   ``all_policies``

    ### Summary
    Verify that, when policies exist on the controller, all_policies returns a dict
    containing these policies.

    ### Test

    -   Exception is not raised.
    -   ``all_policies`` returns a dict containing the controller's image policies.
    """
    key = "test_image_policies_00051a"

    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_policies(key)

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
        instance = image_policies
        instance.rest_send = rest_send
        instance.results = Results()
        instance.refresh()
        value = instance.all_policies
    assert value["KR5M"]["agnostic"] == "false"
    assert value["KR5M"]["epldImgName"] == "n9000-epld.10.2.5.M.img"
    assert value["KR5M"]["imageName"] == "nxos64-cs.10.2.5.M.bin"
    assert value["KR5M"]["nxosVersion"] == "10.2.5_nxos64-cs_64bit"
    assert value["KR5M"]["packageName"] == ""
    assert value["KR5M"]["platform"] == "N9K/N3K"
    assert value["KR5M"]["platformPolicies"] == ""
    assert value["KR5M"]["policyDescr"] == "10.2.(5) with EPLD"
    assert value["KR5M"]["policyName"] == "KR5M"
    assert value["KR5M"]["policyType"] == "PLATFORM"
    assert value["KR5M"]["ref_count"] == 10
    assert value["KR5M"]["rpmimages"] == ""
    assert value["OR1F"]["agnostic"] == "false"
    assert value["OR1F"]["epldImgName"] == "n9000-epld.10.4.1.F.img"
    assert value["OR1F"]["imageName"] == "nxos64-cs.10.4.1.F.bin"
    assert value["OR1F"]["nxosVersion"] == "10.4.1_nxos64-cs_64bit"
    assert value["OR1F"]["packageName"] == ""
    assert value["OR1F"]["platform"] == "N9K/N3K"
    assert value["OR1F"]["platformPolicies"] == ""
    assert value["OR1F"]["policyDescr"] == "OR1F EPLD"
    assert value["OR1F"]["policyName"] == "OR1F"
    assert value["OR1F"]["policyType"] == "PLATFORM"
    assert value["OR1F"]["ref_count"] == 0
    assert value["OR1F"]["rpmimages"] == ""
