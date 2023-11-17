"""
Base class for the other image upgrade classes
"""
from __future__ import absolute_import, division, print_function

# disabling pylint invalid-name for Ansible standard boilerplate
__metaclass__ = type  # pylint: disable=invalid-name

import inspect


class ImageUpgradeCommon:
    """
    Base class for the other image upgrade classes

    Usage (where module is an instance of AnsibleModule):

    class MyClass(ImageUpgradeCommon):
        def __init__(self, module):
            super().__init__(module)
        ...
    """

    def __init__(self, module):
        self.class_name = __class__.__name__
        self.method_name = inspect.stack()[0][3]

        self.module = module
        self.params = module.params
        self.debug = False
        self.fd = None
        self.logfile = "/tmp/ansible_dcnm.log"
        self.module = module
        self.log_msg("ImageUpgradeCommon.__init__ DONE")

    def _handle_response(self, response, verb):
        # don't add self.method_name to this method since
        # it is called by other methods and we want their
        # method_names in the log

        if verb == "GET":
            return self._handle_get_response(response)
        if verb in {"POST", "PUT", "DELETE"}:
            return self._handle_post_put_delete_response(response)
        return self._handle_unknown_request_verbs(response, verb)

    def _handle_unknown_request_verbs(self, response, verb):
        self.method_name = inspect.stack()[0][3]

        msg = f"{self.class_name}.{self.method_name}: "
        msg += f"Unknown request verb ({verb}) for response {response}."
        self.module.fail_json(msg)

    def _handle_get_response(self, response):
        """
        Caller:
            - self._handle_response()
        Handle controller responses to GET requests
        Returns: dict() with the following keys:
        - found:
            - False, if request error was "Not found" and RETURN_CODE == 404
            - True otherwise
        - success:
            - False if RETURN_CODE != 200 or MESSAGE != "OK"
            - True otherwise
        """
        # don't add self.method_name to this method since
        # it is called by other methods and we want their
        # method_names in the log

        result = {}
        success_return_codes = {200, 404}
        if (
            response.get("RETURN_CODE") == 404
            and response.get("MESSAGE") == "Not Found"
        ):
            result["found"] = False
            result["success"] = True
            return result
        if (
            response.get("RETURN_CODE") not in success_return_codes
            or response.get("MESSAGE") != "OK"
        ):
            result["found"] = False
            result["success"] = False
            return result
        result["found"] = True
        result["success"] = True
        return result

    def _handle_post_put_delete_response(self, response):
        """
        Caller:
            - self.self._handle_response()

        Handle POST, PUT responses from the controller.

        Returns: dict() with the following keys:
        - changed:
            - True if changes were made to by the controller
            - False otherwise
        - success:
            - False if RETURN_CODE != 200 or MESSAGE != "OK"
            - True otherwise
        """
        # don't add self.method_name to this method since
        # it is called by other methods and we want their
        # method_names in the log

        result = {}
        if response.get("ERROR") is not None:
            result["success"] = False
            result["changed"] = False
            return result
        if response.get("MESSAGE") != "OK" and response.get("MESSAGE") is not None:
            result["success"] = False
            result["changed"] = False
            return result
        result["success"] = True
        result["changed"] = True
        return result

    def log_msg(self, msg):
        """
        used for debugging. disable this when committing to main
        by setting self.debug to False in __init__()
        """
        if self.debug is False:
            return
        if self.fd is None:
            try:
                # since we need self.fd open throughout several classes
                # we are disabling pylint R1732
                self.fd = open(
                    f"{self.logfile}", "a+", encoding="UTF-8"
                )  # pylint: disable=consider-using-with
            except IOError as err:
                msg = f"error opening logfile {self.logfile}. "
                msg += f"detail: {err}"
                self.module.fail_json(msg)

        self.fd.write(msg)
        self.fd.write("\n")
        self.fd.flush()

    def make_boolean(self, value):
        """
        Return value converted to boolean, if possible.
        Return value, if value cannot be converted.
        """
        self.method_name = inspect.stack()[0][3]

        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ["true", "yes"]:
                return True
            if value.lower() in ["false", "no"]:
                return False
        return value

    def make_none(self, value):
        """
        Return None if value is an empty string, or a string
        representation of a None type
        Return value otherwise
        """
        self.method_name = inspect.stack()[0][3]

        if value in ["", "none", "None", "NONE", "null", "Null", "NULL"]:
            return None
        return value
