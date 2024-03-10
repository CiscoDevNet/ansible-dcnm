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
import json
import logging
import re


class ApiEndpoints:
    """
    Endpoints for fabric API calls

    Usage

    endpoints = ApiEndpoints()
    endpoints.fabric_name = "MyFabric"
    endpoints.template_name = "MyTemplate"
    try:
        endpoint = endpoints.fabric_create
    except ValueError as error:
        self.ansible_module.fail_json(error)

    rest_send = RestSend(self.ansible_module)
    rest_send.path = endpoint.get("path")
    rest_send.verb = endpoint.get("verb")
    rest_send.commit()
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED ApiEndpoints()")

        self.endpoint_api_v1 = "/appcenter/cisco/ndfc/api/v1"

        self.endpoint_fabrics = f"{self.endpoint_api_v1}"
        self.endpoint_fabrics += "/rest/control/fabrics"

        self.endpoint_fabric_summary = f"{self.endpoint_api_v1}"
        self.endpoint_fabric_summary += "/lan-fabric/rest/control/switches"
        self.endpoint_fabric_summary += "/_REPLACE_WITH_FABRIC_NAME_/overview"

        self.endpoint_templates = f"{self.endpoint_api_v1}"
        self.endpoint_templates += "/configtemplate/rest/config/templates"

        self._build_properties()

    def _build_properties(self):
        self.properties = {}
        self.properties["fabric_name"] = None
        self.properties["template_name"] = None

    @property
    def fabric_create(self):
        """
        return fabric_create endpoint
        verb: POST
        path: /rest/control/fabrics
        """
        method_name = inspect.stack()[0][3]
        if not self.fabric_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_name is required."
            raise ValueError(msg)
        if not self.template_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "template_name is required."
            raise ValueError(msg)
        path = self.endpoint_fabrics
        path += f"/{self.fabric_name}/{self.template_name}"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "POST"
        self.log.debug(
            f"Returning endpoint: {json.dumps(endpoint, indent=4, sort_keys=True)}"
        )
        return endpoint

    @property
    def fabric_delete(self):
        """
        return fabric_delete endpoint
        verb: DELETE
        path: /rest/control/fabrics
        """
        method_name = inspect.stack()[0][3]
        if not self.fabric_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_name is required."
            raise ValueError(msg)
        path = self.endpoint_fabrics
        path += f"/{self.fabric_name}"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "DELETE"
        self.log.debug(
            f"Returning endpoint: {json.dumps(endpoint, indent=4, sort_keys=True)}"
        )
        return endpoint

    @property
    def fabric_summary(self):
        """
        return fabric_summary endpoint
        verb: GET
        path: /rest/control/fabrics/summary
        """
        method_name = inspect.stack()[0][3]
        if not self.fabric_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_name is required."
            raise ValueError(msg)
        endpoint = {}
        path = copy.copy(self.endpoint_fabric_summary)
        endpoint["path"] = re.sub("_REPLACE_WITH_FABRIC_NAME_", self.fabric_name, path)
        endpoint["verb"] = "GET"
        self.log.debug(
            f"Returning endpoint: {json.dumps(endpoint, indent=4, sort_keys=True)}"
        )
        return endpoint

    @property
    def fabrics(self):
        """
        return fabrics endpoint
        verb: GET
        path: /rest/control/fabrics
        """
        method_name = inspect.stack()[0][3]
        endpoint = {}
        endpoint["path"] = self.endpoint_fabrics
        endpoint["verb"] = "GET"
        self.log.debug(
            f"Returning endpoint: {json.dumps(endpoint, indent=4, sort_keys=True)}"
        )
        return endpoint

    @property
    def fabric_info(self):
        """
        return fabric_info endpoint
        verb: GET
        path: /rest/control/fabrics/{fabricName}

        Usage:
        endpoints = ApiEndpoints()
        endpoints.fabric_name = "MyFabric"
        try:
            endpoint = endpoints.fabric_info
        except ValueError as error:
            self.ansible_module.fail_json(error)
        """
        method_name = inspect.stack()[0][3]
        if not self.fabric_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_name is required."
            raise ValueError(msg)
        path = self.endpoint_fabrics
        path += f"/{self.fabric_name}"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        self.log.debug(
            f"Returning endpoint: {json.dumps(endpoint, indent=4, sort_keys=True)}"
        )
        return endpoint

    @property
    def fabric_name(self):
        """
        setter: set the fabric_name to include in endpoint paths
        getter: get the current value of fabric_name
        """
        return self.properties["fabric_name"]

    @fabric_name.setter
    def fabric_name(self, value):
        self.properties["fabric_name"] = value

    @property
    def template_name(self):
        """
        setter: set the fabric template_name to include in endpoint paths
        getter: get the current value of template_name
        """
        return self.properties["template_name"]

    @template_name.setter
    def template_name(self, value):
        self.properties["template_name"] = value

    @property
    def template(self):
        """
        return the template content endpoint for template_name
        verb: GET
        path: /appcenter/cisco/ndfc/api/v1/configtemplate/rest/config/templates/{template_name}
        """
        method_name = inspect.stack()[0][3]
        if not self.template_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "template_name is required."
            raise ValueError(msg)
        path = self.endpoint_templates
        path += f"/{self.template_name}"
        endpoint = {}
        endpoint["path"] = path
        endpoint["verb"] = "GET"
        self.log.debug(
            f"Returning endpoint: {json.dumps(endpoint, indent=4, sort_keys=True)}"
        )
        return endpoint

    @property
    def templates(self):
        """
        return the template contents endpoint
        
        This endpoint returns the all template names on the controller.

        verb: GET
        path: /appcenter/cisco/ndfc/api/v1/configtemplate/rest/config/templates
        """
        method_name = inspect.stack()[0][3]
        endpoint = {}
        endpoint["path"] = self.endpoint_templates
        endpoint["verb"] = "GET"
        self.log.debug(
            f"Returning endpoint: {json.dumps(endpoint, indent=4, sort_keys=True)}"
        )
        return endpoint
