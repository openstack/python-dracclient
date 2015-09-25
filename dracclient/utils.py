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

"""
Common functionalities shared between different DRAC modules.
"""

# ReturnValue constants
RET_SUCCESS = '0'
RET_ERROR = '2'
RET_CREATED = '4096'


def find_xml(doc, item, namespace, find_all=False):
    """Find the first or all elements in an ElementTree object.

    :param doc: the element tree object.
    :param item: the element name.
    :param namespace: the namespace of the element.
    :param find_all: Boolean value, if True find all elements, if False
                     find only the first one. Defaults to False.
    :returns: if find_all is False the element object will be returned
              if found, None if not found. If find_all is True a list of
              element objects will be returned or an empty list if no
              elements were found.

    """
    query = ('.//{%(namespace)s}%(item)s' % {'namespace': namespace,
                                             'item': item})
    if find_all:
        return doc.findall(query)
    return doc.find(query)
