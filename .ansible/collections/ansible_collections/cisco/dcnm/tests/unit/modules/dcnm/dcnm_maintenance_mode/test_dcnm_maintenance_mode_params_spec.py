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
# Prefer to use more explicit "== {}" rather than "is None" for comparison of lists and dicts.
# pylint: disable=use-implicit-booleaness-not-comparison
# Unit tests commonly test protected members.
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy

import pytest
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_maintenance_mode import \
    ParamsSpec
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_maintenance_mode.utils import (
    does_not_raise, params)


def test_dcnm_maintenance_mode_params_spec_00000() -> None:
    """
    ### Classes and Methods
    - ParamsSpec
        - __init__()

    ### Summary
    - Verify the class attributes are initialized to expected values.

    ### Test
    - Class attributes are initialized to expected values
    - ``ValueError`` is not called
    """
    with does_not_raise():
        instance = ParamsSpec()
    assert instance.class_name == "ParamsSpec"
    assert instance._params is None
    assert instance._params_spec == {}
    assert instance.valid_states == ["merged", "query"]


def test_dcnm_maintenance_mode_params_spec_00100() -> None:
    """
    ### Classes and Methods
    - ParamsSpec
        - params.setter

    ### Summary
    -   Verify ``TypeError`` is raised.
    -   params is not a dict.
    """
    params_test = "foo"

    with does_not_raise():
        instance = ParamsSpec()

    match = r"ParamsSpec\.params.setter:\s+"
    match += r"Invalid type\. Expected dict but got type str, value foo\."
    with pytest.raises(TypeError, match=match):
        instance.params = params_test


def test_dcnm_maintenance_mode_params_spec_00110() -> None:
    """
    ### Classes and Methods
    - ParamsSpec
        - params.setter

    ### Summary
    -   Verify ``ValueError`` is raised.
    -   params is missing ``state`` key/value.
    """
    params_test = copy.deepcopy(params)
    params_test.pop("state", None)

    with does_not_raise():
        instance = ParamsSpec()

    match = r"ParamsSpec\.params\.setter:\s+"
    match += r"params.state is required but missing\."
    with pytest.raises(ValueError, match=match):
        instance.params = params_test


def test_dcnm_maintenance_mode_params_spec_00120() -> None:
    """
    ### Classes and Methods
    - ParamsSpec
        - params.setter

    ### Summary
    -   Verify ``ValueError`` is raised.
    -   params ``state`` has invalid value.
    """
    params_test = copy.deepcopy(params)
    params_test.update({"state": "foo"})

    with does_not_raise():
        instance = ParamsSpec()

    match = r"ParamsSpec\.params\.setter:\s+"
    match += r"params\.state is invalid: foo\. Expected one of merged, query\."
    with pytest.raises(ValueError, match=match):
        instance.params = params_test


def test_dcnm_maintenance_mode_params_spec_00200() -> None:
    """
    ### Classes and Methods
    - ParamsSpec
        - params.setter
        - commit()

    ### Summary
    -   Verify commit() happy path for merged state.
    """
    params_test = copy.deepcopy(params)

    with does_not_raise():
        instance = ParamsSpec()
        instance.params = params_test
        instance.commit()

    assert instance.params == params_test
    assert instance.params_spec["ip_address"]["required"] is True
    assert instance.params_spec["ip_address"]["type"] == "ipv4"
    assert instance.params_spec["ip_address"].get("default", None) is None

    assert instance.params_spec["mode"]["choices"] == ["normal", "maintenance"]
    assert instance.params_spec["mode"]["default"] == "normal"
    assert instance.params_spec["mode"]["required"] is False
    assert instance.params_spec["mode"]["type"] == "str"

    assert instance.params_spec["deploy"]["default"] is False
    assert instance.params_spec["deploy"]["required"] is False
    assert instance.params_spec["deploy"]["type"] == "bool"

    assert instance.params_spec["wait_for_mode_change"]["default"] is False
    assert instance.params_spec["wait_for_mode_change"]["required"] is False
    assert instance.params_spec["wait_for_mode_change"]["type"] == "bool"


def test_dcnm_maintenance_mode_params_spec_00210() -> None:
    """
    ### Classes and Methods
    - ParamsSpec
        - params.setter
        - commit()

    ### Summary
    -   Verify commit() happy path for query state.
    """
    params_test = copy.deepcopy(params)
    params_test.update({"state": "query"})

    with does_not_raise():
        instance = ParamsSpec()
        instance.params = params_test
        instance.commit()

    assert instance.params == params_test
    assert instance.params_spec["ip_address"]["required"] is True
    assert instance.params_spec["ip_address"]["type"] == "ipv4"
    assert instance.params_spec["ip_address"].get("default", None) is None


def test_dcnm_maintenance_mode_params_spec_00220() -> None:
    """
    ### Classes and Methods
    - ParamsSpec
        - params.setter
        - commit()

    ### Summary
    -   Verify commit() sad path.
    -   params is not set before calling commit.
    -   commit() raises ``ValueError`` when params is not set.
    """
    params_test = copy.deepcopy(params)
    params_test.update({"state": "query"})

    with does_not_raise():
        instance = ParamsSpec()

    match = r"ParamsSpec\.commit:\s+"
    match += r"params must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()
