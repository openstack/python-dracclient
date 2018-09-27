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
from dracclient.resources import inventory
import dracclient.resources.job
from dracclient.resources import uris
from dracclient.tests import base
from dracclient.tests import utils as test_utils


@requests_mock.Mocker()
@mock.patch.object(dracclient.client.WSManClient, 'wait_until_idrac_is_ready',
                   spec_set=True, autospec=True)
class ClientInventoryManagementTestCase(base.BaseTest):

    def setUp(self):
        super(ClientInventoryManagementTestCase, self).setUp()
        self.drac_client = dracclient.client.DRACClient(
            **test_utils.FAKE_ENDPOINT)

    def test_list_cpus(self, mock_requests, mock_wait_until_idrac_is_ready):
        expected_cpu = [inventory.CPU(
            id='CPU.Socket.1',
            cores=6,
            speed_mhz=2400,
            model='Intel(R) Xeon(R) CPU E5-2620 v3 @ 2.40GHz',
            status='ok',
            ht_enabled=True,
            cpu_count=12,
            turbo_enabled=True,
            vt_enabled=True,
            arch64=True)]

        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.InventoryEnumerations[uris.DCIM_CPUView]['ok'])

        self.assertEqual(
            expected_cpu,
            self.drac_client.list_cpus())

    def test_list_cpus_with_missing_flags(self, mock_requests,
                                          mock_wait_until_idrac_is_ready):
        expected_cpu = [inventory.CPU(
            id='CPU.Socket.1',
            cores=8,
            speed_mhz=1900,
            model='Intel(R) Xeon(R) CPU E5-2440 v2 @ 1.90GHz',
            status='ok',
            ht_enabled=False,
            cpu_count=8,
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

    def test_list_memory(self, mock_requests, mock_wait_until_idrac_is_ready):
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

    def test_list_nics(self, mock_requests, mock_wait_until_idrac_is_ready):
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

    def test_get_system(self, mock_requests, mock_wait_until_idrac_is_ready):
        expected_system = inventory.System(
            id='System.Embedded.1',
            uuid='ebd4edd3-dfd7-4c7d-a2c8-562b3c23b811',
            service_tag='A1B2C3D',
            model='PowerEdge R630',
            lcc_version='2.1.0')
        mock_requests.post(
            'https://1.2.3.4:443/wsman',
            text=test_utils.LifecycleControllerEnumerations[
                uris.DCIM_SystemView]['ok'])
        self.assertEqual(
            expected_system,
            self.drac_client.get_system())
