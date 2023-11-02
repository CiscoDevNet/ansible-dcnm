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
        self.module = module
        self.params = module.params
        self.debug = True
        self.fd = None
        self.logfile = "/tmp/ndfc.log"
        self.module = module

    def _handle_response(self, response, verb):
        if verb == "GET":
            return self._handle_get_response(response)
        if verb in {"POST", "PUT", "DELETE"}:
            return self._handle_post_put_delete_response(response)
        return self._handle_unknown_request_verbs(response, verb)

    def _handle_unknown_request_verbs(self, response, verb):
        msg = f"Unknown request verb ({verb}) in _handle_response() for response {response}."
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
        by setting __init__().debug to False
        """
        if self.debug is False:
            return
        if self.fd is None:
            try:
                self.fd = open(f"{self.logfile}", "a+", encoding="UTF-8")
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
        if value in ["", "none", "None", "NONE", "null", "Null", "NULL"]:
            return None
        return value
