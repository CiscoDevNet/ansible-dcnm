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
# pylint: disable=unused-import
# Some fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.control.fabrics.fabrics import (
    EpFabricConfigDeploy, EpFabricCreate)
from ansible_collections.cisco.dcnm.plugins.module_utils.common.sender_dcnm import \
    Sender
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import (
    ResponseGenerator, does_not_raise, responses_sender_dcnm,
    sender_dcnm_fixture)


def test_sender_dcnm_00000() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   __init__()

    ### Summary
    -   Class properties are initialized to expected values
    """
    with does_not_raise():
        instance = Sender()
    assert instance.params is None
    assert instance._ansible_module is None
    assert instance._path is None
    assert instance._payload is None
    assert instance._response is None
    assert instance._valid_verbs == {"GET", "POST", "PUT", "DELETE"}
    assert instance._verb is None


def test_sender_dcnm_00100() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   _verify_commit_parameters()
            -   commit()

    ### Summary
    Verify ``commit()`` re-raises ``ValueError`` when
    ``_verify_commit_parameters()`` raises ``ValueError``
    due to ``ansible_module`` not being set.

    ### Setup - Code
    -   Sender() is initialized.
    -   Sender().path is set.
    -   Sender().verb is set.
    -   Sender().ansible_module is NOT set.

    ### Setup - Data
    None

    ### Trigger
    -   Sender().commit() is called.

    ### Expected Result
    -   Sender().commit() re-raises ``ValueError``.


    """
    with does_not_raise():
        instance = Sender()
        instance.path = "/foo/path"
        instance.verb = "GET"

    match = r"Sender\.commit:\s+"
    match += r"Not all mandatory parameters are set\.\s+"
    match += r"Error detail:\s+"
    match += r"Sender\._verify_commit_parameters:\s+"
    match += r"ansible_module must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_sender_dcnm_00110(sender_dcnm) -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   _verify_commit_parameters()
            -   commit()

    ### Summary
    Verify ``commit()`` re-raises ``ValueError`` when
    ``_verify_commit_parameters()`` raises ``ValueError``
    due to ``path`` not being set.

    ### Setup - Code
    -   Sender() is initialized.
    -   Sender().ansible_module is set.
    -   Sender().verb is set.
    -   Sender().path is NOT set.

    ### Setup - Data
    None

    ### Trigger
    -   Sender().commit() is called.

    ### Expected Result
    -   Sender().commit() re-raises ``ValueError``.
    """
    with does_not_raise():
        instance = sender_dcnm
        instance.verb = "GET"

    match = r"Sender\.commit:\s+"
    match += r"Not all mandatory parameters are set\.\s+"
    match += r"Error detail:\s+"
    match += r"Sender\._verify_commit_parameters:\s+"
    match += r"path must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_sender_dcnm_00120(sender_dcnm) -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   _verify_commit_parameters()
            -   commit()

    ### Summary
    Verify ``commit()`` re-raises ``ValueError`` when
    ``_verify_commit_parameters()`` raises ``ValueError``
    due to ``verb`` not being set.

    ### Setup - Code
    -   Sender() is initialized.
    -   Sender().ansible_module is set.
    -   Sender().path is set.
    -   Sender().verb is NOT set.

    ### Setup - Data
    None

    ### Trigger
    -   Sender().commit() is called.

    ### Expected Result
    -   Sender().commit() re-raises ``ValueError``.
    """
    with does_not_raise():
        instance = sender_dcnm
        instance.path = "/foo/path"

    match = r"Sender\.commit:\s+"
    match += r"Not all mandatory parameters are set\.\s+"
    match += r"Error detail:\s+"
    match += r"Sender\._verify_commit_parameters:\s+"
    match += r"verb must be set before calling commit\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_sender_dcnm_00200(sender_dcnm, monkeypatch) -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   _verify_commit_parameters()
            -   commit()

    ### Summary
    Verify ``commit()`` populates ``response`` with expected values
    for ``verb`` == POST and ``payload`` == None.

    ### Setup - Code
    -   Sender() is initialized.
    -   Sender().ansible_module is set.
    -   Sender().path is set to /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/VXLAN_Fabric/config-deploy/FDO22180ASJ?forceShowRun=False.
    -   Sender().verb is set to POST.

    ### Setup - Data
    responses_SenderDcnm.json:
        -   DATA.status: Configuration deployment completed.
        -   MESSAGE: OK
        -   METHOD: POST
        -   RETURN_CODE: 200


    ### Trigger
    -   Sender().commit() is called.

    ### Expected Result
    -   Sender().commit() sets Sender().response to expected value.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_sender_dcnm(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):  # pylint: disable=unused-argument
        item = gen.next
        return item

    with does_not_raise():
        endpoint = EpFabricConfigDeploy()
        endpoint.fabric_name = "VXLAN_Fabric"
        endpoint.serial_number = "FDO22180ASJ"
        endpoint.force_show_run = False
        instance = sender_dcnm
        monkeypatch.setattr(instance, "_dcnm_send", mock_dcnm_send)
        instance.path = endpoint.path
        instance.verb = endpoint.verb
        instance.commit()
    assert instance.response.get("MESSAGE", None) == "OK"
    assert instance.response.get("METHOD", None) == "POST"
    assert instance.response.get("RETURN_CODE", None) == 200
    assert (
        instance.response.get("DATA", {}).get("status")
        == "Configuration deployment completed."
    )


