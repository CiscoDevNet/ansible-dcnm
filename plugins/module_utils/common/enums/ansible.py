"""
Values used by Ansible
"""
from enum import Enum


class AnsibleStates(Enum):
    """
    Ansible states used by the DCNM Ansible Collection
    """
    deleted = "deleted"
    merged = "merged"
    overridden = "overridden"
    query = "query"
    replaced = "replaced"
