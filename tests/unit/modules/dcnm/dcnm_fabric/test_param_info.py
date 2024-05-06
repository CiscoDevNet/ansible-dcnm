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

import copy
import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.param_info import \
    ParamInfo
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    does_not_raise, templates_param_info)


def test_param_info_00010() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
    - ParamInfo
        - __init__()

    Summary
    - Verify the class attributes are initialized to expected values.

    Test
    - Class attributes are initialized to expected values
    - ``ValueError`` is not called
    """
    with does_not_raise():
        instance = ParamInfo()
    assert instance.class_name == "ParamInfo"
    assert not instance.info
    assert instance.properties["template"] is None


def test_param_info_00020() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter

    Summary
    - Verify ``TypeError`` is raised when template is not a dict.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
    match = r"ParamInfo\.template: "
    match += r"template must be a dict\."
    with pytest.raises(TypeError, match=match):
        instance.template = templates_param_info(key)


def test_param_info_00030() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()

    Summary
    - Verify template setter loads a valid template without error
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)
        instance.refresh()


def test_param_info_00031() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - refresh()

    Summary
    -   Verify refresh() raises ``ValueError`` when called
        without template being set.
    """
    with does_not_raise():
        instance = ParamInfo()

    match = r"ParamInfo\.refresh: "
    match += r"Call instance\.template before calling instance\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_param_info_00032() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()

    Summary
    -   Verify refresh() raises ``ValueError`` when template is missing the
        ``parameters` key.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)

    match = r"ParamInfo\.refresh: "
    match += r"No parameters in template\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_param_info_00033() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()

    Summary
    - Verify refresh() raises ``ValueError`` when ``parameters` is not a list.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)

    match = r"ParamInfo\.refresh: "
    match += r"template\['parameters'\] is not a list\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_param_info_00040() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()
        - _build_info()
        - _get_param_name()

    Summary
    -   Verify _get_param_name() raises ``KeyError`` when parameter is missing
        ``name`` key.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)

    match = r"ParamInfo\._get_param_name: "
    match += r"Parameter is missing name key:"
    with pytest.raises(KeyError, match=match):
        instance.refresh()


def test_param_info_00050() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()
        - _build_info()
        - _get_choices()
        - parameter()

    Summary
    -   Verify _get_choices() returns None when ``Enum`` key is missing
        and ``parameterType`` is not boolean.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)
        instance.refresh()
    assert instance.parameter("UPGRADE_FROM_VERSION").get("choices") is None


def test_param_info_00051() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()
        - _get_choices()
        - parameter()

    Summary
    -   Verify _get_choices() returns [False, True] when
        ``Enum`` key is missing and ``parameterType`` is boolean.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)
        instance.refresh()
    assert instance.parameter("ENABLE_EVPN").get("choices") == [False, True]


def test_param_info_00052() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()
        - _get_choices()
        - parameter()

    Summary
    -   Verify _get_choices() returns the contents of ``Enum`` key,
        formatted as a sorted list, when ``Enum`` key is present and
        ``parameterType`` is not boolean.
    -   "\\"Multicast,Ingress\\"" -> ["Ingress", "Multicast"]
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)
        instance.refresh()
    assert instance.parameter("REPLICATION_MODE").get("choices") == [
        "Ingress",
        "Multicast",
    ]


def test_param_info_00053() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()
        - _get_choices()
        - parameter()

    Summary
    -   Verify _get_choices() returns the contents of ``Enum`` key,
        formatted as a sorted list of integers, when ``Enum`` key is
        present, and ``parameterType`` is not boolean, and the contents
        of ``Enum`` key are string representations of integers:
    -   "1,2" -> [1,2]
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)
        instance.refresh()
    assert instance.parameter("RR_COUNT").get("choices") == [2, 4]


def test_param_info_00060() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()
        - _get_default()
        - parameter()

    Summary
    -   Verify _get_default() returns the default value when,
        ``metaProperties.defaultValue`` is present and not null,
        and when ``defaultValue`` is present and null.
    -   Verify that the default value is returned as an integer
        when the content of ``metaProperties.defaultValue`` is
        a string representation of an integer.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)
        instance.refresh()
    assert instance.parameter("RR_COUNT").get("default") == 2


def test_param_info_00061() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()
        - _get_default()
        - parameter()

    Summary
    -   Verify _get_default() returns the default value when,
        ``metaProperties.defaultValue`` is present and not null,
        and when ``defaultValue`` is present and null.
    -   Verify that the default value is returned as a boolean
        when the content of ``metaProperties.defaultValue`` is
        a string representation of a boolean.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)
        instance.refresh()
    assert instance.parameter("UNDERLAY_IS_V6").get("default") is False


def test_param_info_00062() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()
        - _get_default()
        - parameter()

    Summary
    -   Verify _get_default() returns the default value when,
        ``metaProperties.defaultValue`` is present and not null,
        and when ``defaultValue`` is present and null.
    -   Verify that the default value is returned as a string
        when the content of ``metaProperties.defaultValue`` is
        a string and not a string representation of boolean or
        integer.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)
        instance.refresh()
    assert instance.parameter("LINK_STATE_ROUTING").get("default") == "ospf"


def test_param_info_00063() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()
        - _get_default()
        - parameter()

    Summary
    -   Verify _get_default() returns None when,
        ``metaProperties.defaultValue`` is not present,
        and ``defaultValue`` is present and null.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)
        instance.refresh()
    assert instance.parameter("OSPF_AUTH_KEY").get("default") is None


def test_param_info_00064() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()
        - _get_default()
        - parameter()

    Summary
    -   Verify _get_default() returns 0 when,
        ``metaProperties.defaultValue`` is present and == "0",
        and ``defaultValue`` is present and null.

    NOTES:
    -   Since assert False == 0 is True, the first assert below is not enough.
    -   To test fully, the returned value is converted to a string and
        verified to equal a string representation of zero ("0").
        If False were returned, it would equal 'False' and the assert
        will fail.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)
        instance.refresh()
    assert instance.parameter("BGP_LB_ID").get("default") == 0
    assert str(instance.parameter("BGP_LB_ID").get("default")) == "0"


def test_param_info_00065() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()
        - _get_default()
        - parameter()

    Summary
    -   Verify _get_default() returns 1 when,
        ``metaProperties.defaultValue`` is present and == "1",
        and ``defaultValue`` is present and null.

    NOTES:
    -   Since assert True == 1 is True, the first assert below is not enough.
    -   To test fully, the returned value is converted to a string and
        verified to equal a string representation of one ("1").
        If True were returned, it would equal 'True' and the assert
        will fail.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)
        instance.refresh()
    assert instance.parameter("NVE_LB_ID").get("default") == 1
    assert str(instance.parameter("NVE_LB_ID").get("default")) == "1"


def test_param_info_00070() -> None:
    """
    Classes and Methods
    - ParamInfo
        - __init__()
        - template.setter
        - refresh()
        - parameter(value)

    Summary
    -   Verify parameter() raises ``KeyError`` when value is not in the
        template.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = ParamInfo()
        instance.template = templates_param_info(key)
        instance.refresh()
    match = r"ParamInfo\.parameter:\s+"
    match += r"Parameter UNDERLAY_IS_V6 not found in fabric template\.\s+"
    match += r"This likely means that the parameter UNDERLAY_IS_V6 is\s+"
    match += r"not appropriate for the fabric type\."
    with pytest.raises(KeyError, match=match):
        instance.parameter("UNDERLAY_IS_V6")
