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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError


class ControllerFeatures:
    """
    -   Return feature information from the Controller
    -   Endpoint: /appcenter/cisco/ndfc/api/v1/fm/features
    -   Usage (where params is AnsibleModule.params):

    ```python
        instance = ControllerFeatures(params)
        instance.rest_send = RestSend(AnsibleModule)
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

    -   Retrievable properties for the filtered feature
            -   admin_state - str
                    -   "enabled"
                    -   "disabled"
            -   apidoc - list of dict
                    -   [
                            {
                                "url": "https://path/to/api-docs",
                                "subpath": "pmn",
                                "schema": null
                            }
                        ]
            -   description - str
                    -   "Media Controller for IP Fabrics"
            -   healthz - str
                    -   "https://path/to/healthz"
            -   hidden - bool
                    -   True
                    -   False
            -   featureset - dict
                    -   { "lan": { "default": false }}
            -   name - str
                    -   "IP Fabric for Media"
            -   oper_state - str
                    -   "started"
                    -   "stopped"
                    -   ""
            -   predisablecheck - str
                    -   "https://path/to/predisablecheck"
            -   installed - str
                    -   "2024-05-08 18:02:45.626691263 +0000 UTC"
            -   kind - str
                    -   "feature"
            -   requires - list
                    -   ["pmn-telemetry-mgmt", "pmn-telemetry-data"]
            -   spec - str
                    -   ""
            -   ui - bool
                    -   True
                    -   False

    Response:
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
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__
        self.params = params

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ControllerFeatures()")

        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.__init__(): "
            msg += "check_mode is required"
            raise ValueError(msg)

        self.conversion = ConversionUtils()
        self.endpoints = ApiEndpoints()
        self._init_properties()

    def _init_properties(self):
        self.properties = {}
        self.properties["data"] = None
        self.properties["rest_send"] = None
        self.properties["result"] = None
        self.properties["response"] = None

    def refresh(self):
        """
        -   Refresh self.response_data with current features info
            from the controller
        -   Raise ``ValueError`` if the endpoint assignment fails.
        """
        method_name = inspect.stack()[0][3]

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.rest_send must be set "
            msg += "before calling commit."
            raise ValueError(msg)

        path = self.endpoints.fm_features.get("path")
        verb = self.endpoints.fm_features.get("verb")
        self.rest_send.path = path
        self.rest_send.verb = verb

        # Store the current value of check_mode, then disable
        # check_mode since ControllerFeatures() only reads data
        # from the controller.
        # Restore the value of check_mode after the commit.
        current_check_mode = self.rest_send.check_mode
        self.rest_send.check_mode = False
        self.rest_send.commit()
        self.rest_send.check_mode = current_check_mode

        if self.rest_send.result_current["success"] is False:
            msg = f"{self.class_name}.refresh() failed: {self.rest_send.result_current}"
            raise ControllerResponseError(msg)

        self.properties["response_data"] = (
            self.rest_send.response_current.get("DATA", {})
            .get("data", {})
            .get("features", {})
        )
        if self.response_data is None:
            msg = f"{self.class_name}.refresh() failed: response "
            msg += "does not contain DATA key. Controller response: "
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
        return self.properties.get("filter")

    @filter.setter
    def filter(self, value):
        self.properties["filter"] = value

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

    @property
    def response_data(self):
        """
        Return the data retrieved from the request
        """
        return self.properties.get("response_data")

    @property
    def result(self):
        """
        Return the GET result from the Controller
        """
        return self.properties.get("result")

    @property
    def response(self):
        """
        Return the GET response from the Controller
        """
        return self.properties.get("response")

    @property
    def rest_send(self):
        """
        -   An instance of the RestSend class.
        -   Raise ``TypeError`` if the value is not an instance of RestSend.
        """
        return self.properties["rest_send"]

    @rest_send.setter
    def rest_send(self, value):
        test = None
        msg = f"{self.class_name}.rest_send must be an instance of RestSend. "
        try:
            test = value.class_name
        except AttributeError as error:
            msg += f"Error detail: {error}."
            raise TypeError(msg) from error
        if test != "RestSend":
            self.log.debug(msg)
            raise TypeError(msg)
        self.properties["rest_send"] = value
