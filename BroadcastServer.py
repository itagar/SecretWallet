from Helper import *
import socket
import select

BROADCAST_HOST = 'localhost'
BROADCAST_PORT = 5566
CLIENT_SENDER_ID = 0


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
        self.__inputs = []
        self.__outputs = []

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

    def __get_sid(self, sock):
        for sid, server_sock in self.__servers.items():
            if sock is server_sock:
                return sid

    def __send_broadcast(self, sender_id, sender_sock, data):
        data = str(sender_id) + SENDER_DELIM + data
        for sock in self.__outputs:
            if sock is not sender_sock:
                sock.sendall(data.encode())

    def handle(self):
        print('ready to accept clients')
        busy = False

        self.__inputs = [self.__welcome]
        self.__inputs.extend(self.__servers.values())
        self.__outputs.extend(self.__servers.values())
        client_sock = None

        while True:
            self.__welcome.listen(4)  # todo magic
            readable, writable, exceptional = select.select(self.__inputs, [], self.__inputs)  # todo check writing

            for r in readable:

                if r is self.__welcome and not busy:  # accept new client
                    client_sock, address = self.__welcome.accept()
                    busy = True
                    data = client_sock.recv(4).decode()  # todo magic
                    client_id = data.split(DELIM_1)[0]
                    self.handle()
                    print('connected to client: ', client_id)
                    broadcast_server.__send_broadcast(CLIENT_SENDER_ID, client_sock, data)
                    self.__inputs.append(client_sock)
                    self.__outputs.append(client_sock)
                elif r is client_sock:
                    data = r.recv(BUFFER_SIZE).decode()
                    self.__send_broadcast(CLIENT_SENDER_ID, r, data)
                else:
                    data = r.recv(BUFFER_SIZE).decode()
                    self.__send_broadcast(self.__get_sid(r), r, data)  # todo magic

            for s in exceptional:  # todo check if works
                # Stop listening for input on the connection
                self.__inputs.remove(s)
                self.__outputs.remove(s)
                s.close()
                busy = False

    def close(self):
        for sid in self.__servers:
            self.__servers[sid].close()
        self.__welcome.close()


if __name__ == '__main__':
    broadcast_server = BroadcastServer(DISCOVER_IP, DISCOVER_PORT)
    broadcast_server.handle()
    broadcast_server.close()
