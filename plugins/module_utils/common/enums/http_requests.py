# -*- coding: utf-8 -*-
# @author: Allen Robel
# @file: plugins/module_utils/common/enums/http_requests.py
"""
Enumerations related to HTTP requests
"""
from enum import Enum


class RequestVerb(Enum):
    """
    # Summary

    HTTP request verbs used in this collection.

    ## Values

    -   `DELETE`
    -   `GET`
    -   `POST`
    -   `PUT`

    """

    DELETE = "DELETE"
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
