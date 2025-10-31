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

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import json

from ansible_collections.ansible.netcommon.tests.unit.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    ModuleTestCase,
)
from ansible_collections.ansible.netcommon.tests.unit.modules.utils import (
    set_module_args as _set_module_args,
)


def set_module_args(args):
    """Store module args for potential action plugin use."""
    if hasattr(TestDcnmModule, '_last_module_args'):
        TestDcnmModule._last_module_args = args
    return _set_module_args(args)


fixture_path = os.path.join(os.path.dirname(__file__), "fixtures")
fixture_data = {}


def loadPlaybookData(module_name):
    path = os.path.join(fixture_path, "{0}.json".format(module_name))

    with open(path) as f:
        data = f.read()

    try:
        j_data = json.loads(data)
    except Exception:
        pass

    return j_data


def load_fixture(module_name, name, device=""):
    path = os.path.join(fixture_path, module_name, device, name)
    if not os.path.exists(path):
        path = os.path.join(fixture_path, module_name, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except Exception:
        pass

    fixture_data[path] = data
    return data


class TestDcnmModule(ModuleTestCase):
    # Class variable to store last module args for action plugin execution
    _last_module_args = None

    def execute_module_devices(
        self, failed=False, changed=False, response=None, sort=True, defaults=False
    ):
        module_name = self.module.__name__.rsplit(".", 1)[1]
        local_fixture_path = os.path.join(fixture_path, module_name)

        models = []
        for path in os.listdir(local_fixture_path):
            path = os.path.join(local_fixture_path, path)
            if os.path.isdir(path):
                models.append(os.path.basename(path))
        if not models:
            models = [""]

        retvals = {}
        for model in models:
            retvals[model] = self.execute_module(
                failed, changed, response, sort, device=model
            )

        return retvals

    def execute_module(
        self, failed=False, changed=False, response=None, sort=True, device="", use_action_plugin=False
    ):

        self.load_fixtures(response, device=device)

        if use_action_plugin:
            result = self._execute_via_action_plugin(failed, changed)
        else:
            if failed:
                result = self.failed()
                self.assertTrue(result["failed"], result)
            else:
                result = self.changed(changed)
                self.assertEqual(result["changed"], changed, result)

        if response is not None:
            if sort:
                self.assertEqual(
                    sorted(response), sorted(result["response"]), result["response"]
                )
            else:
                self.assertEqual(response, result["response"], result["response"])

        return result

    def failed(self):
        with self.assertRaises(AnsibleFailJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        self.assertTrue(result["failed"], result)
        return result

    def changed(self, changed=False):
        with self.assertRaises(AnsibleExitJson) as exc:
            self.module.main()

        result = exc.exception.args[0]
        self.assertEqual(result["changed"], changed, result)
        return result

    def load_fixtures(self, response=None, device=""):
        pass

    def _execute_via_action_plugin(self, failed=False, changed=False):
        """
        Execute the module via its action plugin instead of directly.

        This method simulates Ansible's action plugin execution flow by:
        1. Importing the action plugin for the module
        2. Creating a mock ActionBase execution context
        3. Calling the action plugin's run() method
        4. The action plugin then calls the module internally

        Args:
            failed (bool): Whether the execution is expected to fail
            changed (bool): Whether the execution is expected to result in changes

        Returns:
            dict: The result dictionary from action plugin execution
        """
        from unittest.mock import Mock, patch
        from ansible.playbook.task import Task
        import importlib

        # Get module name from the test class's module attribute
        module_name = self.module.__name__.rsplit(".", 1)[1]

        # Construct the action plugin name (should be same as module name)
        action_plugin_name = f"cisco.dcnm.{module_name}"

        # Try to import the action plugin directly instead of using action_loader
        try:
            action_module = importlib.import_module(f"ansible_collections.cisco.dcnm.plugins.action.{module_name}")
            action_plugin = action_module.ActionModule
        except (ImportError, AttributeError):
            action_plugin = None

        if action_plugin is None:
            # If no action plugin exists, fall back to direct module execution
            if failed:
                result = self.failed()
                self.assertTrue(result["failed"], result)
            else:
                result = self.changed(changed)
                self.assertEqual(result["changed"], changed, result)
            return result

        # Create mock objects for action plugin execution context
        mock_connection = Mock()
        mock_play_context = Mock()
        mock_loader = Mock()
        mock_templar = Mock()
        mock_shared_loader_obj = Mock()

        # Create a mock task with the module arguments
        mock_task = Mock(spec=Task)
        mock_task.args = self._last_module_args if self._last_module_args else {}
        mock_task.async_val = 0
        mock_task.action = action_plugin_name

        # Instantiate the action plugin
        action = action_plugin(
            task=mock_task,
            connection=mock_connection,
            play_context=mock_play_context,
            loader=mock_loader,
            templar=mock_templar,
            shared_loader_obj=mock_shared_loader_obj
        )

        # Mock the _execute_module method on the action plugin to call our module directly
        # This preserves the existing test mocking behavior
        original_execute_module = action._execute_module

        def mock_execute_module(module_name=None, module_args=None, task_vars=None, tmp=None, **kwargs):
            # Handle fabric associations API call from action plugin
            if module_name == "cisco.dcnm.dcnm_rest":
                # Return the mocked fabric_associations response directly
                path = module_args.get('path', '') if module_args else ''
                method = module_args.get('method', 'GET') if module_args else 'GET'
                if '/fabric-associations' in path:
                    if hasattr(self, 'fabric_associations'):
                        return {'response': self.fabric_associations, 'failed': False}
                elif 'vrfs' in path:
                    if '/vrfs' in path or 'top-down' in path:
                        return {'response': self.vrf_ready_data, 'failed': False}
                return {'failed': True, 'msg': 'Rest Module Mocks not provided'}

            # Set the module args if provided for dcnm_network module
            if module_args:
                set_module_args(module_args)

            # Execute the module using the standard test flow
            if failed:
                return self.failed()
            else:
                return self.changed(changed)

        # Patch _execute_module to use our mock
        with patch.object(action, '_execute_module', side_effect=mock_execute_module):
            # Execute the action plugin's run method
            # The action plugin will call _execute_module internally
            result = action.run(tmp=None, task_vars={})

        # Validate results
        if failed:
            self.assertTrue(result.get("failed", False), result)
        else:
            self.assertEqual(result.get("changed", False), changed, result)

        return result
