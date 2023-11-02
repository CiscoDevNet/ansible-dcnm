import copy
import json
from time import sleep

from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
)
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.switch_issu_details import SwitchIssuDetailsByIpAddress

class ImageUpgrade(ImageUpgradeCommon):
    """
    Endpoint:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupgrade/upgrade-image
    Verb: POST

    Usage (where module is an instance of AnsibleModule):

    upgrade = ImageUpgrade(module)
    upgrade.devices = devices
    upgrade.commit()
    data = upgrade.data

    Where devices is a list of dict.  Example structure:

        [
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
            etc...
        ]

    Request body:
        Yes, the keys below are misspelled in the request body:
            pacakgeInstall
            pacakgeUnInstall

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
    Response bodies:
        Responses are text, not JSON, and are returned immediately.
        They do not contain useful information. We need to poll the controller
        to determine when the upgrade is complete. Basically, we ignore
        these responses in favor of the poll responses.
        - If an action is in progress, text is returned:
            "Action in progress for some of selected device(s). Please try again after completing current action."
        -   If an action is not in progress, text is returned:
            "3"
    """

    def __init__(self, module):
        super().__init__(module)
        self.class_name = self.__class__.__name__
        self.endpoints = ApiEndpoints()
        # Maximum number of modules/linecards in a switch
        self.max_module_number = 9

        self._init_defaults()
        self._init_properties()
        self.issu_detail = SwitchIssuDetailsByIpAddress(self.module)

    def _init_defaults(self):
        self.defaults = {}
        self.defaults["reboot"] = False
        self.defaults["stage"] = True
        self.defaults["validate"] = True
        self.defaults["upgrade"] = {}
        self.defaults["upgrade"]["nxos"] = True
        self.defaults["upgrade"]["epld"] = False
        self.defaults["options"] = {}
        self.defaults["options"]["nxos"] = {}
        self.defaults["options"]["nxos"]["mode"] = "disruptive"
        self.defaults["options"]["nxos"]["bios_force"] = False
        self.defaults["options"]["epld"] = {}
        self.defaults["options"]["epld"]["module"] = "ALL"
        self.defaults["options"]["epld"]["golden"] = False
        self.defaults["options"]["reboot"] = {}
        self.defaults["options"]["reboot"]["config_reload"] = False
        self.defaults["options"]["reboot"]["write_erase"] = False
        self.defaults["options"]["package"] = {}
        self.defaults["options"]["package"]["install"] = False
        self.defaults["options"]["package"]["uninstall"] = False

    def _init_properties(self):
        # self.ip_addresses is used in:
        #   self._wait_for_current_actions_to_complete()
        #   self._wait_for_image_upgrade_to_complete()
        self.ip_addresses = set()
        # TODO:1 Review these properties since we are no longer
        # calling this class per-switch given the payload structure
        # is not amenable to that.
        self.properties = {}
        self.properties["bios_force"] = False
        self.properties["check_interval"] = 10  # seconds
        self.properties["check_timeout"] = 1800  # seconds
        self.properties["config_reload"] = False
        self.properties["devices"] = None
        self.properties["disruptive"] = True
        self.properties["epld_golden"] = False
        self.properties["epld_module"] = "ALL"
        self.properties["epld_upgrade"] = False
        self.properties["force_non_disruptive"] = False
        self.properties["response_data"] = None
        self.properties["result"] = None
        self.properties["response"] = None
        self.properties["non_disruptive"] = False
        self.properties["package_install"] = False
        self.properties["package_uninstall"] = False
        self.properties["reboot"] = False
        self.properties["write_erase"] = False

        self.valid_epld_module = set()
        self.valid_epld_module.add("ALL")
        for module in range(1, self.max_module_number + 1):
            self.valid_epld_module.add(str(module))

        self.valid_nxos_mode = set()
        self.valid_nxos_mode.add("disruptive")
        self.valid_nxos_mode.add("non_disruptive")
        self.valid_nxos_mode.add("force_non_disruptive")


    # def prune_devices(self):
    #     """
    #     If the image is already upgraded on a device, remove that device
    #     from self.devices.  self.devices dict has already been validated,
    #     so no further error checking is needed here.

    #     TODO:1 This prunes devices only based on the image upgrade state.
    #     TODO:1 It does not check other image states and EPLD states.
    #     """
    #     # issu = SwitchIssuDetailsBySerialNumber(self.module)
    #     pruned_devices = set()
    #     instance = SwitchIssuDetailsByIpAddress(self.module)
    #     instance.refresh()
    #     for device in self.devices:
    #         msg = f"REMOVE: {self.class_name}.prune_devices() device: {device}"
    #         self.log_msg(msg)
    #         instance.ip_address = device.get("ip_address")
    #         instance.refresh()
    #         if instance.upgrade == "Success":
    #             msg = f"REMOVE: {self.class_name}.prune_devices: "
    #             msg = "image already upgraded for "
    #             msg += f"{instance.device_name}, "
    #             msg += f"{instance.serial_number}, "
    #             msg += f"{instance.ip_address}"
    #             self.log_msg(msg)
    #             pruned_devices.add(instance.ip_address)
    #     self.devices = [
    #         device
    #         for device in self.devices
    #         if device.get("ip_address") not in pruned_devices
    #     ]

    def validate_devices(self):
        """
        Fail if the upgrade state for any device is Failed.
        """
        for device in self.devices:
            self.issu_detail.ip_address = device.get("ip_address")
            self.issu_detail.refresh()
            if self.issu_detail.upgrade == "Failed":
                msg = f"{self.class_name}.validate_devices: Image upgrade is "
                msg += "failing for the following switch: "
                msg += f"{self.issu_detail.device_name}, "
                msg += f"{self.issu_detail.ip_address}, "
                msg += f"{self.issu_detail.serial_number}. "
                msg += "Please check the switch "
                msg += "to determine the cause and try again."
                self.module.fail_json(msg)
            # used in self._wait_for_current_actions_to_complete()
            self.ip_addresses.add(self.issu_detail.ip_address)

    def _merge_defaults_to_switch_config(self, config):
        if config.get("stage") is None:
            config["stage"] = self.defaults["stage"]
        if config.get("reboot") is None:
            config["reboot"] = self.defaults["reboot"]
        if config.get("validate") is None:
            config["validate"] = self.defaults["validate"]
        if config.get("upgrade") is None:
            config["upgrade"] = self.defaults["upgrade"]
        if config.get("upgrade").get("nxos") is None:
            config["upgrade"]["nxos"] = self.defaults["upgrade"]["nxos"]
        if config.get("upgrade").get("epld") is None:
            config["upgrade"]["epld"] = self.defaults["upgrade"]["epld"]
        if config.get("options") is None:
            config["options"] = self.defaults["options"]
        if config["options"].get("nxos") is None:
            config["options"]["nxos"] = self.defaults["options"]["nxos"]
        if config["options"]["nxos"].get("mode") is None:
            config["options"]["nxos"]["mode"] = self.defaults["options"]["nxos"]["mode"]
        if config["options"]["nxos"].get("bios_force") is None:
            config["options"]["nxos"]["bios_force"] = self.defaults["options"]["nxos"]["bios_force"]
        if config["options"].get("epld") is None:
            config["options"]["epld"] = self.defaults["options"]["epld"]
        if config["options"]["epld"].get("module") is None:
            config["options"]["epld"]["module"] = self.defaults["options"]["epld"]["module"]
        if config["options"]["epld"].get("golden") is None:
            config["options"]["epld"]["golden"] = self.defaults["options"]["epld"]["golden"]
        if config["options"].get("reboot") is None:
            config["options"]["reboot"] = self.defaults["options"]["reboot"]
        if config["options"]["reboot"].get("config_reload") is None:
            config["options"]["reboot"]["config_reload"] = self.defaults["options"]["reboot"]["config_reload"]
        if config["options"]["reboot"].get("write_erase") is None:
            config["options"]["reboot"]["write_erase"] = self.defaults["options"]["reboot"]["write_erase"]
        if config["options"].get("package") is None:
            config["options"]["package"] = self.defaults["options"]["package"]
        if config["options"]["package"].get("install") is None:
            config["options"]["package"]["install"] = self.defaults["options"]["package"]["install"]
        if config["options"]["package"].get("uninstall") is None:
            config["options"]["package"]["uninstall"] = self.defaults["options"]["package"]["uninstall"]
        return config

    def build_payload(self, device):
        """
        Build the request payload to upgrade the switches.
        """
        msg = f"REMOVE: {self.class_name}.build_payload()  PRE_DEFAULTS: "
        msg += f"device: {device}"
        self.log_msg(msg)
        device = self._merge_defaults_to_switch_config(device)
        msg = f"REMOVE: {self.class_name}.build_payload() POST_DEFAULTS: "
        msg += f"device: {device}"
        self.log_msg(msg)


        # devices_to_upgrade must currently be a single device
        devices_to_upgrade = []
        self.issu_detail.ip_address = device.get("ip_address")
        self.issu_detail.refresh()
        payload_device = {}
        payload_device["serialNumber"] = self.issu_detail.serial_number
        payload_device["policyName"] = device.get("policy")
        devices_to_upgrade.append(payload_device)

        self.payload = {}
        self.payload["devices"] = devices_to_upgrade
        self.payload["issuUpgrade"] = device.get("upgrade").get("nxos")

        # nxos_mode: The choices for nxos_mode are mutually-exclusive.
        # If one is set to True, the others must be False.
        # nonDisruptive corresponds to Allow Non-Disruptive GUI option
        self.payload["issuUpgradeOptions1"] = {}
        self.payload["issuUpgradeOptions1"]["nonDisruptive"] = False
        self.payload["issuUpgradeOptions1"]["forceNonDisruptive"] = False
        self.payload["issuUpgradeOptions1"]["disruptive"] = False

        nxos_mode = device.get("options").get("nxos").get("mode")
        if nxos_mode not in self.valid_nxos_mode:
            msg = f"{self.class_name}.build_payload() options.nxos.mode must "
            msg += f"be one of {self.valid_nxos_mode}. Got {nxos_mode}."
            self.module.fail_json(msg)
        if nxos_mode == "non_disruptive":
            self.payload["issuUpgradeOptions1"]["nonDisruptive"] = True
        if nxos_mode == "disruptive":
            self.payload["issuUpgradeOptions1"]["disruptive"] = True
        if nxos_mode == "force_non_disruptive":
            self.payload["issuUpgradeOptions1"]["forceNonDisruptive"] = True

        # biosForce corresponds to BIOS Force GUI option
        bios_force = device.get("options").get("nxos").get("bios_force")
        if not isinstance(bios_force, bool):
            msg = f"{self.class_name}.build_payload() options.nxos.bios_force "
            msg += f"must be a boolean. Got {bios_force}."
            self.module.fail_json(msg)
        self.payload["issuUpgradeOptions2"] = {}
        self.payload["issuUpgradeOptions2"]["biosForce"] = bios_force

        # EPLD
        epld_module = device.get("options").get("epld").get("module")
        epld_golden = device.get("options").get("epld").get("golden")
        if epld_module not in self.valid_epld_module:
            msg = f"{self.class_name}.build_payload() options.epld.module must "
            msg += f"be one of {self.valid_epld_module}. Got {epld_module}."
            self.module.fail_json(msg)
        if not isinstance(epld_golden, bool):
            msg = f"{self.class_name}.build_payload() options.epld.golden "
            msg += f"must be a boolean. Got {epld_golden}."
            self.module.fail_json(msg)
        self.payload["epldUpgrade"] = device.get("upgrade").get("epld")
        self.payload["epldOptions"] = {}
        self.payload["epldOptions"]["moduleNumber"] = epld_module
        self.payload["epldOptions"]["golden"] = epld_golden

        # Reboot
        reboot = device.get("reboot")
        if not isinstance(reboot, bool):
            msg = f"{self.class_name}.build_payload() reboot must "
            msg += f"be a boolean. Got {reboot}."
            self.module.fail_json(msg)
        self.payload["reboot"] = reboot

        # Reboot options
        config_reload = device.get("options").get("reboot").get("config_reload")
        write_erase = device.get("options").get("reboot").get("write_erase")
        if not isinstance(config_reload, bool):
            msg = f"{self.class_name}.build_payload() options.reboot.config_reload "
            msg += f"must be a boolean. Got {config_reload}."
            self.module.fail_json(msg)
        if not isinstance(write_erase, bool):
            msg = f"{self.class_name}.build_payload() options.reboot.write_erase "
            msg += f"must be a boolean. Got {write_erase}."
            self.module.fail_json(msg)
        self.payload["rebootOptions"] = {}
        self.payload["rebootOptions"]["configReload"] = config_reload
        self.payload["rebootOptions"]["writeErase"] = write_erase

        # Packages
        package_install = device.get("options").get("package").get("install")
        package_uninstall = device.get("options").get("package").get("uninstall")
        if not isinstance(package_install, bool):
            msg = f"{self.class_name}.build_payload() options.package.install "
            msg += f"must be a boolean. Got {package_install}."
            self.module.fail_json(msg)
        if not isinstance(package_uninstall, bool):
            msg = f"{self.class_name}.build_payload() options.package.uninstall "
            msg += f"must be a boolean. Got {package_uninstall}."
            self.module.fail_json(msg)
        self.payload["pacakgeInstall"] = package_install
        self.payload["pacakgeUnInstall"] = package_uninstall

    def commit(self):
        """
        Commit the image upgrade request to the controller and wait
        for the images to be upgraded.
        """
        if self.devices is None:
            msg = f"{self.class_name}.commit() call instance.devices "
            msg += "before calling commit()."
            self.module.fail_json(msg)
        if len(self.devices) == 0:
            msg = f"REMOVE: {self.class_name}.commit() no devices to upgrade."
            self.log_msg(msg)
            return
        #self.prune_devices()
        self.validate_devices()
        self._wait_for_current_actions_to_complete()
        path = self.endpoints.image_upgrade.get("path")
        verb = self.endpoints.image_upgrade.get("verb")
        for device in self.devices:
            self.build_payload(device)
            self.log_msg(f"REMOVE: {self.class_name}.commit() upgrade payload: {self.payload}")
            self.properties["response"] = dcnm_send(
                self.module, verb, path, data=json.dumps(self.payload)
            )
            self.properties["result"] = self._handle_response(self.response, verb)
            self.log_msg(
                f"REMOVE: {self.class_name}.commit() response: {self.response}"
            )
            self.log_msg(f"REMOVE: {self.class_name}.commit() result: {self.result}")
            if not self.result["success"]:
                msg = f"{self.class_name}.commit() failed: {self.result}. "
                msg += f"Controller response: {self.response}"
                self.module.fail_json(msg)
            self.properties["response_data"] = self.response.get("DATA")
        self._wait_for_image_upgrade_to_complete()

    def _wait_for_current_actions_to_complete(self):
        """
        The controller will not upgrade an image if there are any actions
        in progress.  Wait for all actions to complete before upgrading image.
        Actions include image staging, image upgrade, and image validation.
        """
        ipv4_todo = copy.copy(self.ip_addresses)
        timeout = self.check_timeout
        while len(ipv4_todo) > 0 and timeout > 0:
            sleep(self.check_interval)
            timeout -= self.check_interval
            for ipv4 in self.ip_addresses:
                if ipv4 not in ipv4_todo:
                    continue
                self.issu_detail.ip_address = ipv4
                self.issu_detail.refresh()
                if self.issu_detail.actions_in_progress is False:
                    msg = f"REMOVE: {self.class_name}."
                    msg += "_wait_for_current_actions_to_complete: "
                    msg += f"{ipv4} no actions in progress. "
                    msg += f"OK to proceed. {timeout} seconds remaining."
                    self.log_msg(msg)
                    ipv4_todo.remove(ipv4)
                    continue
                msg = f"REMOVE: {self.class_name}."
                msg += "_wait_for_current_actions_to_complete: "
                msg += f"{ipv4} actions in progress. "
                msg += f"Waiting. {timeout} seconds remaining."
                self.log_msg(msg)

    def _wait_for_image_upgrade_to_complete(self):
        """
        Wait for image upgrade to complete
        """
        ipv4_done = set()
        timeout = self.check_timeout
        ipv4_todo = set(copy.copy(self.ip_addresses))
        while ipv4_done != ipv4_todo and timeout > 0:
            sleep(self.check_interval)
            timeout -= self.check_interval
            msg = f"REMOVE: {self.class_name}."
            msg += "_wait_for_image_upgrade_to_complete: "
            msg += f"seconds remaining {timeout}, "
            msg += f"ipv4_todo: {sorted(list(ipv4_todo))}"
            self.log_msg(msg)
            msg = f"REMOVE: {self.class_name}."
            msg += "_wait_for_image_upgrade_to_complete: "
            msg += f"seconds remaining {timeout}, "
            msg += f"ipv4_done: {sorted(list(ipv4_done))}"
            self.log_msg(msg)
            for ipv4 in self.ip_addresses:
                if ipv4 in ipv4_done:
                    continue
                self.issu_detail.ip_address = ipv4
                self.issu_detail.refresh()
                ip_address = self.issu_detail.ip_address
                device_name = self.issu_detail.device_name
                upgrade_percent = self.issu_detail.upgrade_percent
                upgrade_status = self.issu_detail.upgrade
                serial_number = self.issu_detail.serial_number

                if upgrade_status == "Failed":
                    msg = f"{self.class_name}."
                    msg += "_wait_for_image_upgrade_to_complete: "
                    msg += f"Seconds remaining {timeout}: upgrade image "
                    msg += f"{upgrade_status} for "
                    msg += f"{device_name}, {serial_number}, {ip_address}"
                    self.module.fail_json(msg)

                if upgrade_status == "Success":
                    ipv4_done.add(ipv4)
                    status = "succeeded"
                if upgrade_status == None:
                    status = "not started"
                if upgrade_status == "In-Progress":
                    status = "in progress"

                msg = f"REMOVE: {self.class_name}."
                msg += "_wait_for_image_upgrade_to_complete: "
                msg += f"Seconds remaining {timeout}, "
                msg += f"Percent complete {upgrade_percent}, "
                msg += f"Status {status}, "
                msg += f"{device_name}, {serial_number}, {ip_address}"
                self.log_msg(msg)

        if ipv4_done != ipv4_todo:
            msg = f"{self.class_name}._wait_for_image_upgrade_to_complete(): "
            msg += "The following device(s) did not complete upgrade: "
            msg += f"{ipv4_todo.difference(ipv4_done)}. "
            msg += "Try increasing issu timeout in the playbook, or check "
            msg += "the device(s) to determine the cause "
            msg += "(e.g. show install all status)."
            self.module.fail_json(msg)

    # setter properties
    @property
    def bios_force(self):
        """
        Set the bios_force flag to True or False.

        Default: False
        """
        return self.properties.get("bios_force")

    @bios_force.setter
    def bios_force(self, value):
        name = "bios_force"
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be a boolean."
            self.module.fail_json(msg)
        self.properties[name] = value

    @property
    def config_reload(self):
        """
        Set the config_reload flag to True or False.

        Default: False
        """
        return self.properties.get("config_reload")

    @config_reload.setter
    def config_reload(self, value):
        name = "config_reload"
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be a boolean."
            self.module.fail_json(msg)
        self.properties[name] = value

    @property
    def devices(self):
        """
        Set the devices to upgrade.

        list() of dict() with the following structure:
        {
            "serial_number": "FDO211218HH",
            "policy_name": "NR1F"
        }

        Must be set before calling instance.commit()
        """
        return self.properties.get("devices")

    @devices.setter
    def devices(self, value):
        name = "devices"
        if not isinstance(value, list):
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be a python list of dict."
            self.module.fail_json(msg)
        self.properties[name] = value

    @property
    def disruptive(self):
        """
        Set the disruptive flag to True or False.

        Default: False
        """
        return self.properties.get("disruptive")

    @disruptive.setter
    def disruptive(self, value):
        name = "disruptive"
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be a boolean."
            self.module.fail_json(msg)
        self.properties[name] = value

    @property
    def epld_golden(self):
        """
        Set the epld_golden flag to True or False.

        Default: False
        """
        return self.properties.get("epld_golden")

    @epld_golden.setter
    def epld_golden(self, value):
        name = "epld_golden"
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be a boolean."
            self.module.fail_json(msg)
        self.properties[name] = value

    @property
    def epld_upgrade(self):
        """
        Set the epld_upgrade flag to True or False.

        Default: False
        """
        return self.properties.get("epld_upgrade")

    @epld_upgrade.setter
    def epld_upgrade(self, value):
        name = "epld_upgrade"
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be a boolean."
            self.module.fail_json(msg)
        self.properties[name] = value

    @property
    def epld_module(self):
        """
        Set the epld_module to upgrade.

        Ignored if epld_upgrade is set to False
        Valid values: integer or "ALL"
        Default: "ALL"
        """
        return self.properties.get("epld_module")

    @epld_module.setter
    def epld_module(self, value):
        name = "epld_module"
        try:
            value = value.upper()
        except AttributeError:
            pass
        if not isinstance(value, int) and value != "ALL":
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be an integer or 'ALL'"
            self.module.fail_json(msg)
        self.properties[name] = value

    @property
    def force_non_disruptive(self):
        """
        Set the force_non_disruptive flag to True or False.

        Default: False
        """
        return self.properties.get("force_non_disruptive")

    @force_non_disruptive.setter
    def force_non_disruptive(self, value):
        name = "force_non_disruptive"
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be a boolean."
            self.module.fail_json(msg)
        self.properties[name] = value

    @property
    def non_disruptive(self):
        """
        Set the non_disruptive flag to True or False.

        Default: True
        """
        return self.properties.get("non_disruptive")

    @non_disruptive.setter
    def non_disruptive(self, value):
        name = "non_disruptive"
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be a boolean."
            self.module.fail_json(msg)
        self.properties[name] = value

    @property
    def package_install(self):
        """
        Set the package_install flag to True or False.

        Default: False
        """
        return self.properties.get("package_install")

    @package_install.setter
    def package_install(self, value):
        name = "package_install"
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be a boolean."
            self.module.fail_json(msg)
        self.properties[name] = value

    @property
    def package_uninstall(self):
        """
        Set the package_uninstall flag to True or False.

        Default: False
        """
        return self.properties.get("package_uninstall")

    @package_uninstall.setter
    def package_uninstall(self, value):
        name = "package_uninstall"
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be a boolean."
            self.module.fail_json(msg)
        self.properties[name] = value

    @property
    def reboot(self):
        """
        Set the reboot flag to True or False.

        Default: False
        """
        return self.properties.get("reboot")

    @reboot.setter
    def reboot(self, value):
        name = "reboot"
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be a boolean."
            self.module.fail_json(msg)
        self.properties[name] = value

    @property
    def write_erase(self):
        """
        Set the write_erase flag to True or False.

        Default: False
        """
        return self.properties.get("write_erase")

    @write_erase.setter
    def write_erase(self, value):
        name = "write_erase"
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{name}.setter: "
            msg += f"instance.{name} must be a boolean."
            self.module.fail_json(msg)
        self.properties[name] = value


    # getter properties
    @property
    def check_interval(self):
        """
        Return the image upgrade check interval in seconds
        """
        return self.properties.get("check_interval")

    @property
    def check_timeout(self):
        """
        Return the image upgrade check timeout in seconds
        """
        return self.properties.get("check_timeout")

    @property
    def response_data(self):
        """
        Return the data retrieved from the controller for the
        image upgrade request.

        instance.devices must be set first.
        instance.commit() must be called first.
        """
        return self.properties.get("response_data")

    @property
    def result(self):
        """
        Return the POST result.
        instance.devices must be set first.
        instance.commit() must be called first.
        """
        return self.properties.get("result")

    @property
    def response(self):
        """
        Return the POST response from the controller
        instance.devices must be set first.
        instance.commit() must be called first.
        """
        return self.properties.get("response")

    @property
    def serial_numbers(self):
        """
        Return a list of serial numbers from self.devices
        """
        return [device.get("serial_number") for device in self.devices]
