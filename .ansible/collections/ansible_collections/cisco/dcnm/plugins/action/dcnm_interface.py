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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.ansible.netcommon.plugins.action.network import (
    ActionModule as ActionNetworkModule,
)


class ActionModule(ActionNetworkModule):
    def run(self, tmp=None, task_vars=None):

        msg = ''
        warnings = []
        config = self._task.args.get('config', None)
        if (config is None):
            self.result = super(ActionModule, self).run(task_vars=task_vars)
            return self.result

        for cfg in config:

            pop_key = ''
            flattened = False
            flat_sw_list = []
            if (cfg.get('switch', None) is not None):
                for sw in cfg['switch']:
                    if (isinstance(sw, list)):
                        msg = " !!! Switches included in playbook profiles must be individual items, but given switch element = {0} is a list ".format(sw)
                        warnings.append(msg)
                        flattened = True
                    flat_sw_list.extend(sw)
                if (flattened is True):
                    cfg['switch'] = flat_sw_list

            keys = cfg.keys()

            for k in keys:

                if (('profile' in k) and (k != 'profile')):
                    msg = " !!! Profile name included in playbook tasks must be 'profile', but given profile name = '{0}' ".format(k)
                    warnings.append(msg)
                    pop_key = k

            if (pop_key != ''):
                cfg['profile'] = cfg[pop_key]
                cfg.pop(pop_key)

        self.result = super(ActionModule, self).run(task_vars=task_vars)
        if (warnings):
            self.result['warnings'] = []
            self.result['warnings'].append(warnings)
        return self.result
