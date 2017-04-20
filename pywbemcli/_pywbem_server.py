# (C) Copyright 2017 IBM Corp.
# (C) Copyright 2017 Inova Development Inc.
# All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Common Functions applicable across multiple components of pywbemcli
"""


from __future__ import absolute_import, unicode_literals

import re
import click

from pywbem import WBEMServer, WBEMConnection
from .config import DEFAULT_URI_SCHEME, DEFAULT_CONNECTION_TIMEOUT


WBEM_SERVER_OBJ = None


def _validate_server_uri(server):
    """
    Validate  and possibly complete the wbemserver uri provided.

      Parameters:

        server: (string):
          uri of the WBEMServer to which connection is being made including
          scheme, hostname/IPAddress, and optional port
      Returns:
        The input uri or uri extended to use DEFAULT_SCHEME as the
        scheme if not is provided

      Exceptions:
        click.CLICKException if scheme invalid

    """
    if server[0] == '/':
        url = server

    elif re.match(r"^https{0,1}://", server) is not None:
        url = server

    elif re.match(r"^[a-zA-Z0-9]+://", server) is not None:
        raise click.ClickException('Invalid scheme on server argument. %s'
                                   ' Use "http" or "https"' % server)
    else:
        url = "{scheme}://{host}".format(
            scheme=DEFAULT_URI_SCHEME,
            host=DEFAULT_URI_SCHEME)

    return url


class PywbemServer(object):
    """
    Envelope for connections with WBEM Server incorporates both the
    pywbem WBEMConnection and pywbem WBEMServer classes.

    The constructor is separated from the connection method to allow the
    object to be contstructed early but actually create the connection and
    WBEMServer objects only when required.  This allows parameters such
    as the password to be requested only when a connection is made.

    """

    # The following class level variables are the names for the env variables
    # where server connection information are be saved and used as alternate
    # input sources for pywbemcli arguments and options.
    server_envvar = 'PYWBEMCLI_SERVER'
    user_envvar = 'PYWBEMCLI_USER'
    password_envvar = 'PYWBEMCLI_PASSWORD'
    defaultnamespace_envvar = 'PYWBEMCLI_DEFAULT_NAMESPACE'
    timeout_envvar = 'PYWBEMCLI_TIMEOUT'
    keyfile_envvar = 'PYWBEMCLI_KEYFILE'
    certfile_envvar = 'PYWBEMCLI_CERTFILE'
    noverify_envvar = 'PYWBEMCLI_NOVERIFY'
    ca_certs_envvar = 'PYWBEMCLI_CA_CERTS'

    def __init__(self, server, default_namespace, name='default',
                 user=None, password=None, timeout=DEFAULT_CONNECTION_TIMEOUT,
                 noverify=True, certfile=None, keyfile=None, ca_certs=None,
                 verbose=False):
        """
            TODO
        """

        self._server_uri = server
        self._default_namespace = default_namespace
        self._user = user
        self._password = password
        self._timeout = timeout
        self._noverify = noverify
        self._certfile = certfile
        self._keyfile = keyfile
        self._ca_certs = ca_certs
        self._verbose = verbose
        self._name = name
        self._wbem_server = None
        self._validate_timeout()

    def __repr__(self):
        return 'PywbemServer(uri=%s name=%s ns=%s user=%s pw=%s timeout=%s ' \
               'noverify=%s certfile=%s keyfile=%s ca_certs=%s)' % \
               (self.server_uri, self.name, self.default_namespace,
                self.user, self.password, self.timeout, self.noverify,
                self.certfile, self.keyfile, self.ca_certs)

    @property
    def server_uri(self):
        """
        :term:`string`: Scheme with Hostname or IP address of the WBEM Server.
        """
        return self._server_uri

    @property
    def name(self):
        """
        :term:`string`: Defines a name for this connection object.
        """
        return self._name

    @property
    def user(self):
        """
        :term:`string`: Username on the WBEM Server.
        """
        return self._user

    @property
    def password(self):
        """
        :term:`string`: Password for this user on this WBEM Server.
        """
        return self._password

    @property
    def default_namespace(self):
        """
        :term:`string`: Namespace to be used as default  for requests.
        """
        return self._default_namespace

    @property
    def timeout(self):
        """
        :term: `int`: Connection timeout to be used on requests in seconds
        """
        return self._timeout

    @property
    def noverify(self):
        """
        :term: `bool`: Connection server verfication flag. If True
        server cert not verified during connection.
        """
        return self._noverify

    @property
    def certfile(self):
        """
        :term: `string`: certtificate for server or None if parameter not
        provided on input
        """
        return self._certfile

    @property
    def keyfile(self):
        """
        :term: `string`: keyfile or None if no keyfile parameter input
        """
        return self._keyfile

    @property
    def ca_certs(self):
        """
        :term: `list of strings`: List of ca_certs if provided on cmd line
        """
        return self._ca_certs

    @property
    def conn(self):
        """
        :class:`~pywbem.WBEMConnection` WBEMConnection to be used for requests.
        """
        # This is created in wbemserver and retained there.
        return self._wbem_server.conn

    @property
    def wbem_server(self):
        """
        :class:`~pywbem.WBEMConnection` WBEMServer instance to be used for
        requests.
        """
        return self._wbem_server

    def _validate_timeout(self):
        """
        Validate that timeout parameter is in proper range.

        Exception: ValueError in Invalid
        """
        if not self.timeout:   # disallow None
            ValueError('timout of None not allowed')
        if self.timeout is not None and (self.timeout < 0 or
                                         self.timeout > 300):
            ValueError('timeout option(%s) out of range %s to %s sec' %
                       (self.timeout, 0, 300))

    # TODO this function can be merged into get_password below
    def password_prompt(self, ctx):
        """
        Request password from console.
        """
        if self.user:
            ctx.spinner.stop()
            password = click.prompt(
                "Enter password (user {user})" .format(user=self.user),
                hide_input=True,
                confirmation_prompt=False, type=str, err=True)
            ctx.spinner.start()
            self._password = password
        else:
            raise click.ClickException("{cmd} requires user/password, but "
                                       "no password provided."
                                       .format(cmd=ctx.invoked_subcommand))

    def get_password(self, ctx):
        """Conditional password prompt function"""
        if self.user and not self.password:
            self.password_prompt(ctx)

    def create_connection(self):
        """
        Initiate a WBEB connection, via PyWBEM api. Arguments for
        the request are the parameters required by the pywbem
        WBEMConnection constructor.
        See the pywbem WBEMConnection class for more details on the parameters.

           Return:
                pywbem WBEMConnection object that can be used to execute
                other pywbem cim_operation requests

           Exception:
               ValueError: if server paramer is invalid or other issues with
               the input values
        """
        if not self._server_uri:
            raise click.ClickException('Server URI is empty. Cannot connect.')

        self._server_uri = _validate_server_uri(self._server_uri)
        if self.keyfile is not None and self.certfile is None:
            ValueError('keyfile option requires certfile option')

        # If supplied by connect request, save the password
        # if password:
        #   self._password = password

        creds = (self.user, self.password) if self.user or \
            self.password else None

        # If client cert and key provided, create dictionary for
        # wbem connection certs (WBEMConnection takes dictionary for this info)
        x509_dict = None
        if self.certfile is not None:
            x509_dict = {"certfile": self.certfile}
            if self.keyfile is not None:
                x509_dict.update({'keyfile': self.keyfile})

        conn = WBEMConnection(self.server_uri, creds,
                              default_namespace=self.default_namespace,
                              no_verification=self.noverify,
                              x509=x509_dict, ca_certs=self.ca_certs,
                              timeout=self.timeout)
        # Save the connection object and create a WBEMServer object
        self._wbem_server = WBEMServer(conn)