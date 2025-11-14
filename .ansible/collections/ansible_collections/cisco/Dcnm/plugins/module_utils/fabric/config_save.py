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

from ..common.api.v1.lan_fabric.rest.control.fabrics.fabrics import \
    EpFabricConfigSave
from ..common.conversion import ConversionUtils
from ..common.properties import Properties


@Properties.add_rest_send
@Properties.add_results
class FabricConfigSave:
    """
    # Initiate a fabric config-save operation on the controller.

    -   Raise ``ValueError`` for any caller errors, e.g. required properties
        not being set before calling FabricConfigSave().commit().
    -   Update FabricConfigSave().results to reflect success/failure of
        the operation on the controller.

    ## Usage:

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

    config_save = FabricConfigSave()
    config_save.rest_send = rest_send
    config_deploy.payload = payload # a valid payload dictionary
    config_save.results = results
    try:
        config_save.commit()
    except ValueError as error:
        raise ValueError(error) from error
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.action = "config_save"
        self.cannot_save_fabric_reason = ""
        self.config_save_failed = False
        self.fabric_can_be_saved = False

        self.config_save_result: dict[str, bool] = {}

        self.conversion = ConversionUtils()
        self.ep_config_save = EpFabricConfigSave()
        self._fabric_name = None
        self._payload = None
        self._rest_send = None
        self._results = None

        msg = "ENTERED FabricConfigSave()"
        self.log.debug(msg)

    def _can_fabric_be_saved(self) -> None:
        """
        -   Set self.fabric_can_be_saved to True if the fabric configuration
            can be saved.
        -   Set self.fabric_can_be_saved to False otherwise.
        """
        self.fabric_can_be_saved = False

        deploy = self.payload.get("DEPLOY", None)
        if deploy is False or deploy is None:
            msg = f"Fabric {self.fabric_name} DEPLOY is False or None. "
            msg += "Skipping config-save."
            self.log.debug(msg)
            self.cannot_save_fabric_reason = msg
            self.config_save_failed = False
            self.fabric_can_be_saved = False
            return
        self.fabric_can_be_saved = True

    def commit(self):
        """
        -   Save the fabric configuration to the controller.
        -   Raise ``ValueError`` if the endpoint assignment fails.
        """
        method_name = inspect.stack()[0][3]
        # pylint: disable=no-member

        if self.payload is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"{self.class_name}.payload must be set "
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

        self._can_fabric_be_saved()

        if self.fabric_can_be_saved is False:
            self.results.diff_current = {}
            self.results.action = self.action
            self.results.check_mode = self.rest_send.check_mode
            self.results.state = self.rest_send.state
            self.results.response_current = {
                "RETURN_CODE": 200,
                "MESSAGE": self.cannot_save_fabric_reason,
            }
            if self.config_save_failed is True:
                self.results.result_current = {"changed": False, "success": False}
            else:
                self.results.result_current = {"changed": True, "success": True}
            self.results.register_task_result()
            return

        try:
            self.ep_config_save.fabric_name = self.fabric_name
            self.rest_send.path = self.ep_config_save.path
            self.rest_send.verb = self.ep_config_save.verb
            self.rest_send.payload = None
            self.rest_send.commit()
        except ValueError as error:
            raise ValueError(error) from error

        result = self.rest_send.result_current["success"]
        self.config_save_result[self.fabric_name] = result
        if self.config_save_result[self.fabric_name] is False:
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
    def fabric_name(self):
        """
        The name of the fabric to config-save.
        """
        return self._fabric_name

    @fabric_name.setter
    def fabric_name(self, value):
        try:
            self.conversion.validate_fabric_name(value)
        except (TypeError, ValueError) as error:
            raise ValueError(error) from error
        self._fabric_name = value

    @property
    def payload(self):
        """
        -   The fabric payload used to create/merge/replace the fabric.
        -   Raise ``ValueError`` if the value is not a dictionary.
        -   Raise ``ValueError`` the payload is missing FABRIC_NAME key.
        """
        return self._payload

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
        self._payload = value
