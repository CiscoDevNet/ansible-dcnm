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

from ..config import Config


class ClassEp(Config):
    """
    ## API endpoints - Api().Config().ClassEp()

    ### Description
    Common methods and properties for Api().Config().Class() subclasses.

    ### Path
    ``/api/config/class``

    ### Notes
    1.  We could not use Class() as the class name since it's a
        reserved Python name.
    2.  Same goes for the directory name (class_ep vs class).
        i.e. imports didn't work when we tried class as a directory name
        or a file name.
    """

    def __init__(self):
        super().__init__()
        self.class_name = self.__class__.__name__
        self.log = logging.getLogger(f"dcnm.{self.class_name}")
        self.log.debug("ENTERED api.config.class_ep.ClassEp()")
        self.class_ep = f"{self.config}/class"
