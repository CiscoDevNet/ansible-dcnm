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

import inspect
import json
import logging

from ..common.api.v1.imagemanagement.rest.imageupgrade.imageupgrade import \
    EpInstallOptions
from ..common.conversion import ConversionUtils
from ..common.exceptions import ControllerResponseError
from ..common.properties import Properties


@Properties.add_rest_send
@Properties.add_results
class ImageInstallOptions:
    """
    ### Summary
    Retrieve install-options details for ONE switch from the controller and
    provide property accessors for the policy attributes.

    ### Caveats

    -   This retrieves for a SINGLE switch only.
    -   Set serial_number and policy_name and call refresh() for
        each switch separately.

    ### Usage

    ```python
    instance = ImageInstallOptions()
    # Mandatory
    instance.rest_send = rest_send
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
    ### etc...
    ```

    install-options are retrieved by calling ``refresh()``.

    ### Endpoint

    /appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupgrade/install-options

    ### Payload

    ```json
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
    ```

    ### Response body

    -   NOTES
        1.  epldModules will be null if epld is false in the request body.
            This class converts this to None (python NoneType) in this case.

    ```json
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
    ```
    """

    def __init__(self) -> None:
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.compatibility_status = {}
        self.payload: dict = {}

        self.conversion = ConversionUtils()
        self.ep_install_options = EpInstallOptions()

        self._response_data = None

        self._init_properties()
        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

    def _init_properties(self):
        """
        ### Summary
        Initialize class properties.

        ### Raises
        None
        """
        self._epld = False
        self._issu = True
        self._package_install = False
        self._policy_name = None
        self._rest_send = None
        self._results = None
        self._serial_number = None
        self._timeout = 300

    def _validate_refresh_parameters(self) -> None:
        """
        ### Summary
        -   Ensure parameters are set correctly for a refresh() call.

        ### Raises
        ``ValueError`` if parameters are not set correctly.
        """
        # pylint: disable=no-member
        method_name = inspect.stack()[0][3]

        if self.policy_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "policy_name must be set before calling refresh()."
            raise ValueError(msg)

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling refresh()."
            raise ValueError(msg)

        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "results must be set before calling refresh()."
            raise ValueError(msg)

        if self.serial_number is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "serial_number must be set before calling refresh()."
            raise ValueError(msg)

    def refresh(self) -> None:
        """
        ### Summary
        Refresh ``self.response_data`` with current install-options from
        the controller.

        ### Raises
        -   ``ControllerResponseError``: if the controller response is bad.
            e.g. 401, 500 error, etc.
        """
        method_name = inspect.stack()[0][3]

        self._validate_refresh_parameters()

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.epld {self.epld}, "
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
            # Yes, installPackages is intentionally misspelled below.
            self._response_data = {
                "compatibilityStatusList": [],
                "epldModules": {},
                "installPacakges": None,
                "errMessage": "",
            }
            return

        self._build_payload()

        # pylint: disable=no-member
        self.rest_send.path = self.ep_install_options.path
        self.rest_send.verb = self.ep_install_options.verb
        self.rest_send.payload = self.payload
        self.rest_send.commit()

        self._response_data = self.rest_send.response_current.get("DATA", {})
        # pylint: enable=no-member

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.response_data: {json.dumps(self.response_data, indent=4, sort_keys=True)}"
        self.log.debug(msg)

        # pylint: disable=no-member
        if self.rest_send.result_current["success"] is False:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Bad result when retrieving install-options from "
            msg += f"the controller. Controller response: {self.rest_send.response_current}. "
            if self.response_data.get("error", None) is None:
                raise ControllerResponseError(msg)
            if "does not have package to continue" in self.response_data.get(
                "error", ""
            ):
                msg += f"Possible cause: Image policy {self.policy_name} does not have "
                msg += "a package defined, and package_install is set to "
                msg += f"True in the playbook for device {self.serial_number}."
            raise ControllerResponseError(msg)
        # pylint: enable=no-member

        if self.response_data.get("compatibilityStatusList") is None:
            self.compatibility_status = {}
        else:
            self.compatibility_status = self.response_data.get(
                "compatibilityStatusList", [{}]
            )[0]
        # epldModules is handled in the epld_modules.getter property

    def _build_payload(self) -> None:
        """
        ### Summary
        Build the payload for the install-options request.

        ### Raises
        None

        ### Payload structure
        ```json
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
        ```
        """
        self.payload: dict = {}
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
        """
        ### Summary
        Return items from self.response_data.

        ### Raises
        None
        """
        return self.conversion.make_boolean(
            self.conversion.make_none(self.response_data.get(item))
        )

    # Mandatory properties
    @property
    def policy_name(self):
        """
        ### Summary
        Set the policy_name of the policy to query.

        ### Raises
        ``TypeError``: if value is not a string.
        """
        return self._policy_name

    @policy_name.setter
    def policy_name(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"instance.policy_name must be a string. Got {value}."
            raise TypeError(msg)
        self._policy_name = value

    @property
    def serial_number(self):
        """
        ### Summary
        Set the serial_number of the device to query.

        ### Raises
        None
        """
        return self._serial_number

    @serial_number.setter
    def serial_number(self, value):
        self._serial_number = value

    # Optional properties
    @property
    def issu(self):
        """
        ### Summary
        Enable (True) or disable (False) issu compatibility check.

        ### Raises
        ``TypeError``: if value is not a boolean.

        ### Valid values

        -   True - Enable issu compatibility check
        -   False - Disable issu compatibility check

        ### Default value
        True
        """
        return self._issu

    @issu.setter
    def issu(self, value):
        method_name = inspect.stack()[0][3]
        value = self.conversion.make_boolean(value)
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"issu must be a boolean value. Got {value}."
            raise TypeError(msg)
        self._issu = value

    @property
    def epld(self):
        """
        ### Summary
        Enable (True) or disable (False) epld compatibility check.

        ### Raises
        ``TypeError`` if value is not a boolean.

        ### Valid values

        -   True - Enable epld compatibility check
        -   False - Disable epld compatibility check

        ### Default value
        False
        """
        return self._epld

    @epld.setter
    def epld(self, value):
        method_name = inspect.stack()[0][3]
        value = self.conversion.make_boolean(value)
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"epld must be a boolean value. Got {value}."
            raise TypeError(msg)
        self._epld = value

    @property
    def package_install(self):
        """
        ### Summary
        Enable (True) or disable (False) package_install compatibility check.

        ### Raises
        ``TypeError`` if value is not a boolean.

        ### Valid values

        -   True - Enable package_install compatibility check
        -   False - Disable package_install compatibility check

        ### Default value
        False
        """
        return self._package_install

    @package_install.setter
    def package_install(self, value):
        method_name = inspect.stack()[0][3]
        value = self.conversion.make_boolean(value)
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "package_install must be a boolean value. "
            msg += f"Got {value}."
            raise TypeError(msg)
        self._package_install = value

    # Getter properties
    @property
    def comp_disp(self):
        """
        ### Summary

        -   Return the compDisp (CLI output from show install all status)
            of the install-options response, if it exists.
        -   Return None otherwise
        """
        return self.compatibility_status.get("compDisp")

    @property
    def device_name(self):
        """
        ### Summary

        -   Return the deviceName of the install-options response,
            if it exists.
        -   Return None otherwise
        """
        return self.compatibility_status.get("deviceName")

    @property
    def epld_modules(self):
        """
        ### Summary

        -   Return the epldModules of the install-options response,
            if it exists.
        -   Return None otherwise.

        ### Notes
        -   epldModules will be "null" if self.epld is False.
        -   _get() will convert to NoneType in this case.
        """
        return self._get("epldModules")

    @property
    def err_message(self):
        """
        ### Summary

        -   Return the errMessage of the install-options response,
            if it exists.
        -   Return None otherwise
        """
        return self._get("errMessage")

    @property
    def install_option(self):
        """
        ### Summary

        -   Return the installOption of the install-options response,
            if it exists.
        -   Return None otherwise
        """
        return self.compatibility_status.get("installOption")

    @property
    def install_packages(self):
        """
        ### Summary

        -   Return the installPackages of the install-options response,
            if it exists.
        -   Return None otherwise

        ### NOTE
        Yes, installPacakges is misspelled in the response in the following
        controller versions (at least):

        -   12.1.2e
        -   12.1.3b
        """
        return self._get("installPacakges")

    @property
    def ip_address(self):
        """
        ### Summary

        -   Return the ipAddress of the install-options response,
            if it exists.
        -   Return None otherwise
        """
        return self.compatibility_status.get("ipAddress")

    @property
    def response_data(self) -> dict:
        """
        ### Summary

        -   Return the DATA portion of the controller response.
        -   Return empty dict otherwise.
        """
        return self._response_data

    @property
    def os_type(self):
        """
        ### Summary

        -   Return the osType of the install-options response,
            if it exists.
        -   Return None otherwise
        """
        return self.compatibility_status.get("osType")

    @property
    def platform(self):
        """
        ### Summary

        -   Return the platform of the install-options response,
            if it exists.
        -   Return None otherwise
        """
        return self.compatibility_status.get("platform")

    @property
    def pre_issu_link(self):
        """
        ### Summary

        -   Return the ``preIssuLink`` of the install-options response,
            if it exists.
        -   Return ``None`` otherwise.
        """
        return self.compatibility_status.get("preIssuLink")

    @property
    def raw_data(self):
        """
        ### Summary

        -   Return the raw data of the install-options response,
            if it exists.
        -   Return ``None`` otherwise.
        """
        return self.response_data

    @property
    def raw_response(self):
        """
        ### Summary

        -   Return the raw install-options response, if it exists.
        -   Alias for self.rest_send.response_current
        """
        return self.rest_send.response_current  # pylint: disable=no-member

    @property
    def rep_status(self):
        """
        ### Summary

        -   Return the ``repStatus`` of the install-options response,
            if it exists.
        -   Return ``None`` otherwise.
        """
        return self.compatibility_status.get("repStatus")

    @property
    def status(self):
        """
        ### Summary

        -   Return the ``status`` of the install-options response,
            if it exists.
        -   Return ``None`` otherwise.
        """
        return self.compatibility_status.get("status")

    @property
    def timestamp(self):
        """
        ### Summary

        -   Return the ``timestamp`` of the install-options response,
            if it exists.
        -   Return ``None`` otherwise.
        """
        return self.compatibility_status.get("timestamp")

    @property
    def version(self):
        """
        ### Summary

        -   Return the ``version`` of the install-options response,
            if it exists.
        -   Return ``None`` otherwise.
        """
        return self.compatibility_status.get("version")

    @property
    def version_check(self):
        """
        ### Summary

        -   Return the ``versionCheck`` (version check CLI output)
            of the install-options response, if it exists.
        -   Return ``None`` otherwise.
        """
        return self.compatibility_status.get("versionCheck")
