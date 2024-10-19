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

import copy
import inspect
import logging

from ..common.api.v1.configtemplate.rest.config.templates.templates import \
    EpTemplate
from ..common.exceptions import ControllerResponseError
from ..common.properties import Properties


@Properties.add_rest_send
@Properties.add_results
class TemplateGet:
    """
    -   Retrieve a template from the controller.

    -   Usage

    ```python
    instance = TemplateGet()
    instance.rest_send = rest_send_instance
    instance.template_name = "Easy_Fabric"
    instance.refresh()
    template = instance.template
    ```

    TODO: We are not using the `results` property in this class. We should
    remove it or decide whether we want to record the results in the main
    task result.  If we do decide to remove it, we also need to remove the
    unit test that checks for it.
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED TemplateGet(): "
        self.log.debug(msg)

        self.ep_template = EpTemplate()

        self.response = []
        self.response_current = {}
        self.result = []
        self.result_current = {}

        self._rest_send = None
        self._results = None
        self._template = None
        self._template_name = None

    def _set_template_endpoint(self) -> None:
        """
        -   Set the endpoint for the template to be retrieved from
            the controller.
        -   Raise ``ValueError`` if the endpoint assignment fails.
        """
        method_name = inspect.stack()[0][3]
        if self.template_name is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Set instance.template_name property before "
            msg += "calling instance.refresh()"
            self.log.error(msg)
            raise ValueError(msg)

        try:
            self.ep_template.template_name = self.template_name
        except TypeError as error:
            raise ValueError(error) from error

    def refresh(self):
        """
        -   Retrieve the template from the controller.
        -   raise ``ValueError`` if the template endpoint assignment fails
        -   raise ``ControllerResponseError`` if the controller
            ``RETURN_CODE`` != 200
        """
        # pylint: disable=no-member
        method_name = inspect.stack()[0][3]

        try:
            self._set_template_endpoint()
        except ValueError as error:
            raise ValueError(error) from error

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Set instance.rest_send property before "
            msg += "calling instance.refresh()"
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
        self.template["parameters"] = self.response_current.get("DATA", {}).get(
            "parameters", []
        )

    @property
    def template(self):
        """
        -   getter: Return the template retrieved from the controller.
        -   setter: Set the template.
        -   The template must be a template retrieved from the controller.
        -   setter: Raise ``TypeError`` if the value is not a dict.
        """
        return self._template

    @template.setter
    def template(self, value) -> None:
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "template must be an instance of dict."
            self.log.debug(msg)
            raise TypeError(msg)
        self._template = value

    @property
    def template_name(self) -> str:
        """
        -   getter: Return the template name of the template to be retrieved
            from the controller.
        -   setter: Set the template name of the template to be retrieved
            from the controller.
        -   setter: Raise ``TypeError`` if the value is not a str.
        """
        return self._template_name

    @template_name.setter
    def template_name(self, value: str) -> None:
        method_name = inspect.stack()[0][3]
        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += "template_name must be an instance of str. "
            msg += f"Got type: {type(value)} for value: {value}."
            self.log.debug(msg)
            raise TypeError(msg)
        self._template_name = value
