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
import re

from dracclient import constants
from dracclient import exceptions
from dracclient.resources import lifecycle_controller
from dracclient.resources import uris
from dracclient import utils
from dracclient import wsman

LOG = logging.getLogger(__name__)

POWER_STATES = {
    '2': constants.POWER_ON,
    '3': constants.POWER_OFF,
    '11': constants.REBOOT,
}

REVERSE_POWER_STATES = dict((v, k) for (k, v) in POWER_STATES.items())

BOOT_MODE_IS_CURRENT = {
    '1': True,
    '2': False
}

BOOT_MODE_IS_NEXT = {
    '1': True,   # is next
    '2': False,  # is not next
    '3': True    # is next for single use (one time boot only)
}

LC_CONTROLLER_VERSION_12G = (2, 0, 0)

BootMode = collections.namedtuple('BootMode', ['id', 'name', 'is_current',
                                               'is_next'])

BootDevice = collections.namedtuple(
    'BootDevice',
    ['id',  'boot_mode', 'current_assigned_sequence',
     'pending_assigned_sequence', 'bios_boot_string'])


class PowerManagement(object):

    def __init__(self, client):
        """Creates PowerManagement object

        :param client: an instance of WSManClient
        """
        self.client = client

    def get_power_state(self):
        """Returns the current power state of the node

        :returns: power state of the node, one of 'POWER_ON', 'POWER_OFF' or
                  'REBOOT'
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        filter_query = ('select EnabledState from DCIM_ComputerSystem')
        doc = self.client.enumerate(uris.DCIM_ComputerSystem,
                                    filter_query=filter_query)
        enabled_state = utils.find_xml(doc, 'EnabledState',
                                       uris.DCIM_ComputerSystem)

        return POWER_STATES[enabled_state.text]

    def set_power_state(self, target_state):
        """Turns the server power on/off or do a reboot

        :param target_state: target power state. Valid options are: 'POWER_ON',
                             'POWER_OFF' and 'REBOOT'.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        :raises: InvalidParameterValue on invalid target power state
        """

        try:
            drac_requested_state = REVERSE_POWER_STATES[target_state]
        except KeyError:
            msg = ("'%(target_state)s' is not supported. "
                   "Supported power states: %(supported_power_states)r") % {
                       'target_state': target_state,
                       'supported_power_states': list(REVERSE_POWER_STATES)}
            raise exceptions.InvalidParameterValue(reason=msg)

        selectors = {'CreationClassName': 'DCIM_ComputerSystem',
                     'Name': 'srv:system'}
        properties = {'RequestedState': drac_requested_state}

        self.client.invoke(uris.DCIM_ComputerSystem, 'RequestStateChange',
                           selectors, properties)


class BootManagement(object):

    def __init__(self, client):
        """Creates BootManagement object

        :param client: an instance of WSManClient
        """
        self.client = client

    def list_boot_modes(self):
        """Returns the list of boot modes

        :returns: list of BootMode objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        doc = self.client.enumerate(uris.DCIM_BootConfigSetting)

        drac_boot_modes = utils.find_xml(doc, 'DCIM_BootConfigSetting',
                                         uris.DCIM_BootConfigSetting,
                                         find_all=True)

        return [self._parse_drac_boot_mode(drac_boot_mode)
                for drac_boot_mode in drac_boot_modes]

    def list_boot_devices(self):
        """Returns the list of boot devices

        :returns: a dictionary with the boot modes and the list of associated
                  BootDevice objects, ordered by the pending_assigned_sequence
                  property
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        doc = self.client.enumerate(uris.DCIM_BootSourceSetting)

        drac_boot_devices = utils.find_xml(doc, 'DCIM_BootSourceSetting',
                                           uris.DCIM_BootSourceSetting,
                                           find_all=True)
        try:
            boot_devices = [self._parse_drac_boot_device(drac_boot_device)
                            for drac_boot_device in drac_boot_devices]
        except AttributeError:
            # DRAC 11g doesn't have the BootSourceType attribute on the
            # DCIM_BootSourceSetting resource
            controller_version = (
                lifecycle_controller.LifecycleControllerManagement(
                    self.client).get_version())

            if controller_version < LC_CONTROLLER_VERSION_12G:
                boot_devices = [
                    self._parse_drac_boot_device_11g(drac_boot_device)
                    for drac_boot_device in drac_boot_devices]
            else:
                raise

        # group devices by boot mode
        boot_devices_per_mode = {device.boot_mode: []
                                 for device in boot_devices}
        for device in boot_devices:
            boot_devices_per_mode[device.boot_mode].append(device)

        # sort the device list by pending assigned seqeuence
        for mode in boot_devices_per_mode.keys():
            boot_devices_per_mode[mode].sort(
                key=lambda device: device.pending_assigned_sequence)

        return boot_devices_per_mode

    def change_boot_device_order(self, boot_mode, boot_device_list):
        """Changes the boot device sequence for a boot mode

        :param boot_mode: boot mode for which the boot device list is to be
                          changed
        :param boot_device_list: a list of boot device ids in an order
                                 representing the desired boot sequence
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        """

        selectors = {'InstanceID': boot_mode}
        properties = {'source': boot_device_list}

        self.client.invoke(uris.DCIM_BootConfigSetting,
                           'ChangeBootOrderByInstanceID', selectors,
                           properties, expected_return_value=utils.RET_SUCCESS)

    def _parse_drac_boot_mode(self, drac_boot_mode):
        return BootMode(
            id=self._get_boot_mode_attr(drac_boot_mode, 'InstanceID'),
            name=self._get_boot_mode_attr(drac_boot_mode, 'ElementName'),
            is_current=BOOT_MODE_IS_CURRENT[self._get_boot_mode_attr(
                drac_boot_mode, 'IsCurrent')],
            is_next=BOOT_MODE_IS_NEXT[self._get_boot_mode_attr(
                drac_boot_mode, 'IsNext')])

    def _get_boot_mode_attr(self, drac_boot_mode, attr_name):
        return utils.get_wsman_resource_attr(drac_boot_mode,
                                             uris.DCIM_BootConfigSetting,
                                             attr_name)

    def _parse_drac_boot_device_common(self, drac_boot_device, instance_id,
                                       boot_mode):
        return BootDevice(
            id=instance_id,
            boot_mode=boot_mode,
            current_assigned_sequence=int(self._get_boot_device_attr(
                drac_boot_device, 'CurrentAssignedSequence')),
            pending_assigned_sequence=int(self._get_boot_device_attr(
                drac_boot_device, 'PendingAssignedSequence')),
            bios_boot_string=self._get_boot_device_attr(drac_boot_device,
                                                        'BIOSBootString'))

    def _parse_drac_boot_device(self, drac_boot_device):
        instance_id = self._get_boot_device_attr(drac_boot_device,
                                                 'InstanceID')
        boot_mode = self._get_boot_device_attr(drac_boot_device,
                                               'BootSourceType')

        return self._parse_drac_boot_device_common(drac_boot_device,
                                                   instance_id, boot_mode)

    def _parse_drac_boot_device_11g(self, drac_boot_device):
        instance_id = self._get_boot_device_attr(drac_boot_device,
                                                 'InstanceID')
        boot_mode = instance_id.split(':')[0]

        return self._parse_drac_boot_device_common(drac_boot_device,
                                                   instance_id, boot_mode)

    def _get_boot_device_attr(self, drac_boot_device, attr_name):
        return utils.get_wsman_resource_attr(drac_boot_device,
                                             uris.DCIM_BootSourceSetting,
                                             attr_name)


class BIOSAttribute(object):
    """Generic BIOS attribute class"""

    def __init__(self, name, instance_id, current_value, pending_value,
                 read_only):
        """Creates BIOSAttribute object

        :param name: name of the BIOS attribute
        :param instance_id: opaque and unique identifier of the BIOS attribute
        :param current_value: current value of the BIOS attribute
        :param pending_value: pending value of the BIOS attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this BIOS attribute can be changed
        """
        self.name = name
        self.instance_id = instance_id
        self.current_value = current_value
        self.pending_value = pending_value
        self.read_only = read_only

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def parse(cls, namespace, bios_attr_xml):
        """Parses XML and creates BIOSAttribute object"""

        name = utils.get_wsman_resource_attr(
            bios_attr_xml, namespace, 'AttributeName')
        instance_id = utils.get_wsman_resource_attr(
            bios_attr_xml, namespace, 'InstanceID')
        current_value = utils.get_wsman_resource_attr(
            bios_attr_xml, namespace, 'CurrentValue', nullable=True)
        pending_value = utils.get_wsman_resource_attr(
            bios_attr_xml, namespace, 'PendingValue', nullable=True)
        read_only = utils.get_wsman_resource_attr(
            bios_attr_xml, namespace, 'IsReadOnly')

        return cls(name, instance_id, current_value, pending_value,
                   (read_only == 'true'))


class BIOSEnumerableAttribute(BIOSAttribute):
    """Enumerable BIOS attribute class"""

    namespace = uris.DCIM_BIOSEnumeration

    def __init__(self, name, instance_id, current_value, pending_value,
                 read_only, possible_values):
        """Creates BIOSEnumerableAttribute object

        :param name: name of the BIOS attribute
        :param current_value: current value of the BIOS attribute
        :param pending_value: pending value of the BIOS attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this BIOS attribute can be changed
        :param possible_values: list containing the allowed values for the BIOS
                                attribute
        """
        super(BIOSEnumerableAttribute, self).__init__(name, instance_id,
                                                      current_value,
                                                      pending_value, read_only)
        self.possible_values = possible_values

    @classmethod
    def parse(cls, bios_attr_xml):
        """Parses XML and creates BIOSEnumerableAttribute object"""

        bios_attr = BIOSAttribute.parse(cls.namespace, bios_attr_xml)
        possible_values = [attr.text for attr
                           in utils.find_xml(bios_attr_xml, 'PossibleValues',
                                             cls.namespace, find_all=True)]

        return cls(bios_attr.name, bios_attr.instance_id,
                   bios_attr.current_value, bios_attr.pending_value,
                   bios_attr.read_only, possible_values)

    def validate(self, new_value):
        """Validates new value"""

        if str(new_value) not in self.possible_values:
            msg = ("Attribute '%(attr)s' cannot be set to value '%(val)s'."
                   " It must be in %(possible_values)r.") % {
                       'attr': self.name,
                       'val': new_value,
                       'possible_values': self.possible_values}
            return msg


class BIOSStringAttribute(BIOSAttribute):
    """String BIOS attribute class"""

    namespace = uris.DCIM_BIOSString

    def __init__(self, name, instance_id, current_value, pending_value,
                 read_only, min_length, max_length, pcre_regex):
        """Creates BIOSStringAttribute object

        :param name: name of the BIOS attribute
        :param current_value: current value of the BIOS attribute
        :param pending_value: pending value of the BIOS attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this BIOS attribute can be changed
        :param min_length: minimum length of the string
        :param max_length: maximum length of the string
        :param pcre_regex: is a PCRE compatible regular expression that the
                           string must match
        """
        super(BIOSStringAttribute, self).__init__(name, instance_id,
                                                  current_value, pending_value,
                                                  read_only)
        self.min_length = min_length
        self.max_length = max_length
        self.pcre_regex = pcre_regex

    @classmethod
    def parse(cls, bios_attr_xml):
        """Parses XML and creates BIOSStringAttribute object"""

        bios_attr = BIOSAttribute.parse(cls.namespace, bios_attr_xml)
        min_length = int(utils.get_wsman_resource_attr(
            bios_attr_xml, cls.namespace, 'MinLength'))
        max_length = int(utils.get_wsman_resource_attr(
            bios_attr_xml, cls.namespace, 'MaxLength'))
        pcre_regex = utils.get_wsman_resource_attr(
            bios_attr_xml, cls.namespace, 'ValueExpression', nullable=True)

        return cls(bios_attr.name, bios_attr.instance_id,
                   bios_attr.current_value, bios_attr.pending_value,
                   bios_attr.read_only, min_length, max_length, pcre_regex)

    def validate(self, new_value):
        """Validates new value"""

        if self.pcre_regex is not None:
            regex = re.compile(self.pcre_regex)
            if regex.search(str(new_value)) is None:
                msg = ("Attribute '%(attr)s' cannot be set to value '%(val)s.'"
                       " It must match regex '%(re)s'.") % {
                           'attr': self.name,
                           'val': new_value,
                           're': self.pcre_regex}
                return msg


class BIOSIntegerAttribute(BIOSAttribute):
    """Integer BIOS attribute class"""

    namespace = uris.DCIM_BIOSInteger

    def __init__(self, name, instance_id, current_value, pending_value,
                 read_only, lower_bound, upper_bound):
        """Creates BIOSIntegerAttribute object

        :param name: name of the BIOS attribute
        :param current_value: current value of the BIOS attribute
        :param pending_value: pending value of the BIOS attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this BIOS attribute can be changed
        :param lower_bound: minimum value for the BIOS attribute
        :param upper_bound: maximum value for the BIOS attribute
        """
        super(BIOSIntegerAttribute, self).__init__(name, instance_id,
                                                   current_value,
                                                   pending_value, read_only)
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    @classmethod
    def parse(cls, bios_attr_xml):
        """Parses XML and creates BIOSIntegerAttribute object"""

        bios_attr = BIOSAttribute.parse(cls.namespace, bios_attr_xml)
        lower_bound = utils.get_wsman_resource_attr(
            bios_attr_xml, cls.namespace, 'LowerBound')
        upper_bound = utils.get_wsman_resource_attr(
            bios_attr_xml, cls.namespace, 'UpperBound')

        if bios_attr.current_value:
            bios_attr.current_value = int(bios_attr.current_value)
        if bios_attr.pending_value:
            bios_attr.pending_value = int(bios_attr.pending_value)

        return cls(bios_attr.name, bios_attr.instance_id,
                   bios_attr.current_value, bios_attr.pending_value,
                   bios_attr.read_only, int(lower_bound), int(upper_bound))

    def validate(self, new_value):
        """Validates new value"""

        val = int(new_value)
        if val < self.lower_bound or val > self.upper_bound:
            msg = ('Attribute %(attr)s cannot be set to value %(val)d.'
                   ' It must be between %(lower)d and %(upper)d.') % {
                       'attr': self.name,
                       'val': new_value,
                       'lower': self.lower_bound,
                       'upper': self.upper_bound}
            return msg


class BIOSConfiguration(object):

    def __init__(self, client):
        """Creates BIOSConfiguration object

        :param client: an instance of WSManClient
        """
        self.client = client

    def list_bios_settings(self, by_name=True):
        """List the BIOS configuration settings

        :param by_name: Controls whether returned dictionary uses BIOS
                        attribute name or instance_id as key.
        :returns: a dictionary with the BIOS settings using its name as the
                  key. The attributes are either BIOSEnumerableAttribute,
                  BIOSStringAttribute or BIOSIntegerAttribute objects.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        result = {}
        namespaces = [(uris.DCIM_BIOSEnumeration, BIOSEnumerableAttribute),
                      (uris.DCIM_BIOSString, BIOSStringAttribute),
                      (uris.DCIM_BIOSInteger, BIOSIntegerAttribute)]
        for (namespace, attr_cls) in namespaces:
            attribs = self._get_config(namespace, attr_cls, by_name)
            if not set(result).isdisjoint(set(attribs)):
                raise exceptions.DRACOperationFailed(
                    drac_messages=('Colliding attributes %r' % (
                        set(result) & set(attribs))))
            result.update(attribs)
        return result

    def _get_config(self, resource, attr_cls, by_name):
        result = {}

        doc = self.client.enumerate(resource)
        items = doc.find('.//{%s}Items' % wsman.NS_WSMAN)

        for item in items:
            attribute = attr_cls.parse(item)
            if by_name:
                result[attribute.name] = attribute
            else:
                result[attribute.instance_id] = attribute

        return result

    def set_bios_settings(self, new_settings):
        """Sets the BIOS configuration

        To be more precise, it sets the pending_value parameter for each of the
        attributes passed in. For the values to be applied, a config job must
        be created and the node must be rebooted.

        :param new_settings: a dictionary containing the proposed values, with
                             each key being the name of attribute and the
                             value being the proposed value.
        :returns: a dictionary containing the commit_needed key with a boolean
                  value indicating whether a config job must be created for the
                  values to be applied.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        :raises: DRACUnexpectedReturnValue on return value mismatch
        :raises: InvalidParameterValue on invalid BIOS attribute
        """

        current_settings = self.list_bios_settings(by_name=True)
        # BIOS settings are returned as dict indexed by InstanceID.
        # However DCIM_BIOSService requires attribute name, not instance id
        # so recreate this as a dict indexed by attribute name
        # TODO(anish) : Enable this code if/when by_name gets deprecated
        # bios_settings = self.list_bios_settings(by_name=False)
        # current_settings = dict((value.name, value)
        #                         for key, value in bios_settings.items())
        unknown_keys = set(new_settings) - set(current_settings)
        if unknown_keys:
            msg = ('Unknown BIOS attributes found: %(unknown_keys)r' %
                   {'unknown_keys': unknown_keys})
            raise exceptions.InvalidParameterValue(reason=msg)

        read_only_keys = []
        unchanged_attribs = []
        invalid_attribs_msgs = []
        attrib_names = []
        candidates = set(new_settings)

        for attr in candidates:
            if str(new_settings[attr]) == str(
                    current_settings[attr].current_value):
                unchanged_attribs.append(attr)
            elif current_settings[attr].read_only:
                read_only_keys.append(attr)
            else:
                validation_msg = current_settings[attr].validate(
                    new_settings[attr])
                if validation_msg is None:
                    attrib_names.append(attr)
                else:
                    invalid_attribs_msgs.append(validation_msg)

        if unchanged_attribs:
            LOG.warning('Ignoring unchanged BIOS attributes: %r',
                        unchanged_attribs)

        if invalid_attribs_msgs or read_only_keys:
            if read_only_keys:
                read_only_msg = ['Cannot set read-only BIOS attributes: %r.'
                                 % read_only_keys]
            else:
                read_only_msg = []

            drac_messages = '\n'.join(invalid_attribs_msgs + read_only_msg)
            raise exceptions.DRACOperationFailed(
                drac_messages=drac_messages)

        if not attrib_names:
            return {'commit_required': False}

        selectors = {'CreationClassName': 'DCIM_BIOSService',
                     'Name': 'DCIM:BIOSService',
                     'SystemCreationClassName': 'DCIM_ComputerSystem',
                     'SystemName': 'DCIM:ComputerSystem'}
        properties = {'Target': 'BIOS.Setup.1-1',
                      'AttributeName': attrib_names,
                      'AttributeValue': [new_settings[attr] for attr
                                         in attrib_names]}
        doc = self.client.invoke(uris.DCIM_BIOSService, 'SetAttributes',
                                 selectors, properties)

        return {'commit_required': utils.is_reboot_required(
            doc, uris.DCIM_BIOSService)}
