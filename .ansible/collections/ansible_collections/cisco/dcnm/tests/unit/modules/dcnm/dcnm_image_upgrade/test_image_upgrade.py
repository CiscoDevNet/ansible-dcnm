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

from .utils import (MockAnsibleModule, devices_image_upgrade, does_not_raise,
                    image_upgrade_fixture, issu_details_by_ip_address_fixture,
                    params, payloads_ep_image_upgrade,
                    responses_ep_image_upgrade, responses_ep_install_options,
                    responses_ep_issu)


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

    -   ``ip_addresses`` contains the ip addresses of the devices for which
        validation succeeds.

    ### Description

    ImageUpgrade.validate_devices updates the set ImageUpgrade.ip_addresses
    with the ip addresses of the devices for which validation succeeds.
    Currently, validation succeeds for all devices.  This function may be
    updated in the future to handle various failure scenarios.

    ### Expected result

    1.  ``ip_addresses`` will contain {"172.22.150.102", "172.22.150.108"}
    """
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

    devices = [{"ip_address": "172.22.150.102"}, {"ip_address": "172.22.150.108"}]

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

    - ``ValueError`` is called because ``devices`` is None.
    """

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

    -   ``upgrade.nxos`` set to invalid value

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   responses_ep_issu.json indicates that the image has already
        been staged, validated, and the device has already been upgraded
        to the desired version.
    -   responses_ep_install_options.json indicates that the image EPLD
        does not need upgrade.

    ### Expected result

    1.  ``commit`` calls ``_build_payload`` which raises ``ValueError``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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
    instance.devices = gen_devices.next

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
    - ``policy_changed`` is set to False.
    - Verify that payload is built correctly.

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   responses_ep_issu.json indicates that the image has already
        been staged, validated, and the device has already been upgraded
        to the desired version.
    -   responses_ep_install_options.json indicates that the image EPLD
        does not need upgrade.
    -   responses_ep_image_upgrade.json returns a successful response.


    ### Expected result

    1.  instance.payload (built by instance._build_payload and based on
        instance.devices) will equal a payload previously obtained by running
        ansible-playbook against the controller for this scenario, which
        verifies that the non-default values are included in the payload.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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

    # non-default values are set for several options
    instance.devices = gen_devices.next

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

    -   User explicitly sets default values for several options.
    -   ``policy_changed`` is set to True.

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   responses_ep_issu.json indicates that the image has already
        been staged, validated, and the device has already been upgraded to
        the desired version.
    -   responses_ep_install_options.json indicates that the image EPLD
        does not need upgrade.
    -   responses_ep_image_upgrade.json returns a successful response.

    ### Expected result

    -   instance.payload will equal a payload previously obtained by
        running ansible-playbook against the controller for this scenario.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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

    # Default values explicitely set for several options
    instance.devices = gen_devices.next

    with does_not_raise():
        instance.commit()
    assert instance.payload == payloads_ep_image_upgrade(key)


