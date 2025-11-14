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
# pylint: disable=line-too-long
from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Allen Robel"

import inspect
import logging

from ..config import Config


class Templates(Config):
    """
    ## api.v1.configtemplate.rest.config.templates.Templates()

    ### Description
    Common methods and properties for Templates() subclasses.

    ### Path
    -   ``/api/v1/configtemplate/rest/config/templates``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.templates = f"{self.config}/templates"
        self._template_name = None
        msg = "ENTERED api.v1.configtemplate.rest.config."
        msg += f"templates.{self.class_name}"
        self.log.debug(msg)

    @property
    def path_template_name(self):
        """
        - Endpoint for template retrieval.
        - Raise ``ValueError`` if template_name is not set.
        """
        method_name = inspect.stack()[0][3]
        if self.template_name is None and "template_name" in self.required_properties:
            msg = f"{self.class_name}.{method_name}: "
            msg += "template_name must be set prior to accessing path."
            raise ValueError(msg)
        return f"{self.templates}/{self.template_name}"

    @property
    def template_name(self):
        """
        - getter: Return the template_name.
        - setter: Set the template_name.
        - setter: Raise ``ValueError`` if template_name is not a string.
        """
        return self._template_name

    @template_name.setter
    def template_name(self, value):
        self._template_name = value


class EpTemplate(Templates):
    """
    ## V1 API - Templates().EpTemplate()

    ### Description
    Return endpoint information.

    ### Raises
    -   ``ValueError``: If template_name is not set.
    -   ``ValueError``: If template_name is not a valid fabric template name.

    ### Path
    -   ``/api/v1/configtemplates/rest/config/templates/{template_name}``

    ### Verb
    -   GET

    ### Parameters
    - template_name: string
        - set the ``template_name`` to be used in the path
        - required
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpTemplate()
    instance.template_name = "Easy_Fabric"
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.required_properties.add("template_name")
        msg = "ENTERED api.v1.configtemplate.rest.config."
        msg += f"templates.Templates.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        """
        - Endpoint for template retrieval.
        - Raise ``ValueError`` if template_name is not set.
        """
        return self.path_template_name

    @property
    def verb(self):
        """
        - Return the verb for the endpoint.
        """
        return "GET"


class EpTemplates(Templates):
    """
    ## V1 API - Templates().EpTemplates()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/api/v1/configtemplates/rest/config/templates``

    ### Verb
    -   GET

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpTemplates()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self._build_properties()
        msg = "ENTERED api.v1.configtemplate.rest.config."
        msg += f"templates.Templates.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        """
        - Return the path for the endpoint.
        """
        return self.templates

    @property
    def verb(self):
        """
        - Return the verb for the endpoint.
        """
        return "GET"
