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
    MockAnsibleModule, does_not_raise, responses_template_get_all,
    template_get_all_fixture)


def test_template_get_all_00000(template_get_all) -> None:
    """
    Classes and Methods
    - TemplateGetAll
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = template_get_all
    assert instance.class_name == "TemplateGetAll"
    assert instance.ep_templates.class_name == "EpTemplates"
    assert instance.response == []
    assert instance.response_current == {}
    assert instance.result == []
    assert instance.result_current == {}
    assert instance._templates is None
    assert instance._rest_send is None
    assert instance._results is None


MATCH_00020 = r"TemplateGetAll\.rest_send: "
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
def test_template_get_all_00020(template_get_all, value, expected, raised) -> None:
    """
    Classes and Methods
    - TemplateGetAll
        - __init__()
        - rest_send setter

    Summary
    -   Verify that an exception is not raised, and that rest_send
        is set to expected value when a valid instance of RestSend
        is passed to TemplateGetAll().rest_send.
    -   Verify that ``TypeError`` is raised, when an invalid value
        is passed to TemplateGetAll().rest_send.
    """
    with does_not_raise():
        instance = template_get_all
    with expected:
        instance.rest_send = value
    if not raised:
        assert instance.rest_send == value


MATCH_00030 = r"TemplateGetAll\.results: "
MATCH_00030 += r"value must be an instance of Results.\s+"
MATCH_00030 += r"Got value .* of type .*\."


@pytest.mark.parametrize(
    "value, expected, raised",
    [
        (Results(), does_not_raise(), False),
        (
            RestSend(MockAnsibleModule()),
            pytest.raises(TypeError, match=MATCH_00030),
            True,
        ),
        (None, pytest.raises(TypeError, match=MATCH_00030), True),
        ("foo", pytest.raises(TypeError, match=MATCH_00030), True),
        (10, pytest.raises(TypeError, match=MATCH_00030), True),
        ([10], pytest.raises(TypeError, match=MATCH_00030), True),
        ({10}, pytest.raises(TypeError, match=MATCH_00030), True),
    ],
)
def test_template_get_all_00030(template_get_all, value, expected, raised) -> None:
    """
    Classes and Methods
    - TemplateGetAll
        - __init__()
        - results setter

    Summary
    -   Verify that an exception is not raised, and that results
        is set to expected value when a valid instance of Results
        is passed to TemplateGetAll().results.
    -   Verify that ``TypeError`` is raised, when an invalid value
        is passed to TemplateGetAll().results.
    """
    with does_not_raise():
        instance = template_get_all
    with expected:
        instance.results = value
    if not raised:
        assert instance.results == value


MATCH_00040 = r"TemplateGetAll\.templates: "
MATCH_00040 += r"templates must be an instance of dict\."


@pytest.mark.parametrize(
    "value, expected, raised",
    [
        ({"foo:": "bar"}, does_not_raise(), False),
        (Results(), pytest.raises(TypeError, match=MATCH_00040), True),
        (None, pytest.raises(TypeError, match=MATCH_00040), True),
        ("foo", pytest.raises(TypeError, match=MATCH_00040), True),
        (10, pytest.raises(TypeError, match=MATCH_00040), True),
        ([10], pytest.raises(TypeError, match=MATCH_00040), True),
    ],
)
def test_template_get_all_00040(template_get_all, value, expected, raised) -> None:
    """
    Classes and Methods
    - TemplateGetAll
        - __init__()
        - templates setter

    Summary
    -   Verify that an exception is not raised, and that templates
        is set to expected value when a dict is passed to
        TemplateGetAll().templates.
    -   Verify that ``TypeError`` is raised, when an invalid value
        is passed to TemplateGetAll().templates.
    """
    with does_not_raise():
        instance = template_get_all
    with expected:
        instance.templates = value
    if not raised:
        assert instance.templates == value


def test_template_get_all_00061(template_get_all) -> None:
    """
    Classes and Methods
    - TemplateGetAll
        - __init__()
        - refresh()

    Summary
    -   Verify that ``ValueError`` is raised when TemplateGetAll().refresh()
        is called without having first set the TemplateGetAll().rest_send
        property.

    Test
    -   ``ValueError`` is raised because the TemplateGetAll().rest_send
        property is not set.
    """
    match = r"TemplateGetAll\.refresh: "
    match += r"Set instance\.rest_send property before "
    match += r"calling instance\.refresh\(\)"

    with does_not_raise():
        instance = template_get_all
        instance.template_name = "Easy_Fabric"
        instance.results = Results()
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_template_get_all_00062(monkeypatch, template_get_all) -> None:
    """
    Classes and Methods
    - TemplateGetAll
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
        yield responses_template_get_all(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = template_get_all
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True
        instance.rest_send.timeout = 1
        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    match = r"TemplateGetAll\.refresh: "
    match += r"Failed to retrieve templates\. "
    match += r"RETURN_CODE: 500\. "
    match += r"MESSAGE: Internal Server Error\."
    with pytest.raises(ControllerResponseError, match=match):
        instance.refresh()
    assert len(instance.response) == 1
    assert len(instance.result) == 1
    assert instance.result_current.get("success", None) is False
    assert instance.result_current.get("found", None) is False


def test_template_get_all_00063(monkeypatch, template_get_all) -> None:
    """
    Classes and Methods
    - TemplateGetAll
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
        yield responses_template_get_all(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = template_get_all

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True
        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.refresh()
    assert isinstance(instance.templates, dict)
    assert instance.templates.get("Easy_Fabric", {}).get("name") == "Easy_Fabric"
    assert (
        instance.templates.get("Easy_Fabric_Classic", {}).get("templateType")
        == "FABRIC"
    )
    assert len(instance.response) == 1
    assert len(instance.result) == 1
    assert instance.result_current.get("success", None) is True
    assert instance.result_current.get("found", None) is True
