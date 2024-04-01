import logging


class FabricDefaults:
    def __init__(self):
        self.class_name = self.__class__.__name__

        self.log = logging.getLogger(f"dcnm.{self.class_name}")

        self._default_nv_pairs = {}
        self._build_properties()

    def _build_properties(self):
        self.properties = {}
        self.properties["template"] = None
        self.properties["defaults"] = {}

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

        self._build_default_nv_pairs()

    def parameter(self, value):
        try:
            return self._default_nv_pairs[value]
        except KeyError:
            raise KeyError(f"Parameter {value} not found in default NvPairs")

    @staticmethod
    def make_boolean(value):
        if value in ("true", "True", True):
            return True
        if value in ("false", "False", False):
            return False
        return value

    def _build_default_nv_pairs(self):
        """
        Caller: refresh()

        Build a dict of default fabric nvPairs.
        """
        self._default_nv_pairs = {}
        for parameter in self.template.get("parameters", []):
            key = parameter["name"]
            value = parameter.get("metaProperties", {}).get("defaultValue", None)
            self._default_nv_pairs[key] = self.make_boolean(value)
