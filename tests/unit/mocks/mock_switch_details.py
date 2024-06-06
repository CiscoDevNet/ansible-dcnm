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


class MockSwitchDetails:
    """
    ### Summary
    Mock the exceptions raised by the methods and properties
    in the ``SwitchDetails`` class.

    ### NOTES
    -   This class is used to test the exceptions raised by ``SwitchDetails``
    -   This class does NOT simulate the behavior of ``SwitchDetails`` with
        respect its interaction with the controller.  For that, see the
        ``Sender`` class within ``module_utils/common/sender_file.py``,
        and the ``RestSend`` class within ``module_utils/common/rest_send.py``.
    -   Example usage for the ``Sender`` class can be found in
        ``test_maintenance_mode_info_00500`` within
        ``tests/unit/module_utils/common/test_maintenance_mode_info.py``.

    ### Example usage
    ```python
    @pytest.mark.parametrize(
        "mock_class, mock_property, mock_exception, expected_exception, mock_message",
        [
            (
                "FabricDetailsByName",
                "refresh",
                ControllerResponseError,
                ValueError,
                "Bad controller response: fabric_details.refresh",
            ),
            (
                "FabricDetailsByName",
                "results.setter",
                TypeError,
                ValueError,
                "Bad type: fabric_details.results.setter",
            ),
            (
                "FabricDetailsByName",
                "rest_send.setter",
                TypeError,
                ValueError,
                "Bad type: fabric_details.rest_send.setter",
            ),
            (
                "SwitchDetails",
                "refresh",
                ControllerResponseError,
                ValueError,
                "Bad controller response: switch_details.refresh",
            ),
            (
                "SwitchDetails",
                "results.setter",
                TypeError,
                ValueError,
                "Bad type: switch_details.results.setter",
            ),
            (
                "SwitchDetails",
                "rest_send.setter",
                TypeError,
                ValueError,
                "Bad type: switch_details.rest_send.setter",
            ),
        ],
    )
    def test_maintenance_mode_info_00200(
        monkeypatch,
        mock_class,
        mock_property,
        mock_exception,
        expected_exception,
        mock_message,
    ) -> None:
        with does_not_raise():
            instance = MaintenanceModeInfo(PARAMS)

        mock_fabric_details = MockFabricDetailsByName()
        mock_fabric_details.mock_class = mock_class
        mock_fabric_details.mock_exception = mock_exception
        mock_fabric_details.mock_message = mock_message
        mock_fabric_details.mock_property = mock_property

        mock_switch_details = MockSwitchDetails()
        mock_switch_details.mock_class = mock_class
        mock_switch_details.mock_exception = mock_exception
        mock_switch_details.mock_message = mock_message
        mock_switch_details.mock_property = mock_property

        monkeypatch.setattr(instance, "fabric_details", mock_fabric_details)
        monkeypatch.setattr(instance, "switch_details", mock_switch_details)

        with does_not_raise():
            instance.config = CONFIG
            instance.rest_send = RestSend({"state": "query", "check_mode": False})
            instance.results = Results()

        with pytest.raises(expected_exception, match=mock_message):
            instance.refresh()
        ```
    """

    def __init__(self) -> None:

        def null_mock_exception():
            pass

        self.class_name = "SwitchDetails"
        self._mock_class = None
        self._mock_exception = null_mock_exception
        self._mock_message = None
        self._mock_property = None

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
        Mocked filter
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
    def fabric_name(self):
        """
        Mocked fabric_name property
        """
        if (
            self.mock_class == self.class_name
            and self.mock_property == "fabric_name.getter"
        ):
            raise self.mock_exception(self.mock_message)
        return self._fabric_name

    @fabric_name.setter
    def fabric_name(self, value):
        if (
            self.mock_class == self.class_name
            and self.mock_property == "fabric_name.setter"
        ):
            raise self.mock_exception(self.mock_message)
        self._fabric_name = value

    @property
    def freeze_mode(self):
        """
        Mocked freeze_mode property
        """
        if (
            self.mock_class == self.class_name
            and self.mock_property == "freeze_mode.getter"
        ):
            raise self.mock_exception(self.mock_message)
        return self._freeze_mode

    @freeze_mode.setter
    def freeze_mode(self, value):
        if (
            self.mock_class == self.class_name
            and self.mock_property == "freeze_mode.setter"
        ):
            raise self.mock_exception(self.mock_message)
        self._freeze_mode = value

    @property
    def maintenance_mode(self):
        """
        Mocked maintenance_mode property
        """
        if (
            self.mock_class == self.class_name
            and self.mock_property == "maintenance_mode.getter"
        ):
            raise self.mock_exception(self.mock_message)
        return self._maintenance_mode

    @maintenance_mode.setter
    def maintenance_mode(self, value):
        if (
            self.mock_class == self.class_name
            and self.mock_property == "maintenance_mode.setter"
        ):
            raise self.mock_exception(self.mock_message)
        self._maintenance_mode = value

    @property
    def mode(self):
        """
        Mocked mode property
        """
        if self.mock_class == self.class_name and self.mock_property == "mode.getter":
            raise self.mock_exception(self.mock_message)
        return self._mode

    @mode.setter
    def mode(self, value):
        if self.mock_class == self.class_name and self.mock_property == "mode.setter":
            raise self.mock_exception(self.mock_message)
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
        return self.serial_number

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
        if (
            self.mock_class == self.class_name
            and self.mock_property == "switch_role.getter"
        ):
            raise self.mock_exception(self.mock_message)
        return self.switch_role

    @switch_role.setter
    def switch_role(self, value):
        if (
            self.mock_class == self.class_name
            and self.mock_property == "switch_role.setter"
        ):
            raise self.mock_exception(self.mock_message)
        self._switch_role = value

    @property
    def system_mode(self):
        """
        Mocked switch_role property
        """
        if (
            self.mock_class == self.class_name
            and self.mock_property == "system_mode.getter"
        ):
            raise self.mock_exception(self.mock_message)
        return self.system_mode

    @system_mode.setter
    def system_mode(self, value):
        if (
            self.mock_class == self.class_name
            and self.mock_property == "system_mode.setter"
        ):
            raise self.mock_exception(self.mock_message)
        self._system_mode = value
