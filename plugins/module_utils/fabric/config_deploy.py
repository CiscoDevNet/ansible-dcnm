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
import logging

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.control.fabrics.fabrics import \
    EpFabricConfigDeploy
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError


class FabricConfigDeploy:
    """
    # Initiate a fabric config-deploy operation on the controller.

    -   Raise ``ValueError`` for any caller errors, e.g. required properties
        not being set before calling FabricConfigDeploy().commit().
    -   Update FabricConfigDeploy().results to reflect success/failure of
        the operation on the controller.

    ## Usage (where params is AnsibleModule.params)

    ```python
    config_deploy = FabricConfigDeploy(params)
    config_deploy.rest_send = RestSend()
    config_deploy.payload = payload # a valid payload dictionary
    config_deploy.fabric_details = FabricDetailsByName(params)
    config_deploy.fabric_summary = FabricSummary(params)
    config_deploy.results = Results()
    try:
        config_deploy.commit()
    except ValueError as error:
        raise ValueError(error) from error
    ```
    """

    def __init__(self, params):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.params = params
        self.action = "config_deploy"
        self.cannot_deploy_fabric_reason = ""
        self.config_deploy_failed = False
        self.fabric_can_be_deployed = False

        self.check_mode = self.params.get("check_mode", None)
        if self.check_mode is None:
            msg = f"{self.class_name}.__init__(): "
            msg += "params is missing mandatory check_mode parameter."
            raise ValueError(msg)

        self.state = self.params.get("state", None)
        if self.state is None:
            msg = f"{self.class_name}.__init__(): "
            msg += "params is missing mandatory state parameter."
            raise ValueError(msg)

        self.config_deploy_result: dict[str, bool] = {}

        self.path = None
        self.verb = None
        self._init_properties()

        self.conversion = ConversionUtils()
        self.ep_config_deploy = EpFabricConfigDeploy()

        msg = "ENTERED FabricConfigDeploy(): "
        msg += f"check_mode: {self.check_mode}, "
        msg += f"state: {self.state}"
        self.log.debug(msg)

    def _init_properties(self):
        self._properties = {}
        self._properties["fabric_details"] = None
        self._properties["fabric_name"] = None
        self._properties["fabric_summary"] = None
        self._properties["payload"] = None
        self._properties["rest_send"] = None
        self._properties["results"] = None

    def _can_fabric_be_deployed(self) -> None:
        """
        -   Set self.fabric_can_be_deployed to True if the fabric configuration
            can be deployed.
        -   Set self.fabric_can_be_deployed to False otherwise.
        """
        method_name = inspect.stack()[0][3]

        self.fabric_can_be_deployed = False

        deploy = self.payload.get("DEPLOY", None)
        if deploy is False or deploy is None:
            msg = f"Fabric {self.fabric_name} DEPLOY is False or None. "
            msg += "Skipping config-deploy."
            self.log.debug(msg)
            self.cannot_deploy_fabric_reason = msg
            self.fabric_can_be_deployed = False
            self.config_deploy_failed = False
            return

        try:
            self.fabric_summary.fabric_name = self.fabric_name
        except ValueError as error:
            msg = f"Fabric {self.fabric_name} is invalid. "
            msg += "Cannot deploy fabric. "
            msg += f"Error detail: {error}"
            self.log.debug(msg)
            self.cannot_deploy_fabric_reason = msg
            self.fabric_can_be_deployed = False
            self.config_deploy_failed = True
            return

        try:
            self.fabric_summary.refresh()
        except (ControllerResponseError, ValueError) as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during FabricSummary().refresh(). "
            msg += f"Error detail: {error}"
            self.cannot_deploy_fabric_reason = msg
            self.fabric_can_be_deployed = False
            self.config_deploy_failed = True
            return

        if self.fabric_summary.fabric_is_empty is True:
            msg = f"Fabric {self.fabric_name} is empty. "
            msg += "Cannot deploy an empty fabric."
            self.log.debug(msg)
            self.cannot_deploy_fabric_reason = msg
            self.fabric_can_be_deployed = False
            self.config_deploy_failed = False
            return

        try:
            self.fabric_details.refresh()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during FabricDetailsByName().refresh(). "
            msg += f"Error detail: {error}"
            self.cannot_deploy_fabric_reason = msg
            self.fabric_can_be_deployed = False
            self.config_deploy_failed = True
            return

        self.fabric_details.filter = self.fabric_name

        if self.fabric_details.deployment_freeze is True:
            msg = f"Fabric {self.fabric_name} DEPLOYMENT_FREEZE == True. "
            msg += "Cannot deploy a fabric with deployment freeze enabled."
            self.log.debug(msg)
            self.cannot_deploy_fabric_reason = msg
            self.fabric_can_be_deployed = False
            self.config_deploy_failed = False
            return

        if self.fabric_details.is_read_only is True:
            msg = f"Fabric {self.fabric_name} IS_READ_ONLY == True. "
            msg += "Cannot deploy a read only fabric."
            self.log.debug(msg)
            self.cannot_deploy_fabric_reason = msg
            self.fabric_can_be_deployed = False
            self.config_deploy_failed = False
            return

        self.fabric_can_be_deployed = True

    def commit(self):
        """
        -   Initiate a config-deploy operation on the controller.
        -   Raise ``ValueError`` if FabricConfigDeploy().payload is not set.
        -   Raise ``ValueError`` if FabricConfigDeploy().rest_send is not set.
        -   Raise ``ValueError`` if FabricConfigDeploy().results is not set.
        -   Raise ``ValueError`` if the endpoint assignment fails.
        """
        method_name = inspect.stack()[0][3]

        if self.fabric_details is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.fabric_details must be set "
            msg += "before calling commit."
            raise ValueError(msg)
        if self.payload is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.payload must be set "
            msg += "before calling commit."
            raise ValueError(msg)
        if self.fabric_summary is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.fabric_summary must be set "
            msg += "before calling commit."
            raise ValueError(msg)
        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.rest_send must be set "
            msg += "before calling commit."
            raise ValueError(msg)
        if self.results is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.results must be set "
            msg += "before calling commit."
            raise ValueError(msg)

        self._can_fabric_be_deployed()

        msg = f"{self.class_name}.{method_name}: "
        msg += f"fabric_name: {self.fabric_name}, "
        msg += f"fabric_can_be_deployed: {self.fabric_can_be_deployed}, "
        msg += f"cannot_deploy_fabric_reason: {self.cannot_deploy_fabric_reason}"
        msg += f"config_deploy_failed: {self.config_deploy_failed}"
        self.log.debug(msg)

        if self.fabric_can_be_deployed is False:
            self.results.diff_current = {}
            self.results.action = self.action
            self.results.check_mode = self.check_mode
            self.results.state = self.state
            self.results.response_current = {
                "RETURN_CODE": 200,
                "MESSAGE": self.cannot_deploy_fabric_reason,
            }
            if self.config_deploy_failed is True:
                self.results.result_current = {"changed": False, "success": False}
            else:
                self.results.result_current = {"changed": True, "success": True}
            self.results.register_task_result()
            return

        try:
            self.ep_config_deploy.fabric_name = self.fabric_name
            self.path = self.ep_config_deploy.path
            self.verb = self.ep_config_deploy.verb
        except ValueError as error:
            raise ValueError(error) from error

        self.rest_send.path = self.path
        self.rest_send.verb = self.verb
        self.rest_send.payload = None
        self.rest_send.commit()

        result = self.rest_send.result_current["success"]
        self.config_deploy_result[self.fabric_name] = result
        if self.config_deploy_result[self.fabric_name] is False:
            self.results.diff_current = {}
        else:
            self.results.diff_current = {
                "FABRIC_NAME": self.fabric_name,
                f"{self.action}": "OK",
            }

        self.results.action = self.action
        self.results.check_mode = self.check_mode
        self.results.state = self.state
        self.results.response_current = copy.deepcopy(self.rest_send.response_current)
        self.results.result_current = copy.deepcopy(self.rest_send.result_current)
        self.results.register_task_result()

    @property
    def fabric_name(self):
        """
        The name of the fabric to config-save.
        """
        return self._properties["fabric_name"]

    @fabric_name.setter
    def fabric_name(self, value):
        try:
            self.conversion.validate_fabric_name(value)
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error
        self._properties["fabric_name"] = value

    @property
    def fabric_details(self):
        """
        -   getter: Return an instance of the FabricDetailsByName class.
        -   setter: Set an instance of the FabricDetailsByName class.
        -   setter: Raise ``TypeError`` if the value is not an
            instance of FabricDetailsByName.
        """
        return self._properties["fabric_details"]

    @fabric_details.setter
    def fabric_details(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "fabric_details must be an instance of FabricDetailsByName. "
        try:
            class_name = value.class_name
        except AttributeError as error:
            msg += f"Error detail: {error}. "
            raise TypeError(msg) from error
        if class_name != "FabricDetailsByName":
            msg += f"Got {class_name}."
            self.log.debug(msg)
            raise TypeError(msg)
        self._properties["fabric_details"] = value

    @property
    def fabric_summary(self):
        """
        -   getter: Return an instance of the FabricSummary class.
        -   setter: Set an instance of the FabricSummary class.
        -   setter: Raise ``TypeError`` if the value is not an
            instance of FabricSummary.
        """
        return self._properties["fabric_summary"]

    @fabric_summary.setter
    def fabric_summary(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "fabric_summary must be an instance of FabricSummary. "
        try:
            class_name = value.class_name
        except AttributeError as error:
            msg += f"Error detail: {error}. "
            raise TypeError(msg) from error
        if class_name != "FabricSummary":
            msg += f"Got {class_name}."
            self.log.debug(msg)
            raise TypeError(msg)
        self._properties["fabric_summary"] = value

    @property
    def payload(self):
        """
        -   The fabric payload used to create/merge/replace the fabric.
        -   Raise ``ValueError`` if the value is not a dictionary.
        -   Raise ``ValueError`` the payload is missing FABRIC_NAME key.
        """
        return self._properties["payload"]

    @payload.setter
    def payload(self, value):
        method_name = inspect.stack()[0][3]

        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name} must be a dictionary. "
            msg += f"Got type: {type(value).__name__}."
            self.log.debug(msg)
            raise ValueError(msg)
        if value.get("FABRIC_NAME", None) is None:
            msg = f"{self.class_name}.{method_name} payload is missing "
            msg += "FABRIC_NAME."
            self.log.debug(msg)
            raise ValueError(msg)
        try:
            self.fabric_name = value["FABRIC_NAME"]
        except ValueError as error:
            raise ValueError(error) from error
        self._properties["payload"] = value

    @property
    def rest_send(self):
        """
        -   getter: Return an instance of the RestSend class.
        -   setter: Set an instance of the RestSend class.
        -   setter: Raise ``TypeError`` if the value is not an
            instance of RestSend.
        """
        return self._properties["rest_send"]

    @rest_send.setter
    def rest_send(self, value):
        method_name = inspect.stack()[0][3]
        _class_name = None
        msg = f"{self.class_name}.{method_name}: "
        msg += "value must be an instance of RestSend. "
        try:
            _class_name = value.class_name
        except AttributeError as error:
            msg += f"Error detail: {error}."
            raise TypeError(msg) from error
        if _class_name != "RestSend":
            self.log.debug(msg)
            raise TypeError(msg)
        self._properties["rest_send"] = value

    @property
    def results(self):
        """
        -   getter: Return an instance of the Results class.
        -   setter: Set an instance of the Results class.
        -   setter: Raise ``TypeError`` if the value is not an
            instance of Results.
        """
        return self._properties["results"]

    @results.setter
    def results(self, value):
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "
        msg += "value must be an instance of Results. "
        msg += f"Got value {value} of type {type(value).__name__}."
        _class_name = None
        try:
            _class_name = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            self.log.debug(msg)
            raise TypeError(msg) from error
        if _class_name != "Results":
            self.log.debug(msg)
            raise TypeError(msg)
        self._properties["results"] = value
