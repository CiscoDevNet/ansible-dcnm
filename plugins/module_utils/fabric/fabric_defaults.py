import logging


class FabricDefaults:
    """
    Return default values for fabric parameters.
    Raise ValueError during refresh() if:
    - template is not set
    - template has no parameters
    - template[parameters] is not a list

    Raise KeyError during parameter() call if:
    - parameter has no default value

    Usage:

    instance = FabricDefaults()
    instance.template = "Easy_Fabric"

    try:
        instance.refresh()
    except ValueError as error:
        print(error)
        exit(1)

    try:
        my_parameter_default_value = instance.parameter("my_parameter")
    except KeyError as error:
        print(error)
        exit(1)
    """
    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._defaults = {}
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

        self._build_defaults()

    def parameter(self, value):
        try:
            return self._defaults[value]
        except KeyError:
            raise KeyError(f"parameter {value} has no default value.")

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

    def _build_defaults(self):
        """
        Caller: refresh()

        Build a dict of default fabric parameter values.
        """
        self._defaults = {}
        for parameter in self.template.get("parameters", []):
            key = parameter["name"]
            value = parameter.get("metaProperties", {}).get("defaultValue", None)
            self._defaults[key] = self.make_boolean(value)
