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
        self.__broadcast_packet = broadcast_address[0][0] + DELIM_1 + str(broadcast_address[0][1])
        print('connected successfully to broadcast server')
        broadcast_socket.close()
        print('broadcast discovered successfully and connection was closed')

        # now wait for servers to connect
        servers = []
        connections = 0
        self.__servers_packet = ''

        # connect to servers
        while connections < NUM_OF_SERVERS:
            self.__welcome.listen(4)
            conn, address = self.__welcome.accept()
            cur_id = str(connections + 1)
            conn.sendall((cur_id + DELIM_1 + self.__broadcast_packet).encode())
            connections += 1
            servers.append(conn)
            print('connected successfully to server:' + cur_id + ' in ip: ' + address[0] +
                  ' and port number: ' + str(address[1]))
            self.__servers_packet += cur_id + DELIM_1 + address[0] + DELIM_1 + str(address[1]) + DELIM_2

        self.__servers_packet = self.__servers_packet[:-1]  # delete last char

        # send servers information about other servers
        for i, sock in enumerate(servers):
            sock.sendall(self.__servers_packet).encode()
            sock.close()
            cur_id = str(i + 1)
            print('server: ' + cur_id + ' was discovered successfully and connection was closed')

    def connect_to_clients(self):
        pass

    def close(self):
        self.__welcome.close()


if __name__ == '__main__':
    discover_server = DiscoverServer()
