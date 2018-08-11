# Copyright (c) 2016-2018 Dell Inc. or its subsidiaries.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import re

import dracclient.utils as utils

from dracclient.resources import uris

LOG = logging.getLogger(__name__)


class NICAttribute(object):
    """Generic NIC attribute class"""

    def __init__(self, name, instance_id, current_value, pending_value,
                 read_only, fqdd):
        """Construct a NICAttribute object.

        :param name: name of the NIC attribute
        :param instance_id: opaque and unique identifier of the BIOS attribute
        :param current_value: current value of the NIC attribute
        :param pending_value: pending value of the NIC attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this NIC attribute can be changed
        :param fqdd: Fully Qualified Device Description of the NICCard
                Attribute
        """
        self.name = name
        self.instance_id = instance_id
        self.current_value = current_value
        self.pending_value = pending_value
        self.read_only = read_only
        self.fqdd = fqdd

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @classmethod
    def parse(cls, namespace, nic_attr_xml):
        """Parses XML and creates a NICAttribute object."""

        name = utils.get_wsman_resource_attr(nic_attr_xml,
                                             namespace,
                                             'AttributeName')
        instance_id = utils.get_wsman_resource_attr(nic_attr_xml,
                                                    namespace,
                                                    'InstanceID')
        current_value = utils.get_wsman_resource_attr(nic_attr_xml,
                                                      namespace,
                                                      'CurrentValue',
                                                      nullable=True)
        pending_value = utils.get_wsman_resource_attr(nic_attr_xml,
                                                      namespace,
                                                      'PendingValue',
                                                      nullable=True)
        read_only = utils.get_wsman_resource_attr(nic_attr_xml,
                                                  namespace,
                                                  'IsReadOnly')

        fqdd = utils.get_wsman_resource_attr(nic_attr_xml,
                                             namespace,
                                             'FQDD')

        return cls(name, instance_id, current_value, pending_value,
                   (read_only == 'true'), fqdd)


class NICEnumerationAttribute(NICAttribute):
    """Enumeration NIC attribute class"""

    namespace = uris.DCIM_NICEnumeration

    def __init__(self,
                 name,
                 instance_id,
                 current_value,
                 pending_value,
                 read_only,
                 fqdd,
                 possible_values):
        """Construct a NICEnumerationAttribute object.

        :param name: name of the NIC attribute
        :param instance_id: opaque and unique identifier of the BIOS attribute
        :param current_value: current value of the NIC attribute
        :param pending_value: pending value of the NIC attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this NIC attribute can be changed
        :param fqdd: Fully Qualified Device Description of the NICCard
                Attribute
        :param possible_values: list containing the allowed values for the NIC
                                attribute
        """
        super(NICEnumerationAttribute, self).__init__(name,
                                                      instance_id,
                                                      current_value,
                                                      pending_value,
                                                      read_only,
                                                      fqdd)
        self.possible_values = possible_values

    @classmethod
    def parse(cls, nic_attr_xml):
        """Parse XML and create a NICEnumerationAttribute object."""

        nic_attr = NICAttribute.parse(cls.namespace, nic_attr_xml)
        possible_values = [attr.text for attr
                           in utils.find_xml(nic_attr_xml,
                                             'PossibleValues',
                                             cls.namespace,
                                             find_all=True)]

        return cls(nic_attr.name,
                   nic_attr.instance_id,
                   nic_attr.current_value,
                   nic_attr.pending_value,
                   nic_attr.read_only,
                   nic_attr.fqdd,
                   possible_values)

    def validate(self, value):
        """Validate new value."""

        if str(value) not in self.possible_values:
            msg = ("Attribute '%(attr)s' cannot be set to value '%(val)s'."
                   " It must be in %(possible_values)r.") % {
                       'attr': self.name,
                       'val': value,
                       'possible_values': self.possible_values}
            return msg

        return None


class NICStringAttribute(NICAttribute):
    """String NIC attribute class."""

    namespace = uris.DCIM_NICString

    def __init__(self,
                 name,
                 instance_id,
                 current_value,
                 pending_value,
                 read_only,
                 fqdd,
                 min_length,
                 max_length,
                 pcre_regex):
        """Construct a NICStringAttribute object.

        :param name: name of the NIC attribute
        :param instance_id: opaque and unique identifier of the BIOS attribute
        :param current_value: current value of the NIC attribute
        :param pending_value: pending value of the NIC attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this NIC attribute can be changed
        :param fqdd: Fully Qualified Device Description of the NICCard
                Attribute
        :param min_length: minimum length of the string
        :param max_length: maximum length of the string
        :param pcre_regex: is a PCRE compatible regular expression that the
                           string must match
        """
        super(NICStringAttribute, self).__init__(name,
                                                 instance_id,
                                                 current_value,
                                                 pending_value,
                                                 read_only,
                                                 fqdd)
        self.min_length = min_length
        self.max_length = max_length
        self.pcre_regex = pcre_regex

    @classmethod
    def parse(cls, nic_attr_xml):
        """Parse XML and create a NICStringAttribute object."""

        nic_attr = NICAttribute.parse(cls.namespace, nic_attr_xml)
        min_length = int(utils.get_wsman_resource_attr(nic_attr_xml,
                                                       cls.namespace,
                                                       'MinLength'))
        max_length = int(utils.get_wsman_resource_attr(nic_attr_xml,
                                                       cls.namespace,
                                                       'MaxLength'))
        pcre_regex = utils.get_wsman_resource_attr(nic_attr_xml,
                                                   cls.namespace,
                                                   'ValueExpression',
                                                   nullable=True)

        return cls(nic_attr.name,
                   nic_attr.instance_id,
                   nic_attr.current_value,
                   nic_attr.pending_value,
                   nic_attr.read_only,
                   nic_attr.fqdd,
                   min_length,
                   max_length,
                   pcre_regex)

    def validate(self, value):
        """Validate new value."""

        if self.pcre_regex is not None:
            regex = re.compile(self.pcre_regex)

            if regex.search(str(value)) is None:
                msg = ("Attribute '%(attr)s' cannot be set to value '%(val)s.'"
                       " It must match regex '%(re)s'.") % {
                           'attr': self.name,
                           'val': value,
                           're': self.pcre_regex}
                return msg

        return None


