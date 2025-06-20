"""
Load fixtures for VRF module tests.
"""

from __future__ import absolute_import, division, print_function

# Copyright (c) 2025 Cisco and/or its affiliates.
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
import json
import os
import sys

# pylint: disable=invalid-name
__metaclass__ = type
__copyright__ = "Copyright (c) 2025 Cisco and/or its affiliates."
__author__ = "Allen Robel"
# pylint: enable=invalid-name


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

def load_fixture_data(filename: str, key: str) -> dict[str, str]:
    """
    Return fixture data associated with key from data_file.

    :param filename: The name of the fixture data file.
    :param key: The key to look up in the fixture data.
    :return: The data associated with the key.
    """
    data = load_fixture(filename).get(key)
    print(f"{filename}: {key} : {data}")
    return data

def payloads_vrfs_attachments(key: str) -> dict[str, str]:
    """
    Return VRF payloads.
    """
    filename = "model_payload_vrfs_attachments.json"
    data = load_fixture_data(filename=filename, key=key)
    return data

def playbooks(key: str) -> dict[str, str]:
    """
    Return VRF playbooks.
    """
    filename = "model_playbook_vrf_v12.json"
    data = load_fixture_data(filename=filename, key=key)
    return data
