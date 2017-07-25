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
import requests_mock

import dracclient.client
from dracclient.resources import lifecycle_controller
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils


class ClientLifecycleControllerManagementTestCase(base.BaseTest):

    def setUp(self):
        super(ClientLifecycleControllerManagementTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @requests_mock.Mocker()
    def test_get_lifecycle_controller_version(self, mock_requests):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.LifecycleControllerEnumerations[
                uris.DCIM_SystemView]['ok'])

        version = self.drac_client.get_lifecycle_controller_version()

        self.assertEqual((2, 1, 0), version)


class ClientLCConfigurationTestCase(base.BaseTest):

    def setUp(self):
        super(ClientLCConfigurationTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @requests_mock.Mocker()
    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_list_lifecycle_settings(self, mock_requests,
                                     mock_wait_until_idrac_is_ready):
        expected_enum_attr = lifecycle_controller.LCEnumerableAttribute(
            name='Lifecycle Controller State',
            instance_id='LifecycleController.Embedded.1#LCAttributes.1#LifecycleControllerState',  # noqa
            read_only=False,
            current_value='Enabled',
            pending_value=None,
            possible_values=['Disabled', 'Enabled', 'Recovery'])
        expected_string_attr = lifecycle_controller.LCStringAttribute(
            name='SYSID',
            instance_id='LifecycleController.Embedded.1#LCAttributes.1#SystemID',  # noqa
            read_only=True,
            current_value='639',
            pending_value=None,
            min_length=0,
            max_length=3)
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.LifecycleControllerEnumerations[
                uris.DCIM_LCEnumeration]['ok']},
            {'text': test_utils.LifecycleControllerEnumerations[
                uris.DCIM_LCString]['ok']}])

        lifecycle_settings = self.drac_client.list_lifecycle_settings()

        self.assertEqual(14, len(lifecycle_settings))
        # enumerable attribute
        self.assertIn(
            'LifecycleController.Embedded.1#LCAttributes.1#LifecycleControllerState',  # noqa
            lifecycle_settings)
        self.assertEqual(expected_enum_attr, lifecycle_settings[
                         'LifecycleController.Embedded.1#LCAttributes.1#LifecycleControllerState'])  # noqa
        # string attribute
        self.assertIn(
            'LifecycleController.Embedded.1#LCAttributes.1#SystemID',
            lifecycle_settings)
        self.assertEqual(expected_string_attr,
                         lifecycle_settings['LifecycleController.Embedded.1#LCAttributes.1#SystemID'])  # noqa
