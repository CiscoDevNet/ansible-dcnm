"""
Common enum definitions for module utilities in module_utils/common
"""
# Copyright (c) 2025 Cisco and/or its affiliates.
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

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

from enum import Enum


class MaintenanceModeSetEnum(str, Enum):
    """
    # Summary

    Valid maintenance mode values for switches.

    These are modes that the user can set.

    ## Raises

    None

    ## Values

    - `MAINTENANCE`: Switch is in maintenance mode
    - `NORMAL`: Switch is in normal operational mode

    ## See also

    MaintenanceModeGetEnum
    """

    MAINTENANCE = "maintenance"
    NORMAL = "normal"

    @classmethod
    def values(cls) -> list[str]:
        """
        # Summary

        Return a set of valid maintenance mode values.

        ## Raises

        None

        ## Returns

        List of string values for all maintenance modes.
        """
        return [mode.value for mode in cls]


class MaintenanceModeGetEnum(str, Enum):
    """
    # Summary

    Valid maintenance mode values for switches.

    These are modes that the user can retrieve.

    ## Raises

    None

    ## Values

    - `INCONSISTENT`: A synthesized mode indicating that mode != systemMode
    - `MAINTENANCE`: Switch is in maintenance mode
    - `NORMAL`: Switch is in normal operational mode

    ## See also

    MaintenanceModeGetEnum
    """

    INCONSISTENT = "inconsistent"
    MAINTENANCE = "maintenance"
    NORMAL = "normal"

    @classmethod
    def values(cls) -> list[str]:
        """
        # Summary

        Return a set of valid maintenance mode values.

        ## Raises

        None

        ## Returns

        List of string values for all maintenance modes.
        """
        return [mode.value for mode in cls]
