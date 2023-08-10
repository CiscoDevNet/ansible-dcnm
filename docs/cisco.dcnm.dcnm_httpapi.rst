.. _cisco.dcnm.dcnm_httpapi:


***************
cisco.dcnm.dcnm
***************

**Ansible DCNM HTTPAPI Plugin.**


Version added: 0.9.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- This DCNM plugin provides the HTTPAPI transport methods needed to initiate a connection to the DCNM controller, send API requests and process the respsonse from the controller.




Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
                <th>Configuration</th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>login_domain</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">"local"</div>
                </td>
                    <td>
                                <div>env:ANSIBLE_HTTPAPI_LOGIN_DOMAIN</div>
                                <div>var: ansible_httpapi_login_domain</div>
                    </td>
                <td>
                        <div>The login domain name to use for user authentication</div>
                        <div>Only needed for NDFC</div>
                </td>
            </tr>
    </table>
    <br/>








Status
------


Authors
~~~~~~~

- Mike Wiebe (@mikewiebe)


.. hint::
    Configuration entries for each entry type have a low to high priority order. For example, a variable that is lower in the list will override a variable that is higher up.
