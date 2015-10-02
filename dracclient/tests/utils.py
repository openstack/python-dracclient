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
