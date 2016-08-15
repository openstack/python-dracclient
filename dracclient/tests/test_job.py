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
import mock
import requests_mock

import dracclient.client
from dracclient import exceptions
import dracclient.resources.job
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils
from dracclient import utils


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