class NICIntegerAttribute(NICAttribute):
    """Integer NIC attribute class."""

    namespace = uris.DCIM_NICInteger

    def __init__(self,
                 name,
                 instance_id,
                 current_value,
                 pending_value,
                 read_only,
                 fqdd,
                 lower_bound,
                 upper_bound):
        """Construct a NICIntegerAttribute object.

        :param name: name of the NIC attribute
        :param instance_id: opaque and unique identifier of the BIOS attribute
        :param current_value: current value of the NIC attribute
        :param pending_value: pending value of the NIC attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this NIC attribute can be changed
        :param fqdd: Fully Qualified Device Description of the NICCard
                Attribute
        :param lower_bound: minimum value for the NIC attribute
        :param upper_bound: maximum value for the NIC attribute
        """
        super(NICIntegerAttribute, self).__init__(name,
                                                  instance_id,
                                                  current_value,
                                                  pending_value,
                                                  read_only,
                                                  fqdd)
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    @classmethod
    def parse(cls, nic_attr_xml):
        """Parse XML and create a NICIntegerAttribute object."""

        nic_attr = NICAttribute.parse(cls.namespace, nic_attr_xml)
        lower_bound = utils.get_wsman_resource_attr(nic_attr_xml,
                                                    cls.namespace,
                                                    'LowerBound')
        upper_bound = utils.get_wsman_resource_attr(nic_attr_xml,
                                                    cls.namespace,
                                                    'UpperBound')

        if nic_attr.current_value:
            nic_attr.current_value = int(nic_attr.current_value)

        if nic_attr.pending_value:
            nic_attr.pending_value = int(nic_attr.pending_value)

        return cls(nic_attr.name,
                   nic_attr.instance_id,
                   nic_attr.current_value,
                   nic_attr.pending_value,
                   nic_attr.read_only,
                   nic_attr.fqdd,
                   int(lower_bound),
                   int(upper_bound))

    def validate(self, value):
        """Validate new value."""

        val = int(value)

        if val < self.lower_bound or val > self.upper_bound:
            msg = ('Attribute %(attr)s cannot be set to value %(val)d.'
                   ' It must be between %(lower)d and %(upper)d.') % {
                       'attr': self.name,
                       'val': value,
                       'lower': self.lower_bound,
                       'upper': self.upper_bound}
            return msg

        return None


class NICConfiguration(object):

    NAMESPACES = [(uris.DCIM_NICEnumeration, NICEnumerationAttribute),
                  (uris.DCIM_NICString, NICStringAttribute),
                  (uris.DCIM_NICInteger, NICIntegerAttribute)]

    def __init__(self, client):
        """Construct a NICConfiguration object.

        :param client: an instance of WSManClient
        """
        self.client = client

    def list_nic_settings(self, nic_id):
        """Return the list of attribute settings of a NIC.

        :param nic_id: id of the network interface controller (NIC)
        :returns: dictionary containing the NIC settings. The keys are
                  attribute names. Each value is a
                  NICEnumerationAttribute, NICIntegerAttribute, or
                  NICStringAttribute object.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the iDRAC
                 interface
        """

        result = utils.list_settings(self.client,
                                     self.NAMESPACES,
                                     fqdd_filter=nic_id)

        return result

    def set_nic_settings(self, nic_id, new_settings):
        """Modify one or more settings of a NIC.

        To be more precise, it sets the pending_value parameter for each of the
        attributes passed in. For the values to be applied, a config job may
        need to be created and the node may need to be rebooted.

        :param nic_id: id of the network interface controller,
        :param new_settings: a dictionary containing the proposed values, with
                             each key being the name of attribute qualified
                             with the group ID in the form "group_id#name" and
                             the value being the proposed value.
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
        :raises: DRACUnexpectedReturnValue on return value mismatch
        :raises: InvalidParameterValue on invalid attribute
        """

        return utils.set_settings('iDRAC Card',
                                  self.client,
                                  self.NAMESPACES,
                                  new_settings,
                                  uris.DCIM_NICService,
                                  "DCIM_NICService",
                                  "DCIM:NICService",
                                  nic_id)
