#
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

from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Allen Robel"

import copy
import inspect
import json
import logging
from time import sleep

from ..common.api.v1.imagemanagement.rest.imageupgrade.imageupgrade import EpUpgradeImage
from ..common.conversion import ConversionUtils
from ..common.exceptions import ControllerResponseError
from ..common.properties import Properties
from ..common.results import Results
from ..image_upgrade.install_options import ImageInstallOptions
from .switch_issu_details import SwitchIssuDetailsByIpAddress
from .wait_for_controller_done import WaitForControllerDone


@Properties.add_rest_send
@Properties.add_results
class ImageUpgrade:
    """
    ### Summary
    Upgrade the image on one or more switches.


    ### Usage example
    ```python
    # params is typically obtained from ansible_module.params
    # but can also be specified manually, like below.
    params = {"check_mode": False, "state": "merged"}
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender
    results = Results()

    upgrade = ImageUpgrade()
    upgrade.rest_send = rest_send
    upgrade.results = results
    upgrade.devices = devices # see Example devices structure below
    upgrade.commit()
    data = upgrade.data
    ```

    ### Endpoint:
    -   path: /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupgrade/upgrade-image
    -   verb: POST

    ### Example devices structure

    ```python
    devices = [
        {
            'policy': 'KR3F',
            'ip_address': '172.22.150.102',
            'policy_changed': False
            'stage': False,
            'validate': True,
            'upgrade': {
                'nxos': True,
                'epld': False
            },
            'options': {
                'nxos': {
                    'mode': 'non_disruptive'
                    'bios_force': False
                },
                'epld': {
                    'module': 'ALL',
                    'golden': False
                },
                'reboot': {
                    'config_reload': False,
                    'write_erase': False
                },
                'package': {
                    'install': False,
                    'uninstall': False
                }
            },
        },
        {
            "etc...": "etc..."
        }
    ]
    ```

    ### Example request body

    - Yes, the keys below are misspelled in the request body:
        -   ``pacakgeInstall``
        -   ``pacakgeUnInstall``

        ```json
        {
            "devices": [
                {
                    "serialNumber": "FDO211218HH",
                    "policyName": "NR1F"
                }
            ],
            "issuUpgrade": true,
            "issuUpgradeOptions1": {
                "nonDisruptive": true,
                "forceNonDisruptive": false,
                "disruptive": false
            },
            "issuUpgradeOptions2": {
                "biosForce": false
            },
            "epldUpgrade": false,
            "epldOptions": {
                "moduleNumber": "ALL",
                "golden": false
            },
            "reboot": false,
            "rebootOptions": {
                "configReload": "false",
                "writeErase": "false"
            },
            "pacakgeInstall": false,
            "pacakgeUnInstall": false
        }
        ```

    ### Response bodies
    -   Responses are text, not JSON, and are returned immediately.
    -   Responses do not contain useful information. We need to poll
        the controller to determine when the upgrade is complete.
        Basically, we ignore these responses in favor of the poll
        responses.
    -   If an action is in progress, text is returned:
        ``Action in progress for some of selected device(s).
        Please try again after completing current action.``
    -   If an action is not in progress, text is returned:
        ``3``
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.action = "image_upgrade"
        self.diff: dict = {}
        # Used in _wait_for_upgrade_to_complete()
        self.ipv4_done = set()
        self.ipv4_todo = set()
        self.payload = None
        self.saved_response_current: dict = {}
        self.saved_result_current: dict = {}

        self.conversion = ConversionUtils()
        self.ep_upgrade_image = EpUpgradeImage()
        self.install_options = ImageInstallOptions()
        self.issu_detail = SwitchIssuDetailsByIpAddress()
        self.wait_for_controller_done = WaitForControllerDone()

        self._rest_send = None
        self._results = None

        self._init_properties()

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

    def _init_properties(self) -> None:
        """
        Initialize properties used by this class.

        Review these later since we are no longer calling this class
        per-switch given the payload structure is not amenable to that.
        Consider removing some of these.
        """
        # self.ip_addresses is used in:
        #   self._wait_for_current_actions_to_complete()
        #   self._wait_for_image_upgrade_to_complete()
        self.ip_addresses: set = set()

        self.properties = {}
        self._bios_force = False
        self._check_interval = 10  # seconds
        self._check_timeout = 1800  # seconds
        self._config_reload = False
        self._devices = None
        self._disruptive = True
        self._epld_golden = False
        self._epld_module = "ALL"
        self._epld_upgrade = False
        self._force_non_disruptive = False
        self._non_disruptive = False
        self._package_install = False
        self._package_uninstall = False
        self._reboot = False
        self._write_erase = False

        self.valid_nxos_mode: set = set()
        self.valid_nxos_mode.add("disruptive")
        self.valid_nxos_mode.add("non_disruptive")
        self.valid_nxos_mode.add("force_non_disruptive")

    # We used to have a prune_devices() method here, but this
    # is now done in dcnm_image_upgrade.py.  Consider moving
    # that code here later.

    def build_diff(self) -> None:
        """
        ### Summary
        Build the diff of the image validate operation.

        ### Raises
        None
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}"
        self.log.debug(msg)

        self.diff: dict = {}

        for ipv4 in self.ipv4_done:
            self.issu_detail.filter = ipv4

            if ipv4 not in self.diff:
                self.diff[ipv4] = {}

            self.diff[ipv4]["action"] = self.action
            self.diff[ipv4]["ip_address"] = self.issu_detail.ip_address
            self.diff[ipv4]["logical_name"] = self.issu_detail.device_name
            self.diff[ipv4]["policy_name"] = self.issu_detail.policy
            self.diff[ipv4]["serial_number"] = self.issu_detail.serial_number
            msg = f"{self.class_name}.{method_name}: "
            msg += f"self.diff[{ipv4}]: "
            msg += f"{json.dumps(self.diff[ipv4], indent=4)}"
            self.log.debug(msg)

    def _validate_devices(self) -> None:
        """
        1.  Perform any pre-upgrade validations
            a. Verify that self.devices is set
        2.  Populate self.ip_addresses with the ip_address of all
            switches which can be upgraded.  This is used in
            _wait_for_current_actions_to_complete
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}: "
        msg = f"self.devices: {json.dumps(self.devices, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        if self.devices is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "call instance.devices before calling commit."
            raise ValueError(msg)

        self.issu_detail.refresh()
        for device in self.devices:
            self.issu_detail.filter = device.get("ip_address")

            # Any device validation from issu_detail would go here.
            # We used to fail_json if upgrade == "Failed" but that
            # forced users to have to reset the upgrade state on the
            # controller.  We now allow the upgrade to proceed if
            # upgrade == "Failed".  But let's leave this method here
            # in case we want to add more validation in the future.

            # used in self._wait_for_current_actions_to_complete()
            self.ip_addresses.add(str(self.issu_detail.ip_address))

    def _build_payload(self, device) -> None:
        """
        Build the request payload to upgrade the switches.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED {self.class_name}.{method_name}: "
        msg += f"device {device}"
        self.log.debug(msg)

        # issu_detail.refresh() has already been called in _validate_devices()
        # so no need to call it here.
        self.issu_detail.filter = device.get("ip_address")

        self.install_options.serial_number = self.issu_detail.serial_number
        # install_options will fail_json if any of these are invalid
        # so no need to validate these here.
        self.install_options.policy_name = device.get("policy", None)
        self.install_options.epld = device.get("upgrade", {}).get("epld", None)
        self.install_options.nxos = device.get("upgrade", {}).get("nxos", None)
        self.install_options.package_install = (
            device.get("options", {}).get("package", {}).get("install", None)
        )
        self.log.debug("Calling install_options.refresh()")
        self.install_options.refresh()

        # devices_to_upgrade must currently be a single device
        devices_to_upgrade: list = []

        payload_device: dict = {}
        payload_device["serialNumber"] = self.issu_detail.serial_number
        payload_device["policyName"] = device.get("policy")
        devices_to_upgrade.append(payload_device)

        self.payload: dict = {}
        self.payload["devices"] = devices_to_upgrade

        self._build_payload_issu_upgrade(device)
        self._build_payload_issu_options_1(device)
        self._build_payload_issu_options_2(device)
        self._build_payload_epld(device)
        self._build_payload_reboot(device)
        self._build_payload_reboot_options(device)
        self._build_payload_package(device)

        msg = f"EXITING _build_payload: payload {json.dumps(self.payload, indent=4, sort_keys=True)}"
        self.log.debug(msg)

    def _build_payload_issu_upgrade(self, device) -> None:
        """
        Build the issuUpgrade portion of the payload.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}."
        self.log.debug(msg)

        nxos_upgrade = device.get("upgrade").get("nxos")
        nxos_upgrade = self.conversion.make_boolean(nxos_upgrade)
        if not isinstance(nxos_upgrade, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "upgrade.nxos must be a boolean. "
            msg += f"Got {nxos_upgrade}."
            raise TypeError(msg)
        self.payload["issuUpgrade"] = nxos_upgrade

    def _build_payload_issu_options_1(self, device) -> None:
        """
        Build the issuUpgradeOptions1 portion of the payload.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}."
        self.log.debug(msg)

        # nxos_mode: The choices for nxos_mode are mutually-exclusive.
        # If one is set to True, the others must be False.
        # nonDisruptive corresponds to Allow Non-Disruptive GUI option
        self.payload["issuUpgradeOptions1"] = {}
        self.payload["issuUpgradeOptions1"]["nonDisruptive"] = False
        self.payload["issuUpgradeOptions1"]["forceNonDisruptive"] = False
        self.payload["issuUpgradeOptions1"]["disruptive"] = False

        nxos_mode = device.get("options").get("nxos").get("mode")
        if nxos_mode not in self.valid_nxos_mode:
            msg = f"{self.class_name}.{method_name}: "
            msg += "options.nxos.mode must be one of "
            msg += f"{sorted(self.valid_nxos_mode)}. "
            msg += f"Got {nxos_mode}."
            raise ValueError(msg)

        verify_nxos_mode_list = []
        if nxos_mode == "non_disruptive":
            verify_nxos_mode_list.append(True)
            self.payload["issuUpgradeOptions1"]["nonDisruptive"] = True
        if nxos_mode == "disruptive":
            verify_nxos_mode_list.append(True)
            self.payload["issuUpgradeOptions1"]["disruptive"] = True
        if nxos_mode == "force_non_disruptive":
            verify_nxos_mode_list.append(True)
            self.payload["issuUpgradeOptions1"]["forceNonDisruptive"] = True

    def _build_payload_issu_options_2(self, device) -> None:
        """
        Build the issuUpgradeOptions2 portion of the payload.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}."
        self.log.debug(msg)

        msg = f"ENTERED: {self.class_name}.{method_name}."
        self.log.debug(msg)

        bios_force = device.get("options").get("nxos").get("bios_force")
        bios_force = self.conversion.make_boolean(bios_force)
        if not isinstance(bios_force, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "options.nxos.bios_force must be a boolean. "
            msg += f"Got {bios_force}."
            raise TypeError(msg)

        self.payload["issuUpgradeOptions2"] = {}
        self.payload["issuUpgradeOptions2"]["biosForce"] = bios_force

    def _build_payload_epld(self, device) -> None:
        """
        Build the epldUpgrade and epldOptions portions of the payload.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}."
        self.log.debug(msg)

        epld_upgrade = device.get("upgrade").get("epld")
        epld_upgrade = self.conversion.make_boolean(epld_upgrade)
        if not isinstance(epld_upgrade, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "upgrade.epld must be a boolean. "
            msg += f"Got {epld_upgrade}."
            raise TypeError(msg)

        epld_module = device.get("options").get("epld").get("module")
        epld_golden = device.get("options").get("epld").get("golden")

        epld_golden = self.conversion.make_boolean(epld_golden)
        if not isinstance(epld_golden, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "options.epld.golden must be a boolean. "
            msg += f"Got {epld_golden}."
            raise TypeError(msg)

        if epld_golden is True and device.get("upgrade").get("nxos") is True:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Invalid configuration for "
            msg += f"{self.issu_detail.ip_address}. "
            msg += "If options.epld.golden is True "
            msg += "all other upgrade options, e.g. upgrade.nxos, "
            msg += "must be False."
            raise ValueError(msg)

        if epld_module != "ALL":
            try:
                epld_module = int(epld_module)
            except ValueError as error:
                msg = f"{self.class_name}.{method_name}: "
                msg += "options.epld.module must either be 'ALL' "
                msg += f"or an integer. Got {epld_module}."
                raise ValueError(msg) from error

        self.payload["epldUpgrade"] = epld_upgrade
        self.payload["epldOptions"] = {}
        self.payload["epldOptions"]["moduleNumber"] = epld_module
        self.payload["epldOptions"]["golden"] = epld_golden

    def _build_payload_reboot(self, device) -> None:
        """
        Build the reboot portion of the payload.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}."
        self.log.debug(msg)

        reboot = device.get("reboot")

        reboot = self.conversion.make_boolean(reboot)
        if not isinstance(reboot, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "reboot must be a boolean. "
            msg += f"Got {reboot}."
            raise TypeError(msg)
        self.payload["reboot"] = reboot

    def _build_payload_reboot_options(self, device) -> None:
        """
        Build the rebootOptions portion of the payload.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}."
        self.log.debug(msg)

        config_reload = device.get("options").get("reboot").get("config_reload")
        write_erase = device.get("options").get("reboot").get("write_erase")

        config_reload = self.conversion.make_boolean(config_reload)
        if not isinstance(config_reload, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "options.reboot.config_reload must be a boolean. "
            msg += f"Got {config_reload}."
            raise TypeError(msg)

        write_erase = self.conversion.make_boolean(write_erase)
        if not isinstance(write_erase, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "options.reboot.write_erase must be a boolean. "
            msg += f"Got {write_erase}."
            raise TypeError(msg)

        self.payload["rebootOptions"] = {}
        self.payload["rebootOptions"]["configReload"] = config_reload
        self.payload["rebootOptions"]["writeErase"] = write_erase

    def _build_payload_package(self, device) -> None:
        """
        Build the packageInstall and packageUnInstall portions of the payload.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}."
        self.log.debug(msg)

        package_install = device.get("options").get("package").get("install")
        package_uninstall = device.get("options").get("package").get("uninstall")

        package_install = self.conversion.make_boolean(package_install)
        if not isinstance(package_install, bool):
            # This code is never hit since ImageInstallOptions calls
            # fail_json on invalid options.package.install.
            # We'll leave this here in case we change ImageInstallOptions
            # in the future.
            msg = f"{self.class_name}.{method_name}: "
            msg += "options.package.install must be a boolean. "
            msg += f"Got {package_install}."
            raise TypeError(msg)

        package_uninstall = self.conversion.make_boolean(package_uninstall)
        if not isinstance(package_uninstall, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "options.package.uninstall must be a boolean. "
            msg += f"Got {package_uninstall}."
            raise TypeError(msg)

        # Yes, these keys are misspelled. The controller
        # wants them to be misspelled.  Need to keep an
        # eye out for future releases correcting the spelling.
        self.payload["pacakgeInstall"] = package_install
        self.payload["pacakgeUnInstall"] = package_uninstall

    def validate_commit_parameters(self):
        """
        Verify mandatory parameters are set before calling commit.
        """
        # pylint: disable=no-member
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}."
        self.log.debug(msg)

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling commit()."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set before calling commit()."
            raise ValueError(msg)

    def commit(self) -> None:
        """
        ### Summary
        Commit the image upgrade request to the controller and wait
        for the images to be upgraded.

        ### Raises
        -   ``ControllerResponseError`` if the controller returns a non-200
            response.
        -   ``ValueError`` if:
                -   ``RestSend()`` raises a ``TypeError`` or ``ValueError``.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}."
        self.log.debug(msg)

        self.validate_commit_parameters()

        # pylint: disable=no-member
        self.issu_detail.rest_send = self.rest_send
        self.install_options.rest_send = self.rest_send

        self.install_options.results = self.results
        # pylint: enable=no-member
        # We don't want issu_detail results to show up in the user's result output.
        self.issu_detail.results = Results()

        self._validate_devices()
        self.wait_for_controller()

        self.saved_response_current = {}
        self.saved_result_current = {}
        for device in self.devices:
            ipv4 = device.get("ip_address")
            if ipv4 not in self.saved_response_current:
                self.saved_response_current[ipv4] = {}
            if ipv4 not in self.saved_result_current:
                self.saved_result_current[ipv4] = {}

            msg = f"{self.class_name}.{method_name}: "
            msg += f"device: {json.dumps(device, indent=4, sort_keys=True)}."
            self.log.debug(msg)

            self._build_payload(device)

            msg = f"{self.class_name}.{method_name}: "
            msg += "Calling RestSend.commit(). "
            msg += f"verb: {self.ep_upgrade_image.verb}, "
            msg += f"path: {self.ep_upgrade_image.path}."
            self.log.debug(msg)

            # pylint: disable=no-member
            try:
                self.rest_send.path = self.ep_upgrade_image.path
                self.rest_send.verb = self.ep_upgrade_image.verb
                self.rest_send.payload = self.payload
                self.rest_send.commit()
            except (TypeError, ValueError) as error:
                self.results.diff_current = {}
                self.results.action = self.action
                self.results.response_current = copy.deepcopy(
                    self.rest_send.response_current
                )
                self.results.result_current = copy.deepcopy(
                    self.rest_send.result_current
                )
                self.results.register_task_result()
                msg = f"{self.class_name}.{method_name}: "
                msg += "Error while sending request. "
                msg += f"Error detail: {error}"
                raise ValueError(msg) from error

            self.saved_response_current[ipv4] = copy.deepcopy(
                self.rest_send.response_current
            )
            self.saved_result_current[ipv4] = copy.deepcopy(
                self.rest_send.result_current
            )

            if not self.rest_send.result_current["success"]:
                msg = f"{self.class_name}.{method_name}: "
                msg += f"failed: {self.rest_send.result_current}. "
                msg += f"Controller response: {self.rest_send.response_current}"
                self.results.register_task_result()
                raise ControllerResponseError(msg)

        self._wait_for_image_upgrade_to_complete()

        self.build_diff()
        # pylint: disable=no-member
        self.results.action = self.action
        self.results.diff_current = copy.deepcopy(self.diff)
        self.results.response_current = copy.deepcopy(self.saved_response_current)
        self.results.result_current = copy.deepcopy(self.saved_result_current)
        self.results.register_task_result()

    def wait_for_controller(self):
        """
        ### Summary
        Wait for any actions on the controller to complete.

        ### Raises
        -   ValueError: if:
                -   ``items`` is not a set.
                -   ``item_type`` is not a valid item type.
                -   The action times out.
        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}."
        self.log.debug(msg)

        try:
            self.wait_for_controller_done.items = set(copy.copy(self.ip_addresses))
            self.wait_for_controller_done.item_type = "ipv4_address"
            self.wait_for_controller_done.rest_send = (
                self.rest_send  # pylint: disable=no-member
            )
            self.wait_for_controller_done.commit()
        except (TypeError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Error {error}."
            raise ValueError(msg) from error

    def _wait_for_image_upgrade_to_complete(self):
        """
        ### Summary
        Wait for image upgrade to complete

        ### Raises
        -   ``ValueError`` if:
                -   The upgrade does not complete within ``check_timeout``
                    seconds.
                -   The upgrade fails for any device.

        """
        method_name = inspect.stack()[0][3]

        msg = f"ENTERED: {self.class_name}.{method_name}."
        self.log.debug(msg)

        self.ipv4_todo = set(copy.copy(self.ip_addresses))
        if self.rest_send.unit_test is False:  # pylint: disable=no-member
            # See unit test test_image_upgrade_upgrade_00240
            self.ipv4_done = set()
        timeout = self.check_timeout

        while self.ipv4_done != self.ipv4_todo and timeout > 0:
            if self.rest_send.unit_test is False:  # pylint: disable=no-member
                sleep(self.check_interval)
            timeout -= self.check_interval
            self.issu_detail.refresh()

            for ipv4 in self.ip_addresses:
                if ipv4 in self.ipv4_done:
                    continue
                self.issu_detail.filter = ipv4

                ip_address = self.issu_detail.ip_address
                device_name = self.issu_detail.device_name
                upgrade_percent = self.issu_detail.upgrade_percent
                upgrade_status = self.issu_detail.upgrade
                serial_number = self.issu_detail.serial_number

                if upgrade_status == "Failed":
                    msg = f"{self.class_name}.{method_name}: "
                    msg += f"Seconds remaining {timeout}: upgrade image "
                    msg += f"{upgrade_status} for "
                    msg += f"{device_name}, {serial_number}, {ip_address}, "
                    msg += f"upgrade_percent {upgrade_percent}. "
                    msg += "Check the controller to determine the cause. "
                    msg += "Operations > Image Management > Devices > View Details. "
                    msg += "And/or check the devices "
                    msg += "(e.g. show install all status)."
                    raise ValueError(msg)
                if upgrade_status == "Success":
                    self.ipv4_done.add(ipv4)

            msg = f"seconds remaining {timeout}"
            self.log.debug(msg)
            msg = f"ipv4_done: {sorted(self.ipv4_done)}"
            self.log.debug(msg)
            msg = f"ipv4_todo: {sorted(self.ipv4_todo)}"
            self.log.debug(msg)

        if self.ipv4_done != self.ipv4_todo:
            msg = f"{self.class_name}.{method_name}: "
            msg += "The following device(s) did not complete upgrade: "
            msg += f"{sorted(self.ipv4_todo.difference(self.ipv4_done))}. "
            msg += "Check the controller to determine the cause. "
            msg += "Operations > Image Management > Devices > View Details. "
            msg += "And/or check the device(s) "
            msg += "(e.g. show install all status)."
            raise ValueError(msg)

    # setter properties
    @property
    def bios_force(self):
        """
        Set the bios_force flag to True or False.

        Default: False
        """
        return self._bios_force

    @bios_force.setter
    def bios_force(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.bios_force must be a boolean."
            raise TypeError(msg)
        self._bios_force = value

    @property
    def config_reload(self):
        """
        Set the config_reload flag to True or False.

        Default: False
        """
        return self._config_reload

    @config_reload.setter
    def config_reload(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.config_reload must be a boolean."
            raise TypeError(msg)
        self._config_reload = value

    @property
    def devices(self) -> list:
        """
        Set the devices to upgrade.

        list() of dict() with the following structure:
        [
            {
                "ip_address": "192.168.1.1"
            }
        ]
        Must be set before calling instance.commit()
        """
        return self._devices

    @devices.setter
    def devices(self, value: list):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, list):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.devices must be a python list of dict. "
            msg += f"Got {value}."
            raise TypeError(msg)
        for device in value:
            if not isinstance(device, dict):
                msg = f"{self.class_name}.{method_name}: "
                msg += "instance.devices must be a python list of dict. "
                msg += f"Got {value}."
                raise TypeError(msg)
            if "ip_address" not in device:
                msg = f"{self.class_name}.{method_name}: "
                msg += "instance.devices must be a python list of dict, "
                msg += "where each dict contains the following keys: "
                msg += "ip_address. "
                msg += f"Got {value}."
                raise ValueError(msg)
        self._devices = value

    @property
    def disruptive(self):
        """
        Set the disruptive flag to True or False.

        Default: False
        """
        return self._disruptive

    @disruptive.setter
    def disruptive(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.disruptive must be a boolean."
            raise TypeError(msg)
        self._disruptive = value

    @property
    def epld_golden(self):
        """
        Set the epld_golden flag to True or False.

        Default: False
        """
        return self._epld_golden

    @epld_golden.setter
    def epld_golden(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.epld_golden must be a boolean."
            raise TypeError(msg)
        self._epld_golden = value

    @property
    def epld_upgrade(self):
        """
        Set the epld_upgrade flag to True or False.

        Default: False
        """
        return self._epld_upgrade

    @epld_upgrade.setter
    def epld_upgrade(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.epld_upgrade must be a boolean."
            raise TypeError(msg)
        self._epld_upgrade = value

    @property
    def epld_module(self):
        """
        Set the epld_module to upgrade.

        Ignored if epld_upgrade is set to False
        Valid values: integer or "ALL"
        Default: "ALL"
        """
        return self._epld_module

    @epld_module.setter
    def epld_module(self, value):
        method_name = inspect.stack()[0][3]
        try:
            value = value.upper()
        except AttributeError:
            pass
        try:
            value = int(value)
        except ValueError:
            pass
        if not isinstance(value, int) and value != "ALL":
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.epld_module must be an integer or 'ALL'"
            raise TypeError(msg)
        self._epld_module = value

    @property
    def force_non_disruptive(self):
        """
        Set the force_non_disruptive flag to True or False.

        Default: False
        """
        return self._force_non_disruptive

    @force_non_disruptive.setter
    def force_non_disruptive(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.force_non_disruptive must be a boolean."
            raise TypeError(msg)
        self._force_non_disruptive = value

    @property
    def non_disruptive(self):
        """
        Set the non_disruptive flag to True or False.

        Default: True
        """
        return self._non_disruptive

    @non_disruptive.setter
    def non_disruptive(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.non_disruptive must be a boolean."
            raise TypeError(msg)
        self._non_disruptive = value

    @property
    def package_install(self):
        """
        Set the package_install flag to True or False.

        Default: False
        """
        return self._package_install

    @package_install.setter
    def package_install(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.package_install must be a boolean."
            raise TypeError(msg)
        self._package_install = value

    @property
    def package_uninstall(self):
        """
        Set the package_uninstall flag to True or False.

        Default: False
        """
        return self._package_uninstall

    @package_uninstall.setter
    def package_uninstall(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.package_uninstall must be a boolean."
            raise TypeError(msg)
        self._package_uninstall = value

    @property
    def reboot(self):
        """
        Set the reboot flag to True or False.

        Default: False
        """
        return self._reboot

    @reboot.setter
    def reboot(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.reboot must be a boolean."
            raise TypeError(msg)
        self._reboot = value

    @property
    def write_erase(self):
        """
        Set the write_erase flag to True or False.

        Default: False
        """
        return self._write_erase

    @write_erase.setter
    def write_erase(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.write_erase must be a boolean."
            raise TypeError(msg)
        self._write_erase = value

    @property
    def check_interval(self):
        """
        Return the image upgrade check interval in seconds
        """
        return self._check_interval

    @check_interval.setter
    def check_interval(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"instance.{method_name} must be an integer."
        # isinstance(False, int) returns True, so we need first
        # to test for this and fail_json specifically for bool values.
        if isinstance(value, bool):
            raise TypeError(msg)
        if not isinstance(value, int):
            raise TypeError(msg)
        self._check_interval = value

    @property
    def check_timeout(self):
        """
        Return the image upgrade check timeout in seconds
        """
        return self._check_timeout

    @check_timeout.setter
    def check_timeout(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += f"instance.{method_name} must be an integer."
        # isinstance(False, int) returns True, so we need first
        # to test for this and fail_json specifically for bool values.
        if isinstance(value, bool):
            raise TypeError(msg)
        if not isinstance(value, int):
            raise TypeError(msg)
        self._check_timeout = value
