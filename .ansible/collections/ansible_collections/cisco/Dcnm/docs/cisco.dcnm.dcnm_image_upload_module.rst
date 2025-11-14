.. _cisco.dcnm.dcnm_image_upload_module:


****************************
cisco.dcnm.dcnm_image_upload
****************************

**DCNM Ansible Module for managing images.**


Version added: 3.5.0

.. contents::
   :local:
   :depth: 1


Synopsis
--------
- DCNM Ansible Module for the following image management operations
- Upload, Delete, and Display NXOS images from the controller




Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="2">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
            <th width="100%">Comments</th>
        </tr>
            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>files</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=dictionary</span>
                    </div>
                </td>
                <td>
                        <b>Default:</b><br/><div style="color: blue">[]</div>
                </td>
                <td>
                        <div>A dictionary of images and other related information that is required to download the same.</div>
                </td>
            </tr>
                                <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>password</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>Password to be used to log into the image hosting server. This parameter is required only if source is &#x27;scp&#x27;</div>
                        <div>or &#x27;sftp&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
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
                        <div>Full path to the image that is being uploaded to the controller. For deleting an image</div>
                        <div>the exact image name must be provided.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>remote_server</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>IP address of the server hosting the image. This parameter is required only if source is &#x27;scp&#x27;</div>
                        <div>or &#x27;sftp&#x27;.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>source</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li>scp</li>
                                    <li>sftp</li>
                                    <li><div style="color: blue"><b>local</b>&nbsp;&larr;</div></li>
                        </ul>
                </td>
                <td>
                        <div>Protocol to be used to download the image from the controller.</div>
                </td>
            </tr>
            <tr>
                    <td class="elbow-placeholder"></td>
                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>user_name</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                         / <span style="color: red">required</span>
                    </div>
                </td>
                <td>
                </td>
                <td>
                        <div>User name to be used to log into the image hosting server. This parameter is required only if source is &#x27;scp&#x27;</div>
                        <div>or &#x27;sftp&#x27;.</div>
                </td>
            </tr>

            <tr>
                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-"></div>
                    <b>state</b>
                    <a class="ansibleOptionLink" href="#parameter-" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                    </div>
                </td>
                <td>
                        <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                    <li><div style="color: blue"><b>merged</b>&nbsp;&larr;</div></li>
                                    <li>overridden</li>
                                    <li>deleted</li>
                                    <li>query</li>
                        </ul>
                </td>
                <td>
                        <div>The required state of the configuration after module completion.</div>
                </td>
            </tr>
    </table>
    <br/>




Examples
--------

.. code-block:: yaml

    # States:
    # This module supports the following states:
    #
    # Merged:
    #   Images defined in the playbook will be merged into the controller.
    #
    #   The images listed in the playbook will be created if not already present on the server
    #   server. If the image is already present and the configuration information included
    #   in the playbook is either different or not present in server, then the corresponding
    #   information is added to the server. If an image mentioned in playbook
    #   is already present on the server and there is no difference in configuration, no operation
    #   will be performed for such interface.
    #
    # Overridden:
    #   Images defined in the playbook will be overridden in the controller.
    #
    #   The state of the images listed in the playbook will serve as source of truth for all
    #   the images on the controller. Additions and deletions will be done to bring
    #   the images on the controller to the state listed in the playbook. All images other than the
    #   ones mentioned in the playbook will be deleted.
    #   Note: Override will work on the all the images present in the controller.
    #
    # Deleted:
    #   Images defined in the playbook will be deleted from the controller.
    #
    #   Deletes the list of images specified in the playbook. If the playbook does not include
    #   any image information, then all images from the controller will be deleted.
    #
    # Query:
    #   Returns the current state for the images listed in the playbook.

    # UPLOAD IMAGES

    - name: Upload images to controller
      cisco.dcnm.dcnm_image_upload: &img_upload
        state: merged                             # choose form [merged, deleted, overridden, query], default is merged
        files:
          - path: "full/path/to/image1"           # Full path to the image on the server
            source: scp                           # choose from [local, scp, sftp], default is local
            remote_server: "192.168.1.1"          # mandatory when the source is scp or sftp
            username: "image_upload"              # mandatory when source is scp or sftp
            password: "image_upload"              # mandatory when source is scp or sftp

          - path: "full/path/to/image2"           # Full path to image on local host
            source: local                         # choose from [local, scp, sftp], default is local

          - path: "full/path/to/image3"           # Full path to the image on the server
            source: sftp                          # choose from [local, scp, sftp], default is local
            remote_server: "192.168.1.1"          # mandatory when the source is scp or sftp
            username: "image_upload"              # mandatory when source is scp or sftp
            password: "image_upload"              # mandatory when source is scp or sftp

    # DELETE IMAGES

    - name: Delete an image
      cisco.dcnm.dcnm_image_upload:
        state: deleted                            # choose form [merged, deleted, overridden, query], default is merged
        files:
          - name: "nxos.9.3.8.bin"                # Name of the image on the controller

    - name: Delete an image - without explicitly including any config
      cisco.dcnm.dcnm_image_upload:
        state: deleted                            # choose form [merged, deleted, overridden, query], default is merged

    # OVERRIDE IMAGES

    - name: Override without any config
      cisco.dcnm.dcnm_image_upload:
        state: overridden                         # choose form [merged, deleted, overridden, query], default is merged

    - name: Override with a new config
      cisco.dcnm.dcnm_image_upload: &image_override
        state: overridden                         # choose form [merged, deleted, overridden, query], default is merged
        files:
          - path: "full/path/to/image4"           # Full path to the image on local server
            source: local                         # choose from [local, scp, sftp], default is local

    # QUERY IMAGES

    - name: Query for existing image
      cisco.dcnm.dcnm_image_upload:
        state: query                              # choose form [merged, deleted, overridden, query], default is merged
        files:
          - name: "nxos.9.3.8.bin"                # Name of the image to be used to filter the output

    - name: Query without any filters
      cisco.dcnm.dcnm_image_upload:
        state: query                              # choose form [merged, deleted, overridden, query], default is merged




Status
------


Authors
~~~~~~~

- Mallik Mudigonda(@mmudigon)
