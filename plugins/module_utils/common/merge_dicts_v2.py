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

import copy
import inspect
import logging
from collections.abc import MutableMapping as Map


class MergeDicts:
    """
    ### Summary
    Merge two dictionaries.

    Given two dictionaries, dict1 and dict2, merge them into a
    single dictionary, dict_merged, where keys in dict2 have
    precedence over (will overwrite) keys in dict1.

    ### Raises
    -   ``TypeError`` if ``dict1`` is not a dictionary.
    -   ``TypeError`` if ``dict2`` is not a dictionary.
    -   ``ValueError`` if ``dict1`` has not been set before calling commit()
    -   ``ValueError`` if ``dict2`` has not been set before calling commit()
    -   ``ValueError`` if ``dict_merged`` is accessed before calling commit()

    ### Usage
    ```python
    try:
        instance = MergeDicts()
        instance.dict1 = { "foo": 1, "bar": 2 }
        instance.dict2 = { "foo": 3, "baz": 4 }
        instance.commit()
        dict_merged = instance.dict_merged
    except (TypeError, ValueError) as error:
        handle_error(error)
    print(dict_merged)
    ```

    ### Output
    ```json
    { foo: 3, bar: 2, baz: 4 }
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED MergeDicts()")

        self._build_properties()

    def _build_properties(self) -> None:
        self.properties = {}
        self.properties["dict1"] = None
        self.properties["dict2"] = None
        self.properties["dict_merged"] = None

    def commit(self) -> None:
        """
        ### Summary
        Commit the merged dict.

        ### Raises
        -   ``ValueError`` if ``dict1`` or ``dict2`` has not been set.
        """
        method_name = inspect.stack()[0][3]
        if self.dict1 is None or self.dict2 is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "dict1 and dict2 must be set before calling commit()"
            raise ValueError(msg)

        self.properties["dict_merged"] = self.merge_dicts(self.dict1, self.dict2)

    def merge_dicts(self, dict1: dict, dict2: dict) -> dict:
        """
        Merge dict2 into dict1 and return dict1.
        Keys in dict2 have precedence over keys in dict1.
        """
        for key in dict2:
            if (
                key in dict1
                and isinstance(dict1[key], Map)
                and isinstance(dict2[key], Map)
            ):
                self.merge_dicts(dict1[key], dict2[key])
            else:
                dict1[key] = dict2[key]
        return copy.deepcopy(dict1)

    @property
    def dict_merged(self):
        """
        ### Summary
        Returns the merged dictionary.

        ### Raises
        -   ``ValueError`` if ``dict_merged`` is accessed before
            ``commit()`` has been called.
        """
        method_name = inspect.stack()[0][3]
        if self.properties["dict_merged"] is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Call instance.commit() before calling "
            msg += f"instance.{method_name}."
            raise ValueError(msg)
        return self.properties["dict_merged"]

    @property
    def dict1(self):
        """
        ### Summary
        The dictionary into which ``dict2`` will be merged.

        ``dict1``'s keys will be overwritten by ``dict2``'s keys.

        ### Raises
        -   ``TypeError`` if ``value`` is not a dictionary.
        """
        return self.properties["dict1"]

    @dict1.setter
    def dict1(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Invalid value. Expected type dict. "
            msg += f"Got type {type(value)}."
            raise TypeError(msg)
        self.properties["dict1"] = copy.deepcopy(value)

    @property
    def dict2(self):
        """
        ### Summary
        The dictionary which will be merged into ``dict1``.

        ``dict2``'s keys will overwrite by ``dict1``'s keys.

        ### Raises
        -   ``TypeError`` if ``value`` is not a dictionary.
        """
        return self.properties["dict2"]

    @dict2.setter
    def dict2(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Invalid value. Expected type dict. "
            msg += f"Got type {type(value)}."
            raise TypeError(msg)
        self.properties["dict2"] = copy.deepcopy(value)
