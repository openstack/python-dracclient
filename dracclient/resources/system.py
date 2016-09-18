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

from dracclient.resources import uris
from dracclient import utils
from dracclient import wsman


class SystemConfiguration(object):

    def __init__(self, client):
        """Creates SystemManagement object

        :param client: an instance of WSManClient
        """
        self.client = client

    def list_system_settings(self):
        """List the System configuration settings

        :returns: a dictionary with the System settings using its name as the
                  key. The attributes are either SystemEnumerableAttribute,
                  SystemStringAttribute or SystemIntegerAttribute objects.
        :raises: WSManRequestFailure on request failures
        :raises: WSManInvalidResponse when receiving invalid response
        :raises: DRACOperationFailed on error reported back by the DRAC
                 interface
        """
        result = {}
        namespaces = [(uris.DCIM_SystemEnumeration, SystemEnumerableAttribute),
                      (uris.DCIM_SystemString, SystemStringAttribute),
                      (uris.DCIM_SystemInteger, SystemIntegerAttribute)]
        for (namespace, attr_cls) in namespaces:
            attribs = self._get_config(namespace, attr_cls)
            result.update(attribs)
        return result

    def _get_config(self, resource, attr_cls):
        result = {}

        doc = self.client.enumerate(resource)

        items = doc.find('.//{%s}Items' % wsman.NS_WSMAN)

        if items is not None:
            for item in items:
                attribute = attr_cls.parse(item)
                result[attribute.instance_id] = attribute
        return result


class SystemAttribute(object):
    """Generic System attribute class"""

    def __init__(self, name, instance_id, current_value, pending_value,
                 read_only, fqdd, group_id):
        """Creates SystemAttribute object

        :param name: name of the System attribute
        :param instance_id: InstanceID of the System attribute
        :param current_value: current value of the System attribute
        :param pending_value: pending value of the System attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this System attribute can be
                changed
        :param fqdd: Fully Qualified Device Description of the System attribute
        :param group_id: GroupID of System attribute
        """
        self.name = name
        self.instance_id = instance_id
        self.current_value = current_value
        self.pending_value = pending_value
        self.read_only = read_only
        self.fqdd = fqdd
        self.group_id = group_id

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def parse(cls, namespace, system_attr_xml):
        """Parses XML and creates SystemAttribute object"""

        name = utils.get_wsman_resource_attr(
            system_attr_xml, namespace, 'AttributeName')
        instance_id = utils.get_wsman_resource_attr(
            system_attr_xml, namespace, 'InstanceID')
        current_value = utils.get_wsman_resource_attr(
            system_attr_xml, namespace, 'CurrentValue', nullable=True)
        pending_value = utils.get_wsman_resource_attr(
            system_attr_xml, namespace, 'PendingValue', nullable=True)
        read_only = utils.get_wsman_resource_attr(
            system_attr_xml, namespace, 'IsReadOnly')
        fqdd = utils.get_wsman_resource_attr(
            system_attr_xml, namespace, 'FQDD')
        group_id = utils.get_wsman_resource_attr(
            system_attr_xml, namespace, 'GroupID')

        return cls(name, instance_id, current_value, pending_value,
                   (read_only == 'true'), fqdd, group_id)


class SystemEnumerableAttribute(SystemAttribute):
    """Enumerable System attribute class"""

    namespace = uris.DCIM_SystemEnumeration

    def __init__(self, name, instance_id, current_value, pending_value,
                 read_only, fqdd, group_id, possible_values):
        """Creates SystemEnumerableAttribute object

        :param name: name of the System attribute
        :param instance_id: InstanceID of the System attribute
        :param current_value: current value of the System attribute
        :param pending_value: pending value of the System attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this System attribute can be
                changed
        :param fqdd: Fully Qualified Device Description of the System attribute
        :param group_id: GroupID of System attribute
        :param possible_values: list containing the allowed values for the
                                System attribute
        """
        super(SystemEnumerableAttribute, self).__init__(name, instance_id,
                                                        current_value,
                                                        pending_value,
                                                        read_only, fqdd,
                                                        group_id)
        self.possible_values = possible_values

    @classmethod
    def parse(cls, system_attr_xml):
        """Parses XML and creates SystemEnumerableAttribute object"""

        system_attr = SystemAttribute.parse(
            cls.namespace, system_attr_xml)
        possible_values = [attr.text for attr
                           in utils.find_xml(system_attr_xml, 'PossibleValues',
                                             cls.namespace, find_all=True)]

        return cls(system_attr.name, system_attr.instance_id,
                   system_attr.current_value, system_attr.pending_value,
                   system_attr.read_only, system_attr.fqdd,
                   system_attr.group_id, possible_values)

    def validate(self, new_value):
        """Validates new value"""

        if str(new_value) not in self.possible_values:
            msg = ("Attribute '%(attr)s' cannot be set to value '%(val)s'."
                   " It must be in %(possible_values)r.") % {
                       'attr': self.name,
                       'val': new_value,
                       'possible_values': self.possible_values}
            return msg


