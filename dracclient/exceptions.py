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


class BaseClientException(Exception):

    msg_fmt = 'An unknown exception occurred'

    def __init__(self, message=None, **kwargs):
        message = self.msg_fmt % kwargs
        super(BaseClientException, self).__init__(message)


class DRACRequestFailed(BaseClientException):
    pass


class DRACOperationFailed(DRACRequestFailed):
    msg_fmt = ('DRAC operation failed. Messages: %(drac_messages)s')


class DRACUnexpectedReturnValue(DRACRequestFailed):
    msg_fmt = ('DRAC operation yielded return value %(actual_return_value)s '
               'that is neither error nor the expected '
               '%(expected_return_value)s')


class DRACEmptyResponseField(BaseClientException):
    msg_fmt = ("Attribute '%(attr)s' is not nullable, but no value received")


class DRACMissingResponseField(BaseClientException, AttributeError):
    msg_fmt = ("Attribute '%(attr)s' is missing from the response")


class InvalidParameterValue(BaseClientException):
    msg_fmt = '%(reason)s'


class WSManRequestFailure(BaseClientException):
    msg_fmt = ('WSMan request failed')


class WSManInvalidResponse(BaseClientException):
    msg_fmt = ('Invalid response received. Status code: "%(status_code)s", '
               'reason: "%(reason)s"')


class WSManInvalidFilterDialect(BaseClientException):
    msg_fmt = ('Invalid filter dialect "%(invalid_filter)s". '
               'Supported options are %(supported)s')
