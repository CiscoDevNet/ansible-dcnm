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
    EpFabrics
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    ResponseGenerator
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, does_not_raise, fabric_details_by_nv_pair_fixture,
    responses_fabric_details_by_nv_pair)


def test_fabric_details_by_nv_pair_00010(fabric_details_by_nv_pair) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricDetails
        - __init__()
    - FabricDetailsByNvPair
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_details_by_nv_pair
    assert instance.class_name == "FabricDetailsByNvPair"
    assert instance.data == {}
    assert instance.data_subclass == {}
    assert instance._properties["filter_key"] is None
    assert instance._properties["filter_value"] is None
    assert isinstance(instance.ep_fabrics, EpFabrics)
    assert isinstance(instance.results, Results)
    assert isinstance(instance.conversion, ConversionUtils)


def test_fabric_details_by_nv_pair_00030(
    monkeypatch, fabric_details_by_nv_pair
) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByNvPair
        - __init__()
        - refresh()

    Summary
    - Verify FabricDetailsByNvPair.refresh() behavior when:
        - RETURN_CODE is 200.
        - DATA is an empty list, indicating no fabrics
          exist on the controller.

    Code Flow - Setup
    -   FabricDetailsByNvPair() is instantiated
    -   FabricDetails().RestSend() is instantiated
    -   FabricDetails().Results() is instantiated
    -   FabricDetailsByNvPair().refresh() is called
    -   FabricDetailsByNvPair().refresh() calls FabricDetails().refresh_super()
    -   FabricDetails().refresh_super() calls RestSend() and updates Results()
    -   FabricDetailsByNvPair().refresh() updates FabricDetailsByNvPair().data_subclass
        with a copy of FabricDetails().data
    -   responses_FabricDetailsByNvPair contains a dict with:
        - RETURN_CODE == 200
        - DATA == []

    Code Flow - Test
    -   FabricDetailsByNvPair().filter_key is set
    -   FabricDetailsByNvPair().filter_value is set
    -   FabricDetailsByNvPair().refresh() is called

    Expected Result
    -   Exception is not raised
    -   Results() are updated
    -   FabricDetailsByNvPair().data_subclass is updated with FabricDetails().data
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_nv_pair(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_details_by_nv_pair
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True
        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.filter_key = "FABRIC_NAME"
        instance.filter_value = "f1"
        instance.refresh()

    assert instance.data_subclass == instance.data

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 0
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_details_by_nv_pair_00031(
    monkeypatch, fabric_details_by_nv_pair
) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByNvPair
        - __init__()
        - refresh()

    Summary
    - Verify FabricDetailsByNvPair.refresh() behavior when:
        -   RETURN_CODE is 200.
        -   DATA is missing (negative test)

    Code Flow - Setup
    -   FabricDetailsByNvPair() is instantiated
    -   FabricDetails().RestSend() is instantiated
    -   FabricDetails().Results() is instantiated
    -   FabricDetailsByNvPair().refresh() is called
    -   FabricDetailsByNvPair().refresh() calls FabricDetails().refresh_super()
    -   FabricDetails().refresh_super() calls RestSend() and updates Results()
    -   FabricDetailsByNvPair().refresh() updates FabricDetailsByNvPair().data_subclass
        with a copy of FabricDetails().data
    -   responses_FabricDetailsByNvPair contains a dict with:
        - RETURN_CODE == 200
        - DATA is missing

    Code Flow - Test
    -   FabricDetailsByNvPair().filter_key is set
    -   FabricDetailsByNvPair().filter_value is set
    -   FabricDetailsByNvPair().refresh() is called

    Expected Result
    -   Exception is not raised
    -   Results() are updated
    -   FabricDetailsByNvPair().data_subclass is updated with FabricDetails().data
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_nv_pair(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_details_by_nv_pair
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True
        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.filter_key = "FABRIC_NAME"
        instance.filter_value = "f1"
        instance.refresh()

    assert instance.data_subclass == instance.data

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 0
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed


def test_fabric_details_by_nv_pair_00032(
    monkeypatch, fabric_details_by_nv_pair
) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByNvPair
        - __init__()
        - refresh()

    Summary
    - Verify refresh() behavior when:
        -   RETURN_CODE is 200.
        -   Controller response contains one fabric (f1).

    Code Flow - Setup
    -   FabricDetailsByNvPair() is instantiated
    -   FabricDetails().RestSend() is instantiated
    -   FabricDetails().Results() is instantiated
    -   FabricDetailsByNvPair().refresh() is called
    -   FabricDetailsByNvPair().refresh() calls FabricDetails().refresh_super()
    -   FabricDetails().refresh_super() calls RestSend() and updates Results()
    -   FabricDetailsByNvPair().refresh() updates FabricDetailsByNvPair().data_subclass
        with a copy of FabricDetails().data
    -   responses_FabricDetailsByNvPair contains a dict with:
        - RETURN_CODE == 200
        - DATA == [<fabric_info from controller>]

    Code Flow - Test
    -   FabricDetailsByNvPair().filter_key is set
    -   FabricDetailsByNvPair().filter_value is set
    -   FabricDetailsByNvPair().refresh() is called

    Expected Result
    -   Exception is not raised
    -   Results() are updated
    -   FabricDetailsByNvPair().data_subclass is updated with FabricDetails().data
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_nv_pair(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_details_by_nv_pair
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True
        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.filter_key = "FABRIC_NAME"
        instance.filter_value = "f1"
        instance.refresh()

    assert instance.data_subclass == instance.data

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 0
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed

    assert instance.all_data.get("f1", {}).get("asn", None) == "65001"
    assert instance.all_data.get("f1", {}).get("nvPairs", {}).get("FABRIC_NAME") == "f1"


def test_fabric_details_by_nv_pair_00033(fabric_details_by_nv_pair) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByNvPair
        - __init__()
        - refresh()

    Summary
    -   Verify FabricDetails().refresh() raises ``ValueError`` when
        ``filter_key`` is not set.
    """
    with does_not_raise():
        instance = fabric_details_by_nv_pair
        instance.filter_value = "f1"

    match = r"FabricDetailsByNvPair\.refresh: "
    match += r"set FabricDetailsByNvPair\.filter_key to a nvPair key "
    match += r"before calling FabricDetailsByNvPair\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_fabric_details_by_nv_pair_00034(fabric_details_by_nv_pair) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByNvPair
        - __init__()
        - refresh()

    Summary
    -   Verify FabricDetails().refresh() raises ``ValueError`` when
        ``filter_value`` is not set.
    """
    with does_not_raise():
        instance = fabric_details_by_nv_pair
        instance.filter_key = "BGP_AS"

    match = r"FabricDetailsByNvPair\.refresh: "
    match += r"set FabricDetailsByNvPair\.filter_value to a nvPair value "
    match += r"before calling FabricDetailsByNvPair\.refresh\(\)\."
    with pytest.raises(ValueError, match=match):
        instance.refresh()


def test_fabric_details_by_nv_pair_00040(
    monkeypatch, fabric_details_by_nv_pair
) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByNvPair
        - __init__()
        - refresh()
        - filtered_data

    Summary
    -   Verify FabricDetailsByNvPair.filtered_data returns only fabrics which
        match the filter_key and filter_value.

    Code Flow - Setup
    -   FabricDetailsByNvPair() is instantiated
    -   FabricDetails().RestSend() is instantiated
    -   FabricDetails().Results() is instantiated
    -   FabricDetailsByNvPair().filter_key is set
    -   FabricDetailsByNvPair().filter_value is set
    -   FabricDetailsByNvPair().refresh() is called
    -   FabricDetailsByNvPair().refresh() calls FabricDetails().refresh_super()
    -   FabricDetails().refresh_super() calls RestSend() and updates Results()
    -   FabricDetails().refresh_super() updates FabricDetails().data
    -   FabricDetailsByNvPair().refresh() updates FabricDetailsByNvPair().data_subclass
        with fabrics from FabricDetails().data that match the filter_key and filter_value
    -   responses_FabricDetailsByNvPair contains a dict with:
        - RETURN_CODE == 200
        - DATA == [<fabric_info from controller>]

    Code Flow - Test
    -   FabricDetailsByNvPair().filter_key is set
    -   FabricDetailsByNvPair().filter_value is set
    -   FabricDetailsByNvPair().refresh() is called

    Expected Result
    -   Exception is not raised
    -   Results() are updated
    -   FabricDetailsByNvPair().data_subclass is updated with matching
        fabrics from FabricDetails().data
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_nv_pair(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_details_by_nv_pair
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True
        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
        instance.filter_key = "REPLICATION_MODE"
        instance.filter_value = "Ingress"
        instance.refresh()

    # Both fabrics are in instance.data
    assert "IR-Fabric" in instance.data
    assert "MC-Fabric" in instance.data

    # instance.data_subclass only contains the fabric that matches the filter
    assert instance.data_subclass != instance.data
    assert len(instance.data_subclass) == 1
    assert "IR-Fabric" in instance.data_subclass

    # instance.filtered_data property returns contents of
    # instance.data_subclass so will contain only the fabric
    # that matches the filter
    assert "IR-Fabric" in instance.filtered_data
    assert "MC-Fabric" not in instance.filtered_data

    assert isinstance(instance.results.diff, list)
    assert isinstance(instance.results.result, list)
    assert isinstance(instance.results.response, list)

    assert len(instance.results.diff) == 0
    assert len(instance.results.result) == 1
    assert len(instance.results.response) == 1

    assert instance.results.response[0].get("RETURN_CODE", None) == 200
    assert instance.results.result[0].get("found", None) is True
    assert instance.results.result[0].get("success", None) is True

    assert False in instance.results.failed
    assert True not in instance.results.failed
    assert False in instance.results.changed
    assert True not in instance.results.changed

    assert (
        instance.all_data.get("MC-Fabric", {}).get("nvPairs", {}).get("BGP_AS")
        == "65001"
    )
    assert (
        instance.all_data.get("IR-Fabric", {}).get("nvPairs", {}).get("BGP_AS")
        == "65002"
    )
