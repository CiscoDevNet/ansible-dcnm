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
    ```json
        {
            "version": "12.1.2e",
            "mode": "LAN",
            "isMediaController": false,
            "dev": false,
            "isHaEnabled": false,
            "install": "EASYFABRIC",
            "uuid": "f49e6088-ad4f-4406-bef6-2419de914ff1",
            "is_upgrade_inprogress": false
        }
    ```
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

    def _get(self, item):
        return self.conversion.make_none(
            self.conversion.make_boolean(self.response_data.get(item))
        )

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
        Return None otherwise

        Possible values:
            version, e.g. "12.1.2e"
            None
        """
        return self._get("version")

    @property
    def version_major(self):
        """
        Return the controller major version, if it exists.
        Return None otherwise

        We are assuming semantic versioning based on:
        https://semver.org

        Possible values:
            if version is 12.1.2e, return 12
            None
        """
        if self.version is None:
            return None
        return (self._get("version").split("."))[0]

    @property
    def version_minor(self):
        """
        Return the controller minor version, if it exists.
        Return None otherwise

        We are assuming semantic versioning based on:
        https://semver.org

        Possible values:
            if version is 12.1.2e, return 1
            None
        """
        if self.version is None:
            return None
        return (self._get("version").split("."))[1]

    @property
    def version_patch(self):
        """
        Return the controller minor version, if it exists.
        Return None otherwise

        We are assuming semantic versioning based on:
        https://semver.org

        Possible values:
            if version is 12.1.2e, return 2e
            None
        """
        if self.version is None:
            return None
        return (self._get("version").split("."))[2]
