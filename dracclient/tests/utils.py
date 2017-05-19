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

import os

from dracclient.resources import uris

FAKE_ENDPOINT = {
    'host': '1.2.3.4',
    'port': '443',
    'path': '/wsman',
    'protocol': 'https',
    'username': 'admin',
    'password': 's3cr3t'
}


def load_wsman_xml(name):
    """Helper function to load a WSMan XML response from a file."""

    with open(os.path.join(os.path.dirname(__file__), 'wsman_mocks',
              '%s.xml' % name), 'r') as f:
        xml_body = f.read()

    return xml_body

WSManEnumerations = {
    'context': [
        load_wsman_xml('wsman-enum_context-1'),
        load_wsman_xml('wsman-enum_context-2'),
        load_wsman_xml('wsman-enum_context-3'),
        load_wsman_xml('wsman-enum_context-4'),
    ]
}

BIOSEnumerations = {
    uris.DCIM_BIOSEnumeration: {
        'ok': load_wsman_xml('bios_enumeration-enum-ok')
    },
    uris.DCIM_BIOSInteger: {
        'mutable': load_wsman_xml('bios_integer-enum-mutable'),
        'ok': load_wsman_xml('bios_integer-enum-ok')
    },
    uris.DCIM_BIOSString: {
        'colliding': load_wsman_xml('bios_string-enum-colliding'),
        'ok': load_wsman_xml('bios_string-enum-ok'),
        'regexp': load_wsman_xml('bios_string-enum-regexp')
    },
    uris.DCIM_BootConfigSetting: {
        'ok': load_wsman_xml('boot_config_setting-enum-ok')
    },
    uris.DCIM_BootSourceSetting: {
        'ok': load_wsman_xml('boot_source_setting-enum-ok'),
        'ok-11g': load_wsman_xml('boot_source_setting-enum-ok-11g')
    },
    uris.DCIM_ComputerSystem: {
        'ok': load_wsman_xml('computer_system-enum-ok')
    },
}

BIOSInvocations = {
    uris.DCIM_ComputerSystem: {
        'RequestStateChange': {
            'ok': load_wsman_xml(
                'computer_system-invoke-request_state_change-ok'),
            'error': load_wsman_xml(
                'computer_system-invoke-request_state_change-error'),
        },
    },
    uris.DCIM_BIOSService: {
        'SetAttributes': {
            'ok': load_wsman_xml(
                'bios_service-invoke-set_attributes-ok'),
            'error': load_wsman_xml(
                'bios_service-invoke-set_attributes-error'),
        }
    },
    uris.DCIM_BootConfigSetting: {
        'ChangeBootOrderByInstanceID': {
            'ok': load_wsman_xml(
                'boot_config_setting-invoke-change_boot_order_by_instance_id-'
                'ok'),
            'error': load_wsman_xml(
                'boot_config_setting-invoke-change_boot_order_by_instance_id-'
                'error'),
        }
    }
}

InventoryEnumerations = {
    uris.DCIM_CPUView: {
        'ok': load_wsman_xml('cpu_view-enum-ok'),
        'missing_flags': load_wsman_xml('cpu_view-enum-missing_flags'),
        'empty_flag': load_wsman_xml('cpu_view-enum-empty_flag'),
    },
    uris.DCIM_MemoryView: {
        'ok': load_wsman_xml('memory_view-enum-ok')
    },
    uris.DCIM_NICView: {
        'ok': load_wsman_xml('nic_view-enum-ok')
    }
}

JobEnumerations = {
    uris.DCIM_LifecycleJob: {
        'ok': load_wsman_xml('lifecycle_job-enum-ok'),
        'not_found': load_wsman_xml('lifecycle_job-enum-not_found'),
    },
}

JobInvocations = {
    uris.DCIM_BIOSService: {
        'CreateTargetedConfigJob': {
            'ok': load_wsman_xml(
                'bios_service-invoke-create_targeted_config_job-ok'),
            'error': load_wsman_xml(
                'bios_service-invoke-create_targeted_config_job-error'),
        },
        'DeletePendingConfiguration': {
            'ok': load_wsman_xml(
                'bios_service-invoke-delete_pending_configuration-ok'),
            'error': load_wsman_xml(
                'bios_service-invoke-delete_pending_configuration-error'),
        },
    }
}

iDracCardEnumerations = {
    uris.DCIM_iDRACCardEnumeration: {
        'ok': load_wsman_xml('idraccard_enumeration-enum-ok')
    },
    uris.DCIM_iDRACCardString: {
        'ok': load_wsman_xml('idraccard_string-enum-ok')
    },
    uris.DCIM_iDRACCardInteger: {
        'ok': load_wsman_xml('idraccard_integer-enum-ok')
    },
}

LifecycleControllerEnumerations = {
    uris.DCIM_SystemView: {
        'ok': load_wsman_xml('system_view-enum-ok')
    },
    uris.DCIM_LCEnumeration: {
        'ok': load_wsman_xml('lc_enumeration-enum-ok')
    },
    uris.DCIM_LCString: {
        'ok': load_wsman_xml('lc_string-enum-ok')
    }
}

LifecycleControllerInvocations = {
    uris.DCIM_LCService: {
        'GetRemoteServicesAPIStatus': {
            'is_ready': load_wsman_xml('lc_getremoteservicesapistatus_ready'),
            'is_not_ready': load_wsman_xml(
                'lc_getremoteservicesapistatus_not_ready')
        }
    }
}

RAIDEnumerations = {
    uris.DCIM_ControllerView: {
        'ok': load_wsman_xml('controller_view-enum-ok')
    },
    uris.DCIM_PhysicalDiskView: {
        'ok': load_wsman_xml('physical_disk_view-enum-ok')
    },
    uris.DCIM_VirtualDiskView: {
        'ok': load_wsman_xml('virtual_disk_view-enum-ok')
    }
}

RAIDInvocations = {
    uris.DCIM_RAIDService: {
        'CreateVirtualDisk': {
            'ok': load_wsman_xml(
                'raid_service-invoke-create_virtual_disk-ok'),
            'error': load_wsman_xml(
                'raid_service-invoke-create_virtual_disk-error'),
        },
        'DeleteVirtualDisk': {
            'ok': load_wsman_xml(
                'raid_service-invoke-delete_virtual_disk-ok'),
            'error': load_wsman_xml(
                'raid_service-invoke-delete_virtual_disk-error'),
        },
        'ConvertToRAID': {
            'ok': load_wsman_xml(
                'raid_service-invoke-convert_physical_disks-ok'),
            'error': load_wsman_xml(
                'raid_service-invoke-convert_physical_disks-error'),
        }
    }
}
