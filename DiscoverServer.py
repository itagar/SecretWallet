import socket
from Server import NUM_OF_SERVERS, DELIM_1, DELIM_2, DISCOVER_PORT, BUFFER_SIZE


class DiscoverServer:

    def __init__(self):
        # create welcome socket
        self.__welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__welcome.bind(('localhost', DISCOVER_PORT))
        print('discover server is live with ip: ' + socket.gethostbyname('localhost') +
              ' and port: ' + str(DISCOVER_PORT))

        # connect to broadcast to get information for discovery
        print('waiting for broadcast server to connect')
        self.__welcome.listen(1)
        broadcast_socket, broadcast_address = self.__welcome.accept()
        broadcast_host, broadcast_port = broadcast_socket.recv(BUFFER_SIZE).decode().split(DELIM_1)
        self.__broadcast_packet = broadcast_host + DELIM_1 + broadcast_port
        print(broadcast_address)
        print('broadcast packet: ', self.__broadcast_packet)
        print('connected successfully to broadcast server')
        broadcast_socket.close()
        print('broadcast discovered successfully and connection was closed')

        # now wait for servers to connect
        servers = []
        connections = 0
        self.__servers_packet = ''

        # connect to servers
        while connections < NUM_OF_SERVERS:
            print('waiting for servers to connect. currently: ' + str(connections)
                  + ' from total: ' + str(NUM_OF_SERVERS))
            self.__welcome.listen(4)
            conn, address = self.__welcome.accept()
            cur_id = str(connections + 1)
            welcome_host, welcome_port = conn.recv(BUFFER_SIZE).decode().split(DELIM_1)
            conn.sendall((cur_id + DELIM_1 + self.__broadcast_packet).encode())
            connections += 1
            servers.append(conn)
            print('connected successfully to server:' + cur_id + ' in ip: ' + address[0] +
                  ' and port number: ' + str(address[1]))
            self.__servers_packet += cur_id + DELIM_1 + welcome_host + DELIM_1 + welcome_port + DELIM_2
            print('cur servers packet: ', self.__servers_packet)

        self.__servers_packet = self.__servers_packet[:-1]  # delete last char

        # send servers information about other servers
        for i, sock in enumerate(servers):
            sock.sendall(self.__servers_packet.encode())
            sock.close()
            cur_id = str(i + 1)
            print('server: ' + cur_id + ' was discovered successfully and connection was closed')

    def accept_clients(self):
        print('ready to accept clients')
        client_id = 1
        while True:
            self.__welcome.listen(4)  # todo magic
            conn, address = self.__welcome.accept()
            # send to client all data required to connect to the system
            print('connected client: ', client_id)
            data = str(client_id) + DELIM_2 + self.__broadcast_packet + DELIM_2 + self.__servers_packet
            conn.sendall(data.encode())
            conn.close()
            print('discovered client: ', client_id, ' successfully')
            client_id += 1

    def close(self):
        self.__welcome.close()


if __name__ == '__main__':
    discover_server = DiscoverServer()
    discover_server.accept_clients()
    discover_server.close()
