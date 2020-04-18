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

import lxml.etree
import re
from unittest import mock

import requests_mock

import dracclient.client
from dracclient import constants
from dracclient import exceptions
import dracclient.resources.job
from dracclient.resources import lifecycle_controller
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils
from dracclient import utils


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


@requests_mock.Mocker()
class ClientLCConfigurationTestCase(base.BaseTest):

    def setUp(self):
        super(ClientLCConfigurationTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_list_lifecycle_settings_by_instance_id(
            self, mock_requests,
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

        lifecycle_settings = self.drac_client.list_lifecycle_settings(
                by_name=False)

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

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_list_lifecycle_settings_by_name(
            self, mock_requests,
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

        lifecycle_settings = self.drac_client.list_lifecycle_settings(
                by_name=True)

        self.assertEqual(14, len(lifecycle_settings))
        # enumerable attribute
        self.assertIn(
            'Lifecycle Controller State',
            lifecycle_settings)
        self.assertEqual(expected_enum_attr, lifecycle_settings[
                         'Lifecycle Controller State'])
        # string attribute
        self.assertIn(
            'SYSID',
            lifecycle_settings)
        self.assertEqual(expected_string_attr,
                         lifecycle_settings['SYSID'])

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_is_lifecycle_in_recovery(self, mock_requests,
                                      mock_invoke):
        expected_selectors = {'CreationClassName': 'DCIM_LCService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:LCService',
                              'SystemCreationClassName': 'DCIM_ComputerSystem'}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.LifecycleControllerInvocations[uris.DCIM_LCService][
                'GetRemoteServicesAPIStatus']['is_recovery'])
        result = self.drac_client.is_lifecycle_in_recovery()

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_LCService, 'GetRemoteServicesAPIStatus',
            expected_selectors, {},
            expected_return_value=utils.RET_SUCCESS,
            wait_for_idrac=False)

        self.assertEqual(True, result)

    @mock.patch.object(dracclient.client.WSManClient,
                       'invoke', spec_set=True,
                       autospec=True)
    def test_set_lifecycle_settings(self, mock_requests,
                                    mock_invoke):

        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.LifecycleControllerEnumerations[
                uris.DCIM_LCEnumeration]['ok']},
            {'text': test_utils.LifecycleControllerEnumerations[
                uris.DCIM_LCString]['ok']}])

        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.LifecycleControllerInvocations[uris.DCIM_LCService][
                'SetAttributes']['ok'])

        result = self.drac_client.set_lifecycle_settings(
            {'Collect System Inventory on Restart': 'Disabled'})

        self.assertEqual({'is_commit_required': True,
                          'is_reboot_required': constants.RebootRequired.false
                          },
                         result)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_set_lifecycle_settings_with_unknown_attr(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.LifecycleControllerEnumerations[
                uris.DCIM_LCEnumeration]['ok']},
            {'text': test_utils.LifecycleControllerEnumerations[
                uris.DCIM_LCString]['ok']},
            {'text': test_utils.LifecycleControllerInvocations[
                uris.DCIM_LCService]['SetAttributes']['error']}])

        self.assertRaises(exceptions.InvalidParameterValue,
                          self.drac_client.set_lifecycle_settings,
                          {'foo': 'bar'})

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_set_lifecycle_settings_with_unchanged_attr(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.LifecycleControllerEnumerations[
                uris.DCIM_LCEnumeration]['ok']},
            {'text': test_utils.LifecycleControllerEnumerations[
                uris.DCIM_LCString]['ok']}])

        result = self.drac_client.set_lifecycle_settings(
            {'Lifecycle Controller State': 'Enabled'})

        self.assertEqual({'is_commit_required': False,
                          'is_reboot_required':
                          constants.RebootRequired.false},
                         result)

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_set_lifecycle_settings_with_readonly_attr(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        expected_message = ("Cannot set read-only Lifecycle attributes: "
                            "['Licensed'].")
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.LifecycleControllerEnumerations[
                uris.DCIM_LCEnumeration]['ok']},
            {'text': test_utils.LifecycleControllerEnumerations[
                uris.DCIM_LCString]['ok']}])

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.set_lifecycle_settings, {'Licensed': 'yes'})

    @mock.patch.object(dracclient.client.WSManClient,
                       'wait_until_idrac_is_ready', spec_set=True,
                       autospec=True)
    def test_set_lifecycle_settings_with_incorrect_enum_value(
            self, mock_requests, mock_wait_until_idrac_is_ready):
        expected_message = ("Attribute 'Lifecycle Controller State' cannot "
                            "be set to value 'foo'. It must be in "
                            "['Disabled', 'Enabled', 'Recovery'].")

        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.LifecycleControllerEnumerations[
                uris.DCIM_LCEnumeration]['ok']},
            {'text': test_utils.LifecycleControllerEnumerations[
                uris.DCIM_LCString]['ok']}])
        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.set_lifecycle_settings,
            {'Lifecycle Controller State': 'foo'})


class ClientLCChangesTestCase(base.BaseTest):

    def setUp(self):
        super(ClientLCChangesTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_commit_pending_lifecycle_changes(self, mock_create_config_job):

        self.drac_client.commit_pending_lifecycle_changes()

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_LCService,
            cim_creation_class_name='DCIM_LCService',
            cim_name='DCIM:LCService', target='',
            reboot=False, start_time='TIME_NOW',
            wait_for_idrac=False,
            method_name='CreateConfigJob')

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_commit_pending_lifecycle_changes_with_time(
            self, mock_create_config_job):
        timestamp = '20140924140201'
        self.drac_client.commit_pending_lifecycle_changes(
            start_time=timestamp)

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_LCService,
            cim_creation_class_name='DCIM_LCService',
            cim_name='DCIM:LCService', target='',
            reboot=False, start_time=timestamp,
            wait_for_idrac=False,
            method_name='CreateConfigJob')
