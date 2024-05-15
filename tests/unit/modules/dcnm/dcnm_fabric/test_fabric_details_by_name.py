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
from ansible_collections.cisco.dcnm.plugins.module_utils.common.api.v1.rest.control.fabrics import \
    EpFabrics
from ansible_collections.cisco.dcnm.plugins.module_utils.common.conversion import \
    ConversionUtils
from ansible_collections.cisco.dcnm.plugins.module_utils.common.rest_send import \
    RestSend
from ansible_collections.cisco.dcnm.plugins.module_utils.common.results import \
    Results
from ansible_collections.cisco.dcnm.tests.unit.modules.dcnm.dcnm_fabric.utils import (
    MockAnsibleModule, ResponseGenerator, does_not_raise,
    fabric_details_by_name_fixture, responses_fabric_details_by_name)


def test_fabric_details_by_name_00010(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon
        - __init__()
    - FabricDetails
        - __init__()
    - FabricDetailsByName
        - __init__()

    Test
    - Class attributes are initialized to expected values
    - Exception is not raised
    """
    with does_not_raise():
        instance = fabric_details_by_name
    assert instance.class_name == "FabricDetailsByName"
    assert instance.data == {}
    assert instance.data_subclass == {}
    assert instance._properties["filter"] is None
    assert isinstance(instance.ep_fabrics, EpFabrics)
    assert isinstance(instance.results, Results)
    assert isinstance(instance.conversion, ConversionUtils)


def test_fabric_details_by_name_00030(monkeypatch, fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName
        - __init__()
        - refresh()

    Summary
    - Verify FabricDetailsByName.refresh() behavior when:
        - RETURN_CODE is 200.
        - DATA is an empty list, indicating no fabrics
          exist on the controller.

    Code Flow - Setup
    -   FabricDetailsByName() is instantiated
    -   FabricDetails().RestSend() is instantiated
    -   FabricDetails().Results() is instantiated
    -   FabricDetailsByName().refresh() is called
    -   FabricDetailsByName().refresh() calls FabricDetails().refresh_super()
    -   FabricDetails().refresh_super() calls RestSend() and updates Results()
    -   FabricDetailsByName().refresh() updates FabricDetailsByName().data_subclass
        with a copy of FabricDetails().data
    -   responses_FabricDetailsByName contains a dict with:
        - RETURN_CODE == 200
        - DATA == []

    Code Flow - Test
    -   FabricDetailsByName().refresh() is called

    Expected Result
    -   Exception is not raised
    -   Results() are updated
    -   FabricDetailsByName().data_subclass is updated with FabricDetails().data
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_details_by_name
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True
        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
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


def test_fabric_details_by_name_00031(monkeypatch, fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName
        - __init__()
        - refresh()

    Summary
    - Verify FabricDetailsByName.refresh() behavior when:
        -   RETURN_CODE is 200.
        -   DATA is missing (negative test)

    Code Flow - Setup
    -   FabricDetailsByName() is instantiated
    -   FabricDetails().RestSend() is instantiated
    -   FabricDetails().Results() is instantiated
    -   FabricDetailsByName().refresh() is called
    -   FabricDetailsByName().refresh() calls FabricDetails().refresh_super()
    -   FabricDetails().refresh_super() calls RestSend() and updates Results()
    -   FabricDetailsByName().refresh() updates FabricDetailsByName().data_subclass
        with a copy of FabricDetails().data
    -   responses_FabricDetailsByName contains a dict with:
        - RETURN_CODE == 200
        - DATA is missing

    Code Flow - Test
    -   FabricDetailsByName().refresh() is called

    Expected Result
    -   Exception is not raised
    -   Results() are updated
    -   FabricDetailsByName().data_subclass is updated with FabricDetails().data
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_details_by_name
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True
        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
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


def test_fabric_details_by_name_00032(monkeypatch, fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
        - refresh_super()
    - FabricDetailsByName
        - __init__()
        - refresh()

    Summary
    - Verify refresh() behavior when:
        -   RETURN_CODE is 200.
        -   Controller response contains one fabric (f1).

    Code Flow - Setup
    -   FabricDetailsByName() is instantiated
    -   FabricDetails().RestSend() is instantiated
    -   FabricDetails().Results() is instantiated
    -   FabricDetailsByName().refresh() is called
    -   FabricDetailsByName().refresh() calls FabricDetails().refresh_super()
    -   FabricDetails().refresh_super() calls RestSend() and updates Results()
    -   FabricDetailsByName().refresh() updates FabricDetailsByName().data_subclass
        with a copy of FabricDetails().data
    -   responses_FabricDetailsByName contains a dict with:
        - RETURN_CODE == 200
        - DATA == [<fabric_info from controller>]

    Code Flow - Test
    -   FabricDetailsByName().refresh() is called

    Expected Result
    -   Exception is not raised
    -   Results() are updated
    -   FabricDetailsByName().data_subclass is updated with FabricDetails().data
    """
    method_name = inspect.stack()[0][3]
    key = f"{method_name}a"

    PATCH_DCNM_SEND = "ansible_collections.cisco.dcnm.plugins."
    PATCH_DCNM_SEND += "module_utils.common.rest_send.dcnm_send"

    def responses():
        yield responses_fabric_details_by_name(key)

    gen = ResponseGenerator(responses())

    def mock_dcnm_send(*args, **kwargs):
        item = gen.next
        return item

    with does_not_raise():
        instance = fabric_details_by_name
        instance.rest_send = RestSend(MockAnsibleModule())
        instance.rest_send.unit_test = True
        instance.results = Results()

    monkeypatch.setattr(PATCH_DCNM_SEND, mock_dcnm_send)

    with does_not_raise():
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


def test_fabric_details_by_name_00040(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - _get()

    Summary
    -   Verify FabricDetails()._get() raises ``ValueError`` when ``filter``
        is not set.
    """
    with does_not_raise():
        instance = fabric_details_by_name

    match = r"FabricDetailsByName\._get: "
    match += r"set instance\.filter to a fabric name before accessing property"
    with pytest.raises(ValueError, match=match):
        instance._get("foo")


def test_fabric_details_by_name_00041(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - _get()

    Summary
    -   Verify FabricDetails()._get() raises ``ValueError`` when ``filter``
        does not exist on the controller.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {"YourFabric": "bar"}
        instance.filter = "MyFabric"

    match = r"FabricDetailsByName\._get: "
    match += r"fabric_name MyFabric does not exist on the controller."
    with pytest.raises(ValueError, match=match):
        instance._get("BGP_AS")


def test_fabric_details_by_name_00042(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - _get()

    Summary
    -   Verify FabricDetails()._get() raises ``ValueError`` when the fabric
        specified by ``filter`` exists on the controller, but does not contain
        the requested property.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {"MyFabric": {"bar": "baz"}}
        instance.filter = "MyFabric"

    match = r"FabricDetailsByName\._get: "
    match += r"MyFabric unknown property name: foo."
    with pytest.raises(ValueError, match=match):
        instance._get("foo")


def test_fabric_details_by_name_00043(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - _get()

    Summary
    -   Verify FabricDetails()._get() retrieves the requested property when
        the fabric specified by ``filter`` exists on the controller, and it
        contains the requested property.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {"MyFabric": {"bar": "baz"}}
        instance.filter = "MyFabric"
        value = instance._get("bar")
    assert value == "baz"


def test_fabric_details_by_name_00050(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - _get_nv_pair()

    Summary
    -   Verify FabricDetails()._get_nv_pair() raises ``ValueError`` when ``filter``
        is not set.
    """
    with does_not_raise():
        instance = fabric_details_by_name

    match = r"FabricDetailsByName\._get_nv_pair: "
    match += r"set instance\.filter to a fabric name before accessing property"
    with pytest.raises(ValueError, match=match):
        instance._get_nv_pair("foo")


def test_fabric_details_by_name_00051(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - _get_nv_pair()

    Summary
    -   Verify FabricDetails()._get_nv_pair() raises ``ValueError`` when ``filter``
        does not exist on the controller.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {"YourFabric": "bar"}
        instance.filter = "MyFabric"

    match = r"FabricDetailsByName\._get_nv_pair: "
    match += r"fabric_name MyFabric does not exist on the controller."
    with pytest.raises(ValueError, match=match):
        instance._get_nv_pair("BGP_AS")


def test_fabric_details_by_name_00052(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - _get_nv_pair()

    Summary
    -   Verify FabricDetails()._get_nv_pair() raises ``ValueError`` when the fabric
        specified by ``filter`` exists on the controller, but does not contain
        the requested property.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {"MyFabric": {"nvPairs": {"BGP_AS": "65001"}}}
        instance.filter = "MyFabric"

    match = r"FabricDetailsByName\._get_nv_pair: "
    match += r"fabric_name MyFabric unknown property name: FOO_NV_PAIR."
    with pytest.raises(ValueError, match=match):
        instance._get_nv_pair("FOO_NV_PAIR")


def test_fabric_details_by_name_00053(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - _get_nv_pair()

    Summary
    -   Verify FabricDetails()._get_nv_pair() retrieves the requested property when
        the fabric specified by ``filter`` exists on the controller, and it
        contains the requested property.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {"MyFabric": {"nvPairs": {"BGP_AS": "65001"}}}
        instance.filter = "MyFabric"
        value = instance._get_nv_pair("BGP_AS")
    assert value == "65001"


def test_fabric_details_by_name_00060(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - _filtered_data getter

    Summary
    -   Verify FabricDetailsByName().filtered_data raises ``ValueError``
        if FabricDetailsByName().filter is not set.
    """
    with does_not_raise():
        instance = fabric_details_by_name
    match = r"FabricDetailsByName\.filtered_data: "
    match += r"FabricDetailsByName\.filter must be set before calling "
    match += r"FabricDetailsByName\.filtered_data"
    with pytest.raises(ValueError, match=match):
        instance.filtered_data  # pylint: disable=pointless-statement


def test_fabric_details_by_name_00061(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - _filtered_data getter

    Summary
    -   Verify FabricDetailsByName().filtered_data returns the expected
        data when FabricDetailsByName().filter is set.
    -   Verify ``ValueError`` is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {"MyFabric": {"nvPairs": {"BGP_AS": "65001"}}}
        instance.filter = "MyFabric"
        value = instance.filtered_data
    assert value == {"nvPairs": {"BGP_AS": "65001"}}


def test_fabric_details_by_name_00070(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - asn getter

    Summary
    -   Verify FabricDetailsByName().asn returns None
        if encountering an error retrieving the asn property
    -   Verify exception is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.filter = "MyFabric"
        instance.data_subclass = {"MyFabric": {"nvPairs": {"BGP_AS": "65001"}}}
        value = instance.asn
    assert value is None


def test_fabric_details_by_name_00071(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - asn getter

    Summary
    -   Verify FabricDetailsByName().asn returns the expected
        data when FabricDetailsByName().filter is set.
    -   Verify ``ValueError`` is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {"MyFabric": {"asn": "65001"}}
        instance.filter = "MyFabric"
        value = instance.asn
    assert value == "65001"


def test_fabric_details_by_name_00080(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - enable_pbr getter

    Summary
    -   Verify FabricDetailsByName().enable_pbr returns None
        if encountering an error retrieving the nvPairs.ENABLE_PBR
        property.
    -   Verify exception is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.filter = "MyFabric"
        instance.data_subclass = {"MyFabric": {"nvPairs": {"BGP_AS": "65001"}}}
        value = instance.enable_pbr
    assert value is None


def test_fabric_details_by_name_00081(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - enable_pbr getter

    Summary
    -   Verify FabricDetailsByName().enable_pbr returns the expected
        data when FabricDetailsByName().filter is set.
    -   Verify ``ValueError`` is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {"MyFabric": {"nvPairs": {"ENABLE_PBR": "true"}}}
        instance.filter = "MyFabric"
        value = instance.enable_pbr
    assert value is True


def test_fabric_details_by_name_00090(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - fabric_id getter

    Summary
    -   Verify FabricDetailsByName().fabric_id returns None
        if encountering an error retrieving the fabric_id
        property.
    -   Verify exception is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.filter = "MyFabric"
        instance.data_subclass = {"MyFabric": {"nvPairs": {"BGP_AS": "65001"}}}
        value = instance.fabric_id
    assert value is None


def test_fabric_details_by_name_00091(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - fabric_id getter

    Summary
    -   Verify FabricDetailsByName().fabric_id returns the expected
        data when FabricDetailsByName().filter is set.
    -   Verify ``ValueError`` is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {"MyFabric": {"fabricId": "FABRIC-2"}}
        instance.filter = "MyFabric"
        value = instance.fabric_id
    assert value == "FABRIC-2"


def test_fabric_details_by_name_00100(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - template_name getter

    Summary
    -   Verify FabricDetailsByName().template_name returns None
        if encountering an error retrieving the templateName
        property.
    -   Verify exception is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.filter = "MyFabric"
        instance.data_subclass = {"MyFabric": {"nvPairs": {"BGP_AS": "65001"}}}
        value = instance.template_name
    assert value is None


def test_fabric_details_by_name_00101(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - template_name getter

    Summary
    -   Verify FabricDetailsByName().replication_mode returns the expected
        data when FabricDetailsByName().filter is set.
    -   Verify ``ValueError`` is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {"MyFabric": {"templateName": "Easy_Fabric"}}
        instance.filter = "MyFabric"
        value = instance.template_name
    assert value == "Easy_Fabric"


def test_fabric_details_by_name_00300(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - fabric_type getter

    Summary
    -   Verify FabricDetailsByName().fabric_type returns None
        if encountering an error retrieving the nvPairs.FABRIC_TYPE
        property.
    -   Verify exception is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.filter = "MyFabric"
        instance.data_subclass = {"MyFabric": {"nvPairs": {"BGP_AS": "65001"}}}
        value = instance.fabric_type
    assert value is None


def test_fabric_details_by_name_00301(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - fabric_type getter

    Summary
    -   Verify FabricDetailsByName().fabric_type returns the expected
        data when FabricDetailsByName().filter is set.
    -   Verify ``ValueError`` is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {
            "MyFabric": {"nvPairs": {"FABRIC_TYPE": "Switch_Fabric"}}
        }
        instance.filter = "MyFabric"
        value = instance.fabric_type
    assert value == "Switch_Fabric"


def test_fabric_details_by_name_00310(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - replication_mode getter

    Summary
    -   Verify FabricDetailsByName().replication_mode returns None
        if encountering an error retrieving the nvPairs.REPLICATION_MODE
        property.
    -   Verify exception is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.filter = "MyFabric"
        instance.data_subclass = {"MyFabric": {"nvPairs": {"BGP_AS": "65001"}}}
        value = instance.replication_mode
    assert value is None


def test_fabric_details_by_name_00311(fabric_details_by_name) -> None:
    """
    Classes and Methods
    - FabricCommon()
        - __init__()
    - FabricDetails()
        - __init__()
    - FabricDetailsByName
        - __init__()
        - replication_mode getter

    Summary
    -   Verify FabricDetailsByName().replication_mode returns the expected
        data when FabricDetailsByName().filter is set.
    -   Verify ``ValueError`` is not raised.
    """
    with does_not_raise():
        instance = fabric_details_by_name
        instance.data_subclass = {
            "MyFabric": {"nvPairs": {"REPLICATION_MODE": "Ingress"}}
        }
        instance.filter = "MyFabric"
        value = instance.replication_mode
    assert value == "Ingress"
