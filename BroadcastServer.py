import socket
from threading import Thread, Lock
from Server import *

BROADCAST_HOST = 'localhost'
BROADCAST_PORT = 5566


class BroadcastServer:

    def __init__(self, discover_ip, discover_port):
        discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        discover.connect((discover_ip, discover_port))
        print('connected to discover server successfully.')
        discover.sendall((socket.gethostbyname(BROADCAST_HOST) + DELIM_1 + str(BROADCAST_PORT)).encode())
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
            print('connected successfully to: ' + str(address))
            self.__servers.append(conn)

    def __session(self, client_socket, client_id):
        print('started session with client: ', client_id)
        client_socket.close()

    def accept_clients(self):
        print('ready to accept clients')
        while True:
            self.__welcome.listen(4)  # todo magic
            conn, address = self.__welcome.accept()
            client_id = conn.recv()
            print('connected to client: ', client_id)
            t = Thread(target=self.__session, args=(conn, client_id))
            t.start()

    def close(self):
        for sid in self.__servers:
            self.__servers[sid].close()
        self.__welcome.close()


if __name__ == '__main__':
    broadcast_server = BroadcastServer(DISCOVER_IP, DISCOVER_PORT)
    broadcast_server.accept_clients()
    broadcast_server.close()
