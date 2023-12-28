# #
# # Copyright (c) 2024 Cisco and/or its affiliates.
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #     http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.

# from __future__ import absolute_import, division, print_function

# __metaclass__ = type
# __author__ = "Allen Robel"

# import inspect
# from typing import Any, Dict
# from ansible_collections.cisco.dcnm.plugins.module_utils.common.log import \
#     Log

# class ImagePolicyCommon:
#     """
#     Common methods used by the other classes supporting
#     dcnm_image_policy module

#     Usage (where ansible_module is an instance of
#     AnsibleModule or MockAnsibleModule):

#     class MyClass(ImagePolicyCommon):
#         def __init__(self, module):
#             super().__init__(module)
#         ...
#     """

#     def __init__(self, ansible_module):
#         self.class_name = self.__class__.__name__

#         self.ansible_module = ansible_module
#         self.params = ansible_module.params

#         self.log = Log(ansible_module)
#         self.log.debug = False
#         self.log.logfile = "/tmp/dcnm_image_policy.log"

#         self.log.log_msg("ImageUpgradeCommon.__init__ DONE")

#     def _handle_response(self, response, verb):
#         """
#         Call the appropriate handler for response based on verb
#         """
#         if verb == "GET":
#             return self._handle_get_response(response)
#         if verb in {"POST", "PUT", "DELETE"}:
#             return self._handle_post_put_delete_response(response)
#         return self._handle_unknown_request_verbs(response, verb)

#     def _handle_unknown_request_verbs(self, response, verb):
#         method_name = inspect.stack()[0][3]

#         msg = f"{self.class_name}.{method_name}: "
#         msg += f"Unknown request verb ({verb}) for response {response}."
#         self.ansible_module.fail_json(msg)

#     def _handle_get_response(self, response):
#         """
#         Caller:
#             - self._handle_response()
#         Handle controller responses to GET requests
#         Returns: dict() with the following keys:
#         - found:
#             - False, if request error was "Not found" and RETURN_CODE == 404
#             - True otherwise
#         - success:
#             - False if RETURN_CODE != 200 or MESSAGE != "OK"
#             - True otherwise
#         """
#         result = {}
#         success_return_codes = {200, 404}
#         if (
#             response.get("RETURN_CODE") == 404
#             and response.get("MESSAGE") == "Not Found"
#         ):
#             result["found"] = False
#             result["success"] = True
#             return result
#         if (
#             response.get("RETURN_CODE") not in success_return_codes
#             or response.get("MESSAGE") != "OK"
#         ):
#             result["found"] = False
#             result["success"] = False
#             return result
#         result["found"] = True
#         result["success"] = True
#         return result

#     def _handle_post_put_delete_response(self, response):
#         """
#         Caller:
#             - self.self._handle_response()

#         Handle POST, PUT responses from the controller.

#         Returns: dict() with the following keys:
#         - changed:
#             - True if changes were made to by the controller
#             - False otherwise
#         - success:
#             - False if RETURN_CODE != 200 or MESSAGE != "OK"
#             - True otherwise
#         """
#         result = {}
#         if response.get("ERROR") is not None:
#             result["success"] = False
#             result["changed"] = False
#             return result
#         if response.get("MESSAGE") != "OK" and response.get("MESSAGE") is not None:
#             result["success"] = False
#             result["changed"] = False
#             return result
#         result["success"] = True
#         result["changed"] = True
#         return result

#     def make_boolean(self, value):
#         """
#         Return value converted to boolean, if possible.
#         Return value, if value cannot be converted.
#         """
#         if isinstance(value, bool):
#             return value
#         if isinstance(value, str):
#             if value.lower() in ["true", "yes"]:
#                 return True
#             if value.lower() in ["false", "no"]:
#                 return False
#         return value

#     def make_none(self, value):
#         """
#         Return None if value is an empty string, or a string
#         representation of a None type
#         Return value otherwise
#         """
#         if value in ["", "none", "None", "NONE", "null", "Null", "NULL"]:
#             return None
#         return value


# class ParamsSpec:
#     """
#     Parameter specifications for the dcnm_image_policy module.
#     """
#     def __init__(self, ansible_module):
#         self.ansible_module = ansible_module
#         self._params_spec: Dict[str, Any] = {}

#     def commit(self):
#         if self.ansible_module.state == None:
#             self.ansible_module.fail_json(msg="state is None")

#         if self.ansible_module.state == "merged":
#             #self._build_params_spec_for_merged_state()
#             self._build_params_spec_for_merged_state_proposed()
#         elif self.ansible_module.state == "replaced":
#             self._build_params_spec_for_replaced_state()
#         elif self.ansible_module.state == "overridden":
#             self._build_params_spec_for_overridden_state()
#         elif self.ansible_module.state == "deleted":
#             self._build_params_spec_for_deleted_state()
#         elif self.ansible_module.state == "query":
#             self._build_params_spec_for_query_state()
#         else:
#             self.ansible_module.fail_json(msg="Invalid state")

#     def _build_params_spec_for_merged_state(self) -> None:
#         """
#         Build the specs for the parameters expected when state == merged.

#         Caller: _validate_configs()
#         Return: params_spec, a dictionary containing playbook
#                 parameter specifications.
#         """
#         print("Building params spec for merged state")
#         self._params_spec: Dict[str, Any] = {}
#         self._params_spec["name"] = {}
#         self._params_spec["name"]["required"] = True
#         self._params_spec["name"]["type"] = "str"

#         self._params_spec["description"] = {}
#         self._params_spec["description"]["default"] = ""
#         self._params_spec["description"]["required"] = False
#         self._params_spec["description"]["type"] = "str"

