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
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

import inspect
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


def test_image_policy_payload_00100() -> None:
    """
    ### Classes and Methods
    - Payload
    - Config2Payload
    Function
    - __init__

    ### Summary
    Verify Config2Payload is initialized properly

    ### Test
    - Class attributes initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = Config2Payload()
    assert instance.class_name == "Config2Payload"
    assert instance._config == {}
    assert instance._params == {}
    assert instance._payload == {}


def test_image_policy_payload_00120(config2payload) -> None:
    """
    ### Classes and Methods
    - Payload
    - Config2Payload
    Function
    - commit

    ### Summary
    Verify Config2Payload coverts a configuration to a proper payload.

    ### Test
    - Exceptions are not raised.
    - commit converts config to a proper payload.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    data = load_fixture("data_payload")
    config = data.get(key, {}).get("config")
    payload = data.get(key, {}).get("payload")

    with does_not_raise():
        instance = config2payload
        instance.config = config
        instance.commit()
    assert payload is not None
    assert instance.payload == payload


def test_image_policy_payload_00121(config2payload) -> None:
    """
    ### Classes and Methods
    - Payload
    - Config2Payload
    Function
    - commit

    ### Summary
    Verify Config2Payload coverts a configuration to a proper payload when
    the packages.install and packages.uninstall keys are empty lists.

    ### Test
    - config packages.install is an empty list
    - config packages.ininstall is an empty list
    - commit converts config to a proper payload
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    data = load_fixture("data_payload")
    config = data.get(key, {}).get("config")
    payload = data.get(key, {}).get("payload")

    with does_not_raise():
        instance = config2payload
        instance.config = config
        instance.commit()
    assert payload is not None
    assert instance.payload == payload


def test_image_policy_payload_00122(config2payload) -> None:
    """
    ### Classes and Methods
    - Payload
    - Config2Payload
    Function
    - commit

    ### Summary
    Verify Config2Payload.commit() calls fail_json when config is an empty dict

    ### Test
    - config is set to an empty dict
    - commit calls fail_json
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    data = load_fixture("data_payload")
    config = data.get(key, {}).get("config")

    with does_not_raise():
        instance = config2payload
        instance.config = config
    match = r"Config2Payload\.commit: config is empty"
    with pytest.raises(ValueError, match=match):
        instance.commit()


@pytest.mark.parametrize("state", ["deleted", "query"])
def test_image_policy_payload_00123(config2payload, state) -> None:
    """
    ### Classes and Methods
    - Payload
    - Config2Payload
    Function
    - commit

    ### Summary
    Verify Config2Payload.commit() behavior for Ansible states
    "query" and "deleted".

    ### Test
    - payload contains only the policyName key
    - The value of the policyName key == value of the name key in instance.config
    - fail_json is not called
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    data = load_fixture("data_payload")
    config = data.get(key, {}).get("config")

    with does_not_raise():
        instance = config2payload
        instance.config = config
        instance.commit()
    assert instance.payload["agnostic"] == config["agnostic"]
    assert instance.payload["policyDescr"] == config["description"]
    assert instance.payload["policyName"] == config["name"]
    assert instance.payload["epldImgName"] == config["epld_image"]
    assert instance.payload["nxosVersion"] == config["release"]
    assert instance.payload["platform"] == config["platform"]
    assert instance.payload["policyType"] == "PLATFORM"


MATCH_00130 = r"Config2Payload\.payload:\s+"
MATCH_00130 += r"payload must be a dictionary\.\s+"
MATCH_00130 += r"got .* for value .*"


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ([], pytest.raises(TypeError, match=MATCH_00130)),
        ((), pytest.raises(TypeError, match=MATCH_00130)),
        (None, pytest.raises(TypeError, match=MATCH_00130)),
        (1, pytest.raises(TypeError, match=MATCH_00130)),
        (1.1, pytest.raises(TypeError, match=MATCH_00130)),
        ("foo", pytest.raises(TypeError, match=MATCH_00130)),
        (True, pytest.raises(TypeError, match=MATCH_00130)),
        (False, pytest.raises(TypeError, match=MATCH_00130)),
    ],
)
def test_image_policy_payload_00130(config2payload, value, expected) -> None:
    """
    ### Classes and Methods
    - Payload
    - Config2Payload
    Function
    - payload.setter

    ### Summary
    Verify payload setter error handling.

    ### Test
    - payload accepts a dictionary.
    - payload raises ``ValueError`` for non-dictionary values.
    """
    with does_not_raise():
        instance = config2payload
    with expected:
        instance.payload = value


MATCH_00140 = r"Config2Payload\.config:\s+"
MATCH_00140 += r"config must be a dictionary\.\s+"
MATCH_00140 += r"got .* for value .*"


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ([], pytest.raises(TypeError, match=MATCH_00140)),
        ((), pytest.raises(TypeError, match=MATCH_00140)),
        (None, pytest.raises(TypeError, match=MATCH_00140)),
        (1, pytest.raises(TypeError, match=MATCH_00140)),
        (1.1, pytest.raises(TypeError, match=MATCH_00140)),
        ("foo", pytest.raises(TypeError, match=MATCH_00140)),
        (True, pytest.raises(TypeError, match=MATCH_00140)),
        (False, pytest.raises(TypeError, match=MATCH_00140)),
    ],
)
def test_image_policy_payload_00140(
    config2payload: Config2Payload, value, expected
) -> None:
    """
    ### Classes and Methods
    - Payload
    - Payload2Config
    Function
    - config setter

    ### Summary
    Verify config setter error handling

    ### Test
    - config accepts a dictionary.
    - config raises ``ValueError``  for non-dictionary values.
    """
    with does_not_raise():
        instance = config2payload
    with expected:
        instance.config = value


def test_image_policy_payload_00200() -> None:
    """
    ### Classes and Methods
    - Payload
    - Payload2Config
    Function
    - __init__

    ### Summary
    Verify Payload2Config is initialized properly

    ### Test
    - Exceptions are not raised.
    - Class attributes initialized to expected values
    """
    with does_not_raise():
        instance = Payload2Config()
    assert instance.class_name == "Payload2Config"
    assert instance._config == {}
    assert instance._params == {}
    assert instance._payload == {}


def test_image_policy_payload_00220(payload2config) -> None:
    """
    ### Classes and Methods
    - Payload
    - Payload2Config
    Function
    - commit

    ### Summary
    Verify Payload2Config coverts a payload to a proper configuration.

    ### Test
    - Exceptions are not raised.
    - commit converts the payload to a proper config.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    data = load_fixture("data_payload")
    config = data.get(key, {}).get("config")
    payload = data.get(key, {}).get("payload")
    with does_not_raise():
        instance = payload2config
        instance.payload = payload
        instance.commit()
    assert config is not None
    assert instance.config == config


