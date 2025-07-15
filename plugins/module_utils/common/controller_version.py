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
__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect
import logging

from .api.v1.fm.fm import EpVersion
from .conversion import ConversionUtils
from .exceptions import ControllerResponseError
from .properties import Properties


@Properties.add_rest_send
class ControllerVersion:
    """
    Return image version information from the Controller

    ### Endpoint
        ``/appcenter/cisco/ndfc/api/v1/fm/about/version``

    ### Usage (where module is an instance of AnsibleModule):
    ```python
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(ansible_module.params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    instance = ControllerVersion()
    instance.rest_send = rest_send
    instance.refresh()
    if instance.version == "12.1.2e":
        # do 12.1.2e stuff
    else:
        # do other stuff
    ```

    ### Response

    #### ND 3.x

    ```json
        {
            "version": "12.1.2e",
            "mode": "LAN",
            "isMediaController": false,
            "dev": false,
            "isHaEnabled": false,
            "install": "EASYFABRIC",
            "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "is_upgrade_inprogress": false
        }
    ```

    #### ND 4.1 EFT 138c

    ```json
        {
            "version": "12.4.1.225",
            "mode": "",
            "isMediaController": false,
            "dev": false,
            "isHaEnabled": false,
            "install": "",
            "uuid": "",
            "is_upgrade_inprogress": false
        }
    ```

    #### ND 4.1 EFT 156b

    ```json
        {
            "version": "12.4.1.245",
            "mode": "",
            "isMediaController": false,
            "dev": false,
            "isHaEnabled": false,
            "install": "",
            "uuid": "",
            "is_upgrade_inprogress": false
        }

    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.conversion = ConversionUtils()
        self.ep_version = EpVersion()
        self._response_data = None
        self._rest_send = None

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

    def refresh(self):
        """
        Refresh self.response_data with current version info from the Controller
        """
        # pylint: disable=no-member
        method_name = inspect.stack()[0][3]
        self.rest_send.path = self.ep_version.path
        self.rest_send.verb = self.ep_version.verb
        self.rest_send.commit()

        if self.rest_send.result_current["success"] is False:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"failed: {self.rest_send.result_current}"
            raise ControllerResponseError(msg)

        if self.rest_send.result_current["found"] is False:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"failed: {self.rest_send.result_current}"
            raise ControllerResponseError(msg)

        self._response_data = self.rest_send.response_current.get("DATA")
        if self.response_data is None:
            msg = f"{self.class_name}.refresh() failed: response "
            msg += "does not contain DATA key. Controller response: "
            msg += f"{self.rest_send.response_current}"
            raise ValueError(msg)

        # Ensure response_data is a dictionary
        if not isinstance(self._response_data, dict):
            msg = f"{self.class_name}.refresh() failed: "
            msg += f"Expected response data to be a dictionary, got {type(self._response_data).__name__}. "
            msg += f"Data: {self._response_data}"
            raise ValueError(msg)

    def _get(self, item):
        return self.conversion.make_none(self.conversion.make_boolean(self.response_data.get(item)))

    def _validate_and_split_version(self):
        """
        Validate version format and return split version parts.

        Expected formats:
            w.x.y (3 parts) or w.x.y.z (4 parts)

        Returns:
            list: Version parts split by '.'

        Raises:
            ValueError: If version format is unexpected
        """
        version_parts = self.version.split(".")
        if len(version_parts) not in [3, 4]:
            msg = f"{self.class_name}._validate_and_split_version: "
            msg += f"Unexpected version format '{self.version}'. "
            msg += f"Expected 3 or 4 parts (w.x.y or w.x.y.z), got {len(version_parts)} parts"
            raise ValueError(msg)
        return version_parts

    @property
    def dev(self):
        """
        Return True if the Controller is running a development release.
        Return False if the Controller is not running a development release.
        Return None otherwise

        Possible values:
            True
            False
            None
        """
        return self._get("dev")

    @property
    def install(self):
        """
        Return the value of install, if it exists.
        Return None otherwise

        Possible values:
            EASYFABRIC
            (probably other values)
            None
        """
        return self._get("install")

    @property
    def is_ha_enabled(self):
        """
        Return True if Controller is high-availability enabled.
        Return False if Controller is not high-availability enabled.
        Return None otherwise

        Possible values:
            True
            False
            None
        """
        return self._get("isHaEnabled")

    @property
    def is_media_controller(self):
        """
        Return True if Controller is a media controller.
        Return False if Controller is not a media controller.
        Return None otherwise

        Possible values:
            True
            False
            None
        """
        return self._get("isMediaController")

    @property
    def is_upgrade_inprogress(self):
        """
        Return True if a Controller upgrade is in progress.
        Return False if a Controller upgrade is not in progress.
        Return None otherwise

        Possible values:
            True
            False
            None
        """
        return self._get("is_upgrade_inprogress")

    @property
    def response_data(self):
        """
        Return the data retrieved from the request
        """
        return self._response_data

    @property
    def mode(self):
        """
        Return the controller mode, if it exists.
        Return None otherwise

        Possible values:
            LAN
            None
        """
        return self._get("mode")

    @property
    def uuid(self):
        """
        Return the value of uuid, if it exists.
        Return None otherwise

        Possible values:
            uuid e.g. "f49e6088-ad4f-4406-bef6-2419de914df1"
            None
        """
        return self._get("uuid")

    @property
    def version(self):
        """
        Return the controller version, if it exists.
        Raise ValueError if version is not available.

        Possible values:
            version, e.g. "12.1.2e"
        """
        version = self._get("version")
        if version is None:
            msg = f"{self.class_name}.version: "
            msg += "Version information not available in controller response"
            raise ValueError(msg)
        return version

    @property
    def version_major(self):
        """
        Return the controller major version as a string.
        Raise ValueError if version format is unexpected.

        We are assuming semantic versioning based on:
        https://semver.org

        Expected formats:
            w.x.y (3 parts) or w.x.y.z (4 parts)

        Possible values:
            if version is 12.1.2e, return "12"
            if version is 12.4.1.245, return "12"
        """
        version_parts = self._validate_and_split_version()
        return version_parts[0]

    @property
    def version_minor(self):
        """
        Return the controller minor version as a string.
        Raise ValueError if version format is unexpected.

        We are assuming semantic versioning based on:
        https://semver.org

        Expected formats:
            w.x.y (3 parts) or w.x.y.z (4 parts)

        Possible values:
            if version is 12.1.2e, return "1"
            if version is 12.4.1.245, return "4"
        """
        version_parts = self._validate_and_split_version()
        return version_parts[1]

    @property
    def version_patch(self):
        """
        Return the controller patch version as a string.
        Raise ValueError if version format is unexpected.

        We are assuming semantic versioning based on:
        https://semver.org

        Expected formats:
            w.x.y (3 parts) or w.x.y.z (4 parts)

        Possible values:
            if version is 12.1.2e, return "2e"
            if version is 12.4.1.245, return "1"
        """
        version_parts = self._validate_and_split_version()
        return version_parts[2]

    @property
    def is_controller_version_4x(self) -> bool:
        """
        ### Summary

        -   Return True if the controller version implies ND 4.0 or higher.
        -   Return False otherwise.
        """
        method_name = inspect.stack()[0][3]

        result = None
        try:
            major = self.version_major
            minor = self.version_minor

            if major is None or minor is None:
                # If we can't determine version, assume it's a newer version
                result = True
            else:
                # Extract numeric part only from minor version in case of formats like "2e"
                minor_numeric = ""
                for char in minor:
                    if char.isdigit():
                        minor_numeric += char
                    else:
                        break

                if not minor_numeric:
                    # If no numeric part found, assume it's a newer version
                    result = True
                else:
                    if int(major) == 12 and int(minor_numeric) < 3:
                        result = False
                    else:
                        result = True
        except (ValueError, TypeError) as e:
            # If version parsing fails, assume it's a newer version
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Error parsing version {self.version}: {e}. Assuming version 4.x"
            self.log.warning(msg)
            result = True

        msg = f"{self.class_name}.{method_name}: "
        msg += f"self.version: {self.version}, "
        msg += f"Controller is version 4.x: {result}"
        self.log.debug(msg)

        return result
