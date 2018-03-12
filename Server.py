import socket
import select

NUM_OF_SERVERS = 4


class Server:

    __port = 5555
    __num_of_servers = 0

    def __init__(self, port, discover_ip, discover_port):
        self.__host = socket.gethostbyname(socket.gethostname())
        self.__port = port
        self.__welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__welcome.bind((self.__host, self.__port))
        self.__servers_out = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for __ in range(NUM_OF_SERVERS - 1)]
        self.__servers_in = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for __ in range(NUM_OF_SERVERS - 1)]
        self.__discover_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__discover_sock.connect((discover_ip, discover_port))
        self.__id, self.__servers_addresses, broadcast_address = self.__parse_discover_data()
        self.__broadcast = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__broadcast.connect(broadcast_address)
        self.__secrets = {}

    def __parse_discover_data(self):
        pass

    def accept_servers_connections(self):
        connections = 0
        while connections < NUM_OF_SERVERS:
            self.__welcome.listen(1)
            conn, address = self.__welcome.accept()
            self.__servers_in.append(conn)
            connections += 1

    def connect_to_servers(self):
        for i, sock in enumerate(self.__servers_out):
            sock.connect(self.__servers_addresses[i])

    def accept_clients(self):
        pass
