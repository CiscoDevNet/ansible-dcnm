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

from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.configtemplate.rest.config.templates.templates import \
    EpTemplates
from ansible_collections.cisco.dcnm.plugins.module_utils.common.exceptions import \
    ControllerResponseError


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

        self._init_properties()

    def _init_properties(self) -> None:
        self._properties = {}
        self._properties["rest_send"] = None
        self._properties["results"] = None
        self._properties["templates"] = None

    def refresh(self):
        """
        - Retrieve the templates from the controller.
        - raise ``ValueError`` if the endpoint assignment fails
        - raise ``ValueError`` if self.rest_send is not set.
        - raise ``ControllerResponseError`` if RETURN_CODE != 200.
        """
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
        msg = f"{self.class_name}.{method_name}: "
        msg += "value must be an instance of RestSend. "
        msg += f"Got value {value} of type {type(value).__name__}."
        _class_name = None
        try:
            _class_name = value.class_name
        except AttributeError as error:
            msg += f" Error detail: {error}."
            self.log.debug(msg)
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

    @property
    def templates(self) -> dict:
        """
        Return the templates retrieved from the controller.
        """
        return self._properties["templates"]

    @templates.setter
    def templates(self, value) -> None:
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "templates must be an instance of dict."
            self.log.debug(msg)
            raise TypeError(msg)
        self._properties["templates"] = value
