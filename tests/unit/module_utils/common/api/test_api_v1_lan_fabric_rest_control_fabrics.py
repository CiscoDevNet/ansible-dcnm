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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.control.fabrics.fabrics import (
    EpFabricConfigDeploy, EpFabricConfigSave, EpFabricCreate, EpFabricDelete,
    EpFabricDetails, EpFabricFreezeMode, EpFabrics, EpFabricUpdate,
    EpMaintenanceModeDisable, EpMaintenanceModeEnable, Fabrics)
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    does_not_raise

PATH_PREFIX = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics"
FABRIC_NAME = "MyFabric"
SERIAL_NUMBER = "CHS12345678"
TEMPLATE_NAME = "Easy_Fabric"
TICKET_ID = "MyTicket1234"


def test_ep_fabrics_00000():
    """
    ### Class
    -   EpFabricConfigDeploy

    ### Summary
    -   Verify __init__ method
            -   Correct class_name
            -   Correct default values
            -   Correct contents of required_properties
            -   Correct contents of properties dict
            -   Properties return values from properties dict
            -   path property raises ``ValueError`` when accessed, since
                ``fabric_name`` is not yet set.
    """
    with does_not_raise():
        instance = EpFabricConfigDeploy()
    assert instance.class_name == "EpFabricConfigDeploy"
    assert "fabric_name" in instance.required_properties
    assert len(instance.required_properties) == 1
    assert instance.properties["force_show_run"] is False
    assert instance.properties["include_all_msd_switches"] is False
    assert instance.properties["switch_id"] is None
    assert instance.properties["verb"] == "POST"
    assert instance.force_show_run is False
    assert instance.include_all_msd_switches is False
    assert instance.switch_id is None
    match = r"EpFabricConfigDeploy.path_fabric_name:\s+"
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_00010():
    """
    ### Class
    -   EpFabricConfigDeploy

    ### Summary
    -   Verify path and verb
    -   Verify default value for ``force_show_run``
    -   Verify default value for ``include_all_msd_switches``
    """
    with does_not_raise():
        instance = EpFabricConfigDeploy()
        instance.fabric_name = FABRIC_NAME
    assert f"{PATH_PREFIX}/{FABRIC_NAME}/config-deploy" in instance.path
    assert "forceShowRun=False" in instance.path
    assert "inclAllMSDSwitches=False" in instance.path
    assert instance.verb == "POST"


def test_ep_fabrics_00020():
    """
    ### Class
    -   EpFabricConfigDeploy

    ### Summary
    -   Verify setting ``force_show_run`` results in change to path.
    """
    with does_not_raise():
        instance = EpFabricConfigDeploy()
        instance.fabric_name = FABRIC_NAME
        instance.force_show_run = True
    assert f"{PATH_PREFIX}/{FABRIC_NAME}/config-deploy" in instance.path
    assert "forceShowRun=True" in instance.path
    assert "inclAllMSDSwitches=False" in instance.path
    assert instance.verb == "POST"


def test_ep_fabrics_00030():
    """
    ### Class
    -   EpFabricConfigDeploy

    ### Summary
    -   Verify setting ``include_all_msd_switches`` results in change to path.
    """
    with does_not_raise():
        instance = EpFabricConfigDeploy()
        instance.fabric_name = FABRIC_NAME
        instance.include_all_msd_switches = True
    assert f"{PATH_PREFIX}/{FABRIC_NAME}/config-deploy" in instance.path
    assert "forceShowRun=False" in instance.path
    assert "inclAllMSDSwitches=True" in instance.path
    assert instance.verb == "POST"


def test_ep_fabrics_00040():
    """
    ### Class
    -   EpFabricConfigDeploy

    ### Summary
    -   Verify setting ``switch_id`` results in change to path.
    """
    with does_not_raise():
        instance = EpFabricConfigDeploy()
        instance.fabric_name = FABRIC_NAME
        instance.switch_id = SERIAL_NUMBER
        instance.force_show_run = True
    path = f"{PATH_PREFIX}/{FABRIC_NAME}/config-deploy/{SERIAL_NUMBER}"
    path += "?forceShowRun=True"
    assert instance.path == path
    assert instance.verb == "POST"


