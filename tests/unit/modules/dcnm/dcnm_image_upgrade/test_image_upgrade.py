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
# Some tests require calling protected methods
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from typing import Any, Dict

import inspect
import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError
from ansible_collections.cisco.dcnm.plugins.module_utils.common.response_handler import \
    ResponseHandler
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send_v2 import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_file import \
    Sender
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator

from .utils import (MockAnsibleModule, does_not_raise, image_upgrade_fixture,
                    issu_details_by_ip_address_fixture, params, payloads_ep_image_upgrade,
                    responses_ep_install_options, responses_ep_image_upgrade,
                    responses_ep_issu)

PATCH_MODULE_UTILS = "ansible_collections.cisco.dcnm.plugins.module_utils."
PATCH_IMAGE_UPGRADE = PATCH_MODULE_UTILS + "image_upgrade."

PATCH_IMAGE_UPGRADE_REST_SEND_COMMIT = (
    PATCH_IMAGE_UPGRADE + "image_upgrade.RestSend.commit"
)
PATCH_IMAGE_UPGRADE_REST_SEND_RESPONSE_CURRENT = (
    PATCH_IMAGE_UPGRADE + "image_upgrade.RestSend.response_current"
)
PATCH_IMAGE_UPGRADE_REST_SEND_RESULT_CURRENT = (
    PATCH_IMAGE_UPGRADE + "image_upgrade.RestSend.result_current"
)

REST_SEND_IMAGE_UPGRADE = PATCH_IMAGE_UPGRADE + "image_upgrade.RestSend"
DCNM_SEND_IMAGE_UPGRADE_COMMON = PATCH_IMAGE_UPGRADE + "image_upgrade_common.dcnm_send"
DCNM_SEND_INSTALL_OPTIONS = PATCH_IMAGE_UPGRADE + "install_options.dcnm_send"
DCNM_SEND_ISSU_DETAILS = PATCH_IMAGE_UPGRADE + "switch_issu_details.dcnm_send"


