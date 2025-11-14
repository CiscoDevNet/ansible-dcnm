#
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
Update fabric groups in bulk for replaced state
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import copy
import inspect
import logging
from typing import Any

from ..common.exceptions import ControllerResponseError
from ..common.operation_type import OperationType
from ..common.rest_send_v2 import RestSend
from ..common.results_v2 import Results
from ..common.ruleset_v2 import RuleSet
from ..common.template_get_v2 import TemplateGet
from ..fabric.param_info_v2 import ParamInfo


class FabricGroupDefault:
    """
    # Summary

    Build a payload for a default fabric group configuration from a template
    retrieved from the controller.

    ## Raises

    -   `ValueError` if:
        -   `fabric_group_name` is not set.
        -   `rest_send` is not set.
        -   `results` is not set.
        -   Unable to retrieve template from controller.

    ## Usage

    ```python
    from ansible_collections.cisco.dcnm.plugins.module_utils.fabric_group.fabric_group_default import FabricGroupDefault

    instance = FabricGroupDefault()
    instance.fabric_group_name = "my_fabric_group"
    instance.rest_send = rest_send  # An instance of RestSend with params set
    instance.results = Results()  # Optional: An instance of Results
    instance.commit()
    payload_with_default_fabric_group_config = instance.config
    ```

    """

    def __init__(self) -> None:
        method_name = inspect.stack()[0][3]
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.action = "fabric_group_default"
        self.operation_type: OperationType = OperationType.QUERY

        self._fabric_group_default_config: dict[str, Any] = {}
        self._fabric_group_name: str = ""
        self._config_nv_pairs: dict[str, Any] = {}
        self._config_top_level: dict[str, Any] = {}
        self._parameter_names: list[str] = []
        self._param_info: ParamInfo = ParamInfo()
        self._rule_set: RuleSet = RuleSet()
        self._rest_send: RestSend = RestSend({})
        self._results: Results = Results()
        self._results.action = self.action
        self._results.operation_type = self.operation_type
        self._template: dict[str, Any] = {}
        self._template_get: TemplateGet = TemplateGet()
        self._template_name: str = "MSD_Fabric"

        msg = f"{self.class_name}.{method_name}: DONE"
        self.log.debug(msg)

    def commit(self) -> None:
        """
        # Summary

        Build the default fabric group configuration from the provided template.

        ## Raises

        -   `ValueError` if:
            -   `fabric_group_name` is not set.
            -   `rest_send` is not set.
        """
        method_name = inspect.stack()[0][3]
        msg: str = ""
        if not self.fabric_group_name:
            msg = f"{self.class_name}.{method_name}: "
            msg += "fabric_group_name must be set."
            raise ValueError(msg)

        if not self.rest_send.params:
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set to an instance of RestSend with params set."
            raise ValueError(msg)

        self._build_fabric_group_default_config()

    def _get_template(self) -> None:
        """
        # Summary

        Retrieve the template from the controller.

        ## Raises

        -   `ValueError` if unable to retrieve template from controller.
        """
        method_name = inspect.stack()[0][3]
        msg: str = f"{self.class_name}.{method_name}: "
        msg += f"Retrieving template: {self._template_name} from controller."
        self.log.debug(msg)

        self._template_get.rest_send = self.rest_send
        self._template_get.results = Results()
        self._template_get.template_name = self._template_name
        try:
            self._template_get.refresh()
        except ControllerResponseError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Failed to retrieve template: {error}"
            self.log.error(msg)
            raise ValueError(msg) from error
        self._template = self._template_get.template

    def _set_parameter_names(self) -> None:
        """
        # Summary

        Build a list of parameter names from the template.

        ## Raises

        None
        """
        self._parameter_names = [param["name"] for param in self._template.get("parameters", [])]

    def _parse_parameter_info(self) -> None:
        """
        Parse param info from the template.
        """
        self._param_info.template = copy.deepcopy(self._template)
        self._param_info.refresh()

    def _skip(self, param_name: str) -> bool:
        """
        # Summary

        Determine if a parameter should be skipped.

        ## Raises

        None
        """
        if "_PREV" in param_name:
            return True
        if "DCNM_ID" in param_name:
            return True
        return False

    def _build_config_top_level(self) -> None:
        """
        # Summary

        Build the top-level fabric group default config.

        ## Raises

        None
        """
        self._config_top_level["fabricName"] = self.fabric_group_name
        self._config_top_level["fabricTechnology"] = "VXLANFabric"
        self._config_top_level["fabricType"] = "MSD"
        self._config_top_level["templateName"] = self._template_name

    def _build_nv_pairs(self) -> None:
        """
        # Summary

        Build nvPairs for the fabric group default config.

        ## Raises

        None
        """
        method_name = inspect.stack()[0][3]
        msg: str = f"{self.class_name}.{method_name}: "
        msg += "Building NV pairs for fabric group default config."
        self.log.debug(msg)
        _nv_pairs: dict[str, Any] = {}
        # for param_name in self._parameter_names:
        for param_name in self._param_info.parameter_names:
            if self._skip(param_name):
                continue
            self._param_info.parameter_name = param_name
            _nv_pairs[param_name] = self._param_info.parameter_default
        self._config_nv_pairs = _nv_pairs
        self._config_nv_pairs["FABRIC_NAME"] = self.fabric_group_name

    def _build_fabric_group_default_config(self) -> None:
        """
        # Summary

        Build the default fabric group configuration from the template.

        ## Raises

        None
        """
        self._get_template()
        self._parse_parameter_info()
        self._set_parameter_names()
        self._build_nv_pairs()
        self._build_config_top_level()
        self._fabric_group_default_config = copy.deepcopy(self._config_top_level)
        self._fabric_group_default_config["nvPairs"] = copy.deepcopy(self._config_nv_pairs)

    @property
    def config(self) -> dict[str, Any]:
        """
        The fabric group default config.
        """
        return self._fabric_group_default_config

    @property
    def fabric_group_name(self) -> str:
        """
        The name of the fabric group to build default config for.
        """
        return self._fabric_group_name

    @fabric_group_name.setter
    def fabric_group_name(self, value: str) -> None:
        self._fabric_group_name = value

    @property
    def rest_send(self) -> RestSend:
        """
        # Summary

        An instance of the RestSend class.

        ## Raises

        -   `ValueError` if `params` is not set on the RestSend instance.
        """
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value: RestSend) -> None:
        if not value.params:
            msg = f"{self.class_name}.rest_send must be set to an "
            msg += "instance of RestSend with params set."
            raise ValueError(msg)
        self._rest_send = value

    @property
    def results(self) -> Results:
        """
        # Summary

        An instance of the Results class.

        ## Raises

        -  `ValueError` if the value passed to the setter is not an instance of Results.
        """
        return self._results

    @results.setter
    def results(self, value: Results) -> None:
        if not isinstance(value, Results):
            msg = f"{self.class_name}.results must be set to an "
            msg += "instance of Results."
            raise ValueError(msg)
        self._results = value
        self._results.action = self.action
        self._results.add_changed(False)
        self._results.operation_type = self.operation_type