def test_ep_fabrics_00050():
    """
    ### Class
    -   EpFabricConfigDeploy

    ### Summary
    -   Verify ``ValueError`` is raised if path is accessed
        before setting ``fabric_name``.

    """
    with does_not_raise():
        instance = EpFabricConfigDeploy()
    match = r"EpFabricConfigDeploy.path_fabric_name:\s+"
    match += r"fabric_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_00060():
    """
    ### Class
    -   EpFabricConfigDeploy

    ### Summary
    -   Verify ``ValueError`` is raised if ``fabric_name``
        is invalid.
    """
    fabric_name = "1_InvalidFabricName"
    with does_not_raise():
        instance = EpFabricConfigDeploy()
    match = r"EpFabricConfigDeploy.fabric_name:\s+"
    match += r"ConversionUtils\.validate_fabric_name:\s+"
    match += rf"Invalid fabric name: {fabric_name}\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_name = fabric_name  # pylint: disable=pointless-statement


def test_ep_fabrics_00070():
    """
    ### Class
    -   EpFabricConfigDeploy

    ### Summary
    -   Verify ``ValueError`` is raised if ``force_show_run``
        is not a boolean.
    """
    with does_not_raise():
        instance = EpFabricConfigDeploy()
    match = r"EpFabricConfigDeploy.force_show_run:\s+"
    match += r"Expected boolean for force_show_run\.\s+"
    match += r"Got NOT_BOOLEAN with type str\."
    with pytest.raises(ValueError, match=match):
        instance.force_show_run = "NOT_BOOLEAN"  # pylint: disable=pointless-statement


def test_ep_fabrics_00080():
    """
    ### Class
    -   EpFabricConfigDeploy

    ### Summary
    -   Verify ``ValueError`` is raised if ``include_all_msd_switches``
        is not a boolean.
    """
    with does_not_raise():
        instance = EpFabricConfigDeploy()
    match = r"EpFabricConfigDeploy.include_all_msd_switches:\s+"
    match += r"Expected boolean for include_all_msd_switches\.\s+"
    match += r"Got NOT_BOOLEAN with type str\."
    with pytest.raises(ValueError, match=match):
        instance.include_all_msd_switches = (
            "NOT_BOOLEAN"  # pylint: disable=pointless-statement
        )


MATCH_00090 = r"EpFabricConfigDeploy.switch_id:\s+"
MATCH_00090 += r"Expected string or list for switch_id\.\s+"


@pytest.mark.parametrize(
    "value, does_raise, expected",
    [
        (SERIAL_NUMBER, False, does_not_raise()),
        ([SERIAL_NUMBER], False, does_not_raise()),
        (EpFabricCreate(), True, pytest.raises(TypeError, match=MATCH_00090)),
        (None, True, pytest.raises(TypeError, match=MATCH_00090)),
        (10, True, pytest.raises(TypeError, match=MATCH_00090)),
        ([10], True, pytest.raises(TypeError, match=MATCH_00090)),
        ({10}, True, pytest.raises(TypeError, match=MATCH_00090)),
    ],
)
def test_ep_fabrics_00090(value, does_raise, expected):
    """
    ### Class
    -   EpFabricConfigDeploy

    ### Summary
    -   Verify exception is not raised if ``switch_id`` is a string or list.
    -   Verify ``ValueError`` is raised if ``switch_id`` is not a str or list.
    """
    with does_not_raise():
        instance = EpFabricConfigDeploy()
    with expected:
        instance.switch_id = value  # pylint: disable=pointless-statement
    if not does_raise:
        if isinstance(value, list):
            assert instance.switch_id == ",".join(value)
        else:
            assert instance.switch_id == value


