import socket
import sys
import threading

NUM_OF_SERVERS = 4
BUFFER_SIZE = 1024
DELIM = ','
DISCOVER_PORT = 5555


class Server:

    def __init__(self, port, discover_ip, discover_port):
        self.__discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__discover.connect((discover_ip, discover_port))
        print('connected to discover server successfully.')
        data = self.__discover.recv(BUFFER_SIZE).decode()
        print(data)
        self.__id, broadcast_address = data.split(DELIM)
        print('server id is: ' + str(self.__id))
        self.__broadcast.connect(broadcast_address)
        self.__broadcast = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('server' + str(self.__id) + ' connected to broadcast server successfully.')
        self.__welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__welcome.bind(('localhost', port))
        print('server' + str(self.__id) + ' welcome socket established.')
        self.__servers_out = {}
        self.__servers_in = {}
        self.__secrets = {}
        self.__establish_servers_connection()

    def get_id(self):
        return self.__id

    def __establish_servers_connection(self):
        t1 = threading.Thread(target=self.__connect_servers)
        t2 = threading.Thread(target=self.__accept_servers)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        self.__discover.close()

    def __accept_servers(self):
        connections = 0
        while connections < NUM_OF_SERVERS-1:
            self.__welcome.listen(1)
            conn, address = self.__welcome.accept()
            cur_id = conn.recv(BUFFER_SIZE).decode()
            self.__servers_in[cur_id] = conn
            connections += 1

    def __connect_servers(self):
        data = self.__discover.recv(BUFFER_SIZE).decode()
        cur_id, cur_host, cur_port = data.split()
        for _ in range(NUM_OF_SERVERS - 1):
            self.__servers_out[cur_id] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__servers_out[cur_id].connect((cur_host, str(cur_port)))
            self.__servers_out[cur_id].all(self.__id.encode())

    def accept_clients(self):
        pass

    def close(self):
        self.__welcome.close()
        self.__discover.close()
        self.__broadcast.close()
        for sock in self.__servers_in:
            sock.close()
        for sock in self.__servers_out:
            sock.close()


if __name__ == '__main__':
    welcome_port = int(input('please insert port number:'))
    discover_host = input('please insert discover ip address:')
    server = Server(welcome_port, discover_host, DISCOVER_PORT)