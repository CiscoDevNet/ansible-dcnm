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
# pylint: disable=unused-import
# Some fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-argument

from __future__ import absolute_import, division, print_function

import json

import pytest

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"


from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.payload import (
    Config2Payload, Payload2Config)
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.fixture import \
    load_fixture
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.utils import (
    AnsibleFailJson, MockAnsibleModule, config2payload_fixture, does_not_raise,
    payload2config_fixture)


def test_image_policy_payload_00110(config2payload: Config2Payload) -> None:
    """
    Class
    - Payload
    - Config2Payload
    Function
    - __init__

    Summary
    Verify Config2Payload is initialized properly

    Test
    - Class attributes initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = config2payload
    assert instance.class_name == "Config2Payload"
    assert isinstance(instance.properties, dict)
    assert instance.properties.get("config") == {}
    assert instance.properties.get("payload") == {}


def test_image_policy_payload_00120(config2payload: Config2Payload) -> None:
    """
    Class
    - Payload
    - Config2Payload
    Function
    - commit

    Summary
    Verify Config2Payload coverts a configuration to a proper payload.

    Test
    - fail_json is not called
    - commit converts config to a proper payload
    """
    key = "test_image_policy_payload_00120a"
    data = load_fixture("data_payload")

    config = data.get(key, {}).get("config")
    payload = data.get(key, {}).get("payload")

    print(f"config: {json.dumps(config, indent=4, sort_keys=True)}")
    print(f"payload: {json.dumps(payload, indent=4, sort_keys=True)}")

    with does_not_raise():
        instance = config2payload
        instance.config = config
        instance.log.debug(
            f"00120: config: {json.dumps(config, indent=4, sort_keys=True)}"
        )
        instance.log.debug(
            f"00120: payload: {json.dumps(payload, indent=4, sort_keys=True)}"
        )
        instance.commit()
    assert payload is not None
    assert instance.payload == payload


def test_image_policy_payload_00121(config2payload: Config2Payload) -> None:
    """
    Class
    - Payload
    - Config2Payload
    Function
    - commit

    Summary
    Verify Config2Payload coverts a configuration to a proper payload when
    the packages.install and packages.uninstall keys are empty lists.

    Test
    - config packages.install is an empty list
    - config packages.ininstall is an empty list
    - commit converts config to a proper payload
    """
    key = "test_image_policy_payload_00121a"
    data = load_fixture("data_payload")

    config = data.get(key, {}).get("config")
    payload = data.get(key, {}).get("payload")
    with does_not_raise():
        ansible_module = MockAnsibleModule()
        ansible_module.state = "merged"
        instance = config2payload
        instance.config = config
        instance.commit()
    assert payload is not None
    assert instance.payload == payload


def test_image_policy_payload_00122(config2payload: Config2Payload) -> None:
    """
    Class
    - Payload
    - Config2Payload
    Function
    - commit

    Summary
    Verify Config2Payload.commit() calls fail_json when config is an empty dict

    Test
    - config is set to an empty dict
    - commit calls fail_json
    """
    key = "test_image_policy_payload_00122a"
    data = load_fixture("data_payload")

    config = data.get(key, {}).get("config")

    with does_not_raise():
        ansible_module = MockAnsibleModule()
        ansible_module.state = "merged"
        instance = config2payload
        instance.results = Results()
        instance.config = config
    match = "Config2Payload.commit: config is empty"
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


@pytest.mark.parametrize("state", ["deleted", "query"])
def test_image_policy_payload_00123(config2payload: Config2Payload, state) -> None:
    """
    Class
    - Payload
    - Config2Payload
    Function
    - commit

    Summary
    Verify Config2Payload.commit() behavior for Ansible states
    "query" and "deleted".

    Test
    - payload contains only the policyName key
    - The value of the policyName key == value of the name key in instance.config
    - fail_json is not called
    """
    key = "test_image_policy_payload_00123a"
    data = load_fixture("data_payload")

    config = data.get(key, {}).get("config")
    with does_not_raise():
        ansible_module = MockAnsibleModule()
        ansible_module.state = state
        instance = config2payload
        instance.config = config
        instance.commit()
    assert instance.payload == {"policyName": config["name"]}


MATCH_00130 = (
    r"Config2Payload.payload: payload must be a dictionary\. got .* for value .*"
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ([], pytest.raises(AnsibleFailJson, match=MATCH_00130)),
        ((), pytest.raises(AnsibleFailJson, match=MATCH_00130)),
        (None, pytest.raises(AnsibleFailJson, match=MATCH_00130)),
        (1, pytest.raises(AnsibleFailJson, match=MATCH_00130)),
        (1.1, pytest.raises(AnsibleFailJson, match=MATCH_00130)),
        ("foo", pytest.raises(AnsibleFailJson, match=MATCH_00130)),
        (True, pytest.raises(AnsibleFailJson, match=MATCH_00130)),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00130)),
    ],
)
def test_image_policy_payload_00130(
    config2payload: Config2Payload, value, expected
) -> None:
    """
    Class
    - Payload
    - Config2Payload
    Function
    - payload setter

    Summary
    Verify payload setter error handling

    Test
    - payload accepts a dictionary
    - payload calls fail_json for non-dictionary values
    """
    with does_not_raise():
        instance = config2payload
    with expected:
        instance.payload = value


MATCH_00140 = (
    r"Config2Payload.config: config must be a dictionary\. got .* for value .*"
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ([], pytest.raises(AnsibleFailJson, match=MATCH_00140)),
        ((), pytest.raises(AnsibleFailJson, match=MATCH_00140)),
        (None, pytest.raises(AnsibleFailJson, match=MATCH_00140)),
        (1, pytest.raises(AnsibleFailJson, match=MATCH_00140)),
        (1.1, pytest.raises(AnsibleFailJson, match=MATCH_00140)),
        ("foo", pytest.raises(AnsibleFailJson, match=MATCH_00140)),
        (True, pytest.raises(AnsibleFailJson, match=MATCH_00140)),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00140)),
    ],
)
def test_image_policy_payload_00140(
    config2payload: Config2Payload, value, expected
) -> None:
    """
    Class
    - Payload
    - Payload2Config
    Function
    - config setter

    Summary
    Verify config setter error handling

    Test
    - config accepts a dictionary
    - config calls fail_json for non-dictionary values
    """
    with does_not_raise():
        instance = config2payload
    with expected:
        instance.config = value


def test_image_policy_payload_00210(payload2config: Payload2Config) -> None:
    """
    Class
    - Payload
    - Payload2Config
    Function
    - __init__

    Summary
    Verify Payload2Config is initialized properly

    Test
    - fail_json is not called
    - Class attributes initialized to expected values
    """
    with does_not_raise():
        instance = payload2config
    assert instance.class_name == "Payload2Config"
    assert isinstance(instance.properties, dict)
    assert instance.properties.get("config") == {}
    assert instance.properties.get("payload") == {}


def test_image_policy_payload_00220(payload2config: Payload2Config) -> None:
    """
    Class
    - Payload
    - Payload2Config
    Function
    - commit

    Summary
    Verify Payload2Config coverts a payload to a proper configuration.

    Test
    - fail_json is not called
    - commit converts the payload to a proper config
    """
    key = "test_image_policy_payload_00220a"
    data = load_fixture("data_payload")

    config = data.get(key, {}).get("config")
    payload = data.get(key, {}).get("payload")
    with does_not_raise():
        instance = payload2config
        instance.payload = payload
        instance.commit()
    assert config is not None
    assert instance.config == config


def test_image_policy_payload_00221(payload2config: Payload2Config) -> None:
    """
    Class
    - Payload
    - Payload2Config
    Function
    - commit

    Summary
    Verify Payload2Config coverts a payload to a proper configuration when
    the payload is missing the rpmimages and packageName keys.

    Test
    - payload is missing rpmimages and packageName keys
    - commit converts the payload to a proper config
    - missing mandatory key "type" is added to the config
    """
    key = "test_image_policy_payload_00221a"
    data = load_fixture("data_payload")

    config = data.get(key, {}).get("config")
    payload = data.get(key, {}).get("payload")
    with does_not_raise():
        instance = payload2config
        instance.payload = payload
        instance.commit()
    assert config is not None
    assert instance.config == config


def test_image_policy_payload_00222(payload2config: Payload2Config) -> None:
    """
    Class
    - Payload
    - Payload2Config
    Function
    - commit

    Summary
    Verify Payload2Config.commit() calls fail_json when payload is an empty dict

    Test
    - config is set to an empty dict
    - commit calls fail_json
    """
    key = "test_image_policy_payload_00222a"
    data = load_fixture("data_payload")

    payload = data.get(key, {}).get("payload")
    with does_not_raise():
        ansible_module = MockAnsibleModule()
        ansible_module.state = "merged"
        instance = payload2config
        instance.payload = payload
    match = "Payload2Config.commit: payload is empty"
    with pytest.raises(AnsibleFailJson, match=match):
        instance.commit()


MATCH_00230 = (
    r"Payload2Config.payload: payload must be a dictionary\. got .* for value .*"
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ([], pytest.raises(AnsibleFailJson, match=MATCH_00230)),
        ((), pytest.raises(AnsibleFailJson, match=MATCH_00230)),
        (None, pytest.raises(AnsibleFailJson, match=MATCH_00230)),
        (1, pytest.raises(AnsibleFailJson, match=MATCH_00230)),
        (1.1, pytest.raises(AnsibleFailJson, match=MATCH_00230)),
        ("foo", pytest.raises(AnsibleFailJson, match=MATCH_00230)),
        (True, pytest.raises(AnsibleFailJson, match=MATCH_00230)),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00230)),
    ],
)
def test_image_policy_payload_00230(
    payload2config: Payload2Config, value, expected
) -> None:
    """
    Class
    - Payload
    - Payload2Config
    Function
    - payload setter

    Summary
    Verify payload setter error handling

    Test
    - payload accepts a dictionary
    - payload calls fail_json for non-dictionary values
    """
    with does_not_raise():
        instance = payload2config
    with expected:
        instance.payload = value


MATCH_00240 = (
    r"Payload2Config.config: config must be a dictionary\. got .* for value .*"
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ([], pytest.raises(AnsibleFailJson, match=MATCH_00240)),
        ((), pytest.raises(AnsibleFailJson, match=MATCH_00240)),
        (None, pytest.raises(AnsibleFailJson, match=MATCH_00240)),
        (1, pytest.raises(AnsibleFailJson, match=MATCH_00240)),
        (1.1, pytest.raises(AnsibleFailJson, match=MATCH_00240)),
        ("foo", pytest.raises(AnsibleFailJson, match=MATCH_00240)),
        (True, pytest.raises(AnsibleFailJson, match=MATCH_00240)),
        (False, pytest.raises(AnsibleFailJson, match=MATCH_00240)),
    ],
)
def test_image_policy_payload_00240(
    payload2config: Payload2Config, value, expected
) -> None:
    """
    Class
    - Payload
    - Payload2Config
    Function
    - config setter

    Summary
    Verify config setter error handling

    Test
    - config accepts a dictionary
    - config calls fail_json for non-dictionary values
    """
    with does_not_raise():
        instance = payload2config
    with expected:
        instance.config = value
