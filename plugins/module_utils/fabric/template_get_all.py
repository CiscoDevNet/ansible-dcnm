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
    EpTemplates
from ..common.exceptions import ControllerResponseError
from ..common.properties import Properties


@Properties.add_rest_send
@Properties.add_results
class TemplateGetAll:
    """
    Retrieve a list of all templates from the controller.

    Usage:

    ```python
    instance = TemplateGetAll()
    instance.rest_send = RestSend(ansible_module)
    instance.refresh()
    templates = instance.templates
    ```

    TODO: We are not using the `results` property in this class. We should
    remove it or decide whether we want to record the results in the main
    task result.  If we do decide to remove it, we also need to remove the
    unit test that checks for it.
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        msg = "ENTERED TemplateGetAll(): "
        self.log.debug(msg)

        self.ep_templates = EpTemplates()

        self.response = []
        self.response_current = {}
        self.result = []
        self.result_current = {}

        self._rest_send = None
        self._results = None

        self._templates = None

    def refresh(self):
        """
        - Retrieve the templates from the controller.
        - raise ``ValueError`` if the endpoint assignment fails
        - raise ``ValueError`` if self.rest_send is not set.
        - raise ``ControllerResponseError`` if RETURN_CODE != 200.
        """
        # pylint: disable=no-member
        method_name = inspect.stack()[0][3]

        if self.rest_send is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Set instance.rest_send property before "
            msg += "calling instance.refresh()"
            self.log.debug(msg)
            raise ValueError(msg)

        self.rest_send.path = self.ep_templates.path
        self.rest_send.verb = self.ep_templates.verb
        self.rest_send.check_mode = False
        self.rest_send.commit()

        self.response_current = copy.deepcopy(self.rest_send.response_current)
        self.response.append(copy.deepcopy(self.rest_send.response_current))
        self.result_current = copy.deepcopy(self.rest_send.result_current)
        self.result.append(copy.deepcopy(self.rest_send.result_current))

        controller_return_code = self.response_current.get("RETURN_CODE", None)
        controller_message = self.response_current.get("MESSAGE", None)
        if controller_return_code != 200:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Failed to retrieve templates. "
            msg += f"RETURN_CODE: {controller_return_code}. "
            msg += f"MESSAGE: {controller_message}."
            self.log.error(msg)
            raise ControllerResponseError(msg)

        template_list = self.response_current.get("DATA", None)
        templates = {}
        for template in template_list:
            template_name = template.get("name", None)
            templates[template_name] = template
        self.templates = copy.deepcopy(templates)

    @property
    def templates(self) -> dict:
        """
        Return the templates retrieved from the controller.
        """
        return self._templates

    @templates.setter
    def templates(self, value) -> None:
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "templates must be an instance of dict."
            self.log.debug(msg)
            raise TypeError(msg)
        self._templates = value
