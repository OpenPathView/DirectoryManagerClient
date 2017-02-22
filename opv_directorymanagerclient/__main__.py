"""
Usage:
    opv-dm-client <dir-uuid> [--protocol=<proto>] [--dir-manager=<str>]
    opv-dm-client (-h | --help)

Options:
    -h --help                Show help.
    --protocol=<protocol>    The protocol to open files, in FTP, local. [default: FTP]
    --dir-manager=<str>      API for directory manager [default: http://localhost:5001]
"""

import docopt
from opv_directorymanagerclient import DirectoryManagerClient, Protocol

protocols = {proto.name.lower(): proto.value for proto in Protocol}

def main():
    args = docopt.docopt(__doc__)

    proto_arg = args['--protocol'].lower()

    if proto_arg in protocols:
        proto = protocols[proto_arg]
    else:
        print("Protocol not founded. Protocol could be any of {}".format(protocols.keys()))
        return

    dir_manager_client = DirectoryManagerClient(api_base=args['--dir-manager'], default_protocol=proto)
    with dir_manager_client.Open(args['<dir-uuid>']) as infos:
        print('UUID {} is opened in {}\nCTRL-C or close the process to close the uuid'.format(*infos))
        try:
            while True: pass
        except KeyboardInterrupt:
            print("losing UUID")

if __name__ == "__main__":
    main()
