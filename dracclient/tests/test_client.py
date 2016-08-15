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
import random
import requests_mock

import dracclient.client
from dracclient import exceptions
from dracclient.resources import bios
from dracclient.resources import inventory
import dracclient.resources.job
from dracclient.resources import lifecycle_controller
from dracclient.resources import raid
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
    def test_list_bios_settings(self, mock_requests):
        expected_enum_attr = bios.BIOSEnumerableAttribute(
            name='MemTest',
            read_only=False,
            current_value='Disabled',
            pending_value=None,
            possible_values=['Enabled', 'Disabled'])
        expected_string_attr = bios.BIOSStringAttribute(
            name='SystemModelName',
            read_only=True,
            current_value='PowerEdge R320',
            pending_value=None,
            min_length=0,
            max_length=32,
            pcre_regex=None)
        expected_integer_attr = bios.BIOSIntegerAttribute(
            name='Proc1NumCores',
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

        bios_settings = self.drac_client.list_bios_settings()

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
    def test_list_bios_settings_with_colliding_attrs(self, mock_requests):
        mock_requests.post('https://1.2.3.4:443/wsman', [
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSEnumeration]['ok']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSString]['colliding']},
            {'text': test_utils.BIOSEnumerations[
                uris.DCIM_BIOSInteger]['ok']}])

        self.assertRaises(exceptions.DRACOperationFailed,
                          self.drac_client.list_bios_settings)

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


