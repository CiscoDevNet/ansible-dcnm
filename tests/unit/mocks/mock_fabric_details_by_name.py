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

__copyright__ = "Copyright (c) 2024 Cisco and/or its affiliates."
__author__ = "Allen Robel"

from ansible_collections.cisco.dcnm.tests.unit.module_utils.common.common_utils import \
    responses_fabric_details_by_name


class MockFabricDetailsByName:
    """
    Mock the FabricDetailsByName class
    """

    def __init__(self) -> None:

        def null_mock_exception():
            pass

        self.class_name = "FabricDetailsByName"
        self._mock_class = None
        self._mock_exception = null_mock_exception
        self._mock_message = None
        self._mock_property = None
        self._mock_response_key = None

        self._filter = None
        self._info = {}
        self.data_subclass = {}
        self.response = None
        self.response_data = None
        self._rest_send = None
        self._results = None
        self._is_read_only = None

    def _get(self, key):
        """
        Get the value of the key from the info dict.
        """
        return self.data_subclass.get(self.filter, {}).get(key, None)

    def refresh(self):
        """
        Mocked refresh method
        """
        if self.mock_class == self.class_name and self.mock_property == "refresh":
            raise self.mock_exception(self.mock_message)
        if self.mock_response_key is None:
            return
        self.populate_info()

    def populate_info(self):
        """
        Populate the info dict.
        """
        self._info = {}
        self.data_subclass = {}
        self.response = responses_fabric_details_by_name(self.mock_response_key)
        self.response_data = self.response.get("DATA", [])
        for fabric in self.response_data:
            nv_pairs = fabric.get("nvPairs", {})
            fabric_name = nv_pairs.get("FABRIC_NAME", None)
            self._info[fabric_name] = nv_pairs
            self.data_subclass[fabric_name] = nv_pairs

    @property
    def mock_class(self):
        """
        If this matches self.class_name, raise mock_exception.
        """
        return self._mock_class

    @mock_class.setter
    def mock_class(self, value):
        self._mock_class = value

    @property
    def mock_exception(self):
        """
        The exception to raise.
        """
        return self._mock_exception

    @mock_exception.setter
    def mock_exception(self, value):
        self._mock_exception = value

    @property
    def mock_message(self):
        """
        The message to include with the raised mock_exception.
        """
        return self._mock_message

    @mock_message.setter
    def mock_message(self, value):
        self._mock_message = value

    @property
    def mock_property(self):
        """
        The property in which to raise the mock_exception.
        """
        return self._mock_property

    @mock_property.setter
    def mock_property(self, value):
        self._mock_property = value

    @property
    def mock_response_key(self):
        """
        The key used to extract controller response from the mocked response
        in ``responses_FabricDetails.json``.
        """
        return self._mock_response_key

    @mock_response_key.setter
    def mock_response_key(self, value):
        self._mock_response_key = value

    @property
    def filter(self):
        """
        Mocked filter property
        """
        if self.mock_class == self.class_name and self.mock_property == "filter.getter":
            raise self.mock_exception(self.mock_message)
        return self._filter

    @filter.setter
    def filter(self, value):
        if self.mock_class == self.class_name and self.mock_property == "filter.setter":
            raise self.mock_exception(self.mock_message)
        self._filter = value

    @property
    def rest_send(self):
        """
        Mocked rest_send property
        """
        if (
            self.mock_class == self.class_name
            and self.mock_property == "rest_send.getter"
        ):
            raise self.mock_exception(self.mock_message)
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value):
        if (
            self.mock_class == self.class_name
            and self.mock_property == "rest_send.setter"
        ):
            raise self.mock_exception(self.mock_message)
        self._rest_send = value

    @property
    def results(self):
        """
        Mocked results property
        """
        if (
            self.mock_class == self.class_name
            and self.mock_property == "results.getter"
        ):
            raise self.mock_exception(self.mock_message)
        return self._results

    @results.setter
    def results(self, value):
        if (
            self.mock_class == self.class_name
            and self.mock_property == "results.setter"
        ):
            raise self.mock_exception(self.mock_message)
        self._results = value

    @property
    def is_read_only(self):
        """
        Mocked is_read_only property
        """
        return self._get("IS_READ_ONLY")
