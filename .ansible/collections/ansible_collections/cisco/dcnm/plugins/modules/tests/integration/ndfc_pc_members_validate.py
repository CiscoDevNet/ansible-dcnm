#!/usr/bin/python
#
# Copyright (c) 2020-2025 Cisco and/or its affiliates.
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
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
---
module: ndfc_pc_members_validate
short_description: Action plugin to validate NDFC port-channel members data.
version_added: "3.5.0"
author: Mike Wiebe (@mikewiebe)
description:
- Action plugin to validate NDFC port-channel and port-channel member interface data.
- Validates port-channel configurations including trunk, access, L3, and dot1q tunnel modes.
- Checks interface policies and descriptions against expected test data.
options:
    test_data:
        description:
        - Expected port-channel and member interface configuration data to validate against.
        - Must include interface names and expected descriptions for various port-channel types.
        required: true
        type: dict
    ndfc_data:
        description:
        - NDFC response data to validate.
        - Should contain interface configurations from NDFC query.
        required: true
        type: dict
"""

EXAMPLES = """
# Validate Port-Channel Members Data
- name: Validate NDFC Port-Channel and Member Configurations
  cisco.dcnm.ndfc_pc_members_validate:
    test_data: "{{ test_vars }}"
    ndfc_data: "{{ query_result }}"
  register: validation_result
"""