def test_ep_fabrics_00100():
    """
    ### Class
    -   EpFabricConfigSave

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpFabricConfigSave()
        instance.fabric_name = FABRIC_NAME
    assert instance.path == f"{PATH_PREFIX}/{FABRIC_NAME}/config-save"
    assert instance.verb == "POST"


def test_ep_fabrics_00110():
    """
    ### Class
    -   EpFabricConfigSave

    ### Summary
    -   Verify ticket_id is added to path when set.
    """
    with does_not_raise():
        instance = EpFabricConfigSave()
        instance.fabric_name = FABRIC_NAME
        instance.ticket_id = TICKET_ID
    ticket_id_path = f"{PATH_PREFIX}/{FABRIC_NAME}/config-save"
    ticket_id_path += f"?ticketId={TICKET_ID}"
    assert instance.path == ticket_id_path
    assert instance.verb == "POST"


def test_ep_fabrics_00120():
    """
    ### Class
    -   EpFabricConfigSave

    ### Summary
    -   Verify ticket_id is added to path when set.
    """
    with does_not_raise():
        instance = EpFabricConfigSave()
        instance.fabric_name = FABRIC_NAME
        instance.ticket_id = TICKET_ID
    ticket_id_path = f"{PATH_PREFIX}/{FABRIC_NAME}/config-save"
    ticket_id_path += f"?ticketId={TICKET_ID}"
    assert instance.path == ticket_id_path
    assert instance.verb == "POST"


def test_ep_fabrics_00130():
    """
    ### Class
    -   EpFabricConfigSave

    ### Summary
    -   Verify ``ValueError`` is raised if ``ticket_id``
        is not a string.
    """
    with does_not_raise():
        instance = EpFabricConfigSave()
        instance.fabric_name = FABRIC_NAME
    match = r"EpFabricConfigSave.ticket_id:\s+"
    match += r"Expected string for ticket_id\.\s+"
    match += r"Got 10 with type int\."
    with pytest.raises(ValueError, match=match):
        instance.ticket_id = 10  # pylint: disable=pointless-statement


def test_ep_fabrics_00140():
    """
    ### Class
    -   EpFabricConfigSave

    ### Summary
    -   Verify ``ValueError`` is raised if path is accessed
        before setting ``fabric_name``.

    """
    with does_not_raise():
        instance = EpFabricConfigSave()
    match = r"EpFabricConfigSave.path_fabric_name:\s+"
    match += r"fabric_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_00150():
    """
    ### Class
    -   EpFabricConfigSave

    ### Summary
    -   Verify ``ValueError`` is raised if ``fabric_name``
        is invalid.
    """
    fabric_name = "1_InvalidFabricName"
    with does_not_raise():
        instance = EpFabricConfigSave()
    match = r"EpFabricConfigSave.fabric_name:\s+"
    match += r"ConversionUtils\.validate_fabric_name:\s+"
    match += rf"Invalid fabric name: {fabric_name}\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_name = fabric_name  # pylint: disable=pointless-statement


def test_ep_fabrics_00200():
    """
    ### Class
    -   EpFabricCreate

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpFabricCreate()
        instance.fabric_name = FABRIC_NAME
        instance.template_name = TEMPLATE_NAME
    assert instance.path == f"{PATH_PREFIX}/{FABRIC_NAME}/{TEMPLATE_NAME}"
    assert instance.verb == "POST"


def test_ep_fabrics_00240():
    """
    ### Class
    -   EpFabricCreate

    ### Summary
    -   Verify ``ValueError`` is raised if path is accessed
        before setting ``fabric_name``.

    """
    with does_not_raise():
        instance = EpFabricCreate()
    match = r"EpFabricCreate\.path_fabric_name_template_name:\s+"
    match += r"fabric_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_00250():
    """
    ### Class
    -   EpFabricCreate

    ### Summary
    -   Verify ``ValueError`` is raised if ``fabric_name``
        is invalid.
    """
    fabric_name = "1_InvalidFabricName"
    with does_not_raise():
        instance = EpFabricCreate()
    match = r"EpFabricCreate.fabric_name:\s+"
    match += r"ConversionUtils\.validate_fabric_name:\s+"
    match += rf"Invalid fabric name: {fabric_name}\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_name = fabric_name  # pylint: disable=pointless-statement


def test_ep_fabrics_00260():
    """
    ### Class
    -   EpFabricCreate

    ### Summary
    -   Verify ``ValueError`` is raised if path is accessed
        before setting ``template_name``.

    """
    with does_not_raise():
        instance = EpFabricCreate()
        instance.fabric_name = FABRIC_NAME
    match = r"EpFabricCreate\.path_fabric_name_template_name:\s+"
    match += r"template_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_00270():
    """
    ### Class
    -   EpFabricCreate

    ### Summary
    -   Verify ``ValueError`` is raised if ``template_name``
        is invalid.
    """
    template_name = "Invalid_Template_Name"
    with does_not_raise():
        instance = EpFabricCreate()
        instance.fabric_name = FABRIC_NAME
    match = r"EpFabricCreate.template_name:\s+"
    match += r"Invalid template_name: Invalid_Template_Name\.\s+"
    match += r"Expected one of:.*\."
    with pytest.raises(ValueError, match=match):
        instance.template_name = template_name  # pylint: disable=pointless-statement


