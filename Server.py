import socket
import select
import random
from threading import Thread, Lock
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
        discover_msg = socket.gethostbyname('localhost') + DELIM_1 + str(port)
        send_msg(self.__discover, discover_msg)
        print('connected to discover server successfully.')
        data = receive_msg(self.__discover)

        # connect to broadcast server
        self.__id, broadcast_host, broadcast_port = data.split(DELIM_1)
        self.__id = int(self.__id)
        print('server id is: ' + str(self.__id))
        self.broadcast = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.broadcast.connect((broadcast_host, int(broadcast_port)))
        self.send_broadcast(str(self.__id))
        print('server' + str(self.__id) + ' connected to broadcast server successfully.')

        # connect to other servers
        self.servers_out = {}
        self.servers_in = {}
        self.__secrets = {}
        self.__clients = {}
        self.__establish_servers_connection()
        self.__discover.close()

        # for vss usage
        self.lock = Lock()
        self.pipe = None

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
            cur_id = int(receive_msg(conn))
            self.servers_in[cur_id] = conn
            connections += 1
            print('accepted connection from server: ' + str(cur_id))

    def __connect_servers(self):
        addresses = receive_msg(self.__discover).split(DELIM_2)
        for address in addresses:
            cur_id, cur_host, cur_port = address.split(DELIM_1)
            cur_id = int(cur_id)
            if cur_id != self.__id:
                print(cur_id, cur_host, int(cur_port))
                self.servers_out[cur_id] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.servers_out[cur_id].connect((cur_host, int(cur_port)))
                self.send_to_server(cur_id, str(self.__id))
                print('connected to server: ' + str(cur_id))

    def __session(self, client_socket, client_id, request):
        print('started session with client: ', client_id)

        if request == STORE:
            print('client: ', client_id, ' wish to store.')
            self.__store_session(client_socket)

        elif request == RETRIEVE:
            print('client: ', client_id, ' wish to retrieve.')
            self.__retrieve_session(client_socket, client_id)

        else:
            print('session with client: ', client_id, ' closed successfully.')
            client_socket.close()

    def handle_requests(self):
        inputs = [self.__welcome, self.broadcast]  # todo disconnect clients
        while True:
            print('ready to accept clients')
            print('current secrets: ', self.__secrets)
            self.__welcome.listen(4)  # todo magic
            readable, writable, exceptional = select.select(inputs, [], inputs)  # todo check closing sockets
            for r in readable:

                if r is self.__welcome:  # accept new clients
                    conn, address = self.__welcome.accept()
                    cid = int(receive_msg(conn))
                    self.__clients[cid] = conn
                    print('connected to client: ', cid)

                elif r is self.broadcast:  # new session
                    # get cid and request type
                    data = self.receive_broadcast()[1].split(DELIM_1)
                    cid, request = int(data[0]), int(data[1])
                    client_sock = self.__clients[cid]
                    self.__session(client_sock, cid, request)

                else:  # todo close connection
                    pass

    def __store_session(self, client_sock):
        sender, name = self.receive_broadcast()  # todo check if name in library
        poly_k = node_vss(self, client_sock)
        poly_v = node_vss(self, client_sock)
        self.__secrets[name] = poly_k[0][0], poly_v[0][0]

    def __retrieve_session(self, client_sock, client_id):
        # sender, name = self.receive_broadcast()  # todo check if name in library
        # q_k_i, q_v_i = self.__secrets[name]
        # q_d_i = node_vss(self, client_sock)
        p_i = share_random_secret(server)
        print(p_i)
        # R_i = (q_k_i - q_d_i) * p_i

        # send value of R_i to all servers
        # self.send_broadcast(str(R_i))

        # receive values of R_j from all other servers
        # report_mat = np.zeros(NUM_OF_SERVERS)
        # report_mat[self.__id] = True
        # X = np.arange(1, NUM_OF_SERVERS+1)
        # Y = np.zeros(NUM_OF_SERVERS)
        # Y[self.__id-1] = R_i
        # while not report_mat.all():
        #     j, R_j = self.receive_broadcast()
        #     report_mat[j-1] = True
        #     Y[j-1] = int(R_j)

        # interpolate R and retrieve key if R(0)=0
        R = np.polyfit(X, Y, F)
        if R[0] == 0:
            send_msg(client_sock, OK + DELIM_2 + str(q_k_i))
        else:
            send_msg(client_sock, ERROR + DELIM_2)

    def get_sid(self, sock):
        for sid, server_sock in self.servers_in.items():
            if sock is server_sock:
                return sid
        return 0

    def send_broadcast(self, data, send_to_self=False):
        if send_to_self:
            data = SEND_TO_SELF + data
        send_msg(self.broadcast, data)

    def receive_broadcast(self):
        data = receive_msg(self.broadcast)
        sender, data = data.split(SENDER_DELIM)
        return int(sender), data

    def send_to_server(self, sid, data):
        send_msg(self.servers_out[sid], data)

    def receive_from_server(self, sid):
        data = receive_msg(self.servers_in[sid])
        return data

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
