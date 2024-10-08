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
# pylint: disable=unused-import, protected-access, use-implicit-booleaness-not-comparison, unused-variable

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import copy
import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_bootflash import \
    Common
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_bootflash.utils import (
    configs_query, does_not_raise, params_deleted, params_query)


def test_bootflash_common_00000() -> None:
    """
    ### Classes and Methods
    - Common()
        - __init__()

    ### Summary
    __init__() happy path with minimal config.
    - Verify class attributes are initialized to expected values.

    ### Test
    -   Class attributes are initialized to expected values.
    -   Exceptions are not not raised.
    """
    with does_not_raise():
        instance = Common(params_deleted)
    assert instance.bootflash_info.class_name == "BootflashInfo"
    assert instance.params == params_deleted
    assert instance.check_mode is False
    assert instance.config == params_deleted.get("config")
    assert instance.convert_target_to_params.class_name == "ConvertTargetToParams"
    assert instance._rest_send is None
    assert instance.results.class_name == "Results"
    assert instance.results.check_mode is False
    assert instance.results.state == "deleted"
    assert instance.state == "deleted"
    assert instance.switches == [{"ip_address": "192.168.1.2"}]
    assert instance.targets == params_deleted.get("config", {}).get("targets", [])
    assert instance.want == []
    assert instance._valid_states == ["deleted", "query"]


def test_bootflash_common_00010() -> None:
    """
    ### Classes and Methods
    - Common()
        - __init__()

    ### Summary
    ``params`` is missing ``check_mode`` key.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    params = copy.deepcopy(params_deleted)
    params.pop("check_mode")
    match = r"Common\.__init__:\s+"
    match += r"params is missing mandatory key: check_mode\."
    with pytest.raises(ValueError, match=match):
        instance = Common(params)


def test_bootflash_common_00020() -> None:
    """
    ### Classes and Methods
    - Common()
        - __init__()

    ### Summary
    ``params`` contains invalid value for ``check_mode``.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    params = copy.deepcopy(params_deleted)
    params["check_mode"] = "foo"
    match = r"Common\.__init__:\s+"
    match += r"check_mode must be True or False\. Got foo\."
    with pytest.raises(ValueError, match=match):
        instance = Common(params)


def test_bootflash_common_00030() -> None:
    """
    ### Classes and Methods
    - Common()
        - __init__()

    ### Summary
    ``params`` is missing ``state`` key.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    params = copy.deepcopy(params_deleted)
    params.pop("state")
    match = r"Common\.__init__:\s+"
    match += r"params is missing mandatory key: state\."
    with pytest.raises(ValueError, match=match):
        instance = Common(params)


def test_bootflash_common_00040() -> None:
    """
    ### Classes and Methods
    - Common()
        - __init__()

    ### Summary
    ``params`` contains invalid ``state`` key.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    params = copy.deepcopy(params_deleted)
    params["state"] = "foo"
    match = r"Common.__init__:\s+"
    match += r"Invalid state: foo\. Expected one of: deleted,query\."
    with pytest.raises(ValueError, match=match):
        instance = Common(params)


def test_bootflash_common_00050() -> None:
    """
    ### Classes and Methods
    - Common()
        - __init__()

    ### Summary
    ``params`` contains invalid ``config`` key.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    params = copy.deepcopy(params_deleted)
    params["config"] = "foo"
    match = r"Common.__init__:\s+"
    match += r"Expected dict for config\. Got str\."
    with pytest.raises(ValueError, match=match):
        instance = Common(params)


def test_bootflash_common_00060() -> None:
    """
    ### Classes and Methods
    - Common()
        - __init__()

    ### Summary
    ``params.config.targets`` is missing.

    ### Test
    -   ``ValueError`` is not raised.
    -   ``targets`` is initialized to an empty list.
    """
    params = copy.deepcopy(params_deleted)
    params["config"].pop("targets")
    with does_not_raise():
        instance = Common(params)
    assert instance.targets == []


def test_bootflash_common_00070() -> None:
    """
    ### Classes and Methods
    - Common()
        - __init__()

    ### Summary
    ``params`` ``targets`` key is not a list of dict.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    params = copy.deepcopy(params_deleted)
    params["config"]["targets"] = ["foo"]
    match = r"Common.__init__:\s+"
    match += r"Expected list of dict for params\.config\.targets\.\s+"
    match += r"Got list element of type str\."
    with pytest.raises(ValueError, match=match):
        instance = Common(params)


