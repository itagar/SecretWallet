from Helper import *
import socket
import select


class BroadcastServer:
    """
    A Broadcast Server in the SecretWallet system
    """

    def __init__(self, discover_ip, discover_port):
        """
        constructor for BroadcastServer object
        :param discover_ip: DiscoverServer IP
        :param discover_port: DiscoverServer welcome port
        """
        discover = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        discover.connect((discover_ip, discover_port))
        print('connected to discover server successfully.')
        discover_msg = socket.gethostbyname(BROADCAST_HOST) + DELIM_1 + str(BROADCAST_PORT)
        send_msg(discover, discover_msg)
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
            sid = int(receive_msg(conn))
            print('connected successfully to server: ' + str(sid))
            self.__servers[sid] = conn

    def __sid_from_socket(self, sock):
        """
        get server's id from socket
        :param sock: server's socket - socket
        :return: in case is server - server's id associated with socket, else - 0
        """
        for sid, server_sock in self.__servers.items():
            if sock is server_sock:
                return sid
        return 0

    def broadcast(self, sender_id, sender_sock, data):
        """
        broadcast message to all nodes
        :param sender_id: sender's id - int
        :param sender_sock: sender's socket - socket
        :param data: data sender wish to broadcast - str
        :return: None
        """
        data = str(sender_id) + SENDER_DELIM + data
        print('send broadcast: ', data)
        for sock in self.__outputs:
            if sock is not sender_sock:
                send_msg(sock, data)

    def handle(self):
        """
        connect clients to the broadcast channel and broadcast messages between nodes in the channel
        :return: None
        """
        print('ready to accept clients')
        busy = False

        self.__inputs = [self.__welcome]
        self.__inputs.extend(self.__servers.values())
        self.__outputs.extend(self.__servers.values())
        client_sock = None
        client_id = -1

        while True:
            self.__welcome.listen(NUM_OF_SERVERS+1)
            readable, writable, exceptional = select.select(self.__inputs, [], self.__inputs)

            for r in readable:

                if r is self.__welcome and not busy:  # accept new client if no client is already connected
                    print('welcome a new client to the broadcast family')
                    client_sock, address = self.__welcome.accept()
                    busy = True
                    data = receive_msg(client_sock)
                    client_id = data.split(DELIM_1)[0]
                    print('connected to client: ', client_id)
                    broadcast_server.broadcast(CLIENT_SENDER_ID, client_sock, data)
                    self.__inputs.append(client_sock)
                    self.__outputs.append(client_sock)
                elif r is client_sock:  # get info from existing client
                    data = receive_msg(client_sock)
                    if not data:  # client closed connection
                        self.__inputs.remove(r)
                        self.__outputs.remove(r)
                        r.close()
                        print('removed client: ', str(client_id), ' from broadcast')
                        busy = False
                        client_sock = None
                    else:  # client send message
                        self.broadcast(CLIENT_SENDER_ID, r, data)
                elif r in self.__servers.values():  # get info from servers.
                    data = receive_msg(r)
                    self.broadcast(self.__sid_from_socket(r), r, data)

    def close(self):
        """
        close connections upon exit
        :return:
        """
        for sid in self.__servers:
            self.__servers[sid].close()
        self.__welcome.close()


if __name__ == '__main__':
    broadcast_server = BroadcastServer(DISCOVER_IP, DISCOVER_PORT)

    # handle requests
    try:
        broadcast_server.handle()
    finally:
        print('broadcast server exiting system')
        broadcast_server.close()
