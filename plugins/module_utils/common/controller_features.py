"""
Class to retrieve and return information about an NDFC controller
"""

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

from .api.v1.fm.fm import EpFeatures
from .conversion import ConversionUtils
from .exceptions import ControllerResponseError
from .properties import Properties


@Properties.add_rest_send
class ControllerFeatures:
    """
    ### Summary
    Return feature information from the Controller

    ### Usage

    ```python
    sender = Sender()
    sender.ansible_module = ansible_module
    rest_send = RestSend(ansible_module.params)
    rest_send.response_handler = ResponseHandler()
    rest_send.sender = sender

    instance = ControllerFeatures()
    instance.rest_send = rest_send
    # retrieves all feature information
    try:
        instance.refresh()
    except ControllerResponseError as error:
        # handle error
    # filters the feature information
    instance.filter = "pmn"
    # retrieves the admin_state for feature pmn
    pmn_admin_state = instance.admin_state
    # retrieves the operational state for feature pmn
    pmn_oper_state = instance.oper_state
    # etc...
    ```

    ### Retrievable properties for the filtered feature

    -   admin_state - str
            -   "enabled"
            -   "disabled"
    -   apidoc, list of dict
            -   ```json
                [
                    {
                        "url": "https://path/to/api-docs",
                        "subpath": "pmn",
                        "schema": null
                    }
                ]
                ```
    -   description
            -   "Media Controller for IP Fabrics"
            -   str
    -   healthz
            -   "https://path/to/healthz"
            -   str
    -   hidden
            -   True
            -   False
            -   bool
    -   featureset
            -   ```json
                {
                    "lan": {
                        "default": false
                    }
                }
                ```
    -   name
            -   "IP Fabric for Media"
            -   str
    -   oper_state
            -   "started"
            -   "stopped"
            -   ""
            -   str
    -   predisablecheck
            -   "https://path/to/predisablecheck"
            -   str
    -   installed
            -   "2024-05-08 18:02:45.626691263 +0000 UTC"
            -   str
    -   kind
            -   "feature"
            -   str
    -   requires
            -   ```json
                ["pmn-telemetry-mgmt", "pmn-telemetry-data"]
                ```
    -   spec
            -   ""
            -   str
    -   ui
            -   True
            -   False
            -   bool

    ### Response
    ```json
        {
            "status": "success",
            "data": {
                "name": "",
                "version": 179,
                "features": {
                    "change-mgmt": {
                        "name": "Change Control",
                        "description": "Tracking, Approval, and Rollback...",
                        "ui": false,
                        "predisablecheck": "https://path/preDisableCheck",
                        "spec": "",
                        "admin_state": "disabled",
                        "oper_state": "",
                        "kind": "featurette",
                        "featureset": {
                            "lan": {
                                "default": false
                            }
                        }
                    }
                    etc...
                }
            }
        }
    ```

    ### Endpoint
    /appcenter/cisco/ndfc/api/v1/fm/features

    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ControllerFeatures()")

        self.conversion = ConversionUtils()
        self.ep_features = EpFeatures()

        self._filter = None
        self._rest_send = None
        self._response_data = None

    def refresh(self):
        """
        -   Refresh self.response_data with current features info
            from the controller
        -   Raise ``ValueError`` if the endpoint assignment fails.
        """
        method_name = inspect.stack()[0][3]

        # pylint: disable=no-member
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.rest_send must be set "
            msg += "before calling refresh()."
            raise ValueError(msg)

        self.rest_send.path = self.ep_features.path
        self.rest_send.verb = self.ep_features.verb

        # Store the current value of check_mode, then disable
        # check_mode since ControllerFeatures() only reads data
        # from the controller.
        # Restore the value of check_mode after the commit.
        self.rest_send.save_settings()
        self.rest_send.check_mode = False
        self.rest_send.commit()
        self.rest_send.restore_settings()

        if self.rest_send.result_current["success"] is False:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Bad controller response: {self.rest_send.response_current}"
            raise ControllerResponseError(msg)

        self._response_data = (
            self.rest_send.response_current.get("DATA", {})
            .get("data", {})
            .get("features", {})
        )
        if self.response_data == {}:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Controller response does not match expected structure: "
            msg += f"{self.rest_send.response_current}"
            raise ControllerResponseError(msg)

    def _get(self, item):
        """
        -   Return the value of the item from the filtered response_data.
        -   Return None if the item does not exist.
        """
        data = self.response_data.get(self.filter, {}).get(item, None)
        return self.conversion.make_boolean(self.conversion.make_none(data))

    @property
    def admin_state(self):
        """
        -   Return the controller admin_state for filter, if it exists.
        -   Return None otherwise
        -   Possible values:
                -   enabled
                -   disabled
                -   None
        """
        return self._get("admin_state")

    @property
    def enabled(self):
        """
        -   Return True if the filtered feature admin_state is "enabled".
        -   Return False otherwise.
        -   Possible values:
                -   True
                -   False
        """
        if self.admin_state == "enabled":
            return True
        return False

    @property
    def filter(self):
        """
        -   getter: Return the filter value
        -   setter: Set the filter value
        -   The filter value should be the name of the feature
        -   For example:
                -   lan
                        -   Full LAN functionality in addition to Fabric
                            Discovery
                -   pmn
                        -   Media Controller for IP Fabrics
                -   vxlan
                        -   Automation, Compliance, and Management for
                            NX-OS and Other devices

        """
        return self._filter

    @filter.setter
    def filter(self, value):
        self._filter = value

    @property
    def oper_state(self):
        """
        -   Return the oper_state for the filtered feature, if it exists.
        -   Return None otherwise
        -   Possible values:
                -   started
                -   stopped
                -   ""
        """
        return self._get("oper_state")

    @property
    def response_data(self):
        """
        Return the data retrieved from the request
        """
        return self._response_data

    @property
    def started(self):
        """
        -   Return True if the filtered feature oper_state is "started".
        -   Return False otherwise.
        -   Possible values:
                -   True
                -   False
        """
        if self.oper_state == "started":
            return True
        return False
