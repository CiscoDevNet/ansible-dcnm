# -*- coding: utf-8 -*-
"""
Utilities specific to the dcnm_vrf module.
"""
from ..network.dcnm.dcnm import dcnm_send, parse_response


def calculate_items_per_chunk(query_string_items: str, query_string_item_list: list) -> int:
    """
    Calculate the number of items per chunk based on the estimated average item length
    and the maximum allowed URL size.
    """
    max_url_size = 5900  # Room for path/query params
    if not query_string_item_list:
        return 1
    avg_item_len = max(1, len(query_string_items) // max(1, len(query_string_item_list)))
    return max(1, max_url_size // (avg_item_len + 1))  # +1 for comma


def verify_response(module, response: str, fabric_name: str, vrfs: str, caller: str):
    """
    Verify the response from the controller.

    Parameters:
        module: Ansible module instance
        response: Response from the controller

    Raises:
        AnsibleModuleError: If the response indicates an error or if the fabric is missing.
    """
    missing_fabric, not_ok = parse_response(response=response)
    if missing_fabric or not_ok:
        msg1 = f"Fabric {fabric_name} not present on the controller"
        msg2 = f"{caller}: Unable to find vrfs {vrfs[:-1]} under fabric: {fabric_name}"
        module.fail_json(msg=msg1 if missing_fabric else msg2)


def get_endpoint_with_long_query_string(module, fabric_name: str, path: str, query_string_items: str, caller: str = "NA"):
    """
    ## Summary

    Query the controller endpoint, splitting the query string into chunks if necessary
    to avoid exceeding the controller's URL length limit.

    Parameters:
        module: An Ansible module instance
        fabric_name: Name of the fabric to query
        path: Controller endpoint to query
        query_string_items: Comma-separated list of query items (e.g. vrf names)
        caller: Freeform string used to identify the originator of the query (for debugging)

    Returns:
        Consolidated response from the controller.
    """
    query_string_item_list = query_string_items.split(",")
    attach_objects = None

    items_per_chunk = calculate_items_per_chunk(query_string_items, query_string_item_list)

    for i in range(0, len(query_string_item_list), items_per_chunk):
        query_string_subset = query_string_item_list[i : i + items_per_chunk]
        url = path.format(fabric_name, ",".join(query_string_subset))
        attachment_objects = dcnm_send(module, "GET", url)

        verify_response(module=module, response=attachment_objects, fabric_name=fabric_name, vrfs=query_string_subset, caller=caller)

        if attach_objects is None:
            attach_objects = attachment_objects
        else:
            attach_objects["DATA"].extend(attachment_objects["DATA"])

    return attach_objects
