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
import os
import requests
import logging

from tempfile import mkdtemp
from opv_directorymanagerclient import Protocol
from opv_directorymanagerclient import OPVDMCException

class DirectoryUuid():
    """
    Manage a directory UUID.
    """

    def __init__(self, workspace_directory, api_base: str, uuid=None):
        """
        :param uuid: Directory UUID.
        :param api_base: Api base URL.
        :param work_directory: Local directory used to store file. If you use local protocol you may use
                               a folder on the same partition so that cp will be hard link.
        """
        self.__api_base = api_base
        self.__workspace_directory = workspace_directory
        self._uuid = uuid if uuid is not None else self.__generate_uuid()
        self.__create_local_directory()

    def __generate_uuid(self):
        """
        Generate a directory UUID.
        """
        logging.debug("__generate_uuid")
        rep = requests.post(self.__api_base + "/v1/directory")

        if rep.status_code != 200:
            raise OPVDMCException("Can't generate UUID", rep)

        self._uuid = rep.text
        return self._uuid

    def _fetch_uri(self, protocol: Protocol):
        """
        Get a directory URI (with protocol).
        :param protocol: Wanted protocol URI.
        """
        logging.debug("_fetch_uri")
        rep = requests.get(self.__api_base + "/v1/directory/" + self._uuid)

        if rep.status_code != 200:
            raise OPVDMCException("Can't generate UUID", rep)

        self._uri = rep.text
        return self._uri

    def __create_local_directory(self):
        """
         Create a working directory will be associated to the uuid directory.
        """
        self.__local_directory = mkdtemp(dir=self.__workspace_directory)
        logging.debug("Create local directory '" + str(self.__local_directory) + "' associated to uuid : " + str(self._uuid))

    def __delete_local_directory(self):
        """
        Remove directory associated to uuid directory.
        """
        os.removedirs(self.__local_directory)

    def _pull_files(self):
        """
        Import and copy existing data to local_directory
        """
        raise NotImplemented()

    def _push_files(self):
        """
        Push local_directory files to server.
        """
        raise NotImplemented()

    def save(self):
        """
        Save files back to server
        """
        self._push_files()

    @property
    def _local_directory(self):
        """
         Return the directory where files are stored locally.
        """
        return self.__local_directory

    def __del__(self):
        """
        Save files back to server
        """
        self.save()
