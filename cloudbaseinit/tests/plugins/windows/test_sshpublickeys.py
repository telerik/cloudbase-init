# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Cloudbase Solutions Srl
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

import mock
import os
import unittest

from cloudbaseinit.plugins.windows import sshpublickeys
from cloudbaseinit.openstack.common import cfg
from cloudbaseinit.tests.metadata import fake_json_response

CONF = cfg.CONF


class SetUserSSHPublicKeysPluginTests(unittest.TestCase):

    def setUp(self):
        self._set_ssh_keys_plugin = sshpublickeys.SetUserSSHPublicKeysPlugin()
        self.fake_data = fake_json_response.get_fake_metadata_json(
            '2013-04-04')

    @mock.patch('cloudbaseinit.osutils.factory.OSUtilsFactory.get_os_utils')
    @mock.patch('os.path')
    @mock.patch('os.makedirs')
    def _test_execute(self, mock_os_makedirs, mock_os_path,
                      mock_get_os_utils, user_home):
        mock_service = mock.MagicMock()
        mock_osutils = mock.MagicMock()
        fake_shared_data = 'fake data'
        mock_service.get_meta_data.return_value = self.fake_data
        CONF.set_override('username', 'fake user')
        mock_get_os_utils.return_value = mock_osutils
        mock_osutils.get_user_home.return_value = user_home
        mock_os_path.exists.return_value = False

        if user_home is None:
            self.assertRaises(Exception, self._set_ssh_keys_plugin,
                              mock_service, fake_shared_data)
        else:
            with mock.patch('cloudbaseinit.plugins.windows.sshpublickeys'
                            '.open',
                            mock.mock_open(), create=True):
                response = self._set_ssh_keys_plugin.execute(mock_service,
                                                             fake_shared_data)
                mock_service.get_meta_data.assert_called_with('openstack')
                mock_osutils.get_user_home.assert_called_with('fake user')
                self.assertEqual(mock_os_path.join.call_count, 2)
                mock_os_makedirs.assert_called_once_with(mock_os_path.join())

                self.assertEqual(response, (1, False))

    def test_execute_with_user_home(self):
        fake_user_home = os.path.join('fake', 'home')
        self._test_execute(user_home=fake_user_home)

    def test_execute_with_no_user_home(self):
        self._test_execute(user_home=None)
