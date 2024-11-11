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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy
import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_maintenance_mode import \
    Common
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_maintenance_mode.utils import (
    common_fixture, configs_common, does_not_raise, params)


def test_dcnm_maintenance_mode_common_00000(common) -> None:
    """
    ### Classes and Methods
    - Common
        - __init__()

    ### Summary
    - Verify the class attributes are initialized to expected values.

    ### Test
    - Class attributes are initialized to expected values
    - ``ValueError`` is not called
    """
    with does_not_raise():
        instance = common
    assert instance.class_name == "Common"
    assert instance.state == "merged"
    assert instance.check_mode is False
    assert instance.have == {}
    assert instance.payloads == {}
    assert instance.query == []
    assert instance.want == []
    assert instance.results.class_name == "Results"
    assert instance.results.state == "merged"
    assert instance.results.check_mode is False


def test_dcnm_maintenance_mode_common_00010() -> None:
    """
    ### Classes and Methods
    - Common
        - __init__()

    ### Summary
    -   Verify ``ValueError`` is raised.
    -   params is missing ``check_mode`` key/value.
    """
    params_test = copy.deepcopy(params)
    params_test.pop("check_mode", None)
    match = r"Common\.__init__: check_mode is required"
    with pytest.raises(ValueError, match=match):
        Common(params_test)


def test_dcnm_maintenance_mode_common_00020() -> None:
    """
    ### Classes and Methods
    - Common
        - __init__()

    ### Summary
    -   Verify ``ValueError`` is raised.
    -   params is missing ``state`` key/value.
    """
    params_test = copy.deepcopy(params)
    params_test.pop("state", None)
    match = r"Common\.__init__: state is required"
    with pytest.raises(ValueError, match=match):
        Common(params_test)


def test_dcnm_maintenance_mode_common_00030() -> None:
    """
    ### Classes and Methods
    - Common
        - __init__()

    ### Summary
    -   Verify ``ValueError`` is raised.
    -   params is missing ``config`` key/value.
    """
    params_test = copy.deepcopy(params)
    params_test.pop("config", None)
    match = r"Common\.__init__: config is required"
    with pytest.raises(ValueError, match=match):
        Common(params_test)


def test_dcnm_maintenance_mode_common_00040() -> None:
    """
    ### Classes and Methods
    - Common
        - __init__()

    ### Summary
    -   Verify ``TypeError`` is raised.
    -   config is not a dict.
    """
    params_test = copy.deepcopy(params)
    params_test.update({"config": 10})
    match = r"Common\.__init__: Expected dict type for self\.config\. Got int"
    with pytest.raises(TypeError, match=match):
        Common(params_test)


def test_dcnm_maintenance_mode_common_00100() -> None:
    """
    ### Classes and Methods
    - Common
        - get_want()

    ### Summary
    -   Verify Common().get_want() builds expected want contents.
    -   All switches inherit top-level config.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_common(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})
    with does_not_raise():
        instance = Common(params_test)
        instance.get_want()
    assert isinstance(instance.config, dict)
    assert instance.want[0].get("deploy", None) is True
    assert instance.want[1].get("deploy", None) is True
    assert instance.want[0].get("ip_address", None) == "192.168.1.2"
    assert instance.want[1].get("ip_address", None) == "192.168.1.3"
    assert instance.want[0].get("mode", None) == "normal"
    assert instance.want[1].get("mode", None) == "normal"
    assert instance.want[0].get("wait_for_mode_change", None) is True
    assert instance.want[1].get("wait_for_mode_change", None) is True


def test_dcnm_maintenance_mode_common_00110() -> None:
    """
    ### Classes and Methods
    - Common
        - get_want()

    ### Summary
    -   Verify Common().get_want() builds expected want contents.
    -   192.168.1.2 inherits top-level config.
    -   192.168.1.3 overrides top-level config.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_common(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})
    with does_not_raise():
        instance = Common(params_test)
        instance.get_want()
    assert isinstance(instance.config, dict)
    assert instance.want[0].get("deploy", None) is True
    assert instance.want[1].get("deploy", None) is False
    assert instance.want[0].get("ip_address", None) == "192.168.1.2"
    assert instance.want[1].get("ip_address", None) == "192.168.1.3"
    assert instance.want[0].get("mode", None) == "normal"
    assert instance.want[1].get("mode", None) == "maintenance"
    assert instance.want[0].get("wait_for_mode_change", None) is True
    assert instance.want[1].get("wait_for_mode_change", None) is False


