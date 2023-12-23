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

import inspect


class Log:
    """
    A logging utility for use with Ansible modules.

    Log messages to a file.

    Usage:

    instance = Log(ansible_module)
    instance.debug = True
    instance.logfile = "/tmp/params_validate.log"
    instance.log_msg("some message")
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module

        self._build_properties()

    def _build_properties(self) -> None:
        self.properties = {}
        self.properties["debug"] = False
        self.properties["logfile"] = None

    def log_msg(self, msg):
        """
        Open the logfile and write the message to it.

        Call fail_json() if there is an error writing to the logfile.
        """
        if self.debug is False:
            return
        if self.logfile is None:
            return
        try:
            with open(f"{self.logfile}", "a+", encoding="UTF-8") as file_handle:
                file_handle.write(f"{msg}\n")
        except IOError as err:
            msg = f"error writing to logfile {self.logfile}. "
            msg += f"detail: {err}"
            self.ansible_module.fail_json(msg)

    @property
    def debug(self):
        """
        Enable/disable debugging to self.logfile
        """
        return self.properties["debug"]

    @debug.setter
    def debug(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, bool):
            msg = f"{self.class_name}.{method_name}: "
            msg += "Invalid type for debug. Expected bool. "
            msg += f"Got {type(value)}."
            self.ansible_module.fail_json(msg)
        self.properties["debug"] = value

    @property
    def logfile(self):
        """
        Set file to which messages are written
        """
        return self.properties["logfile"]

    @logfile.setter
    def logfile(self, value):
        self.properties["logfile"] = value
