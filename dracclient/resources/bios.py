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

from dracclient import constants
from dracclient import exceptions
from dracclient.resources import lifecycle_controller
from dracclient.resources import uris
from dracclient import utils

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

BootDevice = collections.namedtuple('BootDevice',
                                    ['id',  'boot_mode',
                                     'current_assigned_sequence',
                                     'pending_assigned_sequence',
                                     'bios_boot_string'])


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

        filter_query = ('select EnabledState from '
                        'DCIM_ComputerSystem where Name="srv:system"')
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
