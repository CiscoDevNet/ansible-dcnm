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

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# Also, fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-import
# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
# pylint: disable=unused-argument
# pylint: disable=invalid-name
# pylint: disable=pointless-statement

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect
import re

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.endpoints import \
    ApiEndpoints
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import \
    does_not_raise


def test_endpoints_00010() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
    - ApiEndpoints
        - __init__()

    Summary
    - Verify the class attributes are initialized to expected values.

    Test
    - Class attributes are initialized to expected values
    - ``ValueError`` is not called
    """
    with does_not_raise():
        instance = ApiEndpoints()
    assert instance.class_name == "ApiEndpoints"
    assert instance._re_valid_fabric_name == re.compile(r"[a-zA-Z]+[a-zA-Z0-9_-]*")
    assert instance.endpoint_api_v1 == "/appcenter/cisco/ndfc/api/v1"
    assert instance.endpoint_fabrics == (
        f"{instance.endpoint_api_v1}" + "/rest/control/fabrics"
    )
    assert instance.endpoint_fabric_summary == (
        f"{instance.endpoint_api_v1}"
        + "/lan-fabric/rest/control/switches"
        + "/_REPLACE_WITH_FABRIC_NAME_/overview"
    )
    assert instance.endpoint_templates == (
        f"{instance.endpoint_api_v1}" + "/configtemplate/rest/config/templates"
    )
    assert instance.properties["fabric_name"] is None
    assert instance.properties["template_name"] is None


MATCH_00020a = r"ApiEndpoints\.validate_fabric_name: "
MATCH_00020a = r"Invalid fabric name\. "
MATCH_00020a += r"Expected string\. Got.*\."

MATCH_00020b = r"ApiEndpoints\.validate_fabric_name: "
MATCH_00020b = r"Invalid fabric name:.*\. "
MATCH_00020b += "Fabric name must start with a letter A-Z or a-z and "
MATCH_00020b += r"contain only the characters in: \[A-Z,a-z,0-9,-,_\]\."


@pytest.mark.parametrize(
    "fabric_name, expected, does_raise",
    [
        ("MyFabric", does_not_raise(), False),
        ("My_Fabric", does_not_raise(), False),
        ("My-Fabric", does_not_raise(), False),
        ("M", does_not_raise(), False),
        (1, pytest.raises(TypeError, match=MATCH_00020a), True),
        ({}, pytest.raises(TypeError, match=MATCH_00020a), True),
        ([1, 2, 3], pytest.raises(TypeError, match=MATCH_00020a), True),
        ("1", pytest.raises(ValueError, match=MATCH_00020b), True),
        ("-MyFabric", pytest.raises(ValueError, match=MATCH_00020b), True),
        ("_MyFabric", pytest.raises(ValueError, match=MATCH_00020b), True),
        ("1MyFabric", pytest.raises(ValueError, match=MATCH_00020b), True),
        ("My Fabric", pytest.raises(ValueError, match=MATCH_00020b), True),
        ("My*Fabric", pytest.raises(ValueError, match=MATCH_00020b), True),
    ],
)
def test_endpoints_00020(fabric_name, expected, does_raise) -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_name.setter
        - validate_fabric_name()

    Summary
    - Verify ``TypeError`` is raised for non-string fabric_name.
    - Verify ``ValueError`` is raised for invalid string fabric_name.
    - Verify ``ValueError`` is not raised for valid fabric_name.
    """
    with does_not_raise():
        instance = ApiEndpoints()
    with expected:
        instance.fabric_name = fabric_name
    if does_raise is False:
        assert instance.fabric_name == fabric_name