def test_image_policy_payload_00221(payload2config) -> None:
    """
    ### Classes and Methods
    - Payload
    - Payload2Config
    Function
    - commit

    ### Summary
    Verify Payload2Config coverts a payload to a proper configuration when
    the payload is missing the rpmimages and packageName keys.

    ### Test
    -   ``payload`` is missing rpmimages and packageName keys.
    -   ``commit`` converts ``payload`` to ``config`` properly.
    -   missing mandatory key ``type`` is added to ``config``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    data = load_fixture("data_payload")
    config = data.get(key, {}).get("config")
    payload = data.get(key, {}).get("payload")

    with does_not_raise():
        instance = payload2config
        instance.payload = payload
        instance.commit()
    assert config is not None
    assert instance.config == config


def test_image_policy_payload_00222(payload2config) -> None:
    """
    ### Classes and Methods
    - Payload
    - Payload2Config
    Function
    - commit

    ### Summary
    Verify Payload2Config.commit() raises ``ValueError`` when ``payload``
    is an empty dict

    ### Test
    -   ``commit`` raises ``ValueError``
    -   ``config`` is set to an empty dict
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    data = load_fixture("data_payload")
    payload = data.get(key, {}).get("payload")

    with does_not_raise():
        instance = payload2config
        instance.payload = payload
    match = r"Payload2Config\.commit: payload is empty"
    with pytest.raises(ValueError, match=match):
        instance.commit()
    assert instance.config == {}


MATCH_00230 = r"Payload2Config\.payload:\s+"
MATCH_00230 += r"payload must be a dictionary\. got .* for value .*"


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ([], pytest.raises(TypeError, match=MATCH_00230)),
        ((), pytest.raises(TypeError, match=MATCH_00230)),
        (None, pytest.raises(TypeError, match=MATCH_00230)),
        (1, pytest.raises(TypeError, match=MATCH_00230)),
        (1.1, pytest.raises(TypeError, match=MATCH_00230)),
        ("foo", pytest.raises(TypeError, match=MATCH_00230)),
        (True, pytest.raises(TypeError, match=MATCH_00230)),
        (False, pytest.raises(TypeError, match=MATCH_00230)),
    ],
)
def test_image_policy_payload_00230(payload2config, value, expected) -> None:
    """
    ### Classes and Methods
    - Payload
    - Payload2Config
    Function
    - payload setter

    ### Summary
    Verify payload setter error handling.

    ### Test
    -   ``payload`` accepts a dictionary.
    -   ``payload`` raises ``TypeError`` for non-dictionary values.
    """
    with does_not_raise():
        instance = payload2config
    with expected:
        instance.payload = value


MATCH_00240 = r"Payload2Config\.config:\s+"
MATCH_00240 += r"config must be a dictionary\. got .* for value .*"


@pytest.mark.parametrize(
    "value, expected",
    [
        ({}, does_not_raise()),
        ([], pytest.raises(TypeError, match=MATCH_00240)),
        ((), pytest.raises(TypeError, match=MATCH_00240)),
        (None, pytest.raises(TypeError, match=MATCH_00240)),
        (1, pytest.raises(TypeError, match=MATCH_00240)),
        (1.1, pytest.raises(TypeError, match=MATCH_00240)),
        ("foo", pytest.raises(TypeError, match=MATCH_00240)),
        (True, pytest.raises(TypeError, match=MATCH_00240)),
        (False, pytest.raises(TypeError, match=MATCH_00240)),
    ],
)
def test_image_policy_payload_00240(payload2config, value, expected) -> None:
    """
    ### Classes and Methods
    - Payload
    - Payload2Config
    Function
    - config setter

    ### Summary
    Verify config setter error handling

    ### Test
    - config accepts a dictionary
    - config calls fail_json for non-dictionary values
    """
    with does_not_raise():
        instance = payload2config
    with expected:
        instance.config = value
