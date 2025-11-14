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

import logging

from ..rest import Rest


class PackageMgnt(Rest):
    """
    ## api.v1.imagemanagement.rest.packagemgnt.PackageMgnt()

    ### Description
    Common methods and properties for PackageMgnt() subclasses

    ### Path
    ``/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/packagemgnt``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.packagemgnt = f"{self.rest}/packagemgnt"
        self.log.debug("ENTERED api.v1.PackageMgnt()")


class EpIssu(PackageMgnt):
    """
    ## api.v1.imagemanagement.rest.packagemgnt.EpIssu()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/api/v1/imagemanagement/rest/packagemgnt/issu``

    ### Verb
    -   GET

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpIssu()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"packagemgnt.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        return f"{self.packagemgnt}/issu"

    @property
    def verb(self):
        return "GET"