def test_ep_fabrics_00400():
    """
    ### Class
    -   EpFabricDelete

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpFabricDelete()
        instance.fabric_name = FABRIC_NAME
    assert instance.path == f"{PATH_PREFIX}/{FABRIC_NAME}"
    assert instance.verb == "DELETE"


def test_ep_fabrics_00440():
    """
    ### Class
    -   EpFabricDelete

    ### Summary
    -   Verify ``ValueError`` is raised if path is accessed
        before setting ``fabric_name``.

    """
    with does_not_raise():
        instance = EpFabricDelete()
    match = r"EpFabricDelete.path_fabric_name:\s+"
    match += r"fabric_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_00450():
    """
    ### Class
    -   EpFabricDelete

    ### Summary
    -   Verify ``ValueError`` is raised if ``fabric_name``
        is invalid.
    """
    fabric_name = "1_InvalidFabricName"
    with does_not_raise():
        instance = EpFabricDelete()
    match = r"EpFabricDelete.fabric_name:\s+"
    match += r"ConversionUtils\.validate_fabric_name:\s+"
    match += rf"Invalid fabric name: {fabric_name}\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_name = fabric_name  # pylint: disable=pointless-statement


def test_ep_fabrics_00500():
    """
    ### Class
    -   EpFabricDetails

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpFabricDetails()
        instance.fabric_name = FABRIC_NAME
    assert instance.path == f"{PATH_PREFIX}/{FABRIC_NAME}"
    assert instance.verb == "GET"


def test_ep_fabrics_00540():
    """
    ### Class
    -   EpFabricDetails

    ### Summary
    -   Verify ``ValueError`` is raised if path is accessed
        before setting ``fabric_name``.

    """
    with does_not_raise():
        instance = EpFabricDetails()
    match = r"EpFabricDetails.path_fabric_name:\s+"
    match += r"fabric_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_00550():
    """
    ### Class
    -   EpFabricDetails

    ### Summary
    -   Verify ``ValueError`` is raised if ``fabric_name``
        is invalid.
    """
    fabric_name = "1_InvalidFabricName"
    with does_not_raise():
        instance = EpFabricDetails()
    match = r"EpFabricDetails.fabric_name:\s+"
    match += r"ConversionUtils\.validate_fabric_name:\s+"
    match += rf"Invalid fabric name: {fabric_name}\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_name = fabric_name  # pylint: disable=pointless-statement


def test_ep_fabrics_00600():
    """
    ### Class
    -   EpFabricFreezeMode

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpFabricFreezeMode()
        instance.fabric_name = FABRIC_NAME
    assert instance.path == f"{PATH_PREFIX}/{FABRIC_NAME}/freezemode"
    assert instance.verb == "GET"


def test_ep_fabrics_00640():
    """
    ### Class
    -   EpFabricFreezeMode

    ### Summary
    -   Verify ``ValueError`` is raised if path is accessed
        before setting ``fabric_name``.

    """
    with does_not_raise():
        instance = EpFabricFreezeMode()
    match = r"EpFabricFreezeMode.path_fabric_name:\s+"
    match += r"fabric_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_00650():
    """
    ### Class
    -   EpFabricFreezeMode

    ### Summary
    -   Verify ``ValueError`` is raised if ``fabric_name``
        is invalid.
    """
    fabric_name = "1_InvalidFabricName"
    with does_not_raise():
        instance = EpFabricFreezeMode()
    match = r"EpFabricFreezeMode.fabric_name:\s+"
    match += r"ConversionUtils\.validate_fabric_name:\s+"
    match += rf"Invalid fabric name: {fabric_name}\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_name = fabric_name  # pylint: disable=pointless-statement


# NOTE: EpFabricSummary tests are in test_v1_api_switches.py


def test_ep_fabrics_00700():
    """
    ### Class
    -   EpFabricUpdate

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpFabricUpdate()
        instance.fabric_name = FABRIC_NAME
        instance.template_name = TEMPLATE_NAME
    assert instance.path == f"{PATH_PREFIX}/{FABRIC_NAME}/{TEMPLATE_NAME}"
    assert instance.verb == "PUT"


def test_ep_fabrics_00740():
    """
    ### Class
    -   EpFabricUpdate

    ### Summary
    -   Verify ``ValueError`` is raised if path is accessed
        before setting ``fabric_name``.

    """
    with does_not_raise():
        instance = EpFabricUpdate()
    match = r"EpFabricUpdate\.path_fabric_name_template_name:\s+"
    match += r"fabric_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_00750():
    """
    ### Class
    -   EpFabricUpdate

    ### Summary
    -   Verify ``ValueError`` is raised if ``fabric_name``
        is invalid.
    """
    fabric_name = "1_InvalidFabricName"
    with does_not_raise():
        instance = EpFabricUpdate()
    match = r"EpFabricUpdate.fabric_name:\s+"
    match += r"ConversionUtils\.validate_fabric_name:\s+"
    match += rf"Invalid fabric name: {fabric_name}\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_name = fabric_name  # pylint: disable=pointless-statement


