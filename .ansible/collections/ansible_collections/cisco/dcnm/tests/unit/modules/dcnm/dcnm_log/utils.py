# Copyright (c) 2025 Cisco and/or its affiliates.
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

params_error_severity = {
    "msg": "Message with ERROR severity.",
    "severity": "ERROR"
}

params_missing_severity = {
    "msg": "Message with ERROR severity.",
}

params_missing_msg = {
    "severity": "INFO"
}

params_invalid_severity = {
    "msg": "Message with FOO severity.",
    "severity": "FOO"
}
