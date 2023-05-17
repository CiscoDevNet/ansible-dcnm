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
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionNetworkModule):
    def run(self, tmp=None, task_vars=None):

        if (
            self._task.args.get("state") == "merged"
            or self._task.args.get("state") == "overridden"
            or self._task.args.get("state") == "replaced"
        ):
            for con in self._task.args["config"]:
                if "attach" in con:
                    for at in con["attach"]:
                        if "vlan_id" in at:
                            msg = "Playbook parameter vlan_id should not be specified under the attach: block. Please specify this under the config: block instead"  # noqa
                            return {"failed": True, "msg": msg}
                        if "vrf_lite" in at:
                            try:
                                for vl in at["vrf_lite"]:
                                    continue
                            except TypeError:
                                msg = "Please specify interface parameter under vrf_lite section in the playbook"
                                return {"failed": True, "msg": msg}

        self.result = super(ActionModule, self).run(task_vars=task_vars)
        return self.result
