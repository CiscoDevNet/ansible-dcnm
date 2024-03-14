#!/usr/bin/env python
"""
Name: ndfc_template.py
Description:

Superclass for NdfcTemplateEasyFabric() and NdfcTemplateAll()
"""
import re


class TemplateParseCommon:
    """
    Superclass for TemplateParse*() classes
    """

    def __init__(self):
        self._properties = {}
        self._properties["template"] = None

    @property
    def template(self):
        """
        The template contents supported by the subclass
        """
        return self._properties["template"]

    @template.setter
    def template(self, value):
        self._properties["template"] = value

    @staticmethod
    def delete_key(key, dictionary):
        """
        Delete key from dictionary
        """
        if key in dictionary:
            del dictionary[key]
        return dictionary

    def get_default_value_meta_properties(self, item):
        """
        Return defaultValue of metaProperties item, if any
        Return None otherwise
        """
        try:
            result = item["metaProperties"]["defaultValue"]
        except KeyError:
            return None
        return self.clean_string(result)

    def get_default_value_root(self, item):
        """
        Return defaultValue of a root item, if any
        Return None otherwise
        """
        try:
            result = item["defaultValue"]
        except KeyError:
            return None
        return self.clean_string(result)

    def get_default_value(self, item):
        """
        Return the default value for item, if it exists.
        Return None otherwise.
        """
        result = self.get_default_value_meta_properties(item)
        if result is not None:
            return result
        result = self.get_default_value_root(item)
        return result

    def get_description(self, item):
        """
        Return the description of an item, i.e.:
        item['annotations']['Description']
        """
        try:
            description = item["annotations"]["Description"]
        except KeyError:
            description = "unknown"
        return self.clean_string(description)

    def get_dict_value(self, dictionary, key):
        """
        Return value of the first instance of key found via
        recursive search of dictionary

        Return None if key is not found
        """
        if not isinstance(dictionary, dict):
            return None
        if key in dictionary:
            return dictionary[key]
        for k, v in dictionary.items():  # pylint: disable=unused-variable
            if isinstance(v, dict):
                item = self.get_dict_value(v, key)
                if item is not None:
                    return item
        return None

    def get_display_name(self, item):
        """
        Return the NDFC GUI label for an item, i.e.:
        item['annotations']['DisplayName']
        """
        result = self.get_dict_value(item, "DisplayName")
        return self.clean_string(result)

    def get_enum(self, item):
        """
        Return the enum for an item as a list()
        Return an empty list if the key does not exist
        item["annotations"]["Enum"]
        """
        result = self.get_dict_value(item, "Enum")
        if result is None:
            return []
        # if "annotations" not in item:
        #     return []
        # if "Enum" not in item["annotations"]:
        #     return []
        result = self.clean_string(result)
        result = result.split(",")
        try:
            result = [int(x) for x in result]
        except ValueError:
            pass
        return result

    def get_min_max(self, item):
        """
        Return the min and max values of an item from the item's description
        Otherwise return None, None

        If item['annotations']['Description'] contains
        "(Min: X, Max: Y)" return int(X), and int(Y)
        """
        result = self.get_dict_value(item, "Description")
        if result is None:
            return None, None
        # (Min:240, Max:3600)
        m = re.search(r"\(Min:\s*(\d+),\s*Max:\s*(\d+)\)", result)
        if m:
            return int(m.group(1)), int(m.group(2))
        return None, None

    def get_min(self, item):
        """
        Return the minimum value of an item
        Otherwise return None

        Typically, item['metaProperties']['min']
        """
        result = self.get_dict_value(item, "min")
        return self.clean_string(result)

    def get_max(self, item):
        """
        Return the maximum value of an item
        Otherwise return None

        Typically, item['metaProperties']['max']
        """
        result = self.get_dict_value(item, "max")
        return self.clean_string(result)

    def get_min_length(self, item):
        """
        Return the minimum length of an item
        Otherwise return None

        Typically, item['metaProperties']['minLength']
        """
        result = self.get_dict_value(item, "minLength")
        return self.clean_string(result)

    def get_max_length(self, item):
        """
        Return the maximum length of an item
        Otherwise return None

        Typically, item['metaProperties']['maxLength']
        """
        result = self.get_dict_value(item, "minLength")
        return self.clean_string(result)

    def get_name(self, item):
        """
        Return the name of an item
        Otherwise return None

        Typically, item['name']
        """
        try:
            result = item["name"]
        except KeyError:
            result = "unknown"
        return self.clean_string(result)

    def is_internal(self, item):
        """
        Return True if item["annotations"]["IsInternal"] is True
        Return False otherwise
        """
        result = self.get_dict_value(item, "IsInternal")
        return self.make_bool(result)

    def is_optional(self, item):
        """
        Return the optional status of an item (True or False) if it exists.

        Otherwise return None
        """
        result = self.make_bool(item.get("optional", None))
        return result

    def get_parameter_type(self, item):  # pylint: disable=too-many-return-statements
        """
        Return the parameter type of an item if it exists.
        Otherwise return None

        Typically, item['parameterType']

        TODO:2 review whether we should do this translation
        This is translated to the Ansible type, e.g.
        string -> str
        boolean -> bool
        ipV4Address -> ipv4
        etc.
        """
        result = self.get_dict_value(item, "parameterType")
        if result is None:
            return None
        if result in ["STRING", "string", "str"]:
            return "str"
        if result in ["INTEGER", "INT", "integer", "int"]:
            return "int"
        if result in ["BOOLEAN", "boolean", "bool"]:
            return "bool"
        if result in ["ipAddress", "ipV4Address"]:
            return "ipv4"
        if result in ["ipV4AddressWithSubnet"]:
            return "ipv4_subnet"
        if result in ["ipV6Address"]:
            return "ipv6"
        if result in ["ipV6AddressWithSubnet"]:
            return "ipv6_subnet"
        return result

    def get_section(self, item):
        """
        Return the Section annotation of an item
        Otherwise return None

        Typically, item['annotations']['Section']
        """
        result = self.get_dict_value(item, "Section")
        return self.clean_string(result)

    def get_template_content_type(self, template):
        """
        Return the type of the template if it exists.
        Return None otherwise.
        template['type']
        """
        try:
            result = template["contentType"]
        except KeyError:
            result = "unknown"
        return self.clean_string(result)

    def get_template_description(self, template):
        """
        Return the description of the template if it exists.
        Return None otherwise.
        template['description']
        """
        try:
            result = template["description"]
        except KeyError:
            result = "unknown"
        return self.clean_string(result)

    def get_template_name(self, template):
        """
        Return the name of the template if it exists.
        Return None otherwise.
        template['name']
        """
        try:
            result = template["name"]
        except KeyError:
            result = "unknown"
        return self.clean_string(result)

    def get_template_subtype(self, template):
        """
        Return the subtype of the template if it exists.
        Return None otherwise.
        template['templateSubType']
        """
        try:
            result = template["templateSubType"]
        except KeyError:
            result = "unknown"
        return self.clean_string(result)

    def get_template_supported_platforms(self, template):
        """
        Return the supportedPlatforms of the template if it exists.
        Return None otherwise.
        template['supportedPlatforms']
        """
        try:
            result = template["supportedPlatforms"]
        except KeyError:
            result = "unknown"
        return self.clean_string(result)

    def get_template_tags(self, template):
        """
        Return the tags of the template if it exists.
        Return None otherwise.
        template['tags']
        """
        try:
            result = template["tags"]
        except KeyError:
            result = "unknown"
        return self.clean_string(result)

    def get_template_type(self, template):
        """
        Return the type of the template if it exists.
        Return None otherwise.
        template['templateType']
        """
        try:
            result = template["templateType"]
        except KeyError:
            result = "unknown"
        return self.clean_string(result)

    def get_valid_values(self, item):
        """
        Return the validValues annotation of an item
        Otherwise return None

        Typically, item['metaProperties']['validValues']
        """
        result = self.get_dict_value(item, "validValues")
        if result is None:
            return []
        result = result.split(",")
        try:
            result = [int(x) for x in result]
        except ValueError:
            pass
        return result

    def is_mandatory(self, item):
        """
        Return the mandatory status of a parameter
        True if the parameter is mandatory.
        False if the parameter is optional.
        False if the IsMandatory key does not exist

        item["annotations"]["IsMandatory"]
        """
        result = self.get_dict_value(item, "IsMandatory")
        return self.make_bool(result)

    def is_hidden(self, item):
        """
        Return True if item["annotations"]["Section"] is "Hidden"
        Return False otherwise
        """
        result = self.get_section(item)
        if "Hidden" in result:
            return True
        return False

    def is_required(self, item):
        """
        Return the required status of an item (True or False)
        The inverse of item['optional']

        Otherwise return None
        """
        result = self.make_bool(item.get("optional", None))
        if result is True:
            return False
        if result is False:
            return True
        return None

    @staticmethod
    def make_bool(value):
        """
        Translate various string values to a boolean value
        """
        if value in ["true", "yes", "True", "Yes", "TRUE", "YES"]:
            return True
        if value in ["false", "no", "False", "No", "FALSE", "NO"]:
            return False
        return value

    def clean_string(self, string):
        """
        Remove unwanted characters found in various locations
        within the returned NDFC JSON.
        """
        if string is None:
            return ""
        string = string.strip()
        string = re.sub("<br />", " ", string)
        string = re.sub("&#39;", "", string)
        string = re.sub("&#43;", "+", string)
        string = re.sub("&#61;", "=", string)
        string = re.sub("amp;", "", string)
        string = re.sub(r"\[", "", string)
        string = re.sub(r"\]", "", string)
        string = re.sub('"', "", string)
        string = re.sub("'", "", string)
        string = re.sub(r"\s+", " ", string)
        string = self.make_bool(string)
        try:
            string = int(string)
        except ValueError:
            pass
        if not isinstance(string, int):
            try:
                string = float(string)
            except ValueError:
                pass
        return string
