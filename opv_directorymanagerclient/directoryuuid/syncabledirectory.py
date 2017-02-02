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

class SyncableDirectory:
    """
    Utility class to walk over remote/local directries and deal with relative path (relative to directoryuuid root).
    """

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

        if not self.os_utils.path.exists(dest):
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
