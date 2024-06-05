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


class MockSwitchDetails:
    """
    Mock the SwitchDetails class
    """

    def __init__(self) -> None:

        def null_mock_exception():
            pass

        self.class_name = "SwitchDetails"
        self._mock_class = None
        self._mock_exception = null_mock_exception
        self._mock_message = None
        self._mock_property = None

        self._rest_send = None
        self._results = None
        self._serial_number = None
        self._fabric_name = None
        self._freeze_mode = None
        self._maintenance_mode = None
        self._switch_role = None

    def refresh(self):
        """
        Mocked refresh method
        """

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
    def rest_send(self):
        """
        Mocked rest_send property
        """
        return self._rest_send

    @rest_send.setter
    def rest_send(self, value):
        if self.mock_class == self.class_name and self.mock_property == "rest_send":
            raise self.mock_exception(self.mock_message)
        self._rest_send = value

    @property
    def results(self):
        """
        Mocked results property
        """
        return self._results

    @results.setter
    def results(self, value):
        if self.mock_class == self.class_name and self.mock_property == "results":
            raise self.mock_exception(self.mock_message)
        self._results = value

    @property
    def fabric_name(self):
        """
        Mocked fabric_name property
        """
        return self._fabric_name

    @property
    def freeze_mode(self):
        """
        Mocked freeze_mode property
        """
        return self._freeze_mode

    @property
    def maintenance_mode(self):
        """
        Mocked maintenance_mode property
        """
        return self._maintenance_mode

    @property
    def serial_number(self):
        """
        Mocked serial_number property
        """
        return self._serial_number

    @property
    def switch_role(self):
        """
        Mocked switch_role property
        """
        return self._switch_role
