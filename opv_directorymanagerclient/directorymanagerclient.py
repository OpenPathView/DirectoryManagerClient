# coding: utf-8

# Copyright (C) 2017 Open Path View
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

# Contributors: Benjamin BERNARD
# Email: benjamin.bernard@openpathview.fr

import requests
import logging

from tempfile import TemporaryDirectory
from opv_directorymanagerclient import OPVDMCException
from opv_directorymanagerclient import Protocol
from opv_directorymanagerclient import DirectoryUuidFtp

class DirectoryManagerClient:
    """
    OPV Directory Manager Client
    """

    def __init__(self, api_base=None, default_protocol=Protocol.FTP, workspace_directory=None):
        """
        :param api_base: Base URL for the storage API.
        :param default_protocol: Default protocol, if not specified FTP is choosen if available.
        :param workspace_directory: Directory were files will be temporary stored, default is a directory in /tmp, prefixed by 'OPVDirManClient'
        """
        self.__api_base = api_base
        self.__available_protocols = self.__fetch_protocols()
        self.__tempory_dir = TemporaryDirectory(prefix='OPVDirManClient-')
        self.__workspace_directory = workspace_directory if workspace_directory is not None else self.__tempory_dir.name
        logging.debug("Available protocoles on server are : " + str(self.__available_protocols))

        if len(self.__available_protocols) == 0:
            raise OPVDMCException("No supported protocols on server.")

        self.__default_protocol = default_protocol if default_protocol in self.__available_protocols else self.__available_protocols[0]
        logging.debug("Selected protocol : " + str(self.__default_protocol))

    def __str2Protocol(self, str):
        """
         Convert string to corresponding protocol.
        """
        try:
            return Protocol(str)
        except ValueError:
            return None

    def __fetch_protocols(self):
        """
        Returns available protocols.
        """
        logging.debug("__fetch_protocols")
        r = requests.get(self.__api_base + "/v1/protocols")
        if r.status_code != 200:
            raise OPVDMCException("Unable to get supported protocols (got HTTP status " + r.status_code)

        return list(filter(None.__ne__, map(self.__str2Protocol, r.json())))

    def Open(self, uuid=None):
        """
        Get a directory form it's uuid or create one.
        :param uuid: Optional directory's uuid.
        """
        if self.__default_protocol == Protocol.FTP:
            return DirectoryUuidFtp(uuid=uuid, api_base=self.__api_base, workspace_directory=self.__workspace_directory)
        raise NotImplemented

    @property
    def available_protocols(self):
        return self.__available_protocols
