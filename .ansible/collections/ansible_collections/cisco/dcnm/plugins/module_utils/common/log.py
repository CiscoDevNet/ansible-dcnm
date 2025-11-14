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

import json
import logging
from logging.config import dictConfig


class Log:
    """
    Create the base dcnm logging object.

    Usage (where ansible_module is an instance of AnsibleModule):

    Below, config.json is a logging config file in JSON format conformant
    with Python's logging.config.dictConfig.  The file can be located
    anywhere on the filesystem.  See the following for an example:

    cisco/dcnm/plugins/module_utils/common/logging_config.json

    from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import Log
    log = Log(ansible_module)
    log.config = "/path/to/logging/config.json"
    log.commit()

    At this point, a base/parent logger is created for which all other
    loggers throughout the dcnm collection will be children.
    This allows for a single logging config to be used for all dcnm
    modules, and allows for the logging config to be specified in a
    single place external to the code.

    If log.config is set to None (which is the default if it's not explictely set),
    then logging is disabled.
    """

    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module

        self._build_properties()

    def _build_properties(self) -> None:
        self.properties = {}
        self.properties["config"] = None

    def commit(self):
        """
        Create the base logger instance from a source conformant with
        logging.config.dictConfig.

        1.  If self.config is None, then logging is disabled.
        2.  If self.config is a JSON file, then it is read and logging
            is configured from the JSON file.
        3.  If self.config is a dictionary, then logging is configured
            from the dictionary.
        """
        if self.config is None:
            logger = logging.getLogger()
            for handler in logger.handlers.copy():
                try:
                    logger.removeHandler(handler)
                except ValueError:  # if handler already removed
                    pass
            logger.addHandler(logging.NullHandler())
            logger.propagate = False
            return

        if isinstance(self.config, dict):
            try:
                dictConfig(self.config)
                return
            except ValueError as err:
                msg = "error configuring logging from dict. "
                msg += f"detail: {err}"
                self.ansible_module.fail_json(msg=msg)

        try:
            with open(self.config, "r", encoding="utf-8") as file:
                logging_config = json.load(file)
        except IOError as err:
            msg = f"error reading logging config from {self.config}. "
            msg += f"detail: {err}"
            self.ansible_module.fail_json(msg=msg)
        dictConfig(logging_config)

    @property
    def config(self):
        """
        Can be either:

        1.  None, in which case logging is disabled
        2.  A JSON file from which logging config is read.
            Must conform to logging.config.dictConfig
        3.  A dictionary containing logging config
            Must conform to logging.config.dictConfig
        """
        return self.properties["config"]

    @config.setter
    def config(self, value):
        self.properties["config"] = value