def test_bootflash_common_00080() -> None:
    """
    ### Classes and Methods
    - Common()
        - __init__()

    ### Summary
    ``params.config.switches`` is not a list.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    params = copy.deepcopy(params_deleted)
    params["config"]["switches"] = "foo"
    match = r"Common.__init__:\s+"
    match += r"Expected list of dict for params\.config\.switches\. Got str\."
    with pytest.raises(ValueError, match=match):
        instance = Common(params)


def test_bootflash_common_00090() -> None:
    """
    ### Classes and Methods
    - Common()
        - __init__()

    ### Summary
    ``params`` ``switches`` key is not a list of dict.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    params = copy.deepcopy(params_deleted)
    params["config"]["switches"] = ["foo"]
    match = r"Common.__init__:\s+"
    match += r"Expected list of dict for params\.config\.switches\.\s+"
    match += r"Got list element of type str\."
    with pytest.raises(ValueError, match=match):
        instance = Common(params)


def test_bootflash_common_00200() -> None:
    """
    ### Classes and Methods
    - Common()
        - get_want()

    ### Summary
    - Verify get_want() happy path with minimal config.

    ### Test
    -   instance.want matches expectation.
    -   Exceptions are not not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    params = copy.deepcopy(params_query)
    params["config"] = configs_query(key)
    with does_not_raise():
        instance = Common(params)
        instance.get_want()
    assert instance.want == [
        {
            "ip_address": "192.168.1.2",
            "targets": [{"filepath": "bootflash:/foo.txt", "supervisor": "active"}],
        }
    ]


def test_bootflash_common_00210() -> None:
    """
    ### Classes and Methods
    - Common()
        - get_want()

    ### Summary
    Verify ``get_want()`` behavior when a dictionary in the switches
    list is missing the ``ip_address`` parameter.

    ### Setup
    -   ``configs_query`` contains ``switches[0].ip_address_misspelled``
        rather than the expected ``switches[0].ip_address``.

    ### Test
    -   ValueError is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    params = copy.deepcopy(params_query)
    params["config"] = configs_query(key)
    with does_not_raise():
        instance = Common(params)
    match = r"Common.get_want:\s+"
    match += r"Expected ip_address in switch dict\.\s+"
    match += r"Got.*ip_address_misspelled.*\."
    with pytest.raises(ValueError, match=match):
        instance.get_want()


def test_bootflash_common_00220() -> None:
    """
    ### Classes and Methods
    - Common()
        - get_want()

    ### Summary
    Verify ``get_want()`` behavior when a switch in config.switches contains
    an invalid ``targets`` parameter value.

    ### Setup
    -   ``configs_query`` contains a switch with local ``targets`` parameter,
        and that parameter is a string rather than a list, i.e.
        switches[0].targets = "NOT_A_LIST".

    ### Test
    -   TypeError is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    params = copy.deepcopy(params_query)
    params["config"] = configs_query(key)
    with does_not_raise():
        instance = Common(params)
    match = r"Common.get_want:\s+"
    match += r"Expected list of dictionaries for switch\['targets'\]\.\s+"
    match += r"Got str\."
    with pytest.raises(TypeError, match=match):
        instance.get_want()


def test_bootflash_common_00230() -> None:
    """
    ### Classes and Methods
    - Common()
        - get_want()

    ### Summary
    Verify ``get_want()`` behavior when a switch in config.switches contains
    a ``targets`` parameter value that is missing the ``filepath`` key.

    ### Setup
    -   ``configs_query`` contains a switch with local ``targets`` parameter,
        and that parameter is a list, but a dictionary in the list has
        misspelled ``filepath`` as ``filepath_misspelled`` i.e.
        ``switches[0].targets[0].filepath_misspelled``.

    ### Test
    -   ValueError is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    params = copy.deepcopy(params_query)
    params["config"] = configs_query(key)
    with does_not_raise():
        instance = Common(params)
    match = r"Common.get_want:\s+"
    match += r"Expected filepath in target dict\.\s+"
    match += r"Got.*filepath_misspelled.*\."
    with pytest.raises(ValueError, match=match):
        instance.get_want()


def test_bootflash_common_00240() -> None:
    """
    ### Classes and Methods
    - Common()
        - get_want()

    ### Summary
    Verify ``get_want()`` behavior when a switch in config.switches contains
    a ``targets`` parameter value that is missing the ``supervisor`` key.

    ### Setup
    -   ``configs_query`` contains a switch with local ``targets`` parameter,
        and that parameter is a list of dict, but a dictionary in the list has
        misspelled ``supervisor`` as ``supervisor_misspelled`` i.e.
        ``switches[0].targets[0].supervisor_misspelled``.

    ### Test
    -   ValueError is raised.
    -   Error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    params = copy.deepcopy(params_query)
    params["config"] = configs_query(key)
    with does_not_raise():
        instance = Common(params)
    match = r"Common.get_want:\s+"
    match += r"Expected supervisor in target dict\.\s+"
    match += r"Got.*supervisor_misspelled.*\."
    with pytest.raises(ValueError, match=match):
        instance.get_want()