def test_endpoints_00030() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_config_deploy getter

    Summary
    -   Verify fabric_config_deploy getter raises ``ValueError``
        if ``fabric_name`` is not set.
    """
    with does_not_raise():
        instance = ApiEndpoints()
    match = r"ApiEndpoints\.fabric_config_deploy: "
    match += r"fabric_name is required\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_config_deploy


def test_endpoints_00031() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_config_deploy getter

    Summary
    -   Verify fabric_config_deploy getter returns the expected
        endpoint when ``fabric_name`` is set.
    """
    fabric_name = "MyFabric"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.fabric_name = fabric_name
        endpoint = instance.fabric_config_deploy
    assert endpoint.get("verb", None) == "POST"
    assert endpoint.get("path", None) == (
        f"{instance.endpoint_fabrics}/{fabric_name}"
        + "/config-deploy?forceShowRun=false&inclAllMSDSwitches"
    )


def test_endpoints_00040() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_config_save getter

    Summary
    -   Verify fabric_config_save getter raises ``ValueError``
        if ``fabric_name`` is not set.
    """
    with does_not_raise():
        instance = ApiEndpoints()
    match = r"ApiEndpoints\.fabric_config_save: "
    match += r"fabric_name is required\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_config_save


def test_endpoints_00041() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_config_save getter

    Summary
    -   Verify fabric_config_save getter returns the expected
        endpoint when ``fabric_name`` is set.
    """
    fabric_name = "MyFabric"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.fabric_name = fabric_name
        endpoint = instance.fabric_config_save
    assert endpoint.get("verb", None) == "POST"
    assert endpoint.get("path", None) == (
        f"{instance.endpoint_fabrics}/{fabric_name}" + "/config-save"
    )


def test_endpoints_00050() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_create getter

    Summary
    -   Verify fabric_create getter raises ``ValueError``
        if ``fabric_name`` is not set.
    """
    template_name = "MyTemplate"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.template_name = template_name
    match = r"ApiEndpoints\.fabric_create: "
    match += r"fabric_name is required\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_create


def test_endpoints_00051() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_create getter

    Summary
    -   Verify fabric_create getter raises ``ValueError``
        if ``template_name`` is not set.
    """
    fabric_name = "MyFabric"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.fabric_name = fabric_name
    match = r"ApiEndpoints\.fabric_create: "
    match += r"template_name is required\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_create


def test_endpoints_00052() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_create getter

    Summary
    -   Verify fabric_create getter returns the expected
        endpoint when ``fabric_name`` and ``template_name``
        are set.
    """
    fabric_name = "MyFabric"
    template_name = "MyTemplate"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.fabric_name = fabric_name
        instance.template_name = template_name
        endpoint = instance.fabric_create
    assert endpoint.get("verb", None) == "POST"
    assert endpoint.get("path", None) == (
        f"{instance.endpoint_fabrics}/" + f"{fabric_name}/" + f"{template_name}"
    )


def test_endpoints_00060() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_delete getter

    Summary
    -   Verify fabric_delete getter raises ``ValueError``
        if ``fabric_name`` is not set.
    """
    fabric_name = "MyFabric"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.template_name = fabric_name
    match = r"ApiEndpoints\.fabric_delete: "
    match += r"fabric_name is required\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_delete


def test_endpoints_00061() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_delete getter

    Summary
    -   Verify fabric_delete getter returns the expected
        endpoint when ``fabric_name`` is set.
    """
    fabric_name = "MyFabric"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.fabric_name = fabric_name
        endpoint = instance.fabric_delete
    assert endpoint.get("verb", None) == "DELETE"
    assert endpoint.get("path", None) == (
        f"{instance.endpoint_fabrics}/" + f"{fabric_name}"
    )


def test_endpoints_00070() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_summary getter

    Summary
    -   Verify fabric_summary getter raises ``ValueError``
        if ``fabric_name`` is not set.
    """
    with does_not_raise():
        instance = ApiEndpoints()
    match = r"ApiEndpoints\.fabric_summary: "
    match += r"fabric_name is required\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_summary


