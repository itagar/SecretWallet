import socket
import random
from threading import Thread, Lock

NUM_OF_SERVERS = 4
BUFFER_SIZE = 1024
DELIM_1 = ','
DELIM_2 = '~'
DISCOVER_IP = '127.0.0.1'
DISCOVER_PORT = 5555
END_SESSION = 0
STORE = 1
RETRIEVE = 2


class Server:

    def __init__(self, port, discover_ip, discover_port):
        # create welcome socket
        self.__welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__welcome.bind(('localhost', port))
        print('welcome socket established.')

        # connect to discover server
        self.__discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__discover.connect((discover_ip, discover_port))
        self.__discover.sendall((socket.gethostbyname('localhost') + DELIM_1 + str(port)).encode())
        print('connected to discover server successfully.')
        data = self.__discover.recv(BUFFER_SIZE).decode()

        # connect to broadcast server
        self.__id, broadcast_host, broadcast_port = data.split(DELIM_1)
        print('server id is: ' + str(self.__id))
        self.__broadcast = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__broadcast.connect((broadcast_host, int(broadcast_port)))
        print('server' + str(self.__id) + ' connected to broadcast server successfully.')

        # connect to other servers
        self.__servers_out = {}
        self.__servers_in = {}
        self.__secrets = {}
        self.__establish_servers_connection()
        self.__discover.close()

    def get_id(self):
        return self.__id

    def __establish_servers_connection(self):
        t1 = Thread(target=self.__accept_servers)
        t2 = Thread(target=self.__connect_servers)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        print('established connection to all servers.')

    def __accept_servers(self):
        connections = 0
        while connections < NUM_OF_SERVERS-1:
            self.__welcome.listen(NUM_OF_SERVERS-1)
            conn, address = self.__welcome.accept()
            cur_id = conn.recv(BUFFER_SIZE).decode()
            self.__servers_in[cur_id] = conn
            connections += 1
            print('accepted connection from server: ' + cur_id)

    def __connect_servers(self):
        addresses = self.__discover.recv(BUFFER_SIZE).decode().split(DELIM_2)
        for address in addresses:
            cur_id, cur_host, cur_port = address.split(DELIM_1)
            if cur_id != self.__id:
                self.__servers_out[cur_id] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.__servers_out[cur_id].connect((cur_host, int(cur_port)))
                self.__servers_out[cur_id].sendall(self.__id.encode())
                print('connected to server: ' + cur_id)

    def __session(self, client_socket, client_id):
        print('started session with client: ', client_id)

        # while GUI is opened
        while True:
            data = client_socket.recv(BUFFER_SIZE).decode().split()
            request = data[0]

            if request == STORE:
                name, key_req, value_req = data[1:]
                self.__begin_store_session(client_socket, client_id, name, key_req, value_req)

            elif request == RETRIEVE:
                name, key_req = data[1:]
                self.__begin_retrieve_session(client_socket, client_id, name, key_req)

            else:  # end of session
                break
        print('session with client: ', client_id, ' closed successfully.')
        client_socket.close()

    def accept_clients(self):
        print('ready to accept clients')
        while True:
            self.__welcome.listen(4)  # todo magic
            conn, address = self.__welcome.accept()
            client_id = conn.recv(BUFFER_SIZE)
            print('connected to client: ', client_id)
            t = Thread(target=self.__session, args=(conn, client_id))
            t.start()

    def __begin_store_session(self, client_sock, client_id, name, key_share, value_share):
        pass

    def __begin_retrieve_session(self, client_sock, client_id, name, key_share):
        pass

    def close(self):
        self.__welcome.close()
        self.__discover.close()
        self.__broadcast.close()
        for sid in self.__servers_in:
            self.__servers_in[sid].close()
        for sid in self.__servers_out:
            self.__servers_out[sid].close()


if __name__ == '__main__':
    welcome_port = random.randint(6000, 8000)  # todo change port assignment to discover
    server = Server(welcome_port, DISCOVER_IP, DISCOVER_PORT)
    server.accept_clients()
    server.close()
