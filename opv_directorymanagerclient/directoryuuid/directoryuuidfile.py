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
import os
from tempfile import NamedTemporaryFile
from shutil import copyfile
from urllib.parse import urlparse

from opv_directorymanagerclient.directoryuuid import DirectoryUuid, SyncableDirectory
from opv_directorymanagerclient import Protocol

class DirectoryUuidFile(DirectoryUuid):
    """
    Deal locally with a directory uuid.
    """

    def __init__(self, *args, **kwargs):
        self.__can_hard_link = None

        DirectoryUuid.__init__(self, *args, **kwargs)

    def _can_hard_link(self):
        """
        Return true if we can use hardlink.
        Also save the state to prevent retry.
        """
        if self.__can_hard_link is not None:
            return self.__can_hard_link

        self.__can_hard_link = False
        with NamedTemporaryFile(dir=self.local_directory) as f:
            try:
                f_path = os.path.join(self.local_directory, str(f.name))
                dest = self._syncable_remote.get_full_path(os.path.basename(f_path))
                os.link(f_path, dest)
                os.unlink(dest)
                self.__can_hard_link = True
            except OSError as e:
                self.__can_hard_link = False

        return self.__can_hard_link

    def _cp_or_link(self, src: str, dest: str):
        """
        Hadrlink src to dest if possible, else copy.
        :param src: source path.
        :param dest: dest path.
        """
        if self._can_hard_link():
            logging.debug('DirectoryUuidFile._cp_or_link : hardlinking ' + src + ' -> ' + dest)
            os.link(src, dest)
        else:
            logging.debug('DirectoryUuidFile._cp_or_link : copying ' + src + ' -> ' + dest)
            copyfile(src, dest)

    def _ensure_remote_connexion(self):
        """
        No remote connexion to ensure.
        """
        if self._syncable_remote is None:
            parsed_uri = urlparse(self._fetch_uri(protocol=Protocol.FILE))
            self._syncable_remote = SyncableDirectory(parsed_uri.path, os)

    def _is_newer(self, src: str, dest: str):
        """
        Return true if src is newer than dest.
        :param src: source full path.
        :param dest: dest full path.
        """
        return (os.stat(src).st_mtime - os.stat(dest).st_mtime) > 0

    def _cp_file_push_method(self, rel_path: str, src: SyncableDirectory, dest: SyncableDirectory):
        """
        Atomic cp or hardlink files.
        :param rel_path: Relative path to directoryuuid root.
        :param src: source directory (should be local directory).
        :param dest: destination directory (should be remote directory).
        """
        src_path = src.get_full_path(rel_path)
        dest_path = dest.get_full_path(rel_path)
        if os.path.exists(src_path) and os.path.exists(dest_path) and self._can_hard_link():  # hard link exists nothing to do
            return

        if not os.path.exists(dest_path):
            logging.debug("DirectoryUuidFile._cp_file_push_method: " + str(dest_path) + " doesn't exists ")
            self._cp_or_link(src_path, dest_path)
            return

        if self._is_newer(src_path, dest_path):
            logging.debug("DirectoryUuidFile._cp_file_push_method:  " + str(src_path) + " newer than " + str(dest_path))
            self._cp_or_link(src_path, dest_path)

    def _cp_file_pull_method(self, rel_path, src, dest):
        """
        Pull files.
        :param rel_path: Relative path to directoryuuid root.
        :param src: source directory (should be remote directory)
        :param dest: destination directory (should be local directory).
        """
        self._cp_file_push_method(rel_path, src, dest)
