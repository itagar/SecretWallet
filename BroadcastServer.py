import socket
import sys
from Server import NUM_OF_SERVERS, BUFFER_SIZE, DISCOVER_PORT

BROADCAST_HOST = 'localhost'
BROADCAST_PORT = 5566


class BroadcastServer:

    def __init__(self, discover_ip, discover_port):
        discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        discover.connect((discover_ip, discover_port))
        print('connected to discover server successfully.')
        discover.close()
        print('discovered successfully and closed connection.')
        self.__welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__welcome.bind((BROADCAST_HOST, BROADCAST_PORT))
        print('broadcast welcome socket established.')
        self.__servers = []

        # connect servers
        for i in range(NUM_OF_SERVERS):
            self.__welcome.listen(NUM_OF_SERVERS)
            conn, address = self.__welcome.accept()
            print('connected successfully to: ' + address)
            self.__servers.append(conn)

    def close(self):
        for server in self.__servers:
            server.close()


if __name__ == '__main__':
    discover_host = input('please insert discover ip address:')
    broadcast_server = BroadcastServer(discover_host, DISCOVER_PORT)
    broadcast_server.close()
