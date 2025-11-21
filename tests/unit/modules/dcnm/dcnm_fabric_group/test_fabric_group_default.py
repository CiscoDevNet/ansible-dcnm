# Copyright (c) 2025 Cisco and/or its affiliates.
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
# pylint: disable=unused-variable
# pylint: disable=invalid-name
# pylint: disable=line-too-long
# pylint: disable=too-many-lines
"""
Unit tests for FabricGroupDefault class in module_utils/fabric_group/fabric_group_default.py
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results_v2 import Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import Sender
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.fabric_group_default import FabricGroupDefault
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric_group.fixture import load_fixture
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric_group.utils import (
    MockAnsibleModule,
    does_not_raise,
    params,
)


def responses_template_get(key: str) -> dict[str, str]:
    """
    Return responses for TemplateGet
    """
    data_file = "responses_TemplateGet"
    data = load_fixture(data_file).get(key)
    print(f"{data_file}: {key} : {data}")
    return data


@pytest.fixture(name="fabric_group_default")
def fabric_group_default_fixture():
    """
    Return FabricGroupDefault() instance.
    """
    return FabricGroupDefault()


def test_fabric_group_default_00000(fabric_group_default) -> None:
    """
    # Summary

    Verify class initialization

    ## Classes and Methods

    - FabricGroupDefault.__init__()

    ## Test

    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_group_default
    assert instance.class_name == "FabricGroupDefault"
    assert instance.action == "fabric_group_default"
    assert instance._fabric_group_default_config == {}
    assert instance._fabric_group_name == ""
    assert instance._config_nv_pairs == {}
    assert instance._config_top_level == {}
    assert instance._parameter_names == []
    assert instance._template_name == "MSD_Fabric"


def test_fabric_group_default_00010(fabric_group_default) -> None:
    """
    # Summary

    Verify fabric_group_name property setter and getter

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault.fabric_group_name (setter/getter)

    ## Test

    - fabric_group_name is set to "MFG1"
    - fabric_group_name returns "MFG1"
    """
    with does_not_raise():
        instance = fabric_group_default
        instance.fabric_group_name = "MFG1"
    assert instance.fabric_group_name == "MFG1"


def test_fabric_group_default_00020(fabric_group_default) -> None:
    """
    # Summary

    Verify rest_send property setter and getter

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault.rest_send (setter/getter)

    ## Test

    - rest_send is set to RestSend() instance
    - rest_send returns RestSend() instance
    """
    with does_not_raise():
        instance = fabric_group_default
        rest_send = RestSend(params)
        instance.rest_send = rest_send
    assert instance.rest_send == rest_send


def test_fabric_group_default_00021(fabric_group_default) -> None:
    """
    # Summary

    Verify ValueError is raised when rest_send is set without params

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault.rest_send (setter)

    ## Test

    - ValueError is raised with expected message
    """
    match = r"FabricGroupDefault\.rest_send must be set to an "
    match += r"instance of RestSend with params set\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_default
        rest_send = RestSend({})
        instance.rest_send = rest_send


def test_fabric_group_default_00030(fabric_group_default) -> None:
    """
    # Summary

    Verify results property setter and getter

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault.results (setter/getter)

    ## Test

    - results is set to Results() instance
    - results returns Results() instance
    - results properties are set correctly
    """
    with does_not_raise():
        instance = fabric_group_default
        results = Results()
        instance.results = results
    assert instance.results == results
    assert instance.results.action == "fabric_group_default"
    assert False in instance.results.changed


def test_fabric_group_default_00031(fabric_group_default) -> None:
    """
    # Summary

    Verify ValueError is raised when results is set to non-Results instance

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault.results (setter)

    ## Test

    - ValueError is raised with expected message
    """
    match = r"FabricGroupDefault\.results must be set to an "
    match += r"instance of Results\."

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_default
        instance.results = "not a Results instance"


def test_fabric_group_default_00040(fabric_group_default) -> None:
    """
    # Summary

    Verify commit() raises ValueError when fabric_group_name is not set

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault.commit()

    ## Test

    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    match = r"FabricGroupDefault\.commit: "
    match += r"fabric_group_name must be set\."

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_default
        instance.rest_send = rest_send
        instance.commit()


def test_fabric_group_default_00041(fabric_group_default) -> None:
    """
    # Summary

    Verify commit() raises ValueError when rest_send params is not set

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault.commit()

    ## Test

    - ValueError is raised with expected message
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    match = r"FabricGroupDefault\.commit: "
    match += r"rest_send must be set to an instance of RestSend with params set\."

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    rest_send = RestSend({})
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_default
        instance.fabric_group_name = "MFG1"
        instance.commit()


