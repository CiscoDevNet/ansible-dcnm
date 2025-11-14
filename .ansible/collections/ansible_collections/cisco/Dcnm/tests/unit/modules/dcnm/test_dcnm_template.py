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

from unittest.mock import patch

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_template
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData

from ansible_collections.ansible.netcommon.tests.unit.modules.utils import (
    AnsibleFailJson,
)

import pytest


class TestDcnmTemplateModule(TestDcnmModule):

    module = dcnm_template

    fd = None

    def init_data(self):
        pass

    def log_msg(self, msg):

        if fd is None:
            fd = open("template-ut.log", "w")
        self.fd.write(msg)
        self.fd.flush()

    def setUp(self):

        super(TestDcnmTemplateModule, self).setUp()

        self.mock_dcnm_version_supported = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_template.dcnm_version_supported"
        )
        self.run_dcnm_version_supported = self.mock_dcnm_version_supported.start()

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_template.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()

    def tearDown(self):

        super(TestDcnmTemplateModule, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_version_supported.stop()

    # -------------------------- FIXTURES --------------------------

    def load_template_fixtures(self):

        if "_template_merged_new" in self._testMethodName:

            # No templates exists

            template1 = []
            template2 = []
            template3 = []
            template4 = []

            self.run_dcnm_send.side_effect = [
                template1,
                template2,
                template3,
                template4,
                self.validate_resp,
                self.validate_resp,
                self.validate_resp,
                self.validate_resp,
                self.create_succ_resp,
                self.create_succ_resp,
                self.create_succ_resp,
                self.create_succ_resp,
            ]

        if "_template_merged_new_check_mode" in self._testMethodName:

            # No templates exists

            template1 = []
            template2 = []
            template3 = []
            template4 = []

            self.run_dcnm_send.side_effect = [
                template1,
                template2,
                template3,
                template4,
                self.validate_resp,
                self.validate_resp,
                self.validate_resp,
                self.validate_resp,
            ]

        if "_template_merged_in_use" in self._testMethodName:

            inuse_template1 = self.payloads_data.get("template_110_inuse_have_resp")
            inuse_template2 = self.payloads_data.get("template_111_inuse_have_resp")

            # templates exists and is also in use

            self.run_dcnm_send.side_effect = [
                inuse_template1,
                inuse_template2,
                self.validate_resp,
                self.validate_resp,
                self.create_inuse_resp,
                self.create_inuse_resp,
            ]

        if "_template_merged_existing" in self._testMethodName:

            # Templates exist

            template1 = self.payloads_data.get("template_101_have_resp")
            template2 = self.payloads_data.get("template_102_have_resp")
            template3 = self.payloads_data.get("template_103_have_resp")
            template4 = self.payloads_data.get("template_104_have_resp")

            self.run_dcnm_send.side_effect = [
                template1,
                template2,
                template3,
                template4,
                self.validate_resp,
                self.validate_resp,
                self.validate_resp,
                self.validate_resp,
                self.create_succ_resp,
                self.create_succ_resp,
                self.create_succ_resp,
                self.create_succ_resp,
            ]

        if "_template_delete_existing" in self._testMethodName:

            # Templates exist

            template1 = self.payloads_data.get("template_101_have_resp")
            template2 = self.payloads_data.get("template_102_have_resp")
            template3 = self.payloads_data.get("template_103_have_resp")
            template4 = self.payloads_data.get("template_104_have_resp")

            self.run_dcnm_send.side_effect = [
                template1,
                template2,
                template3,
                template4,
                self.delete_succ_resp,
            ]

        if "_template_delete_inuse" in self._testMethodName:

            # Templates exist

            template1 = self.payloads_data.get("template_101_have_resp")
            template2 = self.payloads_data.get("template_110_inuse_have_resp")
            template3 = self.payloads_data.get("template_111_inuse_have_resp")
            switches = self.payloads_data.get("template_switches")
            policies = self.payloads_data.get("template_policies")

            self.run_dcnm_send.side_effect = [
                template1,
                template2,
                template3,
                self.delete_inuse_resp,
                switches,
                policies,
            ]

        if "_template_delete_inuse_only" in self._testMethodName:

            # Templates exist

            template1 = self.payloads_data.get("template_110_inuse_have_resp")
            template2 = self.payloads_data.get("template_111_inuse_have_resp")
            switches = self.payloads_data.get("template_switches")
            policies = self.payloads_data.get("template_policies")

            self.run_dcnm_send.side_effect = [
                template1,
                template2,
                self.delete_inuse_resp,
                switches,
                policies,
            ]

        if "_template_delete_non_existing" in self._testMethodName:

            # Templates exist

            template1 = []
            template2 = []
            template3 = []
            template4 = []

            self.run_dcnm_send.side_effect = [
                template1,
                template2,
                template3,
                template4,
                self.delete_non_exist_resp,
            ]

        if "_template_replace_existing" in self._testMethodName:

            # Templates exist

            template1 = self.payloads_data.get("template_101_have_resp")

            self.run_dcnm_send.side_effect = [
                template1,
                self.validate_resp,
                self.create_succ_resp,
            ]

        if "_template_replace_no_description" in self._testMethodName:

            # Templates exist

            template1 = self.payloads_data.get("template_101_have_resp")

            self.run_dcnm_send.side_effect = [
                template1,
                self.validate_resp,
                self.create_succ_resp,
            ]

        if "_template_replace_no_tags" in self._testMethodName:

            # Templates exist

            template1 = self.payloads_data.get("template_101_have_resp")

            self.run_dcnm_send.side_effect = [
                template1,
                self.validate_resp,
                self.create_succ_resp,
            ]

        if "_template_replace_one_existing" in self._testMethodName:

            # Templates exist

            template1 = self.payloads_data.get("template_101_have_resp")
            template2 = self.payloads_data.get("template_102_have_resp")
            template3 = self.payloads_data.get("template_103_have_resp")
            template4 = self.payloads_data.get("template_104_have_resp")

            self.run_dcnm_send.side_effect = [
                template1,
                template2,
                template3,
                template4,
                self.validate_resp,
                self.validate_resp,
                self.validate_resp,
                self.validate_resp,
                self.create_succ_resp,
                self.create_succ_resp,
                self.create_succ_resp,
                self.create_succ_resp,
            ]

        if "_template_query_existing" in self._testMethodName:

            # Templates exist

            template1 = self.payloads_data.get("template_101_query_resp")
            template2 = self.payloads_data.get("template_102_query_resp")
            template3 = self.payloads_data.get("template_103_query_resp")
            template4 = self.payloads_data.get("template_104_query_resp")
            switches = self.payloads_data.get("template_switches")
            policies = []

            self.run_dcnm_send.side_effect = [
                template1,
                template2,
                template3,
                template4,
                switches,
                policies,
            ]

        if "_template_query_existing_inuse" in self._testMethodName:

            # Templates exist and in use

            template1 = self.payloads_data.get("template_110_inuse_query_resp")
            template2 = self.payloads_data.get("template_111_inuse_query_resp")
            switches = self.payloads_data.get("template_switches")
            policies = self.payloads_data.get("template_policies")

            self.run_dcnm_send.side_effect = [template1, template2, switches, policies]

        if "_template_validation_fail" in self._testMethodName:

            template1 = []

            self.run_dcnm_send.side_effect = [template1, self.validate_fail_resp]

    def load_fixtures(self, response=None, device=""):

        self.run_dcnm_version_supported.side_effect = [11]

        # Load template related side-effects
        self.load_template_fixtures()

    # -------------------------- TEST-CASES --------------------------

    def test_dcnm_template_wrong_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")

        # load required config data
        self.playbook_config = self.config_data.get("template_merge_new_config")

        set_module_args(dict(state="replaced", config=self.playbook_config))
        result = None
        try:
            result = self.execute_module(changed=False, failed=False)
        except Exception:
            self.assertEqual(result, None)

    def test_dcnm_template_merged_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_merge_new_config")
        self.validate_resp = self.payloads_data.get("template_validate_resp")
        self.create_succ_resp = self.payloads_data.get("template_create_succ_resp")

        set_module_args(dict(state="merged", config=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 4)
        for d in result["diff"][0]["merged"]:
            self.assertEqual(
                (
                    d["template_name"]
                    in ["template_101", "template_102", "template_103", "template_104"]
                ),
                True,
            )

        for r in result["response"]:
            self.assertEqual(("Template Created" in r["DATA"]["status"]), True)

    def test_dcnm_template_merged_new_check_mode(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_merge_new_config")
        self.validate_resp = self.payloads_data.get("template_validate_resp")
        self.create_succ_resp = self.payloads_data.get("template_create_succ_resp")

        set_module_args(
            dict(state="merged", config=self.playbook_config, _ansible_check_mode=True)
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 4)
        self.assertEqual(len(result["response"]), 0)
        for d in result["diff"][0]["merged"]:
            self.assertEqual(
                (
                    d["template_name"]
                    in ["template_101", "template_102", "template_103", "template_104"]
                ),
                True,
            )

    def test_dcnm_template_merged_in_use(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_merge_inuse_config")
        self.validate_resp = self.payloads_data.get("template_validate_resp")
        self.create_inuse_resp = self.payloads_data.get("template_create_in_use_resp")

        set_module_args(dict(state="merged", config=self.playbook_config))

        with pytest.raises(AnsibleFailJson) as failure_msg:
            self.execute_module(changed=False, failed=False)

        fail_data = failure_msg.value.args[0]["msg"]
        print(fail_data)
        self.assertEqual(fail_data["RETURN_CODE"], 500)
        self.assertEqual(fail_data["MESSAGE"], "Internal Server Error")
        self.assertRegex(
            fail_data["DATA"], "Template is already in use.Cannot be overwritten"
        )

    def test_dcnm_template_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_merge_existing_config")
        self.validate_resp = self.payloads_data.get("template_validate_resp")
        self.create_succ_resp = self.payloads_data.get("template_create_succ_resp")

        set_module_args(dict(state="merged", config=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 4)
        for d in result["diff"][0]["merged"]:
            self.assertEqual(
                (
                    d["template_name"]
                    in ["template_101", "template_102", "template_103", "template_104"]
                ),
                True,
            )
        for r in result["response"]:
            self.assertEqual(("Template Created" in r["DATA"]["status"]), True)

    def test_dcnm_template_delete_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_delete_existing_config")
        self.delete_succ_resp = self.payloads_data.get("template_delete_succ_resp")

        set_module_args(dict(state="deleted", config=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 4)
        for r in result["response"]:
            self.assertEqual(("Template deletion successful" in r["DATA"]), True)

    def test_dcnm_template_delete_inuse(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_delete_inuse_config")
        self.delete_inuse_resp = self.payloads_data.get("template_delete_inuse_resp")

        set_module_args(dict(state="deleted", config=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        for r in result["response"]:
            self.assertEqual(("Templates in use, not deleted" in r["DATA"]), True)
            self.assertEqual(("template_101" not in r["DATA"]), True)
            self.assertEqual(("template_110" in r["DATA"]), True)
            self.assertEqual(("template_111" in r["DATA"]), True)

    def test_dcnm_template_delete_inuse_only(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_delete_inuse_only_config")
        self.delete_inuse_resp = self.payloads_data.get("template_delete_inuse_resp")

        set_module_args(dict(state="deleted", config=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        for r in result["response"]:
            self.assertEqual(("Templates in use, not deleted" in r["DATA"]), True)
            self.assertEqual(("template_110" in r["DATA"]), True)
            self.assertEqual(("template_111" in r["DATA"]), True)

    def test_dcnm_template_delete_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "template_delete_non_existing_config"
        )
        self.delete_non_exist_resp = self.payloads_data.get(
            "template_delete_no_exist_resp"
        )

        set_module_args(dict(state="deleted", config=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        for r in result["response"]:
            self.assertEqual((result["response"] == []), True)

    def test_dcnm_template_replace_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_replace_config")
        self.validate_resp = self.payloads_data.get("template_validate_resp")
        self.create_succ_resp = self.payloads_data.get("template_create_succ_resp")

        set_module_args(dict(state="merged", config=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        for d in result["diff"][0]["merged"]:
            self.assertEqual((d["template_name"] in ["template_101"]), True)
            self.assertEqual(("Template_101 being replaced" in d["content"]), True)
            self.assertEqual(
                ("internal policy 101 after replacement" in d["content"]), True
            )
        for r in result["response"]:
            self.assertEqual(("Template Created" in r["DATA"]["status"]), True)

    def test_dcnm_template_replace_one_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_replace_one_config")
        self.validate_resp = self.payloads_data.get("template_validate_resp")
        self.create_succ_resp = self.payloads_data.get("template_create_succ_resp")

        set_module_args(dict(state="merged", config=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        for d in result["diff"][0]["merged"]:
            self.assertEqual((d["template_name"] in ["template_101"]), True)
        for r in result["response"]:
            self.assertEqual(("Template Created" in r["DATA"]["status"]), True)

        r = result["diff"][0]["merged"]

        self.assertEqual(("Template_101 being replaced" in r[0]["content"]), True)
        self.assertEqual(
            ("internal policy 101 after replacement" in r[0]["content"]), True
        )
        self.assertEqual(("destination-group 1001" in r[0]["content"]), True)
        self.assertEqual(("port 51001" in r[0]["content"]), True)
        self.assertEqual(("dst-grp 1001" in r[0]["content"]), True)
        self.assertEqual(("snsr-grp 1001" in r[0]["content"]), True)

    def test_dcnm_template_replace_no_description(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_replace_no_description")
        self.validate_resp = self.payloads_data.get("template_validate_resp")
        self.create_succ_resp = self.payloads_data.get("template_create_succ_resp")

        set_module_args(dict(state="merged", config=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        for d in result["diff"][0]["merged"]:
            self.assertEqual((d["template_name"] in ["template_101"]), True)
        for r in result["response"]:
            self.assertEqual(("Template Created" in r["DATA"]["status"]), True)

        r = result["diff"][0]["merged"]

        self.assertEqual(("Template_101" in r[0]["content"]), True)
        self.assertEqual(
            ("internal policy 101 being replaced" in r[0]["content"]), True
        )

    def test_dcnm_template_replace_no_tags(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_replace_no_tags")
        self.validate_resp = self.payloads_data.get("template_validate_resp")
        self.create_succ_resp = self.payloads_data.get("template_create_succ_resp")

        set_module_args(dict(state="merged", config=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        for d in result["diff"][0]["merged"]:
            self.assertEqual((d["template_name"] in ["template_101"]), True)
        for r in result["response"]:
            self.assertEqual(("Template Created" in r["DATA"]["status"]), True)

        r = result["diff"][0]["merged"]

        self.assertEqual(("internal policy 101" in r[0]["content"]), True)
        self.assertEqual(("Template_101 being replaced" in r[0]["content"]), True)

    def test_dcnm_template_query_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_query_config")

        set_module_args(dict(state="query", config=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["query"]), 4)
        self.assertEqual(len(result["response"]), 4)

        r = result["response"]

        self.assertEqual(("Template_101" in r[0]["content"]), True)
        self.assertEqual(("internal policy 101" in r[0]["content"]), True)
        self.assertEqual(("destination-group 101" in r[0]["content"]), True)
        self.assertEqual(("port 57101" in r[0]["content"]), True)
        self.assertEqual(("dst-grp 101" in r[0]["content"]), True)
        self.assertEqual(("snsr-grp 101" in r[0]["content"]), True)

        self.assertEqual(("Template_102" in r[1]["content"]), True)
        self.assertEqual(("internal policy 102" in r[1]["content"]), True)
        self.assertEqual(("destination-group 102" in r[1]["content"]), True)
        self.assertEqual(("port 57102" in r[1]["content"]), True)
        self.assertEqual(("dst-grp 102" in r[1]["content"]), True)
        self.assertEqual(("snsr-grp 102" in r[1]["content"]), True)

        self.assertEqual(("Template_103" in r[2]["content"]), True)
        self.assertEqual(("internal policy 103" in r[2]["content"]), True)
        self.assertEqual(("destination-group 103" in r[2]["content"]), True)
        self.assertEqual(("port 57103" in r[2]["content"]), True)
        self.assertEqual(("dst-grp 103" in r[2]["content"]), True)
        self.assertEqual(("snsr-grp 103" in r[2]["content"]), True)

        self.assertEqual(("Template_104" in r[3]["content"]), True)
        self.assertEqual(("internal policy 104" in r[3]["content"]), True)
        self.assertEqual(("destination-group 104" in r[3]["content"]), True)
        self.assertEqual(("port 57104" in r[3]["content"]), True)
        self.assertEqual(("dst-grp 104" in r[3]["content"]), True)
        self.assertEqual(("snsr-grp 104" in r[3]["content"]), True)

    def test_dcnm_template_query_existing_inuse(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")

        # load required config data
        self.playbook_config = self.config_data.get("template_query_inuse_config")

        set_module_args(dict(state="query", config=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["query"]), 2)
        self.assertEqual(len(result["response"]), 2)

        r = result["response"]

        self.assertEqual(("Template_110" in r[0]["content"]), True)
        self.assertEqual(("internal policy 110" in r[0]["content"]), True)
        self.assertEqual(("destination-group 101" in r[0]["content"]), True)
        self.assertEqual(("port 57101" in r[0]["content"]), True)
        self.assertEqual(("dst-grp 101" in r[0]["content"]), True)
        self.assertEqual(("snsr-grp 101" in r[0]["content"]), True)

        self.assertEqual(("Template_111" in r[1]["content"]), True)
        self.assertEqual(("internal policy 111" in r[1]["content"]), True)
        self.assertEqual(("destination-group 102" in r[1]["content"]), True)
        self.assertEqual(("port 57102" in r[1]["content"]), True)
        self.assertEqual(("dst-grp 102" in r[1]["content"]), True)
        self.assertEqual(("snsr-grp 102" in r[1]["content"]), True)

        self.assertEqual(len(result["template-policy-map"]), 2)

        self.assertEqual(
            (
                result["template-policy-map"]["template_110_inuse"]["POLICY-35967"][
                    "fabricName"
                ]
                in ["test-fabric"]
            ),
            True,
        )
        self.assertEqual(
            (
                result["template-policy-map"]["template_110_inuse"]["POLICY-35967"][
                    "serialNumber"
                ]
                in ["SAL1812NTBP", "FOX1821H035"]
            ),
            True,
        )

        self.assertEqual(
            (
                result["template-policy-map"]["template_111_inuse"]["POLICY-46328"][
                    "fabricName"
                ]
                in ["test-fabric"]
            ),
            True,
        )
        self.assertEqual(
            (
                result["template-policy-map"]["template_111_inuse"]["POLICY-46328"][
                    "serialNumber"
                ]
                in ["SAL1812NTBP", "FOX1821H035"]
            ),
            True,
        )

    def test_dcnm_template_validation_fail(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_template_configs")
        self.payloads_data = loadPlaybookData("dcnm_template_payloads")
        self.validate_fail_resp = self.payloads_data.get(
            "template_validation_fail_resp"
        )

        # load required config data
        self.playbook_config = self.config_data.get("template_validation_fail_config")

        set_module_args(dict(state="merged", config=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["failed"]), 1)

        errored = False
        for d in result["response"][0]["DATA"]:
            if d["reportItemType"] == "ERROR":
                errored = True

        self.assertEqual(errored, True)