def test_image_upgrade_00000(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            - ``__init__``

    ### Test
    - Class attributes are initialized to expected values.
    """
    with does_not_raise():
        instance = image_upgrade

    assert instance.class_name == "ImageUpgrade"
    assert instance.action == "image_upgrade"
    assert instance.diff == {}
    assert instance.payload is None
    assert instance.saved_response_current == {}
    assert instance.saved_result_current == {}
    assert isinstance(instance.ipv4_done, set)
    assert isinstance(instance.ipv4_todo, set)

    assert instance.conversion.class_name == "ConversionUtils"
    assert instance.ep_upgrade_image.class_name == "EpUpgradeImage"
    assert instance.issu_detail.class_name == "SwitchIssuDetailsByIpAddress"
    assert instance.wait_for_controller_done.class_name == "WaitForControllerDone"

    endpoint_path = "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/"
    endpoint_path += "imageupgrade/upgrade-image"
    assert instance.ep_upgrade_image.path == endpoint_path
    assert instance.ep_upgrade_image.verb == "POST"

    # properties
    assert instance.check_interval == 10
    assert instance.check_timeout == 1800
    assert instance.non_disruptive is False
    assert instance.rest_send is None
    assert instance.results is None

def test_image_upgrade_00010(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            - ``_init_properties``

    ### Test
    - Class properties are initialized to expected values.
    """
    instance = image_upgrade
    instance._init_properties()
    assert instance.bios_force is False
    assert instance.check_interval == 10
    assert instance.check_timeout == 1800
    assert instance.config_reload is False
    assert instance.devices is None
    assert instance.disruptive is True
    assert instance.epld_golden is False
    assert instance.epld_module == "ALL"
    assert instance.epld_upgrade is False
    assert instance.force_non_disruptive is False
    assert instance.non_disruptive is False
    assert instance.force_non_disruptive is False
    assert instance.package_install is False
    assert instance.package_uninstall is False
    assert instance.reboot is False
    assert instance.write_erase is False
    assert instance.valid_nxos_mode == {
        "disruptive",
        "non_disruptive",
        "force_non_disruptive",
    }


def test_image_upgrade_00100(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``validate_devices``

    ### Test
    -   ip_addresses contains the ip addresses of the devices for which
        validation succeeds.

    ### Description
    ImageUpgrade.validate_devices updates the set ImageUpgrade.ip_addresses
    with the ip addresses of the devices for which validation succeeds.
    Currently, validation succeeds for all devices.  This function may be
    updated in the future to handle various failure scenarios.

    ### Expected results

    1.  instance.ip_addresses will contain {"172.22.150.102", "172.22.150.108"}
    """
    devices = [{"ip_address": "172.22.150.102"}, {"ip_address": "172.22.150.108"}]

    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.devices = devices
        instance._validate_devices()  # pylint: disable=protected-access

    assert isinstance(instance.ip_addresses, set)
    assert len(instance.ip_addresses) == 2
    assert "172.22.150.102" in instance.ip_addresses
    assert "172.22.150.108" in instance.ip_addresses


def test_image_upgrade_01000(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``commit``

    ### Test
    - ``ValueError`` is called because devices is None.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield None

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    match = r"ImageUpgrade\._validate_devices:\s+"
    match += r"call instance.devices before calling commit\."

    with pytest.raises(ValueError, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_upgrade_01010(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``commit``

    ### Test
    - upgrade.nxos set to invalid value

    ### Setup
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    -   The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.

    Expected results:

    1.  ``commit`` calls ``_build_payload`` which raises ``ValueError``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.validate_commit_parameters.
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    # Set upgrade.nxos to invalid value "FOO"
    instance.devices = [
        {
            "policy": "KR5M",
            "stage": True,
            "upgrade": {"nxos": "FOO", "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": True},
                "package": {"install": False, "uninstall": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
        }
    ]

    match = r"ImageUpgrade\._build_payload_issu_upgrade: upgrade.nxos must be a\s+"
    match += r"boolean\. Got FOO\."
    with pytest.raises(TypeError, match=match):
        instance.commit()


def test_image_upgrade_01020(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test
    - non-default values are set for several options.
    - policy_changed is set to False.
    - Verify that payload is built correctly.

    ### Setup
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    -   commit -> _build_payload -> issu_details is mocked to simulate
        that the image has already been staged and validated and the
        device has already been upgraded to the desired version.
    -   commit -> _build_payload -> install_options is mocked to simulate
        that the EPLD image does not need upgrade.
    -   The following methods, called by commit() are mocked to do nothing:
        - _wait_for_current_actions_to_complete
        - _wait_for_image_upgrade_to_complete
    -   RestSend is mocked to return a successful response


    Expected results:

    1.  instance.payload (built by instance._build_payload and based on
        instance.devices) will equal a payload previously obtained by running
        ansible-playbook against the controller for this scenario, which verifies
        that the non-default values are included in the payload.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key)
        # ImageUpgrade.commit
        yield responses_ep_image_upgrade(key)
        # ImageUpgrade._wait_for_image_upgrade_to_complete
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    instance.devices = [
        {
            "policy": "KR5M",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": False, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": True},
                "package": {"install": True, "uninstall": False},
                "epld": {"module": 1, "golden": True},
                "reboot": {"config_reload": True, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
        }
    ]

    with does_not_raise():
        instance.commit()
    assert instance.payload == payloads_ep_image_upgrade(key)


def test_image_upgrade_01030(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test
    - User explicitely sets default values for several options
    - policy_changed is set to True

    ### Setup
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   commit -> _build_payload -> issu_details is mocked to simulate
        that the image has already been staged and validated and the
        device has already been upgraded to the desired version.
    -   commit -> _build_payload -> install_options is mocked to simulate
        that the image EPLD does not need upgrade.
    -   The following methods, called by commit() are mocked to do nothing:
        - _wait_for_current_actions_to_complete
        - _wait_for_image_upgrade_to_complete
    -   RestSend is mocked to return a successful response

    ### Expected results

    -   instance.payload will equal a payload previously obtained by
        running ansible-playbook against the controller for this scenario
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key)
        # ImageUpgrade.commit
        yield responses_ep_image_upgrade(key)
        # ImageUpgrade._wait_for_image_upgrade_to_complete
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": True, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    with does_not_raise():
        instance.commit()
    assert instance.payload == payloads_ep_image_upgrade(key)


def test_image_upgrade_01040(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ## Test
    - Invalid value for ``nxos.mode``

    ## Setup
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Method called by commit, _wait_for_current_actions_to_complete
        is mocked to do nothing
    -   instance.devices is set to contain an invalid nxos.mode value

    ### Expected results

    -   ``commit`` calls ``_build_payload``, which raises ``ValueError``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    # nxos.mode is invalid
    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "FOO", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    match = r"ImageUpgrade\._build_payload_issu_options_1:\s+"
    match += r"options.nxos.mode must be one of\s+"
    match += r"\['disruptive', 'force_non_disruptive', 'non_disruptive'\].\s+"
    match += r"Got FOO\."

    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_image_upgrade_01050(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test
    - Force code coverage of ``nxos.mode`` == "non_disruptive" path.

    ### Setup
    -   ``ImageUpgrade.devices`` is set to a list of one dict for a device
        to be upgraded.
    -   Responses are mocked to allow the code to reach ``commit``,
        and for ``commit`` to succeed.
    -   ``devices`` is set to contain ``nxos.mode`` == "non_disruptive",
        forcing the code to take ``nxos_mode`` == "non_disruptive" path.

    ### Expected results

    1.  self.payload["issuUpgradeOptions1"]["disruptive"] is False
    2.  self.payload["issuUpgradeOptions1"]["forceNonDisruptive"] is False
    3.  self.payload["issuUpgradeOptions1"]["nonDisruptive"] is True
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key)
        # ImageUpgrade.commit
        yield responses_ep_image_upgrade(key)
        # ImageUpgrade._wait_for_image_upgrade_to_complete
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    # nxos.mode == non_disruptive
    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "non_disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    with does_not_raise():
        instance.commit()

    assert instance.payload["issuUpgradeOptions1"]["disruptive"] is False
    assert instance.payload["issuUpgradeOptions1"]["forceNonDisruptive"] is False
    assert instance.payload["issuUpgradeOptions1"]["nonDisruptive"] is True


def test_image_upgrade_01060(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test
    -   Force code coverage of ``nxos.mode`` == "force_non_disruptive" path.

    ### Setup:
    -   ``ImageUpgrade.devices`` is set to a list of one dict for a device
        to be upgraded.
    -   Responses are mocked to allow the code to reach ``commit``,
        and for ``commit`` to succeed.
    -   ``devices`` is set to contain ``nxos.mode`` == "force_non_disruptive",
        forcing the code to take ``nxos_mode`` == "force_non_disruptive" path

    Expected results:

    1.  self.payload["issuUpgradeOptions1"]["disruptive"] is False
    2.  self.payload["issuUpgradeOptions1"]["forceNonDisruptive"] is True
    3.  self.payload["issuUpgradeOptions1"]["nonDisruptive"] is False
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key)
        # ImageUpgrade.commit
        yield responses_ep_image_upgrade(key)
        # ImageUpgrade._wait_for_image_upgrade_to_complete
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    # nxos.mode == force_non_disruptive
    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "force_non_disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    with does_not_raise():
        instance.commit()

    assert instance.payload["issuUpgradeOptions1"]["disruptive"] is False
    assert instance.payload["issuUpgradeOptions1"]["forceNonDisruptive"] is True
    assert instance.payload["issuUpgradeOptions1"]["nonDisruptive"] is False


def test_image_upgrade_01070(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``

   ### Test
    -   Invalid value for ``options.nxos.bios_force``

    Setup:
    -   ``ImageUpgrade.devices`` is set to a list of one dict for a device
        to be upgraded.
    -   Responses are mocked to allow the code to reach ``_build_payload``.
    -   ``devices`` is set to contain a non-boolean value for
        ``options.nxos.bios_force``.

    Expected results:

    1.  ``_build_payload_issu_options_2`` raises ``TypeError``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    # options.nxos.bios_force is invalid (FOO)
    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": "FOO"},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    match = r"ImageUpgrade\._build_payload_issu_options_2:\s+"
    match += r"options\.nxos\.bios_force must be a boolean\.\s+"
    match += r"Got FOO\."
    with pytest.raises(TypeError, match=match):
        instance.commit()


def test_image_upgrade_01080(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test
    -   Incompatible values for ``options.epld.golden`` and ``upgrade.nxos``.

    Setup:
    -   ``ImageUpgrade.devices`` is set to a list of one dict for a device
        to be upgraded.
    -   Responses are mocked to allow the code to reach ``commit``,
        and for ``commit`` to succeed.
    -   ``devices`` is set to contain ``epld.golden`` == True and
        ``upgrade.nxos`` == True.

    Expected results:

    1.  ``commit`` calls ``_build_payload`` which raises ``ValueError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    # options.epld.golden is True and upgrade.nxos is True
    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": True},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    match = r"ImageUpgrade\._build_payload_epld:\s+"
    match += r"Invalid configuration for 172\.22\.150\.102\.\s+"
    match += r"If options\.epld.golden is True\s+"
    match += r"all other upgrade options, e\.g\. upgrade\.nxos,\s+"
    match += r"must be False\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_image_upgrade_01090(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test
    -   Invalid value for ``epld.module``

    ### Setup
    -   ``ImageUpgrade.devices`` is set to a list of one dict for a device
        to be upgraded.
    -   Responses are mocked to allow the code to reach ``commit``,
        and for ``commit`` to succeed.
    -   ``devices`` is set to contain invalid ``epld.module``.

    ### Expected results

    1.  ``commit`` calls ``_build_payload`` which raises ``ValueError``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    # options.epld.module is invalid
    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "FOO", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    match = r"ImageUpgrade\._build_payload_epld:\s+"
    match += r"options\.epld\.module must either be 'ALL'\s+"
    match += r"or an integer\. Got FOO\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_image_upgrade_01100(monkeypatch, image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test
    -   Invalid value for ``epld.golden``

    ### Setup
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   Responses are mocked to allow the code to reach ``commit``,
        and for ``commit`` to succeed.
    -   instance.devices is set to contain invalid ``epld.golden``

    ### Expected results

    1.  ``commit`` calls ``_build_payload`` which raises ``TypeError``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    # options.epld.golden is not a boolean
    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": "FOO"},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    match = r"ImageUpgrade\._build_payload_epld:\s+"
    match += r"options\.epld\.golden must be a boolean\.\s+"
    match += r"Got FOO\."
    with pytest.raises(TypeError, match=match):
        instance.commit()


def test_image_upgrade_01110(monkeypatch, image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test
    - Invalid value for ``reboot``

    Setup:
    -   ``ImageUpgrade.devices`` is set to a list of one dict for a device
        to be upgraded.
    -   Responses are mocked to allow the code to reach ``commit``,
        and for ``commit`` to succeed.
    -   ``devices`` is set to contain invalid value for ``reboot``.

    ## Expected result

    1.  ``commit`` calls ``_build_payload`` which raises ``TypeError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    # reboot is invalid
    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": "FOO",
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    match = r"ImageUpgrade\._build_payload_reboot:\s+"
    match += r"reboot must be a boolean\. Got FOO\."
    with pytest.raises(TypeError, match=match):
        instance.commit()


def test_image_upgrade_01120(monkeypatch, image_upgrade) -> None:
    """
    Function
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    Test
    - Invalid value for ``options.reboot.config_reload``.

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   Responses are mocked to allow the code to reach ``commit``,
        and for ``commit`` to succeed.
    -   instance.devices is set to contain invalid value for
        ``options.reboot.config_reload``.

    Expected results:

    1.  ``commit`` calls ``_build_payload`` which raises ``TypeError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    # options.reboot.config_reload is invalid
    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": True,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": "FOO", "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    match = "ImageUpgrade._build_payload_reboot_options: "
    match += r"options.reboot.config_reload must be a boolean. Got FOO\."
    with pytest.raises(TypeError, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_upgrade_00030(monkeypatch, image_upgrade) -> None:
    """
    Function
    - ImageUpgrade.commit

    Test
    - Invalid value for options.reboot.write_erase

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain invalid value for
        options.reboot.write_erase

    Expected results:

    1.  commit calls _build_payload which calls fail_json
    """
    instance = image_upgrade

    key = "test_image_upgrade_00030a"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_issu(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": True,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": "FOO"},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    match = "ImageUpgrade._build_payload_reboot_options: "
    match += r"options.reboot.write_erase must be a boolean. Got FOO\."
    with pytest.raises(ValueError, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_upgrade_00031(monkeypatch, image_upgrade) -> None:
    """
    Function
    - ImageUpgrade.commit

    Test
    - Invalid value for options.package.uninstall

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain invalid value for
        options.package.uninstall

    Expected results:

    1.  commit calls _build_payload which calls fail_json

    NOTES:
    1. The corresponding test for options.package.install is missing.
        It's not needed since ImageInstallOptions will call fail_json
        on invalid values before ImageUpgrade has a chance to verify
        the value.
    """
    instance = image_upgrade

    key = "test_image_upgrade_00031a"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_issu(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": True,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": "FOO"},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    match = "ImageUpgrade._build_payload_package: "
    match += r"options.package.uninstall must be a boolean. Got FOO\."
    with pytest.raises(ValueError, match=match):
        instance.unit_test = True
        instance.commit()


def test_image_upgrade_00032(monkeypatch, image_upgrade) -> None:
    """
    Function
    - ImageUpgrade.commit

    Test
    - Bad result code in image upgrade response

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   ImageUpgrade response (mock_dcnm_send_image_upgrade_commit) is set
        to return RESULT_CODE 500 with MESSAGE "Internal Server Error"

    Expected results:

    1.  commit calls fail_json because self.result will not equal "success"

    """
    instance = image_upgrade

    key = "test_image_upgrade_00032a"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_install_options(key)

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_issu(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_rest_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_image_upgrade(key)

    monkeypatch.setattr(
        PATCH_IMAGE_UPGRADE_REST_SEND_COMMIT, mock_rest_send_image_upgrade
    )
    monkeypatch.setattr(
        PATCH_IMAGE_UPGRADE_REST_SEND_RESPONSE_CURRENT, responses_ep_image_upgrade(key)
    )
    monkeypatch.setattr(
        PATCH_IMAGE_UPGRADE_REST_SEND_RESULT_CURRENT,
        {"success": False, "changed": False},
    )

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    match = "ImageUpgrade.commit_normal_mode: failed: "
    match += r"\{'success': False, 'changed': False\}. "
    match += r"Controller response: \{'DATA': 123, "
    match += "'MESSAGE': 'Internal Server Error', 'METHOD': 'POST', "
    match += "'REQUEST_PATH': "
    match += "'https://172.22.150.244:443/appcenter/cisco/ndfc/api/v1/"
    match += "imagemanagement/rest/imageupgrade/upgrade-image', "
    match += r"'RETURN_CODE': 500\}"
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_image_upgrade_00033(monkeypatch, image_upgrade) -> None:
    """
    Function
    - ImageUpgrade.commit

    Test
    - Invalid value for upgrade.epld

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded
    -   The methods called by commit are mocked to simulate that the
        device has not yet been upgraded to the desired version
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing
    -   instance.devices is set to contain invalid value for
        upgrade.epld

    Expected results:

    1.  commit calls _build_payload which calls fail_json
    """
    instance = image_upgrade

    key = "test_image_upgrade_00033a"

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_issu(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "stage": True,
            "upgrade": {"nxos": True, "epld": "FOO"},
            "options": {
                "package": {
                    "uninstall": False,
                }
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]

    match = "ImageInstallOptions.epld: "
    match += r"epld must be a boolean value. Got FOO\."
    with pytest.raises(ValueError, match=match):
        instance.unit_test = True
        instance.commit()


# test getter properties
# check_interval (see test_image_upgrade_00070)
# check_timeout (see test_image_upgrade_00075)


def test_image_upgrade_00045(monkeypatch, image_upgrade) -> None:
    """
    Function
    - ImageUpgrade.commit
    - ImageUpgradeCommon.response_data getter

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    -   The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.


    Expected results:

    1.  instance.response_data == 121
    """
    with does_not_raise():
        instance = image_upgrade

    key = "test_image_upgrade_00045a"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return {}

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_issu(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    def mock_rest_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_image_upgrade(key)

    monkeypatch.setattr(
        PATCH_IMAGE_UPGRADE_REST_SEND_COMMIT, mock_rest_send_image_upgrade
    )
    monkeypatch.setattr(
        PATCH_IMAGE_UPGRADE_REST_SEND_RESPONSE_CURRENT, responses_ep_image_upgrade(key)
    )
    monkeypatch.setattr(
        PATCH_IMAGE_UPGRADE_REST_SEND_RESULT_CURRENT, {"success": True, "changed": True}
    )

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "NR3F",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": True, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": False},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": True,
        }
    ]
    with does_not_raise():
        instance.commit()
    assert instance.response_data == [121]


def test_image_upgrade_00046(monkeypatch, image_upgrade) -> None:
    """
    Function
    - ImageUpgradeCommon.result
    - ImageUpgrade.commit

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    -   The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.


    Expected results:

    1. instance.result is a list: [{'success': True, 'changed': True}]
    """
    with does_not_raise():
        instance = image_upgrade

    key = "test_image_upgrade_00046a"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return {}

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_issu(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    def mock_rest_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_image_upgrade(key)

    monkeypatch.setattr(
        PATCH_IMAGE_UPGRADE_REST_SEND_COMMIT, mock_rest_send_image_upgrade
    )
    monkeypatch.setattr(
        PATCH_IMAGE_UPGRADE_REST_SEND_RESULT_CURRENT, {"success": True, "changed": True}
    )

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "KR5M",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": False, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": True},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
        }
    ]

    with does_not_raise():
        instance.unit_test = True
        instance.commit()
    assert instance.result == [{"success": True, "changed": True}]


def test_image_upgrade_00047(monkeypatch, image_upgrade) -> None:
    """
    Function
    - ImageUpgradeCommon.response
    - ImageUpgrade.commit

    Setup:
    -   ImageUpgrade.devices is set to a list of one dict for a device
        to be upgraded.
    -   The methods called by commit are mocked to simulate that the
        the image has already been staged and validated and the device
        has already been upgraded to the desired version.
    -   Methods called by commit that wait for current actions, and
        image upgrade, to complete are mocked to do nothing.


    Expected results:

    1. instance.response is a list
    """
    with does_not_raise():
        instance = image_upgrade

    key = "test_image_upgrade_00047a"

    def mock_dcnm_send_install_options(*args, **kwargs) -> Dict[str, Any]:
        return {}

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_issu(key)

    def mock_wait_for_current_actions_to_complete(*args, **kwargs):
        pass

    def mock_wait_for_image_upgrade_to_complete(*args, **kwargs):
        pass

    def mock_rest_send_image_upgrade(*args, **kwargs) -> Dict[str, Any]:
        return responses_ep_image_upgrade(key)

    monkeypatch.setattr(
        PATCH_IMAGE_UPGRADE_REST_SEND_COMMIT, mock_rest_send_image_upgrade
    )
    monkeypatch.setattr(
        PATCH_IMAGE_UPGRADE_REST_SEND_RESPONSE_CURRENT, responses_ep_image_upgrade(key)
    )
    monkeypatch.setattr(
        PATCH_IMAGE_UPGRADE_REST_SEND_RESULT_CURRENT, {"success": True, "changed": True}
    )

    monkeypatch.setattr(DCNM_SEND_INSTALL_OPTIONS, mock_dcnm_send_install_options)
    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)
    monkeypatch.setattr(
        instance,
        "_wait_for_current_actions_to_complete",
        mock_wait_for_current_actions_to_complete,
    )
    monkeypatch.setattr(
        instance,
        "_wait_for_image_upgrade_to_complete",
        mock_wait_for_image_upgrade_to_complete,
    )

    instance.devices = [
        {
            "policy": "KR5M",
            "reboot": False,
            "stage": True,
            "upgrade": {"nxos": False, "epld": True},
            "options": {
                "nxos": {"mode": "disruptive", "bios_force": True},
                "package": {"install": False, "uninstall": False},
                "epld": {"module": "ALL", "golden": False},
                "reboot": {"config_reload": False, "write_erase": False},
            },
            "validate": True,
            "ip_address": "172.22.150.102",
            "policy_changed": False,
        }
    ]

    with does_not_raise():
        instance.commit()
    assert isinstance(instance.response, list)
    assert instance.response[0]["DATA"] == 121


# test setter properties

MATCH_00060 = "ImageUpgrade.bios_force: instance.bios_force must be a boolean."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(ValueError, match=MATCH_00060), True),
    ],
)
def test_image_upgrade_00060(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.bios_force

    Verify that bios_force does not call fail_json if passed a boolean.
    Verify that bios_force does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade

    with expected:
        instance.bios_force = value
    if raise_flag is False:
        assert instance.bios_force == value
    else:
        assert instance.bios_force is False


MATCH_00070 = r"ImageUpgrade\.check_interval: instance\.check_interval "
MATCH_00070 += r"must be an integer\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (1, does_not_raise(), False),
        (False, pytest.raises(ValueError, match=MATCH_00070), True),
        ("FOO", pytest.raises(ValueError, match=MATCH_00070), True),
    ],
)
def test_image_upgrade_00070(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.check_interval

    Summary
    Verify that check_interval does not call fail_json if the value is an integer
    and does call fail_json if the value is not an integer.  Verify that the
    default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.check_interval = value
    if raise_flag is False:
        assert instance.check_interval == value
    else:
        assert instance.check_interval == 10


MATCH_00075 = r"ImageUpgrade\.check_timeout: instance\.check_timeout "
MATCH_00075 += r"must be an integer\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (1, does_not_raise(), False),
        (False, pytest.raises(ValueError, match=MATCH_00075), True),
        ("FOO", pytest.raises(ValueError, match=MATCH_00075), True),
    ],
)
def test_image_upgrade_00075(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.check_timeout

    Summary
    Verify that check_timeout does not call fail_json if the value is an integer
    and does call fail_json if the value is not an integer.  Verify that the
    default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.check_timeout = value
    if raise_flag is False:
        assert instance.check_timeout == value
    else:
        assert instance.check_timeout == 1800


MATCH_00080 = r"ImageUpgrade\.config_reload: "
MATCH_00080 += r"instance\.config_reload must be a boolean\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(ValueError, match=MATCH_00080), True),
    ],
)
def test_image_upgrade_00080(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.config_reload

    Summary
    Verify that config_reload does not call fail_json if passed a boolean.
    Verify that config_reload does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade

    with expected:
        instance.config_reload = value
    if raise_flag is False:
        assert instance.config_reload == value
    else:
        assert instance.config_reload is False


MATCH_00090_COMMON = "ImageUpgrade.devices: "
MATCH_00090_COMMON += "instance.devices must be a python list of dict"

MATCH_00090_FAIL_1 = f"{MATCH_00090_COMMON}. Got not a list."
MATCH_00090_FAIL_2 = rf"{MATCH_00090_COMMON}. Got \['not a dict'\]."

MATCH_00090_FAIL_3 = f"{MATCH_00090_COMMON}, where each dict contains "
MATCH_00090_FAIL_3 += "the following keys: ip_address. "
MATCH_00090_FAIL_3 += r"Got \[\{'bad_key_ip_address': '192.168.1.1'\}\]."

DATA_00090_PASS = [{"ip_address": "192.168.1.1"}]
DATA_00090_FAIL_1 = "not a list"
DATA_00090_FAIL_2 = ["not a dict"]
DATA_00090_FAIL_3 = [{"bad_key_ip_address": "192.168.1.1"}]


@pytest.mark.parametrize(
    "value, expected",
    [
        (DATA_00090_PASS, does_not_raise()),
        (DATA_00090_FAIL_1, pytest.raises(ValueError, match=MATCH_00090_FAIL_1)),
        (DATA_00090_FAIL_2, pytest.raises(ValueError, match=MATCH_00090_FAIL_2)),
        (DATA_00090_FAIL_3, pytest.raises(ValueError, match=MATCH_00090_FAIL_3)),
    ],
)
def test_image_upgrade_00090(image_upgrade, value, expected) -> None:
    """
    Function
    - ImageUpgrade.devices

    Summary
    Verify that devices does not call fail_json if passed a list of dicts
    and does call fail_json if passed a non-list or a list of non-dicts.
    """
    instance = image_upgrade

    with expected:
        instance.devices = value


MATCH_00100 = "ImageUpgrade.disruptive: "
MATCH_00100 += "instance.disruptive must be a boolean."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(ValueError, match=MATCH_00100), True),
    ],
)
def test_image_upgrade_00100x(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.disruptive

    Summary
    Verify that disruptive does not call fail_json if passed a boolean.
    Verify that disruptive does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    instance = image_upgrade

    with expected:
        instance.disruptive = value
    if raise_flag is False:
        assert instance.disruptive == value
    else:
        assert instance.disruptive is True


MATCH_00110 = "ImageUpgrade.epld_golden: "
MATCH_00110 += "instance.epld_golden must be a boolean."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(ValueError, match=MATCH_00110), True),
    ],
)
def test_image_upgrade_00110x(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.epld_golden

    Summary
    Verify that epld_golden does not call fail_json if passed a boolean.
    Verify that epld_golden does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    instance = image_upgrade

    with expected:
        instance.epld_golden = value
    if raise_flag is False:
        assert instance.epld_golden == value
    else:
        assert instance.epld_golden is False


MATCH_00120 = "ImageUpgrade.epld_upgrade: "
MATCH_00120 += "instance.epld_upgrade must be a boolean."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(ValueError, match=MATCH_00120), True),
    ],
)
def test_image_upgrade_00120x(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.epld_upgrade

    Summary
    Verify that epld_upgrade does not call fail_json if passed a boolean.
    Verify that epld_upgrade does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    instance = image_upgrade

    with expected:
        instance.epld_upgrade = value
    if raise_flag is False:
        assert instance.epld_upgrade == value
    else:
        assert instance.epld_upgrade is False


MATCH_00130 = "ImageUpgrade.epld_module: "
MATCH_00130 += "instance.epld_module must be an integer or 'ALL'"


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        ("ALL", does_not_raise(), False),
        (1, does_not_raise(), False),
        (27, does_not_raise(), False),
        ("27", does_not_raise(), False),
        ("FOO", pytest.raises(ValueError, match=MATCH_00130), True),
    ],
)
def test_image_upgrade_00130x(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.epld_module

    Summary
    Verify that epld_module does not call fail_json if passed a valid value.
    Verify that epld_module does call fail_json if passed an invalid value.
    Verify that the default value is set if fail_json is called.
    Verify that valid string values are converted to int()
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.epld_module = value
    if raise_flag is False:
        if value == "ALL":
            assert instance.epld_module == value
        else:
            assert instance.epld_module == int(value)
    else:
        assert instance.epld_module == "ALL"


MATCH_00140 = r"ImageUpgrade\.force_non_disruptive: "
MATCH_00140 += r"instance\.force_non_disruptive must be a boolean\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(ValueError, match=MATCH_00140), True),
    ],
)
def test_image_upgrade_00140x(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.force_non_disruptive

    Summary
    Verify that force_non_disruptive does not call fail_json if passed a boolean.
    Verify that force_non_disruptive does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    instance = image_upgrade

    with expected:
        instance.force_non_disruptive = value
    if raise_flag is False:
        assert instance.force_non_disruptive == value
    else:
        assert instance.force_non_disruptive is False


MATCH_00150 = r"ImageUpgrade\.non_disruptive: "
MATCH_00150 += r"instance\.non_disruptive must be a boolean\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(ValueError, match=MATCH_00150), True),
    ],
)
def test_image_upgrade_00150x(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.non_disruptive

    Summary
    Verify that non_disruptive does not call fail_json if passed a boolean.
    Verify that non_disruptive does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.non_disruptive = value
    if raise_flag is False:
        assert instance.non_disruptive == value
    else:
        assert instance.non_disruptive is False


MATCH_00160 = r"ImageUpgrade\.package_install: "
MATCH_00160 += r"instance\.package_install must be a boolean\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(ValueError, match=MATCH_00160), True),
    ],
)
def test_image_upgrade_00160x(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.package_install

    Summary
    Verify that package_install does not call fail_json if passed a boolean.
    Verify that package_install does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.package_install = value
    if raise_flag is False:
        assert instance.package_install == value
    else:
        assert instance.package_install is False


MATCH_00170 = "ImageUpgrade.package_uninstall: "
MATCH_00170 += "instance.package_uninstall must be a boolean."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(ValueError, match=MATCH_00170), True),
    ],
)
def test_image_upgrade_00170x(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.package_uninstall

    Summary
    Verify that package_uninstall does not call fail_json if passed a boolean.
    Verify that package_uninstall does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.package_uninstall = value
    if raise_flag is False:
        assert instance.package_uninstall == value
    else:
        assert instance.package_uninstall is False


MATCH_00180 = r"ImageUpgrade\.reboot: "
MATCH_00180 += r"instance\.reboot must be a boolean\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(ValueError, match=MATCH_00180), True),
    ],
)
def test_image_upgrade_00180x(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.reboot

    Summary
    Verify that reboot does not call fail_json if passed a boolean.
    Verify that reboot does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.reboot = value
    if raise_flag is False:
        assert instance.reboot == value
    else:
        assert instance.reboot is False


MATCH_00190 = "ImageUpgrade.write_erase: "
MATCH_00190 += "instance.write_erase must be a boolean."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(ValueError, match=MATCH_00190), True),
    ],
)
def test_image_upgrade_00190x(
    image_upgrade, value, expected, raise_flag
) -> None:
    """
    Function
    - ImageUpgrade.write_erase

    Summary
    Verify that write_erase does not call fail_json if passed a boolean.
    Verify that write_erase does call fail_json if passed a non-boolean.
    Verify that the default value is set if fail_json is called.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.write_erase = value
    if raise_flag is False:
        assert instance.write_erase == value
    else:
        assert instance.write_erase is False


def test_image_upgrade_00200x(
    monkeypatch, image_upgrade, issu_details_by_ip_address
) -> None:
    """
    Function
    - ImageUpgrade._wait_for_current_actions_to_complete

    Test
    - Two switches are added to ipv4_done

    Description
    _wait_for_current_actions_to_complete waits until staging, validation,
    and upgrade actions are complete for all ip addresses.  It calls
    SwitchIssuDetailsByIpAddress.actions_in_progress() and expects
    this to return False.  actions_in_progress() returns True until none of
    the following keys has a value of "In-Progress":

    ["imageStaged", "upgrade", "validated"]

    Expectations:
    1.  instance.ipv4_done is a set()
    2.  instance.ipv4_done is length 2
    3.  instance.ipv4_done contains all ip addresses in
        instance.ip_addresses
    4.  fail_json is not called
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_upgrade_00200a"
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    with does_not_raise():
        instance = image_upgrade
        instance.unit_test = True
        instance.issu_detail = issu_details_by_ip_address
        instance.ip_addresses = [
            "172.22.150.102",
            "172.22.150.108",
        ]
        instance.check_interval = 0
        instance._wait_for_current_actions_to_complete()
    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 2
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" in instance.ipv4_done


