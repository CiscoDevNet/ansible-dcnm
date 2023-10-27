# Copyright (c) 2020-2022 Cisco and/or its affiliates.
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

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import json

fixture_path = os.path.join(os.path.dirname(__file__), "fixtures")

def load_fixture(filename):
    path = os.path.join(fixture_path, "{0}.json".format(filename))

    with open(path) as f:
        data = f.read()

    try:
        fixture = json.loads(data)
    except Exception as exception:
        print(f"Exception loading fixture {filename}.  Exception detail: {exception}")

    return fixture


