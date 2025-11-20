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
module: ndfc_inventory_validate
short_description: Action plugin to validate NDFC inventory data.
version_added: "3.5.0"
author: Akshayanat Chengam Saravanan (@achengam)
description:
- Action plugin to validate NDFC inventory data.
- Compares test data against NDFC response data and validates according to specified mode.
options:
    test_data:
        description:
        - Expected inventory configuration data to validate against.
        required: true
        type: list
        elements: dict
    ndfc_data:
        description:
        - NDFC response data to validate.
        required: true
        type: dict
    mode:
        description:
        - Validation mode (ip or role).
        required: false
        type: str
        choices: ['ip', 'role']
    changed:
        description:
        - Whether the task resulted in changes.
        required: false
        type: bool
"""

EXAMPLES = """
# Validate Inventory Data
- name: Validate NDFC Inventory
  cisco.dcnm.ndfc_inventory_validate:
    test_data: "{{ expected_inventory }}"
    ndfc_data: "{{ query_result }}"
    mode: "ip"
  register: validation_result
"""
