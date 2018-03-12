import socket
import sys
from Server import NUM_OF_SERVERS, DELIM, DISCOVER_PORT
from BroadcastServer import BROADCAST_PORT


class DiscoverServer:

    def __init__(self):
        self.__welcome = socket.socket((socket.AF_INET, socket.SOCK_STREAM))
        self.__welcome.bind(('localhost', DISCOVER_PORT))
        self.__servers = []
        self.__welcome.listen(1)
        self.__broadcast = self.__welcome.accept()
        connections = 0
        while connections < NUM_OF_SERVERS:
            self.__welcome.listen(4)
            conn, address = self.__welcome.accept()
            cur_id = str(connections + 1)
            conn.sendall(cur_id + DELIM + self.__broadcast[1] + DELIM + BROADCAST_PORT)
            self.__servers.append((conn, address))

    def close(self):
        for server in self.__servers:
            server[0].close()
        self.__welcome.close()