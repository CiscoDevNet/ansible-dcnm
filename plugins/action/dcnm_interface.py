# Copyright (c) 2020 Cisco and/or its affiliates.
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

import copy
import re
import sys

from ansible_collections.ansible.netcommon.plugins.action.network import (
    ActionModule as ActionNetworkModule,
)
from ansible.module_utils.connection import Connection
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    load_provider,
)
from ansible.utils.display import Display
from pprint import pprint

class ActionModule(ActionNetworkModule):
    def run(self, tmp=None, task_vars=None):

        config = self._task.args.get('config', None)
        if (config is None):
            self.result = super(ActionModule, self).run(task_vars=task_vars)
            return self.result

        for cfg in config:

            if (cfg.get('switch', None) is not None):
                for sw in cfg['switch']:
                    if (isinstance(sw, list)):
                        msg = " Switches included in playbook profiles must be individual items, but given switch element = {} is a list ".format(sw)
                        return {"failed": True, "msg": msg}
                        
            keys = cfg.keys()

            for k in keys:
                
                if (('profile' in k) and (k != 'profile')):
                    msg = " Profile name included in playbook tasks must be 'profile', but given profile name = '{}' ".format(k)
                    return {"failed": True, "msg": msg}
        self.result = super(ActionModule, self).run(task_vars=task_vars)
        return self.result
