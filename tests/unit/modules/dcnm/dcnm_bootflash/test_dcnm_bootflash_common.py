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

# TODO: Add imports as needed
import copy

# import inspect
import pytest
from ansible_collections.cisco.dcnm.plugins.modules.dcnm_bootflash import \
    Common
# from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.bootflash_files import \
#     BootflashFiles
# from ansible_collections.cisco.dcnm.plugins.module_utils.bootflash.convert_target_to_params import \
#     ConvertTargetToParams
# from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
#     ResponseHandler
# from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
#     RestSend
# from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
#     Results
# from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
#     Sender
# from ansible_collections.cisco.dcnm.plugins.module_utils.common.switch_details import \
#     SwitchDetails
# from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
#     ResponseGenerator
# from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_bootflash.utils import (
#     MockAnsibleModule, configs_deleted, does_not_raise, params_deleted,
#     payloads_bootflash_files, responses_ep_all_switches,
#     responses_ep_bootflash_files, targets)
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_bootflash.utils import (
    does_not_raise, params_deleted)


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
    ``params`` ``targets`` key is not a list.

    ### Test
    -   ``ValueError`` is raised.
    -   Error message matches expectation.
    """
    params = copy.deepcopy(params_deleted)
    params["config"]["targets"] = "foo"
    match = r"Common.__init__:\s+"
    match += r"Expected list of dict for params\.config\.targets\. Got str\."
    with pytest.raises(ValueError, match=match):
        instance = Common(params)


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
    with does_not_raise():
        instance = Common(params_deleted)
        instance.get_want()
    # print(f"instance.want: {instance.want}")
    assert instance.want == [
        {
            "ip_address": "192.168.1.2",
            "targets": [{"filepath": "bootflash:/testfile", "supervisor": "active"}],
        }
    ]
