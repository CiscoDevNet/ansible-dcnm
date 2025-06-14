from __future__ import absolute_import, division, print_function

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

# See the following regarding *_fixture imports
# https://pylint.pycqa.org/en/latest/user_guide/messages/warning/redefined-outer-name.html
# Due to the above, we also need to disable unused-import
# pylint: disable=unused-import
# Some fixtures need to use *args to match the signature of the function they are mocking
# pylint: disable=unused-argument
# Some tests require calling protected methods
# pylint: disable=protected-access

__metaclass__ = type

__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Allen Robel"

import json
import os
import sys

fixture_path = os.path.join(os.path.dirname(__file__), "")


def load_fixture(filename):
    """
    load test inputs from json files
    """
    path = os.path.join(fixture_path, f"{filename}")

    try:
        with open(path, encoding="utf-8") as file_handle:
            data = file_handle.read()
    except IOError as exception:
        msg = f"Exception opening test input file {filename} : "
        msg += f"Exception detail: {exception}"
        print(msg)
        sys.exit(1)

    try:
        fixture = json.loads(data)
    except json.JSONDecodeError as exception:
        msg = "Exception reading JSON contents in "
        msg += f"test input file {filename} : "
        msg += f"Exception detail: {exception}"
        print(msg)
        sys.exit(1)

    return fixture

def playbooks(key: str) -> dict[str, str]:
    """
    Return VRF playbooks.
    """
    playbook_file = "model_playbook_vrf_v12.json"
    playbook = load_fixture(playbook_file).get(key)
    print(f"{playbook_file}: {key} : {playbook}")
    return playbook
