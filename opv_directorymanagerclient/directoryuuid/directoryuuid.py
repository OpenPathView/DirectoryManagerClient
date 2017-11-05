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
import shutil
import logging
import requests
from path import Path

from tempfile import mkdtemp
from opv_directorymanagerclient import Protocol
from opv_directorymanagerclient import OPVDMCException
from opv_directorymanagerclient.directoryuuid import SyncableDirectory

class DirectoryUuid():
    """
    Manage a directory UUID.
    implement a ContextManager that return a (uuid, local path).
    """

    def __init__(self, workspace_directory, api_base: str, uuid=None, autosave=True):
        """
        :param uuid: Directory UUID.
        :param api_base: Api base URL.
        :param work_directory: Local directory used to store file. If you use local protocol you may use
                               a folder on the same partition so that cp will be hard link.
        :param autosave: Save changed data on the server at exit or context manager close (Default: True).
        """
        self.__api_base = api_base
        self.__workspace_directory = workspace_directory
        self._uuid = uuid if uuid is not None else self.__generate_uuid()
        self._syncable_local = None
        self._syncable_remote = None  # User need to define it in their implementation
        self.__create_local_directory()
        self._autosave = autosave

        # Fetching files for existing uuids
        if uuid is not None:
            self._pull_files()

    def __generate_uuid(self):
        """
        Generate a directory UUID.
        """
        logging.debug("__generate_uuid")
        rep = requests.post(self.__api_base + "/v1/directory")

        if rep.status_code != 200:
            raise OPVDMCException("Can't generate UUID", rep)

        self._uuid = rep.json()
        return self._uuid

    def _fetch_uri(self, protocol: Protocol):
        """
        Get a directory URI (with protocol).
        :param protocol: Wanted protocol URI.
        """
        logging.debug("_fetch_uri")
        rep = requests.get(self.__api_base + "/v1/directory/" + self._uuid + "/" + protocol.value)

        if rep.status_code != 200:
            raise OPVDMCException("Can't generate UUID", rep)

        self._uri = rep.json()
        return self._uri

    def __create_local_directory(self):
        """
         Create a working directory will be associated to the uuid directory.
        """
        self.__local_directory = mkdtemp(dir=self.__workspace_directory)
        self._syncable_local = SyncableDirectory(self.local_directory, os)
        logging.debug("Create local directory '" + str(self.__local_directory) + "' associated to uuid : " + str(self._uuid))

    def __delete_local_directory(self):
        """
        Remove directory associated to uuid directory.
        """
        if Path(self.__local_directory).isdir():
            shutil.rmtree(self.__local_directory)

    def _ensure_remote_connexion(self):
        """
        Ensure connexion to remote.
        """
        raise NotImplemented()

    def __sync(self, src: SyncableDirectory, dest: SyncableDirectory, cp_file_method):
        """
        Sync 2 folders.
        :param src: SyncableFolder source directory.
        :param dest: SyncableFolder destination directory.
        :param cp_file_method: Function use to transfert a file from source to destination.
                               This function takes (rel_path, srcSyncFolder, desSyncFolder).
        """

        for (src_path, dir_names, file_names) in src.rel_walk():
            logging.debug("__sync: src_path=" + src_path)

            # creating directories
            dir_relative_paths = [os.path.join(src_path, d_name) for d_name in dir_names]
            dest.make_dirs(dir_relative_paths)

            # copy files
            file_relative_paths = [os.path.join(src_path, f_name) for f_name in file_names]
            dest.cp_files(file_relative_paths, src, cp_file_method)

    def _cp_file_push_method(self, rel_path: str, src: SyncableDirectory, dest: SyncableDirectory):
        """
        Method used to cp files from local to remote (upload file).
        Needs to be defined in user implementation.*
        :param rel_path: Relative path to directoryuuid root of file we want to copy.
        :param src: Source directory (should be local).
        :param dest: Destination directory (should be remote).
        """
        raise NotImplemented()

    def _cp_file_pull_method(self, rel_path: str, src: SyncableDirectory, dest: SyncableDirectory):
        """
        Method used to cp files from remote to local (download file).
        Needs to be defined in user implementation.*
        :param rel_path: Relative path to directoryuuid root of file we want to copy.
        :param src: Source directory (should be remote).
        :param dest: Destination directory (should be local).
        """
        raise NotImplemented()

    def _pull_files(self):
        """
        Import and copy existing data to local_directory
        """
        self._ensure_remote_connexion()
        self.__sync(self._syncable_remote, self._syncable_local, self._cp_file_pull_method)

    def _push_files(self):
        """
        Push local_directory files to server.
        """
        self._ensure_remote_connexion()
        self.__sync(self._syncable_local, self._syncable_remote, self._cp_file_push_method)

    def save(self):
        """
        Save files back to server
        """
        self._push_files()

    def close(self):
        """
        Close and clean stuff without saving.
        Add connexion close when you subclass.
        """
        self.__delete_local_directory()

    @property
    def local_directory(self):
        """
         Return the directory where files are stored locally.
        """
        return self.__local_directory

    @property
    def uuid(self):
        """
        Return uuid.
        """
        return self._uuid

    def __enter__(self):
        """
         Context manager, enter.
         Do nothing as the pull action is already done at __init__.
         :return: Return (uuid, local_path).
        """
        return (self._uuid, self.local_directory)

    def __exit__(self, type, value, traceback):
        """
        Context manager.
        Save files back to server.
        """
        if self._autosave:
            self.save()
        self.close()