def test_image_upgrade_00205x(
    monkeypatch, image_upgrade, issu_details_by_ip_address
) -> None:
    """
    Function
    - ImageUpgrade._wait_for_current_actions_to_complete

    Summary
    -   Verify that ipv4_done contains two ip addresses since
        issu_detail is mocked to indicate that no actions are in
        progress for either ip address.
    -   Verify in post analysis that the continue statement is
        hit in the for loop that iterates over ip addresses since
        one of the ip addresses is manually added to ipv4_done.

    Setup
    -   Manually add one ip address to ipv4_done
    -   Set instance.unit_test to True so that instance.ipv4_done is not
        initialized to an empty set in _wait_for_current_actions_to_complete

    Description
    _wait_for_current_actions_to_complete waits until staging, validation,
    and upgrade actions are complete for all ip addresses.  It calls
    SwitchIssuDetailsByIpAddress.actions_in_progress() and expects
    this to return False.  actions_in_progress() returns True until none of
    the following keys has a value of "In-Progress":

    ["imageStaged", "upgrade", "validated"]

    Expectations:
    1.  instance.ipv4_done is a set()
    2.  instance.ipv4_done is length 2
    3.  instance.ipv4_done contains all ip addresses in
        instance.ip_addresses
    4.  fail_json is not called
    5.  (Post analysis) converage tool indicates tha the continue
        statement is hit.
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_upgrade_00205a"
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    with does_not_raise():
        instance = image_upgrade
        instance.unit_test = True
        instance.issu_detail = issu_details_by_ip_address
        instance.ip_addresses = [
            "172.22.150.102",
            "172.22.150.108",
        ]
        instance.check_interval = 0
        instance.ipv4_done.add("172.22.150.102")
        instance._wait_for_current_actions_to_complete()
    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 2
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" in instance.ipv4_done


def test_image_upgrade_00210x(
    monkeypatch, image_upgrade, issu_details_by_ip_address
) -> None:
    """
    Function
    - ImageUpgrade._wait_for_current_actions_to_complete

    Test
    - one switch is added to ipv4_done
    - fail_json is called due to timeout

    See test_image_upgrade_00080 for functional details.

    Expectations:
    - instance.ipv4_done is a set()
    - instance.ipv4_done is length 1
    - instance.ipv4_done contains 172.22.150.102
    - instance.ipv4_done does not contain 172.22.150.108
    - fail_json is called due to timeout
    - fail_json error message is matched
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_upgrade_00210a"
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    with does_not_raise():
        instance = image_upgrade
        instance.unit_test = True
        instance.issu_detail = issu_details_by_ip_address
        instance.ip_addresses = [
            "172.22.150.102",
            "172.22.150.108",
        ]
        instance.check_interval = 1
        instance.check_timeout = 1

    match = "ImageUpgrade._wait_for_current_actions_to_complete: "
    match += "Timed out waiting for actions to complete. "
    match += r"ipv4_done: 172\.22\.150\.102, "
    match += r"ipv4_todo: 172\.22\.150\.102,172\.22\.150\.108\. "
    match += r"check the device\(s\) to determine the cause "
    match += r"\(e\.g\. show install all status\)\."
    with pytest.raises(ValueError, match=match):
        instance._wait_for_current_actions_to_complete()
    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 1
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" not in instance.ipv4_done


