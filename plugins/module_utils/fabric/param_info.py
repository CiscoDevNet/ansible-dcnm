import logging
import re

class ParamInfo:
    """
    Given a parameter, return a python dict containing parameter info.
    Parameter info culled from the provided template.

    Raise ValueError during refresh() if:
    - template is not set
    - template has no parameters
    - template[parameters] is not a list

    Raise KeyError during parameter() call if:
    - parameter has no default value

    Usage:

    instance = ParamChoices()
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
    """
    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._choices = {}
        self._build_properties()

    def _build_properties(self):
        self.properties = {}
        self.properties["template"] = None

    @property
    def template(self):
        return self.properties["template"]

    @template.setter
    def template(self, value):
        self.properties["template"] = value

    def refresh(self):
        """
        Refresh the defaults based on the template
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
        try:
            return self.info[value]
        except KeyError:
            raise KeyError(f"Parameter {value} not found in self.info")

    @staticmethod
    def make_boolean(value):
        """
        Return value converted to boolean, if possible.
        Otherwise, return value.

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
        Otherwise, return value.
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
        Caller: self._build_info()

        "\"Multicast,Ingress\"" -> ["Multicast", "Ingress"]
        "\"true,false\"" -> [True, False]

        Return a python list of valid parameter choices, if specified
        in the template.
        Return None otherwise.
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
        Caller: self._build_info()

        Return the parameter's default value, if specified in the template.
        Return None otherwise.
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
        Caller: self._build_info()

        Return the parameter's minimum value, if specified in the template.
        Return None otherwise.
        """
        value = parameter.get("metaProperties", {}).get("min", None)
        if value is None:
            return None
        return self.make_int(value)

    def _get_max(self, parameter):
        """
        Caller: self._build_info()

        Return the parameter's maximum value, if specified in the template.
        Return None otherwise.
        """
        value = parameter.get("metaProperties", {}).get("max", None)
        if value is None:
            return None
        return self.make_int(value)

    def _get_type(self, parameter):
        """
        Caller: self._build_info()

        Return the parameter's type, if specified in the template.
        Return None otherwise.
        """
        return parameter.get("parameterType", None)

    def _build_info(self):
        """
        Caller: refresh()

        Build a dict of parameter information.
        key: parameter_name
        value: dict of parameter information

        self.info[parameter_name] = {
            "type": (python type: bool, str, int, dict, set, list, None)
            "choices": (python list, or None)
            "min": (int, or None)
            "max": (int, or None)
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
