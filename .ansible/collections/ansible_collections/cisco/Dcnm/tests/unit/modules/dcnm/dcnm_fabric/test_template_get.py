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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, does_not_raise, responses_template_get,
    template_get_fixture)


def test_template_get_00000(template_get) -> None:
    """
    Classes and Methods
    - TemplateGet
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = template_get
    assert instance.class_name == "TemplateGet"
    assert instance.ep_template.class_name == "EpTemplate"
    assert instance.response == []
    assert instance.response_current == {}
    assert instance.result == []
    assert instance.result_current == {}
    assert instance.template_name is None
    assert instance.template is None
    assert instance.rest_send is None
    assert instance.results is None


MATCH_00020 = r"TemplateGet\.rest_send: "
MATCH_00020 += r"value must be an instance of RestSend.\s+"
MATCH_00020 += r"Got value .* of type .*\."


@pytest.mark.parametrize(
    "value, expected, raised",
    [
        (RestSend(MockAnsibleModule()), does_not_raise(), False),
        (Results(), pytest.raises(TypeError, match=MATCH_00020), True),
        (None, pytest.raises(TypeError, match=MATCH_00020), True),
        ("foo", pytest.raises(TypeError, match=MATCH_00020), True),
        (10, pytest.raises(TypeError, match=MATCH_00020), True),
        ([10], pytest.raises(TypeError, match=MATCH_00020), True),
        ({10}, pytest.raises(TypeError, match=MATCH_00020), True),
    ],
)
def test_template_get_00020(template_get, value, expected, raised) -> None:
    """
    Classes and Methods
    - TemplateGet
        - __init__()
        - rest_send setter

    Summary
    -   Verify that an exception is not raised, and that rest_send
        is set to expected value when a valid instance of RestSend
        is passed to TemplateGet().rest_send.
    -   Verify that ``TypeError`` is raised, when an invalid value
        is passed to TemplateGet().rest_send.
    """
    with does_not_raise():
        instance = template_get
    with expected:
        instance.rest_send = value
    if not raised:
        assert instance.rest_send == value


MATCH_00030 = r"TemplateGet\.results: "
MATCH_00030 += r"value must be an instance of Results.\s+"
MATCH_00030 += r"Got value .* of type .*\."


@pytest.mark.parametrize(
    "value, expected, raised",
    [
        (Results(), does_not_raise(), False),
        (MockAnsibleModule(), pytest.raises(TypeError, match=MATCH_00030), True),
        (None, pytest.raises(TypeError, match=MATCH_00030), True),
        ("foo", pytest.raises(TypeError, match=MATCH_00030), True),
        (10, pytest.raises(TypeError, match=MATCH_00030), True),
        ([10], pytest.raises(TypeError, match=MATCH_00030), True),
        ({10}, pytest.raises(TypeError, match=MATCH_00030), True),
    ],
)
def test_template_get_00030(template_get, value, expected, raised) -> None:
    """
    Classes and Methods
    - TemplateGet
        - __init__()
        - results setter

    Summary
    -   Verify that an exception is not raised, and that results
        is set to expected value when a valid instance of Results
        is passed to TemplateGet().results.
    -   Verify that ``TypeError`` is raised, when an invalid value
        is passed to TemplateGet().results.
    """
    with does_not_raise():
        instance = template_get
    with expected:
        instance.results = value
    if not raised:
        assert instance.results == value


MATCH_00040 = r"TemplateGet\.template: "
MATCH_00040 += r"template must be an instance of dict\."


@pytest.mark.parametrize(
    "value, expected, raised",
    [
        ({"foo": "bar"}, does_not_raise(), False),
        (Results(), pytest.raises(TypeError, match=MATCH_00040), True),
        (None, pytest.raises(TypeError, match=MATCH_00040), True),
        ("foo", pytest.raises(TypeError, match=MATCH_00040), True),
        (10, pytest.raises(TypeError, match=MATCH_00040), True),
        ([10], pytest.raises(TypeError, match=MATCH_00040), True),
        ({10}, pytest.raises(TypeError, match=MATCH_00040), True),
    ],
)
def test_template_get_00040(template_get, value, expected, raised) -> None:
    """
    Classes and Methods
    - TemplateGet
        - __init__()
        - template setter

    Summary
    -   Verify that an exception is not raised, and that template
        is set to expected value when a dictionary is passed to
        TemplateGet().template.
    -   Verify that ``TypeError`` is raised, when an invalid value
        is passed to TemplateGet().template.
    """
    with does_not_raise():
        instance = template_get
    with expected:
        instance.template = value
    if not raised:
        assert instance.template == value


MATCH_00050 = r"TemplateGet\.template_name: "
MATCH_00050 += r"template_name must be an instance of str\."


@pytest.mark.parametrize(
    "value, expected, raised",
    [
        ("Easy_Fabric", does_not_raise(), False),
        (Results(), pytest.raises(TypeError, match=MATCH_00050), True),
        (None, pytest.raises(TypeError, match=MATCH_00050), True),
        (10, pytest.raises(TypeError, match=MATCH_00050), True),
        ([10], pytest.raises(TypeError, match=MATCH_00050), True),
        ({10}, pytest.raises(TypeError, match=MATCH_00050), True),
        ({"foo": "bar"}, pytest.raises(TypeError, match=MATCH_00050), True),
    ],
)
def test_template_get_00050(template_get, value, expected, raised) -> None:
    """
    Classes and Methods
    - TemplateGet
        - __init__()
        - template_name setter

    Summary
    -   Verify that an exception is not raised, and that template_name
        is set to expected value when a string is passed to
        TemplateGet().template_name.
    -   Verify that ``TypeError`` is raised, when an invalid value
        is passed to TemplateGet().template_name.
    """
    with does_not_raise():
        instance = template_get
    with expected:
        instance.template_name = value
    if not raised:
        assert instance.template_name == value


def test_template_get_00060(template_get) -> None:
    """
    Classes and Methods
    - TemplateGet
        - __init__()
        - refresh()
        - _set_template_endpoint()

    Summary
    -   Verify that ``ValueError`` is raised when TemplateGet().refresh()
        is called without having first set the TemplateGet().template_name
        property.

    Test
    -   ``ValueError`` is raised because the TemplateGet().template_name
        property is not set.
    """
    match = r"TemplateGet\._set_template_endpoint: "
    match += r"Set instance\.template_name property before "
    match += r"calling instance\.refresh\(\)"

    with does_not_raise():
        instance = template_get
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_template_get_00061(template_get) -> None:
    """
    Classes and Methods
    - TemplateGet
        - __init__()
        - refresh()

    Summary
    -   Verify that ``ValueError`` is raised when TemplateGet().refresh()
        is called without having first set the TemplateGet().rest_send
        property.

    Test
    -   ``ValueError`` is raised because the TemplateGet().rest_send
        property is not set.
    """
    match = r"TemplateGet\.refresh: "
    match += r"Set instance\.rest_send property before "
    match += r"calling instance\.refresh\(\)"

    with does_not_raise():
        instance = template_get
        instance.template_name = "Easy_Fabric"
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_template_get_00062(monkeypatch, template_get) -> None:
    """
    Classes and Methods
    - TemplateGet
        - __init__()
        - refresh()
        - _set_template_endpoint()

    Summary
    -   Verify that ``ControllerResponseError`` is raised when refresh()
        is called and the response from the controller contains a RETURN_CODE
        other than 200.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_template_get(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = template_get

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()
        instance.template_name = "Easy_Fabric"

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    match = r"TemplateGet\.refresh: "
    match += r"Failed to retrieve template Easy_Fabric\. "
    match += r"RETURN_CODE: 500\. "
    match += r"MESSAGE: Internal Server Error\."
    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()
    assert len(instance.response) == 1
    assert len(instance.result) == 1
    assert instance.result_current.get("success", None) is False
    assert instance.result_current.get("found", None) is False


def test_template_get_00063(monkeypatch, template_get) -> None:
    """
    Classes and Methods
    - TemplateGet
        - __init__()
        - refresh()
        - _set_template_endpoint()

    Summary
    -   Verify behavior when refresh() is called and the response from the
        indicates success i.e. RETURN_CODE == 200.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_template_get(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = template_get

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()
        instance.template_name = "Easy_Fabric"

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.refresh()
    assert isinstance(instance.template, dict)
    assert isinstance(instance.template.get("parameters"), list)
    assert len(instance.response) == 1
    assert len(instance.result) == 1
    assert instance.result_current.get("success", None) is True
    assert instance.result_current.get("found", None) is True


def test_template_get_00070(monkeypatch, template_get) -> None:
    """
    Classes and Methods
    - TemplateGet
        - __init__()
        - _set_template_endpoint()

    Summary
    -   Verify that TemplateGet()._set_template_endpoint() re-raises
        ``ValueError`` when EpTemplate() raises ``ValueError``.
    """

    class MockEpTemplate:  # pylint: disable=too-few-public-methods
        """
        Mock the EpTemplate.template_name setter property to raise ``ValueError``.
        """

        @property
        def template_name(self):
            """
            -   Mocked template_name property getter
            """

        @template_name.setter
        def template_name(self, value):
            """
            -   Mocked template_name property setter
            """
            raise ValueError("mocked EpTemplate().template_name setter exception.")

    match = r"mocked EpTemplate\(\)\.template_name setter exception\."

    with does_not_raise():
        instance = template_get
        monkeypatch.setattr(instance, "ep_template", MockEpTemplate())
    with pytest.raises(ValueError, match=match):
        instance.template_name = "Easy_Fabric"  # pylint: disable=pointless-statement
        instance._set_template_endpoint()