class ClientJobManagementTestCase(base.BaseTest):

    def setUp(self):
        super(ClientJobManagementTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    @requests_mock.Mocker()
    def test_list_jobs(self, mock_requests):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.JobEnumerations[uris.DCIM_LifecycleJob]['ok'])

        jobs = self.drac_client.list_jobs()

        self.assertEqual(6, len(jobs))

    @mock.patch.object(dracclient.client.WSManClient, 'enumerate',
                       spec_set=True, autospec=True)
    def test_list_jobs_only_unfinished(self, mock_enumerate):
        expected_filter_query = ('select * from DCIM_LifecycleJob '
                                 'where Name != "CLEARALL" and '
                                 'JobStatus != "Reboot Completed" and '
                                 'JobStatus != "Completed" and '
                                 'JobStatus != "Completed with Errors" and '
                                 'JobStatus != "Failed"')
        mock_enumerate.return_value = lxml.etree.fromstring(
            test_utils.JobEnumerations[uris.DCIM_LifecycleJob]['ok'])

        self.drac_client.list_jobs(only_unfinished=True)

        mock_enumerate.assert_called_once_with(
            mock.ANY, uris.DCIM_LifecycleJob,
            filter_query=expected_filter_query)

    @mock.patch.object(dracclient.client.WSManClient, 'enumerate',
                       spec_set=True, autospec=True)
    def test_get_job(self, mock_enumerate):
        expected_filter_query = ('select * from DCIM_LifecycleJob'
                                 ' where InstanceID="42"')
        # NOTE: This is the first job in the xml. Filtering the job is the
        #       responsibility of the controller, so not testing it.
        expected_job = dracclient.resources.job.Job(id='JID_CLEARALL',
                                                    name='CLEARALL',
                                                    start_time='TIME_NA',
                                                    until_time='TIME_NA',
                                                    message='NA',
                                                    status='Pending',
                                                    percent_complete='0')
        mock_enumerate.return_value = lxml.etree.fromstring(
            test_utils.JobEnumerations[uris.DCIM_LifecycleJob]['ok'])

        job = self.drac_client.get_job(42)

        mock_enumerate.assert_called_once_with(
            mock.ANY, uris.DCIM_LifecycleJob,
            filter_query=expected_filter_query)
        self.assertEqual(expected_job, job)

    @mock.patch.object(dracclient.client.WSManClient, 'enumerate',
                       spec_set=True, autospec=True)
    def test_get_job_not_found(self, mock_enumerate):
        expected_filter_query = ('select * from DCIM_LifecycleJob'
                                 ' where InstanceID="42"')
        mock_enumerate.return_value = lxml.etree.fromstring(
            test_utils.JobEnumerations[uris.DCIM_LifecycleJob]['not_found'])

        job = self.drac_client.get_job(42)

        mock_enumerate.assert_called_once_with(
            mock.ANY, uris.DCIM_LifecycleJob,
            filter_query=expected_filter_query)
        self.assertIsNone(job)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_create_config_job(self, mock_invoke):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        expected_selectors = {'CreationClassName': cim_creation_class_name,
                              'Name': cim_name,
                              'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Target': target,
                               'ScheduledStartTime': 'TIME_NOW'}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.JobInvocations[uris.DCIM_BIOSService][
                'CreateTargetedConfigJob']['ok'])

        job_id = self.drac_client.create_config_job(
            uris.DCIM_BIOSService, cim_creation_class_name, cim_name, target)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_BIOSService, 'CreateTargetedConfigJob',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_CREATED)
        self.assertEqual('JID_442507917525', job_id)

    @requests_mock.Mocker()
    def test_create_config_job_failed(self, mock_requests):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.JobInvocations[uris.DCIM_BIOSService][
                'CreateTargetedConfigJob']['error'])

        self.assertRaises(
            exceptions.DRACOperationFailed, self.drac_client.create_config_job,
            uris.DCIM_BIOSService, cim_creation_class_name, cim_name, target)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_create_config_job_with_reboot(self, mock_invoke):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        expected_selectors = {'CreationClassName': cim_creation_class_name,
                              'Name': cim_name,
                              'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Target': target,
                               'RebootJobType': '3',
                               'ScheduledStartTime': 'TIME_NOW'}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.JobInvocations[uris.DCIM_BIOSService][
                'CreateTargetedConfigJob']['ok'])

        job_id = self.drac_client.create_config_job(
            uris.DCIM_BIOSService, cim_creation_class_name, cim_name, target,
            reboot=True)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_BIOSService, 'CreateTargetedConfigJob',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_CREATED)
        self.assertEqual('JID_442507917525', job_id)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke', spec_set=True,
                       autospec=True)
    def test_delete_pending_config(self, mock_invoke):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        expected_selectors = {'CreationClassName': cim_creation_class_name,
                              'Name': cim_name,
                              'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'SystemName': 'DCIM:ComputerSystem'}
        expected_properties = {'Target': target}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.JobInvocations[uris.DCIM_BIOSService][
                'DeletePendingConfiguration']['ok'])

        self.drac_client.delete_pending_config(
            uris.DCIM_BIOSService, cim_creation_class_name, cim_name, target)

        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_BIOSService, 'DeletePendingConfiguration',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @requests_mock.Mocker()
    def test_delete_pending_config_failed(self, mock_requests):
        cim_creation_class_name = 'DCIM_BIOSService'
        cim_name = 'DCIM:BIOSService'
        target = 'BIOS.Setup.1-1'
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.JobInvocations[uris.DCIM_BIOSService][
                'DeletePendingConfiguration']['error'])

        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.delete_pending_config, uris.DCIM_BIOSService,
            cim_creation_class_name, cim_name, target)


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
class ClientRAIDManagementTestCase(base.BaseTest):

    def setUp(self):
        super(ClientRAIDManagementTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    def test_list_raid_controllers(self, mock_requests):
        expected_raid_controller = raid.RAIDController(
            id='RAID.Integrated.1-1',
            description='Integrated RAID Controller 1',
            manufacturer='DELL',
            model='PERC H710 Mini',
            firmware_version='21.3.0-0009')

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_ControllerView]['ok'])

        self.assertIn(expected_raid_controller,
                      self.drac_client.list_raid_controllers())

    def test_list_virtual_disks(self, mock_requests):
        expected_virtual_disk = raid.VirtualDisk(
            id='Disk.Virtual.0:RAID.Integrated.1-1',
            name='disk 0',
            description='Virtual Disk 0 on Integrated RAID Controller 1',
            controller='RAID.Integrated.1-1',
            raid_level='1',
            size_mb=571776,
            status='ok',
            raid_status='online',
            span_depth=1,
            span_length=2,
            pending_operations=None)

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_VirtualDiskView]['ok'])

        self.assertIn(expected_virtual_disk,
                      self.drac_client.list_virtual_disks())

    def test_list_physical_disks(self, mock_requests):
        expected_physical_disk = raid.PhysicalDisk(
            id='Disk.Bay.1:Enclosure.Internal.0-1:RAID.Integrated.1-1',
            description=('Disk 1 in Backplane 1 of '
                         'Integrated RAID Controller 1'),
            controller='RAID.Integrated.1-1',
            manufacturer='SEAGATE',
            model='ST600MM0006',
            media_type='hdd',
            interface_type='sas',
            size_mb=571776,
            free_size_mb=571776,
            serial_number='S0M3EY2Z',
            firmware_version='LS0A',
            status='ok',
            raid_status='ready')

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDEnumerations[uris.DCIM_PhysicalDiskView]['ok'])

        self.assertIn(expected_physical_disk,
                      self.drac_client.list_physical_disks())

    # Verify that various client convert_physical_disks calls to dracclient
    # result in a WSMan.invoke with appropriate parameters
    def _random_term(self):
        return "".join(random.sample('ABCDEFGHabcdefgh0123456',
                                     random.randint(4, 12)))

    def _random_fqdd(self):
        result = self._random_term()
        for i in range(0, random.randint(6, 10)):
            result += random.sample('.:-', 1)[0] + self._random_term()
        return result

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_convert_physical_disks_1(self, mock_requests, mock_invoke):
        '''Convert a single disk to RAID mode'''
        device_fqdd = self._random_fqdd()
        expected_invocation = 'ConvertToRAID'
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'PDArray': [device_fqdd]}

        result = self.drac_client.convert_physical_disks(
            raid_controller='controller',
            physical_disks=[device_fqdd],
            raid_enable=True)

        self.assertEqual({'commit_required': False}, result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, expected_invocation,
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_convert_physical_disks_n(self, mock_requests, mock_invoke):
        '''Convert a number of disks to RAID mode'''
        device_list = []
        for i in range(0, random.randint(2, 10)):
            device_list += self._random_fqdd()

        expected_invocation = 'ConvertToRAID'
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'PDArray': device_list}

        result = self.drac_client.convert_physical_disks(
            raid_controller='controller',
            physical_disks=device_list,
            raid_enable=True)

        self.assertEqual({'commit_required': False}, result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, expected_invocation,
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_convert_physical_disks_nonraid_1(self, mock_requests,
                                              mock_invoke):
        '''Convert a single disk to non-RAID mode'''
        device_fqdd = self._random_fqdd()
        expected_invocation = 'ConvertToNonRAID'
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'PDArray': [device_fqdd]}

        result = self.drac_client.convert_physical_disks(
            raid_controller='controller',
            physical_disks=[device_fqdd],
            raid_enable=False)

        self.assertEqual({'commit_required': False}, result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, expected_invocation,
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_convert_physical_disks_nonraid_n(self, mock_requests,
                                              mock_invoke):
        '''Convert a number of disks to non-RAID mode'''
        device_list = []
        for i in range(0, random.randint(2, 10)):
            device_list += self._random_fqdd()

        expected_invocation = 'ConvertToNonRAID'
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'PDArray': device_list}

        result = self.drac_client.convert_physical_disks(
            raid_controller='controller',
            physical_disks=device_list,
            raid_enable=False)

        self.assertEqual({'commit_required': False}, result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, expected_invocation,
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_convert_physical_disks_ok(self, mock_requests, mock_invoke):
        '''Convert a number of disks to RAID mode and check the return value'''
        device_list = []
        for i in range(0, random.randint(2, 10)):
            device_list += self._random_fqdd()

        expected_invocation = 'ConvertToRAID'
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'PDArray': device_list}

        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.RAIDInvocations[uris.DCIM_RAIDService][
                expected_invocation]['ok'])

        result = self.drac_client.convert_physical_disks(
            raid_controller='controller',
            physical_disks=device_list,
            raid_enable=True)

        self.assertEqual({'commit_required': True}, result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, expected_invocation,
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    def test_convert_physical_disks_fail(self, mock_requests):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDInvocations[
                uris.DCIM_RAIDService]['ConvertToRAID']['error'])

        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.convert_physical_disks,
            raid_controller='controller',
            physical_disks=['Disk0:Enclosure-1:RAID-1',
                            'Disk1:Enclosure-1:RAID-1'],
            raid_enable=True)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_create_virtual_disk(self, mock_requests, mock_invoke):
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'Target': 'controller',
                               'PDArray': ['disk1', 'disk2'],
                               'VDPropNameArray': ['Size', 'RAIDLevel'],
                               'VDPropValueArray': ['42', '4']}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.RAIDInvocations[uris.DCIM_RAIDService][
                'CreateVirtualDisk']['ok'])

        result = self.drac_client.create_virtual_disk(
            raid_controller='controller', physical_disks=['disk1', 'disk2'],
            raid_level='1', size_mb=42)

        self.assertEqual({'commit_required': True}, result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, 'CreateVirtualDisk',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_create_virtual_disk_with_extra_params(self, mock_requests,
                                                   mock_invoke):
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'Target': 'controller',
                               'PDArray': ['disk1', 'disk2'],
                               'VDPropNameArray': ['Size', 'RAIDLevel',
                                                   'VirtualDiskName',
                                                   'SpanDepth', 'SpanLength'],
                               'VDPropValueArray': ['42', '4', 'name', '3',
                                                    '2']}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.RAIDInvocations[uris.DCIM_RAIDService][
                'CreateVirtualDisk']['ok'])

        result = self.drac_client.create_virtual_disk(
            raid_controller='controller', physical_disks=['disk1', 'disk2'],
            raid_level='1', size_mb=42, disk_name='name', span_length=2,
            span_depth=3)

        self.assertEqual({'commit_required': True}, result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, 'CreateVirtualDisk',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    def test_create_virtual_disk_fail(self, mock_requests):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDInvocations[
                uris.DCIM_RAIDService]['CreateVirtualDisk']['error'])

        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level='1', size_mb=42,
            disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_missing_controller(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller=None,
            physical_disks=['disk1', 'disk2'], raid_level='1', size_mb=42,
            disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_missing_physical_disks(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=None, raid_level='1', size_mb=42,
            disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_missing_raid_level(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level=None, size_mb=42,
            disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_invalid_raid_level(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level='foo', size_mb=42,
            disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_missing_size(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level='1', size_mb=None,
            disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_invalid_size(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level='1',
            size_mb='foo', disk_name='name', span_length=2, span_depth=3)

    def test_create_virtual_disk_invalid_span_length(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level='1', size_mb=42,
            disk_name='name', span_length='foo', span_depth=3)

    def test_create_virtual_disk_invalid_span_depth(self, mock_requests):
        self.assertRaises(
            exceptions.InvalidParameterValue,
            self.drac_client.create_virtual_disk, raid_controller='controller',
            physical_disks=['disk1', 'disk2'], raid_level='1', size_mb=42,
            disk_name='name', span_length=2, span_depth='foo')

    @mock.patch.object(dracclient.client.WSManClient, 'invoke',
                       spec_set=True, autospec=True)
    def test_delete_virtual_disk(self, mock_requests, mock_invoke):
        expected_selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                              'CreationClassName': 'DCIM_RAIDService',
                              'SystemName': 'DCIM:ComputerSystem',
                              'Name': 'DCIM:RAIDService'}
        expected_properties = {'Target': 'disk1'}
        mock_invoke.return_value = lxml.etree.fromstring(
            test_utils.RAIDInvocations[uris.DCIM_RAIDService][
                'DeleteVirtualDisk']['ok'])

        result = self.drac_client.delete_virtual_disk('disk1')

        self.assertEqual({'commit_required': True}, result)
        mock_invoke.assert_called_once_with(
            mock.ANY, uris.DCIM_RAIDService, 'DeleteVirtualDisk',
            expected_selectors, expected_properties,
            expected_return_value=utils.RET_SUCCESS)

    def test_delete_virtual_disk_fail(self, mock_requests):
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.RAIDInvocations[
                uris.DCIM_RAIDService]['DeleteVirtualDisk']['error'])

        self.assertRaises(
            exceptions.DRACOperationFailed,
            self.drac_client.delete_virtual_disk, 'disk1')

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_commit_pending_raid_changes(self, mock_requests,
                                         mock_create_config_job):
        self.drac_client.commit_pending_raid_changes('controller')

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_RAIDService,
            cim_creation_class_name='DCIM_RAIDService',
            cim_name='DCIM:RAIDService', target='controller', reboot=False)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'create_config_job', spec_set=True, autospec=True)
    def test_commit_pending_raid_changes_with_reboot(self, mock_requests,
                                                     mock_create_config_job):
        self.drac_client.commit_pending_raid_changes('controller', reboot=True)

        mock_create_config_job.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_RAIDService,
            cim_creation_class_name='DCIM_RAIDService',
            cim_name='DCIM:RAIDService', target='controller', reboot=True)

    @mock.patch.object(dracclient.resources.job.JobManagement,
                       'delete_pending_config', spec_set=True, autospec=True)
    def test_abandon_pending_bios_changes(self, mock_requests,
                                          mock_delete_pending_config):
        self.drac_client.abandon_pending_raid_changes('controller')

        mock_delete_pending_config.assert_called_once_with(
            mock.ANY, resource_uri=uris.DCIM_RAIDService,
            cim_creation_class_name='DCIM_RAIDService',
            cim_name='DCIM:RAIDService', target='controller')


