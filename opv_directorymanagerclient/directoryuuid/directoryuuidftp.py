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

import logging
import ftplib
import ftputil
import os
from urllib.parse import urlparse

from opv_directorymanagerclient.directoryuuid import DirectoryUuid
from opv_directorymanagerclient import Protocol

# https://docs.python.org/3/library/urllib.parse.html
# https://gist.github.com/slok/1447559

class FTPAnonSessionWithPort(ftplib.FTP):
    """
    Factory for FTPutil, to be able to deal with anonymous FTP and different port.
    """

    def __init__(self, host, userid, password, port):
        ftplib.FTP.__init__(self)
        self.connect(host, port)
        if userid is not None and password is not None:
            self.login(userid, password)
        else:
            self.login()

class SyncableFolder:

    def __init__(self, dir_uuid_path, os_utils):
        """
        :param dir_uuid_path: UUID directory path.
        :param os_utils: OS lib (like os), must implement : os_utils.walk, os_utils.path.join and os_utils.path.relpath.
        """
        self.os_utils = os_utils
        self.dir_uuid_path = dir_uuid_path

    def rel_walk(self):
        """
        Act like os.walk, but elements of tuple relative path to dir_uuid_path so that it can be easily used in an other context.
        """
        for (dir_full_path, dir_names, files_names) in self.os_utils.walk(self.dir_uuid_path):
            yield (self._get_rel_path(dir_full_path), dir_names, files_names)

    def _make_dir(self, rel_path):
        """
        Make dir with sub directories.
        :param rel_path: relative path.
        """
        logging.debug("_make_dir: rel_path=" + rel_path)
        dest = self.os_utils.path.join(self.dir_uuid_path, rel_path)
        return self.os_utils.makedirs(dest)

    def make_dirs(self, rel_paths):
        """
        Make directories with their relative paths (relative to the syncable folder location).
        """
        for p in rel_paths:
            self._make_dir(p)

    def cp_files(self, relatives_files_paths, src, cp_file_method):
        for rel_path in relatives_files_paths:
            cp_file_method(rel_path, src, self)

    def _get_rel_path(self, full_path):
        """
         Return relative path from full_path. Relative to dir_uuid_path.
        """
        return os.path.relpath(full_path, start=self.dir_uuid_path)

    def get_full_path(self, rel_path=None):
        """
        Return full paths (absolute FTP path or local path) with a relative to uuid directory path.
        :param rel_path: Optional, relative path if not specified will simply return the full path associated to directory UUID.
        """
        return self.os_utils.path.join(self.dir_uuid_path, rel_path) if rel_path is not None else self.dir_uuid_path

class DirectoryUuidFtp(DirectoryUuid):

    def __init__(self, *args, **kwargs):
        DirectoryUuid.__init__(self, *args, **kwargs)

        self.__ftp_host = None
        self.syncable_ftp = None
        self.syncable_local = SyncableFolder(self._local_directory, os)

    def __connectFtp(self, uri: str):
        """
        Initiate self.ftp, connect to FTP server if not already connected.
        """
        parsed_uri = urlparse(uri)
        self.__ftp_host = ftputil.FTPHost(
            parsed_uri.hostname,
            parsed_uri.username,
            parsed_uri.password,
            port=parsed_uri.port,
            session_factory=FTPAnonSessionWithPort)
        self.__ftp_host.chdir(parsed_uri.path)
        self.syncable_ftp = SyncableFolder(parsed_uri.path, self.__ftp_host)

    def _ensure_ftp_connexion(self):
        """
        Ensure FTP is connected.
        """
        if self.__ftp_host is None:
            self.__connectFtp(self._fetch_uri(protocol=Protocol.FTP))

    def __local_to_ftp_cp_file(self, rel_path: str, src: SyncableFolder, dest: SyncableFolder):
        """
        Atomic cp file from local -> FTP.
        :param rel_path: Relative path to directoryuuid root.
        :param src: source directory (should be local directory).
        :param des: destination directory (should be FTP directory).
        """
        logging.debug("__local_to_ftp_cp_file: " + str(src.get_full_path(rel_path)) + " -> " + str(dest.get_full_path(rel_path)))
        self.__ftp_host.upload_if_newer(src.get_full_path(rel_path), dest.get_full_path(rel_path))

    def __ftp_to_local_cp_file(self, rel_path, src, dest):
        """
        Atomic cp file from FTP -> local.
        :param rel_path: Relative path to directoryuuid root.
        :param src: source directory (should be FTP directory)
        :param des: destination directory (should be local directory).
        """
        logging.debug("__ftp_to_local_cp_file: " + str(src.get_full_path(rel_path)) + " -> " + str(dest.get_full_path(rel_path)))
        self.__ftp_host.download_if_newer(src.get_full_path(rel_path), dest.get_full_path(rel_path))

    def _push_files(self):
        """
        Push files to FTP server.
        """
        self._ensure_ftp_connexion()
        self.__sync(self.syncable_local, self.syncable_ftp, self.__local_to_ftp_cp_file)

    def _pull_files(self):
        """
        Pull files from FTP server.
        """
        self._ensure_ftp_connexion()
        self.__sync(self.syncable_ftp, self.syncable_local, self.__ftp_to_local_cp_file)

    def __sync(self, src: SyncableFolder, dest: SyncableFolder, cp_file_method):
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
