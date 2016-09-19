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

import re

import lxml.etree
import mock
import requests_mock

import dracclient.client
from dracclient import exceptions
from dracclient.resources import bios
import dracclient.resources.job
from dracclient.resources import lifecycle_controller
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils
from dracclient import utils


@requests_mock.Mocker()
class ClientPowerManagementTestCase(base.BaseTest):

    def setUp(self):
        super(ClientPowerManagementTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    def test_get_power_state(self, mock_requests):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.BIOSEnumerations[uris.DCIM_ComputerSystem]['ok'])

        self.assertEqual('POWER_ON', self.drac_client.get_power_state())

    def test_set_power_state(self, mock_requests):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.BIOSInvocations[
                uris.DCIM_ComputerSystem]['RequestStateChange']['ok'])

        self.assertIsNone(self.drac_client.set_power_state('POWER_ON'))

    def test_set_power_state_fail(self, mock_requests):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.BIOSInvocations[
                uris.DCIM_ComputerSystem]['RequestStateChange']['error'])

        self.assertRaises(exceptions.DRACOperationFailed,
                          self.drac_client.set_power_state, 'POWER_ON')

    def test_set_power_state_invalid_target_state(self, mock_requests):
        self.assertRaises(exceptions.InvalidParameterValue,
                          self.drac_client.set_power_state, 'foo')


class ClientBootManagementTestCase(base.BaseTest):

    def setUp(self):
        super(ClientBootManagementTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @requests_mock.Mocker()
    def test_list_boot_modes(self, mock_requests):
        expected_boot_mode = bios.BootMode(id='IPL', name='BootSeq',
                                           is_current=True, is_next=True)
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.BIOSEnumerations[
                uris.DCIM_BootConfigSetting]['ok'])

        boot_modes = self.drac_client.list_boot_modes()

        self.assertEqual(5, len(boot_modes))
        self.assertIn(expected_boot_mode, boot_modes)

    @requests_mock.Mocker()
    def test_list_boot_devices(self, mock_requests):
        expected_boot_device = bios.BootDevice(
            id=('IPL:BIOS.Setup.1-1#BootSeq#NIC.Embedded.1-1-1#'
                'fbeeb18f19fd4e768c941e66af4fc424'),
            boot_mode='IPL',
            pending_assigned_sequence=0,
            current_assigned_sequence=0,
            bios_boot_string=('Embedded NIC 1 Port 1 Partition 1: '
                              'BRCM MBA Slot 0200 v16.4.3 BootSeq'))
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.BIOSEnumerations[
                uris.DCIM_BootSourceSetting]['ok'])

        boot_devices = self.drac_client.list_boot_devices()

        self.assertEqual(3, len(boot_devices))
        self.assertIn('IPL', boot_devices)
        self.assertIn('BCV', boot_devices)
        self.assertIn('UEFI', boot_devices)
        self.assertEqual(3, len(boot_devices['IPL']))
        self.assertIn(expected_boot_device, boot_devices['IPL'])
        self.assertEqual(
            0,  boot_devices['IPL'][0].pending_assigned_sequence)
        self.assertEqual(
            1,  boot_devices['IPL'][1].pending_assigned_sequence)
        self.assertEqual(
            2,  boot_devices['IPL'][2].pending_assigned_sequence)

    @requests_mock.Mocker()
    @mock.patch.object(lifecycle_controller.LifecycleControllerManagement,
                       'get_version', spec_set=True, autospec=True)
    def test_list_boot_devices_11g(self, mock_requests,
                                   mock_get_lifecycle_controller_version):
        expected_boot_device = bios.BootDevice(
            id=('IPL:NIC.Embedded.1-1:082927b7c62a9f52ef0d65a33416d76c'),
            boot_mode='IPL',
            pending_assigned_sequence=0,
            current_assigned_sequence=0,
            bios_boot_string=('Embedded NIC 1: '
                              'BRCM MBA Slot 0200 v7.2.3 BootSeq'))

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.BIOSEnumerations[
                uris.DCIM_BootSourceSetting]['ok-11g'])
        mock_get_lifecycle_controller_version.return_value = (1, 0, 0)

        boot_devices = self.drac_client.list_boot_devices()

        self.assertEqual(3, len(boot_devices))
        self.assertIn('IPL', boot_devices)
        self.assertIn('BCV', boot_devices)
        self.assertIn('UEFI', boot_devices)
        self.assertEqual(3, len(boot_devices['IPL']))
        self.assertIn(expected_boot_device, boot_devices['IPL'])
        self.assertEqual(
            0,  boot_devices['IPL'][0].pending_assigned_sequence)
        self.assertEqual(
            1,  boot_devices['IPL'][1].pending_assigned_sequence)
        self.assertEqual(
            2,  boot_devices['IPL'][2].pending_assigned_sequence)

    @requests_mock.Mocker()
    def test_change_boot_device_order(self, mock_requests):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.BIOSInvocations[
                uris.DCIM_BootConfigSetting][
                    'ChangeBootOrderByInstanceID']['ok'])

        self.assertIsNone(
            self.drac_client.change_boot_device_order('IPL', 'foo'))

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_change_boot_device_order_list(self, mock_invoke):
        expected_selectors = {'InstanceID': 'IPL'}
        expected_properties = {'source': ['foo', 'bar', 'baz']}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.BIOSInvocations[uris.DCIM_BootConfigSetting][
                'ChangeBootOrderByInstanceID']['ok'])

        self.drac_client.change_boot_device_order('IPL',
                                                  ['foo', 'bar', 'baz'])

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_BootConfigSetting,
            'ChangeBootOrderByInstanceID', expected_selectors,
            expected_properties, expected_return_value=utils.RET_SUCCESS)

    @requests_mock.Mocker()
    def test_change_boot_device_order_error(self, mock_requests):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.BIOSInvocations[
                uris.DCIM_BootConfigSetting][
                    'ChangeBootOrderByInstanceID']['error'])

        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.change_boot_device_order, 'IPL', 'foo')


