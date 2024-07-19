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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import inspect

import pytest
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.lan_fabric.rest.control.fabrics.fabrics import \
    EpFabricDelete
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_details import \
    FabricDetailsByName
from ansible_collections.cisco.dcnm.plugins.module_utils.fabric.fabric_summary import \
    FabricSummary
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, does_not_raise, fabric_delete_fixture, params,
    responses_fabric_delete, responses_fabric_details_by_name,
    responses_fabric_summary, rest_send_response_current)


def test_fabric_delete_00010(fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricDelete
        - __init__()
        - _build_properties()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_delete
        instance.fabric_details = FabricDetailsByName(params)
    assert instance.action == "delete"
    assert instance._cannot_delete_fabric_reason is None
    assert instance.class_name == "FabricDelete"
    assert instance.fabric_names is None
    assert instance._fabrics_to_delete == []
    assert instance.path is None
    assert instance.state == "deleted"
    assert instance.verb is None
    assert isinstance(instance.ep_fabric_delete, EpFabricDelete)
    assert isinstance(instance.fabric_details, FabricDetailsByName)


def test_fabric_delete_00020(fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricDelete
        - __init__()
        - _set_fabric_delete_endpoint()

    Summary
    -   Verify that endpoint values are set correctly when a valid
        fabric_name is passed to _set_fabric_delete_endpoint()
    -   Verify that an Exception is not raised
    """
    with does_not_raise():
        instance = fabric_delete
        instance.results = Results()
        instance._set_fabric_delete_endpoint("MyFabric")
    path = "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics"
    path += "/MyFabric"
    assert instance.path == path
    assert instance.verb == "DELETE"


def test_fabric_delete_00021(fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricDelete
        - __init__()
        - _set_fabric_delete_endpoint()

    Summary
    -   Verify ``TypeError`` is raised because call to
        _set_fabric_delete_endpoint() is missing argument
        ``fabric_name``.
    """
    with does_not_raise():
        instance = fabric_delete
        instance.results = Results()

    match = r"_set_fabric_delete_endpoint\(\)\s+"
    match += r"missing 1 required positional argument: 'fabric_name'"
    with pytest.raises(TypeError, match=match):
        instance._set_fabric_delete_endpoint()


@pytest.mark.parametrize("fabric_name", [None, 123, 123.45, [], {}])
def test_fabric_delete_00022(fabric_delete, fabric_name) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricDelete
        - __init__()
        - _set_fabric_delete_endpoint()
        - ApiEndpoints.fabric_delete

    Summary
    -   Verify ApiEndpoints re-raises ``TypeError`` raised by
        ConversionUtils() because ``fabric_name`` argument passed
        to _set_fabric_delete_endpoint() is not a string.
    """
    match = r"ConversionUtils\.validate_fabric_name: "
    match += "Invalid fabric name. Expected string. Got"

    with does_not_raise():
        instance = fabric_delete
    with pytest.raises(ValueError, match=match):
        instance._set_fabric_delete_endpoint(fabric_name)


@pytest.mark.parametrize("fabric_name", ["", "1abc", "a,bcd", "abc d", "ab!d"])
def test_fabric_delete_00023(fabric_delete, fabric_name) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
        - payloads setter
    - FabricDelete
        - __init__()
        - _set_fabric_delete_endpoint()
        - ApiEndpoints.fabric_delete

    Summary
    -   Verify ApiEndpoints() re-raises ``ValueError`` raised by
        ConversionUtils() because ``fabric_name`` argument passed
        to _set_fabric_delete_endpoint() is an invalid string.
    """
    match = r"ConversionUtils\.validate_fabric_name: "
    match += rf"Invalid fabric name: {fabric_name}\. "
    match += "Fabric name must start with a letter A-Z "
    match += "or a-z and contain only the characters in: "
    match += r"\[A-Z,a-z,0-9,-,_\]\."

    with does_not_raise():
        instance = fabric_delete
    with pytest.raises(ValueError, match=match):
        instance._set_fabric_delete_endpoint(fabric_name)


def test_fabric_delete_00030(fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricDelete
        - __init__()
        - commit()
        - _validate_commit_parameters()

    Summary
    -   Verify that ``ValueError`` is raised because fabric_names is not set
        prior to calling commit()

    """
    with does_not_raise():
        instance = fabric_delete
        instance.results = Results()
        instance.rest_send = RestSend(MockAnsibleModule())

    match = r"FabricDelete\._validate_commit_parameters: "
    match += "fabric_names must be set prior to calling commit."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_delete_00031(fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricDelete
        - __init__()
        - commit()
        - _validate_commit_parameters()

    Summary
    -   Verify that ``ValueError`` is raised because rest_send is not set
        prior to calling commit()

    """
    with does_not_raise():
        instance = fabric_delete
        instance.results = Results()
        instance.fabric_names = ["MyFabric"]

    match = r"FabricDelete\._validate_commit_parameters: "
    match += "rest_send must be set prior to calling commit."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_delete_00032(fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricDelete
        - __init__()
        - commit()
        - _validate_commit_parameters()

    Summary
    -   Verify that ``ValueError`` is raised because results is not set
        prior to calling commit()

    """
    with does_not_raise():
        instance = fabric_delete
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_names = ["MyFabric"]

    match = r"FabricDelete\._validate_commit_parameters: "
    match += "results must be set prior to calling commit."
    with pytest.raises(ValueError, match=match):
        instance.commit()


def test_fabric_delete_00040(monkeypatch, fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
        - payloads setter
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricDelete
        - __init__()
        - commit()

    Summary
    -   Verify successful fabric delete code path.
    -   The user attempts to delete a fabric and the fabric exists on the
        controller, and the fabric is empty.

    Code Flow
    -   FabricDelete.commit() calls FabricDelete()._validate_commit_parameters()
        which succeeds since all required parameters are set.
    -   FabricDelete.commit() calls FabricDelete()._get_fabrics_to_delete()
    -   FabricDelete()._get_fabrics_to_delete() calls
        FabricDetails().refresh() which returns a dict with keys
        DATA == [{f1 fabric data dict}], RETURN_CODE == 200
    -   FabricDelete()._get_fabrics_to_delete() calls
        FabricDelete()._verify_fabric_can_be_deleted() which returns
        successfully (does not raise ``ValueError``)
    -   FabricDelete()._get_fabrics_to_delete() sets
        FabricDelete()._fabrics_to_delete to a list containing fabric f1.
    -   FabricDelete().commit() calls FabricDelete()._send_requests()
    -   FabricDelete._send_requests() sets RestSend() parameters
    -   FabricDelete._send_requests() calls FabricDelete._send_request() for
        each fabric in the FabricDelete()._fabrics_to_delete list.
    -   FabricDelete._send_request() calls FabricDelete._set_fabric_delete_endpoint()
        which returns the request endpoint information (path, verb) for fabric f1.
    -   FabricDelete._send_request() sets RestSend().path and RestSend().verb and
        calls RestSend().commit(), which sends the request.
    -   FabricDelete()._send_request() calls FabricDelete().register_result()
    -   FabricDelete().register_result() sets the results for the fabric
        delete operation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
        yield responses_fabric_summary(key)
        yield responses_fabric_delete(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_delete
        instance.fabric_names = ["f1"]

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)
    with does_not_raise():
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[0].get("FABRIC_NAME", None) == "f1"

    assert instance.results.metadata[0].get("action", None) == "delete"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "deleted"

    assert instance.results.response[0].get("RETURN_CODE", None) == 200

    msg = "Fabric 'f1' is deleted successfully!"
    assert instance.results.response[0].get("DATA", None) == msg
    assert instance.results.response[0].get("METHOD", None) == "DELETE"

    assert instance.results.result[0].get("changed", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert True in instance.results.changed
    assert False not in instance.results.changed


def test_fabric_delete_00042(monkeypatch, fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
        - payloads setter
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricDelete
        - __init__()
        - commit()

    Summary
    -   Verify FabricDelete().commit() re-raises ``ValueError`` when
        ``EpFabricDelete()._send_requests() re-raises ``ValueError`` when
        ``EpFabricDelete()._send_request() re-raises ``ValueError`` when
        ``FabricDelete()._set_fabric_delete_endpoint()`` raises ``ValueError``.
    -   The user attempts to delete a fabric and the fabric exists on the
        controller, and the fabric is empty, but _set_fabric_delete_endpoint()
        re-raises ``ValueError``.

    Code Flow
    -   FabricDelete.commit() calls FabricDelete()._validate_commit_parameters()
        which succeeds since all required parameters are set.
    -   FabricDelete.commit() calls FabricDelete()._get_fabrics_to_delete()
    -   FabricDelete()._get_fabrics_to_delete() calls
        FabricDetails().refresh() which returns a dict with keys
        DATA == [{f1 fabric data dict}], RETURN_CODE == 200
    -   FabricDelete()._get_fabrics_to_delete() calls
        FabricDelete()._verify_fabric_can_be_deleted() which returns
        successfully (does not raise ``ValueError``)
    -   FabricDelete()._get_fabrics_to_delete() sets
        FabricDelete()._fabrics_to_delete to a list containing fabric f1.
    -   FabricDelete().commit() calls FabricDelete()._send_requests()
    -   FabricDelete._send_requests() sets RestSend() parameters
    -   FabricDelete._send_requests() calls FabricDelete._send_request() for
        each fabric in the FabricDelete()._fabrics_to_delete list.
    -   FabricDelete._send_request() calls FabricDelete._set_fabric_delete_endpoint()
        which calls EpFabricDelete().fabric_name setter, which is mocked to raise
        ``ValueError``.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    class MockEpFabricDelete:  # pylint: disable=too-few-public-methods
        """
        Mock the EpFabricDelete.path property to raise ``ValueError``.
        """

        @property
        def fabric_name(self):
            """
            Mocked property getter
            """

        @fabric_name.setter
        def fabric_name(self, value):
            """
            Mocked property setter
            """
            msg = "mocked MockEpFabricDelete().fabric_name setter exception."
            raise ValueError(msg)

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
        yield responses_fabric_summary(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance = fabric_delete
        monkeypatch.setattr(instance, "ep_fabric_delete", MockEpFabricDelete())
        instance.fabric_names = ["f1"]

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()

    match = r"mocked MockEpFabricDelete\(\)\.fabric_name setter exception\."
    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 2
    assert len(instance.results.metadata) == 2
    assert len(instance.results.response) == 2
    assert len(instance.results.result) == 2

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[1].get("sequence_number", None) == 2

    assert instance.results.metadata[0].get("action", None) == "delete"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "deleted"

    assert instance.results.metadata[1].get("action", None) == "delete"
    assert instance.results.metadata[1].get("check_mode", None) is False
    assert instance.results.metadata[1].get("sequence_number", None) == 2
    assert instance.results.metadata[1].get("state", None) == "deleted"

    assert instance.results.response[0].get("sequence_number", None) == 1
    assert instance.results.response[1].get("sequence_number", None) == 2

    assert instance.results.result[0].get("sequence_number", None) == 1
    assert instance.results.result[1].get("sequence_number", None) == 2

    assert True in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_delete_00043(monkeypatch, fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
        - payloads setter
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricDelete
        - __init__()
        - commit()

    Summary
    -   Verify successful fabric delete code path (fabric does not exist).
    -   The user attempts to delete a fabric and the fabric does not exist
        on the controller.

    Code Flow
    -   FabricDelete.commit() calls FabricDelete()._validate_commit_parameters()
        which succeeds since all required parameters are set.
    -   FabricDelete.commit() calls FabricDelete()._get_fabrics_to_delete()
    -   FabricDelete()._get_fabrics_to_delete() calls
        FabricDetails().refresh() which returns a dict with keys
        DATA == [], RETURN_CODE == 200
    -   FabricDelete()._get_fabrics_to_delete() sets
        FabricDelete()._fabrics_to_delete to an empty list.
    -   FabricDelete().commit() sets results and calls register_result().
    -   FabricDelete().register_result() registers the results of the fabric
        delete operation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
        yield responses_fabric_summary(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_delete
        instance.fabric_names = ["f1"]

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)
    with does_not_raise():
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[0].get("fabric_name", None) is None

    assert instance.results.metadata[0].get("action", None) == "delete"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "deleted"

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.response[0].get("MESSAGE", None) == "No fabrics to delete"

    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_delete_00044(monkeypatch, fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
        - payloads setter
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricDelete
        - __init__()
        - commit()

    Summary
    -   Verify unsuccessful fabric delete code path.
    -   The user attempts to delete a fabric and the fabric exists on the
        controller, and the fabric is empty, but the controller
        RETURN_CODE is not 200.

    Code Flow
    -   FabricDelete.commit() calls FabricDelete()._validate_commit_parameters()
        which succeeds since all required parameters are set.
    -   FabricDelete.commit() calls FabricDelete()._get_fabrics_to_delete()
    -   FabricDelete()._get_fabrics_to_delete() calls
        FabricDetails().refresh() which returns a dict with keys
        DATA == [{f1 fabric data dict}], RETURN_CODE == 200
    -   FabricDelete()._get_fabrics_to_delete() calls
        FabricDelete()._verify_fabric_can_be_deleted() which returns
        successfully (does not raise ``ValueError``)
    -   FabricDelete()._get_fabrics_to_delete() sets
        FabricDelete()._fabrics_to_delete to a list containing fabric f1.
    -   FabricDelete().commit() calls FabricDelete()._send_requests()
    -   FabricDelete._send_requests() sets RestSend() parameters
    -   FabricDelete._send_requests() calls FabricDelete._send_request() for
        each fabric in the FabricDelete()._fabrics_to_delete list.
    -   FabricDelete._send_request() calls FabricDelete._set_fabric_delete_endpoint()
        which returns the request endpoint information (path, verb) for fabric f1.
    -   FabricDelete._send_request() sets RestSend().path and RestSend().verb and
        calls RestSend().commit(), which sends the request.
    -   The response includes a RETURN_CODE != 200
    -   FabricDelete()._send_request() calls FabricDelete().register_result()
    -   FabricDelete().register_result() sets the results for the fabric
        delete operation.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
        yield responses_fabric_summary(key)
        yield responses_fabric_delete(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_delete
        instance.fabric_names = ["f1"]

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)
    with does_not_raise():
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1

    assert instance.results.metadata[0].get("action", None) == "delete"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "deleted"

    assert instance.results.response[0].get("RETURN_CODE", None) == 500

    msg = "Failed to delete fabric f1."
    assert instance.results.response[0].get("DATA", None) == msg
    assert instance.results.response[0].get("METHOD", None) == "DELETE"

    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is False

    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_delete_00050(monkeypatch, fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
        - payloads setter
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricDelete
        - __init__()
        - commit()
        - _verify_fabric_can_be_deleted()

    Summary
    -   Verify unsuccessful fabric delete code path.
    -   FabricDelete()._verify_fabric_can_be_deleted() raises ``ValueError``
        because fabric is not empty.
    -   The user attempts to delete a fabric and the fabric exists on the
        controller, and the fabric is not empty.

    Code Flow
    -   FabricDelete.commit() calls FabricDelete()._validate_commit_parameters()
        which succeeds since all required parameters are set.
    -   FabricDelete.commit() calls FabricDelete()._get_fabrics_to_delete()
    -   FabricDelete()._get_fabrics_to_delete() calls
        FabricDetails().refresh() which returns a dict with keys
        DATA == [{f1 fabric data dict}], RETURN_CODE == 200
    -   FabricDelete()._get_fabrics_to_delete() calls
        FabricDelete()._verify_fabric_can_be_deleted() raises ``ValueError``
        since the fabric is not empty.
    -   FabricDelete()._get_fabrics_to_delete() re-raises ``ValueError``
    -   FabricDelete().commit() catches the ``ValueError``, sets
        the (failed) results for the fabric delete operation, and calls
        self.register_result(None)
    -   FabricDelete().register_result() sets the final result for the
        fabric delete operation and returns.
    -   FabricDelete().commit() re-raises the ``ValueError`` which is caught
        by the main Task(), in real life, but caught by the test here.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
        yield responses_fabric_summary(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_delete
        instance.fabric_names = ["f1"]

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    match = r"FabricDelete\._verify_fabric_can_be_deleted: "
    match += "Fabric f1 cannot be deleted since it is not empty. "
    match += "Remove all devices from the fabric and try again."
    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[0].get("fabric_name", None) is None

    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is False

    assert instance.results.metadata[0].get("action", None) == "delete"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "deleted"

    assert instance.results.response[0].get("RETURN_CODE", None) is None


def test_fabric_delete_00051(monkeypatch, fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
        - payloads setter
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName()
        - __init__()
        - refresh()
    - FabricDelete
        - __init__()
        - commit()
        - _verify_fabric_can_be_deleted()

    Summary
    -   Verify unsuccessful fabric delete code path.
    -   FabricDelete()._verify_fabric_delete() re-raises ``ValueError``
        because FabricSummary().refresh() raises ``ControllerResponseError``.

    Code Flow
    -   FabricDelete.commit() calls FabricDelete()._validate_commit_parameters()
        which succeeds since all required parameters are set.
    -   FabricDelete.commit() calls FabricDelete()._get_fabrics_to_delete()
    -   FabricDelete()._get_fabrics_to_delete() calls
        FabricDetails().refresh() which returns a dict with keys
        DATA == [{f1 fabric data dict}], RETURN_CODE == 200
    -   FabricDelete()._get_fabrics_to_delete() calls
        FabricDelete()._verify_fabric_can_be_deleted() which calls
        FabricSummary().refresh() which raises ``ControllerResponseError``
        due to a 404 RETURN_CODE.
    -   FabricDelete()._verify_fabric_can_be_deleted() re-raises the
        ``ControllerResponseError`` and a ``ValueError``.
    -   FabricDelete()._get_fabrics_to_delete() re-raises the ``ValueError``.
    -   FabricDelete().commit() catches the ``ValueError``, sets
        the (failed) results for the fabric delete operation, and calls
        self.register_result(None)
    -   FabricDelete().register_result() sets the final result for the
        fabric delete operation and returns.
    -   FabricDelete().commit() re-raises the ``ValueError`` which is caught
        by the main Task() in real life, but caught by the test here.
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)
        yield responses_fabric_summary(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_delete
        instance.fabric_names = ["f1"]

        instance.fabric_details = FabricDetailsByName(params)
        instance.fabric_details.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_details.rest_send.unit_test = True

        instance.fabric_summary = FabricSummary(params)
        instance.fabric_summary.rest_send = RestSend(MockAnsibleModule())
        instance.fabric_summary.rest_send.unit_test = True

        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True

        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    match = r"FabricSummary\._verify_controller_response:\s+"
    match += r"Failed to retrieve fabric_summary for fabric_name f1.\s+"
    match += r"RETURN_CODE: 404.\s+"
    match += r"MESSAGE: Not Found\."
    with pytest.raises(ValueError, match=match):
        instance.commit()

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert True in instance.results.failed
    assert False not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed

    assert len(instance.results.diff) == 1
    assert len(instance.results.metadata) == 1
    assert len(instance.results.response) == 1
    assert len(instance.results.result) == 1

    assert instance.results.diff[0].get("sequence_number", None) == 1
    assert instance.results.diff[0].get("fabric_name", None) is None

    assert instance.results.result[0].get("changed", None) is False
    assert instance.results.result[0].get("success", None) is False

    assert instance.results.metadata[0].get("action", None) == "delete"
    assert instance.results.metadata[0].get("check_mode", None) is False
    assert instance.results.metadata[0].get("sequence_number", None) == 1
    assert instance.results.metadata[0].get("state", None) == "deleted"

    assert instance.results.response[0].get("RETURN_CODE", None) is None


def test_fabric_delete_00060(fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricDelete
        - __init__()
        - commit()
        - _validate_commit_parameters()

    Summary
    -   Verify that ``ValueError`` is raised because fabric_names
        is not a list.
    """
    with does_not_raise():
        instance = fabric_delete

    match = r"FabricDelete\.fabric_names: "
    match += r"fabric_names must be a list\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_names = "NOT_A_LIST"


def test_fabric_delete_00061(fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricDelete
        - __init__()
        - commit()
        - _validate_commit_parameters()

    Summary
    -   Verify that ``ValueError`` is raised because fabric_names is an
        empty list.
    """
    with does_not_raise():
        instance = fabric_delete
        # instance.rest_send = RestSend(MockAnsibleModule())

    match = r"FabricDelete\.fabric_names: "
    match += r"fabric_names must be a list of at least one string. got \[\]\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_names = []


def test_fabric_delete_00062(fabric_delete) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricDelete
        - __init__()
        - commit()
        - _validate_commit_parameters()

    Summary
    -   Verify that ``ValueError`` is raised because fabric_names is a
        list containing non-string elements.
    """
    with does_not_raise():
        instance = fabric_delete

    match = r"FabricDelete\.fabric_names: "
    match += r"fabric_names must be a list of strings\."
    with pytest.raises(ValueError, match=match):
        instance.fabric_names = ["MyFabric", 123]
