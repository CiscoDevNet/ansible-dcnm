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


class MockFabricDetailsByName:
    """
    ### Summary
    Mock the exceptions raised by the methods and properties
    in the ``MockFabricDetailsByName`` class.

    ### NOTES
    -   This class is used to test the exceptions raised by
        ``MockFabricDetailsByName``
    -   This class does NOT simulate the behavior of
        ``MockFabricDetailsByName`` with respect its interaction with the
        controller.  For that, see the ``Sender`` class within
        ``module_utils/common/sender_file.py``,
        and the ``RestSend`` class within ``module_utils/common/rest_send.py``.
    -   Example usage for the ``Sender`` class can be found in
        ``test_maintenance_mode_info_00500`` within
        ``tests/unit/module_utils/common/test_maintenance_mode_info.py``.
    """

    def __init__(self) -> None:

        def null_mock_exception():
            pass

        self.class_name = "FabricDetailsByName"
        self._mock_class = None
        self._mock_exception = null_mock_exception
        self._mock_message = None
        self._mock_property = None

        self._filter = None
        self._info = {}
        self.data_subclass = {}
        self.response = None
        self.response_data = None
        self._rest_send = None
        self._results = None
        self._is_read_only = None

    def refresh(self):
        """
        Mocked refresh method
        """
        if self.mock_class == self.class_name and self.mock_property == "refresh":
            raise self.mock_exception(self.mock_message)

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
        if (
            self.mock_class == self.class_name
            and self.mock_property == "system_mode.setter"
        ):
            raise self.mock_exception(self.mock_message)
        return self._is_read_only

    @is_read_only.setter
    def is_read_only(self, value):
        if (
            self.mock_class == self.class_name
            and self.mock_property == "is_read_only.setter"
        ):
            raise self.mock_exception(self.mock_message)
        self._is_read_only = value
