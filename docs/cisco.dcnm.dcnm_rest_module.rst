.. _cisco.dcnm.dcnm_rest_module:


********************
cisco.dcnm.dcnm_rest
********************

**Send REST API requests to DCNM controller.**


Version added: 0.9.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- Send REST API requests to DCNM controller.




Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>data</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">raw</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Additional data in JSON or TEXT to include with the REST API call</div>
                        <div style="font-size: small; color: darkgreen"><br/>aliases: json_data</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>method</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>GET</li>
                                    <li>POST</li>
                                    <li>PUT</li>
                                    <li>DELETE</li>
                        </ul>
                </td>
                <td>
                        <div>REST API Method</div>
                </td>
            </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>path</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>REST API Path Endpoint</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    # This module can be used to send any REST API requests that are supported by
    # the DCNM controller.
    #
    # This module is not idempotent but can be used as a stop gap until a feature
    # module can be developed for the target DCNM functionality.

    - name: Gather List of Fabrics from DCNM
      dcnm_rest:
        method: GET
        path: /rest/control/fabrics

    - name: Set deployment to false in lanAttachList for vrf
      dcnm_rest:
        method: POST
        path: /rest/top-down/fabrics/fabric1/vrfs/attachments
        json_data: '[{"vrfName":"sales66_vrf1","lanAttachList":[{"fabric":"fabric1","vrfName":"sales66_vrf1","serialNumber":"FDO21392QKM","vlan":2000,"freeformConfig":"","deployment":false,"extensionValues":"","instanceValues":"{"loopbackId":"","loopbackIpAddress":"","loopbackIpV6Address":""}"}]}]'

    # Read payload data from file and validate a template
    - set_fact:
        data: "{{ lookup('file', 'validate_payload') }}"

    - name: Validate a template
      cisco.dcnm.dcnm_rest:
        method: POST
        path: /fm/fmrest/config/templates/validate
        json_data: "{{ data }}"
        register: result



Return Values
-------------
Common return values are documented `here <https://docs.ansible.com/ansible/latest/reference_appendices/common_return_values.html#common-return-values>`_, the following are the fields unique to this module:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Key</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-"></div>
                    <b>response</b>
                    <a class="ansibleOptionLink" href="#return-" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>always</td>
                <td>
                            <div>Success or Error Data retrieved from DCNM</div>
                    <br/>
                </td>
            </tr>
    </table>
    <br/><br/>


Status
------


Authors
~~~~~~~

- Mike Wiebe (@mikewiebe)