def test_image_upgrade_00220x(
    monkeypatch, image_upgrade, issu_details_by_ip_address
) -> None:
    """
    Function
    - ImageUpgrade._wait_for_image_upgrade_to_complete

    Test
    - One ip address is added to ipv4_done due to issu_detail.upgrade == "Success"
    - fail_json is called due one ip address with issu_detail.upgrade == "Failed"

    Description
    _wait_for_image_upgrade_to_complete looks at the upgrade status for each
    ip address and waits for it to be "Success" or "Failed".
    In the case where all ip addresses are "Success", the module returns.
    In the case where any ip address is "Failed", the module calls fail_json.

    Expectations:
    - instance.ipv4_done is a set()
    - instance.ipv4_done has length 1
    - instance.ipv4_done contains 172.22.150.102, upgrade is "Success"
    - Call fail_json on ip address 172.22.150.108, upgrade is "Failed"
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_upgrade_00220a"
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    with does_not_raise():
        instance = image_upgrade
        instance.unit_test = True
        instance.issu_detail = issu_details_by_ip_address
        instance.ip_addresses = [
            "172.22.150.102",
            "172.22.150.108",
        ]
        instance.check_interval = 0
    match = "ImageUpgrade._wait_for_image_upgrade_to_complete: "
    match += "Seconds remaining 1800: "
    match += "upgrade image Failed for cvd-2313-leaf, FDO2112189M, "
    match += r"172\.22\.150\.108, upgrade_percent 50\. "
    match += "Check the controller to determine the cause. "
    match += "Operations > Image Management > Devices > View Details."
    with pytest.raises(ValueError, match=match):
        instance._wait_for_image_upgrade_to_complete()
    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 1
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" not in instance.ipv4_done


def test_image_upgrade_00230x(
    monkeypatch, image_upgrade, issu_details_by_ip_address
) -> None:
    """
    Function
    - ImageUpgrade._wait_for_image_upgrade_to_complete

    Test
    -   One ip address is added to ipv4_done as
        issu_detail.upgrade == "Success"
    -   fail_json is called due to timeout since one
        ip address has value issu_detail.upgrade == "In-Progress"

    Description
    _wait_for_image_upgrade_to_complete looks at the upgrade status for each
    ip address and waits for it to be "Success" or "Failed".
    In the case where all ip addresses are "Success", the module returns.
    In the case where any ip address is "Failed", the module calls fail_json.
    In the case where any ip address is "In-Progress", the module waits until
    timeout is exceeded

    Expectations:
    - instance.ipv4_done is a set()
    - instance.ipv4_done has length 1
    - instance.ipv4_done contains 172.22.150.102, upgrade is "Success"
    - fail_json is called due to timeout exceeded
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_upgrade_00230a"
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    with does_not_raise():
        instance = image_upgrade
        instance.unit_test = True
        instance.issu_detail = issu_details_by_ip_address
        instance.ip_addresses = [
            "172.22.150.102",
            "172.22.150.108",
        ]
        instance.check_interval = 1
        instance.check_timeout = 1

    match = "ImageUpgrade._wait_for_image_upgrade_to_complete: "
    match += r"The following device\(s\) did not complete upgrade: "
    match += r"\['172\.22\.150\.108'\]. "
    match += "Check the controller to determine the cause. "
    match += "Operations > Image Management > Devices > View Details. "
    match += r"And/or check the device\(s\) "
    match += r"\(e\.g\. show install all status\)\."
    with pytest.raises(ValueError, match=match):
        instance._wait_for_image_upgrade_to_complete()
    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 1
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" not in instance.ipv4_done