def test_ep_fabrics_00760():
    """
    ### Class
    -   EpFabricUpdate

    ### Summary
    -   Verify ``ValueError`` is raised if path is accessed
        before setting ``template_name``.

    """
    with does_not_raise():
        instance = EpFabricUpdate()
        instance.fabric_name = FABRIC_NAME
    match = r"EpFabricUpdate\.path_fabric_name_template_name:\s+"
    match += r"template_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_00770():
    """
    ### Class
    -   EpFabricUpdate

    ### Summary
    -   Verify ``ValueError`` is raised if ``template_name``
        is invalid.
    """
    template_name = "Invalid_Template_Name"
    with does_not_raise():
        instance = EpFabricUpdate()
        instance.fabric_name = FABRIC_NAME
    match = r"EpFabricUpdate.template_name:\s+"
    match += r"Invalid template_name: Invalid_Template_Name\.\s+"
    match += r"Expected one of:.*\."
    with pytest.raises(ValueError, match=match):
        instance.template_name = template_name  # pylint: disable=pointless-statement


def test_ep_fabrics_00800():
    """
    ### Class
    -   EpFabrics

    ### Summary
    -   Verify __init__ method
            -   Correct class_name
    """
    with does_not_raise():
        instance = EpFabrics()
    assert instance.class_name == "EpFabrics"


