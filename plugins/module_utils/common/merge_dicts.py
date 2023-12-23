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
from collections.abc import MutableMapping as Map
from typing import Any, Dict

from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log


class MergeDicts:
    """
    Merge two dictionaries.

    Given two dictionaries, dict1 and dict2, merge them into a
    single dictionary, dict_merged, where keys in dict2 have
    precedence over (will overwrite) keys in dict1.

    Example:

    module = AnsibleModule(...)
    instance = MergeDicts(module)
    instance.dict1 = { "foo": 1, "bar": 2 }
    instance.dict2 = { "foo": 3, "baz": 4 }
    instance.commit()
    dict_merged = instance.dict_merged
    print(dict_merged)

    Output:
    { foo: 3, bar: 2, baz: 4 }
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module

        self.log = Log(self.ansible_module)
        self.log.debug = False
        self.log.logfile = None

        self._build_properties()

    def _build_properties(self) -> None:
        self.properties = {}
        self.properties["dict1"] = None
        self.properties["dict2"] = None
        self.properties["dict_merged"] = None

    def commit(self) -> None:
        """
        Commit the merged dict.
        """
        method_name = inspect.stack()[0][3]
        if self.dict1 is None or self.dict2 is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "dict1 and dict2 must be set before calling commit()"
            self.ansible_module.fail_json(msg)

        self.properties["dict_merged"] = self.merge_dicts(self.dict1, self.dict2)

    def merge_dicts(
        self, dict1: Dict[Any, Any], dict2: Dict[Any, Any]
    ) -> Dict[Any, Any]:
        """
        Merge dict2 into dict1 and return dict1.
        Keys in dict2 have precedence over keys in dict1.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable
        for key in dict2:
            if isinstance(dict1.get(key, None), Map) and dict2.get(key, None) is None:
                # This is to handle a case where dict1 contains a key that is a
                # dict, which is supposed to contain sub-options, but the dict
                # is empty.
                #
                # For example, below, upgrade is specified, but upgrade.nxos
                # and upgrade.epld are not.  In this case, we copy the entire
                # 'upgrade' dict from dict1 to dict2:
                #
                # -   ip_address: 172.22.150.110
                #     upgrade:
                #     options:
                #         epld:
                #             module: 27
                #             golden: false
                dict2[key] = dict1[key]
            elif (
                key in dict1
                and isinstance(dict1[key], Map)
                and isinstance(dict2[key], Map)
            ):
                self.merge_dicts(dict1[key], dict2[key])
            else:
                dict1[key] = dict2[key]
        return copy.deepcopy(dict1)

    @property
    def debug(self):
        """
        Enable/disable debugging to self.logfile
        """
        return self.log.debug

    @debug.setter
    def debug(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Invalid type for debug. Expected bool. "
            msg += f"Got {type(value)}."
            self.ansible_module.fail_json(msg)
        self.log.debug = value

    @property
    def logfile(self):
        """
        Set file to which debug log is written
        """
        return self.log.logfile

    @logfile.setter
    def logfile(self, value):
        self.log.logfile = value

    @property
    def dict_merged(self):
        """
        Getter for the merged dictionary.
        """
        method_name = inspect.stack()[0][3]
        if self.properties["dict_merged"] is None:
            msg = f"{self.class_name}.{method_name}: "
            msg += "Call instance.commit() before calling "
            msg += f"instance.{method_name}."
            self.ansible_module.fail_json(msg)
        return self.properties["dict_merged"]

    @property
    def dict1(self):
        """
        The dictionary into which dict2 will be merged.

        dict1's keys will be overwritten by dict2's keys.
        """
        return self.properties["dict1"]

    @dict1.setter
    def dict1(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Invalid parameters. Expected type dict. "
            msg += f"Got type {type(value)}."
            self.ansible_module.fail_json(msg)
        self.properties["dict1"] = copy.deepcopy(value)

    @property
    def dict2(self):
        """
        The dictionary which will be merged into dict1.

        dict2's keys will overwrite by dict1's keys.
        """
        return self.properties["dict2"]

    @dict2.setter
    def dict2(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Invalid parameters. Expected type dict. "
            msg += f"Got type {type(value)}."
            self.ansible_module.fail_json(msg)
        self.properties["dict2"] = copy.deepcopy(value)