def test_image_upgrade_00240x(
    monkeypatch, image_upgrade, issu_details_by_ip_address
) -> None:
    """
    Function
    - ImageUpgrade._wait_for_image_upgrade_to_complete

    Summary
    Verify that, when two ip addresses are checked, the method's
    continue statement is reached.  This is verified in post analysis
    using the coverage report.

    Setup
    -   SwitchIssuDetails is mocked to indicate that both ip address
        upgrade status == Success
    -   instance.ipv4_done is set manually to contain one of the ip addresses
    -   Set instance.unit_test to True so that instance.ipv4_done is not
        initialized to an empty set in _wait_for_image_upgrade_to_complete

    Description
    _wait_for_image_upgrade_to_complete looks at the upgrade status for each
    ip address and waits for it to be "Success" or "Failed".
    In the case where all ip addresses are "Success", the module returns.
    Since instance.ipv4_done is manually populated with one of the ip addresses,
    and instance.unit_test is set to True, the method's continue statement is
    reached.  This is verified in post analysis using the coverage report.

    Expectations:
    - instance.ipv4_done will have length 2
    - instance.ipv4_done contains 172.22.150.102 and 172.22.150.108
    - fail_json is not called
    """

    def mock_dcnm_send_issu_details(*args, **kwargs) -> Dict[str, Any]:
        key = "test_image_upgrade_00240a"
        return responses_ep_issu(key)

    monkeypatch.setattr(DCNM_SEND_ISSU_DETAILS, mock_dcnm_send_issu_details)

    with does_not_raise():
        instance = image_upgrade
        instance.unit_test = True
        instance.issu_detail = issu_details_by_ip_address
        instance.ip_addresses = [
            "172.22.150.102",
            "172.22.150.108",
        ]
        instance.check_interval = 1
        instance.check_timeout = 1
        instance.ipv4_done.add("172.22.150.102")
        instance._wait_for_image_upgrade_to_complete()
    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 2
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" in instance.ipv4_done


