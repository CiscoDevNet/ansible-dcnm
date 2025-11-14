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
import re

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.ruleset import \
    RuleSet
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    does_not_raise, templates_ruleset)


def test_ruleset_00010() -> None:
    """
    Classes and Methods
    - RuleSet
        - __init__()
    - RuleSet
        - __init__()

    Summary
    - Verify the class attributes are initialized to expected values.

    Test
    - Class attributes are initialized to expected values
    - ``ValueError`` is not called
    """
    with does_not_raise():
        instance = RuleSet()
    assert instance.class_name == "RuleSet"
    assert isinstance(instance.conversion, ConversionUtils)
    assert instance.properties["template"] is None
    assert instance.properties["ruleset"] == {}
    assert instance.re_multi_rule == re.compile(r"^\s*(\(.*\))(.*)(\(.*\))\s*$")


@pytest.mark.parametrize(
    "rule, converted_rule",
    [
        ('"', ""),
        ("'", ""),
        ("$$", ""),
        ("&&", " and "),
        ("||", " or "),
        ("==", " == "),
        ("!=", " != "),
        ("(", " ( "),
        (")", " ) "),
        ("true", "True"),
        ("false", "False"),
        ("   ", " "),
    ],
)
def test_ruleset_00020(rule, converted_rule) -> None:
    """
    Classes and Methods
    - RuleSet
        - __init__()
        - clean_rule()

    Summary
    - Verify RuleSet.clean_rule() converts inputs correctly.
    """
    with does_not_raise():
        instance = RuleSet()
        instance.rule = rule
        instance.clean_rule()
    assert instance.rule == converted_rule


def test_ruleset_00030() -> None:
    """
    Classes and Methods
    - RuleSet
        - __init__()
        - template.setter
        - ruleset.getter

    Summary
    -   Verify template setter accepts a valid template.
    -   Verify ruleset getter returns the expected ruleset.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = RuleSet()
        instance.template = templates_ruleset(key)
        instance.refresh()
    assert instance.ruleset.get("ADVERTISE_PIP_ON_BORDER", {}).get("terms", {}).get(
        "na"
    ) == [{"operator": "!=", "parameter": "ADVERTISE_PIP_BGP", "value": True}]


@pytest.mark.parametrize("bad_value", [("BAD_STRING"), (None), (10), ([10]), ({10})])
def test_ruleset_00031(bad_value) -> None:
    """
    Classes and Methods
    - RuleSet
        - __init__()
        - template.setter

    Summary
    - Verify template setter reject invalid templates.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = RuleSet()
    match = r"RuleSet\.template must be a dictionary."
    with pytest.raises(ValueError, match=match):
        instance.template = templates_ruleset(key)


def test_ruleset_00040() -> None:
    """
    Classes and Methods
    - RuleSet
        - __init__()
        - refresh()

    Summary
    -   Verify ``ValueError`` is raised if refresh() is called before
        setting template.
    """
    with does_not_raise():
        instance = RuleSet()
    match = r"RuleSet\.refresh: template is not set.\s+"
    match += r"Set RuleSet\.template before calling RuleSet\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_ruleset_00041() -> None:
    """
    Classes and Methods
    - RuleSet
        - __init__()
        - template.setter
        - refresh()

    Summary
    -   Verify ``ValueError`` is raised if parameters key is missing.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = RuleSet()
        instance.template = templates_ruleset(key)
    match = r"RuleSet\.refresh: No parameters in template\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_ruleset_00042() -> None:
    """
    Classes and Methods
    - RuleSet
        - __init__()
        - template.setter
        - refresh()

    Summary
    -   Verify ``ValueError`` is raised if parameters is not a list.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = RuleSet()
        instance.template = templates_ruleset(key)
    match = r"RuleSet\.refresh: template\[parameters\] is not a list\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_ruleset_00043() -> None:
    """
    Classes and Methods
    - RuleSet
        - __init__()
        - template.setter
        - refresh()

    Summary
    -   Verify ``ValueError`` is raised if ``name`` key is missing
        from parameter.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    with does_not_raise():
        instance = RuleSet()
        instance.template = templates_ruleset(key)
    match = r"RuleSet\.refresh: name key missing from parameter:"
    with pytest.raises(ValueError, match=match):
        instance.refresh()
