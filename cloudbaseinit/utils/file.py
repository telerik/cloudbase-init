from StringIO import StringIO

import os
import os.path
import errno
import hashlib
from zipfile import ZipFile as ZipFile

from cloudbaseinit.openstack.common import log as logging
from cloudbaseinit.utils import url_helper

LOG = logging.getLogger(__name__)

def write_file(filename, content, mode=0644, omode="wb"):
    """
    Writes a file with the given content and sets the file mode as specified.
    Resotres the SELinux context if possible.

    @param filename: The full path of the file to write.
    @param content: The content to write to the file.
    @param mode: The filesystem mode to set on the file.
    @param omode: The open mode used when opening the file (r, rb, a, etc.)
    """

    dir_name = os.path.dirname(filename)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    ensure_dir(dir_name)
    LOG.debug("Writing to %s - %s: [%s] %s bytes", filename, omode, mode, len(content))
    with open(filename, omode) as fh:
        fh.write(content)
        fh.flush()
    chmod(filename, mode)

def ensure_dir(path, mode=None):
    if not os.path.isdir(path):
        # Make the dir and adjust the mode
        chmod(path, mode)
    else:
        # Just adjust the mode
        chmod(path, mode)

def chmod(path, mode):
    real_mode = safe_int(mode)
    if path and real_mode:
        os.chmod(path, real_mode)

def safe_int(possible_int):
    try:
        return int(possible_int)
    except (ValueError, TypeError):
        return None

def pipe_in_out(in_fh, out_fh, chunk_size=1024, chunk_cb=None):
    bytes_piped = 0
    while True:
        data = in_fh.read(chunk_size)
        if data == '':
            break
        else:
            out_fh.write(data)
            bytes_piped += len(data)
            if chunk_cb:
                chunk_cb(bytes_piped)
    out_fh.flush()
    return bytes_piped

def read_file_or_url(url, timeout=5, retries=10,
                     headers=None, data=None, sec_between=1, ssl_details=None,
                     headers_cb=None):
    url = url.lstrip()
    if url.startswith("/"):
        url = "file://%s" % url
    if url.lower().startswith("file://"):
        if data:
            LOG.warn("Unable to post data to file resource %s", url)
        file_path = url[len("file://"):]
        return FileResponse(file_path, contents=load_file(file_path))
    else:
        return url_helper.readurl(url,
                                  timeout=timeout,
                                  retries=retries,
                                  headers=headers,
                                  headers_cb=headers_cb,
                                  data=data,
                                  sec_between=sec_between,
                                  ssl_details=ssl_details)

def load_file(fname, read_cb=None, quiet=False):
    LOG.debug("Reading from %s (quiet=%s)", fname, quiet)
    ofh = StringIO()
    try:
        with open(fname, 'rb') as ifh:
            pipe_in_out(ifh, ofh, chunk_cb=read_cb)
    except IOError as e:
        if not quiet:
            raise
        if e.errno != errno.ENOENT:
            raise
    contents = ofh.getvalue()
    LOG.debug("Read %s bytes from %s", len(contents), fname)
    return contents


# Made to have same accessors as UrlResponse so that the
# read_file_or_url can return this or that object and the
# 'user' of those objects will not need to know the difference.
class StringResponse(object):
    def __init__(self, contents, code=200):
        self.code = code
        self.headers = {}
        self.contents = contents
        self.url = None

    def ok(self, *args, **kwargs):  # pylint: disable=W0613
        if self.code != 200:
            return False
        return True

    def __str__(self):
        return self.contents

class FileResponse(StringResponse):
    def __init__(self, path, contents, code=200):
        StringResponse.__init__(self, contents, code=code)
        self.url = path

def hash_blob(blob, routine, mlen=None):
    hasher = hashlib.new(routine)
    hasher.update(blob)
    digest = hasher.hexdigest()
    # Don't get to long now
    if mlen is not None:
        return digest[0:mlen]
    else:
        return digest

def unzip_archive(source_filename, dest_dir=None):
     with ZipFile(source_filename) as zf:
        zf.extractall(dest_dir)