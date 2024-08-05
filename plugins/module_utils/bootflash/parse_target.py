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

import inspect
import logging

class ParseTarget:
    def __init__(self) -> None:
        self.class_name = self.__class__.__name__

        self._filename = None
        self._filepath = None
        self._target = None
        self._partition = None
        self._supervisor = None

        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED ParseTarget(): "
        self.log.debug(msg)

    def commit(self):
        """
        ### Summary
        Commit the target to be parsed.

        ### Raises
        -   ``ValueError`` if:
            -   target is not set before calling commit.
        """
        if self.target is None:
            msg = f"{self.class_name}.commit: "
            msg += f"target must be set before calling commit."
            raise ValueError(msg)

        self.parse_target()

    def parse_target(self) -> None:
        """
        ### Summary
        Parse the target.filepath parameter into its consituent API parameters.

        ### Raises
        -   ``ValueError`` if:
            -   ``filepath`` is not set in the target dict.
            -   ``supervisor`` is not set in the target dict.

        ### Target Structure
        {
            filepath: bootflash:/myDir/foo.txt
            supervisor: active
        }

        Set the following API parameters from the above structure:

        - self.partition: bootflash:
        - self.filepath: bootflash:/myDir/
        - self.filename: foo.txt
        - self.supervisor: active

        ### Notes
        -   While this method is written to support files in directories, the
            NDFC API does not support listing files within a directory.
            Hence, we currently support only files in the root directory of
            the partition.
        -   If the file is located in the root directory of the of the
            partition, the filepath MUST NOT have a trailing slash.
            i.e. filepath == "bootflash:/" will NOT match.  It MUST
            be "bootflash:".
        -   If the file is located in a directory, the filepath MUST
            have a trailing slash.  i.e. filepath == "bootflash:/myDir"
            will NOT match since NDFC is not smart enough to add the
            slash between the filepath and filename and, using the example
            in Target Structure above, it will reconstruct the path as
            bootflash:/myDirfoo.txt which, of course, will not match
            (or worse yet, match and delete the wrong file).
        """
        method_name = inspect.stack()[0][3]

        def raise_error(msg):
            raise ValueError(f"{self.class_name}.{method_name}: {msg}")

        if self.target.get("filepath", None) is None:
            msg = "Expected filepath in target dict. "
            msg += f"Got {self.target}"
            raise_error(msg)
        if self.target.get("supervisor", None) is None:
            msg = "Expected supervisor in target dict. "
            msg += f"Got {self.target}"
            raise_error(msg)

        parts = self.target.get("filepath").split("/")
        self.partition = parts[0]
        # If len(parts) == 2, the file is located in the root directory of the
        # partition. In this case we DO NOT want to add a trailing slash to
        # the filepath.  i.e. filepath == "bootflash:/" will NOT match.
        self.filepath = "/".join(parts[0:-1])
        # If there's one or more directory levels in the path we DO need to
        # add a trailing slash to filepath.
        if len(parts) > 2:
            # Input: bootflash:/myDir/foo.txt
            # parts: ['bootflash:', 'myDir', 'foo.txt']
            # Result: self.filepath == bootflash:/myDir/
            self.filepath = "/".join(parts[0:-1]) + "/"
        self.filename = parts[-1]
        self.supervisor = self.target.get("supervisor")

    @property
    def filename(self):
        return self._filename
    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    def filepath(self):
        return self._filepath
    @filepath.setter
    def filepath(self, value):
        self._filepath = value

    @property
    def target(self):
        return self._target
    @target.setter
    def target(self, value):
        self._target = value

    @property
    def partition(self):
        return self._partition
    @partition.setter
    def partition(self, value):
        self._partition = value

    @property
    def supervisor(self):
        return self._supervisor
    @supervisor.setter
    def supervisor(self, value):
        self._supervisor = value
