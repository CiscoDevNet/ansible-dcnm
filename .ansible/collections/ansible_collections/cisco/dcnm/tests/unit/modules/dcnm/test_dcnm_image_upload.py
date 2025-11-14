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

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from unittest.mock import patch

from ansible_collections.cisco.dcnm.plugins.modules import dcnm_image_upload
from .dcnm_module import TestDcnmModule, set_module_args, loadPlaybookData


class TestDcnmImageUploadModule(TestDcnmModule):

    module = dcnm_image_upload
    fd = None

    def init_data(self):
        self.fd = None

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("image-upload-ut.log", "a+")
        self.fd.write(msg)

    def setUp(self):

        super(TestDcnmImageUploadModule, self).setUp()

        self.mock_dcnm_send = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upload.dcnm_send"
        )
        self.run_dcnm_send = self.mock_dcnm_send.start()

        self.mock_dcnm_version_supported = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upload.dcnm_version_supported"
        )
        self.run_dcnm_version_supported = (
            self.mock_dcnm_version_supported.start()
        )

        self.mock_dcnm_get_protocol_and_address = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upload.dcnm_get_protocol_and_address"
        )

        self.run_dcnm_get_protocol_and_address = (
            self.mock_dcnm_get_protocol_and_address.start()
        )

        self.mock_dcnm_get_auth_token = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upload.dcnm_get_auth_token"
        )

        self.run_dcnm_get_auth_token = self.mock_dcnm_get_auth_token.start()

        self.mock_dcnm_post_request = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upload.dcnm_post_request"
        )

        self.run_dcnm_post_request = self.mock_dcnm_post_request.start()

        self.mock_open = patch(
            "ansible_collections.cisco.dcnm.plugins.modules.dcnm_image_upload.open"
        )

        self.run_open = self.mock_open.start()

    def tearDown(self):

        super(TestDcnmImageUploadModule, self).tearDown()
        self.mock_dcnm_send.stop()
        self.mock_dcnm_version_supported.stop()
        self.mock_dcnm_get_protocol_and_address.stop()
        self.mock_dcnm_get_auth_token.stop()
        self.mock_dcnm_post_request.stop()

    # -------------------------- FIXTURES --------------------------

    def load_image_upload_fixtures(self):

        if "test_dcnm_image_upload_merged_all_new" == self._testMethodName:

            create_resp = self.payloads_data.get("create_response")
            image_list_no_images_resp = self.payloads_data.get(
                "image_list_no_images_resp"
            )

            self.run_dcnm_send.side_effect = [
                image_list_no_images_resp,
                create_resp,
                create_resp,
                create_resp,
            ]

            self.run_dcnm_post_request.side_effect = [create_resp]

        if "test_dcnm_image_upload_merged_no_source" == self._testMethodName:

            create_resp = self.payloads_data.get("create_response")
            image_list_no_images_resp = self.payloads_data.get(
                "image_list_no_images_resp"
            )

            self.run_dcnm_send.side_effect = [
                image_list_no_images_resp,
                create_resp,
            ]

            self.run_dcnm_post_request.side_effect = [create_resp]

        if "test_dcnm_image_upload_merged_existing" == self._testMethodName:

            image_list_all_images_response = self.payloads_data.get(
                "image_list_all_images_response"
            )

            self.run_dcnm_send.side_effect = [image_list_all_images_response]

        if (
            "test_dcnm_image_upload_merged_new_no_state"
            == self._testMethodName
        ):

            create_resp = self.payloads_data.get("create_response")
            image_list_no_images_resp = self.payloads_data.get(
                "image_list_no_images_resp"
            )

            self.run_dcnm_send.side_effect = [
                image_list_no_images_resp,
                create_resp,
                create_resp,
                create_resp,
            ]

            self.run_dcnm_post_request.side_effect = [create_resp]

        if (
            "test_dcnm_image_upload_merged_new_check_mode"
            == self._testMethodName
        ):
            pass

        if (
            "test_dcnm_image_upload_merged_new_existing_and_non_existing"
            == self._testMethodName
        ):

            create_resp = self.payloads_data.get("create_response")
            image_list_9_3_8_and_9_3_10_image_response = self.payloads_data.get(
                "image_list_9_3_8_and_9_3_10_image_response"
            )

            self.run_dcnm_send.side_effect = [
                image_list_9_3_8_and_9_3_10_image_response,
                create_resp,
            ]

            self.run_dcnm_post_request.side_effect = [create_resp]

        if "test_dcnm_image_upload_delete_existing" == self._testMethodName:

            delete_resp = self.payloads_data.get("delete_response")
            image_list_all_images_response = self.payloads_data.get(
                "image_list_all_images_response"
            )

            self.run_dcnm_send.side_effect = [
                image_list_all_images_response,
                delete_resp,
            ]

        if (
            "test_dcnm_image_upload_delete_existing_and_non_existing"
            == self._testMethodName
        ):

            delete_resp = self.payloads_data.get("delete_response")
            image_list_9_3_8_and_9_3_10_image_response = self.payloads_data.get(
                "image_list_9_3_8_and_9_3_10_image_response"
            )

            self.run_dcnm_send.side_effect = [
                image_list_9_3_8_and_9_3_10_image_response,
                delete_resp,
            ]

        if (
            "test_dcnm_image_upload_delete_non_existing"
            == self._testMethodName
        ):

            image_list_no_images_response = self.payloads_data.get(
                "image_list_no_images_response"
            )

            self.run_dcnm_send.side_effect = [image_list_no_images_response]

        if (
            "test_dcnm_image_upload_delete_without_config"
            == self._testMethodName
        ):

            delete_resp = self.payloads_data.get("delete_response")
            image_list_all_images_response = self.payloads_data.get(
                "image_list_all_images_response"
            )

            self.run_dcnm_send.side_effect = [
                image_list_all_images_response,
                delete_resp,
            ]

        if "test_dcnm_image_upload_delete_one" == self._testMethodName:

            delete_resp = self.payloads_data.get("delete_response")
            image_list_all_images_response = self.payloads_data.get(
                "image_list_all_images_response"
            )

            self.run_dcnm_send.side_effect = [
                image_list_all_images_response,
                delete_resp,
            ]

        if "test_dcnm_image_upload_query_no_config" == self._testMethodName:

            image_list_all_images_response = self.payloads_data.get(
                "image_list_all_images_response"
            )

            self.run_dcnm_send.side_effect = [image_list_all_images_response]

        if "test_dcnm_image_upload_query_one" == self._testMethodName:

            image_list_all_images_response = self.payloads_data.get(
                "image_list_all_images_response"
            )

            self.run_dcnm_send.side_effect = [image_list_all_images_response]

        if "test_dcnm_image_upload_query_all" == self._testMethodName:

            image_list_all_images_response = self.payloads_data.get(
                "image_list_all_images_response"
            )

            self.run_dcnm_send.side_effect = [image_list_all_images_response]

        if "test_dcnm_image_upload_query_non_existing" == self._testMethodName:

            image_list_all_images_response = self.payloads_data.get(
                "image_list_all_images_response"
            )

            self.run_dcnm_send.side_effect = [image_list_all_images_response]

        if "test_dcnm_image_upload_query_2" == self._testMethodName:

            image_list_all_images_response = self.payloads_data.get(
                "image_list_all_images_response"
            )

            self.run_dcnm_send.side_effect = [image_list_all_images_response]

        if (
            "test_dcnm_image_upload_query_exist_and_non_exist"
            == self._testMethodName
        ):

            image_list_all_images_response = self.payloads_data.get(
                "image_list_all_images_response"
            )

            self.run_dcnm_send.side_effect = [image_list_all_images_response]

        if (
            "test_dcnm_image_upload_override_existing_no_config"
            == self._testMethodName
        ):

            delete_resp = self.payloads_data.get("delete_response")
            image_list_all_images_response = self.payloads_data.get(
                "image_list_all_images_response"
            )

            self.run_dcnm_send.side_effect = [
                image_list_all_images_response,
                delete_resp,
                delete_resp,
                delete_resp,
            ]

        if (
            "test_dcnm_image_upload_override_non_existing_no_config"
            == self._testMethodName
        ):

            image_list_no_images_response = self.payloads_data.get(
                "image_list_no_images_response"
            )

            self.run_dcnm_send.side_effect = [image_list_no_images_response]

        if (
            "test_dcnm_image_upload_override_non_existing_with_new_config"
            == self._testMethodName
        ):

            create_resp = self.payloads_data.get("create_response")
            image_list_no_images_response = self.payloads_data.get(
                "image_list_no_images_response"
            )

            self.run_dcnm_send.side_effect = [
                image_list_no_images_response,
                image_list_no_images_response,
                create_resp,
            ]

            self.run_dcnm_post_request.side_effect = [create_resp]

        if (
            "test_dcnm_image_upload_override_existing_with_new_config"
            == self._testMethodName
        ):

            create_resp = self.payloads_data.get("create_response")
            delete_resp = self.payloads_data.get("delete_response")
            image_list_9_3_8_and_9_3_10_image_response = self.payloads_data.get(
                "image_list_9_3_8_and_9_3_10_image_response"
            )

            self.run_dcnm_send.side_effect = [
                image_list_9_3_8_and_9_3_10_image_response,
                image_list_9_3_8_and_9_3_10_image_response,
                delete_resp,
                delete_resp,
                create_resp,
            ]

            self.run_dcnm_post_request.side_effect = [create_resp]

        if (
            "test_dcnm_image_upload_override_with_new_and_existing_config"
            == self._testMethodName
        ):

            create_resp = self.payloads_data.get("create_response")
            image_list_9_3_8_and_9_3_10_image_response = self.payloads_data.get(
                "image_list_9_3_8_and_9_3_10_image_response"
            )

            self.run_dcnm_send.side_effect = [
                image_list_9_3_8_and_9_3_10_image_response,
                image_list_9_3_8_and_9_3_10_image_response,
                create_resp,
            ]

            self.run_dcnm_post_request.side_effect = [create_resp]

    def load_fixtures(self, response=None, device=""):

        self.run_dcnm_version_supported.side_effect = [11]
        self.run_dcnm_get_protocol_and_address.side_effect = [
            ["https", "//10.195.225.193"]
        ]
        self.run_dcnm_get_auth_token.side_effect = [
            {"BearerToken": "SampleTokenForUT1"},
            {"BearerToken": "SampleTokenForUT2"},
            {"BearerToken": "SampleTokenForUT3"},
            {"BearerToken": "SampleTokenForUT4"},
            {"BearerToken": "SampleTokenForUT5"},
            {"BearerToken": "SampleTokenForUT6"},
            {"BearerToken": "SampleTokenForUT7"},
        ]
        self.run_open.side_effect = ["dummy_file"]

        # Load image upload related side-effects
        self.load_image_upload_fixtures()

    # -------------------------- FIXTURES END --------------------------
    # -------------------------- TEST-CASES ----------------------------

    def test_dcnm_image_upload_merged_all_new(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_merge_all_config"
        )

        set_module_args(dict(state="merged", files=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(
                resp["DATA"], "Successfully uploaded selected image file(s)."
            )

    def test_dcnm_image_upload_merged_no_source(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_merge_without_source_config"
        )

        set_module_args(dict(state="merged", files=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(
                resp["DATA"], "Successfully uploaded selected image file(s)."
            )

    def test_dcnm_image_upload_merged_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_merge_all_config"
        )

        set_module_args(dict(state="merged", files=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["response"]), 0)

    def test_dcnm_image_upload_merged_new_no_state(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_merge_all_config"
        )

        set_module_args(dict(files=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(
                resp["DATA"], "Successfully uploaded selected image file(s)."
            )

    def test_dcnm_image_upload_merged_new_check_mode(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_merge_all_config"
        )

        set_module_args(
            dict(
                _ansible_check_mode=True,
                state="merged",
                files=self.playbook_config,
            )
        )
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 3)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["response"]), 0)

    def test_dcnm_image_upload_merged_new_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_merge_all_config"
        )

        set_module_args(dict(state="merged", files=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate create responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)

    def test_dcnm_image_upload_delete_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_delete_all_config"
        )

        set_module_args(dict(state="deleted", files=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["DATA"], "Image(s) Deleted Successfully")

    def test_dcnm_image_upload_delete_existing_and_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_delete_all_config"
        )

        set_module_args(dict(state="deleted", files=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["DATA"], "Image(s) Deleted Successfully")

    def test_dcnm_image_upload_delete_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_delete_all_config"
        )

        set_module_args(dict(state="deleted", files=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["diff"][0]["query"]), 0)
        self.assertEqual(len(result["response"]), 0)

    def test_dcnm_image_upload_delete_without_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = []

        set_module_args(dict(state="deleted", files=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["DATA"], "Image(s) Deleted Successfully")

    def test_dcnm_image_upload_delete_one(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_delete_rpm_config"
        )

        set_module_args(dict(state="deleted", files=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 1)
        self.assertEqual(len(result["diff"][0]["query"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["DATA"], "Image(s) Deleted Successfully")

    def test_dcnm_image_upload_query_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = []

        set_module_args(dict(state="query", files=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["response"]), 3)

    def test_dcnm_image_upload_query_one(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_query_rpm_config"
        )

        set_module_args(dict(state="query", files=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["response"]), 1)

    def test_dcnm_image_upload_query_all(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_query_all_config"
        )

        set_module_args(dict(state="query", files=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["response"]), 3)

    def test_dcnm_image_upload_query_non_existing(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_query_non_exist_config"
        )

        set_module_args(dict(state="query", files=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["response"]), 0)

    def test_dcnm_image_upload_query_2(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_query_9_3_8_and_9_3_10_config"
        )

        set_module_args(dict(state="query", files=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["response"]), 2)

    def test_dcnm_image_upload_query_exist_and_non_exist(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_query_exist_and_non_exist_config"
        )

        set_module_args(dict(state="query", files=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)
        self.assertEqual(len(result["response"]), 1)

    def test_dcnm_image_upload_override_existing_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = []

        set_module_args(dict(state="overridden", files=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 3)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(resp["DATA"], "Image(s) Deleted Successfully")

    def test_dcnm_image_upload_override_non_existing_no_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = []

        set_module_args(dict(state="overridden", files=self.playbook_config))
        result = self.execute_module(changed=False, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 0)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)

    def test_dcnm_image_upload_override_non_existing_with_new_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_override_rpm_config"
        )

        set_module_args(dict(state="overridden", files=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertEqual(
                resp["DATA"], "Successfully uploaded selected image file(s)."
            )

    def test_dcnm_image_upload_override_existing_with_new_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_override_rpm_config"
        )

        set_module_args(dict(state="overridden", files=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 2)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertTrue(
                "Image(s) Deleted Successfully" in resp["DATA"]
                or "Successfully uploaded selected image file(s)."
                in resp["DATA"]
            )

    def test_dcnm_image_upload_override_with_new_and_existing_config(self):

        # load the json from playbooks
        self.config_data = loadPlaybookData("dcnm_image_upload_configs")
        self.payloads_data = loadPlaybookData("dcnm_image_upload_payloads")

        # load required config data
        self.playbook_config = self.config_data.get(
            "image_upload_override_all_new_config"
        )

        set_module_args(dict(state="overridden", files=self.playbook_config))
        result = self.execute_module(changed=True, failed=False)

        self.assertEqual(len(result["diff"][0]["merged"]), 1)
        self.assertEqual(len(result["diff"][0]["deleted"]), 0)

        # Validate delete responses
        for resp in result["response"]:
            self.assertEqual(resp["RETURN_CODE"], 200)
            self.assertTrue(
                "Successfully uploaded selected image file(s)." in resp["DATA"]
            )
