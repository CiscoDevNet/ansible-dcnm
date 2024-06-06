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
    responses_switch_details


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
        self._mock_response_key = None

        self.response = None
        self.response_data = None

        self._filter = None
        self._info = {}
        self._fabric_name = None
        self._freeze_mode = None
        self._maintenance_mode = None
        self._mode = None
        self._rest_send = None
        self._results = None
        self._serial_number = None
        self._switch_role = None
        self._system_mode = None

    def refresh(self):
        """
        Mocked refresh method
        """
        if self.mock_class == self.class_name and self.mock_property == "refresh":
            raise self.mock_exception(self.mock_message)

    def populate_info(self):
        """
        Populate the info dict.
        """
        self._info = {}
        self.response = responses_switch_details(self.mock_response_key)
        self.response_data = self.response.get("DATA", [])
        for switch in self.response_data:
            self._info[switch["ipAddress"]] = switch

    def populate_mocked_properties(self):
        """
        Set the mocked property values from the contents of the mocked response.
        """
        if self.mock_response_key:
            self.populate_info()
            if self.filter is None:
                raise ValueError(
                    "filter must be set before calling populate_mocked_properties()"
                )

            self.serial_number = self._info.get(self.filter, {}).get("serialNumber")
            self.fabric_name = self._info.get(self.filter, {}).get("fabricName")
            self.freeze_mode = self._info.get(self.filter, {}).get("freezeMode")
            self.mode = self._info.get(self.filter, {}).get("mode")
            self.system_mode = self._info.get(self.filter, {}).get("systemMode")

            if str(self.mode).lower() == "migration":
                self.maintenance_mode = "migration"
            elif str(self.mode).lower() != str(self.system_mode).lower():
                self.maintenance_mode = "inconsistent"
            else:
                self.maintenance_mode = self.mode

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
        IP Address of the switch with which to filter self._info()
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
    def mock_response_key(self):
        """
        The key used to extract controller response from the mocked response
        in ``responses_SwitchDetails.json``.

        When setter is accessed, call ``populate_properties()`` to set the
        mocked property values from the contents of the mocked response.
        """
        return self._mock_response_key

    @mock_response_key.setter
    def mock_response_key(self, value):
        self._mock_response_key = value
        self.populate_mocked_properties()

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
    def fabric_name(self):
        """
        Mocked fabric_name property
        """
        return self._fabric_name

    @fabric_name.setter
    def fabric_name(self, value):
        self._fabric_name = value

    @property
    def freeze_mode(self):
        """
        Mocked freeze_mode property
        """
        return self._freeze_mode

    @freeze_mode.setter
    def freeze_mode(self, value):
        self._freeze_mode = value

    @property
    def maintenance_mode(self):
        """
        Mocked maintenance_mode property
        """
        return self._maintenance_mode

    @maintenance_mode.setter
    def maintenance_mode(self, value):
        self._maintenance_mode = value

    @property
    def mode(self):
        """
        Mocked mode property
        """
        return self._mode

    @mode.setter
    def mode(self, value):
        self._mode = value

    @property
    def serial_number(self):
        """
        Mocked serial_number property
        """
        if (
            self.mock_class == self.class_name
            and self.mock_property == "serial_number.getter"
        ):
            raise self.mock_exception(self.mock_message)
        return self._serial_number

    @serial_number.setter
    def serial_number(self, value):
        if (
            self.mock_class == self.class_name
            and self.mock_property == "serial_number.setter"
        ):
            raise self.mock_exception(self.mock_message)
        self._serial_number = value

    @property
    def switch_role(self):
        """
        Mocked switch_role property
        """
        return self._switch_role

    @switch_role.setter
    def switch_role(self, value):
        self._switch_role = value

    @property
    def system_mode(self):
        """
        Mocked switch_role property
        """
        return self._system_mode

    @system_mode.setter
    def system_mode(self, value):
        self._system_mode = value
