"""
Enums related to HTTP requests
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
