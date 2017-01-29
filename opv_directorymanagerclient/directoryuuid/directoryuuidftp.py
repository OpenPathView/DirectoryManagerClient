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

from opv_directorymanagerclient.directoryuuid import DirectoryUuid, SyncableDirectory
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


class DirectoryUuidFtp(DirectoryUuid):

    def __init__(self, *args, **kwargs):
        self.__ftp_host = None
        self._syncable_ftp = None
        DirectoryUuid.__init__(self, *args, **kwargs)

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
        self._syncable_ftp = SyncableDirectory(parsed_uri.path, self.__ftp_host)

    def _ensure_ftp_connexion(self):
        """
        Ensure FTP is connected.
        """
        if self.__ftp_host is None:
            self.__connectFtp(self._fetch_uri(protocol=Protocol.FTP))

    def __local_to_ftp_cp_file(self, rel_path: str, src: SyncableDirectory, dest: SyncableDirectory):
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
        self.__sync(self._syncable_local, self._syncable_ftp, self.__local_to_ftp_cp_file)

    def _pull_files(self):
        """
        Pull files from FTP server.
        """
        self._ensure_ftp_connexion()
        self.__sync(self._syncable_ftp, self._syncable_local, self.__ftp_to_local_cp_file)

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
