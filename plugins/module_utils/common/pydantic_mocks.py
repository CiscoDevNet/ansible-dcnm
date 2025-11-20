# coding: utf-8
# @file: plugins/module_utils/pydantic_mocks.py
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
"""
Pydantic mocks for environments where pydantic is not installed.
"""

BaseModel = object


def AfterValidator(func):  # pylint: disable=invalid-name
    """Pydantic AfterValidator fallback when pydantic is not available."""
    return func


def BeforeValidator(func):  # pylint: disable=invalid-name
    """Pydantic BeforeValidator fallback when pydantic is not available."""
    return func


def ConfigDict(**kwargs):  # pylint: disable=unused-argument,invalid-name
    """Pydantic ConfigDict fallback when pydantic is not available."""
    return {}


def Field(**kwargs):  # pylint: disable=unused-argument,invalid-name
    """Pydantic Field fallback when pydantic is not available."""
    return None


PydanticExperimentalWarning = Warning

StrictBool = bool


class ValidationError(Exception):
    """
    Pydantic ValidationError fallback when pydantic is not available.
    """

    def __init__(self, message="A custom error occurred."):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"ValidationError: {self.message}"


def field_serializer(*args, **kwargs):  # pylint: disable=unused-argument
    """Pydantic field_serializer fallback when pydantic is not available."""

    def decorator(func):
        return func

    return decorator


def field_validator(*args, **kwargs):  # pylint: disable=unused-argument
    """Pydantic field_validator fallback when pydantic is not available."""

    def decorator(func):
        return func

    return decorator


def model_validator(*args, **kwargs):  # pylint: disable=unused-argument
    """Pydantic model_validator fallback when pydantic is not available."""

    def decorator(func):
        return func

    return decorator
