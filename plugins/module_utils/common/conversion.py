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