def test_ep_fabrics_00810():
    """
    ### Class
    -   EpFabrics

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpFabrics()
    assert instance.path == f"{PATH_PREFIX}"
    assert instance.verb == "GET"


def test_ep_fabrics_03000():
    """
    ### Class
    -   EpMaintenanceModeEnable

    ### Summary
    -   Verify __init__ method
            -   Correct class_name
            -   Correct contents of required_properties
            -   Correct verb is returned
    """
    with does_not_raise():
        instance = EpMaintenanceModeEnable()
    assert instance.class_name == "EpMaintenanceModeEnable"
    assert "fabric_name" in instance.required_properties
    assert "serial_number" in instance.required_properties
    assert instance.verb == "POST"


def test_ep_fabrics_03010():
    """
    ### Class
    -   EpMaintenanceModeEnable

    ### Summary
    -   verb property returns POST.
    """
    with does_not_raise():
        instance = EpMaintenanceModeEnable()
    assert instance.verb == "POST"


def test_ep_fabrics_03020():
    """
    ### Class
    -   EpMaintenanceModeEnable

    ### Summary
    -   Verify path property raises ``ValueError`` if accessed before setting
        fabric_name.
    """
    with does_not_raise():
        instance = EpMaintenanceModeEnable()
        instance.serial_number = SERIAL_NUMBER
    match = r"EpMaintenanceModeEnable.path_fabric_name_serial_number:\s+"
    match += r"fabric_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_03030():
    """
    ### Class
    -   EpMaintenanceModeEnable

    ### Summary
    -   Verify path property raises ``ValueError`` if accessed before setting
        serial_number.
    """
    with does_not_raise():
        instance = EpMaintenanceModeEnable()
        instance.fabric_name = FABRIC_NAME
    match = r"EpMaintenanceModeEnable.path_fabric_name_serial_number:\s+"
    match += r"serial_number must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_03040():
    """
    ### Class
    -   EpMaintenanceModeEnable

    ### Summary
    -   Verify path is set correctly if fabric_name and
        serial_number are provided.
    """
    with does_not_raise():
        instance = EpMaintenanceModeEnable()
        instance.fabric_name = FABRIC_NAME
        instance.serial_number = SERIAL_NUMBER
    path = f"{PATH_PREFIX}/{FABRIC_NAME}/switches/{SERIAL_NUMBER}"
    path += "/maintenance-mode"
    assert instance.path == path


def test_ep_fabrics_03050():
    """
    ### Class
    -   EpMaintenanceModeEnable

    ### Summary
    -   Verify path is set correctly if fabric_name and
        serial_number and ticket_id are provided.
    """
    with does_not_raise():
        instance = EpMaintenanceModeEnable()
        instance.fabric_name = FABRIC_NAME
        instance.serial_number = SERIAL_NUMBER
        instance.ticket_id = TICKET_ID
    path = f"{PATH_PREFIX}/{FABRIC_NAME}/switches/{SERIAL_NUMBER}"
    path += f"/maintenance-mode?ticketId={TICKET_ID}"
    assert instance.path == path


def test_ep_fabrics_03100():
    """
    ### Class
    -   EpMaintenanceModeDisable

    ### Summary
    -   Verify __init__ method
            -   Correct class_name
            -   Correct contents of required_properties
    """
    with does_not_raise():
        instance = EpMaintenanceModeDisable()
    assert instance.class_name == "EpMaintenanceModeDisable"
    assert "fabric_name" in instance.required_properties
    assert "serial_number" in instance.required_properties


def test_ep_fabrics_03110():
    """
    ### Class
    -   EpMaintenanceModeDisable

    ### Summary
    -   verb property returns DELETE.
    """
    with does_not_raise():
        instance = EpMaintenanceModeDisable()
    assert instance.verb == "DELETE"


def test_ep_fabrics_03120():
    """
    ### Class
    -   EpMaintenanceModeDisable

    ### Summary
    -   Verify path property raises ``ValueError`` if accessed before setting
        fabric_name.
    """
    with does_not_raise():
        instance = EpMaintenanceModeDisable()
        instance.serial_number = SERIAL_NUMBER
    match = r"EpMaintenanceModeDisable.path_fabric_name_serial_number:\s+"
    match += r"fabric_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_03130():
    """
    ### Class
    -   EpMaintenanceModeDisable

    ### Summary
    -   Verify path property raises ``ValueError`` if accessed before setting
        serial_number.
    """
    with does_not_raise():
        instance = EpMaintenanceModeDisable()
        instance.fabric_name = FABRIC_NAME
    match = r"EpMaintenanceModeDisable.path_fabric_name_serial_number:\s+"
    match += r"serial_number must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_03140():
    """
    ### Class
    -   EpMaintenanceModeDisable

    ### Summary
    -   Verify path is set correctly if fabric_name and
        serial_number are provided.
    """
    with does_not_raise():
        instance = EpMaintenanceModeDisable()
        instance.fabric_name = FABRIC_NAME
        instance.serial_number = SERIAL_NUMBER
    path = f"{PATH_PREFIX}/{FABRIC_NAME}/switches/{SERIAL_NUMBER}"
    path += "/maintenance-mode"
    assert instance.path == path


def test_ep_fabrics_03150():
    """
    ### Class
    -   EpMaintenanceModeDisable

    ### Summary
    -   Verify path is set correctly if fabric_name and
        serial_number and ticket_id are provided.
    """
    with does_not_raise():
        instance = EpMaintenanceModeDisable()
        instance.fabric_name = FABRIC_NAME
        instance.serial_number = SERIAL_NUMBER
        instance.ticket_id = TICKET_ID
    path = f"{PATH_PREFIX}/{FABRIC_NAME}/switches/{SERIAL_NUMBER}"
    path += f"/maintenance-mode?ticketId={TICKET_ID}"
    assert instance.path == path


MATCH_10000 = r"Fabrics.serial_number:\s+"
MATCH_10000 += r"Expected string for serial_number\.\s+"


@pytest.mark.parametrize(
    "value, does_raise, expected",
    [
        (SERIAL_NUMBER, False, does_not_raise()),
        ([SERIAL_NUMBER], True, pytest.raises(TypeError, match=MATCH_10000)),
        (EpFabricCreate(), True, pytest.raises(TypeError, match=MATCH_10000)),
        (None, True, pytest.raises(TypeError, match=MATCH_10000)),
        (10, True, pytest.raises(TypeError, match=MATCH_10000)),
        ([10], True, pytest.raises(TypeError, match=MATCH_10000)),
        ({10}, True, pytest.raises(TypeError, match=MATCH_10000)),
    ],
)
def test_ep_fabrics_10000(value, does_raise, expected):
    """
    ### Class
    -   Fabrics

    ### Summary
    -   Verify serial_number does not raise if set to string.
    -   Verify serial_number raises ``ValueError`` if not a string.
    """
    with does_not_raise():
        instance = Fabrics()
    with expected:
        instance.serial_number = value  # pylint: disable=pointless-statement
    if not does_raise:
        assert instance.serial_number == value
