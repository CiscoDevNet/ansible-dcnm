#!/usr/bin/python
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
__author__ = "Mallik Mudigonda"

DOCUMENTATION = """
---
module: dcnm_image_upload
short_description: DCNM Ansible Module for managing images.
version_added: "3.5.0"
description:
    - "DCNM Ansible Module for the following image management operations"
    - "Upload, Delete, and Display NXOS images from the controller"

author: Mallik Mudigonda(@mmudigon)
options:
  state:
    description:
    - The required state of the configuration after module completion.
    type: str
    choices: ['merged', 'overridden', 'deleted', 'query']
    default: merged
  files:
    description:
    - A dictionary of images and other related information that is required to download the same.
    type: list
    elements: dict
    default: []
    suboptions:
      path:
        description:
        - Full path to the image that is being uploaded to the controller. For deleting an image
        - the exact image name must be provided.
        type: str
        required: true
      source:
        description:
        - Protocol to be used to download the image from the controller.
        type: str
        choices: ['scp', 'sftp', 'local']
        default: local
      remote_server:
        description:
        - IP address of the server hosting the image. This parameter is required only if source is 'scp'
        - or 'sftp'.
        type: str
        required: true
      user_name:
        description:
        - User name to be used to log into the image hosting server. This parameter is required only if source is 'scp'
        - or 'sftp'.
        type: str
        required: true
      password:
        description:
        - Password to be used to log into the image hosting server. This parameter is required only if source is 'scp'
        - or 'sftp'.
        type: str
        required: true
"""

EXAMPLES = """

# States:
# This module supports the following states:
#
# Merged:
#   Images defined in the playbook will be merged into the controller.
#
#   The images listed in the playbook will be created if not already present on the server
#   server. If the image is already present and the configuration information included
#   in the playbook is either different or not present in server, then the corresponding
#   information is added to the server. If an image mentioned in playbook
#   is already present on the server and there is no difference in configuration, no operation
#   will be performed for such interface.
#
# Overridden:
#   Images defined in the playbook will be overridden in the controller.
#
#   The state of the images listed in the playbook will serve as source of truth for all
#   the images on the controller. Additions and deletions will be done to bring
#   the images on the controller to the state listed in the playbook. All images other than the
#   ones mentioned in the playbook will be deleted.
#   Note: Override will work on the all the images present in the controller.
#
# Deleted:
#   Images defined in the playbook will be deleted from the controller.
#
#   Deletes the list of images specified in the playbook. If the playbook does not include
#   any image information, then all images from the controller will be deleted.
#
# Query:
#   Returns the current state for the images listed in the playbook.

# UPLOAD IMAGES

- name: Upload images to controller
  cisco.dcnm.dcnm_image_upload: &img_upload
    state: merged                             # choose form [merged, deleted, overridden, query], default is merged
    files:
      - path: "full/path/to/image1"           # Full path to the image on the server
        source: scp                           # choose from [local, scp, sftp], default is local
        remote_server: "192.168.1.1"          # mandatory when the source is scp or sftp
        username: "image_upload"              # mandatory when source is scp or sftp
        password: "image_upload"              # mandatory when source is scp or sftp

      - path: "full/path/to/image2"           # Full path to image on local host
        source: local                         # choose from [local, scp, sftp], default is local

      - path: "full/path/to/image3"           # Full path to the image on the server
        source: sftp                          # choose from [local, scp, sftp], default is local
        remote_server: "192.168.1.1"          # mandatory when the source is scp or sftp
        username: "image_upload"              # mandatory when source is scp or sftp
        password: "image_upload"              # mandatory when source is scp or sftp

# DELETE IMAGES

- name: Delete an image
  cisco.dcnm.dcnm_image_upload:
    state: deleted                            # choose form [merged, deleted, overridden, query], default is merged
    files:
      - name: "nxos.9.3.8.bin"                # Name of the image on the controller

- name: Delete an image - without explicitly including any config
  cisco.dcnm.dcnm_image_upload:
    state: deleted                            # choose form [merged, deleted, overridden, query], default is merged

# OVERRIDE IMAGES

- name: Override without any config
  cisco.dcnm.dcnm_image_upload:
    state: overridden                         # choose form [merged, deleted, overridden, query], default is merged

- name: Override with a new config
  cisco.dcnm.dcnm_image_upload: &image_override
    state: overridden                         # choose form [merged, deleted, overridden, query], default is merged
    files:
      - path: "full/path/to/image4"           # Full path to the image on local server
        source: local                         # choose from [local, scp, sftp], default is local

# QUERY IMAGES

- name: Query for existing image
  cisco.dcnm.dcnm_image_upload:
    state: query                              # choose form [merged, deleted, overridden, query], default is merged
    files:
      - name: "nxos.9.3.8.bin"                # Name of the image to be used to filter the output

- name: Query without any filters
  cisco.dcnm.dcnm_image_upload:
    state: query                              # choose form [merged, deleted, overridden, query], default is merged
"""

