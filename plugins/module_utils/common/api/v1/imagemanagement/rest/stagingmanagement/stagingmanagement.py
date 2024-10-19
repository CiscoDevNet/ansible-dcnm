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


class StagingManagement(Rest):
    """
    ## api.v1.imagemanagement.rest.stagingmanagement.StagingManagement()

    ### Description
    Common methods and properties for StagingManagement() subclasses

    ### Path
    ``/api/v1/imagemanagement/rest/stagingmanagement``
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.stagingmanagement = f"{self.rest}/stagingmanagement"
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"stagingmanagement.{self.class_name}"
        self.log.debug(msg)


class EpImageStage(StagingManagement):
    """
    ## api.v1.imagemanagement.rest.stagingmanagement.EpImageStage()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/api/v1/imagemanagement/rest/stagingmanagement/stage-image``

    ### Verb
    -   POST

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpImageStage()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"stagingmanagement.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        return f"{self.stagingmanagement}/stage-image"

    @property
    def verb(self):
        return "POST"


class EpImageValidate(StagingManagement):
    """
    ## V1 API - StagingManagement().EpImageValidate()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/api/v1/imagemanagement/rest/stagingmanagement/validate-image``

    ### Verb
    -   POST

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpImageValidate()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"stagingmanagement.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        return f"{self.stagingmanagement}/validate-image"

    @property
    def verb(self):
        return "POST"


class EpStageInfo(StagingManagement):
    """
    ## V1 API - StagingManagement().EpStageInfo()

    ### Description
    Return endpoint information.

    ### Raises
    -   None

    ### Path
    -   ``/api/v1/imagemanagement/rest/stagingmanagement/stage-info``

    ### Verb
    -   GET

    ### Parameters
    -   path: retrieve the path for the endpoint
    -   verb: retrieve the verb for the endpoint

    ### Usage
    ```python
    instance = EpStageInfo()
    path = instance.path
    verb = instance.verb
    ```
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        msg = "ENTERED api.v1.imagemanagement.rest."
        msg += f"stagingmanagement.{self.class_name}"
        self.log.debug(msg)

    @property
    def path(self):
        return f"{self.stagingmanagement}/stage-info"

    @property
    def verb(self):
        return "GET"
