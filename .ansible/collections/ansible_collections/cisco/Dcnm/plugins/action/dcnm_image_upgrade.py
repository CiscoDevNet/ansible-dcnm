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

from ansible_collections.ansible.netcommon.plugins.action.network import (
    ActionModule as ActionNetworkModule,
)
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionNetworkModule):
    def run(self, tmp=None, task_vars=None):

        connection = self._connection
        persistent_connect_timeout = connection.get_option("persistent_connect_timeout")
        persistent_command_timeout = connection.get_option("persistent_command_timeout")

        timeout = 1800

        if (persistent_command_timeout < timeout or persistent_connect_timeout < timeout):
            display.warning(
                "PERSISTENT_COMMAND_TIMEOUT is %s"
                % str(persistent_command_timeout),
                self._play_context.remote_addr,
            )
            display.warning(
                "PERSISTENT_CONNECT_TIMEOUT is %s"
                % str(persistent_connect_timeout),
                self._play_context.remote_addr,
            )
            msg = (
                "PERSISTENT_COMMAND_TIMEOUT and PERSISTENT_CONNECT_TIMEOUT"
            )
            msg += " must be set to {0} seconds or higher when using dcnm_image_upgrade module.".format(timeout)
            msg += " Current persistent_command_timeout setting:" + str(
                persistent_command_timeout
            )
            msg += " Current persistent_connect_timeout setting:" + str(
                persistent_connect_timeout
            )
            return {"failed": True, "msg": msg}

        if self._task.args.get('state') == 'merged':
            display.warning("Upgrading switches can take a while.  Please be patient...")
        self.result = super(ActionModule, self).run(task_vars=task_vars)
        return self.result
