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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.param_info import \
    ParamInfo
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.ruleset import \
    RuleSet
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.verify_playbook_params import \
    VerifyPlaybookParams
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    does_not_raise, templates_verify_playbook_params)


def test_verify_playbook_params_00010() -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - __init__()
        - _init_properties()
    - ConversionUtils
        - __init__()
    - ParamInfo
        - __init__()

    Summary
    - Verify the class attributes are initialized to expected values.

    Test
    - Class attributes are initialized to expected values
    - Exceptions are not raised
    """
    with does_not_raise():
        instance = VerifyPlaybookParams()
    assert instance.class_name == "VerifyPlaybookParams"
    assert isinstance(instance.conversion, ConversionUtils)
    assert isinstance(instance._param_info, ParamInfo)
    assert isinstance(instance._ruleset, RuleSet)
    assert not instance.bad_params
    assert instance.fabric_name is None
    assert instance.local_params == {"DEPLOY"}
    assert instance.parameter is None
    assert instance.params_are_valid == set()
    assert instance.properties["config_playbook"] is None
    assert instance.properties["config_controller"] is None
    assert instance.properties["template"] is None


MATCH_OOO20 = r"VerifyPlaybookParams\.config_controller: "
MATCH_OOO20 += r"config_controller must be a dict, or None\."


@pytest.mark.parametrize(
    "value, returned, does_raise, expected",
    [
        ({"foo": "bar"}, {"foo": "bar"}, False, does_not_raise()),
        (None, {}, False, does_not_raise()),
        (10, None, True, pytest.raises(TypeError, match=MATCH_OOO20)),
        ({10, 20}, None, True, pytest.raises(TypeError, match=MATCH_OOO20)),
        ([10, "foo"], None, True, pytest.raises(TypeError, match=MATCH_OOO20)),
        (ParamInfo, None, True, pytest.raises(TypeError, match=MATCH_OOO20)),
    ],
)
def test_verify_playbook_params_00020(value, returned, does_raise, expected) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - __init__()
        - config_controller.setter
        - config_controller.getter

    Summary
    -   Verify ``TypeError`` is raised when config_controller is not either
        a dict or None.
    """
    with does_not_raise():
        instance = VerifyPlaybookParams()
    with expected:
        instance.config_controller = value
    if not does_raise:
        assert instance.config_controller == returned


MATCH_OOO30 = r"VerifyPlaybookParams\.config_playbook: "
MATCH_OOO30 += r"config_playbook must be a dict\."


@pytest.mark.parametrize(
    "value, returned, does_raise, expected",
    [
        ({"foo": "bar"}, {"foo": "bar"}, False, does_not_raise()),
        (None, None, True, pytest.raises(TypeError, match=MATCH_OOO30)),
        (10, None, True, pytest.raises(TypeError, match=MATCH_OOO30)),
        ({10, 20}, None, True, pytest.raises(TypeError, match=MATCH_OOO30)),
        ([10, "foo"], None, True, pytest.raises(TypeError, match=MATCH_OOO30)),
        (ParamInfo, None, True, pytest.raises(TypeError, match=MATCH_OOO30)),
    ],
)
def test_verify_playbook_params_00030(value, returned, does_raise, expected) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - __init__()
        - config_playbook.setter
        - config_playbook.getter

    Summary
    -   Verify ``TypeError`` is raised when config_playbook is not a dict.
    """
    with does_not_raise():
        instance = VerifyPlaybookParams()
    with expected:
        instance.config_playbook = value
    if not does_raise:
        assert instance.config_playbook == returned


MATCH_OOO40 = r"VerifyPlaybookParams\.template: "
MATCH_OOO40 += r"template must be a dict\."


@pytest.mark.parametrize(
    "value, returned, does_raise, expected",
    [
        ({"foo": "bar"}, {"foo": "bar"}, False, does_not_raise()),
        (None, None, True, pytest.raises(TypeError, match=MATCH_OOO40)),
        (10, None, True, pytest.raises(TypeError, match=MATCH_OOO40)),
        ({10, 20}, None, True, pytest.raises(TypeError, match=MATCH_OOO40)),
        ([10, "foo"], None, True, pytest.raises(TypeError, match=MATCH_OOO40)),
        (ParamInfo, None, True, pytest.raises(TypeError, match=MATCH_OOO40)),
    ],
)
def test_verify_playbook_params_00040(value, returned, does_raise, expected) -> None:
    """
    Classes and Methods
    - VerifyPlaybookParams
        - __init__()
        - template.setter
        - template.getter

    Summary
    -   Verify ``TypeError`` is raised when template is not a dict.
    """
    with does_not_raise():
        instance = VerifyPlaybookParams()
    with expected:
        instance.template = value
    if not does_raise:
        assert instance.template == returned
