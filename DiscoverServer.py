import socket
from Helper import *


class DiscoverServer:
    """
    A Discover Server in SecretWallet System
    """

    def __init__(self):
        """
        constructor for DiscoverServer object
        """
        # create welcome socket
        self.__welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__welcome.bind(('localhost', DISCOVER_PORT))
        print('discover server is live with ip: ' + socket.gethostbyname('localhost') +
              ' and port: ' + str(DISCOVER_PORT))

        # connect to broadcast to get information for discovery
        self.__welcome.listen(1)
        print('waiting for broadcast server to connect')
        broadcast_socket, broadcast_address = self.__welcome.accept()
        broadcast_host, broadcast_port = receive_msg(broadcast_socket).split(DELIM_1)
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

        # create random polynomial for retrieve usage
        p = np.random.randint(1, P, F+1)
        p_values = np.polyval(p, np.arange(NUM_OF_SERVERS+1))

        # connect to servers
        while connections < NUM_OF_SERVERS:
            print('waiting for servers to connect. currently: ' + str(connections)
                  + ' from total: ' + str(NUM_OF_SERVERS))
            self.__welcome.listen(4)
            conn, address = self.__welcome.accept()
            cur_id = str(connections + 1)
            welcome_host, welcome_port = receive_msg(conn).split(DELIM_1)
            server_msg = cur_id + DELIM_1 + self.__broadcast_packet
            send_msg(conn, server_msg)  # send id and broadcast details
            send_msg(conn, str(p_values[int(cur_id)]))  # send p_value for retrieve
            connections += 1
            servers.append(conn)
            print('connected successfully to server:' + cur_id + ' in ip: ' + address[0] +
                  ' and port number: ' + str(address[1]))
            self.__servers_packet += cur_id + DELIM_1 + welcome_host + DELIM_1 + welcome_port + DELIM_2
            print('cur servers packet: ', self.__servers_packet)

        self.__servers_packet = self.__servers_packet[:-1]  # delete last char

        # send servers information about other servers
        for i, sock in enumerate(servers):
            send_msg(sock, self.__servers_packet)
            sock.close()
            cur_id = str(i + 1)
            print('server: ' + cur_id + ' was discovered successfully and connection was closed')

    def accept_clients(self):
        """
        accept new clients and discover them to system
        :return: None
        """
        print('ready to accept clients')
        client_id = 1
        while True:
            self.__welcome.listen(NUM_OF_SERVERS)
            conn, address = self.__welcome.accept()
            # send to client all data required to connect to the system
            print('connected client: ', client_id)
            client_data = str(client_id) + DELIM_2 + self.__broadcast_packet + DELIM_2 + self.__servers_packet
            send_msg(conn, client_data)
            conn.close()
            print('discovered client: ', client_id, ' successfully')
            client_id += 1

    def close(self):
        """
        close connections upon exit
        :return: None
        """
        self.__welcome.close()


if __name__ == '__main__':
    discover_server = DiscoverServer()
    discover_server.accept_clients()
    discover_server.close()