#         self._params_spec["disabled_rpm"] = {}
#         self._params_spec["disabled_rpm"]["default"] = ""
#         self._params_spec["disabled_rpm"]["required"] = False
#         self._params_spec["disabled_rpm"]["type"] = "str"

#         self._params_spec["epld_image"] = {}
#         self._params_spec["epld_image"]["required"] = False
#         self._params_spec["epld_image"]["type"] = "str"

#         self._params_spec["platform"] = {}
#         self._params_spec["platform"]["required"] = True
#         self._params_spec["platform"]["type"] = "str"
#         self._params_spec["platform"]["choices"] = ["N9K", "N7K", "N77", "N6K", "N5K"]

#         self._params_spec["release"] = {}
#         self._params_spec["release"]["required"] = True
#         self._params_spec["release"]["type"] = "str"

#         self._params_spec["packages"] = {}
#         self._params_spec["packages"]["required"] = False
#         self._params_spec["packages"]["type"] = "list"

#         self._params_spec["agnostic"] = {}
#         self._params_spec["agnostic"]["required"] = False
#         self._params_spec["agnostic"]["type"] = "bool"
#         self._params_spec["agnostic"]["default"] = False

#     def _build_params_spec_for_merged_state_proposed(self) -> None:
#         """
#         Build the specs for the parameters expected when state == merged.

#         Caller: _validate_configs()
#         Return: params_spec, a dictionary containing playbook
#                 parameter specifications.
#         """
#         print("Building params spec for merged state PROPOSED")
#         self._params_spec: Dict[str, Any] = {}
#         self._params_spec["name"] = {}
#         self._params_spec["name"]["required"] = True
#         self._params_spec["name"]["type"] = "str"

#         self._params_spec["description"] = {}
#         self._params_spec["description"]["default"] = ""
#         self._params_spec["description"]["required"] = False
#         self._params_spec["description"]["type"] = "str"

#         self._params_spec["disabled_rpm"] = {}
#         self._params_spec["disabled_rpm"]["default"] = ""
#         self._params_spec["disabled_rpm"]["required"] = False
#         self._params_spec["disabled_rpm"]["type"] = "str"

#         self._params_spec["epld_image"] = {}
#         self._params_spec["epld_image"]["required"] = False
#         self._params_spec["epld_image"]["type"] = "str"

#         self._params_spec["platform"] = {}
#         self._params_spec["platform"]["required"] = True
#         self._params_spec["platform"]["type"] = "str"
#         self._params_spec["platform"]["choices"] = ["N9K", "N7K", "N77", "N6K", "N5K"]

#         self._params_spec["release"] = {}
#         self._params_spec["release"]["required"] = True
#         self._params_spec["release"]["type"] = "str"

#         self._params_spec["packages"] = {}
#         self._params_spec["packages"]["required"] = False
#         self._params_spec["packages"]["type"] = "dict"

#         self._params_spec["packages"]["install"] = {}
#         self._params_spec["packages"]["install"]["required"] = False
#         self._params_spec["packages"]["install"]["type"] = "list"

#         self._params_spec["packages"]["uninstall"] = {}
#         self._params_spec["packages"]["uninstall"]["required"] = False
#         self._params_spec["packages"]["uninstall"]["type"] = "list"

#         self._params_spec["agnostic"] = {}
#         self._params_spec["agnostic"]["required"] = False
#         self._params_spec["agnostic"]["type"] = "bool"
#         self._params_spec["agnostic"]["default"] = False

#     @property
#     def params_spec(self) -> Dict[str, Any]:
#         return self._params_spec


# class Payload:
#     """
#     Build the payload for the dcnm_image_policy module.
#     """
#     def __init__(self, ansible_module):
#         self.ansible_module = ansible_module
#         self._payload: Dict[str, Any] = {}
#         self._config: Dict[str, Any] = {}

#     def commit(self):
#         method_name = inspect.stack()[0][3]

#         if self.ansible_module.state == "merged":
#             self._build_payload_for_merged_state()
#         elif self.ansible_module.state == "replaced":
#             self._build_payload_for_replaced_state()
#         elif self.ansible_module.state == "overridden":
#             self._build_payload_for_overridden_state()
#         elif self.ansible_module.state == "deleted":
#             self._build_payload_for_deleted_state()
#         elif self.ansible_module.state == "query":
#             self._build_payload_for_query_state()
#         else:
#             msg = f"{self.class_name}.{method_name}: "
#             msg += "Invalid state {self.ansible_module.state}"
#             self.ansible_module.fail_json(msg)

#     def _build_payload_for_merged_state(self):
#         method_name = inspect.stack()[0][3]

#         if self.config == {}:
#             msg = f"{self.class_name}.{method_name}: "
#             msg += "self.config is empty"
#             self.ansible_module.fail_json(msg)

#         self._payload["agnostic"] = self.config["agnostic"]
#         self._payload["epldImgName"] = self.config["epld_image"]
#         self._payload["nxosVersion"] = self.config["release"]
#         self._payload["platform"] = self.config["platform"]
#         self._payload["policyDescr"] = self.config["description"]
#         self._payload["policyName"] = self.config["name"]
#         self._payload["policyType"] = "PLATFORM"

#         if len(self.config.get("packages", {}).get("install", [])) != 0:
#             self._payload["packageName"] = ','.join(self.config["packages"]["install"])
#         if len(self.config.get("packages", {}).get("uninstall", [])) != 0:
#             self._payload["rpmimages"] = ','.join(self.config["packages"]["uninstall"])

#     @property
#     def payload(self):
#         if self._payload == {}:
#             self.commit()
#         return self._payload

#     @property
#     def config(self):
#         return self._config
#     @config.setter
#     def config(self, value):
#         if not isinstance(value, dict):
#             self.ansible_module.fail_json(msg="config must be a dictionary")
#         self._config = value