def test_image_upgrade_01040(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test

    - Invalid value for ``nxos.mode``

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   ``devices`` is set to contain an invalid ``nxos.mode`` value.
    -   responses_ep_issu.json indicates that the device has not yet been
        upgraded to the desired version
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.

    ### Expected result

    -   ``commit`` calls ``_build_payload``, which raises ``ValueError``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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
    instance.devices = gen_devices.next

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

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   ``devices`` is set to contain ``nxos.mode`` == "non_disruptive",
        forcing the code to take ``nxos_mode`` == "non_disruptive" path.
    -   responses_ep_issu.json (key_a) indicates that the device has not yet
        been upgraded to the desired version
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.
    -   responses_ep_issu.json (key_b) indicates that the device upgrade has
        completed.

    ### Expected result

    1.  self.payload["issuUpgradeOptions1"]["disruptive"] is False
    2.  self.payload["issuUpgradeOptions1"]["forceNonDisruptive"] is False
    3.  self.payload["issuUpgradeOptions1"]["nonDisruptive"] is True
    """
    method_name = inspect.stack()[0][3]
    key_a = f"{method_name}a"
    key_b = f"{method_name}b"

    def devices():
        yield devices_image_upgrade(key_a)

    gen_devices = ResponseGenerator(devices())

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key_a)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key_a)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key_a)
        # ImageUpgrade.commit
        yield responses_ep_image_upgrade(key_a)
        # ImageUpgrade._wait_for_image_upgrade_to_complete
        yield responses_ep_issu(key_b)

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
    instance.devices = gen_devices.next

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

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   ``devices`` is set to contain ``nxos.mode`` == "force_non_disruptive",
        forcing the code to take ``nxos_mode`` == "force_non_disruptive" path
    -   responses_ep_issu.json (key_a) indicates that the device has not yet
        been upgraded to the desired version
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.
    -   responses_ep_issu.json (key_b) indicates that the device upgrade has
        completed.

    ### Expected result

    1.  self.payload["issuUpgradeOptions1"]["disruptive"] is False
    2.  self.payload["issuUpgradeOptions1"]["forceNonDisruptive"] is True
    3.  self.payload["issuUpgradeOptions1"]["nonDisruptive"] is False
    """
    method_name = inspect.stack()[0][3]
    key_a = f"{method_name}a"
    key_b = f"{method_name}b"

    def devices():
        yield devices_image_upgrade(key_a)

    gen_devices = ResponseGenerator(devices())

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key_a)
        # ImageUpgrade.wait_for_controller
        yield responses_ep_issu(key_a)
        # ImageUpgrade._build_payload
        #     -> ImageInstallOptions.refresh
        yield responses_ep_install_options(key_a)
        # ImageUpgrade.commit
        yield responses_ep_image_upgrade(key_a)
        # ImageUpgrade._wait_for_image_upgrade_to_complete
        yield responses_ep_issu(key_b)

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
    instance.devices = gen_devices.next

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

     ### Setup

     -   ``devices`` is set to a list of one dict for a device to be upgraded.
     -   ``devices`` is set to contain a non-boolean value for
         ``options.nxos.bios_force``.
     -   responses_ep_issu.json indicates that the device has not yet been
         upgraded to the desired version.
     -   responses_ep_install_options.json indicates that EPLD upgrade is
         not needed.

     ### Expected result

     1.  ``_build_payload_issu_options_2`` raises ``TypeError``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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
    instance.devices = gen_devices.next

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

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   ``devices`` is set to contain ``epld.golden`` == True and
        ``upgrade.nxos`` == True.
    -   responses_ep_issu.json indicates that the device has not yet been
        upgraded to the desired version.
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.

    ### Expected result

    1.  ``commit`` calls ``_build_payload`` which raises ``ValueError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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
    instance.devices = gen_devices.next

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

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   ``devices`` is set to contain invalid ``epld.module``.
    -   responses_ep_issu.json indicates that the device has not yet been
        upgraded to the desired version.
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.

    ### Expected result

    1.  ``commit`` calls ``_build_payload`` which raises ``ValueError``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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
    instance.devices = gen_devices.next

    match = r"ImageUpgrade\._build_payload_epld:\s+"
    match += r"options\.epld\.module must either be 'ALL'\s+"
    match += r"or an integer\. Got FOO\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_image_upgrade_01100(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test
    -   Invalid value for ``epld.golden``

    ### Setup
    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   instance.devices is set to contain invalid ``epld.golden``
    -   responses_ep_issu.json indicates that the device has not yet been
        upgraded to the desired version.
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.

    ### Expected result

    1.  ``commit`` calls ``_build_payload`` which raises ``TypeError``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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
    instance.devices = gen_devices.next

    match = r"ImageUpgrade\._build_payload_epld:\s+"
    match += r"options\.epld\.golden must be a boolean\.\s+"
    match += r"Got FOO\."
    with pytest.raises(TypeError, match=match):
        instance.commit()


