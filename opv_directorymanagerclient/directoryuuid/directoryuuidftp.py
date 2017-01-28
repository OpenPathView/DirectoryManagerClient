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

from os import walk
import logging
from urllib.parse import urlparse
from ftplib import FTP

from opv_directorymanagerclient.directoryuuid import DirectoryUuid
from opv_directorymanagerclient import Protocol

# https://docs.python.org/3/library/urllib.parse.html
# https://gist.github.com/slok/1447559


class DirectoryUuidFtp(DirectoryUuid):

    def __init__(self, *args, **kwargs):
        self.__ftp = None
        DirectoryUuid.__init__(self, *args, **kwargs)

    def __connectFtp(self, uri: str):
        """
        Initiate self.ftp, connect to FTP server if not already connected.
        """
        parsed_uri = urlparse(uri)
        self.__ftp = FTP()
        self.__ftp.connect(parsed_uri.hostname, parsed_uri.port)
        if parsed_uri.username is not None:
            self.__ftp.login(parsed_uri.username, parsed_uri.password)
        self.__ftp_dir_path = parsed_uri.path

    def _pull_files(self):
        if self.__ftp is None:
            self.__connectFtp(self._fetch_uri(protocol=Protocol.FTP))

        pass

    def __mk_remote_dir(self, path: str):
        """
        Create remote directory if it doesn't exists.
        :param path: path to root (relative to uuidDir local_directory or associated ftp directory) of the current directory.
        """
        logging.debug('__mk_remote_dir : ' + self.__ftp_dir_path + '/' + path)
        # TODO actual mkdir

    def __mk_remote_dirs(self, paths: list):
        """
        Create remote directories if they doesn't exists.
        :param paths: a list of path (relative to FTP associated directory)
        """
        logging.debug('__mk_remote_dirs : ' + str(paths))
        for path in paths:
            self.__mk_remote_dir(path)

    def __push_local_file(self, local_relative_path: str):
        """
        Push a file to the remote server at same relative location.
        :param local_relative_path: relative path of the file (to it's local_dir or ftp_dir_path)
        """
        logging.debug('__cp_local_file_to_remote : from ' + self._local_directory + local_relative_path + ' to ' + self.__ftp_dir_path + local_relative_path)
        # TODO actual copy

    def __push_local_files(self, local_relative_paths: str):
        """
        Push a list of files.
        :param local_relative_paths: Paths of the files.
        """
        for path in local_relative_paths:
            self.__push_local_file(path)

    def __get_loc_relative_path(self, full_dir_path: str):
        """
        Remove local_directory from full_dir_path.
        :param full_dir_path: local absolute directory path.
        """
        return full_dir_path.replace(self._local_directory, '')

    def _push_files(self):
        if self.__ftp is None:
            self.__connectFtp(self._fetch_uri(protocol=Protocol.FTP))

        loc_dir = self._local_directory
        for (dir_path, dir_names, file_names) in walk(loc_dir):
            relative_dir_path = self.__get_loc_relative_path(dir_path)

            # creating directories
            self.__mk_remote_dirs(list(map(self.__get_loc_relative_path, dir_names)))

            # copy files
            files_fullpath = list(map(lambda fname: self.__get_loc_relative_path(dir_path + '/' + fname), file_names))
            self.__push_local_files(files_fullpath)