def test_fabric_group_default_00050(fabric_group_default) -> None:
    """
    # Summary

    Verify commit() builds default config successfully

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault.commit()

    ## Test

    - commit() is called successfully
    - config contains expected keys and values
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_template_get(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = fabric_group_default
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.commit()

    assert instance.config.get("fabricName") == "MFG1"
    assert instance.config.get("fabricTechnology") == "VXLANFabric"
    assert instance.config.get("fabricType") == "MSD"
    assert instance.config.get("templateName") == "MSD_Fabric"
    assert instance.config.get("nvPairs") is not None
    assert isinstance(instance.config.get("nvPairs"), dict)
    assert instance.config["nvPairs"].get("FABRIC_NAME") == "MFG1"


def test_fabric_group_default_00060(fabric_group_default) -> None:
    """
    # Summary

    Verify config property returns default fabric group config

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault.config (property)

    ## Test

    - config returns empty dict before commit
    """
    with does_not_raise():
        instance = fabric_group_default

    assert instance.config == {}


def test_fabric_group_default_00070(fabric_group_default) -> None:
    """
    # Summary

    Verify _skip() method correctly identifies parameters to skip

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault._skip()

    ## Test

    - _skip() returns True for parameters with _PREV suffix
    - _skip() returns True for DCNM_ID parameter
    - _skip() returns False for other parameters
    """
    with does_not_raise():
        instance = fabric_group_default

    assert instance._skip("BGP_AS_PREV") is True
    assert instance._skip("UNDERLAY_IS_V6_PREV") is True
    assert instance._skip("DCNM_ID") is True
    assert instance._skip("BGP_AS") is False
    assert instance._skip("FABRIC_NAME") is False
    assert instance._skip("DEPLOYMENT_FREEZE") is False


def test_fabric_group_default_00080(fabric_group_default) -> None:
    """
    # Summary

    Verify _build_config_top_level() builds correct top-level config

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault._build_config_top_level()

    ## Test

    - _build_config_top_level() populates _config_top_level correctly
    """
    with does_not_raise():
        instance = fabric_group_default
        instance.fabric_group_name = "MFG1"
        instance._build_config_top_level()

    assert instance._config_top_level["fabricName"] == "MFG1"
    assert instance._config_top_level["fabricTechnology"] == "VXLANFabric"
    assert instance._config_top_level["fabricType"] == "MSD"
    assert instance._config_top_level["templateName"] == "MSD_Fabric"


def test_fabric_group_default_00090(fabric_group_default) -> None:
    """
    # Summary

    Verify commit() handles template retrieval errors

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault.commit()
    - FabricGroupDefault._get_template()

    ## Test

    - ValueError is raised when template retrieval fails
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_template_get(f"{key}")

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.timeout = 1
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    match = r"FabricGroupDefault\._get_template: "
    match += r"Failed to retrieve template:"

    with pytest.raises(ValueError, match=match):
        instance = fabric_group_default
        instance.rest_send = rest_send
        instance.results = Results()
        instance.fabric_group_name = "MFG1"
        instance.commit()


def test_fabric_group_default_00100(fabric_group_default) -> None:
    """
    # Summary

    Verify _set_parameter_names() extracts parameter names from template

    ## Classes and Methods

    - FabricGroupDefault.__init__()
    - FabricGroupDefault._set_parameter_names()

    ## Test

    - _set_parameter_names() populates _parameter_names list
    """
    with does_not_raise():
        instance = fabric_group_default
        instance._template = {
            "parameters": [
                {"name": "FABRIC_NAME", "defaultValue": ""},
                {"name": "BGP_AS", "defaultValue": "65000"},
                {"name": "DEPLOYMENT_FREEZE", "defaultValue": "false"},
            ]
        }
        instance._set_parameter_names()

    assert "FABRIC_NAME" in instance._parameter_names
    assert "BGP_AS" in instance._parameter_names
    assert "DEPLOYMENT_FREEZE" in instance._parameter_names
    assert len(instance._parameter_names) == 3
