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
Retrieve from the controller a template's parameter list.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import logging
from typing import Any

from .api.v1.configtemplate.rest.config.templates.templates import EpTemplate
from .exceptions import ControllerResponseError
from .rest_send_v2 import RestSend
from .results_v2 import Results


class TemplateGet:
    """
    # Summary

    Retrieve from the controller a template's parameter list.

    ## Usage

    ```python
    instance = TemplateGet()
    instance.rest_send = rest_send_instance
    instance.template_name = "Easy_Fabric"
    instance.refresh()
    template = instance.template
    template_name = instance.template_name
    ```

    `instance.template` will be a dict with the following top-level keys:

    -   "template_name": The name of the template.
    -   "parameters": A list of parameters for template_name.

    ## Example instance.template

    ```json
    {
        "template_name": "Easy_Fabric",
        "parameters": [
            {
                "annotations": {
                    "Description": "Please provide the fabric name to create it (Max Size 64)",
                    "DisplayName": "Fabric Name",
                    "IsFabricName": "true",
                    "IsMandatory": "true"
                },
                "defaultValue": null,
                "description": null,
                "metaProperties": {
                    "maxLength": "64",
                    "minLength": "1"
                },
                "name": "FABRIC_NAME",
                "optional": false,
                "parameterType": "string",
                "parameterTypeStructure": false,
                "structureParameters": {}
            },
            ...
        ]
    }
    ```
    """

    def __init__(self) -> None:
        self.class_name: str = self.__class__.__name__

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED TemplateGet(): "
        self.log.debug(msg)

        self.ep_template: EpTemplate = EpTemplate()

        self.response: list[dict[str, Any]] = []
        self.response_current: dict[str, Any] = {}
        self.result: list[dict[str, Any]] = []
        self.result_current: dict[str, Any] = {}

        self._rest_send: RestSend = RestSend({})
        self._results: Results = Results()
        self._template: dict[str, Any] = {}
        self._template_name: str = ""

    def _set_template_endpoint(self) -> None:
        """
        # Summary

        -   Set the endpoint for the template to be retrieved from the controller.

        ## Raises

        -   `ValueError` if the endpoint assignment fails.
        """
        method_name: str = inspect.stack()[0][3]
        if not self.template_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Set instance.template_name property before calling instance.refresh()"
            self.log.error(msg)
            raise ValueError(msg)

        try:
            self.ep_template.template_name = self.template_name
        except TypeError as error:
            raise ValueError(error) from error

    def refresh(self) -> None:
        """
        # Summary

        -   Retrieve the template from the controller.
        -   Populate the instance.template property.

        # Raises

        -   `ValueError` if the template endpoint assignment fails
        -   `ControllerResponseError` if the controller `RETURN_CODE` != 200
        """
        method_name: str = inspect.stack()[0][3]

        try:
            self._set_template_endpoint()
        except ValueError as error:
            raise ValueError(error) from error

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Set instance.rest_send property before calling instance.refresh()"
            self.log.debug(msg)
            raise ValueError(msg)

        self.rest_send.path = self.ep_template.path
        self.rest_send.verb = self.ep_template.verb
        self.rest_send.check_mode = False
        self.rest_send.timeout = 2
        self.rest_send.commit()

        self.response_current = copy.deepcopy(self.rest_send.response_current)
        self.response.append(copy.deepcopy(self.rest_send.response_current))
        self.result_current = copy.deepcopy(self.rest_send.result_current)
        self.result.append(copy.deepcopy(self.rest_send.result_current))

        controller_return_code = self.response_current.get("RETURN_CODE", None)
        controller_message = self.response_current.get("MESSAGE", None)
        if controller_return_code != 200:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Failed to retrieve template {self.template_name}. "
            msg += f"RETURN_CODE: {controller_return_code}. "
            msg += f"MESSAGE: {controller_message}."
            self.log.error(msg)
            raise ControllerResponseError(msg)

        self.template = {}
        self.template["template_name"] = self.response_current.get("DATA", {}).get("name", "")
        self.template["parameters"] = self.response_current.get("DATA", {}).get("parameters", [])

    @property
    def rest_send(self) -> RestSend:
        """
        # Summary

        An instance of the RestSend class.

        ## Raises

        -   setter: `ValueError` if RestSend.params is not set.
        """
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        method_name: str = inspect.stack()[0][3]
        if not value.params:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must have params set."
            raise ValueError(msg)
        self._rest_send = value

    @property
    def results(self) -> Results:
        """
        # Summary

        An instance of the Results class.
        """
        return self._results

    @results.setter
    def results(self, value: Results) -> None:
        self._results = value

    @property
    def template(self) -> dict[str, Any]:
        """
        # Summary

        -   getter: Return the template retrieved from the controller.
        -   setter: Set the template.
        -   The template must be a template retrieved from the controller.

        ## Raises

        -   setter: `TypeError` if the value is not a dict.
        """
        return self._template

    @template.setter
    def template(self, value) -> None:
        method_name: str = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "template must be an instance of dict."
            self.log.debug(msg)
            raise TypeError(msg)
        self._template = value

    @property
    def template_name(self) -> str:
        """
        # Summary

        -   getter: Return the template name of the template to be retrieved
            from the controller.
        -   setter: Set the template name of the template to be retrieved
            from the controller.
        -   setter: Raise ``TypeError`` if the value is not a str.

        ## Raises

        -   `TypeError` if the value passed to the setter is not an instance of str.
        """
        return self._template_name

    @template_name.setter
    def template_name(self, value: str) -> None:
        method_name: str = inspect.stack()[0][3]
        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += "template_name must be an instance of str. "
            msg += f"Got type: {type(value)} for value: {value}."
            self.log.debug(msg)
            raise TypeError(msg)
        self._template_name = value
