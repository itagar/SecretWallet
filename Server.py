import socket
import select
import random
from threading import Thread
from Helper import *

BUFFER_SIZE = 1024


class Server:

    def __init__(self, port, discover_ip, discover_port):
        # create welcome socket
        self.__welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__welcome.bind(('localhost', port))
        self.__welcome.listen(NUM_OF_SERVERS)
        print('welcome socket established in ip:', socket.gethostbyname('localhost'), ' and port: ', str(port))

        # connect to discover server
        self.__discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__discover.connect((discover_ip, discover_port))
        self.__discover.sendall((socket.gethostbyname('localhost') + DELIM_1 + str(port)).encode())
        print('connected to discover server successfully.')
        data = self.__discover.recv(BUFFER_SIZE).decode()

        # connect to broadcast server
        self.__id, broadcast_host, broadcast_port = data.split(DELIM_1)
        self.__id = int(self.__id)
        print('server id is: ' + str(self.__id))
        self.broadcast = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.broadcast.connect((broadcast_host, int(broadcast_port)))
        self.broadcast.sendall(str(self.__id).encode())
        print('server' + str(self.__id) + ' connected to broadcast server successfully.')

        # connect to other servers
        self.servers_out = {}
        self.servers_in = {}
        self.__secrets = {}
        self.__clients = {}
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
            conn, address = self.__welcome.accept()
            cur_id = conn.recv(BUFFER_SIZE).decode()
            self.servers_in[cur_id] = conn
            connections += 1
            print('accepted connection from server: ' + cur_id)

    def __connect_servers(self):
        addresses = self.__discover.recv(BUFFER_SIZE).decode().split(DELIM_2)
        for address in addresses:
            cur_id, cur_host, cur_port = address.split(DELIM_1)
            cur_id = int(cur_id)
            if cur_id != self.__id:
                print(cur_id, cur_host, int(cur_port))
                self.servers_out[cur_id] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.servers_out[cur_id].connect((cur_host, int(cur_port)))
                self.servers_out[cur_id].sendall(str(self.__id).encode())
                print('connected to server: ' + str(cur_id))

    def __session(self, client_socket, client_id, request):
        print('started session with client: ', client_id)

        if request == STORE:
            print('client: ', client_id, ' wish to store.')
            self.__store_session(client_socket, client_id)

        elif request == RETRIEVE:
            print('client: ', client_id, ' wish to retrieve.')
            self.__retrieve_session(client_socket, client_id)

        else:
            print('session with client: ', client_id, ' closed successfully.')
            client_socket.close()

    def handle_requests(self):
        print('ready to accept clients')
        inputs = [self.__welcome, self.broadcast]
        while True:
            self.__welcome.listen(4)  # todo magic
            readable, writable, exceptional = select.select(inputs, [], inputs)  # todo check closing sockets
            for r in readable:

                if r is self.__welcome:  # accept new clients
                    conn, address = self.__welcome.accept()
                    cid = int(conn.recv(2).decode())  # todo magic
                    self.__clients[cid] = conn
                    print('connected to client: ', cid)

                elif r is self.broadcast:  # new session
                    # get cid and request type
                    data = self.receive_broadcast(6)[1].split(DELIM_1)  # todo magic
                    cid, request = int(data[0]), int(data[1])
                    client_sock = self.__clients[cid]
                    self.__session(client_sock, cid, request)

                else:  # todo close connection
                    pass

    def __store_session(self, client_sock, client_id):
        return node_vss(self, client_sock)

    def __retrieve_session(self, client_sock, client_id):
        pass

    def receive_broadcast(self, size=BUFFER_SIZE):
        data = self.broadcast.recv(size+2).decode()
        print(data)
        sender, data = data.split(SENDER_DELIM)
        return int(sender), data

    def close(self):
        self.__welcome.close()
        self.__discover.close()
        self.broadcast.close()
        for sid in self.servers_in:
            self.servers_in[sid].close()
        for sid in self.servers_out:
            self.servers_out[sid].close()


if __name__ == '__main__':
    welcome_port = random.randint(6000, 8000)  # todo change port assignment to discover
    server = Server(welcome_port, DISCOVER_IP, DISCOVER_PORT)
    server.handle_requests()
    server.close()