#
# WARNING:
#   This file is automatically generated. Take a backup of your changes to this file before
#   manually running cg_run.py script to generate it again
#

import os
import json
import copy

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.cisco.dcnm.plugins.module_utils.network.dcnm.dcnm import (
    dcnm_send,
    validate_list_of_dicts,
    dcnm_version_supported,
    dcnm_get_protocol_and_address,
    dcnm_get_auth_token,
    dcnm_post_request,
)


# Resource Class object which includes all the required methods and data to configure and maintain Image_upload
class DcnmImageUpload:
    dcnm_image_upload_paths = {
        11: {
            "DCNM_CREATE_IMAGE_LOCAL": "/imageupload/smart-image-upload",
            "DCNM_CREATE_IMAGE_SCP": "/rest/imageupload/scp-upload",
            "DCNM_CREATE_IMAGE_SFTP": "/rest/imageupload/sftp-upload",
            "DCNM_DELETE_IMAGE": "/rest/imageupload/smart-image",
            "DCNM_GET_IMAGE_LIST": "/rest/imageupload/uploaded-images-table",
        },
        12: {
            "DCNM_CREATE_IMAGE_LOCAL": "/appcenter/cisco/ndfc/api/v1/imagemanagement/imageupload/smart-image-upload",
            "DCNM_CREATE_IMAGE_SCP": "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupload/scp-upload",
            "DCNM_CREATE_IMAGE_SFTP": "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupload/sftp-upload",
            "DCNM_DELETE_IMAGE": "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupload/smart-image",
            "DCNM_GET_IMAGE_LIST": "/appcenter/cisco/ndfc/api/v1/imagemanagement/rest/imageupload/uploaded-images-table",
        },
    }

    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.files = copy.deepcopy(module.params.get("files", []))
        self.image_upload_info = []
        self.want = []
        self.have = []
        self.diff_create = []
        self.diff_delete = []
        self.fd = None
        self.changed_dict = [
            {"merged": [], "deleted": [], "query": [], "debugs": []}
        ]

        self.dcnm_version = dcnm_version_supported(self.module)

        self.paths = self.dcnm_image_upload_paths[self.dcnm_version]
        self.result = dict(changed=False, diff=[], response=[])

    def log_msg(self, msg):

        if self.fd is None:
            self.fd = open("dcnm_image_upload.log", "a+")
        if self.fd is not None:
            self.fd.write(msg)
            self.fd.write("\n")
            self.fd.flush()

    def dcnm_image_upload_get_info_from_dcnm(self):

        """
        Routine to get existing information from DCNM which matches the given object.

        Parameters:
            None

        Returns:
            resp["DATA"] (dict): image_upload informatikon obtained from the DCNM server if it exists
            [] otherwise
        """

        path = self.paths["DCNM_GET_IMAGE_LIST"]

        resp = dcnm_send(self.module, "GET", path)

        if (
            resp
            and (resp["RETURN_CODE"] == 200)
            and resp["MESSAGE"] == "OK"
            and resp["DATA"]
            and resp["DATA"]["lastOperDataObject"]
        ):
            return resp["DATA"]["lastOperDataObject"]
        else:
            return []

    def dcnm_image_upload_get_diff_deleted(self):

        """
        Routine to get a list of payload information that will be used to delete Image_upload.
        This routine updates self.diff_delete with payloads that are used to delete Image_upload
        from the server.

        Parameters:
            None

        Returns:
            None
        """

        del_payload = {"deleteTasksList": []}

        dcnm_image_list = self.dcnm_image_upload_get_info_from_dcnm()

        if self.image_upload_info == []:
            # No image names included. Delete all images
            for img in dcnm_image_list:
                delem = {
                    "platform": img["platform"],
                    "version": img["version"],
                    "imageType": img["imageType"],
                    "imagename": img["imageName"],
                    "osType": img["osType"],
                }
                del_payload["deleteTasksList"].append(delem)
                self.changed_dict[0]["deleted"].append(delem)

        for elem in self.image_upload_info:
            match_elem = [
                img
                for img in dcnm_image_list
                if ((os.path.basename(elem["name"]) == img["imageName"]))
            ]

            for melem in match_elem:
                delem = {
                    "platform": melem["platform"],
                    "version": melem["version"],
                    "imageType": melem["imageType"],
                    "imagename": melem["imageName"],
                    "osType": melem["osType"],
                }
                del_payload["deleteTasksList"].append(delem)
                self.changed_dict[0]["deleted"].append(delem)

        if del_payload["deleteTasksList"] != []:
            self.diff_delete.append(del_payload)

    def dcnm_image_upload_compare_want_and_have(self, want):

        # Check if the image is already present. If present, do not try to upload again
        match_have = [
            elem
            for elem in self.have
            if os.path.basename(want["filePath"]) == elem["imageName"]
        ]

        if match_have:
            # Have found a matching image on the controller. No need to create again
            return "DCNM_IMAGE_UPLOAD_EXIST", [], match_have[0]
        else:
            return "DCNM_IMAGE_UPLOAD_CREATE", [], []

    def dcnm_image_upload_get_diff_merge(self):

        """
        Routine to populate a list of payload information in self.diff_create to create/update Image_upload.

        Parameters:
            None

        Returns:
            None
        """

        if not self.want:
            return

        for elem in self.want:

            rc, reasons, have = self.dcnm_image_upload_compare_want_and_have(
                elem
            )

            if rc == "DCNM_IMAGE_UPLOAD_CREATE":
                # Object does not exists, create a new one.
                if elem not in self.diff_create:
                    self.changed_dict[0]["merged"].append(elem)
                    self.diff_create.append(elem)

    def dcnm_image_upload_get_diff_overridden(self, files):

        # Get all the images that are already present.
        dcnm_image_list = self.dcnm_image_upload_get_info_from_dcnm()

        del_payload = {"deleteTasksList": []}

        if files:
            # User has included some imahe names in the playbook. Check if the file is already present. If
            # yes then do not try to create it again. Also remove this file from the list of files to be deleted.
            for elem in self.want:
                match_elem = [
                    img
                    for img in dcnm_image_list
                    if (
                        (
                            os.path.basename(elem["filePath"])
                            == img["imageName"]
                        )
                    )
                ]

                if match_elem == []:
                    # The image that user is trying to create is not present in the image list.
                    # Add the image from the playbook to create list so that it is created.
                    self.diff_create.append(elem)
                    self.changed_dict[0]["merged"].append(elem)
                else:
                    # There is a match.  User is trying to create an image that is already existing. So remove the matching
                    # image from the image list so that is is not deleted in the following block.
                    dcnm_image_list.remove(match_elem[0])

        # Delete all files from image list
        for img in dcnm_image_list:
            delem = {
                "platform": img["platform"],
                "version": img["version"],
                "imageType": img["imageType"],
                "imagename": img["imageName"],
                "osType": img["osType"],
            }
            del_payload["deleteTasksList"].append(delem)
            self.changed_dict[0]["deleted"].append(delem)
            self.diff_delete.append(del_payload)

    def dcnm_image_upload_get_diff_query(self):

        dcnm_image_list = self.dcnm_image_upload_get_info_from_dcnm()

        if self.image_upload_info == []:
            # No filters specified. Add all images to the output
            self.result["response"].extend(dcnm_image_list)

        for elem in self.image_upload_info:
            # Image names a re provided as filters. Filter the output as required
            match_elem = [
                img
                for img in dcnm_image_list
                if ((os.path.basename(elem["name"]) == img["imageName"]))
            ]
            if match_elem:
                self.result["response"].append(match_elem[0])

    def dcnm_image_upload_get_want(self):

        """
        This routine updates self.want with the payload information based on the playbook configuration.

        Parameters:
            None

        Returns:
            None
        """

        if [] is self.files:
            return

        if not self.image_upload_info:
            return

        for elem in self.image_upload_info:

            payload = self.dcnm_image_upload_get_payload(elem)
            if payload not in self.want:
                self.want.append(payload)

    def dcnm_image_upload_get_have(self):

        """
        Routine to get exisitng image_upload information from DCNM that matches information in self.want.
        This routine updates self.have with all the image_upload that match the given playbook configuration

        Parameters:
            None

        Returns:
            None
        """

        if self.want == []:
            return

        dcnm_image_list = self.dcnm_image_upload_get_info_from_dcnm()

        # Compare the images from want and dcnm_image_list. Keep only those that match
        for want in self.want:
            match_have = [
                elem
                for elem in dcnm_image_list
                if os.path.basename(want["filePath"]) == elem["imageName"]
            ]

            if match_have and match_have[0]["imageName"] not in self.have:
                self.have.append(match_have[0])

    def dcnm_image_upload_validate_query_state_input(self, cfg):

        """
        Playbook input will be different for differnt states. This routine validates the query state
        input. This routine updates self.image_upload_info with validated playbook information related
        to query state.

        Parameters:
            cfg (dict): The config from playbook

        Returns:
           None
        """

        arg_spec = dict(name=dict(required=True, type="str"))

        image_upload_info, invalid_params = validate_list_of_dicts(
            cfg, arg_spec
        )
        if invalid_params:
            mesg = "Invalid parameters in playbook: {0}".format(invalid_params)
            self.module.fail_json(msg=mesg)

        if image_upload_info:
            self.image_upload_info.extend(image_upload_info)

    def dcnm_image_upload_validate_input(self, cfg):

        ldicts = []
        arg_spec = dict(
            path=dict(required=True, type="str"),
            source=dict(type="str", default="local"),
        )

        source = cfg[0].get("source", None)

        if source != "local" and source is not None:
            arg_spec["remote_server"] = dict(required=True, type="str")
            arg_spec["username"] = dict(required=True, type="str")
            arg_spec["password"] = dict(required=True, type="str")

        for elem in arg_spec:
            image_upload_info, invalid_params = validate_list_of_dicts(
                cfg, arg_spec
            )
            if invalid_params:
                mesg = "Invalid parameters in playbook: {0}".format(
                    invalid_params
                )
                self.module.fail_json(msg=mesg)

        if image_upload_info:
            self.image_upload_info.extend(image_upload_info)

    def dcnm_image_upload_validate_deleted_state_input(self, cfg):

        arg_spec = dict(name=dict(required=True, type="str"))

        for elem in arg_spec:
            image_upload_info, invalid_params = validate_list_of_dicts(
                cfg, arg_spec
            )
            if invalid_params:
                mesg = "Invalid parameters in playbook: {0}".format(
                    invalid_params
                )
                self.module.fail_json(msg=mesg)

        if image_upload_info:
            self.image_upload_info.extend(image_upload_info)

    def dcnm_image_upload_validate_all_input(self):

        """
        Routine to validate playbook input based on the state. Since each state has a different
        config structure, this routine handles the validation based on the given state

        Parameters:
            None

        Returns:
            None
        """

        if [] is self.files:
            return

        cfg = []
        for item in self.files:

            citem = copy.deepcopy(item)

            cfg.append(citem)

            if self.module.params["state"] == "query":
                # config for query state is different. So validate query state differently
                self.dcnm_image_upload_validate_query_state_input(cfg)
            elif self.module.params["state"] == "deleted":
                # config for deleted state is different. So validate deleted state differently
                self.dcnm_image_upload_validate_deleted_state_input(cfg)
            else:
                self.dcnm_image_upload_validate_input(cfg)
            cfg.remove(citem)

    def dcnm_image_upload_get_payload(self, image_upload_info):

        """
        This routine builds the complete object payload based on the information in self.want

        Parameters:
            image_upload_info (dict): Object information

        Returns:
            image_upload_payload (dict): Object payload information populated with appropriate data from playbook config
        """

        if image_upload_info["source"] != "local":
            image_upload_payload = {
                # Fill in the parameters that are required for creating/replacing image_upload object
                "server": image_upload_info["remote_server"],
                "filePath": image_upload_info["path"],
                "userName": image_upload_info["username"],
                "password": image_upload_info["password"],
                "acceptHostKey": "false",
                "source": image_upload_info["source"],
            }
        else:
            image_upload_payload = {
                # Fill in the parameters that are required for creating/replacing image_upload object
                "filePath": image_upload_info["path"],
                "source": image_upload_info["source"],
            }

        return image_upload_payload

    def dcnm_image_upload_handle_local_file_transfer(self, elem):

        """
        Routine to read a local file specified in the playbook and transfer the file to DCNM controller

        Parameters:
            elem (dict): A dict containing complete path to local file

        Returns:
            True if file successfully transfered
            False otherwise
        """

        protocol, address = dcnm_get_protocol_and_address(self.module)

        path = protocol + ":" + address + self.paths["DCNM_CREATE_IMAGE_LOCAL"]

        # We should use the authentication token already obtained to send data over this connection.
        # So update the headers with appropriate token details
        headers = {}
        auth_token = dcnm_get_auth_token(self.module)
        headers.update(auth_token)

        file_path = elem.get("filePath", "")

        if file_path:
            upload_files = {"file": open(file_path, "rb")}

            resp = dcnm_post_request(path, headers, False, upload_files)

            self.result["response"].append(resp)

            if resp["DATA"] == "Successfully uploaded selected image file(s).":
                resp["MESSAGE"] = "OK"
                return True
            else:
                resp["MESSAGE"] = ""
                return False
        else:
            return False

    def dcnm_image_upload_send_message_to_dcnm(self):

        """
        Routine to push payloads to DCNM server. This routine implements required error checks and retry mechanisms to handle
        transient errors. This routine checks self.diff_create, self.diff_delete lists and push appropriate requests to DCNM.

        Parameters:
            None

        Returns:
            None
        """

        resp = None
        create_flag = False
        delete_flag = False

        for elem in self.diff_delete:
            path = self.paths["DCNM_DELETE_IMAGE"]
            json_payload = json.dumps(elem)

            resp = dcnm_send(self.module, "DELETE", path, json_payload)

            if resp != []:
                self.result["response"].append(resp)

            if resp and resp.get("RETURN_CODE") != 200:
                resp["CHANGED"] = self.changed_dict[0]
                self.module.fail_json(msg=resp)
            else:
                delete_flag = True

        for elem in self.diff_create:
            source = elem.pop("source")

            if source in ["scp", "sftp"]:
                path = self.paths["DCNM_CREATE_IMAGE_" + source.upper()]
                json_payload = json.dumps(elem)
                resp = dcnm_send(self.module, "POST", path, json_payload)

                if resp != []:
                    self.result["response"].append(resp)
                if resp and resp.get("RETURN_CODE") != 200:
                    resp["CHANGED"] = self.changed_dict[0]
                    self.module.fail_json(msg=resp)
                else:
                    create_flag = True
            else:
                # Source is local and so the file is present on the local host. Read the file
                # and tranfer the contents.

                create_flag = self.dcnm_image_upload_handle_local_file_transfer(
                    elem
                )

        self.result["changed"] = create_flag or delete_flag


