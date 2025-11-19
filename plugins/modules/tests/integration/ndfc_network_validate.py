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
module: ndfc_network_validate
short_description: Action plugin to validate NDFC network data.
version_added: "3.5.0"
author: Neil John (@neijohn)
description:
- Action plugin to validate NDFC network data.
- Compares test data against NDFC response data using DeepDiff.
- Supports checking for deleted networks.
options:
    test_data:
        description:
        - Expected network configuration data to validate against.
        required: true
        type: dict
    ndfc_data:
        description:
        - NDFC response data to validate.
        required: true
        type: dict
    config_path:
        description:
        - Path to the YAML configuration file with expected network data.
        required: true
        type: str
    check_deleted:
        description:
        - Whether to check for deleted networks.
        required: false
        type: bool
        default: false
    ignore_fields:
        description:
        - List of fields to ignore during validation.
        required: false
        type: list
        elements: str
"""

EXAMPLES = """
# Validate Network Data
- name: Validate NDFC Network Configuration
  cisco.dcnm.ndfc_network_validate:
    test_data: "{{ test_vars }}"
    ndfc_data: "{{ query_result }}"
    config_path: "{{ playbook_dir }}/configs/networks.yaml"
    ignore_fields: ["networkStatus"]
  register: validation_result
"""
