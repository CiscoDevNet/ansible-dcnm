import inspect
import logging
import re


class ParamInfo:
    """
    Given a parameter, return a python dict containing parameter info.
    Parameter info is culled from the provided template.

    Raise ValueError during refresh() if:
    - template is not set
    - template has no parameters
    - template[parameters] is not a list

    Raise KeyError during parameter() call if:
    - parameter has no default value

    Usage:

    ```python
    instance = ParamInfo()
    instance.template = "Easy_Fabric"

    try:
        instance.refresh()
    except ValueError as error:
        print(error)
        exit(1)

    try:
        my_parameter_info = instance.parameter("my_parameter")
    except KeyError as error:
        print(error)
        exit(1)

    parameter_type = my_parameter_info["type"] # python type: bool, str, int, dict, set, list, None
    parameter_choices = my_parameter_info["choices"] # python list, or None
    parameter_min = my_parameter_info["min"] # int, or None
    parameter_max = my_parameter_info["max"] # int, or None
    parameter_default = my_parameter_info["default"] # Any, or None
    ```
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self.info = {}
        self._build_properties()

    def _build_properties(self):
        """
        Initialize the properties dict containing properties used by the class.
        """
        self.properties = {}
        self.properties["template"] = None

    @property
    def template(self):
        """
        - getter : return the template used to cull parameter info.
        - setter : set the template used to cull parameter info.
        - setter : raise TypeError if template is not a dict
        """
        return self.properties["template"]

    @template.setter
    def template(self, value):
        method_name = inspect.stack()[0][3]
        if not isinstance(value, dict):
            msg = f"{self.class_name}.{method_name}: "
            msg += "template must be a dict. "
            msg += f"got {type(value).__name__} for "
            msg += f"value {value}"
            raise TypeError(msg)
        self.properties["template"] = value

    def refresh(self):
        """
        # Refresh the parameter information based on the template

        - raise ValueError if template is not set
        - raise ValueError if template has no parameters
        - raise ValueError if template[parameters] is not a list
        """
        if self.template is None:
            msg = "Call instance.template before calling instance.refresh()."
            raise ValueError(msg)
        if self.template.get("parameters") is None:
            msg = "No parameters in template."
            raise ValueError(msg)
        if isinstance(self.template["parameters"], list) is False:
            msg = "template[parameters] is not a list."
            raise ValueError(msg)

        self._build_info()

    def parameter(self, value):
        """
        # Return parameter information based on the template.

        Usage:

        ```python
        parameter_info = instance.parameter("my_parameter")
        ```

        - raise ``KeyError`` if parameter is not found

        Parameter information is returned as a python dict:

        ```json
        {
            "type": str,
            "choices": ["Ingress", "Multicast"],
            "min": None,
            "max": None,
            "default": "Multicast"
        }
        ```

        - type: (``bool, str, int, dict, set, list, None``),
        - choices: (``list``, or ``None``)
        - min: (``int``, or ``None``)
        - max: (``int``, or ``None``)
        - default: (``str``, ``int``, etc, or ``None``)

        """
        method_name = inspect.stack()[0][3]
        try:
            return self.info[value]
        except KeyError as error:
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Parameter {value} not found in self.info. "
            raise KeyError(msg) from error

    @staticmethod
    def make_boolean(value):
        """
        - Return value converted to boolean, if possible.
        - Returm value, otherwise.

        TODO: This method is duplicated in several other classes.
        TODO: Would be good to move this to a Utility() class.
        """
        if str(value).lower() in ["true", "yes"]:
            return True
        if str(value).lower() in ["false", "no"]:
            return False
        return value

    @staticmethod
    def make_int(value):
        """
        Return value converted to int, if possible.
        Return value, otherwise.
        """
        # Don't convert boolean values to integers
        if isinstance(value, bool):
            return value
        try:
            return int(value)
        except (ValueError, TypeError):
            return value

    def _get_choices(self, parameter):
        """
        -   Return a python list of valid parameter choices, if specified
            in the template.
        -   Return None otherwise.

        Example conversions:

        ```
        "\\"Multicast,Ingress\\"" -> ["Multicast", "Ingress"]
        "\\"1,2\\"" -> [1,2]
        "\\"true,false\\"" -> [False, True]
        ```

        """
        parameter_type = self._get_type(parameter)
        if parameter_type == "boolean":
            return [False, True]
        choices = parameter.get("annotations", {}).get("Enum", None)
        if choices is None:
            return None
        choices = re.sub(r"\"", "", choices)
        choices = choices.split(",")
        choices = [self.make_int(choice) for choice in choices]
        return sorted(choices)

    def _get_default(self, parameter):
        """
        - Return the parameter's default value, if specified in the template.
        - Return None otherwise.
        """
        # default value can be in two places
        value = parameter.get("metaProperties", {}).get("defaultValue", None)
        if value is None:
            value = parameter.get("defaultValue", None)
        if value is None:
            return None

        # make_int() must preceed make_boolean()
        value = self.make_int(value)
        if isinstance(value, int):
            return value
        return self.make_boolean(value)

    def _get_min(self, parameter):
        """
        - Return the parameter's minimum value, if specified in the template.
        - Return None otherwise.
        """
        value = parameter.get("metaProperties", {}).get("min", None)
        if value is None:
            return None
        return self.make_int(value)

    def _get_max(self, parameter):
        """
        - Return the parameter's maximum value, if specified in the template.
        - Return None otherwise.
        """
        value = parameter.get("metaProperties", {}).get("max", None)
        if value is None:
            return None
        return self.make_int(value)

    def _get_type(self, parameter):
        """
        - Return the parameter's type, if specified in the template.
        - Return None otherwise.
        """
        return parameter.get("parameterType", None)

    def _build_info(self) -> None:
        """
        # Build a ``dict`` of parameter information, keyed on parameter name.

        ## Parameter information is culled from the template.

        - type: (``bool, str, int, dict, set, list, None``),
        - choices: (``list``, or ``None``)
        - min: (``int``, or ``None``)
        - max: (``int``, or ``None``)
        - default: (``str``, ``int``, etc, or ``None``)

        Example:

        ```python
        self.info[parameter] = {
            "type": str,
            "choices": ["Ingress", "Multicast"],
            "min": None,
            "max": None,
            "default": "Multicast"
        }
        ```

        """
        self.info = {}
        for parameter in self.template.get("parameters", []):
            param_name = parameter["name"]
            if param_name not in self.info:
                self.info[param_name] = {}
            self.info[param_name]["choices"] = self._get_choices(parameter)
            self.info[param_name]["default"] = self._get_default(parameter)
            self.info[param_name]["max"] = self._get_max(parameter)
            self.info[param_name]["min"] = self._get_min(parameter)
            self.info[param_name]["type"] = self._get_type(parameter)