def main():

    """ main entry point for module execution
    """
    element_spec = dict(
        files=dict(required=False, type="list", elements="dict", default=[]),
        state=dict(
            type="str",
            default="merged",
            choices=["merged", "deleted", "overridden", "query"],
        ),
    )

    module = AnsibleModule(
        argument_spec=element_spec, supports_check_mode=True
    )

    dcnm_image_upload = DcnmImageUpload(module)

    state = module.params["state"]

    if [] is dcnm_image_upload.files:
        if state == "merged":
            module.fail_json(
                msg="'files' element is mandatory for state '{0}', given = '{1}'".format(
                    state, dcnm_image_upload.config
                )
            )
    dcnm_image_upload.dcnm_image_upload_validate_all_input()

    if (
        module.params["state"] != "query"
        and module.params["state"] != "deleted"
    ):
        dcnm_image_upload.dcnm_image_upload_get_want()
        dcnm_image_upload.dcnm_image_upload_get_have()

    if module.params["state"] == "merged":
        dcnm_image_upload.dcnm_image_upload_get_diff_merge()

    if module.params["state"] == "deleted":
        dcnm_image_upload.dcnm_image_upload_get_diff_deleted()

    if module.params["state"] == "overridden":
        dcnm_image_upload.dcnm_image_upload_get_diff_overridden(
            dcnm_image_upload.files
        )

    if module.params["state"] == "query":
        dcnm_image_upload.dcnm_image_upload_get_diff_query()

    dcnm_image_upload.result["diff"] = dcnm_image_upload.changed_dict

    if dcnm_image_upload.diff_create or dcnm_image_upload.diff_delete:
        dcnm_image_upload.result["changed"] = True

    if module.check_mode:
        dcnm_image_upload.result["changed"] = False
        module.exit_json(**dcnm_image_upload.result)

    dcnm_image_upload.dcnm_image_upload_send_message_to_dcnm()

    module.exit_json(**dcnm_image_upload.result)


if __name__ == "__main__":
    main()
