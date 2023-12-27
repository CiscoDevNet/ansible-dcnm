#
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

import sys

class MockAnsibleModule:
    """
    Use as a direct replacement for AnsibleModule when developing
    and testing Ansible modules outside of Ansible.

    Doesn't work with dcnm_send currently since it doesn't
    setup sockets, etc.
    """
    def __init__(self, argument_spec=None, supports_check_mode=None):
        self.params = {}
        self.params["argument_spec"] = argument_spec
        self.params["supports_check_mode"] = supports_check_mode
        self.params["state"] = None
        self.params["config"] = None

    def fail_json(self, msg):
        print(msg)
        sys.exit(1)

    def exit_json(self, **kwargs):
        print(kwargs)
        sys.exit(0)
        
    @property
    def argument_spec(self):
        return self.params["argument_spec"]
    @argument_spec.setter
    def argument_spec(self, value):
        self.params["argument_spec"] = value
    
    @property
    def supports_check_mode(self):
        return self.params["supports_check_mode"]
    @supports_check_mode.setter
    def supports_check_mode(self, value):
        self.params["supports_check_mode"] = value
    
    @property
    def state(self):
        return self.params["state"]
    @state.setter
    def state(self, state):
        self.params["state"] = state

    @property
    def config(self):
        return self.params["config"]
    @config.setter
    def config(self, config):
        self.params["config"] = config
