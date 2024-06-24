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
# pylint: disable=protected-access
# pylint: disable=use-implicit-booleaness-not-comparison

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy
import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_maintenance_mode import (
    ParamsSpec, Want)
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.test_params_validate_v2 import \
    ParamsValidate
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_maintenance_mode.utils import (
    configs_want, does_not_raise, params)


def test_dcnm_maintenance_mode_want_00000() -> None:
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
        instance = Want()
    assert instance.class_name == "Want"
    assert instance._config is None
    assert instance._items_key is None
    assert instance._params is None
    assert instance._params_spec is None
    assert instance._validator is None
    assert instance._want == []
    assert instance.merged_configs == []
    assert instance.item_configs == []


def test_dcnm_maintenance_mode_want_00100() -> None:
    """
    ### Classes and Methods
    - Want()
        - commit()

    ### Summary
    -   Verify ``commit()`` happy path.
    -   No exceptions are raised.
    -   want contains expected structure and values.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_want(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})

    with does_not_raise():
        instance = Want()
        instance.items_key = "switches"
        instance.config = params_test.get("config")
        instance.params = params_test
        instance.params_spec = ParamsSpec()
        instance.validator = ParamsValidate()
        instance.commit()
    assert instance.want[0].get("deploy", None) is True
    assert instance.want[0].get("ip_address", None) == "192.168.1.2"
    assert instance.want[0].get("mode", None) == "normal"
    assert instance.want[0].get("wait_for_mode_change", None) is True
    assert instance.want[1].get("deploy", None) is True
    assert instance.want[1].get("ip_address", None) == "192.168.1.3"
    assert instance.want[1].get("mode", None) == "normal"
    assert instance.want[1].get("wait_for_mode_change", None) is True


def test_dcnm_maintenance_mode_want_00110() -> None:
    """
    ### Classes and Methods
    - Want()
        - commit()

    ### Summary
    -   Verify ``ValueError`` is raised.
    -   Want().validator is not set prior to calling commit().
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_want(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})

    with does_not_raise():
        instance = Want()
        instance.items_key = "switches"
        instance.config = params_test.get("config")
        instance.params = params_test
        instance.params_spec = ParamsSpec()
    match = r"Want\.commit:\s+"
    match += r"self\.validator must be set before calling commit\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_dcnm_maintenance_mode_want_00120() -> None:
    """
    ### Classes and Methods
    - Want()
        - commit()

    ### Summary
    -   Verify Want().commit() catches and re-raises ``ValueError``.
    -   Want().generate_params_spec() raises ``ValueError`` because
        ``params`` is not set.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_want(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})

    with does_not_raise():
        instance = Want()
        instance.items_key = "switches"
        instance.config = params_test.get("config")
        instance.params_spec = ParamsSpec()
        instance.validator = ParamsValidate()
    match = r"Want\.commit:\s+"
    match += r"Error generating params_spec\.\s+"
    match += r"Error detail:\s+"
    match += r"Want\.generate_params_spec\(\):\s+"
    match += r"params is not set, and is required\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_dcnm_maintenance_mode_want_00121() -> None:
    """
    ### Classes and Methods
    - Want()
        - commit()

    ### Summary
    -   Verify Want().commit() catches and re-raises ``ValueError``.
    -   Want().generate_params_spec() raises ``ValueError`` because
        ``params_spec`` is not set.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_want(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})

    with does_not_raise():
        instance = Want()
        instance.items_key = "switches"
        instance.config = params_test.get("config")
        instance.params = params_test
        instance.validator = ParamsValidate()
    match = r"Want\.commit:\s+"
    match += r"Error generating params_spec\.\s+"
    match += r"Error detail:\s+"
    match += r"Want\.generate_params_spec\(\):\s+"
    match += r"params_spec is not set, and is required\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_dcnm_maintenance_mode_want_00130() -> None:
    """
    ### Classes and Methods
    - Want()
        - commit()

    ### Summary
    -   Verify Want().commit() catches and re-raises ``ValueError``.
    -   Want()._merge_global_and_item_configs() raises ``ValueError``
        because ``config`` is not set.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_want(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})

    with does_not_raise():
        instance = Want()
        instance.items_key = "switches"
        instance.params = params_test
        instance.params_spec = ParamsSpec()
        instance.validator = ParamsValidate()
    match = r"Want\.commit:\s+"
    match += r"Error merging global and item configs\.\s+"
    match += r"Error detail:\s+"
    match += r"Want\._merge_global_and_item_configs:\s+"
    match += r"config is not set, and is required\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_dcnm_maintenance_mode_want_00131() -> None:
    """
    ### Classes and Methods
    - Want()
        - commit()

    ### Summary
    -   Verify Want().commit() catches and re-raises ``ValueError``.
    -   Want()._merge_global_and_item_configs() raises ``ValueError``
        because ``items_key`` is not set.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_want(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})

    with does_not_raise():
        instance = Want()
        instance.config = params_test.get("config")
        instance.params = params_test
        instance.params_spec = ParamsSpec()
        instance.validator = ParamsValidate()
    match = r"Want\.commit:\s+"
    match += r"Error merging global and item configs\.\s+"
    match += r"Error detail:\s+"
    match += r"Want\._merge_global_and_item_configs:\s+"
    match += r"items_key is not set, and is required\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_dcnm_maintenance_mode_want_00132() -> None:
    """
    ### Classes and Methods
    - Want()
        - commit()

    ### Summary
    -   Verify Want().commit() catches and re-raises ``ValueError``.
    -   Want()._merge_global_and_item_configs() raises ``ValueError``
        because ``config`` is missing the key specified by items_key.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_want(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})

    with does_not_raise():
        instance = Want()
        instance.config = params_test.get("config")
        instance.items_key = "NOT_PRESENT_IN_CONFIG"
        instance.params = params_test
        instance.params_spec = ParamsSpec()
        instance.validator = ParamsValidate()
    match = r"Want\.commit:\s+"
    match += r"Error merging global and item configs\.\s+"
    match += r"Error detail:\s+"
    match += r"Want\._merge_global_and_item_configs:\s+"
    match += r"playbook is missing list of NOT_PRESENT_IN_CONFIG\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_dcnm_maintenance_mode_want_00133(monkeypatch) -> None:
    """
    ### Classes and Methods
    - Want()
        - commit()

    ### Summary
    -   Verify Want().commit() catches and re-raises ``ValueError``.
    -   Want()._merge_global_and_item_configs() raises ``ValueError``
        because MergeDict().commit() raises ``ValueError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_want(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})

    class MockMergeDicts:  # pylint: disable=too-few-public-methods
        """
        Mock class for MergeDicts().
        """

        @staticmethod
        def commit():
            """
            ### Summary
            Mock method for MergeDicts().commit().

            ### Raises
            ValueError: Always
            """
            raise ValueError("MergeDicts().commit(). ValueError.")

    with does_not_raise():
        instance = Want()
        monkeypatch.setattr(instance, "merge_dicts", MockMergeDicts)
        instance.config = params_test.get("config")
        instance.items_key = "switches"
        instance.params = params_test
        instance.params_spec = ParamsSpec()
        instance.validator = ParamsValidate()
    match = r"Want\.commit: Error merging global and item configs\.\s+"
    match += r"Error detail:\s+"
    match += r"Want\._merge_global_and_item_configs:\s+"
    match += r"Error in MergeDicts\(\)\.\s+"
    match += r"Error detail: MergeDicts\(\)\.commit\(\)\. ValueError\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_dcnm_maintenance_mode_want_00140(monkeypatch) -> None:
    """
    ### Classes and Methods
    - Want()
        - commit()

    ### Summary
    -   Verify Want().commit() catches and re-raises ``ValueError``
        when Want().validate_configs() raises ``ValueError``.
    -   Want().validate_configs() is mocked to raise ``ValueError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def configs():
        yield configs_want(key)

    gen = ResponseGenerator(configs())

    params_test = copy.deepcopy(params)
    params_test.update({"config": gen.next})

    def mock_def():
        raise ValueError("validate_configs ValueError.")

    with does_not_raise():
        instance = Want()
        monkeypatch.setattr(instance, "validate_configs", mock_def)
        instance.config = params_test.get("config")
        instance.params = params_test
        instance.params_spec = ParamsSpec()
        instance.items_key = "switches"
        instance.validator = ParamsValidate()
    match = r"Want\.commit:\s+"
    match += r"Error validating playbook configs against params spec\.\s+"
    match += r"Error detail: validate_configs ValueError\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_dcnm_maintenance_mode_want_00200() -> None:
    """
    ### Classes and Methods
    - Want()
        - config.setter

    ### Summary
    -   Verify Want().config raises ``TypeError`` when config is not a dict.
    """
    with does_not_raise():
        instance = Want()

    match = r"Want\.config\.setter:\s+"
    match += r"expected dict but got str, value NOT_A_DICT\."
    with pytest.raises(TypeError, match=match):
        instance.config = "NOT_A_DICT"


def test_dcnm_maintenance_mode_want_00300() -> None:
    """
    ### Classes and Methods
    - Want()
        - items_key.setter

    ### Summary
    -   Verify Want().items_key raises ``TypeError`` when items_key is not
        a string.
    """
    with does_not_raise():
        instance = Want()

    match = r"Want\.items_key\.setter:\s+"
    match += r"expected string but got set, value {'NOT_A_STRING'}\."
    with pytest.raises(TypeError, match=match):
        instance.items_key = {"NOT_A_STRING"}


def test_dcnm_maintenance_mode_want_00400() -> None:
    """
    ### Classes and Methods
    - Want()
        - params.setter

    ### Summary
    Verify Want().params happy path.
    """
    with does_not_raise():
        instance = Want()
        instance.params = {"state": "merged"}


def test_dcnm_maintenance_mode_want_00410() -> None:
    """
    ### Classes and Methods
    - Want()
        - params.setter

    ### Summary
    -   Verify Want().params raises ``TypeError`` when params is not a dict.
    """
    with does_not_raise():
        instance = Want()

    match = r"Want\.params\.setter:\s+"
    match += r"expected dict but got str, value NOT_A_DICT\."
    with pytest.raises(TypeError, match=match):
        instance.params = "NOT_A_DICT"


def test_dcnm_maintenance_mode_want_00500() -> None:
    """
    ### Classes and Methods
    - Want()
        - params_spec.setter

    ### Summary
    Verify Want().params_spec happy path.
    """
    with does_not_raise():
        instance = Want()
        instance.params_spec = ParamsSpec()


def test_dcnm_maintenance_mode_want_00510() -> None:
    """
    ### Classes and Methods
    - Want()
        - params_spec.setter

    ### Summary
    -   Verify Want().params_spec raises ``TypeError`` when params_spec
        is not an instance of ParamsSpec().
    """
    with does_not_raise():
        instance = Want()

    match = r"Want\.params_spec:\s+"
    match += r"value must be an instance of ParamsSpec\.\s+"
    match += r"Got type str, value NOT_AN_INSTANCE_OF_PARAMS_SPEC\.\s+"
    match += r"Error detail: 'str' object has no attribute 'class_name'\."
    with pytest.raises(TypeError, match=match):
        instance.params_spec = "NOT_AN_INSTANCE_OF_PARAMS_SPEC"


def test_dcnm_maintenance_mode_want_00520() -> None:
    """
    ### Classes and Methods
    - Want()
        - params_spec.setter

    ### Summary
    Verify Want().params_spec raises ``TypeError`` when params_spec
    is not an instance of ParamsSpec(), but IS an instance of another
    class.
    """
    with does_not_raise():
        instance = Want()

    match = r"Want\.params_spec:\s+"
    match += r"value must be an instance of ParamsSpec\.\s+"
    match += r"Got type ParamsValidate, value .* object at 0x.*\."
    with pytest.raises(TypeError, match=match):
        instance.params_spec = ParamsValidate()


def test_dcnm_maintenance_mode_want_00600() -> None:
    """
    ### Classes and Methods
    - Want()
        - validator.setter

    ### Summary
    Verify Want().validator happy path.
    """
    with does_not_raise():
        instance = Want()
        instance.validator = ParamsValidate()


def test_dcnm_maintenance_mode_want_00610() -> None:
    """
    ### Classes and Methods
    - Want()
        - validator.setter

    ### Summary
    -   Verify Want().validator raises ``TypeError`` when validator
        is not an instance of ParamsValidate().
    """
    with does_not_raise():
        instance = Want()

    match = r"Want\.validator:\s+"
    match += r"value must be an instance of ParamsValidate\.\s+"
    match += r"Got type str, value NOT_AN_INSTANCE_OF_PARAMS_VALIDATE\.\s+"
    match += r"Error detail: 'str' object has no attribute 'class_name'\."
    with pytest.raises(TypeError, match=match):
        instance.validator = "NOT_AN_INSTANCE_OF_PARAMS_VALIDATE"


def test_dcnm_maintenance_mode_want_00620() -> None:
    """
    ### Classes and Methods
    - Want()
        - validator.setter

    ### Summary
    Verify Want().validator raises ``TypeError`` when validator
    is not an instance of ParamsValidate(), but IS an instance of
    another class.
    """
    with does_not_raise():
        instance = Want()

    match = r"Want\.validator:\s+"
    match += r"value must be an instance of ParamsValidate\.\s+"
    match += r"Got type ParamsSpec, value .* object at 0x.*\."
    with pytest.raises(TypeError, match=match):
        instance.validator = ParamsSpec()
