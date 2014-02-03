# Copyright 2013 Mirantis Inc.
# Copyright 2014 Cloudbase Solutions Srl
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import tempfile
import uuid
import email

from cloudbaseinit.openstack.common import log as logging
from cloudbaseinit.osutils import factory as osutils_factory
from cloudbaseinit.plugins.windows.userdataplugins import base
from cloudbaseinit.utils import file as util



from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.text import MIMEText

from urlparse import urlparse, urlunparse, urljoin, urlsplit, urldefrag

DECOMP_TYPES = [
    'application/zip',
    'application/gzip',
    'application/gzip-compressed',
    'application/gzipped',
    'application/x-compress',
    'application/x-compressed',
    'application/x-gunzip',
    'application/x-gzip',
    'application/x-gzip-compressed',
]

# Saves typing errors
CONTENT_TYPE = 'Content-Type'
NOT_MULTIPART_TYPE = "text/x-not-multipart"

DOWNLOAD_DIR = "openstack"


LOG = logging.getLogger(__name__)


class URLDownloadPlugin(base.BaseUserDataPlugin):
    def __init__(self):
        super(URLDownloadPlugin, self).__init__("text/x-download-url")
        self.ssl_details = None #need to be changed ??? lem0na

    def process(self, part):
        content = part.get_payload()
        self._do_include(content)

    def _do_include(self, content):
        # Include a list of urls, one per line
        # lines starting with # are treated as comments
        # empty lines are skipped
        for line in content.splitlines():
            if line.startswith("#"):
                continue
            download_url = line.strip()
            if not download_url:
                continue

            LOG.debug("Downloading '%s'." % download_url)
            resp = util.read_file_or_url(download_url, ssl_details=self.ssl_details)
            if resp is not None:

                local_filename = None
                url_path = urlsplit(download_url)[2]
                dest_dir = os.path.join(tempfile.gettempdir(), DOWNLOAD_DIR)
                if url_path != "":
                    file_name = os.path.basename(url_path)
                    local_filename = os.path.join(dest_dir, file_name)
                    LOG.debug("Saving '%s' to '%s'." % (file_name, dest_dir))
                    try:
                        util.write_file(local_filename, str(resp), mode=0600)
                    except Exception as ex:
                        LOG.warning('An error occurred during saving file: \'%s\'' % ex)
                        raise

                content_type = resp.headers.get("content-type")
                if local_filename is not None and content_type in DECOMP_TYPES:
                    LOG.debug("Uncompressing '%s' to '%s'." % (local_filename, dest_dir))
                    try:
                        util.unzip_archive(local_filename, dest_dir)
                        os.remove(local_filename)
                    except Exception as ex:
                        LOG.warning('An error occurred during uncompressing file: \'%s\'' % ex)
                        raise
                    finally:
                        if os.path.exists(local_filename):
                            os.remove(local_filename)
            pass

