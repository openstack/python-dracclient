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

import collections
import logging

from dracclient import constants
import dracclient.exceptions as exceptions
from dracclient.resources import uris
from dracclient import utils
from dracclient import wsman

LOG = logging.getLogger(__name__)

Job = collections.namedtuple(
    'Job',
    ['id', 'name', 'start_time', 'until_time', 'message', 'status',
     'percent_complete'])

REBOOT_TYPES = {
    constants.RebootJobType.power_cycle: '1',
    constants.RebootJobType.graceful_reboot: '2',
    constants.RebootJobType.reboot_forced_shutdown: '3',
}


class JobManagement(object):

    def __init__(self, client):
        """Creates JobManagement object

        :param client: an instance of WSManClient
        """
        self.client = client

    def list_jobs(self, only_unfinished=False):
        """Returns a list of jobs from the job queue

        :param only_unfinished: indicates whether only unfinished jobs should
                                be returned
        :returns: a list of Job objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        filter_query = None
        if only_unfinished:
            filter_query = ('select * from DCIM_LifecycleJob '
                            'where Name != "CLEARALL" and '
                            'JobStatus != "Reboot Completed" and '
                            'JobStatus != "Reboot Failed" and '
                            'JobStatus != "Completed" and '
                            'JobStatus != "Completed with Errors" and '
                            'JobStatus != "Failed"')

        doc = self.client.enumerate(uris.DCIM_LifecycleJob,
                                    filter_query=filter_query)

        drac_jobs = utils.find_xml(doc, 'DCIM_LifecycleJob',
                                   uris.DCIM_LifecycleJob, find_all=True)

        return [self._parse_drac_job(drac_job) for drac_job in drac_jobs]

    def get_job(self, job_id):
        """Returns a job from the job queue

        :param job_id: id of the job
        :returns: a Job object on successful query, None otherwise
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        filter_query = ('select * from DCIM_LifecycleJob where InstanceID="%s"'
                        % job_id)

        doc = self.client.enumerate(uris.DCIM_LifecycleJob,
                                    filter_query=filter_query)

        drac_job = utils.find_xml(doc, 'DCIM_LifecycleJob',
                                  uris.DCIM_LifecycleJob)

        if drac_job is not None:
            return self._parse_drac_job(drac_job)

    def create_config_job(self, resource_uri, cim_creation_class_name,
                          cim_name, target,
                          cim_system_creation_class_name='DCIM_ComputerSystem',
                          cim_system_name='DCIM:ComputerSystem',
                          reboot=False,
                          start_time='TIME_NOW',
                          realtime=False):
        """Creates a config job

        In CIM (Common Information Model), weak association is used to name an
        instance of one class in the context of an instance of another class.
        SystemName and SystemCreationClassName are the attributes of the
        scoping system, while Name and CreationClassName are the attributes of
        the instance of the class, on which the CreateTargetedConfigJob method
        is invoked.

        :param resource_uri: URI of resource to invoke
        :param cim_creation_class_name: creation class name of the CIM object
        :param cim_name: name of the CIM object
        :param target: target device
        :param cim_system_creation_class_name: creation class name of the
                                               scoping system
        :param cim_system_name: name of the scoping system
        :param reboot: indicates whether a RebootJob should also be created or
                       not
        :param start_time: start time for job execution in format
                           yyyymmddhhmmss; the string 'TIME_NOW' means
                           immediately and None means the job is registered
                           but will not start execution until
                           schedule_job_execution is called with the returned
                           job id.
        :param realtime: Indicates if reatime mode should be used.
               Valid values are True and False. Default value is False.
        :returns: id of the created job
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """

        selectors = {'SystemCreationClassName': cim_system_creation_class_name,
                     'SystemName': cim_system_name,
                     'CreationClassName': cim_creation_class_name,
                     'Name': cim_name}

        properties = {'Target': target}

        if realtime:
            properties['RealTime'] = '1'

        if not realtime and reboot:
            properties['RebootJobType'] = '3'

        if start_time is not None:
            properties['ScheduledStartTime'] = start_time

        doc = self.client.invoke(resource_uri, 'CreateTargetedConfigJob',
                                 selectors, properties,
                                 expected_return_value=utils.RET_CREATED)

        return self._get_job_id(doc)

    def create_reboot_job(
            self,
            reboot_type=constants.RebootJobType.reboot_forced_shutdown):
        """Creates a reboot job.

        :param reboot_type: type of reboot
        :returns id of the created job
        :raises: InvalidParameterValue on invalid reboot type
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """

        try:
            drac_reboot_type = REBOOT_TYPES[reboot_type]
        except KeyError:
            msg = ("'%(reboot_type)s' is not supported. "
                   "Supported reboot types: %(supported_reboot_types)r") % {
                       'reboot_type': reboot_type,
                       'supported_reboot_types': list(REBOOT_TYPES)}
            raise exceptions.InvalidParameterValue(reason=msg)

        selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                     'SystemName': 'idrac',
                     'CreationClassName': 'DCIM_JobService',
                     'Name': 'JobService'}

        properties = {'RebootJobType': drac_reboot_type}

        doc = self.client.invoke(uris.DCIM_JobService,
                                 'CreateRebootJob',
                                 selectors,
                                 properties,
                                 expected_return_value=utils.RET_CREATED)

        return self._get_job_id(doc)

    def schedule_job_execution(self, job_ids, start_time='TIME_NOW'):
        """Schedules jobs for execution in a specified order.

        :param job_ids: list of job identifiers
        :param start_time: start time for job execution in format
                           yyyymmddhhmmss; the string 'TIME_NOW' means
                           immediately
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """

        # If the list of job identifiers is empty, there is nothing to do.
        if not job_ids:
            return

        selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                     'SystemName': 'idrac',
                     'CreationClassName': 'DCIM_JobService',
                     'Name': 'JobService'}

        properties = {'JobArray': job_ids,
                      'StartTimeInterval': start_time}

        self.client.invoke(uris.DCIM_JobService,
                           'SetupJobQueue',
                           selectors,
                           properties,
                           expected_return_value=utils.RET_SUCCESS)

    def _get_job_id(self, doc):
        query = (
            './/{%(namespace)s}%(item)s[@%(attribute_name)s='
            '"%(attribute_value)s"]' % {
                'namespace': wsman.NS_WSMAN,
                'item': 'Selector',
                'attribute_name': 'Name',
                'attribute_value': 'InstanceID'})
        job_id = doc.find(query).text
        return job_id

    def delete_jobs(self, job_ids=['JID_CLEARALL']):
        """Deletes the given jobs, or all jobs if none specified

        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface
        :raises: DRACUnexpectedReturnValue on non-success
        """

        selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                     'SystemName': 'idrac',
                     'CreationClassName': 'DCIM_JobService',
                     'Name': 'JobService'}

        if job_ids is None:
            return

        messages = []

        for job_id in job_ids:
            properties = {'JobID': job_id}

            try:
                self.client.invoke(
                    uris.DCIM_JobService,
                    'DeleteJobQueue',
                    selectors,
                    properties,
                    expected_return_value=utils.RET_SUCCESS)
            except exceptions.DRACOperationFailed as dof:
                for message in dof.args:
                    messages.append(message + " " + job_id)

        if len(messages):
            raise exceptions.DRACOperationFailed(drac_messages=messages)

    def delete_pending_config(
            self, resource_uri, cim_creation_class_name, cim_name, target,
            cim_system_creation_class_name='DCIM_ComputerSystem',
            cim_system_name='DCIM:ComputerSystem'):
        """Cancels pending configuration

        Once a config job has been submitted, it can no longer be abandoned.

        In CIM (Common Information Model), weak association is used to name an
        instance of one class in the context of an instance of another class.
        SystemName and SystemCreationClassName are the attributes of the
        scoping system, while Name and CreationClassName are the attributes of
        the instance of the class, on which the CreateTargetedConfigJob method
        is invoked.

        :param resource_uri: URI of resource to invoke
        :param cim_creation_class_name: creation class name of the CIM object
        :param cim_name: name of the CIM object
        :param target: target device
        :param cim_system_creation_class_name: creation class name of the
                                               scoping system
        :param cim_system_name: name of the scoping system
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """

        selectors = {'SystemCreationClassName': cim_system_creation_class_name,
                     'SystemName': cim_system_name,
                     'CreationClassName': cim_creation_class_name,
                     'Name': cim_name}

        properties = {'Target': target}

        self.client.invoke(resource_uri, 'DeletePendingConfiguration',
                           selectors, properties,
                           expected_return_value=utils.RET_SUCCESS)

    def _parse_drac_job(self, drac_job):
        return Job(id=self._get_job_attr(drac_job, 'InstanceID'),
                   name=self._get_job_attr(drac_job, 'Name'),
                   start_time=self._get_job_attr(drac_job, 'JobStartTime'),
                   until_time=self._get_job_attr(drac_job, 'JobUntilTime'),
                   message=self._get_job_attr(drac_job, 'Message'),
                   status=self._get_job_attr(drac_job, 'JobStatus'),
                   percent_complete=self._get_job_attr(drac_job,
                                                       'PercentComplete'))

    def _get_job_attr(self, drac_job, attr_name):
        return utils.get_wsman_resource_attr(drac_job, uris.DCIM_LifecycleJob,
                                             attr_name)
