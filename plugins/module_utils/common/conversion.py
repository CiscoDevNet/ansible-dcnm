# Copyright (c) 2024 Cisco and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

__metaclass__ = type
__author__ = "Allen Robel"

import inspect
import re


class ConversionUtils:
    """
    Utility methods for converting, translating, and validating values.

    - bgp_asn_is_valid: Return True if value is a valid BGP ASN, False otherwise.
    - make_boolean: Return value converted to boolean, if possible.
    - make_int: Return value converted to int, if possible.
    - make_none: Return None if value is a string representation of a None type.
    - reject_boolean_string: Reject quoted boolean values e.g. "False", "true"
    - translate_mac_address: Convert mac address to dotted-quad format expected by the controller.
    - validate_fabric_name: Validate the fabric name meets the requirements of the controller.
    """

    def __init__(self):
        self.class_name = self.__class__.__name__

        re_asn_str = "^(((\\+)?[1-9]{1}[0-9]{0,8}|(\\+)?[1-3]{1}[0-9]{1,9}|(\\+)?[4]"
        re_asn_str += "{1}([0-1]{1}[0-9]{8}|[2]{1}([0-8]{1}[0-9]{7}|[9]{1}([0-3]{1}"
        re_asn_str += "[0-9]{6}|[4]{1}([0-8]{1}[0-9]{5}|[9]{1}([0-5]{1}[0-9]{4}|[6]"
        re_asn_str += "{1}([0-6]{1}[0-9]{3}|[7]{1}([0-1]{1}[0-9]{2}|[2]{1}([0-8]{1}"
        re_asn_str += "[0-9]{1}|[9]{1}[0-5]{1})))))))))|([1-5]\\d{4}|[1-9]\\d{0,3}|6"
        re_asn_str += "[0-4]\\d{3}|65[0-4]\\d{2}|655[0-2]\\d|6553[0-5])"
        re_asn_str += "(\\.([1-5]\\d{4}|[1-9]\\d{0,3}|6[0-4]\\d{3}|65[0-4]"
        re_asn_str += "\\d{2}|655[0-2]\\d|6553[0-5]|0))?)$"
        self.re_asn = re.compile(re_asn_str)
        self.re_valid_fabric_name = re.compile(r"[a-zA-Z]+[a-zA-Z0-9_-]*")

        self.bgp_as_invalid_reason = None

    def bgp_as_is_valid(self, value):
        """
        -   Return True if value is a valid BGP ASN.
        -   Return False, otherwise.
        -   Set ConversionUtils().bgp_as_invalid_reason to a string with the
            reason why the value is not a valid BGP ASN.

        Usage example:

        ```python
        conversion = ConversionUtils()
        if not conversion.bgp_as_is_valid(value):
            print(conversion.bgp_as_invalid_reason)
        ```
        """
        if isinstance(value, float):
            msg = f"BGP ASN ({value}) cannot be type float() due to "
            msg += "loss of trailing zeros. "
            msg += "Use a string or integer instead."
            self.bgp_as_invalid_reason = msg
            return False
        try:
            asn = str(value)
        except UnicodeEncodeError:
            msg = f"BGP ASN ({value}) could not be converted to a string."
            self.bgp_as_invalid_reason = msg
            return False
        if not self.re_asn.match(asn):
            msg = f"BGP ASN {value} failed regex validation."
            self.bgp_as_invalid_reason = msg
            return False
        return True

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
        -   Raise ``ValueError`` with informative message if the value is
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

    @staticmethod
    def translate_mac_address(mac_addr):
        """
        -   Accept mac address with any (or no) punctuation and convert it
            into the dotted-quad format that the controller expects.
        -   On success, return translated mac address.
        -   On failure, raise ``ValueError``.
        """
        mac_addr = re.sub(r"[\W\s_]", "", mac_addr)
        if not re.search("^[A-Fa-f0-9]{12}$", mac_addr):
            raise ValueError(f"Invalid MAC address: {mac_addr}")
        return "".join((mac_addr[:4], ".", mac_addr[4:8], ".", mac_addr[8:]))

    def validate_fabric_name(self, value):
        """
        -   Validate the fabric name meets the requirements of the controller.
        -   Raise ``TypeError`` if value is not a string.
        -   Raise ``ValueError`` if value does not meet the requirements.
        """
        method_name = inspect.stack()[0][3]  # pylint: disable=unused-variable

        if not isinstance(value, str):
            msg = f"{self.class_name}.{method_name}: "
            msg += f"Invalid fabric name. Expected string. Got {value}."
            raise TypeError(msg)

        if re.fullmatch(self.re_valid_fabric_name, value) is not None:
            return
        msg = f"{self.class_name}.{method_name}: "
        msg += f"Invalid fabric name: {value}. "
        msg += "Fabric name must start with a letter A-Z or a-z and "
        msg += "contain only the characters in: [A-Z,a-z,0-9,-,_]."
        raise ValueError(msg)
