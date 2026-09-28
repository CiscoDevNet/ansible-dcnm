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
"""
Parse `target` into its constituent API parameters
"""
from __future__ import absolute_import, division, print_function

__metaclass__ = type  # pylint: disable=invalid-name
__author__ = "Allen Robel"

import inspect
import logging


class ConvertTargetToParams:
    """
    # Summary

    Parse `target` into its constituent API parameters.

    ## Raises

    ### ValueError

    -   `filepath` is not set in the target dict.
    -   `supervisor` is not set in the target dict.

    ## Usage

    ### Example 1, file in directory.

    ```python
    target = {
        "filepath": "bootflash:/myDir/foo.txt",
        "supervisor": "active"
    }
    instance = ConvertTargetToParams()
    instance.target = target
    instance.commit()
    print(instance.partition)  # bootflash:
    print(instance.filepath)   # bootflash:/myDir/
    print(instance.filename)   # foo.txt
    print(instance.supervisor) # active
    ```

    ### Example 2, file in root of bootflash partition.

    ```python
    target = {
        "filepath": "bootflash:/foo.txt",
        "supervisor": "active"
    }
    instance = ConvertTargetToParams()
    instance.target = target
    instance.commit()
    print(instance.partition)  # bootflash:
    print(instance.filepath)   # bootflash:
    print(instance.filename)   # foo.txt
    print(instance.supervisor) # active
    ```
    """

    def __init__(self) -> None:
        self.class_name: str = self.__class__.__name__
        self.action: str = "convert_target_to_params"
        self._committed: bool = False
        self.valid_supervisor: list[str] = ["active", "standby"]

        self._filename: str = ""
        self._filepath: str = ""
        self._target: dict = {}
        self._partition: str = ""
        self._supervisor: str = ""

        self.log: logging.Logger = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED ConvertTargetToParams(): "
        self.log.debug(msg)

    def commit(self) -> None:
        """
        # Summary

        Commit the target to be parsed.

        ## Raises

        ### ValueError

        - `target` is not set before calling commit.
        """
        if not self.target:
            msg = f"{self.class_name}.commit: "
            msg += "target must be set before calling commit."
            raise ValueError(msg)

        self.parse_target()
        self._committed = True

    def parse_target(self) -> None:
        """
        # Summary

        Parse `target` into its constituent API parameters.

        ## Raises

        ### ValueError

        - `filepath` is not set in the target dict.
        - `supervisor` is not set in the target dict.

        ## Target Structure

        ```json
        {
            filepath: bootflash:/myDir/foo.txt
            supervisor: active
        }
        ```

        ## API Parameters

        Set the following API parameters from the above structure:

        - self.partition: bootflash:
        - self.filepath: bootflash:/myDir/
        - self.filename: foo.txt
        - self.supervisor: active

        ## Notes

        -   While this method is written to support files in directories, the
            NDFC API does not support listing files within a directory. Hence,
            we currently support only files in the root directory of the
            partition.
        -   If the file is located in the root directory of the partition,
            the filepath MUST NOT have a trailing slash.
            i.e. filepath == "bootflash:/" will NOT match.  It MUST be
            "bootflash:".
        -   If the file is located in a directory, the filepath MUST
            have a trailing slash.  i.e. filepath == "bootflash:/myDir"
            will NOT match since NDFC is not smart enough to add the
            slash between the filepath and filename and, using the example
            in Target Structure above, it will reconstruct the path as
            bootflash:/myDirfoo.txt which, of course, will not match
            (or worse yet, match and delete the wrong file).
        """
        method_name: str = inspect.stack()[0][3]

        msg = f"{self.class_name}.{method_name}: "

        if not self._target:
            msg += "Expected target to be set before calling parse_target."
            raise ValueError(msg)

        if self._target.get("filepath") is None:
            msg += "Expected filepath in target dict. "
            msg += f"Got {self.target}."
            raise ValueError(msg)

        if self._target.get("supervisor") is None:
            msg += "Expected supervisor in target dict. "
            msg += f"Got {self.target}."
            raise ValueError(msg)

        parts: list[str] = self._target.get("filepath", "").split("/")
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
        self.supervisor = self._target.get("supervisor", "")

    @property
    def filename(self) -> str:
        """
        # Summary

        Return the filename parsed from `target`.

        ## Raises

        ### ValueError

        - `commit()` has not been called before accessing this property.
        """
        method_name = inspect.stack()[0][3]
        if not self._committed:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"commit() must be called before accessing {method_name}."
            raise ValueError(msg)
        return self._filename

    @filename.setter
    def filename(self, value: str) -> None:
        self._filename = value

    @property
    def filepath(self) -> str:
        """
        # Summary

        Return the filepath parsed from `target`.

        ## Raises

        ### ValueError

        -   `commit()` has not been called before accessing this property.
        """
        method_name = inspect.stack()[0][3]
        if not self._committed:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"commit() must be called before accessing {method_name}."
            raise ValueError(msg)
        return self._filepath

    @filepath.setter
    def filepath(self, value: str) -> None:
        self._filepath = value

    @property
    def target(self) -> dict:
        """
        # Summary

        The target to be parsed.  This is a dictionary with the following structure:

        ```json
        {
            "filepath": "bootflash:/myDir/foo.txt",
            "supervisor": "active"
        }
        ```
        """
        return self._target

    @target.setter
    def target(self, value: dict) -> None:
        self._target = value

    @property
    def partition(self) -> str:
        """
        # Summary

        Return the partition parsed from `target`.

        ## Raises

        ### ValueError

        -   `commit()` has not been called before accessing this property.
        """
        method_name = inspect.stack()[0][3]
        if not self._committed:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"commit() must be called before accessing {method_name}."
            raise ValueError(msg)
        return self._partition

    @partition.setter
    def partition(self, value: str) -> None:
        method_name = inspect.stack()[0][3]
        if not str(value).endswith(":"):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid partition: {value}. "
            msg += "Expected partition to end with a colon."
            raise ValueError(msg)
        self._partition = value

    @property
    def supervisor(self) -> str:
        """
        # Summary

        Return the supervisor parsed from `target`. This is the state
        (active or standby) of the supervisor that hosts the file described
        in `target`.

        ## Raises

        ### ValueError

        - `commit()` has not been called before accessing this property.
        """
        method_name = inspect.stack()[0][3]
        if not self._committed:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"commit() must be called before accessing {method_name}."
            raise ValueError(msg)
        return self._supervisor

    @supervisor.setter
    def supervisor(self, value: str) -> None:
        method_name = inspect.stack()[0][3]
        if value not in self.valid_supervisor:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid supervisor: {value}. "
            msg += f"Expected one of: {','.join(self.valid_supervisor)}."
            raise ValueError(msg)
        self._supervisor = value