class ClientBIOSConfigurationTestCase(base.BaseTest):

    def setUp(self):
        super(ClientBIOSConfigurationTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @requests_mock.Mocker()
    def test_list_bios_settings_by_instance_id(self, mock_requests):
        expected_enum_attr = bios.BIOSEnumerableAttribute(
            name='MemTest',
            instance_id='BIOS.Setup.1-1:MemTest',
            read_only=False,
            current_value='Disabled',
            pending_value=None,
            possible_values=['Enabled', 'Disabled'])
        expected_string_attr = bios.BIOSStringAttribute(
            name='SystemModelName',
            instance_id='BIOS.Setup.1-1:SystemModelName',
            read_only=True,
            current_value='PowerEdge R320',
            pending_value=None,
            min_length=0,
            max_length=32,
            pcre_regex=None)
        expected_integer_attr = bios.BIOSIntegerAttribute(
            name='Proc1NumCores',
            instance_id='BIOS.Setup.1-1:Proc1NumCores',
            read_only=True,
            current_value=8,
            pending_value=None,
            lower_bound=0,
            upper_bound=65535)
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSEnumeration]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSString]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSInteger]['ok']}])

        bios_settings = self.drac_client.list_bios_settings(by_name=False)

        self.assertEqual(103, len(bios_settings))
        # enumerable attribute
        self.assertIn('BIOS.Setup.1-1:MemTest', bios_settings)
        self.assertEqual(expected_enum_attr, bios_settings[
                         'BIOS.Setup.1-1:MemTest'])
        # string attribute
        self.assertIn('BIOS.Setup.1-1:SystemModelName', bios_settings)
        self.assertEqual(expected_string_attr,
                         bios_settings['BIOS.Setup.1-1:SystemModelName'])
        # integer attribute
        self.assertIn('BIOS.Setup.1-1:Proc1NumCores', bios_settings)
        self.assertEqual(expected_integer_attr, bios_settings[
                         'BIOS.Setup.1-1:Proc1NumCores'])

    @requests_mock.Mocker()
    def test_list_bios_settings_by_name(self, mock_requests):
        expected_enum_attr = bios.BIOSEnumerableAttribute(
            name='MemTest',
            instance_id='BIOS.Setup.1-1:MemTest',
            read_only=False,
            current_value='Disabled',
            pending_value=None,
            possible_values=['Enabled', 'Disabled'])
        expected_string_attr = bios.BIOSStringAttribute(
            name='SystemModelName',
            instance_id='BIOS.Setup.1-1:SystemModelName',
            read_only=True,
            current_value='PowerEdge R320',
            pending_value=None,
            min_length=0,
            max_length=32,
            pcre_regex=None)
        expected_integer_attr = bios.BIOSIntegerAttribute(
            name='Proc1NumCores',
            instance_id='BIOS.Setup.1-1:Proc1NumCores',
            read_only=True,
            current_value=8,
            pending_value=None,
            lower_bound=0,
            upper_bound=65535)
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSEnumeration]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSString]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSInteger]['ok']}])

        bios_settings = self.drac_client.list_bios_settings(by_name=True)

        self.assertEqual(103, len(bios_settings))
        # enumerable attribute
        self.assertIn('MemTest', bios_settings)
        self.assertEqual(expected_enum_attr, bios_settings['MemTest'])
        # string attribute
        self.assertIn('SystemModelName', bios_settings)
        self.assertEqual(expected_string_attr,
                         bios_settings['SystemModelName'])
        # integer attribute
        self.assertIn('Proc1NumCores', bios_settings)
        self.assertEqual(expected_integer_attr, bios_settings['Proc1NumCores'])

    @requests_mock.Mocker()
    def test_list_bios_settings_by_name_with_colliding_attrs(
            self, mock_requests):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSEnumeration]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSString]['colliding']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSInteger]['ok']}])

        self.assertRaises(exceptions.DRACOperationFailed,
                          self.drac_client.list_bios_settings, by_name=True)

    @requests_mock.Mocker()
    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_set_bios_settings(self, mock_requests, mock_invoke):
        expected_selectors = {'CreationClassName': 'DCIM_BIOSService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:BIOSService',
                              'SystemCreationClassName': 'DCIM_ComputerSystem'}
        expected_properties = {'Target': 'BIOS.Setup.1-1',
                               'AttributeName': ['ProcVirtualization'],
                               'AttributeValue': ['Disabled']}
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSEnumeration]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSString]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSInteger]['ok']}])
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.BIOSInvocations[uris.DCIM_BIOSService][
                'SetAttributes']['ok'])

        result = self.drac_client.set_bios_settings(
            {'ProcVirtualization': 'Disabled'})

        self.assertEqual({'commit_required': True}, result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_BIOSService, 'SetAttributes',
            expected_selectors, expected_properties)

    @requests_mock.Mocker()
    def test_set_bios_settings_error(self, mock_requests):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSEnumeration]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSString]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSInteger]['ok']},
            {'text': test_utils.BIOSInvocations[
                uris.DCIM_BIOSService]['SetAttributes']['error']}])

        self.assertRaises(exceptions.DRACOperationFailed,
                          self.drac_client.set_bios_settings,
                          {'ProcVirtualization': 'Disabled'})

    @requests_mock.Mocker()
    def test_set_bios_settings_with_unknown_attr(self, mock_requests):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSEnumeration]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSString]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSInteger]['ok']}])

        self.assertRaises(exceptions.InvalidParameterValue,
                          self.drac_client.set_bios_settings, {'foo': 'bar'})

    @requests_mock.Mocker()
    def test_set_bios_settings_with_unchanged_attr(self, mock_requests):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSEnumeration]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSString]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSInteger]['ok']}])

        result = self.drac_client.set_bios_settings(
            {'ProcVirtualization': 'Enabled'})

        self.assertEqual({'commit_required': False}, result)

    @requests_mock.Mocker()
    def test_set_bios_settings_with_readonly_attr(self, mock_requests):
        expected_message = ("Cannot set read-only BIOS attributes: "
                            "['Proc1NumCores'].")
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSEnumeration]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSString]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSInteger]['ok']}])

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.set_bios_settings, {'Proc1NumCores': 42})

    @requests_mock.Mocker()
    def test_set_bios_settings_with_incorrect_enum_value(self, mock_requests):
        expected_message = ("Attribute 'MemTest' cannot be set to value "
                            "'foo'. It must be in ['Enabled', 'Disabled'].")
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSEnumeration]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSString]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSInteger]['ok']}])

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.set_bios_settings, {'MemTest': 'foo'})

    @requests_mock.Mocker()
    def test_set_bios_settings_with_incorrect_regexp(self, mock_requests):
        expected_message = ("Attribute 'SystemModelName' cannot be set to "
                            "value 'bar.' It must match regex 'foo'.")
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSEnumeration]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSString]['regexp']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSInteger]['ok']}])

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.set_bios_settings, {'SystemModelName': 'bar'})

    @requests_mock.Mocker()
    def test_set_bios_settings_with_out_of_bounds_value(self, mock_requests):
        expected_message = ('Attribute Proc1NumCores cannot be set to value '
                            '-42. It must be between 0 and 65535.')
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSEnumeration]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSString]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSInteger]['mutable']}])

        self.assertRaisesRegexp(
            exceptions.DRACOperationFailed, re.escape(expected_message),
            self.drac_client.set_bios_settings, {'Proc1NumCores': -42})


class ClientBIOSChangesTestCase(base.BaseTest):

    def setUp(self):
        super(ClientBIOSChangesTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_commit_pending_bios_changes(self, mock_create_config_job):
        self.drac_client.commit_pending_bios_changes()

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_BIOSService,
            cim_creation_class_name='DCIM_BIOSService',
            cim_name='DCIM:BIOSService', target='BIOS.Setup.1-1', reboot=False)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_commit_pending_bios_changes_with_reboot(self,
                                                     mock_create_config_job):
        self.drac_client.commit_pending_bios_changes(reboot=True)

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_BIOSService,
            cim_creation_class_name='DCIM_BIOSService',
            cim_name='DCIM:BIOSService', target='BIOS.Setup.1-1', reboot=True)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'delete_pending_config', spec_set=True, autospec=True)
    def test_abandon_pending_bios_changes(self, mock_delete_pending_config):
        self.drac_client.abandon_pending_bios_changes()

        mock_delete_pending_config.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_BIOSService,
            cim_creation_class_name='DCIM_BIOSService',
            cim_name='DCIM:BIOSService', target='BIOS.Setup.1-1')