def test_image_upgrade_00250x(image_upgrade) -> None:
    """
    Function
    - ImageUpgrade._build_payload_issu_upgrade

    Summary
    Verify that fail_json is called when device.upgrade.nxos is not a boolean

    Setup
    -   device.upgrade.nxos is set to "FOO"
    -   device is passed to _build_payload_issu_upgrade
    """
    match = r"ImageUpgrade\._build_payload_issu_upgrade: upgrade\.nxos must "
    match += r"be a boolean\. Got FOO\."

    device = {"upgrade": {"nxos": "FOO"}}

    with does_not_raise():
        instance = image_upgrade
    with pytest.raises(ValueError, match=match):
        instance._build_payload_issu_upgrade(device)


def test_image_upgrade_00260x(image_upgrade) -> None:
    """
    Function
    - ImageUpgrade._build_payload_issu_options_1

    Summary
    Verify that fail_json is called when device.options.nxos.mode is
    set to an invalid value.

    Setup
    -   device.options.nxos.mode is set to invalid value "FOO"
    -   device is passed to _build_payload_issu_options_1
    """
    match = r"ImageUpgrade\._build_payload_issu_options_1: "
    match += r"options\.nxos\.mode must be one of.*Got FOO\."

    device = {"options": {"nxos": {"mode": "FOO"}}}

    with does_not_raise():
        instance = image_upgrade
    with pytest.raises(ValueError, match=match):
        instance._build_payload_issu_options_1(device)


