import socket
from Server import NUM_OF_SERVERS, DELIM, DISCOVER_PORT, BUFFER_SIZE


class DiscoverServer:

    def __init__(self):
        self.__welcome = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__welcome.bind(('localhost', DISCOVER_PORT))
        print('discover server is live with ip: ' + socket.gethostbyname('localhost') +
              ' and port: ' + str(DISCOVER_PORT))
        print('waiting for broadcast server to connect')
        self.__welcome.listen(1)
        broadcast_socket, broadcast_address = self.__welcome.accept()
        self.__broadcast_packet = broadcast_address[0][0] + DELIM + str(broadcast_address[0][1])
        print('connected successfully to broadcast server')
        broadcast_socket.close()
        print('broadcast discovered successfully and connection was closed')

        servers = []
        connections = 0
        self.__servers_packet = ''

        while connections < NUM_OF_SERVERS:  # connect to servers
            self.__welcome.listen(4)
            conn, address = self.__welcome.accept()
            cur_id = str(connections + 1)
            conn.sendall((cur_id + DELIM + self.__broadcast_packet).encode())
            connections += 1
            servers.append(conn)
            print('connected successfully to server:' + cur_id + ' in ip: ' + address[0] +
                  ' and port number: ' + str(address[1]))
            self.__servers_packet += cur_id + DELIM + address[0] + DELIM + str(address[1]) + DELIM

        for i, sock in enumerate(servers):  # send servers information about other servers
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