class SystemStringAttribute(SystemAttribute):
    """String System attribute class"""

    namespace = uris.DCIM_SystemString

    def __init__(self, name, instance_id, current_value, pending_value,
                 read_only, fqdd, group_id, min_length, max_length):
        """Creates SystemStringAttribute object

        :param name: name of the System attribute
        :param instance_id: InstanceID of the System attribute
        :param current_value: current value of the System attribute
        :param pending_value: pending value of the System attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this System attribute can be
                changed
        :param fqdd: Fully Qualified Device Description of the System attribute
        :param group_id: GroupID of System attribute
        :param min_length: minimum length of the string
        :param max_length: maximum length of the string
        """
        super(SystemStringAttribute, self).__init__(name, instance_id,
                                                    current_value,
                                                    pending_value, read_only,
                                                    fqdd, group_id)
        self.min_length = min_length
        self.max_length = max_length

    @classmethod
    def parse(cls, system_attr_xml):
        """Parses XML and creates SystemStringAttribute object"""

        system_attr = SystemAttribute.parse(
            cls.namespace, system_attr_xml)
        min_length = int(utils.get_wsman_resource_attr(
            system_attr_xml, cls.namespace, 'MinLength'))
        max_length = int(utils.get_wsman_resource_attr(
            system_attr_xml, cls.namespace, 'MaxLength'))

        return cls(system_attr.name, system_attr.instance_id,
                   system_attr.current_value, system_attr.pending_value,
                   system_attr.read_only, system_attr.fqdd,
                   system_attr.group_id, min_length, max_length)


class SystemIntegerAttribute(SystemAttribute):
    """Integer System attribute class"""

    namespace = uris.DCIM_SystemInteger

    def __init__(self, name, instance_id, current_value, pending_value,
                 read_only, fqdd, group_id, lower_bound, upper_bound):
        """Creates SystemIntegerAttribute object

        :param name: name of the System attribute
        :param instance_id: InstanceID of the System attribute
        :param current_value: current value of the System attribute
        :param pending_value: pending value of the System attribute, reflecting
                an unprocessed change (eg. config job not completed)
        :param read_only: indicates whether this System attribute can be
                changed
        :param fqdd: Fully Qualified Device Description of the System attribute
        :param group_id: GroupID of System attribute
        :param lower_bound: minimum value for the System attribute
        :param upper_bound: maximum value for the BOIS attribute
        """
        super(SystemIntegerAttribute, self).__init__(name, instance_id,
                                                     current_value,
                                                     pending_value, read_only,
                                                     fqdd, group_id)
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    @classmethod
    def parse(cls, system_attr_xml):
        """Parses XML and creates SystemIntegerAttribute object"""

        system_attr = SystemAttribute.parse(cls.namespace, system_attr_xml)
        lower_bound = utils.get_wsman_resource_attr(
            system_attr_xml, cls.namespace, 'LowerBound', nullable=True)
        upper_bound = utils.get_wsman_resource_attr(
            system_attr_xml, cls.namespace, 'UpperBound', nullable=True)

        if system_attr.current_value:
            system_attr.current_value = int(system_attr.current_value)
        if system_attr.pending_value:
            system_attr.pending_value = int(system_attr.pending_value)

        if lower_bound:
            lower_bound = int(lower_bound)
        if upper_bound:
            upper_bound = int(upper_bound)
        return cls(system_attr.name, system_attr.instance_id,
                   system_attr.current_value, system_attr.pending_value,
                   system_attr.read_only, system_attr.fqdd,
                   system_attr.group_id, lower_bound, upper_bound)

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
