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

# iDRAC is ready retry constants
DEFAULT_IDRAC_IS_READY_RETRIES = 96
DEFAULT_IDRAC_IS_READY_RETRY_DELAY_SEC = 10

# Web Services Management (WS-Management and WS-Man) SSL retry on error
# behavior constants
DEFAULT_WSMAN_SSL_ERROR_RETRIES = 3
DEFAULT_WSMAN_SSL_ERROR_RETRY_DELAY_SEC = 0

# power states
POWER_ON = 'POWER_ON'
POWER_OFF = 'POWER_OFF'
REBOOT = 'REBOOT'

PRIMARY_STATUS = {
    '0': 'unknown',
    '1': 'ok',
    '2': 'degraded',
    '3': 'error'
}

# binary unit constants
UNITS_KI = 2 ** 10


# Reboot required indicator
# Note: When the iDRAC returns optional for this value, this indicates that
# either a reboot may be performed to complete the operation or a real time
# config job may be created to complete the operation without performing a
# reboot.  This library does not currently support creating a real time config
# job, so a reboot must be performed when a value of "optional" is returned.
class RebootRequired(object):
    true = 'true'
    optional = 'optional'
    false = 'false'

    @classmethod
    def all(cls):
        return [cls.true, cls.optional, cls.false]


class RebootJobType(object):
    """Enumeration of different reboot job types."""

    power_cycle = 'power_cycle'
    """Hard power off, power on cycle"""

    graceful_reboot = 'graceful_reboot'
    """OS level reboot and wait for OS shutdown"""

    reboot_forced_shutdown = 'reboot_forced_shutdown'
    """OS level reboot and force power cycle if OS does not shut
    down
    """

    @classmethod
    def all(cls):
        return [cls.power_cycle,
                cls.graceful_reboot,
                cls.reboot_forced_shutdown]
