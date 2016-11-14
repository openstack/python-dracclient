Usage
=====

Create a client object by providing the connection details of the DRAC card::

    client = dracclient.client.DRACClient('1.2.3.4', 'username', 's3cr3t')

.. note::
    By default it will use port 443, '/wsman' as path and https protocol.

You can override the default port, path and protocol::

    client = dracclient.client.DRACClient('1.2.3.4', 'username', 's3cr3t',
                                          port=443, path='/wsman',
                                          protocol='https')
