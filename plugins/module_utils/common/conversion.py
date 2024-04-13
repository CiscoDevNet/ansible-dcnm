class ConversionUtils:
    @staticmethod
    def make_boolean(value):
        """
        - Return value converted to boolean, if possible.
        - Return value, otherwise.
        """
        if str(value).lower() in ["true", "yes"]:
            return True
        if str(value).lower() in ["false", "no"]:
            return False
        return value

    @staticmethod
    def make_int(value):
        """
        - Return value converted to int, if possible.
        - Return value, otherwise.
        """
        # Don't convert boolean values to integers
        if isinstance(value, bool):
            return value
        try:
            return int(value)
        except (ValueError, TypeError):
            return value

    @staticmethod
    def make_none(value):
        """
        - Return None if value is a string representation of a None type
        - Return value, otherwise.
        """
        if str(value).lower() in {"", "none", "null"}:
            return None
        return value

    @staticmethod
    def reject_boolean_string(parameter, value) -> None:
        """
        -   Reject quoted boolean values e.g. "False", "true"
        -   raise ValueError with informative message if the value is
            a string representation of a boolean.
        """
        if isinstance(value, int):
            return
        if isinstance(value, bool):
            return
        if str(value).lower() in ["true", "false"]:
            msg = f"Parameter {parameter}, value '{value}', "
            msg += "is a quoted string representation of a boolean. "
            msg += "Please remove the quotes and try again "
            msg += "(e.g. True/False or true/false, instead of "
            msg += "'True'/'False' or 'true'/'false')."
            raise ValueError(msg)
