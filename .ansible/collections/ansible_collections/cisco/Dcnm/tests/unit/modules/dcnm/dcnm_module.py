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
        self, failed=False, changed=False, response=None, sort=True, device=""
    ):

        self.load_fixtures(response, device=device)

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