@requests_mock.Mocker()
class ClientInventoryManagementTestCase(base.BaseTest):

    def setUp(self):
        super(ClientInventoryManagementTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    def test_list_cpus(self, mock_requests):
        expected_cpu = [inventory.CPU(
            id='CPU.Socket.1',
            cores=6,
            speed_mhz=2400,
            model='Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz',
            status='ok',
            ht_enabled=True,
            turbo_enabled=True,
            vt_enabled=True,
            arch64=True)]

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.InventoryEnumerations[uris.DCIM_CPUView]['ok'])

        self.assertEqual(
            expected_cpu,
            self.drac_client.list_cpus())

    def test_list_cpus_with_missing_flags(self, mock_requests):
        expected_cpu = [inventory.CPU(
            id='CPU.Socket.1',
            cores=8,
            speed_mhz=1900,
            model='Intel(R) Xeon(R) CPU E5-2440 v2 @ 1.90GHz',
            status='ok',
            ht_enabled=False,
            turbo_enabled=False,
            vt_enabled=False,
            arch64=False)]

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.InventoryEnumerations[
                uris.DCIM_CPUView]['missing_flags'])

        self.assertEqual(
            expected_cpu,
            self.drac_client.list_cpus())

    def test_list_memory(self, mock_requests):
        expected_memory = [inventory.Memory(
            id='DIMM.Socket.A1',
            size_mb=16384,
            speed_mhz=2133,
            manufacturer='Samsung',
            model='DDR4 DIMM',
            status='ok')]

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.InventoryEnumerations[uris.DCIM_MemoryView]['ok'])

        self.assertEqual(
            expected_memory,
            self.drac_client.list_memory())

    def test_list_nics(self, mock_requests):
        expected_nics = [
            inventory.NIC(
                id='NIC.Embedded.1-1-1',
                mac='B0:83:FE:C6:6F:A1',
                model='Broadcom Gigabit Ethernet BCM5720 - B0:83:FE:C6:6F:A1',
                speed_mbps=1000,
                duplex='full duplex',
                media_type='Base T'),
            inventory.NIC(
                id='NIC.Slot.2-1-1',
                mac='A0:36:9F:52:7D:1E',
                model='Intel(R) Gigabit 2P I350-t Adapter - A0:36:9F:52:7D:1E',
                speed_mbps=1000,
                duplex='full duplex',
                media_type='Base T'),
            inventory.NIC(
                id='NIC.Slot.2-2-1',
                mac='A0:36:9F:52:7D:1F',
                model='Intel(R) Gigabit 2P I350-t Adapter - A0:36:9F:52:7D:1F',
                speed_mbps=1000,
                duplex='full duplex',
                media_type='Base T'),
            inventory.NIC(
                id='NIC.Embedded.2-1-1',
                mac='B0:83:FE:C6:6F:A2',
                model='Broadcom Gigabit Ethernet BCM5720 - B0:83:FE:C6:6F:A2',
                speed_mbps=1000,
                duplex='full duplex',
                media_type='Base T')]

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.InventoryEnumerations[uris.DCIM_NICView]['ok'])

        self.assertEqual(
            expected_nics,
            self.drac_client.list_nics())