def test_endpoints_00071() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_summary getter

    Summary
    -   Verify fabric_summary getter returns the expected
        endpoint when ``fabric_name`` is set.
    """
    fabric_name = "MyFabric"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.fabric_name = fabric_name
        endpoint = instance.fabric_summary
    assert endpoint.get("verb", None) == "GET"
    assert endpoint.get("path", None) == (
        f"{instance.endpoint_api_v1}/"
        + "lan-fabric/rest/control/switches/"
        + f"{fabric_name}/overview"
    )


def test_endpoints_00080() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_update getter

    Summary
    -   Verify fabric_update getter raises ``ValueError``
        if ``fabric_name`` is not set.
    """
    template_name = "MyTemplate"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.template_name = template_name
    match = r"ApiEndpoints\.fabric_update: "
    match += r"fabric_name is required\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_update


def test_endpoints_00081() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_update getter

    Summary
    -   Verify fabric_update getter raises ``ValueError``
        if ``template_name`` is not set.
    """
    fabric_name = "MyFabric"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.fabric_name = fabric_name
    match = r"ApiEndpoints\.fabric_update: "
    match += r"template_name is required\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_update


def test_endpoints_00082() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_update getter

    Summary
    -   Verify fabric_update getter returns the expected
        endpoint when ``fabric_name`` and ``template_name``
        are set.
    """
    fabric_name = "MyFabric"
    template_name = "MyTemplate"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.fabric_name = fabric_name
        instance.template_name = template_name
        endpoint = instance.fabric_update
    assert endpoint.get("verb", None) == "PUT"
    assert endpoint.get("path", None) == (
        f"{instance.endpoint_fabrics}/" + f"{fabric_name}/" + f"{template_name}"
    )


def test_endpoints_00090() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_info getter

    Summary
    -   Verify fabric_info getter raises ``ValueError``
        if ``fabric_name`` is not set.
    """
    with does_not_raise():
        instance = ApiEndpoints()
    match = r"ApiEndpoints\.fabric_info: "
    match += r"fabric_name is required\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_info


def test_endpoints_00091() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - fabric_info getter

    Summary
    -   Verify fabric_info getter returns the expected
        endpoint when ``fabric_name`` is set.
    """
    fabric_name = "MyFabric"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.fabric_name = fabric_name
        endpoint = instance.fabric_info
    assert endpoint.get("verb", None) == "GET"
    assert endpoint.get("path", None) == (
        f"{instance.endpoint_fabrics}/" + f"{fabric_name}"
    )


def test_endpoints_00100() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - template_name getter/setter

    Summary
    -   Verify template_name getter returns the value set
        with template_name setter.
    """
    template_name = "MyTemplate"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.template_name = template_name
    assert instance.template_name == template_name


def test_endpoints_00110() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - template getter

    Summary
    -   Verify template getter raises ``ValueError``
        if `template_name`` is not set.
    """
    with does_not_raise():
        instance = ApiEndpoints()
    match = r"ApiEndpoints\.template: "
    match += r"template_name is required\."
    with pytest.raises(ValueError, match=match):
        instance.template


def test_endpoints_00111() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - template getter

    Summary
    -   Verify template getter returns the expected
        endpoint when ``template_name`` is set.
    """
    template_name = "MyTemplate"
    with does_not_raise():
        instance = ApiEndpoints()
        instance.template_name = template_name
        endpoint = instance.template
    assert endpoint.get("verb", None) == "GET"
    assert endpoint.get("path", None) == (
        f"{instance.endpoint_templates}/" + f"{template_name}"
    )


def test_endpoints_00120() -> None:
    """
    Classes and Methods
    - ApiEndpoints
        - __init__()
        - templates getter

    Summary
    -   Verify templates getter returns the expected endpoint.
    """
    with does_not_raise():
        instance = ApiEndpoints()
        endpoint = instance.templates
    assert endpoint.get("verb", None) == "GET"
    assert endpoint.get("path", None) == (f"{instance.endpoint_templates}")
