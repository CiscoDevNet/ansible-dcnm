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

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"


from ansible_collections.cisco.dcnm.plugins.module_utils.image_policy.payload import (
    Config2Payload, Payload2Config)
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.fixture import \
    load_fixture
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_image_policy.utils import (
    MockAnsibleModule, config2payload_fixture, does_not_raise,
    payload2config_fixture)


def test_image_policy_payload_00110(config2payload: Config2Payload) -> None:
    """
    Class
    - Payload
    - Config2Payload
    Function
    - __init__

    Test
    - Class attributes initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = config2payload
    assert instance.class_name == "Config2Payload"


def test_image_policy_payload_00111(config2payload: Config2Payload) -> None:
    """
    Class
    - Payload
    - Config2Payload
    Function
    - __init__
    - _build_properties

    Test
    - Class properties are initialized to expected values
    """
    with does_not_raise():
        instance = config2payload
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

    Test
    - commit converts config to a proper payload
    """
    key = "test_image_policy_payload_00120"
    data = load_fixture("data_payload")

    config = data.get(key, {}).get("config")
    payload = data.get(key, {}).get("payload")
    with does_not_raise():
        instance = config2payload
        instance.config = config
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

    Test
    - config packages.install is an empty list
    - config packages.ininstall is an empty list
    - commit converts config to a proper payload
    """
    key = "test_image_policy_payload_00120"
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


def test_image_policy_payload_00210(payload2config: Payload2Config) -> None:
    """
    Class
    - Payload
    - Payload2Config
    Function
    - __init__

    Test
    - Class attributes initialized to expected values
    - fail_json is not called
    """
    with does_not_raise():
        instance = payload2config
    assert instance.class_name == "Payload2Config"


def test_image_policy_payload_00211(payload2config: Payload2Config) -> None:
    """
    Class
    - Payload
    - Payload2Config
    Function
    - __init__
    - _build_properties

    Test
    - Class properties are initialized to expected values
    """
    with does_not_raise():
        instance = payload2config
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

    Test
    - commit converts the payload to a proper config
    """
    key = "test_image_policy_payload_00220"
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

    Test
    - payload is missing rpmimages and packageName keys
    - commit converts the payload to a proper config
    """
    key = "test_image_policy_payload_00220"
    data = load_fixture("data_payload")

    config = data.get(key, {}).get("config")
    payload = data.get(key, {}).get("payload")
    with does_not_raise():
        instance = payload2config
        instance.payload = payload
        instance.commit()
    assert config is not None
    assert instance.config == config