@requests_mock.Mocker()
class WSManClientTestCase(base.BaseTest):

    def test_enumerate(self, mock_requests):
        mock_requests.post('https://1.2.3.4:443/wsman',
                           text='<result>yay!</result>')

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        resp = client.enumerate('http://resource')
        self.assertEqual('yay!', resp.text)

    def test_invoke(self, mock_requests):
        xml = """
<response xmlns:n1="http://resource">
    <n1:ReturnValue>42</n1:ReturnValue>
    <result>yay!</result>
</response>
"""  # noqa
        mock_requests.post('https://1.2.3.4:443/wsman', text=xml)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        resp = client.invoke('http://resource', 'Foo')
        self.assertEqual('yay!', resp.find('result').text)

    def test_invoke_with_expected_return_value(self, mock_requests):
        xml = """
<response xmlns:n1="http://resource">
    <n1:ReturnValue>42</n1:ReturnValue>
    <result>yay!</result>
</response>
"""  # noqa
        mock_requests.post('https://1.2.3.4:443/wsman', text=xml)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        resp = client.invoke('http://resource', 'Foo',
                             expected_return_value='42')
        self.assertEqual('yay!', resp.find('result').text)

    def test_invoke_with_error_return_value(self, mock_requests):
        xml = """
<response xmlns:n1="http://resource">
    <n1:ReturnValue>2</n1:ReturnValue>
    <result>yay!</result>
</response>
"""  # noqa
        mock_requests.post('https://1.2.3.4:443/wsman', text=xml)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        self.assertRaises(exceptions.DRACOperationFailed, client.invoke,
                          'http://resource', 'Foo')

    def test_invoke_with_unexpected_return_value(self, mock_requests):
        xml = """
<response xmlns:n1="http://resource">
    <n1:ReturnValue>42</n1:ReturnValue>
    <result>yay!</result>
</response>
"""  # noqa
        mock_requests.post('https://1.2.3.4:443/wsman', text=xml)

        client = dracclient.client.WSManClient(**test_utils.FAKE_ENDPOINT)
        self.assertRaises(exceptions.DRACUnexpectedReturnValue, client.invoke,
                          'http://resource', 'Foo',
                          expected_return_value='4242')
