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

import logging
from logging.config import dictConfig

import yaml


class Log:
    def __init__(self, ansible_module):
        self.class_name = self.__class__.__name__
        self.ansible_module = ansible_module

        self._build_properties()

    def _build_properties(self) -> None:
        self.properties = {}
        self.properties["config"] = None

    def commit(self):
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
                msg = f"error configuring logging from dict. "
                msg += f"detail: {err}"
                self.ansible_module.fail_json(msg=msg)

        try:
            with open(self.config, "r") as file:
                logging_config = yaml.safe_load(file)
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
        2.  A YAML file from which logging config is read.
            Must conform to logging.config.dictConfig
        3.  A dictionary containing logging config
            Must conform to logging.config.dictConfig
        """
        return self.properties["config"]

    @config.setter
    def config(self, value):
        self.properties["config"] = value
