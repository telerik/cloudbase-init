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
import unittest

from cloudbaseinit.plugins import factory
from cloudbaseinit.openstack.common import cfg

CONF = cfg.CONF


class PluginFactoryTests(unittest.TestCase):
    def setUp(self):
        self._factory = factory.PluginFactory()

    @mock.patch('cloudbaseinit.utils.classloader.ClassLoader.load_class')
    def test_load_plugins(self, mock_load_class):
        expected = []
        for path in CONF.plugins:
            expected.append(mock.call(path))
        response = self._factory.load_plugins()
        self.assertEqual(mock_load_class.call_args_list, expected)
        self.assertTrue(response is not None)
