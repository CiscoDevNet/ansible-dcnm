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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.rest.control.fabrics import (
    EpFabricConfigDeploy, EpFabricConfigSave, EpFabricDelete, EpFabricDetails, EpFabricFreezeMode)
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    does_not_raise

PATH_PREFIX = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics"
FABRIC_NAME = "MyFabric"

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
    -   Verify ``ValueError`` is raised if path is accessed
        before setting ``fabric_name``.

    """
    with does_not_raise():
        instance = EpFabricConfigDeploy()
    match = r"EpFabricConfigDeploy.path_fabric_name:\s+"
    match += r"fabric_name must be set prior to accessing path\."
    with pytest.raises(ValueError, match=match):
        instance.path  # pylint: disable=pointless-statement


def test_ep_fabrics_00050():
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


def test_ep_fabrics_00060():
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


def test_ep_fabrics_00070():
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
        instance.include_all_msd_switches = "NOT_BOOLEAN"  # pylint: disable=pointless-statement


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
        instance.ticket_id = "MyTicket1234"
    ticket_id_path = f"{PATH_PREFIX}/{FABRIC_NAME}/config-save"
    ticket_id_path += "?ticketId=MyTicket1234"
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
        instance.ticket_id = "MyTicket1234"
    ticket_id_path = f"{PATH_PREFIX}/{FABRIC_NAME}/config-save"
    ticket_id_path += "?ticketId=MyTicket1234"
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
    -   EpFabricDelete

    ### Summary
    -   Verify path and verb
    """
    with does_not_raise():
        instance = EpFabricDelete()
        instance.fabric_name = FABRIC_NAME
    assert instance.path == f"{PATH_PREFIX}/{FABRIC_NAME}"
    assert instance.verb == "DELETE"


def test_ep_fabrics_00240():
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


def test_ep_fabrics_00250():
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


def test_ep_fabrics_00300():
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


def test_ep_fabrics_00340():
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


def test_ep_fabrics_00350():
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


def test_ep_fabrics_00400():
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


def test_ep_fabrics_00440():
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


def test_ep_fabrics_00450():
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
