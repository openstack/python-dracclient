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

from dracclient import constants
from dracclient.resources import uris
from dracclient import utils


class LifecycleControllerManagement(object):

    def __init__(self, client):
        """Creates LifecycleControllerManagement object

        :param client: an instance of WSManClient
        """
        self.client = client

    def get_version(self):
        """Returns the Lifecycle controller version

        :returns: Lifecycle controller version as a tuple of integers
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        doc = self.client.enumerate(uris.DCIM_SystemView, wait_for_idrac=False)
        lc_version_str = utils.find_xml(doc, 'LifecycleControllerVersion',
                                        uris.DCIM_SystemView).text

        return tuple(map(int, (lc_version_str.split('.'))))


class LCAttribute(object):
    """Generic LC attribute class"""

    def __init__(self, name, instance_id, current_value, pending_value,
                 read_only):
        """Creates LCAttribute object

        :param name: name of the LC attribute
        :param instance_id: InstanceID of the LC attribute
        :param current_value: current value of the LC attribute
        :param pending_value: pending value of the LC attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this LC attribute can be changed
        """
        self.name = name
        self.instance_id = instance_id
        self.current_value = current_value
        self.pending_value = pending_value
        self.read_only = read_only

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @classmethod
    def parse(cls, namespace, lifecycle_attr_xml):
        """Parses XML and creates LCAttribute object"""

        name = utils.get_wsman_resource_attr(
            lifecycle_attr_xml, namespace, 'AttributeName')
        instance_id = utils.get_wsman_resource_attr(
            lifecycle_attr_xml, namespace, 'InstanceID')
        current_value = utils.get_wsman_resource_attr(
            lifecycle_attr_xml, namespace, 'CurrentValue', nullable=True)
        pending_value = utils.get_wsman_resource_attr(
            lifecycle_attr_xml, namespace, 'PendingValue', nullable=True)
        read_only = utils.get_wsman_resource_attr(
            lifecycle_attr_xml, namespace, 'IsReadOnly')

        return cls(name, instance_id, current_value, pending_value,
                   (read_only == 'true'))


class LCEnumerableAttribute(LCAttribute):
    """Enumerable LC attribute class"""

    namespace = uris.DCIM_LCEnumeration

    def __init__(self, name, instance_id, current_value, pending_value,
                 read_only, possible_values):
        """Creates LCEnumerableAttribute object

        :param name: name of the LC attribute
        :param current_value: current value of the LC attribute
        :param pending_value: pending value of the LC attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this LC attribute can be changed
        :param possible_values: list containing the allowed values for the LC
                                attribute
        """
        super(LCEnumerableAttribute, self).__init__(name, instance_id,
                                                    current_value,
                                                    pending_value, read_only)
        self.possible_values = possible_values

    @classmethod
    def parse(cls, lifecycle_attr_xml):
        """Parses XML and creates LCEnumerableAttribute object"""

        lifecycle_attr = LCAttribute.parse(cls.namespace, lifecycle_attr_xml)
        possible_values = [attr.text for attr
                           in utils.find_xml(lifecycle_attr_xml,
                                             'PossibleValues',
                                             cls.namespace, find_all=True)]

        return cls(lifecycle_attr.name, lifecycle_attr.instance_id,
                   lifecycle_attr.current_value, lifecycle_attr.pending_value,
                   lifecycle_attr.read_only, possible_values)

    def validate(self, new_value):
        """Validates new value"""

        if str(new_value) not in self.possible_values:
            msg = ("Attribute '%(attr)s' cannot be set to value '%(val)s'."
                   " It must be in %(possible_values)r.") % {
                       'attr': self.name,
                       'val': new_value,
                       'possible_values': self.possible_values}
            return msg


class LCStringAttribute(LCAttribute):
    """String LC attribute class"""

    namespace = uris.DCIM_LCString

    def __init__(self, name, instance_id, current_value, pending_value,
                 read_only, min_length, max_length):
        """Creates LCStringAttribute object

        :param name: name of the LC attribute
        :param instance_id: InstanceID of the LC attribute
        :param current_value: current value of the LC attribute
        :param pending_value: pending value of the LC attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this LC attribute can be changed
        :param min_length: minimum length of the string
        :param max_length: maximum length of the string
        """
        super(LCStringAttribute, self).__init__(name, instance_id,
                                                current_value, pending_value,
                                                read_only)
        self.min_length = min_length
        self.max_length = max_length

    @classmethod
    def parse(cls, lifecycle_attr_xml):
        """Parses XML and creates LCStringAttribute object"""

        lifecycle_attr = LCAttribute.parse(cls.namespace, lifecycle_attr_xml)
        min_length = int(utils.get_wsman_resource_attr(
            lifecycle_attr_xml, cls.namespace, 'MinLength'))
        max_length = int(utils.get_wsman_resource_attr(
            lifecycle_attr_xml, cls.namespace, 'MaxLength'))

        return cls(lifecycle_attr.name, lifecycle_attr.instance_id,
                   lifecycle_attr.current_value, lifecycle_attr.pending_value,
                   lifecycle_attr.read_only, min_length, max_length)


class LCConfiguration(object):

    NAMESPACES = [(uris.DCIM_LCEnumeration, LCEnumerableAttribute),
                  (uris.DCIM_LCString, LCStringAttribute)]

    def __init__(self, client):
        """Creates LifecycleControllerManagement object

        :param client: an instance of WSManClient
        """
        self.client = client

    def list_lifecycle_settings(self, by_name=False):
        """List the LC configuration settings

        :param by_name: Controls whether returned dictionary uses Lifecycle
                        attribute name or instance_id as key.
        :returns: a dictionary with the LC settings using InstanceID as the
                  key. The attributes are either LCEnumerableAttribute,
                  LCStringAttribute or LCIntegerAttribute objects.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        return utils.list_settings(self.client, self.NAMESPACES, by_name)

    def is_lifecycle_in_recovery(self):
        """Check if Lifecycle Controller in recovery mode or not

        This method checks the LCStatus value to determine if lifecycle
        controller is in recovery mode by invoking GetRemoteServicesAPIStatus
        from iDRAC.

        :returns: a boolean indicating if lifecycle controller is in recovery
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        selectors = {'SystemCreationClassName': 'DCIM_ComputerSystem',
                     'SystemName': 'DCIM:ComputerSystem',
                     'CreationClassName': 'DCIM_LCService',
                     'Name': 'DCIM:LCService'}

        doc = self.client.invoke(uris.DCIM_LCService,
                                 'GetRemoteServicesAPIStatus',
                                 selectors,
                                 {},
                                 expected_return_value=utils.RET_SUCCESS,
                                 wait_for_idrac=False)

        lc_status = utils.find_xml(doc,
                                   'LCStatus',
                                   uris.DCIM_LCService).text

        return lc_status == constants.LC_IN_RECOVERY

    def set_lifecycle_settings(self, settings):
        """Sets the Lifecycle Controller configuration

        It sets the pending_value parameter for each of the attributes
        passed in. For the values to be applied, a config job must
        be created.

        :param settings: a dictionary containing the proposed values, with
                         each key being the name of attribute and the value
                         being the proposed value.
        :returns: a dictionary containing:
                 - The is_commit_required key with a boolean value indicating
                   whether a config job must be created for the values to be
                   applied.
                 - The is_reboot_required key with a RebootRequired enumerated
                   value indicating whether the server must be rebooted for the
                   values to be applied.  Possible values are true and false.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        return utils.set_settings('Lifecycle',
                                  self.client,
                                  self.NAMESPACES,
                                  settings,
                                  uris.DCIM_LCService,
                                  "DCIM_LCService",
                                  "DCIM:LCService",
                                  '',
                                  wait_for_idrac=False)