def test_image_upgrade_00270x(image_upgrade) -> None:
    """
    Function
    - ImageUpgrade._build_payload_epld

    Summary
    Verify that fail_json is called when device.upgrade.epld is not a boolean

    Setup
    -   device.upgrade.epld is set to "FOO"
    -   device is passed to _build_payload_epld
    """
    match = r"ImageUpgrade\._build_payload_epld: upgrade.epld must be a "
    match += r"boolean\. Got FOO\."

    device = {"upgrade": {"epld": "FOO"}}

    with does_not_raise():
        instance = image_upgrade
    with pytest.raises(ValueError, match=match):
        instance._build_payload_epld(device)


def test_image_upgrade_00280x(image_upgrade) -> None:
    """
    Function
    - ImageUpgrade._build_payload_package

    Summary
    Verify that fail_json is called when device.options.package.install
    is not a boolean

    Setup
    -   device.options.package.install is set to "FOO"
    -   device is passed to _build_payload_package
    """
    match = r"ImageUpgrade\._build_payload_package: options.package.install "
    match += r"must be a boolean\. Got FOO\."

    device = {"options": {"package": {"install": "FOO"}}}

    with does_not_raise():
        instance = image_upgrade
    with pytest.raises(ValueError, match=match):
        instance._build_payload_package(device)


def test_image_upgrade_00281x(image_upgrade) -> None:
    """
    Function
    - ImageUpgrade._build_payload_package

    Summary
    Verify that fail_json is called when device.options.package.uninstall
    is not a boolean

    Setup
    -   device.options.package.install is set to a boolean
    -   device.options.package.uninstall is set to "FOO"
    -   device is passed to _build_payload_package
    """
    match = r"ImageUpgrade\._build_payload_package: options.package.uninstall "
    match += r"must be a boolean\. Got FOO\."

    device = {"options": {"package": {"install": True, "uninstall": "FOO"}}}

    with does_not_raise():
        instance = image_upgrade
    with pytest.raises(ValueError, match=match):
        instance._build_payload_package(device)