def test_sender_dcnm_00210(sender_dcnm, monkeypatch) -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   _verify_commit_parameters()
            -   commit()

    ### Summary
    Verify ``commit()`` populates ``response`` with expected values
    for ``verb`` == POST and ``payload`` != None.

    ### Setup - Code
    -   Sender() is initialized.
    -   Sender().ansible_module is set.
    -   Sender().path is set to /appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/VXLAN_Fabric/config-deploy/FDO22180ASJ?forceShowRun=False.
    -   Sender().verb is set to POST.

    ### Setup - Data
    responses_SenderDcnm.json:
        -   DATA.status: Configuration deployment completed.
        -   MESSAGE: OK
        -   METHOD: POST
        -   RETURN_CODE: 200


    ### Trigger
    -   Sender().commit() is called.

    ### Expected Result
    -   Sender().commit() sets Sender().response to expected value.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    def responses():
        yield responses_sender_dcnm(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):  # pylint: disable=unused-argument
        item = gen.next
        return item

    payload = {
        "BGP_AS": 65001,
        "DEPLOY": True,
        "FABRIC_NAME": "VXLAN_Fabric",
        "FABRIC_TYPE": "VXLAN_EVPN",
    }

    with does_not_raise():
        endpoint = EpFabricCreate()
        endpoint.fabric_name = "VXLAN_Fabric"
        endpoint.template_name = "Easy_Fabric"
        instance = sender_dcnm
        monkeypatch.setattr(instance, "_dcnm_send", mock_dcnm_send)
        instance.path = endpoint.path
        instance.verb = endpoint.verb
        instance.payload = payload
        instance.commit()
    assert instance.response.get("MESSAGE", None) == "OK"
    assert instance.response.get("METHOD", None) == "POST"
    assert instance.response.get("RETURN_CODE", None) == 200
    assert (
        instance.response.get("DATA", {}).get("nvPairs").get("FABRIC_NAME", None)
        == "VXLAN_Fabric"
    )


def test_sender_dcnm_00300() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   ansible_module.setter

    ### Summary
    Verify ``ansible_module.setter`` raises ``TypeError``
    if passed something other than an AnsibleModule() instance.
    """
    with does_not_raise():
        instance = Sender()

    match = r"Sender\.ansible_module:\s+"
    match += r"ansible_module must be an instance of AnsibleModule\.\s+"
    match += r"Got type int, value 10\.\s+"
    match += r"Error detail: 'int' object has no attribute 'params'\."
    with pytest.raises(TypeError, match=match):
        instance.ansible_module = 10


def test_sender_dcnm_00400() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   payload.setter

    ### Summary
    Verify ``payload.setter`` raises ``TypeError``
    if passed something other than a ``dict``.
    """
    with does_not_raise():
        instance = Sender()

    match = r"Sender\.payload:\s+"
    match += r"payload must be a dict\.\s+"
    match += r"Got type int, value 10\."
    with pytest.raises(TypeError, match=match):
        instance.payload = 10


def test_sender_dcnm_00500() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   response.setter

    ### Summary
    Verify ``response.setter`` raises ``TypeError``
    if passed something other than a ``dict``.
    """
    with does_not_raise():
        instance = Sender()

    match = r"Sender\.response:\s+"
    match += r"response must be a dict\.\s+"
    match += r"Got type int, value 10\."
    with pytest.raises(TypeError, match=match):
        instance.response = 10


def test_sender_dcnm_00600() -> None:
    """
    ### Classes and Methods
    -   Sender()
            -   verb.setter

    ### Summary
    Verify ``verb.setter`` raises ``ValueError``
    if passed an invalid value (not one of DELETE, GET, POST, PUT).
    """
    with does_not_raise():
        instance = Sender()

    match = r"Sender\.verb:\s+"
    match += r"verb must be one of.*\.\s+"
    match += r"Got 10\."
    with pytest.raises(ValueError, match=match):
        instance.verb = 10