def test_dcnm_maintenance_mode_common_00120() -> None:
    """
    ### Classes and Methods
    - Common
        - get_want()

    ### Summary
    -   Verify Common().get_want() builds expected want contents.
    -   top-level config is missing.
    -   192.168.1.2 uses switch-level config.
    -   192.168.1.3 uses switch-level config.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_common(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})
    with does_not_raise():
        instance = Common(params_test)
        instance.get_want()
    assert isinstance(instance.config, dict)
    assert instance.want[0].get("deploy", None) is True
    assert instance.want[1].get("deploy", None) is False
    assert instance.want[0].get("ip_address", None) == "192.168.1.2"
    assert instance.want[1].get("ip_address", None) == "192.168.1.3"
    assert instance.want[0].get("mode", None) == "normal"
    assert instance.want[1].get("mode", None) == "maintenance"
    assert instance.want[0].get("wait_for_mode_change", None) is True
    assert instance.want[1].get("wait_for_mode_change", None) is False


def test_dcnm_maintenance_mode_common_00130() -> None:
    """
    ### Classes and Methods
    - Common
        - get_want()

    ### Summary
    -   Verify Common().get_want() builds expected want contents.
    -   192.168.1.2 missing all optional parameters, so default values
        are provided.
            - deploy default value is False.
            - mode default value is "normal".
            - wait_for_mode_change default value is False.
    -   192.168.1.3 uses switch-level config.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_common(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})
    with does_not_raise():
        instance = Common(params_test)
        instance.get_want()
    assert isinstance(instance.config, dict)
    assert instance.want[0].get("deploy", None) is False
    assert instance.want[1].get("deploy", None) is True
    assert instance.want[0].get("ip_address", None) == "192.168.1.2"
    assert instance.want[1].get("ip_address", None) == "192.168.1.3"
    assert instance.want[0].get("mode", None) == "normal"
    assert instance.want[1].get("mode", None) == "maintenance"
    assert instance.want[0].get("wait_for_mode_change", None) is False
    assert instance.want[1].get("wait_for_mode_change", None) is True


def test_dcnm_maintenance_mode_common_00140() -> None:
    """
    ### Classes and Methods
    - Common
        - get_want()

    ### Summary
    -   Verify ``ValueError`` is raised.
    -   switch is missing mandatory parameter ip_address
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_common(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})
    with does_not_raise():
        instance = Common(params_test)
    match = r"ParamsValidate\._validate_parameters:\s+"
    match += r"Playbook is missing mandatory parameter:\s+"
    match += r"ip_address\."
    with pytest.raises(ValueError, match=match):
        instance.get_want()


def test_dcnm_maintenance_mode_common_00150() -> None:
    """
    ### Classes and Methods
    - Common
        - get_want()

    ### Summary
    -   Verify ``ValueError`` is raised.
    -   192.168.1.2 contains invalid choice for mode
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_common(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})
    with does_not_raise():
        instance = Common(params_test)
    match = r"ParamsValidate._verify_choices:\s+"
    match += r"Invalid value for parameter 'mode'\.\s+"
    match += r"Expected one of \['normal', 'maintenance'\]\.\s+"
    match += r"Got foo"
    with pytest.raises(ValueError, match=match):
        instance.get_want()


def test_dcnm_maintenance_mode_common_00160() -> None:
    """
    ### Classes and Methods
    - Common
        - get_want()

    ### Summary
    -   Verify ``ValueError`` is raised.
    -   192.168.1.2 contains non-boolean value for deploy
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_common(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})
    with does_not_raise():
        instance = Common(params_test)
    match = r"ParamsValidate._invalid_type:\s+"
    match += r"Invalid type for parameter 'deploy'\.\s+"
    match += r"Expected bool\. Got 'foo'\.\s+"
    match += r"Error detail: The value 'foo' is not a valid boolean\."
    with pytest.raises(ValueError, match=match):
        instance.get_want()


def test_dcnm_maintenance_mode_common_00170() -> None:
    """
    ### Classes and Methods
    - Common
        - get_want()

    ### Summary
    -   Verify ``ValueError`` is raised.
    -   192.168.1.2 contains non-boolean value for wait_for_mode_change
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_common(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})
    with does_not_raise():
        instance = Common(params_test)
    match = r"ParamsValidate._invalid_type:\s+"
    match += r"Invalid type for parameter 'wait_for_mode_change'\.\s+"
    match += r"Expected bool\. Got 'foo'\.\s+"
    match += r"Error detail: The value 'foo' is not a valid boolean\."
    with pytest.raises(ValueError, match=match):
        instance.get_want()


def test_dcnm_maintenance_mode_common_00180() -> None:
    """
    ### Classes and Methods
    - Common
        - get_want()

    ### Summary
    -   Verify ``ValueError`` is raised.
    -   params contains invalid value for ``state``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_common(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})
    params_test.update({"state": "foo"})
    with does_not_raise():
        instance = Common(params_test)
    match = r"Want.commit:\s+"
    match += r"Error generating params_spec\.\s+"
    match += r"Error detail:\s+"
    match += r"ParamsSpec\.params\.setter:\s+"
    match += r"params\.state is invalid: foo\.\s+"
    match += r"Expected one of merged, query\."
    with pytest.raises(ValueError, match=match):
        instance.get_want()
