# OPV Directory Manager Client

## Description
Python client for [OPV Directory Manager](https://github.com/OpenPathView/DirectoryManager).
This module can be used to work easily with UUID directory as if they were local directories and push their content back to the storage service.
This client can use both FTP and local protocoles to fetch files from the storage service and push them back.

## How to use it

###
```python
from opv_directorymanagerclient import DirectoryManagerClient, Protocol

dm_client = DirectoryManagerClient(api_base="http://opv_master:5005", default_protocol=Protocol.FTP)
uuid = None

# Create a directory with context manager
with dm_client.Open() as (dir_uuid, dir_path):
    uuid = dir_uuid
    with open(dir_path + "/test_file.txt", "w") as f:
        f.write("test for {}".format(uuid))

# Create directory without context manager
d = dm_client.Open()
print("uuid : {} - path : {}".format(d.uuid, d.local_directory))
with open(d.local_directory + "/test_file.txt", "w") as f:
    f.write("test for {}".format(d.uuid))
d.save()
d.close()

# Open existing directory
with dm_client.Open(uuid=uuid) as (_, dir_path):
    with open(dir_path + "/test_file.txt", "r") as f:
        print(f.readlines())

# Open existing directory without context manager
d = dm_client.Open(uuid=uuid)
with open(d.local_directory + "/test_file.txt", "r") as f:
    print(f.readlines())
d.close()
```

## Launch tests

## License

Copyright (C) 2017 Open Path View <br />
This program is free software; you can redistribute it and/or modify  <br />
it under the terms of the GNU General Public License as published by  <br />
the Free Software Foundation; either version 3 of the License, or  <br />
(at your option) any later version.  <br />
This program is distributed in the hope that it will be useful,  <br />
but WITHOUT ANY WARRANTY; without even the implied warranty of  <br />
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the  <br />
GNU General Public License for more details.  <br />
You should have received a copy of the GNU General Public License along  <br />
with this program. If not, see <http://www.gnu.org/licenses/>.  <br />
