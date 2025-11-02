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
"""
Enumeration for operation types used in Nexus Dashboard modules.
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

from enum import Enum


class OperationType(Enum):
    """
    # Summary

    Enumeration for operation types.

    Used by ResultsV2 to determine if changes have occurred based on the operation type.

    - QUERY: Represents a query operation which does not change state.
    - CREATE: Represents a create operation which adds new resources.
    - UPDATE: Represents an update operation which modifies existing resources.
    - DELETE: Represents a delete operation which removes resources.

    # Usage

    ```python
    from plugins.module_utils.common.operation_types import OperationType
    class MyModule:
        def __init__(self):
            self.operation_type = OperationType.QUERY
    ```

    The above informs the ResultsV2 class that the current operation is a query, and thus
    no changes should be expected.

    Specifically, Results.has_anything_changed() will return False for QUERY operations,
    while it will evaluate CREATE, UPDATE, and DELETE operations in more detail to
    determine if any changes have occurred.
    """

    QUERY = "query"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

    def changes_state(self) -> bool:
        """
        # Summary

        Return True if this operation type can change controller state.

        ## Returns

        - `bool`: True if operation can change state, False otherwise

        ## Examples

        ```python
        OperationType.QUERY.changes_state()  # Returns False
        OperationType.CREATE.changes_state()  # Returns True
        OperationType.DELETE.changes_state()  # Returns True
        ```
        """
        return self in (
            OperationType.CREATE,
            OperationType.UPDATE,
            OperationType.DELETE,
        )

    def is_read_only(self) -> bool:
        """
        # Summary

        Return True if this operation type is read-only.

        ## Returns

        - `bool`: True if operation is read-only, False otherwise

        ## Examples

        ```python
        OperationType.QUERY.is_read_only()  # Returns True
        OperationType.CREATE.is_read_only()  # Returns False
        ```
        """
        return self == OperationType.QUERY
