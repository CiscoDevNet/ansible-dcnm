#
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
__author__ = "Allen Robel"

import copy
import inspect
import logging
from time import sleep

from ..common.properties import Properties
from ..common.results import Results
from .switch_issu_details import (
    SwitchIssuDetailsByDeviceName,
    SwitchIssuDetailsByIpAddress,
    SwitchIssuDetailsBySerialNumber
)


@Properties.add_rest_send
class WaitForControllerDone:
    """
    ### Summary
    Wait for actions to complete on the controller.

    Actions include image staging, image upgrade, and image validation.

    ### Raises
    -   ``ValueError`` if:
            - Controller actions do not complete within ``rest_send.timeout`` seconds.
            - ``items`` is not a set prior to calling ``commit()``.
            - ``item_type`` is not set prior to calling ``commit()``.
            - ``rest_send`` is not set prior to calling ``commit()``.
    """

    def __init__(self):
        self.class_name = self.__class__.__name__
        method_name = inspect.stack()[0][3]

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.action = "wait_for_controller"
        self.done = set()
        self.todo = set()
        self.issu_details = None

        self._items = None
        self._item_type = None
        self._rest_send = None
        self._valid_item_types = ["device_name", "ipv4_address", "serial_number"]

        msg = f"ENTERED {self.class_name}().{method_name}"
        self.log.debug(msg)

    def get_filter_class(self) -> None:
        """
        ### Summary
        Set the appropriate ''SwitchIssuDetails'' subclass based on
        ``item_type``.

        The subclass is used to filter the issu_details controller data
        by item_type.

        ### Raises
        None
        """
        _select = {}
        _select["device_name"] = SwitchIssuDetailsByDeviceName
        _select["ipv4_address"] = SwitchIssuDetailsByIpAddress
        _select["serial_number"] = SwitchIssuDetailsBySerialNumber
        self.issu_details = _select[self.item_type]()
        self.issu_details.rest_send = self.rest_send  # pylint: disable=no-member
        self.issu_details.results = Results()
        self.issu_details.results.action = self.action

    def verify_commit_parameters(self):
        """
        ### Summary
        Verify that mandatory parameters are set before calling commit().

        ### Raises
        -   ``ValueError`` if:
                - ``items`` is not set.
                - ``item_type`` is not set.
                - ``rest_send`` is not set.
        """
        method_name = inspect.stack()[0][3]
        msg = f"{self.class_name}.{method_name}: "

        if self.items is None:
            msg += "items must be set before calling commit()."
            raise ValueError(msg)

        if self.item_type is None:
            msg += "item_type must be set before calling commit()."
            raise ValueError(msg)

        if self.rest_send is None:  # pylint: disable=no-member
            msg = f"{self.class_name}.{method_name}: "
            msg += "rest_send must be set before calling commit()."
            raise ValueError(msg)

    def commit(self):
        """
        ### Summary
        The controller will not proceed with certain operations if there
        are any actions in progress.  Wait for all actions to complete
        and then return.

        Actions include image staging, image upgrade, and image validation.

        ### Raises
        -   ``ValueError`` if:
                -   Actions do not complete within ``rest_send.timeout`` seconds.
                -   ``items`` is not a set.
                -   ``item_type`` is not set.
                -   ``rest_send`` is not set.
        """
        # pylint: disable=no-member
        method_name = inspect.stack()[0][3]

        self.verify_commit_parameters()

        if len(self.items) == 0:
            return
        self.get_filter_class()
        self.todo = copy.copy(self.items)
        timeout = self.rest_send.timeout

        while self.done != self.todo and timeout > 0:
            if self.rest_send.unit_test is False:  # pylint: disable=no-member
                sleep(self.rest_send.send_interval)
            timeout -= self.rest_send.send_interval

            self.issu_details.refresh()

            for item in self.todo:
                if item in self.done:
                    continue
                self.issu_details.filter = item
                if self.issu_details.actions_in_progress is False:
                    self.done.add(item)

        if self.done != self.todo:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Timed out after {self.rest_send.timeout} seconds "
            msg += "waiting for controller actions to complete on items: "
            msg += f"{sorted(self.todo)}. "
            if len(self.done) > 0:
                msg += "The following items did complete: "
                msg += f"{','.join(sorted(self.done))}."
            raise ValueError(msg)

    @property
    def items(self):
        """
        ### Summary
        A set of serial_number, ipv4_address, or device_name to wait for.

        ### Raises
        ValueError: If ``items`` is not a set.

        ### Example
        ```python
        instance.items = {"192.168.1.1", "192.168.1.2"}
        ```
        """
        return self._items

    @items.setter
    def items(self, value):
        if not isinstance(value, set):
            raise TypeError("items must be a set")
        self._items = value

    @property
    def item_type(self):
        """
        ### Summary
        The type of items to wait for.

        ### Raises
        ValueError: If ``item_type`` is not one of the valid values.

        ### Valid Values
        -   ``serial_number``
        -   ``ipv4_address``
        -   ``device_name``

        ### Example
        ```python
        instance.item_type = "ipv4_address"
        ```
        """
        return self._item_type

    @item_type.setter
    def item_type(self, value):
        if value not in self._valid_item_types:
            msg = f"{self.class_name}.item_type: "
            msg = "item_type must be one of "
            msg += f"{','.join(self._valid_item_types)}."
            raise ValueError(msg)
        self._item_type = value
