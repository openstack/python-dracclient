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
from dracclient.resources import uris
from dracclient import utils

CPU_CHARACTERISTICS_64BIT = '4'

NIC_LINK_SPEED_MBPS = {
    '0': None,
    '1': 10,
    '2': 100,
    '3': 1000,
    '4': 2.5 * constants.UNITS_KI,
    '5': 10 * constants.UNITS_KI,
    '6': 20 * constants.UNITS_KI,
    '7': 40 * constants.UNITS_KI,
    '8': 100 * constants.UNITS_KI,
    '9': 25 * constants.UNITS_KI,
    '10': 50 * constants.UNITS_KI
}

NIC_LINK_DUPLEX = {
    '0': 'unknown',
    '1': 'full duplex',
    '2': 'half duplex'
}

NIC_MODE = {
    '0': 'unknown',
    '2': 'enabled',
    '3': 'disabled'}

CPU = collections.namedtuple(
    'CPU',
    ['id', 'cores', 'speed_mhz', 'model', 'status', 'ht_enabled',
     'turbo_enabled', 'vt_enabled', 'arch64'])

Memory = collections.namedtuple(
    'Memory',
    ['id', 'size_mb', 'speed_mhz', 'manufacturer', 'model', 'status'])

NIC = collections.namedtuple(
    'NIC',
    ['id', 'mac', 'model', 'speed_mbps', 'duplex', 'media_type'])


class InventoryManagement(object):

    def __init__(self, client):
        """Creates InventoryManagement object

        :param client: an instance of WSManClient
        """
        self.client = client

    def list_cpus(self):
        """Returns the list of CPUs

        :returns: a list of CPU objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
        """

        doc = self.client.enumerate(uris.DCIM_CPUView)

        cpus = utils.find_xml(doc, 'DCIM_CPUView',
                              uris.DCIM_CPUView,
                              find_all=True)

        return [self._parse_cpus(cpu) for cpu in cpus]

    def _parse_cpus(self, cpu):
        drac_characteristics = self._get_cpu_attr(cpu, 'Characteristics')
        arch64 = (CPU_CHARACTERISTICS_64BIT == drac_characteristics)

        return CPU(
            id=self._get_cpu_attr(cpu, 'FQDD'),
            cores=int(self._get_cpu_attr(cpu, 'NumberOfProcessorCores')),
            speed_mhz=int(self._get_cpu_attr(cpu, 'CurrentClockSpeed')),
            model=self._get_cpu_attr(cpu, 'Model'),
            status=constants.PRIMARY_STATUS[
                self._get_cpu_attr(cpu, 'PrimaryStatus')],
            ht_enabled=bool(self._get_cpu_attr(cpu, 'HyperThreadingEnabled',
                                               allow_missing=True)),
            turbo_enabled=bool(self._get_cpu_attr(cpu, 'TurboModeEnabled',
                                                  allow_missing=True)),
            vt_enabled=bool(self._get_cpu_attr(
                cpu, 'VirtualizationTechnologyEnabled', allow_missing=True)),
            arch64=arch64)

    def _get_cpu_attr(self, cpu, attr_name, allow_missing=False):
        return utils.get_wsman_resource_attr(
            cpu, uris.DCIM_CPUView, attr_name, allow_missing=allow_missing)

    def list_memory(self):
        """Returns the list of installed memory

        :returns: a list of Memory objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
        """

        doc = self.client.enumerate(uris.DCIM_MemoryView)

        installed_memory = utils.find_xml(doc, 'DCIM_MemoryView',
                                          uris.DCIM_MemoryView,
                                          find_all=True)

        return [self._parse_memory(memory) for memory in installed_memory]

    def _parse_memory(self, memory):
        return Memory(
            id=self._get_memory_attr(memory, 'FQDD'),
            size_mb=int(self._get_memory_attr(memory, 'Size')),
            speed_mhz=int(self._get_memory_attr(memory, 'Speed')),
            manufacturer=self._get_memory_attr(memory, 'Manufacturer'),
            model=self._get_memory_attr(memory, 'Model'),
            status=constants.PRIMARY_STATUS[
                self._get_memory_attr(memory, 'PrimaryStatus')])

    def _get_memory_attr(self, memory, attr_name):
        return utils.get_wsman_resource_attr(memory, uris.DCIM_MemoryView,
                                             attr_name)

    def list_nics(self):
        """Returns the list of NICs

        :returns: a list of NIC objects
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """

        doc = self.client.enumerate(uris.DCIM_NICView)
        drac_nics = utils.find_xml(doc, 'DCIM_NICView', uris.DCIM_NICView,
                                   find_all=True)

        return [self._parse_drac_nic(nic) for nic in drac_nics]

    def _parse_drac_nic(self, drac_nic):
        fqdd = self._get_nic_attr(drac_nic, 'FQDD')
        drac_speed = self._get_nic_attr(drac_nic, 'LinkSpeed')
        drac_duplex = self._get_nic_attr(drac_nic, 'LinkDuplex')

        return NIC(
            id=fqdd,
            mac=self._get_nic_attr(drac_nic, 'CurrentMACAddress'),
            model=self._get_nic_attr(drac_nic, 'ProductName'),
            speed_mbps=NIC_LINK_SPEED_MBPS[drac_speed],
            duplex=NIC_LINK_DUPLEX[drac_duplex],
            media_type=self._get_nic_attr(drac_nic, 'MediaType'))

    def _get_nic_attr(self, drac_nic, attr_name):
        return utils.get_wsman_resource_attr(drac_nic, uris.DCIM_NICView,
                                             attr_name)
