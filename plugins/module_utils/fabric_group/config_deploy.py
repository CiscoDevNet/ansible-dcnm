# Copyright (c) 2025 Cisco and/or its affiliates.
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
# pylint: disable=too-many-instance-attributes
"""
Initiate a fabric group config-deploy operation on the controller.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import logging

from ..common.api.onemanage.endpoints import EpOneManageFabricConfigDeploy
from ..common.conversion import ConversionUtils
from ..common.exceptions import ControllerResponseError
from ..common.rest_send_v2 import RestSend
from ..common.results_v2 import Results
from ..fabric.fabric_details_v3 import FabricDetailsByName
from ..fabric.fabric_summary_v2 import FabricSummary


class FabricGroupConfigDeploy:
    """
    # Initiate a fabric config-deploy operation on the controller.

    -   Raise ``ValueError`` for any caller errors, e.g. required properties
        not being set before calling FabricConfigDeploy().commit().
    -   Update FabricConfigDeploy().results to reflect success/failure of
        the operation on the controller.

    ## Usage

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

    config_deploy = FabricGroupConfigDeploy()
    config_deploy.rest_send = rest_send
    config_deploy.payload = payload # a valid payload dictionary
    config_deploy.fabric_details = FabricDetailsByName()
    config_deploy.fabric_summary = FabricSummary(params)
    config_deploy.results = results
    try:
        config_deploy.commit()
    except ValueError as error:
        raise ValueError(error) from error
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.action: str = "config_deploy"
        self.cannot_deploy_fabric_reason: str = ""
        self.config_deploy_failed: bool = False
        self.config_deploy_result: dict[str, bool] = {}

        self.conversion: ConversionUtils = ConversionUtils()
        self.ep_config_deploy: EpOneManageFabricConfigDeploy = EpOneManageFabricConfigDeploy()

        self._rest_send: RestSend = RestSend({})
        self._results: Results = Results()

        self.fabric_can_be_deployed = False
        self._fabric_details: FabricDetailsByName = FabricDetailsByName()
        self._fabric_name: str = ""
        self._fabric_summary: FabricSummary = FabricSummary()
        self._payload: dict = {}

        msg = "ENTERED FabricConfigDeploy():"
        self.log.debug(msg)

    def _can_fabric_be_deployed(self) -> None:
        """
        ### Summary
        -   Set self.fabric_can_be_deployed to True if the fabric configuration
            can be deployed.
        -   Set self.fabric_can_be_deployed to False otherwise.
        """
        method_name = inspect.stack()[0][3]

        self.fabric_can_be_deployed = False

        deploy = self.payload.get("DEPLOY", None)
        if deploy is False or deploy is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Fabric {self.fabric_name} DEPLOY is False or None. "
            msg += "Skipping config-deploy."
            self.log.debug(msg)
            self.cannot_deploy_fabric_reason = msg
            self.fabric_can_be_deployed = False
            self.config_deploy_failed = False
            return

        try:
            self.fabric_summary.fabric_name = self.fabric_name
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Fabric {self.fabric_name} is invalid. "
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
            self.log.debug(msg)
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
            self.fabric_details.results = Results()
            self.fabric_details.refresh()
        except ValueError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Error during FabricDetailsByName().refresh(). "
            msg += f"Error detail: {error}"
            self.log.debug(msg)
            self.cannot_deploy_fabric_reason = msg
            self.fabric_can_be_deployed = False
            self.config_deploy_failed = True
            return

        self.fabric_details.filter = self.fabric_name

        if self.fabric_details.deployment_freeze is True:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Fabric {self.fabric_name} DEPLOYMENT_FREEZE == True. "
            msg += "Cannot deploy a fabric with deployment freeze enabled."
            self.log.debug(msg)
            self.cannot_deploy_fabric_reason = msg
            self.fabric_can_be_deployed = False
            self.config_deploy_failed = False
            return

        if self.fabric_details.is_read_only is True:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Fabric {self.fabric_name} IS_READ_ONLY == True. "
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
        # pylint: disable=no-member
        method_name = inspect.stack()[0][3]

        if not self.fabric_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.fabric_name must be set "
            msg += "before calling commit."
            raise ValueError(msg)
        if not self.fabric_details.data:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.fabric_details must be set "
            msg += "before calling commit."
            raise ValueError(msg)
        if not self.payload:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.payload must be set "
            msg += "before calling commit."
            raise ValueError(msg)
        if not self.fabric_summary.refreshed:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.fabric_summary must be set and refreshed "
            msg += "before calling commit."
            raise ValueError(msg)
        if not self.rest_send.params:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.rest_send.params must be set "
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
            self.results.check_mode = self.rest_send.check_mode
            self.results.state = self.rest_send.state
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
            self.rest_send.path = self.ep_config_deploy.path
            self.rest_send.verb = self.ep_config_deploy.verb
            self.rest_send.payload = None
            self.rest_send.commit()
        except ValueError as error:
            raise ValueError(error) from error

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
        self.results.check_mode = self.rest_send.check_mode
        self.results.state = self.rest_send.state
        self.results.response_current = copy.deepcopy(self.rest_send.response_current)
        self.results.result_current = copy.deepcopy(self.rest_send.result_current)
        self.results.register_task_result()

    @property
    def fabric_name(self) -> str:
        """
        The name of the fabric to config-save.
        """
        return self._fabric_name

    @fabric_name.setter
    def fabric_name(self, value: str) -> None:
        try:
            self.conversion.validate_fabric_name(value)
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error
        self._fabric_name = value

    @property
    def fabric_details(self) -> FabricDetailsByName:
        """
        -   getter: Return an instance of the FabricDetailsByName class.
        -   setter: Set an instance of the FabricDetailsByName class.
        -   setter: Raise ``TypeError`` if the value is not an
            instance of FabricDetailsByName.
        """
        return self._fabric_details

    @fabric_details.setter
    def fabric_details(self, value: FabricDetailsByName) -> None:
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
        self._fabric_details = value

    @property
    def fabric_summary(self) -> FabricSummary:
        """
        -   getter: Return an instance of the FabricSummary class.
        -   setter: Set an instance of the FabricSummary class.
        -   setter: Raise ``TypeError`` if the value is not an
            instance of FabricSummary.
        """
        return self._fabric_summary

    @fabric_summary.setter
    def fabric_summary(self, value: FabricSummary) -> None:
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
        self._fabric_summary = value

    @property
    def payload(self) -> dict:
        """
        -   The fabric payload used to create/merge/replace the fabric.
        -   Raise ``ValueError`` if the value is not a dictionary.
        -   Raise ``ValueError`` the payload is missing FABRIC_NAME key.
        """
        return self._payload

    @payload.setter
    def payload(self, value: dict) -> None:
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
        self._payload = value

    @property
    def rest_send(self) -> RestSend:
        """
        An instance of the RestSend class.
        """
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        if not value.params:
            msg = f"{self.class_name}.rest_send.params must be set."
            raise ValueError(msg)
        self._rest_send = value

    @property
    def results(self) -> Results:
        """
        An instance of the Results class.
        """
        return self._results

    @results.setter
    def results(self, value: Results) -> None:
        self._results = value
