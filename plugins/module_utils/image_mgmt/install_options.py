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
import time
from typing import Any, Dict

from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.api_endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.image_mgmt.image_upgrade_common import \
    ImageUpgradeCommon
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import \
    dcnm_send


class ImageInstallOptions(ImageUpgradeCommon):
    """
    Retrieve install-options details for ONE switch from the controller and
    provide property accessors for the policy attributes.

    Caveats:
        -   This retrieves for a SINGLE switch only.
        -   Set serial_number and policy_name and call refresh() for
            each switch separately.

    Usage (where module is an instance of AnsibleModule):

    instance = ImageInstallOptions(module)
    # Mandatory
    instance.policy_name = "NR3F"
    instance.serial_number = "FDO211218GC"
    # Optional
    instance.epld = True
    instance.package_install = True
    instance.issu = True
    # Retrieve install-options details from the controller
    instance.refresh()
    if instance.device_name is None:
        msg = "Cannot retrieve policy/serial_number combination from "
        msg += "the controller"
        print(msg)
        exit(1)
    status = instance.status
    platform = instance.platform
    etc...

    install-options are retrieved by calling instance.refresh().

    Endpoint:
    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupgrade/install-options
    Request body:
    {
        "devices": [
            {
                "serialNumber": "FDO211218HH",
                "policyName": "NR1F"
            },
            {
                "serialNumber": "FDO211218GC",
                "policyName": "NR3F"
            }
        ],
        "issu": true,
        "epld": false,
        "packageInstall": false
    }
    Response body:
    NOTES:
    1.  epldModules will be null if epld is false in the request body.
        This class converts this to None (python NoneType) in this case.

    {
        "compatibilityStatusList": [
            {
                "deviceName": "cvd-1312-leaf",
                "ipAddress": "172.22.150.103",
                "policyName": "KR5M",
                "platform": "N9K/N3K",
                "version": "10.2.5",
                "osType": "64bit",
                "status": "Skipped",
                "installOption": "NA",
                "compDisp": "Compatibility status skipped.",
                "versionCheck": "Compatibility status skipped.",
                "preIssuLink": "Not Applicable",
                "repStatus": "skipped",
                "timestamp": "NA"
            }
        ],
        "epldModules": {
            "moduleList": [
                {
                    "deviceName": "cvd-1312-leaf",
                    "ipAddress": "172.22.150.103",
                    "policyName": "KR5M",
                    "module": 1,
                    "name": null,
                    "modelName": "N9K-C93180YC-EX",
                    "moduleType": "IO FPGA",
                    "oldVersion": "0x15",
                    "newVersion": "0x15"
                },
                {
                    "deviceName": "cvd-1312-leaf",
                    "ipAddress": "172.22.150.103",
                    "policyName": "KR5M",
                    "module": 1,
                    "name": null,
                    "modelName": "N9K-C93180YC-EX",
                    "moduleType": "MI FPGA",
                    "oldVersion": "0x4",
                    "newVersion": "0x04"
                }
            ],
            "bException": false,
            "exceptionReason": null
        },
        "installPacakges": null,
        "errMessage": ""
    }
    """

    def __init__(self, module) -> None:
        super().__init__(module)
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ImageInstallOptions()")

        self.endpoints = ApiEndpoints()

        self.path = self.endpoints.install_options.get("path")
        self.verb = self.endpoints.install_options.get("verb")

        self.payload: Dict[str, Any] = {}

        self.compatibility_status = {}

        self._init_properties()

    def _init_properties(self):
        # self.properties is already initialized in the parent class
        self.properties["epld"] = False
        self.properties["epld_modules"] = None
        self.properties["issu"] = True
        self.properties["package_install"] = False
        self.properties["policy_name"] = None
        self.properties["response_data"] = None
        self.properties["serial_number"] = None
        self.properties["timeout"] = 300
        self.properties["unit_test"] = False

    def _validate_refresh_parameters(self) -> None:
        """
        Ensure parameters are set correctly for a refresh() call.

        fail_json if not.
        """
        method_name = inspect.stack()[0][3]
        if self.policy_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.policy_name must be set before "
            msg += "calling refresh()"
            self.module.fail_json(msg, **self.failed_result)

        if self.serial_number is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "instance.serial_number must be set before "
            msg += "calling refresh()"
            self.module.fail_json(msg, **self.failed_result)

    def refresh(self) -> None:
        """
        Refresh self.response_data with current install-options from the controller
        """
        method_name = inspect.stack()[0][3]

        self._validate_refresh_parameters()

        msg = f"self.epld {self.epld}, "
        msg += f"self.issu {self.issu}, "
        msg += f"self.package_install {self.package_install}"
        self.log.debug(msg)
        # At least one of epld, issu, or package_install must be True
        # before calling refresh() or the controller will return an error.
        # Mock the response such that the caller knows nothing needs to be
        # done.
        if self.epld is False and self.issu is False and self.package_install is False:
            msg = "At least one of epld, issu, or package_install "
            msg += "must be True before calling refresh(). Skipping."
            self.log.debug(msg)
            self.compatibility_status = {}
            self.properties["response_data"] = {
                "compatibilityStatusList": [],
                "epldModules": None,
                "installPacakges": None,
                "errMessage": "",
            }
            return

        self._build_payload()

        timeout = self.timeout
        sleep_time = 5
        self.result_current["success"] = False

        while timeout > 0 and self.result_current.get("success") is False:
            msg = f"Calling dcnm_send: verb {self.verb} path {self.path} payload: "
            msg += f"{json.dumps(self.payload, indent=4, sort_keys=True)}"
            self.log.debug(msg)

            response = dcnm_send(
                self.module, self.verb, self.path, data=json.dumps(self.payload)
            )

            self.properties["response_data"] = response.get("DATA", {})
            self.result_current = self._handle_response(response, self.verb)
            self.response_current = copy.deepcopy(response)

            if self.result_current.get("success") is False and self.unit_test is False:
                time.sleep(sleep_time)
            timeout -= sleep_time

        if self.result_current["success"] is False:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Bad result when retrieving install-options from "
            msg += f"the controller. Controller response: {self.response_current}. "
            if self.response_data.get("error", None) is None:
                self.module.fail_json(msg, **self.failed_result)
            if "does not have package to continue" in self.response_data.get(
                "error", ""
            ):
                msg += f"Possible cause: Image policy {self.policy_name} does not have "
                msg += "a package defined, and package_install is set to "
                msg += f"True in the playbook for device {self.serial_number}."
            self.module.fail_json(msg, **self.failed_result)

        self.response = copy.deepcopy(self.response_current)
        if self.response_data.get("compatibilityStatusList") is None:
            self.compatibility_status = {}
        else:
            self.compatibility_status = self.response_data.get(
                "compatibilityStatusList", [{}]
            )[0]

    def _build_payload(self) -> None:
        """
        {
            "devices": [
                {
                    "serialNumber": "FDO211218HH",
                    "policyName": "NR1F"
                }
            ],
            "issu": true,
            "epld": false,
            "packageInstall": false
        }
        """
        self.payload: Dict[str, Any] = {}
        self.payload["devices"] = []
        devices = {}
        devices["serialNumber"] = self.serial_number
        devices["policyName"] = self.policy_name
        self.payload["devices"].append(devices)
        self.payload["issu"] = self.issu
        self.payload["epld"] = self.epld
        self.payload["packageInstall"] = self.package_install

        msg = f"self.payload {self.payload}"
        self.log.debug(msg)

    def _get(self, item):
        return self.make_boolean(self.make_none(self.response_data.get(item)))

    # Mandatory properties
    @property
    def policy_name(self):
        """
        Set the policy_name of the policy to query.
        """
        return self.properties.get("policy_name")

    @policy_name.setter
    def policy_name(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"policy_name must be a string. Got {value}."
            self.module.fail_json(msg, **self.failed_result)
        self.properties["policy_name"] = value

    @property
    def serial_number(self):
        """
        Set the serial_number of the device to query.
        """
        return self.properties.get("serial_number")

    @serial_number.setter
    def serial_number(self, value):
        self.properties["serial_number"] = value

    # Optional properties

    @property
    def issu(self):
        """
        Enable (True) or disable (False) issu compatibility check.
        Valid values:
            True - Enable issu compatibility check
            False - Disable issu compatibility check
        Default: True
        """
        return self.properties.get("issu")

    @issu.setter
    def issu(self, value):
        method_name = inspect.stack()[0][3]
        value = self.make_boolean(value)
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"issu must be a boolean value. Got {value}."
            self.module.fail_json(msg, **self.failed_result)
        self.properties["issu"] = value

    @property
    def epld(self):
        """
        Enable (True) or disable (False) epld compatibility check.

        Valid values:
            True - Enable epld compatibility check
            False - Disable epld compatibility check
        Default: False
        """
        return self.properties.get("epld")

    @epld.setter
    def epld(self, value):
        method_name = inspect.stack()[0][3]
        value = self.make_boolean(value)
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"epld must be a boolean value. Got {value}."
            self.module.fail_json(msg, **self.failed_result)
        self.properties["epld"] = value

    @property
    def package_install(self):
        """
        Enable (True) or disable (False) package_install compatibility check.
        Valid values:
            True - Enable package_install compatibility check
            False - Disable package_install compatibility check
        Default: False
        """
        return self.properties.get("package_install")

    @package_install.setter
    def package_install(self, value):
        method_name = inspect.stack()[0][3]
        value = self.make_boolean(value)
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "package_install must be a boolean value. "
            msg += f"Got {value}."
            self.module.fail_json(msg, **self.failed_result)
        self.properties["package_install"] = value

    # Getter properties
    @property
    def comp_disp(self):
        """
        Return the compDisp (CLI output from show install all status)
        of the install-options response, if it exists.
        Return None otherwise
        """
        return self.compatibility_status.get("compDisp")

    @property
    def device_name(self):
        """
        Return the deviceName of the install-options response,
        if it exists.
        Return None otherwise
        """
        return self.compatibility_status.get("deviceName")

    @property
    def epld_modules(self):
        """
        Return the epldModules of the install-options response,
        if it exists.
        Return None otherwise

        epldModules will be "null" if self.epld is False.
        _get will convert to NoneType in this case.
        """
        return self._get("epldModules")

    @property
    def err_message(self):
        """
        Return the errMessage of the install-options response,
        if it exists.
        Return None otherwise
        """
        return self._get("errMessage")

    @property
    def install_option(self):
        """
        Return the installOption of the install-options response,
        if it exists.
        Return None otherwise
        """
        return self.compatibility_status.get("installOption")

    @property
    def install_packages(self):
        """
        Return the installPackages of the install-options response,
        if it exists.
        Return None otherwise

        NOTE:   yes, installPacakges is misspelled in the response in the
                following versions (at least):
                12.1.2e
                12.1.3b
        """
        return self._get("installPacakges")

    @property
    def ip_address(self):
        """
        Return the ipAddress of the install-options response,
        if it exists.
        Return None otherwise
        """
        return self.compatibility_status.get("ipAddress")

    @property
    def response_data(self) -> Dict[str, Any]:
        """
        Return the DATA portion of the controller response.
        Return empty dict otherwise
        """
        return self.properties.get("response_data", {})

    @property
    def os_type(self):
        """
        Return the osType of the install-options response,
        if it exists.
        Return None otherwise
        """
        return self.compatibility_status.get("osType")

    @property
    def platform(self):
        """
        Return the platform of the install-options response,
        if it exists.
        Return None otherwise
        """
        return self.compatibility_status.get("platform")

    @property
    def pre_issu_link(self):
        """
        Return the preIssuLink of the install-options response, if it exists.
        Return None otherwise
        """
        return self.compatibility_status.get("preIssuLink")

    @property
    def raw_data(self):
        """
        Return the raw data of the install-options response, if it exists.
        Alias for self.response_data
        """
        return self.response_data

    @property
    def raw_response(self):
        """
        Return the raw response, if it exists.
        Alias for self.response_current
        """
        return self.response_current

    @property
    def rep_status(self):
        """
        Return the repStatus of the install-options response, if it exists.
        Return None otherwise
        """
        return self.compatibility_status.get("repStatus")

    @property
    def status(self):
        """
        Return the status of the install-options response,
        if it exists.
        Return None otherwise
        """
        return self.compatibility_status.get("status")

    @property
    def timestamp(self):
        """
        Return the timestamp of the install-options response,
        if it exists.
        Return None otherwise
        """
        return self.compatibility_status.get("timestamp")

    @property
    def version(self):
        """
        Return the version of the install-options response,
        if it exists.
        Return None otherwise
        """
        return self.compatibility_status.get("version")

    @property
    def version_check(self):
        """
        Return the versionCheck (version check CLI output)
        of the install-options response, if it exists.
        Return None otherwise
        """
        return self.compatibility_status.get("versionCheck")
