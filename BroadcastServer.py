from Helper import *
import socket
import select

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
        self.__servers = {}
        self.__clients = {}
        self.__inputs = [self.__welcome]

        # connect servers
        for i in range(NUM_OF_SERVERS):
            self.__welcome.listen(NUM_OF_SERVERS)
            conn, address = self.__welcome.accept()
            sid = conn.recv(1).decode()  # todo magic
            print('connected successfully to server: ' + sid)
            self.__servers[sid] = conn

    def __session(self, cid, client_sock, request):
        print('session started with: ', cid)
        data = str(cid).zfill(2) + DELIM_1 + str(request)  # todo magic
        for server_sock in self.__servers.values():
            server_sock.sendall(data.encode())
        self.__inputs.remove(client_sock)

    def accept_clients(self):
        print('ready to accept clients')
        self.__inputs = [self.__welcome]

        while True:
            self.__welcome.listen(4)  # todo magic
            readable, writable, exceptional = select.select(self.__inputs, [], self.__inputs)

            for r in readable:

                if r is self.__welcome:  # accept new client
                    conn, address = self.__welcome.accept()
                    client_id = int(conn.recv(2).decode())  # todo magic
                    print('connected to client: ', client_id)
                    self.__clients[client_id] = conn
                    self.__inputs.append(conn)

                else:  # client request
                    request = int(r.recv(1).decode())  # todo magic
                    for cid, client_sock in self.__clients.items():
                        if r is client_sock:
                            self.__session(cid, client_sock, request)

            for r in exceptional:  # todo implement?
                pass

    def close(self):
        for sid in self.__servers:
            self.__servers[sid].close()
        self.__welcome.close()


if __name__ == '__main__':
    broadcast_server = BroadcastServer(DISCOVER_IP, DISCOVER_PORT)
    broadcast_server.accept_clients()
    broadcast_server.close()
