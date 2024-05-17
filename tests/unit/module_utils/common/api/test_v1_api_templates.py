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


import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.configtemplate.rest.config.templates.templates import (
    EpTemplate, EpTemplates)
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    does_not_raise

PATH_PREFIX = "/appcenter/cisco/ndfc/api/v1/configtemplate/rest/config/templates"
TEMPLATE_NAME = "Easy_Fabric"


def test_ep_templates_00010():
    """
    ### Class
    -   EpTemplate

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpTemplate()
        instance.template_name = TEMPLATE_NAME
    assert f"{PATH_PREFIX}/{TEMPLATE_NAME}" in instance.path
    assert instance.verb == "GET"


def test_ep_templates_00040():
    """
    ### Class
    -   EpTemplate

    ### Summary
    -   Verify ``ValueError`` is raised if path is accessed
        before setting ``template_name``.

    """
    with does_not_raise():
        instance = EpTemplate()
    match = r"EpTemplate.path_template_name:\s+"
    match += r"template_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_templates_00050():
    """
    ### Class
    -   EpFabricConfigDeploy

    ### Summary
    -   Verify ``ValueError`` is raised if ``template_name``
        is invalid.
    """
    template_name = "Invalid_Template_Name"
    with does_not_raise():
        instance = EpTemplate()
    match = r"EpTemplate.template_name:\s+"
    match += r"Invalid template_name: Invalid_Template_Name.\s+"
    match += r"Expected one of:\s+"
    with pytest.raises(ValueError, match=match):
        instance.template_name = template_name  # pylint: disable=pointless-statement


def test_ep_templates_00100():
    """
    ### Class
    -   EpTemplates

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpTemplates()
    assert instance.path == PATH_PREFIX
    assert instance.verb == "GET"