def test_image_upgrade_01110(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test
    - Invalid value for ``reboot``

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   ``devices`` is set to contain invalid value for ``reboot``.
    -   responses_ep_issu.json indicates that the device has not yet been
        upgraded to the desired version.
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.

    ## Expected result

    1.  ``commit`` calls ``_build_payload`` which raises ``TypeError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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
    instance.devices = gen_devices.next

    match = r"ImageUpgrade\._build_payload_reboot:\s+"
    match += r"reboot must be a boolean\. Got FOO\."
    with pytest.raises(TypeError, match=match):
        instance.commit()


def test_image_upgrade_01120(image_upgrade) -> None:
    """
    ### Classes and Methods
    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test

    - Invalid value for ``options.reboot.config_reload``.

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   ``devices`` is set to contain invalid value for
        ``options.reboot.config_reload``.
    -   responses_ep_issu.json indicates that the device has not yet been
        upgraded to the desired version.
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.

    ### Expected result

    1.  ``commit`` calls ``_build_payload`` which raises ``TypeError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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
    instance.devices = gen_devices.next

    match = "ImageUpgrade._build_payload_reboot_options: "
    match += r"options.reboot.config_reload must be a boolean. Got FOO\."
    with pytest.raises(TypeError, match=match):
        instance.commit()


def test_image_upgrade_01130(image_upgrade) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test

    - Invalid value for options.reboot.write_erase

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   ``devices`` is set to contain invalid value for
        ``options.reboot.write_erase``.
    -   responses_ep_issu.json indicates that the device has not yet been
        upgraded to the desired version.
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.

    ### Expected result

    1.  ``commit`` calls ``_build_payload`` which raises ``TypeError``
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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

    # options.reboot.write_erase is invalid
    instance.devices = gen_devices.next

    match = "ImageUpgrade._build_payload_reboot_options: "
    match += r"options.reboot.write_erase must be a boolean. Got FOO\."
    with pytest.raises(TypeError, match=match):
        instance.commit()


def test_image_upgrade_01140(image_upgrade) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test

    Invalid value for ``options.package.uninstall``.

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   ``devices`` is set to contain invalid value for
        ``options.package.uninstall``
    -   responses_ep_issu.json indicates that the device has not yet been
        upgraded to the desired version.
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.

    ### Expected result

    1.  ``commit`` calls ``_build_payload`` which raises ``TypeError``

    ### NOTES

    1. The corresponding test for options.package.install is missing.
        It's not needed since ``ImageInstallOptions`` will raise exceptions
        on invalid values before ``ImageUpgrade`` has a chance to verify
        the value.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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

    # options.package.uninstall is invalid
    instance.devices = gen_devices.next

    match = "ImageUpgrade._build_payload_package: "
    match += r"options.package.uninstall must be a boolean. Got FOO\."
    with pytest.raises(TypeError, match=match):
        instance.commit()


def test_image_upgrade_01150(image_upgrade) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test

    Invalid value for ``options.package.install``.

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   ``devices`` is set to contain invalid value for
        ``options.package.install``
    -   responses_ep_issu.json indicates that the device has not yet been
        upgraded to the desired version.
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.

    ### Expected result

    1.  ``commit`` calls ``_build_payload`` which calls
        ``ImageInstallOptions.package_install`` which raises
        ``TypeError``.

    ### NOTES
    1.  This test differs from the previous test since ``ImageInstallOptions``
        catches the error sooner.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

    def responses():
        # ImageUpgrade.validate_commit_parameters
        yield responses_ep_issu(key)
        # ImageUpgrade.wait_for_controller
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

    # options.package.install is invalid
    instance.devices = gen_devices.next

    match = r"ImageInstallOptions\.package_install:\s+"
    match += r"package_install must be a boolean value\.\s+"
    match += r"Got FOO\."
    with pytest.raises(TypeError, match=match):
        instance.commit()


def test_image_upgrade_01160(image_upgrade) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            -   ``_build_payload``
            -   ``commit``

    ### Test

    - Invalid value for upgrade.epld

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   ``devices`` is set to contain invalid value for ``upgrade.epld``.
    -   responses_ep_issu.json indicates that the device has not yet been
        upgraded to the desired version.
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.

    ### Expected result

    1.  ``commit`` calls ``_build_payload`` which raises ``TypeError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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

    # upgrade.epld is invalid
    instance.devices = gen_devices.next

    match = "ImageInstallOptions.epld: "
    match += r"epld must be a boolean value. Got FOO\."
    with pytest.raises(TypeError, match=match):
        instance.commit()


def test_image_upgrade_02000(image_upgrade) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            -   ``commit``

    #### Test

    - Bad result code in image upgrade response

    ### Setup

    -   ``devices`` is set to a list of one dict for a device to be upgraded.
    -   responses_ep_issu.json indicates that the device has not yet been
        upgraded to the desired version.
    -   responses_ep_install_options.json indicates that EPLD upgrade is
        not needed.
    -   responses_ep_image_upgrade.json returns RESULT_CODE 500 with
        MESSAGE "Internal Server Error".

    ### Expected result

    1.  ``commit`` raises ``ControllerResponseError`` because
        ``rest_send.result_current`` does not equal "success".
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def devices():
        yield devices_image_upgrade(key)

    gen_devices = ResponseGenerator(devices())

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

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.timeout = 1
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()

    # Valid devices
    instance.devices = gen_devices.next

    match = "ImageUpgrade.commit: failed: "
    match += r"\{'success': False, 'changed': False\}. "
    match += r"Controller response: \{'DATA': 123, "
    match += "'MESSAGE': 'Internal Server Error', 'METHOD': 'POST', "
    match += "'REQUEST_PATH': "
    match += "'https://172.22.150.244:443/appcenter/cisco/ndfc/api/v1/"
    match += "imagemanagement/rest/imageupgrade/upgrade-image', "
    match += r"'RETURN_CODE': 500\}"
    with pytest.raises(ControllerResponseError, match=match):
        instance.commit()


# test getter properties


# test setter properties


MATCH_03000 = r"ImageUpgrade\.bios_force:\s+"
MATCH_03000 += r"instance.bios_force must be a boolean\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(TypeError, match=MATCH_03000), True),
    ],
)
def test_image_upgrade_03000(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``bios_force``

    ### Test

    -   ``bios_force`` does not raise ``TypeError`` if passed a boolean.
    -   ``bios_force`` raises ``TypeError`` if passed a non-boolean.
    -   The default value is set if ``TypeError`` is raised.
    """
    with does_not_raise():
        instance = image_upgrade

    with expected:
        instance.bios_force = value
    if raise_flag is False:
        assert instance.bios_force == value
    else:
        assert instance.bios_force is False


MATCH_03010 = r"ImageUpgrade\.check_interval: instance\.check_interval "
MATCH_03010 += r"must be an integer\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (1, does_not_raise(), False),
        (False, pytest.raises(TypeError, match=MATCH_03010), True),
        ("FOO", pytest.raises(TypeError, match=MATCH_03010), True),
    ],
)
def test_image_upgrade_03010(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``check_interval``

    ### Test

    -   ``check_interval`` does not raise ``TypeError`` if the value is an
        integer
    -   ``check_interval`` raises ``TypeError`` if the value is not an
        integer
    -   The default value is set if ``TypeError`` is raised.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.check_interval = value
    if raise_flag is False:
        assert instance.check_interval == value
    else:
        assert instance.check_interval == 10


MATCH_03020 = r"ImageUpgrade\.check_timeout: instance\.check_timeout "
MATCH_03020 += r"must be an integer\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (1, does_not_raise(), False),
        (False, pytest.raises(TypeError, match=MATCH_03020), True),
        ("FOO", pytest.raises(TypeError, match=MATCH_03020), True),
    ],
)
def test_image_upgrade_03020(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``check_timeout``

    ### Test

    -   ``check_timeout`` does not raise ``TypeError`` if passed an integer.
    -   ``check_timeout`` raises ``TypeError`` if passed a non-integer.
    -   The default value is set if ``TypeError`` is raised.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.check_timeout = value
    if raise_flag is False:
        assert instance.check_timeout == value
    else:
        assert instance.check_timeout == 1800


MATCH_03030 = r"ImageUpgrade\.config_reload: "
MATCH_03030 += r"instance\.config_reload must be a boolean\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(TypeError, match=MATCH_03030), True),
    ],
)
def test_image_upgrade_03030(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``config_reload``

    ### Test

    -   ``config_reload`` does not raise ``TypeError`` if passed a boolean.
    -   ``config_reload`` raises ``TypeError`` if passed a non-boolean.
    -   The default value is set if ``TypeError`` is raised.
    """
    with does_not_raise():
        instance = image_upgrade

    with expected:
        instance.config_reload = value
    if raise_flag is False:
        assert instance.config_reload == value
    else:
        assert instance.config_reload is False


MATCH_03040_COMMON = r"ImageUpgrade.devices:\s+"
MATCH_03040_COMMON += r"instance\.devices must be a python list of dict"

MATCH_03040_FAIL_1 = rf"{MATCH_03040_COMMON}. Got not a list\."
MATCH_03040_FAIL_2 = rf"{MATCH_03040_COMMON}. Got \['not a dict'\]\."

MATCH_03040_FAIL_3 = rf"{MATCH_03040_COMMON}, where each dict contains\s+"
MATCH_03040_FAIL_3 += r"the following keys: ip_address\.\s+"
MATCH_03040_FAIL_3 += r"Got \[\{'bad_key_ip_address': '192.168.1.1'\}\]."

DATA_03040_PASS = [{"ip_address": "192.168.1.1"}]
DATA_03040_FAIL_1 = "not a list"
DATA_03040_FAIL_2 = ["not a dict"]
DATA_03040_FAIL_3 = [{"bad_key_ip_address": "192.168.1.1"}]


@pytest.mark.parametrize(
    "value, expected",
    [
        (DATA_03040_PASS, does_not_raise()),
        (DATA_03040_FAIL_1, pytest.raises(TypeError, match=MATCH_03040_FAIL_1)),
        (DATA_03040_FAIL_2, pytest.raises(TypeError, match=MATCH_03040_FAIL_2)),
        (DATA_03040_FAIL_3, pytest.raises(ValueError, match=MATCH_03040_FAIL_3)),
    ],
)
def test_image_upgrade_03040(image_upgrade, value, expected) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``devices``

    ### Test

    -   ``devices`` does not raise Exception if passed a valid list
        of dict.
    -   ``devices`` raises ``TypeError`` if passed a non-list or a list of
        non-dicts.
    -   ``devices`` raises ``ValueError`` if passed a list of dict where
        dict is missing mandatory key "ip_address".
    """
    instance = image_upgrade

    with expected:
        instance.devices = value


MATCH_03050 = r"ImageUpgrade\.disruptive:\s+"
MATCH_03050 += r"instance\.disruptive must be a boolean\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(TypeError, match=MATCH_03050), True),
    ],
)
def test_image_upgrade_03050(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``disruptive``

    ### Test

    -   ``disruptive`` does not raise ``TypeError`` if passed a boolean.
    -   ``disruptive`` raises ``TypeError`` if passed a non-boolean.
    -   The default value is set if ``TypeError`` is raised.
    """
    instance = image_upgrade

    with expected:
        instance.disruptive = value
    if raise_flag is False:
        assert instance.disruptive == value
    else:
        assert instance.disruptive is True


MATCH_03060 = "ImageUpgrade.epld_golden: "
MATCH_03060 += "instance.epld_golden must be a boolean."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(TypeError, match=MATCH_03060), True),
    ],
)
def test_image_upgrade_03060(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``epld_golden``

    ### Test

    -   ``epld_golden`` does not raise ``TypeError`` if passed a boolean.
    -   ``epld_golden`` raises ``TypeError`` if passed a non-boolean.
    -   The default value is set if ``TypeError`` is raised.
    """
    instance = image_upgrade

    with expected:
        instance.epld_golden = value
    if raise_flag is False:
        assert instance.epld_golden == value
    else:
        assert instance.epld_golden is False


MATCH_03070 = "ImageUpgrade.epld_upgrade: "
MATCH_03070 += "instance.epld_upgrade must be a boolean."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(TypeError, match=MATCH_03070), True),
    ],
)
def test_image_upgrade_03070(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``epld_upgrade``

    ### Test

    -   ``epld_upgrade`` does not raise ``TypeError`` if passed a boolean.
    -   ``epld_upgrade`` raises ``TypeError`` if passed a non-boolean.
    -   The default value is set if ``TypeError`` is raised.
    """
    instance = image_upgrade

    with expected:
        instance.epld_upgrade = value
    if raise_flag is False:
        assert instance.epld_upgrade == value
    else:
        assert instance.epld_upgrade is False


MATCH_03080 = "ImageUpgrade.epld_module: "
MATCH_03080 += "instance.epld_module must be an integer or 'ALL'"


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        ("ALL", does_not_raise(), False),
        (1, does_not_raise(), False),
        (27, does_not_raise(), False),
        ("27", does_not_raise(), False),
        ("FOO", pytest.raises(TypeError, match=MATCH_03080), True),
    ],
)
def test_image_upgrade_03080(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``epld_module``

    ### Test

    -   ``epld_module`` does not raise ``TypeError`` if passed a valid value.
    -   ``epld_module`` raises ``TypeError`` if passed an invalid value.
    -   ``epld_module`` converts valid string values to integer.
    -   The default value ("ALL") is set if ``TypeError`` is raised.
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
        ("FOO", pytest.raises(TypeError, match=MATCH_00140), True),
    ],
)
def test_image_upgrade_03090(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``force_non_disruptive``

    ### Test

    -   ``force_non_disruptive`` does not raise ``TypeError`` if passed
        a boolean.
    -   ``force_non_disruptive`` raises ``TypeError`` if passed a
        non-boolean.
    -   The default value is set if ``TypeError`` is raised.
    """
    instance = image_upgrade

    with expected:
        instance.force_non_disruptive = value
    if raise_flag is False:
        assert instance.force_non_disruptive == value
    else:
        assert instance.force_non_disruptive is False


MATCH_03100 = r"ImageUpgrade\.non_disruptive:\s+"
MATCH_03100 += r"instance\.non_disruptive must be a boolean\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(TypeError, match=MATCH_03100), True),
    ],
)
def test_image_upgrade_03100(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``non_disruptive``

    ### Test

    -   ``non_disruptive`` does not raise ``TypeError`` if passed a boolean.
    -   ``non_disruptive`` raises ``TypeError`` if passed a non-boolean.
    -   The default value is set if ``TypeError`` is raised.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.non_disruptive = value
    if raise_flag is False:
        assert instance.non_disruptive == value
    else:
        assert instance.non_disruptive is False


MATCH_03110 = r"ImageUpgrade\.package_install:\s+"
MATCH_03110 += r"instance\.package_install must be a boolean\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(TypeError, match=MATCH_03110), True),
    ],
)
def test_image_upgrade_03110(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``package_install``

    ### Test

    -   ``package_install`` does not raise ``TypeError`` if passed a boolean.
    -   ``package_install`` raises ``TypeError`` if passed a non-boolean.
    -   The default value is set if ``TypeError`` is raised.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.package_install = value
    if raise_flag is False:
        assert instance.package_install == value
    else:
        assert instance.package_install is False


MATCH_03120 = r"ImageUpgrade\.package_uninstall:\s+"
MATCH_03120 += r"instance.package_uninstall must be a boolean\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(TypeError, match=MATCH_03120), True),
    ],
)
def test_image_upgrade_03120(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``package_uninstall``

    ### Test

    -   ``package_uninstall`` does not raise ``TypeError`` if passed a boolean.
    -   ``package_uninstall`` raises ``TypeError`` if passed a non-boolean.
    -   The default value is set if ``TypeError`` is raised.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.package_uninstall = value
    if raise_flag is False:
        assert instance.package_uninstall == value
    else:
        assert instance.package_uninstall is False


MATCH_03130 = r"ImageUpgrade\.reboot:\s+"
MATCH_03130 += r"instance\.reboot must be a boolean\."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(TypeError, match=MATCH_03130), True),
    ],
)
def test_image_upgrade_03130(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``reboot``

    ### Test

    -   ``reboot`` does not raise ``TypeError`` if passed a boolean.
    -   ``reboot`` raises ``TypeError`` if passed a non-boolean.
    -   The default value is set if ``TypeError`` is raised.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.reboot = value
    if raise_flag is False:
        assert instance.reboot == value
    else:
        assert instance.reboot is False


MATCH_03140 = "ImageUpgrade.write_erase: "
MATCH_03140 += "instance.write_erase must be a boolean."


@pytest.mark.parametrize(
    "value, expected, raise_flag",
    [
        (True, does_not_raise(), False),
        (False, does_not_raise(), False),
        ("FOO", pytest.raises(TypeError, match=MATCH_03140), True),
    ],
)
def test_image_upgrade_03140(image_upgrade, value, expected, raise_flag) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            - ``write_erase``

    ### Test

    -   ``write_erase`` does not raise ``TypeError`` if passed a boolean.
    -   ``write_erase`` raises ``TypeError`` if passed a non-boolean.
    -   The default value is set if ``TypeError`` is raised.
    """
    with does_not_raise():
        instance = image_upgrade
    with expected:
        instance.write_erase = value
    if raise_flag is False:
        assert instance.write_erase == value
    else:
        assert instance.write_erase is False


def test_image_upgrade_04000(image_upgrade) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            -   ``wait_for_controller``

    ### Test

    -   Two switches are added to ``wait_for_controller_done.done``.

    ### Setup

    -   responses_ep_issu_detail.json indicates that both switches are
        upgraded to the desired version.

    ### Description
    ``wait_for_controller_done`` waits until staging, validation,
    and upgrade actions are complete for all ip addresses.  It accesses
    ``SwitchIssuDetailsByIpAddress.actions_in_progress`` and expects
    this to return False.  ``actions_in_progress`` returns True until none of
    the following keys has a value of "In-Progress":

    ```json
    ["imageStaged", "upgrade", "validated"]
    ```

    ### Expected result

    1.  ``instance.wait_for_controller_done.done`` is length 2.
    2.  ``instance.wait_for_controller_done.done`` contains all ip
        addresses in ``ip_addresses``.
    3.  Exceptions are not raised.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.wait_for_controller.
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.timeout = 1
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.ip_addresses = [
            "172.22.150.102",
            "172.22.150.108",
        ]
        instance.wait_for_controller()
    assert len(instance.wait_for_controller_done.done) == 2
    assert "172.22.150.102" in instance.wait_for_controller_done.done
    assert "172.22.150.108" in instance.wait_for_controller_done.done


def test_image_upgrade_04100(image_upgrade) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            -   ``wait_for_controller``

    ### Test

    -   Two switches are added to ``wait_for_controller_done.done``.

    ### Setup

    -   responses_ep_issu_detail.json (all keys) indicate that "validated"
        is "Success" and "upgrade" is "Success" for all switches.
    -   responses_ep_issu_detail.json (key_a) indicates that "imageStaged"
        is "In-Progress" for all switches
    -   responses_ep_issu_detail.json (key_a) indicates that "imageStaged"
        is "Success" for one switch and "In-Progress" for one switch.
    -   responses_ep_issu_detail.json (key_c) indicates that "imageStaged"
        is "Success" for all switches.

    ### Description
    See test_image_upgrade_04000 for functional details.

    This test ensures that the following continue statement in
    ``WaitForControllerDone().commit()`` is hit.

    ```python
    for item in self.todo:
        if item in self.done:
            continue
    ```

    ### Expected result

    1.  ``instance.wait_for_controller_done.done`` is length 2.
    2.  ``instance.wait_for_controller_done.done`` contains all ip
        addresses in ``ip_addresses``.
    3.  Exceptions are not raised.
    """
    method_name = inspect.stack()[0][3]
    key_a = f"{method_name}a"
    key_b = f"{method_name}b"
    key_c = f"{method_name}c"

    def responses():
        # ImageUpgrade.wait_for_controller.
        yield responses_ep_issu(key_a)
        yield responses_ep_issu(key_b)
        yield responses_ep_issu(key_c)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    # rest_send.timeout = 1
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.ip_addresses = [
            "172.22.150.102",
            "172.22.150.108",
        ]
        instance.wait_for_controller()
    assert len(instance.wait_for_controller_done.done) == 2
    assert "172.22.150.102" in instance.wait_for_controller_done.done
    assert "172.22.150.108" in instance.wait_for_controller_done.done


def test_image_upgrade_04110(image_upgrade) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            -   ``wait_for_controller``

    ### Test
    - one switch is added to ipv4_done
    - ValueError is raised due to timeout

    ### Description
    See test_image_upgrade_04000 for functional details.

    ### Expected result

    1.  ``wait_for_controller_done.done`` is length 1.
    2.  ``wait_for_controller_done.done`` contains 172.22.150.102
    3.  ``wait_for_controller_done.done`` does not contain 172.22.150.108
    4.  ``ValueError`` is raised due to timeout.
    5.  ``ValueError`` error message matches expectation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade.wait_for_controller.
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.timeout = 1
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.ip_addresses = [
            "172.22.150.102",
            "172.22.150.108",
        ]

    match = r"ImageUpgrade\.wait_for_controller:\s+"
    match += r"Error WaitForControllerDone\.commit:\s+"
    match += r"Timed out after 1 seconds waiting for controller actions\s+"
    match += r"to complete on items:\s+"
    match += r"\['172.22.150.102', '172.22.150.108'\]\.\s+"
    match += r"The following items did complete: 172\.22\.150\.102\.\."

    with pytest.raises(ValueError, match=match):
        instance.wait_for_controller()

    assert isinstance(instance.ipv4_done, set)
    assert len(instance.wait_for_controller_done.done) == 1
    assert "172.22.150.102" in instance.wait_for_controller_done.done
    assert "172.22.150.108" not in instance.wait_for_controller_done.done


def test_image_upgrade_04120(image_upgrade) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            -   ``_wait_for_image_upgrade_to_complete``

    ### Test

    -   One ip address is added to ``ipv4_done`` due to
        ``issu_detail.upgrade`` == "Success".
    -   ``ValueError`` is raised due one ip address with
        ``issu_detail.upgrade`` == "Failed".

    ### Description

    -   ``_wait_for_image_upgrade_to_complete`` looks at the upgrade status for
        each ip address and waits for it to be "Success" or "Failed".
    -   If all ip addresses are "Success", the module returns.
    -   If any ip address is "Failed", the module raises ``ValueError``.

    ### Expected result

    - ``ipv4_done`` is a set().
    - ``ipv4_done`` has length 1.
    -   ``ipv4_done`` contains 172.22.150.102, upgrade is "Success".
    -   ``ValueError`` is raised because ip address 172.22.150.108,
        upgrade status is "Failed".
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade._wait_for_image_upgrade_to_complete.
        yield responses_ep_issu(key)

    gen_responses = ResponseGenerator(responses())

    sender = Sender()
    sender.ansible_module = MockAnsibleModule()
    sender.gen = gen_responses
    rest_send = RestSend(params)
    rest_send.timeout = 1
    rest_send.unit_test = True
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    with does_not_raise():
        instance = image_upgrade
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.ip_addresses = [
            "172.22.150.102",
            "172.22.150.108",
        ]

    match = r"ImageUpgrade\._wait_for_image_upgrade_to_complete:\s+"
    match += r"Seconds remaining 1790:\s+"
    match += r"upgrade image Failed for cvd-2313-leaf, FDO2112189M,\s+"
    match += r"172\.22\.150\.108, upgrade_percent 50\.\s+"
    match += r"Check the controller to determine the cause\.\s+"
    match += r"Operations > Image Management > Devices > View Details\."

    with pytest.raises(ValueError, match=match):
        instance._wait_for_image_upgrade_to_complete()

    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 1
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" not in instance.ipv4_done


def test_image_upgrade_04130(image_upgrade) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            -   ``_wait_for_image_upgrade_to_complete``

    ### Test

    -   One ip address is added to ``ipv4_done`` because
        issu_detail.upgrade == "Success".
    -   ``ValueError`` is raised due to timeout since one
        ip address returns ``issu_detail.upgrade`` == "In-Progress".

    ### Description
    _wait_for_image_upgrade_to_complete looks at the upgrade status for each
    ip address and waits for it to be "Success" or "Failed".
    In the case where all ip addresses are "Success", the module returns.
    In the case where any ip address is "Failed", the module calls fail_json.
    In the case where any ip address is "In-Progress", the module waits until
    timeout is exceeded.

    ### Expected result

    -   instance.ipv4_done is a set().
    -   instance.ipv4_done has length 1.
    -   instance.ipv4_done contains 172.22.150.102, upgrade is "Success".
    -   ''ValueError'' is raised due to timeout exceeded.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        # ImageUpgrade._wait_for_image_upgrade_to_complete.
        yield responses_ep_issu(key)
        # SwitchIssuDetailsByIpAddress.refresh_super
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
        instance.check_timeout = 1
        instance.results = Results()
        instance.rest_send = rest_send
        instance.issu_detail.rest_send = rest_send
        instance.issu_detail.results = Results()
        instance.ip_addresses = [
            "172.22.150.102",
            "172.22.150.108",
        ]

    match = r"ImageUpgrade\._wait_for_image_upgrade_to_complete:\s+"
    match += r"The following device\(s\) did not complete upgrade:\s+"
    match += r"\['172\.22\.150\.108'\].\s+"
    match += r"Check the controller to determine the cause\.\s+"
    match += r"Operations > Image Management > Devices > View Details\.\s+"
    match += r"And/or check the device\(s\)\s+"
    match += r"\(e\.g\. show install all status\)\."

    with pytest.raises(ValueError, match=match):
        instance._wait_for_image_upgrade_to_complete()

    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 1
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" not in instance.ipv4_done


def test_image_upgrade_04140(image_upgrade) -> None:
    """
    ### Classes and Methods

    -   ``ImageUpgrade``
            -   ``_wait_for_image_upgrade_to_complete``

    ### Test
    For code coverage purposes, ensure that, when two ip addresses are
    processed, `_wait_for_image_upgrade_to_complete` continue statement
    is reached. Specifically:

    ```python
    for ipv4 in self.ip_addresses:
        if ipv4 in self.ipv4_done:
            continue
    ```

    ### Setup

    -   responses_ep_issu_detail.json (all keys) indicate that "imageStaged",
        "validated" are "Success" for all switches.
    -   responses_ep_issu_detail.json (key_a) indicates that "upgrade"
        is "In-Progress" for all switches
    -   responses_ep_issu_detail.json (key_a) indicates that "upgrade"
        is "Success" for one switch and "In-Progress" for one switch.
    -   responses_ep_issu_detail.json (key_c) indicates that "upgrade"
        is "Success" for all switches.

    Description
    _wait_for_image_upgrade_to_complete looks at the upgrade status for each
    ip address and waits for it to be "Success" or "Failed".
    In the case where all ip addresses are "Success", the module returns.
    In the case where any ip address is "In-Progress", the module waits until
    timeout is exceeded.  For this test, we incrementally change the status
    of the ip addresses from "In-Progress" to "Success", until all ip addresses
    are "Success".  This ensures that the conti``nue statement in the for loop
    is reached.

    Expectations:
    - instance.ipv4_done will have length 2
    - instance.ipv4_done contains 172.22.150.102 and 172.22.150.108
    - Exceptions are not raised.
    """
    method_name = inspect.stack()[0][3]
    key_a = f"{method_name}a"
    key_b = f"{method_name}b"
    key_c = f"{method_name}c"

    def responses():
        # ImageUpgrade._wait_for_image_upgrade_to_complete.
        yield responses_ep_issu(key_a)
        # ImageUpgrade._wait_for_image_upgrade_to_complete.
        yield responses_ep_issu(key_b)
        # ImageUpgrade._wait_for_image_upgrade_to_complete.
        yield responses_ep_issu(key_c)

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
        instance.ip_addresses = [
            "172.22.150.102",
            "172.22.150.108",
        ]
        instance._wait_for_image_upgrade_to_complete()

    assert isinstance(instance.ipv4_done, set)
    assert len(instance.ipv4_done) == 2
    assert "172.22.150.102" in instance.ipv4_done
    assert "172.22.150.108" in instance.ipv4_done
